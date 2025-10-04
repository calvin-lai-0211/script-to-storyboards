#!/usr/bin/env python3
"""
RunningHub API Jimeng Image-to-Image implementation.
Provides image-to-image generation using RunningHub API's Jimeng model,
supporting 1 to 5 input images.
"""

import time
import requests
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any, Union, List, Callable
from PIL import Image
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import random

from utils.config import RUNNINGHUB_API_CONFIG

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RunningHubConcurrencyManager:
    """
    RunningHub Concurrency Manager - Extremely conservative concurrency control
    to avoid TASK_QUEUE_MAXED errors.
    """
    
    def __init__(self, max_concurrent: int = 3, conservative_threshold: int = 1):
        self.max_concurrent = max_concurrent
        self.conservative_threshold = max(1, conservative_threshold)
        self.submitted_tasks = 0
        self.running_tasks = 0
        self.lock = threading.Lock()
        
    def try_submit_task(self) -> bool:
        """
        Atomic operation: check and submit a task within the same lock.
        Returns True if submission is permitted, False otherwise.
        """
        with self.lock:
            can_submit = self.submitted_tasks < self.max_concurrent
            if can_submit:
                self.submitted_tasks += 1
                self.running_tasks += 1
                logger.info(f"✅ Acquired task submission slot. Submitted: {self.submitted_tasks}/{self.max_concurrent}, Running: {self.running_tasks}")
                return True
            else:
                submitted = self.submitted_tasks
                running = self.running_tasks
                logger.info(f"🚫 Cannot submit task: already {submitted}/{self.max_concurrent} tasks (Running: {running}, Queued: {submitted - running})")
                return False

    def task_finished(self):
        """Records the completion of a task (success or failure)."""
        with self.lock:
            self.submitted_tasks = max(0, self.submitted_tasks - 1)
            self.running_tasks = max(0, self.running_tasks - 1)
            logger.info(f"📊 Task finished. Current running tasks: {self.running_tasks}, Submitted tasks: {self.submitted_tasks}/{self.max_concurrent}")

    def get_status(self) -> dict:
        """Gets the complete status."""
        with self.lock:
            submitted = self.submitted_tasks
            running = self.running_tasks
            return {
                "submitted": submitted,
                "running": running,
                "queued": submitted - running,
                "max_concurrent": self.max_concurrent,
            }

# Global concurrency manager
_concurrency_manager = RunningHubConcurrencyManager(max_concurrent=3)


