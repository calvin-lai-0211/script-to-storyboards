#!/usr/bin/env python3
"""
RunningHub API Qwen Image Text-to-Image implementation.
Provides text-to-image generation using RunningHub API's Qwen Image model.
"""

import time
import requests
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any, Union, List
from PIL import Image
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import random

from utils.config import RUNNINGHUB_API_CONFIG

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RunningHubConcurrencyManager:
    """RunningHub并发管理器 - 极其保守的并发控制，避免TASK_QUEUE_MAXED错误"""
    
    def __init__(self, max_concurrent: int = 3, conservative_threshold: int = 1):
        # 注意：conservative_threshold设为1以避免服务器队列限制
        self.max_concurrent = max_concurrent
        self.conservative_threshold = max(1, conservative_threshold)  # 最小为1，极其保守
        self.submitted_tasks = 0  # 已提交到服务器的任务数（包括QUEUED）
        self.running_tasks = 0    # 实际正在运行的任务数（RUNNING状态）
        self.lock = threading.Lock()
        
    def can_submit_task_conservative(self) -> bool:
        """
        保守模式：允许最多 max_concurrent 个任务并发运行
        这样可以充分利用RunningHub的并发能力同时避免TASK_QUEUE_MAXED错误
        注意：此方法仅用于检查，不修改状态
        """
        with self.lock:
            # 使用局部变量确保多线程一致性
            submitted = self.submitted_tasks
            running = self.running_tasks
            max_concurrent = self.max_concurrent
            
            # 🔒 使用max_concurrent作为并发限制，允许多个任务并发
            can_submit = submitted < max_concurrent
            
            if not can_submit:
                logger.info(f"🚫 并发控制：当前已提交任务数 {submitted} >= {max_concurrent}，等待任务完成")
                logger.info(f"   其中正在运行: {running}, 排队中: {submitted - running}")
            
            return can_submit
    
    def try_submit_task(self) -> bool:
        """
        🔒 原子操作：检查并提交任务（在同一个锁中完成）
        这样可以防止多个线程同时通过检查并提交任务的竞争条件
        
        Returns:
            True: 成功获得提交权限，已增加计数
            False: 当前无法提交，需要等待
        """
        with self.lock:
            # 使用局部变量确保多线程一致性
            submitted = self.submitted_tasks
            running = self.running_tasks
            max_concurrent = self.max_concurrent
            
            # 🔒 原子检查和提交：允许最多 max_concurrent 个任务并发
            can_submit = submitted < max_concurrent
            
            if can_submit:
                # 🔒 关键修复：立即增加已提交和运行任务计数
                # 这样可以避免在轮询过程中的同步问题
                self.submitted_tasks += 1
                self.running_tasks += 1  # 立即计为运行中，不等待轮询确认
                logger.info(f"✅ 获得任务提交权限，已提交: {self.submitted_tasks}/{max_concurrent}, 运行中: {self.running_tasks}")
                return True
            else:
                logger.info(f"🚫 无法提交任务：当前已有 {submitted}/{max_concurrent} 个任务 (运行中: {running}, 排队中: {submitted - running})")
                return False
    
    def task_finished(self):
        """记录任务完成（包括成功和失败）"""
        with self.lock:
            self.submitted_tasks = max(0, self.submitted_tasks - 1)
            self.running_tasks = max(0, self.running_tasks - 1)
            # 使用局部变量确保多线程一致性
            running = self.running_tasks
            submitted = self.submitted_tasks
            max_concurrent = self.max_concurrent
            
            logger.info(f"📊 任务完成，当前运行任务数: {running}, 已提交任务数: {submitted}/{max_concurrent}")
            
            # 当已提交任务数小于max_concurrent时，可以启动新任务
            if submitted < max_concurrent:
                logger.info(f"✅ 可以启动新任务 (当前: {submitted}/{max_concurrent})")
    
    def task_failed_before_running(self):
        """记录任务在开始运行前就失败了（提交失败或异常状态）"""
        with self.lock:
            self.submitted_tasks = max(0, self.submitted_tasks - 1)
            # 使用局部变量确保多线程一致性
            running = self.running_tasks
            submitted = self.submitted_tasks
            logger.info(f"❌ 任务提交失败，当前运行任务数: {running}, 已提交任务数: {submitted}")
    
    def get_submitted_count(self) -> int:
        """获取当前已提交任务数"""
        with self.lock:
            return self.submitted_tasks
    
    def get_running_count(self) -> int:
        """获取当前正在运行任务数"""
        with self.lock:
            return self.running_tasks
    
    def get_status(self) -> dict:
        """获取完整状态"""
        with self.lock:
            # 确保所有变量访问都在锁保护下，保证多线程一致性
            submitted = self.submitted_tasks
            running = self.running_tasks
            max_concurrent = self.max_concurrent
            conservative_threshold = self.conservative_threshold
            return {
                "submitted": submitted,
                "running": running,
                "queued": submitted - running,
                "max_concurrent": max_concurrent,
                "conservative_threshold": conservative_threshold
            }


