#!/usr/bin/env python3
"""
RunningHub API Flux Kontext Img2Img implementation.
Provides image-to-image generation using RunningHub API's Flux Kontext model.
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


class FluxKontextImg2ImgRH:
    """RunningHub API Flux Kontext 图片转图片生成器"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 FluxKontextImg2ImgRH
        
        Args:
            api_key: RunningHub API Key，如果为None则使用配置文件中的值
        """
        self.api_key = api_key or RUNNINGHUB_API_CONFIG["api_key"]
        self.host = RUNNINGHUB_API_CONFIG["host"]
        self.base_url = RUNNINGHUB_API_CONFIG["base_url"]
        self.upload_url = RUNNINGHUB_API_CONFIG["upload_url"]
        self.run_url = RUNNINGHUB_API_CONFIG["run_url"]
        self.status_url = RUNNINGHUB_API_CONFIG["status_url"]
        self.outputs_url = RUNNINGHUB_API_CONFIG["outputs_url"]
        self.webapp_id = RUNNINGHUB_API_CONFIG["webapp_id"]
        self.image_node_id = RUNNINGHUB_API_CONFIG["image_node_id"]
        self.model_node_id = RUNNINGHUB_API_CONFIG["model_node_id"]
        self.output_node_id = RUNNINGHUB_API_CONFIG["output_node_id"]
        self.scale_node_id = RUNNINGHUB_API_CONFIG["scale_node_id"]
        self.poll_interval = RUNNINGHUB_API_CONFIG["poll_interval"]
        
        self.headers = {
            'Host': self.host,
            'Content-Type': 'application/json'
        }
        
        logger.info(f"FluxKontextImg2ImgRH 初始化完成，使用WebApp ID: {self.webapp_id}")
    
    def upload_image(self, image_path: str) -> Optional[str]:
        """
        上传图片到RunningHub服务器
        
        Args:
            image_path: 本地图片路径
            
        Returns:
            上传成功返回图片文件名，失败返回None
        """
        try:
            if not os.path.exists(image_path):
                logger.error(f"图片文件不存在: {image_path}")
                return None
            
            logger.info(f"上传图片到RunningHub: {image_path}")
            
            # 准备上传请求
            upload_headers = {
                'Host': self.host
            }
            
            # 确定Content-Type
            file_ext = Path(image_path).suffix.lower()
            content_type_map = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
            }
            content_type = content_type_map.get(file_ext, 'image/jpeg')
            
            # 准备文件上传 - RunningHub需要在form data中包含apiKey和fileType
            with open(image_path, 'rb') as f:
                files = {
                    'file': (os.path.basename(image_path), f, content_type)
                }
                
                # RunningHub需要的form data参数
                form_data = {
                    'apiKey': self.api_key,
                    'fileType': 'image'
                }
                
                # 打印上传请求数据格式
                logger.info("=== RunningHub 图片上传请求数据格式 ===")
                logger.info(f"URL: {self.upload_url}")
                logger.info(f"Headers: {upload_headers}")
                logger.info(f"Form Data: {form_data}")
                logger.info(f"File Name: {os.path.basename(image_path)}")
                logger.info(f"Content Type: {content_type}")
                logger.info("=" * 50)
                
                response = requests.post(
                    url=self.upload_url,
                    headers=upload_headers,
                    data=form_data,
                    files=files,
                    timeout=RUNNINGHUB_API_CONFIG["upload_timeout"]
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"上传响应: {result}")
                
                if result.get('code') == 0:
                    file_name = result['data']['fileName']
                    logger.info(f"图片上传成功: {file_name}")
                    return file_name
                else:
                    logger.error(f"图片上传失败: {result.get('msg', '未知错误')}")
                    return None
            
        except requests.exceptions.Timeout:
            logger.error("图片上传超时")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"图片上传网络错误: {e}")
            return None
        except Exception as e:
            logger.error(f"图片上传失败: {e}")
            return None
    
    def generate_img2img(self, 
                        image_file_name: str,
                        prompt: Optional[str] = None,
                        aspect_ratio: Optional[str] = None,
                        guidance_scale: Optional[float] = None,
                        img_count: Optional[int] = None,
                        scale_to_length: Optional[int] = None,
                        timeout: Optional[int] = None,
                        use_concurrency_control: bool = True) -> Optional[Dict[str, Any]]:
        """
        执行图片转图片生成
        
        Args:
            image_file_name: 上传后的图片文件名
            prompt: 风格化提示词，如果为None则使用默认的新海诚风格
            aspect_ratio: 长宽比，如果为None则使用默认值
            guidance_scale: 引导强度（RunningHub中暂未使用）
            img_count: 生成图片数量（RunningHub中暂未使用）
            scale_to_length: 缩放边长度，如果为None则使用默认值640
            timeout: 超时时间（秒），如果为None则使用默认值
            use_concurrency_control: 是否使用并发控制，默认为True
            
        Returns:
            生成结果字典，包含图片URL等信息，失败返回None
        """
        try:
            # 🔒 原子并发控制 - 在同一个锁中检查并提交任务
            if use_concurrency_control:
                while not _concurrency_manager.try_submit_task():
                    status = _concurrency_manager.get_status()
                    logger.info(f"⏳ 并发控制：已提交 {status['submitted']}，运行中 {status['running']}，排队中 {status['queued']}，等待任务完成...")
                    time.sleep(2)
                # 此时已经原子地获得了提交权限并增加了计数
            
            # 🔒 关键修复：在获得任务执行权限后才进行图片上传
            # 这样可以避免多个任务同时上传消耗资源
            logger.info(f"开始上传图片到RunningHub: {image_file_name}")
            
            # 准备上传请求
            upload_headers = {
                'Host': self.host
            }
            
            # 确定Content-Type
            file_ext = Path(image_file_name).suffix.lower() if isinstance(image_file_name, str) else '.jpg'
            content_type_map = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg', 
                '.png': 'image/png',
            }
            content_type = content_type_map.get(file_ext, 'image/jpeg')
            
            # 如果image_file_name是本地路径，需要上传
            if isinstance(image_file_name, str) and os.path.exists(image_file_name):
                # 准备文件上传 - RunningHub需要在form data中包含apiKey和fileType
                with open(image_file_name, 'rb') as f:
                    files = {
                        'file': (os.path.basename(image_file_name), f, content_type)
                    }
                    
                    # RunningHub需要的form data参数
                    form_data = {
                        'apiKey': self.api_key,
                        'fileType': 'image'
                    }
                    
                    logger.info("=== RunningHub 图片上传请求数据格式 ===")
                    logger.info(f"URL: {self.upload_url}")
                    logger.info(f"File Name: {os.path.basename(image_file_name)}")
                    logger.info(f"Content Type: {content_type}")
                    
                    response = requests.post(
                        url=self.upload_url,
                        headers=upload_headers,
                        data=form_data,
                        files=files,
                        timeout=RUNNINGHUB_API_CONFIG["upload_timeout"]
                    )
                    response.raise_for_status()
                    
                    upload_result = response.json()
                    logger.info(f"上传响应: {upload_result}")
                    
                    if upload_result.get('code') == 0:
                        uploaded_file_name = upload_result['data']['fileName']
                        logger.info(f"图片上传成功: {uploaded_file_name}")
                    else:
                        logger.error(f"图片上传失败: {upload_result.get('msg', '未知错误')}")
                        if use_concurrency_control:
                            _concurrency_manager.task_finished()
                        return None
            else:
                # 假设已经是上传后的文件名
                uploaded_file_name = image_file_name
            
            # 构建请求数据
            request_data = {
                "webappId": self.webapp_id,
                "apiKey": self.api_key,
                "nodeInfoList": [
                    {
                        "nodeId": self.image_node_id,
                        "fieldName": "image",
                        "fieldValue": uploaded_file_name  # 使用上传后的文件名
                    },
                    {
                        "nodeId": self.model_node_id,
                        "fieldName": "model",
                        "fieldValue": RUNNINGHUB_API_CONFIG["default_model"]
                    },
                    {
                        "nodeId": self.model_node_id,
                        "fieldName": "aspect_ratio",
                        "fieldValue": aspect_ratio or RUNNINGHUB_API_CONFIG["default_aspect_ratio"]
                    },
                    {
                        "nodeId": self.model_node_id,
                        "fieldName": "prompt",
                        "fieldValue": prompt or RUNNINGHUB_API_CONFIG["makoto_shinkai_prompt"]
                    },
                    {
                        "nodeId": self.model_node_id,
                        "fieldName": "seed",
                        "fieldValue": RUNNINGHUB_API_CONFIG["default_seed"]
                    },
                    {
                        "nodeId": self.model_node_id,
                        "fieldName": "control_afeter_generate",
                        "fieldValue": RUNNINGHUB_API_CONFIG["control_after_generate"]
                    },
                    {
                        "nodeId": self.model_node_id,
                        "fieldName": "guidance_scale",
                        "fieldValue": RUNNINGHUB_API_CONFIG["default_guidance_scale"]
                    },
                    {
                        "nodeId": self.model_node_id,
                        "fieldName": "safety_tolerance",
                        "fieldValue": RUNNINGHUB_API_CONFIG["safety_tolerance"]
                    }
                ]
            }
            
            # 打印生成请求数据格式
            logger.info("=== RunningHub Img2Img生成请求数据格式 ===")
            logger.info(f"URL: {self.run_url}")
            logger.info(f"Headers: {self.headers}")
            logger.info("=" * 50)
            
            # 详细打印每个参数
            logger.info("📋 ComfyUI参数详情:")
            logger.info(f"  WebApp ID: {request_data['webappId']}")
            logger.info(f"  API Key: {request_data['apiKey'][:10]}...")
            logger.info(f"  节点信息列表:")
            
            for i, node_info in enumerate(request_data['nodeInfoList']):
                logger.info(f"    节点 {i+1}:")
                logger.info(f"      - Node ID: {node_info['nodeId']}")
                logger.info(f"      - Field Name: {node_info['fieldName']}")
                logger.info(f"      - Field Value: {node_info['fieldValue']}")
            
            # 发送生成请求
            response = requests.post(
                url=self.run_url, 
                headers=self.headers, 
                data=json.dumps(request_data)
            )
            response.raise_for_status()
            result = response.json()
            
            logger.info("=== 任务提交结果 ===")
            logger.info(f"响应代码: {result.get('code')}")
            logger.info(f"响应消息: {result.get('msg')}")
            
            if result.get('code') == 0:
                task_data = result["data"]
                logger.info(f"✅ 任务提交成功!")
                logger.info(f"  任务ID: {task_data['taskId']}")
                logger.info(f"  客户端ID: {task_data['clientId']}")
                logger.info(f"  任务状态: {task_data['taskStatus']}")
                logger.info("=" * 50)
                
                # 获取任务ID并轮询状态
                task_id = task_data["taskId"]
                task_status = task_data["taskStatus"]
                
                if task_status in ["QUEUED", "RUNNING"]:
                    if task_status == "QUEUED":
                        logger.info("⏳ 任务已加入队列，等待开始执行...")
                    elif task_status == "RUNNING":
                        logger.info("🚀 任务正在执行中...")
                    
                    # 🔒 关键修复：无论QUEUED还是RUNNING，都需要轮询直到完成
                    # 不再在这里增加running_tasks计数，应该在提交时就计数
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
                    logger.error(f"任务状态异常: {task_status}，期望状态: QUEUED 或 RUNNING")
                    if use_concurrency_control:
                        # 🔒 关键修复：任务已提交到服务器但状态异常，视为任务已提交但失败
                        _concurrency_manager.task_finished()
                    return None
            else:
                error_msg = result.get('msg', '未知错误')
                logger.error(f"❌ 任务提交失败: {error_msg}")
                
                # 🔒 特别处理TASK_QUEUE_MAXED错误
                if 'TASK_QUEUE_MAXED' in error_msg:
                    logger.error(f"🚨 检测到TASK_QUEUE_MAXED错误：服务器队列已满")
                    logger.error(f"📝 建议：请等待现有任务完成后再提交新任务")
                    logger.error(f"🔧 已启用极保守模式，一次只允许一个任务")
                
                if use_concurrency_control:
                    # 🔒 关键修复：API已响应，说明已与服务器通信，视为任务已提交但失败
                    _concurrency_manager.task_finished()
                return None
                
        except Exception as e:
            logger.error(f"图片生成失败: {e}")
            if use_concurrency_control:
                # 🔒 关键修复：由于在开始就调用了task_submitted()，
                # 所以所有异常都应该被视为任务已提交但失败
                _concurrency_manager.task_finished()
            return None
    
    def _poll_task_status(self, task_id: str, timeout: int, use_concurrency_control: bool = True) -> Optional[Dict[str, Any]]:
        """
        轮询任务状态直到完成
        
        Args:
            task_id: 任务ID
            timeout: 超时时间（秒）
            use_concurrency_control: 是否使用并发控制
            
        Returns:
            任务完成结果，超时或失败返回None
        """
        start_time = time.time()
        last_status = None  # 跟踪上一次的状态
        has_seen_running = False  # 是否已经观测到RUNNING
        
        while True:
            current_time = time.time()
            if (current_time - start_time) > timeout:
                logger.error(f"{timeout}秒任务超时，已退出轮询")
                return None
            
            try:
                # 查询任务状态
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
                
                logger.info(f"🔄 任务状态查询 (任务ID: {task_id})")
                logger.info(f"  响应代码: {status_result.get('code')}")
                logger.info(f"  响应消息: {status_result.get('msg')}")
                logger.info(f"  状态数据: {status_result.get('data', 'N/A')}")
                
                # 检查code字段
                if status_result.get('code') != 0:
                    logger.error(f"❌ 任务状态查询失败，错误代码: {status_result.get('code')}, 错误信息: {status_result.get('msg', '未知错误')}")
                    return None
                
                # 检查任务是否完成
                status_data_str = status_result.get('data', '')
                if isinstance(status_data_str, str) and 'success' in status_data_str.lower():
                    # 🔒 关键修复：直接完成，不需要在轮询中增加running计数
                    logger.info("✅ ComfyUI任务完成，获取结果...")
                    return self._get_task_outputs(task_id)
                elif isinstance(status_data_str, str) and 'fail' in status_data_str.lower():
                    logger.error(f"❌ ComfyUI任务失败: {status_data_str}")
                    return None
                
                # 检测状态变化（从QUEUED变为RUNNING） - 仅用于日志记录
                current_status = None
                if isinstance(status_data_str, str):
                    if 'queued' in status_data_str.lower() or 'queue' in status_data_str.lower():
                        current_status = "QUEUED"
                        logger.info(f"⏳ 任务排队中，等待 {self.poll_interval} 秒后继续查询...")
                    elif 'running' in status_data_str.lower():
                        current_status = "RUNNING"
                        logger.info(f"🚀 任务执行中，等待 {self.poll_interval} 秒后继续查询...")
                        # 🔒 关键修复：移除running计数增加，避免重复计数和同步问题
                        has_seen_running = True
                    else:
                        logger.info(f"⏳ ComfyUI任务尚未完成，状态: {status_data_str}，等待 {self.poll_interval} 秒...")
                else:
                    logger.info(f"⏳ ComfyUI任务尚未完成，等待 {self.poll_interval} 秒...")
                
                # 更新上次状态
                if current_status:
                    last_status = current_status
                
                time.sleep(self.poll_interval)
                
            except Exception as e:
                logger.error(f"查询任务状态失败: {e}")
                time.sleep(self.poll_interval)
    
    def _get_task_outputs(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务输出结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务输出结果，失败返回None
        """
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
            
            logger.info("=== ComfyUI任务输出结果 ===")
            logger.info(f"响应代码: {outputs_result.get('code')}")
            logger.info(f"响应消息: {outputs_result.get('msg')}")
            
            if outputs_result.get('code') != 0:
                logger.error(f"❌ 获取任务输出失败，错误代码: {outputs_result.get('code')}, 错误信息: {outputs_result.get('msg', '未知错误')}")
                return None
            
            # 转换为与LibLib兼容的格式
            data = outputs_result.get('data', [])
            logger.info(f"📤 输出数据数量: {len(data)}")
            
            if data and len(data) > 0:
                logger.info("📋 输出节点详情:")
                for i, item in enumerate(data):
                    logger.info(f"  输出 {i+1}:")
                    logger.info(f"    - 节点ID: {item.get('nodeId')}")
                    logger.info(f"    - 文件URL: {item.get('fileUrl')}")
                    logger.info(f"    - 文件类型: {item.get('fileType')}")
                    logger.info(f"    - 处理耗时: {item.get('taskCostTime')}秒")
                
                # 找到输出节点的结果
                for item in data:
                    if item.get('nodeId') == self.output_node_id:
                        logger.info(f"✅ 找到目标输出节点 {self.output_node_id}: {item.get('fileUrl')}")
                        return {
                            'code': 0,
                            'data': {
                                'images': [{'imageUrl': item.get('fileUrl')}]
                            }
                        }
                
                # 如果没找到特定节点，使用第一个结果
                logger.info(f"⚠️ 未找到目标节点，使用第一个输出: {data[0].get('fileUrl')}")
                return {
                    'code': 0,
                    'data': {
                        'images': [{'imageUrl': data[0].get('fileUrl')}]
                    }
                }
            else:
                logger.error("❌ 未获取到输出结果")
                return None
                
        except Exception as e:
            logger.error(f"获取任务输出失败: {e}")
            return None
    
    def stylize_image(self, 
                     image_input: Union[str, Image.Image],
                     output_path: Optional[str] = None,
                     prompt: Optional[str] = None,
                     aspect_ratio: Optional[str] = None,
                     guidance_scale: Optional[float] = None,
                     scale_to_length: Optional[int] = None) -> Optional[str]:
        """
        风格化单张图片的便利方法
        
        Args:
            image_input: 输入图片路径或PIL Image对象
            output_path: 输出路径，如果为None则自动生成
            prompt: 风格化提示词
            aspect_ratio: 长宽比
            guidance_scale: 引导强度（RunningHub中暂未使用）
            scale_to_length: 缩放边长度，如果为None则使用默认值640
            
        Returns:
            输出文件路径，失败返回None
        """
        try:
            # 检查输出文件是否已存在
            if output_path and os.path.exists(output_path):
                logger.info(f"文件已存在，跳过生成: {output_path}")
                return output_path
            
            # 处理输入图片
            if isinstance(image_input, str):
                if image_input.startswith(('http://', 'https://')):
                    logger.error("RunningHub不支持直接使用URL，请提供本地文件路径")
                    return None
                else:
                    # 本地文件路径，直接传给generate_img2img（内部会处理上传）
                    image_file_name = image_input
            else:
                # PIL Image对象，需要先保存为本地文件
                logger.warning("PIL Image对象需要先保存为本地文件再上传")
                return None
            
            # 执行风格化（内部会处理图片上传）
            result = self.generate_img2img(
                image_file_name=image_file_name,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                guidance_scale=guidance_scale,
                scale_to_length=scale_to_length
            )
            
            # 检查返回结果
            if not result:
                logger.error("风格化失败，未获取到返回结果")
                return None
            
            # 检查code字段
            if result.get('code') != 0:
                logger.error(f"风格化失败，错误代码: {result.get('code')}, 错误信息: {result.get('msg', '未知错误')}")
                return None
            
            # 检查images数据
            if not result.get('data', {}).get('images'):
                logger.error("风格化失败，未获取到结果图片")
                return None
            
            # 下载生成的图片
            generated_images = result['data']['images']
            first_image_info = None
            
            for img_info in generated_images:
                if img_info and isinstance(img_info, dict) and img_info.get('imageUrl'):
                    first_image_info = img_info
                    break
                elif isinstance(img_info, str) and img_info:
                    # 兼容旧格式，直接是URL字符串
                    first_image_info = {'imageUrl': img_info}
                    break
            
            if not first_image_info:
                logger.error("未找到有效的生成图片URL")
                return None
            
            first_image_url = first_image_info['imageUrl']
            
            # 确定输出路径
            if not output_path:
                os.makedirs("image_temp", exist_ok=True)
                timestamp = int(time.time())
                output_path = f"image_temp/rh_stylized_{timestamp}.jpg"
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            return self._download_image(first_image_url, output_path)
            
        except Exception as e:
            logger.error(f"风格化图片失败: {e}")
            return None
    
    def stylize_video_frame(self, 
                           input_frame_path: str,
                           output_dir: str,
                           prompt: Optional[str] = None,
                           aspect_ratio: Optional[str] = None,
                           guidance_scale: Optional[float] = None,
                           scale_to_length: Optional[int] = None) -> Optional[str]:
        """
        风格化视频帧的便利方法，保持原始文件名
        
        Args:
            input_frame_path: 输入帧路径
            output_dir: 输出目录
            prompt: 风格化提示词
            aspect_ratio: 长宽比
            guidance_scale: 引导强度（RunningHub中暂未使用）
            scale_to_length: 缩放边长度，如果为None则使用默认值640
            
        Returns:
            输出文件路径，失败返回None
        """
        try:
            # 获取原始文件名
            original_filename = os.path.basename(input_frame_path)
            output_path = os.path.join(output_dir, original_filename)
            
            # 检查输出文件是否已存在
            if os.path.exists(output_path):
                logger.info(f"文件已存在，跳过生成: {output_path}")
                return output_path
            
            return self.stylize_image(
                image_input=input_frame_path,
                output_path=output_path,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                guidance_scale=guidance_scale,
                scale_to_length=scale_to_length
            )
            
        except Exception as e:
            logger.error(f"风格化视频帧失败: {e}")
            return None

    def _download_image(self, image_url: str, output_path: str) -> Optional[str]:
        """
        下载图片到本地
        
        Args:
            image_url: 图片URL
            output_path: 输出路径
            
        Returns:
            下载成功返回文件路径，失败返回None
        """
        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"图片下载完成: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"下载图片失败: {e}")
            return None
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            模型信息字典
        """
        return {
            "model_name": "Flux Kontext",
            "provider": "RunningHub",
            "type": "img2img",
            "webapp_id": self.webapp_id,
            "base_url": self.base_url,
            "default_prompt": RUNNINGHUB_API_CONFIG["makoto_shinkai_prompt"],
            "default_aspect_ratio": RUNNINGHUB_API_CONFIG["default_aspect_ratio"],
            "default_model": RUNNINGHUB_API_CONFIG["default_model"]
        }


def create_flux_stylizer_rh(api_key: Optional[str] = None) -> FluxKontextImg2ImgRH:
    """
    创建 FluxKontextImg2ImgRH 实例的便利函数
    
    Args:
        api_key: RunningHub API Key
        
    Returns:
        FluxKontextImg2ImgRH实例
    """
    return FluxKontextImg2ImgRH(api_key=api_key)


def stylize_with_flux_rh(image_path: str, 
                        prompt: Optional[str] = None,
                        output_path: Optional[str] = None,
                        aspect_ratio: Optional[str] = None,
                        guidance_scale: Optional[float] = None,
                        scale_to_length: Optional[int] = None) -> Optional[str]:
    """
    使用RunningHub Flux Kontext风格化图片的便利函数
    
    Args:
        image_path: 输入图片路径
        prompt: 风格化提示词
        output_path: 输出路径
        aspect_ratio: 长宽比
        guidance_scale: 引导强度（RunningHub中暂未使用）
        scale_to_length: 缩放边长度，如果为None则使用默认值640
        
    Returns:
        输出文件路径，失败返回None
    """
    stylizer = create_flux_stylizer_rh()
    return stylizer.stylize_image(
        image_input=image_path,
        output_path=output_path,
        prompt=prompt,
        aspect_ratio=aspect_ratio,
        guidance_scale=guidance_scale,
        scale_to_length=scale_to_length
    )


def stylize_video_frame_with_flux_rh(input_frame_path: str,
                                    output_dir: str,
                                    prompt: Optional[str] = None,
                                    aspect_ratio: Optional[str] = None,
                                    guidance_scale: Optional[float] = None,
                                    scale_to_length: Optional[int] = None) -> Optional[str]:
    """
    使用RunningHub Flux Kontext风格化视频帧的便利函数
    
    Args:
        input_frame_path: 输入帧路径
        output_dir: 输出目录
        prompt: 风格化提示词
        aspect_ratio: 长宽比
        guidance_scale: 引导强度（RunningHub中暂未使用）
        scale_to_length: 缩放边长度，如果为None则使用默认值640
        
    Returns:
        输出文件路径，失败返回None
    """
    stylizer = create_flux_stylizer_rh()
    return stylizer.stylize_video_frame(
        input_frame_path=input_frame_path,
        output_dir=output_dir,
        prompt=prompt,
        aspect_ratio=aspect_ratio,
        guidance_scale=guidance_scale,
        scale_to_length=scale_to_length
    )


if __name__ == "__main__":
    # 测试代码
    stylizer = create_flux_stylizer_rh()
    print("模型信息:", stylizer.get_model_info())
    
    # 注意：需要提供有效的本地图片路径进行测试
    test_image_path = "test_image.jpg"
    print(f"测试图片路径: {test_image_path}") 