class JimengImg2ImgRH:
    """
    RunningHub API Jimeng Image-to-Image Generator.
    """
    
    MODEL_CONFIGS = {
        1: {
            "webappId": "1974308812641406977",
            "image_node_ids": ["2"]
        },
        2: {
            "webappId": "1974313475067482113",
            "image_node_ids": ["2", "5"]
        },
        3: {
            "webappId": "1974412050791272449",
            "image_node_ids": ["2", "5", "6"]
        },
        4: {
            "webappId": "1974426055425568770",
            "image_node_ids": ["2", "5", "6", "7"]
        },
        5: {
            "webappId": "1974431077643194369",
            "image_node_ids": ["2", "5", "6", "7", "9"]
        }
    }
    PROMPT_NODE_ID = "4"
    SIZE_NODE_ID = "1"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initializes the JimengImg2ImgRH client.
        
        Args:
            api_key: RunningHub API Key. Uses value from config if None.
        """
        self.api_key = api_key or RUNNINGHUB_API_CONFIG["api_key"]
        self.host = RUNNINGHUB_API_CONFIG["host"]
        self.base_url = RUNNINGHUB_API_CONFIG["base_url"]
        self.upload_url = RUNNINGHUB_API_CONFIG["upload_url"]
        self.run_url = RUNNINGHUB_API_CONFIG["run_url"]
        self.status_url = RUNNINGHUB_API_CONFIG["status_url"]
        self.outputs_url = RUNNINGHUB_API_CONFIG["outputs_url"]
        self.poll_interval = RUNNINGHUB_API_CONFIG["poll_interval"]
        
        self.headers = {
            'Host': self.host,
            'Content-Type': 'application/json'
        }
        
        logger.info("JimengImg2ImgRH initialized.")

    def upload_image(self, image_path: str) -> Optional[str]:
        """
        Uploads an image to the RunningHub server.
        
        Args:
            image_path: Path to the local image file.
            
        Returns:
            The uploaded file name on success, None on failure.
        """
        if not os.path.exists(image_path):
            logger.error(f"Image file does not exist: {image_path}")
            return None
            
        logger.info(f"Uploading image to RunningHub: {image_path}")
        
        upload_headers = {'Host': self.host}
        file_ext = Path(image_path).suffix.lower()
        content_type = {'jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png'}.get(file_ext, 'image/jpeg')
        
        try:
            with open(image_path, 'rb') as f:
                files = {'file': (os.path.basename(image_path), f, content_type)}
                form_data = {'apiKey': self.api_key, 'fileType': 'image'}
                
                response = requests.post(
                    url=self.upload_url,
                    headers=upload_headers,
                    data=form_data,
                    files=files,
                    timeout=RUNNINGHUB_API_CONFIG["upload_timeout"]
                )
                response.raise_for_status()
                result = response.json()
                
                if result.get('code') == 0:
                    file_name = result['data']['fileName']
                    logger.info(f"Image uploaded successfully: {file_name}")
                    return file_name
                else:
                    logger.error(f"Image upload failed: {result.get('msg', 'Unknown error')}")
                    return None
        except Exception as e:
            logger.error(f"Image upload failed: {e}", exc_info=True)
            return None

    def generate_image(self,
                       prompt: str,
                       image_paths: List[str],
                       size: str = "1K",
                       timeout: Optional[int] = None,
                       use_concurrency_control: bool = True,
                       on_start_callback: Optional[Callable[[], None]] = None) -> Optional[Dict[str, Any]]:
        """
        Executes image-to-image generation.
        
        Args:
            prompt: The text prompt.
            image_paths: A list of local paths to the input images (1 to 5).
            size: The output size ("1K", "2K", "4K").
            timeout: Timeout in seconds.
            use_concurrency_control: Whether to use the concurrency manager.
            on_start_callback: Callback to execute when the task starts.
            
        Returns:
            A dictionary with the generation result, or None on failure.
        """
        num_images = len(image_paths)
        if num_images not in self.MODEL_CONFIGS:
            logger.error(f"Invalid number of images: {num_images}. Supported counts are 1, 2, 3, 4, 5.")
            return None

        slot_acquired = False
        try:
            if use_concurrency_control:
                while not _concurrency_manager.try_submit_task():
                    status = _concurrency_manager.get_status()
                    logger.info(f"⏳ Concurrency control: Waiting for a slot. Submitted: {status['submitted']}, Running: {status['running']}")
                    time.sleep(2)
                slot_acquired = True

            if on_start_callback:
                on_start_callback()

            # Upload images in parallel
            logger.info(f"Uploading {num_images} images...")
            uploaded_file_names = []
            with ThreadPoolExecutor() as executor:
                future_to_path = {executor.submit(self.upload_image, path): path for path in image_paths}
                for future in as_completed(future_to_path):
                    file_name = future.result()
                    if not file_name:
                        logger.error(f"Failed to upload image: {future_to_path[future]}")
                        return None
                    uploaded_file_names.append(file_name)
            
            if len(uploaded_file_names) != num_images:
                logger.error("One or more image uploads failed. Aborting generation.")
                return None

            config = self.MODEL_CONFIGS[num_images]
            webapp_id = config["webappId"]
            image_node_ids = config["image_node_ids"]

            # Construct nodeInfoList
            node_info_list = [
                {
                    "nodeId": self.SIZE_NODE_ID,
                    "fieldName": "size",
                    "fieldValue": size,
                    "description": "size"
                },
                {
                    "nodeId": self.PROMPT_NODE_ID,
                    "fieldName": "prompt",
                    "fieldValue": prompt,
                    "description": "prompt"
                }
            ]

            for i, file_name in enumerate(uploaded_file_names):
                node_info_list.append({
                    "nodeId": image_node_ids[i],
                    "fieldName": "image",
                    "fieldValue": file_name,
                    "description": f"image_{i+1}"
                })

            request_data = {
                "webappId": webapp_id,
                "apiKey": self.api_key,
                "nodeInfoList": node_info_list
            }

            logger.info("Submitting generation task...")
            response = requests.post(
                url=self.run_url, 
                headers=self.headers, 
                data=json.dumps(request_data)
            )
            response.raise_for_status()
            submission_result = response.json()

            if submission_result.get('code') != 0:
                logger.error(f"❌ Task submission failed: {submission_result.get('msg', 'Unknown error')}")
                return None
            
            task_data = submission_result.get("data", {})
            task_id = task_data.get("taskId")
            if not task_id:
                logger.error(f"❌ Failed to get taskId from submission response: {task_data}")
                return None
                
            logger.info(f"✅ Task submitted successfully! Task ID: {task_id}")
            
            return self._poll_task_status(task_id, timeout or RUNNINGHUB_API_CONFIG["generate_timeout"])

        except Exception as e:
            logger.error(f"An exception occurred during image generation: {e}", exc_info=True)
            return None
        finally:
            if slot_acquired:
                _concurrency_manager.task_finished()

    def _poll_task_status(self, task_id: str, timeout: int) -> Optional[Dict[str, Any]]:
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            try:
                status_data = {"apiKey": self.api_key, "taskId": task_id}
                response = requests.post(self.status_url, headers=self.headers, data=json.dumps(status_data), timeout=10)
                response.raise_for_status()
                status_result = response.json()

                if status_result.get('code') == 0:
                    task_status_data = status_result.get('data')
                    task_status = ""
                    if isinstance(task_status_data, str):
                        task_status = task_status_data
                    elif isinstance(task_status_data, dict):
                        task_status = task_status_data.get('taskStatus')

                    if task_status == 'SUCCESS':
                        logger.info(f"✅ Task {task_id} completed successfully. Fetching outputs...")
                        return self._get_task_outputs(task_id)
                    elif task_status in ['FAIL', 'CANCEL']:
                        logger.error(f"❌ Task {task_id} failed or was cancelled with status: {task_status}")
                        return None
                    else:
                        logger.info(f"⏳ Task {task_id} status: {task_status}. Polling again in {self.poll_interval}s...")
                else:
                    logger.warning(f"⚠️ Status check API returned an error: {status_result.get('msg', 'Unknown API error')}")

            except Exception as e:
                logger.warning(f"⚠️ An error occurred while polling task status: {e}")
            
            time.sleep(self.poll_interval)
        
        logger.error(f"Task {task_id} timed out after {timeout} seconds.")
        return None

    def _get_task_outputs(self, task_id: str) -> Optional[Dict[str, Any]]:
        try:
            outputs_data = {"apiKey": self.api_key, "taskId": task_id}
            response = requests.post(self.outputs_url, headers=self.headers, data=json.dumps(outputs_data))
            response.raise_for_status()
            outputs_result = response.json()

            if outputs_result.get('code') != 0:
                logger.error(f"❌ Failed to get task outputs: {outputs_result.get('msg', 'Unknown error')}")
                return None
            
            data = outputs_result.get('data', [])
            if data:
                for item in data:
                    if 'fileUrl' in item:
                        return {
                            'code': 0,
                            'data': {
                                'images': [{'imageUrl': item.get('fileUrl')}]
                            }
                        }
            
            logger.error("❌ No output file URL found in the response.")
            return None
        except Exception as e:
            logger.error(f"Failed to get task outputs: {e}", exc_info=True)
            return None

    def _download_image(self, image_url: str, output_path: str, retries: int = 3, delay: int = 5) -> Optional[str]:
        for attempt in range(retries):
            try:
                response = requests.get(image_url, timeout=60)
                response.raise_for_status()
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                logger.info(f"Image downloaded successfully to: {output_path}")
                return output_path
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to download image (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(delay)
                else:
                    logger.error("Max retries reached. Download failed.")
        return None

    def image_to_image(self, 
                       prompt: str,
                       image_paths: List[str],
                       output_path: str,
                       size: str = "1K",
                       on_start_callback: Optional[Callable[[], None]] = None) -> Optional[str]:
        """
        Convenience method to generate and download a single image.
        """
        if os.path.exists(output_path):
            logger.info(f"File already exists, skipping generation: {output_path}")
            return output_path
            
        try:
            result = self.generate_image(
                prompt=prompt,
                image_paths=image_paths,
                size=size,
                on_start_callback=on_start_callback
            )
            
            if not result or result.get('code') != 0:
                logger.error("Generation failed, no result obtained.")
                return None
            
            images = result.get('data', {}).get('images', [])
            if not images or not images[0].get('imageUrl'):
                logger.error("Generation failed, no image URL in the result.")
                return None
            
            image_url = images[0]['imageUrl']
            
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            return self._download_image(image_url, output_path)
        except Exception as e:
            logger.error(f"Failed to generate image: {e}", exc_info=True)
            return None

def create_jimeng_img2img_rh(api_key: Optional[str] = None) -> JimengImg2ImgRH:
    return JimengImg2ImgRH(api_key=api_key)

if __name__ == "__main__":
    # This is an example, you need to create dummy image files for it to run.
    # e.g., `touch test_image_1.jpg`
    
    # Create dummy files for testing
    test_image_files = []
    for i in range(1, 6):
        file_path = f"test_image_{i}.jpg"
        if not os.path.exists(file_path):
            Image.new('RGB', (100, 100), color = 'red').save(file_path)
        test_image_files.append(file_path)

    generator = create_jimeng_img2img_rh()
    
    test_cases = {
        "1_image": {
            "prompt": "这个女性的衣服虽然旧了，有点褪色，但是非常干净",
            "images": [test_image_files[0]]
        },
        "2_images": {
            "prompt": "图1 的女性换上图2的裙子，虽然有一点点的褪色，但是非常整洁干净",
            "images": test_image_files[0:2]
        },
        "3_images": {
            "prompt": "图1 的女性换上图2的裙子，坐在图三小屋灯旁边的椅子上，近景，神色平静，再看一张报纸",
            "images": test_image_files[0:3]
        }
    }
    
    for name, case in test_cases.items():
        print(f"\n--- Running test case: {name} ---")
        output_file = f"jimeng_i2i_test_{name}.jpg"
        
        saved_path = generator.image_to_image(
            prompt=case["prompt"],
            image_paths=case["images"],
            output_path=output_file
        )
        
        if saved_path:
            print(f"✅ Image generated successfully and saved to: {saved_path}")
        else:
            print(f"❌ Image generation failed for case: {name}")

    # Clean up dummy files
    # for file_path in test_image_files:
    #     if os.path.exists(file_path):
    #         os.remove(file_path)