# 全局并发管理器 - 使用极保守设置避免TASK_QUEUE_MAXED错误
_concurrency_manager = RunningHubConcurrencyManager(max_concurrent=3, conservative_threshold=1)


class QwenImageT2IRH:
    """RunningHub API Qwen Image 文本转图片生成器"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 QwenImageT2IRH
        
        Args:
            api_key: RunningHub API Key，如果为None则使用配置文件中的值
        """
        self.api_key = api_key or RUNNINGHUB_API_CONFIG["api_key"]
        self.host = RUNNINGHUB_API_CONFIG["host"]
        self.base_url = RUNNINGHUB_API_CONFIG["base_url"]
        self.run_url = RUNNINGHUB_API_CONFIG["run_url"]
        self.status_url = RUNNINGHUB_API_CONFIG["status_url"]
        self.outputs_url = RUNNINGHUB_API_CONFIG["outputs_url"]
        self.webapp_id = "1955451864637587458"
        self.output_node_id = "9" # Assuming same as flux
        self.poll_interval = RUNNINGHUB_API_CONFIG["poll_interval"]
        
        self.headers = {
            'Host': self.host,
            'Content-Type': 'application/json'
        }
        
        logger.info(f"QwenImageT2IRH 初始化完成，使用WebApp ID: {self.webapp_id}")

    def generate_image(self, 
                       prompt: str,
                       width: int = 720,
                       height: int = 1280,
                       seed: Optional[int] = None,
                       timeout: Optional[int] = None,
                       use_concurrency_control: bool = True) -> Optional[Dict[str, Any]]:
        """
        执行文本转图片生成
        
        Args:
            prompt: 提示词
            width: 图片宽度
            height: 图片高度
            seed: 随机种子, 如果为None则随机生成
            timeout: 超时时间（秒），如果为None则使用默认值
            use_concurrency_control: 是否使用并发控制，默认为True
            
        Returns:
            生成结果字典，包含图片URL等信息，失败返回None
        """
        try:
            if use_concurrency_control:
                while not _concurrency_manager.try_submit_task():
                    status = _concurrency_manager.get_status()
                    logger.info(f"⏳ 并发控制：已提交 {status['submitted']}，运行中 {status['running']}，排队中 {status['queued']}，等待任务完成...")
                    time.sleep(2)
            
            if seed is None:
                seed = random.randint(0, 2**32 - 1)

            negative_prompt = "色调艳丽，过曝，细节模糊不清，画面，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，杂乱的背景"

            request_data = {
                "webappId": self.webapp_id,
                "apiKey": self.api_key,
                "nodeInfoList": [
                    {
                        "nodeId": "58",
                        "fieldName": "height",
                        "fieldValue": str(height),
                        "description": "height"
                    },
                    {
                        "nodeId": "58",
                        "fieldName": "width",
                        "fieldValue": str(width),
                        "description": "width"
                    },
                    {
                        "nodeId": "3",
                        "fieldName": "seed",
                        "fieldValue": str(seed),
                        "description": "seed"
                    },
                    {
                        "nodeId": "6",
                        "fieldName": "text",
                        "fieldValue": prompt,
                        "description": "text"
                    },
                    {
                        "nodeId": "7",
                        "fieldName": "text",
                        "fieldValue": negative_prompt,
                        "description": "text"
                    }
                ]
            }
            
            logger.info("=== RunningHub T2I生成请求数据格式 ===")
            logger.info(f"URL: {self.run_url}")
            logger.info(f"Headers: {self.headers}")
            logger.info(f"Payload: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
            logger.info("=" * 50)
            
            response = requests.post(
                url=self.run_url, 
                headers=self.headers, 
                data=json.dumps(request_data)
            )
            response.raise_for_status()
            result = response.json()
            
            logger.info("=== 任务提交结果 ===")
            logger.info(f"响应: {result}")
            
            if result.get('code') == 0:
                task_data = result["data"]
                task_id = task_data["taskId"]
                logger.info(f"✅ 任务提交成功! 任务ID: {task_id}")
                
                try:
                    result = self._poll_task_status(task_id, timeout or RUNNINGHUB_API_CONFIG["generate_timeout"], use_concurrency_control)
                    if result:
                        if use_concurrency_control:
                            _concurrency_manager.task_finished()
                        return result
                    else:
                        if use_concurrency_control:
                            _concurrency_manager.task_finished()
                        return None
                except Exception as e:
                    if use_concurrency_control:
                        _concurrency_manager.task_finished()
                    raise e
            else:
                error_msg = result.get('msg', '未知错误')
                logger.error(f"❌ 任务提交失败: {error_msg}")
                if use_concurrency_control:
                    _concurrency_manager.task_finished()
                return None
                
        except Exception as e:
            logger.error(f"图片生成失败: {e}")
            if use_concurrency_control:
                _concurrency_manager.task_finished()
            return None
    
    def _poll_task_status(self, task_id: str, timeout: int, use_concurrency_control: bool = True) -> Optional[Dict[str, Any]]:
        start_time = time.time()
        while True:
            if (time.time() - start_time) > timeout:
                logger.error(f"{timeout}秒任务超时，已退出轮询")
                return None
            
            try:
                status_data = {
                    "apiKey": self.api_key,
                    "taskId": task_id
                }
                
                response = requests.post(
                    url=self.status_url, 
                    headers=self.headers, 
                    data=json.dumps(status_data)
                )
                response.raise_for_status()
                status_result = response.json()
                
                logger.info(f"🔄 任务状态查询 (任务ID: {task_id}): {status_result}")
                
                if status_result.get('code') != 0:
                    logger.error(f"❌ 任务状态查询失败: {status_result.get('msg', '未知错误')}")
                    return None
                
                task_status_data = status_result.get('data', {})
                task_status = task_status_data.get('taskStatus')

                if task_status == 'SUCCESS':
                    logger.info("✅ 任务完成，获取结果...")
                    return self._get_task_outputs(task_id)
                elif task_status in ['FAIL', 'CANCEL']:
                    logger.error(f"❌ 任务失败或被取消: {task_status}")
                    return None
                else: # QUEUED, RUNNING
                    logger.info(f"⏳ 任务状态: {task_status}，等待 {self.poll_interval} 秒...")
                    time.sleep(self.poll_interval)
                
            except Exception as e:
                logger.error(f"查询任务状态失败: {e}")
                time.sleep(self.poll_interval)
    
    def _get_task_outputs(self, task_id: str) -> Optional[Dict[str, Any]]:
        try:
            outputs_data = {
                "apiKey": self.api_key,
                "taskId": task_id
            }
            
            response = requests.post(
                url=self.outputs_url,
                headers=self.headers,
                data=json.dumps(outputs_data)
            )
            response.raise_for_status()
            outputs_result = response.json()
            
            logger.info("=== 任务输出结果 ===")
            logger.info(f"响应: {outputs_result}")
            
            if outputs_result.get('code') != 0:
                logger.error(f"❌ 获取任务输出失败: {outputs_result.get('msg', '未知错误')}")
                return None
            
            data = outputs_result.get('data', [])
            if data:
                # Assuming the first output is the one we want.
                # A more robust solution would be to check node ID if available.
                for item in data:
                    if 'fileUrl' in item:
                         return {
                            'code': 0,
                            'data': {
                                'images': [{'imageUrl': item.get('fileUrl')}]
                            }
                        }
            
            logger.error("❌ 未获取到输出结果")
            return None
                
        except Exception as e:
            logger.error(f"获取任务输出失败: {e}")
            return None

    def _download_image(self, image_url: str, output_path: str) -> Optional[str]:
        try:
            response = requests.get(image_url, timeout=60)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"图片下载完成: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"下载图片失败: {e}")
            return None

    def text_to_image(self, 
                      prompt: str,
                      output_path: str,
                      width: int = 720,
                      height: int = 1280,
                      seed: Optional[int] = None) -> Optional[str]:
        """
        生成并下载单张图片
        """
        try:
            if os.path.exists(output_path):
                logger.info(f"文件已存在，跳过生成: {output_path}")
                return output_path

            result = self.generate_image(
                prompt=prompt,
                width=width,
                height=height,
                seed=seed
            )
            
            if not result or result.get('code') != 0:
                logger.error("生成失败，未获取到结果")
                return None
            
            images = result.get('data', {}).get('images', [])
            if not images:
                logger.error("生成失败，未获取到图片URL")
                return None
            
            image_url = images[0].get('imageUrl')
            if not image_url:
                logger.error("生成失败，图片URL为空")
                return None

            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            return self._download_image(image_url, output_path)
            
        except Exception as e:
            logger.error(f"生成图片失败: {e}")
            return None

def create_qwen_t2i_rh(api_key: Optional[str] = None) -> QwenImageT2IRH:
    return QwenImageT2IRH(api_key=api_key)


if __name__ == "__main__":
    generator = create_qwen_t2i_rh()
    
    test_prompt = "超高清，高质量，8K,HDR ,干净的修仙俯视大全景，画面中心字体设计“逍遥天地，共赴同游”富有创意，创意手绘毛笔字体，文字排版，高级艺术，标题周围有云雾，将字体抽象变形，创造出独特的节奏和动感，"
    output_file = "qwen_t2i_test.jpg"

    print(f"正在生成图片，提示词: {test_prompt}")
    
    saved_path = generator.text_to_image(
        prompt=test_prompt,
        output_path=output_file,
        width=720,
        height=1280
    )
    
    if saved_path:
        print(f"图片生成成功，已保存至: {saved_path}")
    else:
        print("图片生成失败。")
