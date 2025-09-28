#!/usr/bin/env python3
"""
RunningHub API Wan Vace Img2Video implementation.
Provides image-to-video generation using RunningHub API's Wan Vace model.
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
_video_concurrency_manager = RunningHubConcurrencyManager(max_concurrent=3, conservative_threshold=1)


class WanVaceImg2VideoRH:
    """RunningHub API Wan Vace 图片转视频生成器"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 WanVaceImg2VideoRH
        
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
        
        # Wan Vace 视频生成模型的特定配置 (v2.2)
        self.webapp_id = "1956200271837843458"
        self.first_frame_node_id = "21"   # 首帧节点ID
        self.last_frame_node_id = "20"    # 尾帧节点ID
        self.prompt_node_id = "19"        # 提示词节点ID
        self.duration_node_id = "26"      # 时长节点ID
        self.resolution_node_id = "32"    # 分辨率节点ID
        self.prompt_mode_node_id = "38"   # 提示词模式节点ID（1=手写，2=自动）
        
        # Video enhancement model configuration
        self.video_enhance_webapp_id = "1903013826319519745"  # 视频增强WebApp ID
        self.video_load_node_id = "38"    # 视频加载节点ID
        self.resolution_output_node_id = "132"  # 输出分辨率节点ID
        self.interpolation_node_id = "110"  # 插帧节点ID
        self.interpolation_rate_node_id = "137"  # 插帧倍率节点ID
        
        self.poll_interval = RUNNINGHUB_API_CONFIG["poll_interval"]
        
        self.headers = {
            'Host': self.host,
            'Content-Type': 'application/json'
        }
        
        logger.info(f"WanVaceImg2VideoRH 初始化完成，使用WebApp ID: {self.webapp_id}")
    
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
    
    def upload_video(self, video_path: str) -> Optional[str]:
        """
        上传视频到RunningHub服务器
        
        Args:
            video_path: 本地视频路径
            
        Returns:
            上传成功返回视频文件名，失败返回None
        """
        try:
            if not os.path.exists(video_path):
                logger.error(f"视频文件不存在: {video_path}")
                return None
            
            logger.info(f"上传视频到RunningHub: {video_path}")
            
            # 准备上传请求
            upload_headers = {
                'Host': self.host
            }
            
            # 确定Content-Type
            file_ext = Path(video_path).suffix.lower()
            content_type_map = {
                '.mp4': 'video/mp4',
                '.mov': 'video/quicktime',
                '.avi': 'video/x-msvideo',
                '.mkv': 'video/x-matroska',
            }
            content_type = content_type_map.get(file_ext, 'video/mp4')
            
            # 准备文件上传 - RunningHub需要在form data中包含apiKey和fileType
            with open(video_path, 'rb') as f:
                files = {
                    'file': (os.path.basename(video_path), f, content_type)
                }
                
                # RunningHub需要的form data参数
                form_data = {
                    'apiKey': self.api_key,
                    'fileType': 'video'
                }
                
                # 打印上传请求数据格式
                logger.info("=== RunningHub 视频上传请求数据格式 ===")
                logger.info(f"URL: {self.upload_url}")
                logger.info(f"Headers: {upload_headers}")
                logger.info(f"Form Data: {form_data}")
                logger.info(f"File Name: {os.path.basename(video_path)}")
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
                    logger.info(f"视频上传成功: {file_name}")
                    return file_name
                else:
                    logger.error(f"视频上传失败: {result.get('msg', '未知错误')}")
                    return None
            
        except requests.exceptions.Timeout:
            logger.error("视频上传超时")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"视频上传网络错误: {e}")
            return None
        except Exception as e:
            logger.error(f"视频上传失败: {e}")
            return None
    
    def generate_img2video(self, 
                          first_frame_file_name: str,
                          last_frame_file_name: str,
                          prompt: str,
                          duration: int = 5,
                          resolution: int = 720,
                          use_smart_prompt: bool = True,
                          timeout: Optional[int] = None,
                          use_concurrency_control: bool = True,
                          max_retries: int = 3,
                          retry_delay: int = 5) -> Optional[Dict[str, Any]]:
        """
        执行图片转视频生成
        
        Args:
            first_frame_file_name: 首帧图片文件名（已上传）
            last_frame_file_name: 尾帧图片文件名（已上传）
            prompt: 视频生成提示词
            duration: 视频时长（秒），默认5秒
            resolution: 分辨率，默认720
            use_smart_prompt: 是否使用智能提示词（True=手写提示词，False=自动提示词），默认True
            timeout: 超时时间（秒），如果为None则使用默认值
            use_concurrency_control: 是否使用并发控制，默认为True
            max_retries: 最大重试次数，默认3次
            retry_delay: 重试间隔时间（秒），默认5秒
            
        Returns:
            生成结果字典，包含视频URL等信息，失败返回None
        """
        # 重试逻辑
        for attempt in range(max_retries + 1):  # +1 因为包含初始尝试
            try:
                if attempt > 0:
                    logger.info(f"🔄 开始第 {attempt} 次重试（总共最多 {max_retries} 次重试）...")
                    time.sleep(retry_delay)
                
                # 🔒 原子并发控制 - 在同一个锁中检查并提交任务
                if use_concurrency_control:
                    while not _video_concurrency_manager.try_submit_task():
                        status = _video_concurrency_manager.get_status()
                        logger.info(f"⏳ 并发控制：已提交 {status['submitted']}，运行中 {status['running']}，排队中 {status['queued']}，等待任务完成...")
                        time.sleep(2)
                    # 此时已经原子地获得了提交权限并增加了计数
                
                # 🔒 关键修复：参数已经是上传后的文件名，不需要重新上传
                # first_frame_file_name 和 last_frame_file_name 已经是上传后返回的文件名
                
                # 构建请求数据 (v2.2)
                request_data = {
                    "webappId": self.webapp_id,
                    "apiKey": self.api_key,
                    "nodeInfoList": [
                        {
                            "nodeId": self.first_frame_node_id,
                            "fieldName": "image",
                            "fieldValue": first_frame_file_name,
                            "description": "首帧"
                        },
                        {
                            "nodeId": self.last_frame_node_id,
                            "fieldName": "image",
                            "fieldValue": last_frame_file_name,
                            "description": "尾帧"
                        },
                        {
                            "nodeId": self.duration_node_id,
                            "fieldName": "value",
                            "fieldValue": str(duration),
                            "description": "时长"
                        },
                        {
                            "nodeId": self.resolution_node_id,
                            "fieldName": "value",
                            "fieldValue": str(resolution),
                            "description": "分辨率"
                        },
                        {
                            "nodeId": self.prompt_mode_node_id,
                            "fieldName": "value",
                            "fieldValue": "1" if use_smart_prompt else "2",
                            "description": "可选提示词（1 手写提示词， 2自动提示词）"
                        },
                        {
                            "nodeId": self.prompt_node_id,
                            "fieldName": "text",
                            "fieldValue": f"turn this image into a makoto shinkai style,a Japanese anime aesthetics, {prompt}" if use_smart_prompt else "",
                            "description": "提示词"
                        }
                    ]
                }
                
                # 打印生成请求数据格式
                if attempt == 0:  # 只在第一次尝试时打印详细信息
                    logger.info("=== RunningHub Img2Video生成请求数据格式 ===")
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
                        logger.info(f"      - Description: {node_info.get('description', 'N/A')}")
                    
                    logger.info("=" * 50)
                    logger.info(f"🎬 视频生成参数摘要 (v2.2):")
                    logger.info(f"  首帧图片: {request_data['nodeInfoList'][0]['fieldValue']}")
                    logger.info(f"  尾帧图片: {request_data['nodeInfoList'][1]['fieldValue']}")
                    logger.info(f"  视频时长: {request_data['nodeInfoList'][2]['fieldValue']}秒")
                    logger.info(f"  分辨率: {request_data['nodeInfoList'][3]['fieldValue']}")
                    logger.info(f"  提示词模式: {'手写提示词' if request_data['nodeInfoList'][4]['fieldValue'] == '1' else '自动提示词'}")
                    logger.info(f"  提示词: {request_data['nodeInfoList'][5]['fieldValue']}")
                    logger.info("=" * 50)
                
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
                            if result:  # 成功获取结果
                                if use_concurrency_control:
                                    _video_concurrency_manager.task_finished()
                                return result
                            else:
                                # 轮询失败，记录错误并准备重试
                                logger.warning(f"⚠️ 任务轮询失败 (尝试 {attempt + 1}/{max_retries + 1})")
                                if use_concurrency_control:
                                    _video_concurrency_manager.task_finished()
                                if attempt < max_retries:
                                    continue  # 重试
                                else:
                                    return None  # 达到最大重试次数
                        except Exception as e:
                            logger.warning(f"⚠️ 任务轮询异常 (尝试 {attempt + 1}/{max_retries + 1}): {e}")
                            if use_concurrency_control:
                                _video_concurrency_manager.task_finished()
                            if attempt < max_retries:
                                continue  # 重试
                            else:
                                return None  # 达到最大重试次数
                    else:
                        logger.warning(f"⚠️ 任务状态异常 (尝试 {attempt + 1}/{max_retries + 1}): {task_status}，期望状态: QUEUED 或 RUNNING")
                        if use_concurrency_control:
                            # 🔒 关键修复：任务已提交到服务器但状态异常，视为任务已提交但失败
                            _video_concurrency_manager.task_finished()
                        if attempt < max_retries:
                            continue  # 重试
                        else:
                            return None  # 达到最大重试次数
                else:
                    error_msg = result.get('msg', '未知错误')
                    logger.warning(f"⚠️ 任务提交失败 (尝试 {attempt + 1}/{max_retries + 1}): {error_msg}")
                    
                    # 🔒 特别处理TASK_QUEUE_MAXED错误
                    if 'TASK_QUEUE_MAXED' in error_msg:
                        logger.error(f"🚨 检测到TASK_QUEUE_MAXED错误：服务器队列已满")
                        logger.error(f"📝 建议：请等待现有任务完成后再提交新任务")
                        logger.error(f"🔧 已启用极保守模式，一次只允许一个任务")
                    
                    if use_concurrency_control:
                        # 🔒 关键修复：API已响应，说明已与服务器通信，视为任务已提交但失败
                        _video_concurrency_manager.task_finished()
                    if attempt < max_retries:
                        continue  # 重试
                    else:
                        logger.error(f"❌ 任务提交失败，已达到最大重试次数: {error_msg}")
                        return None  # 达到最大重试次数
                    
            except Exception as e:
                logger.warning(f"⚠️ 视频生成异常 (尝试 {attempt + 1}/{max_retries + 1}): {e}")
                if use_concurrency_control:
                    # 🔒 关键修复：由于在开始就调用了task_submitted()，
                    # 所以所有异常都应该被视为任务已提交但失败
                    _video_concurrency_manager.task_finished()
                if attempt < max_retries:
                    continue  # 重试
                else:
                    logger.error(f"❌ 视频生成失败，已达到最大重试次数: {e}")
                    return None  # 达到最大重试次数
        
        return None
    
    def enhance_video(self,
                     video_file_name: str,
                     resolution_output: int = 1,
                     enable_interpolation: bool = True,
                     interpolation_rate: int = 2,
                     timeout: Optional[int] = None,
                     use_concurrency_control: bool = True,
                     max_retries: int = 3,
                     retry_delay: int = 5) -> Optional[Dict[str, Any]]:
        """
        对视频进行补帧和超分处理
        
        Args:
            video_file_name: 视频文件名（已上传）
            resolution_output: 输出分辨率（0为原始尺寸，1为放大一倍，2为1080P输出）
            enable_interpolation: 是否插帧
            interpolation_rate: 插帧倍率（默认2倍）
            timeout: 超时时间（秒），如果为None则使用默认值
            use_concurrency_control: 是否使用并发控制，默认为True
            max_retries: 最大重试次数，默认3次
            retry_delay: 重试间隔时间（秒），默认5秒
            
        Returns:
            处理结果字典，包含视频URL等信息，失败返回None
        """
        # 重试逻辑
        for attempt in range(max_retries + 1):  # +1 因为包含初始尝试
            try:
                if attempt > 0:
                    logger.info(f"🔄 开始第 {attempt} 次重试（总共最多 {max_retries} 次重试）...")
                    time.sleep(retry_delay)
                
                # 🔒 原子并发控制 - 在同一个锁中检查并提交任务
                if use_concurrency_control:
                    while not _video_concurrency_manager.try_submit_task():
                        status = _video_concurrency_manager.get_status()
                        logger.info(f"⏳ 并发控制：已提交 {status['submitted']}，运行中 {status['running']}，排队中 {status['queued']}，等待任务完成...")
                        time.sleep(2)
                    # 此时已经原子地获得了提交权限并增加了计数
                
                # 构建请求数据 (视频增强)
                request_data = {
                    "webappId": self.video_enhance_webapp_id,
                    "apiKey": self.api_key,
                    "nodeInfoList": [
                        {
                            "nodeId": self.video_load_node_id,
                            "fieldName": "video",
                            "fieldValue": video_file_name,
                            "description": "视频加载"
                        },
                        {
                            "nodeId": self.resolution_output_node_id,
                            "fieldName": "string",
                            "fieldValue": str(resolution_output),
                            "description": "输出分辨率（0为原始尺寸，1为放大一倍，2为1080P输出）"
                        },
                        {
                            "nodeId": self.interpolation_node_id,
                            "fieldName": "value",
                            "fieldValue": str(enable_interpolation).lower(),
                            "description": "是否插帧"
                        },
                        {
                            "nodeId": self.interpolation_rate_node_id,
                            "fieldName": "string",
                            "fieldValue": str(interpolation_rate),
                            "description": "插帧倍率（默认2倍）"
                        }
                    ]
                }
                
                # 打印生成请求数据格式
                if attempt == 0:  # 只在第一次尝试时打印详细信息
                    logger.info("=== RunningHub 视频增强请求数据格式 ===")
                    logger.info(f"URL: {self.run_url}")
                    logger.info(f"Headers: {self.headers}")
                    logger.info("=" * 50)
                    
                    # 详细打印每个参数
                    logger.info("📋 视频增强参数详情:")
                    logger.info(f"  WebApp ID: {request_data['webappId']}")
                    logger.info(f"  API Key: {request_data['apiKey'][:10]}...")
                    logger.info(f"  节点信息列表:")
                    
                    for i, node_info in enumerate(request_data['nodeInfoList']):
                        logger.info(f"    节点 {i+1}:")
                        logger.info(f"      - Node ID: {node_info['nodeId']}")
                        logger.info(f"      - Field Name: {node_info['fieldName']}")
                        logger.info(f"      - Field Value: {node_info['fieldValue']}")
                        logger.info(f"      - Description: {node_info.get('description', 'N/A')}")
                    
                    logger.info("=" * 50)
                    logger.info(f"🎬 视频增强参数摘要:")
                    logger.info(f"  视频文件: {request_data['nodeInfoList'][0]['fieldValue']}")
                    logger.info(f"  输出分辨率: {request_data['nodeInfoList'][1]['fieldValue']}")
                    logger.info(f"  是否插帧: {request_data['nodeInfoList'][2]['fieldValue']}")
                    logger.info(f"  插帧倍率: {request_data['nodeInfoList'][3]['fieldValue']}")
                    logger.info("=" * 50)
                
                # 发送生成请求
                response = requests.post(
                    url=self.run_url, 
                    headers=self.headers, 
                    data=json.dumps(request_data)
                )
                response.raise_for_status()
                result = response.json()
                
                logger.info("=== 视频增强任务提交结果 ===")
                logger.info(f"响应代码: {result.get('code')}")
                logger.info(f"响应消息: {result.get('msg')}")
                
                if result.get('code') == 0:
                    task_data = result["data"]
                    logger.info(f"✅ 视频增强任务提交成功!")
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
                            if result:  # 成功获取结果
                                if use_concurrency_control:
                                    _video_concurrency_manager.task_finished()
                                return result
                            else:
                                # 轮询失败，记录错误并准备重试
                                logger.warning(f"⚠️ 任务轮询失败 (尝试 {attempt + 1}/{max_retries + 1})")
                                if use_concurrency_control:
                                    _video_concurrency_manager.task_finished()
                                if attempt < max_retries:
                                    continue  # 重试
                                else:
                                    return None  # 达到最大重试次数
                        except Exception as e:
                            logger.warning(f"⚠️ 任务轮询异常 (尝试 {attempt + 1}/{max_retries + 1}): {e}")
                            if use_concurrency_control:
                                _video_concurrency_manager.task_finished()
                            if attempt < max_retries:
                                continue  # 重试
                            else:
                                return None  # 达到最大重试次数
                    else:
                        logger.warning(f"⚠️ 任务状态异常 (尝试 {attempt + 1}/{max_retries + 1}): {task_status}，期望状态: QUEUED 或 RUNNING")
                        if use_concurrency_control:
                            # 🔒 关键修复：任务已提交到服务器但状态异常，视为任务已提交但失败
                            _video_concurrency_manager.task_finished()
                        if attempt < max_retries:
                            continue  # 重试
                        else:
                            return None  # 达到最大重试次数
                else:
                    error_msg = result.get('msg', '未知错误')
                    logger.warning(f"⚠️ 任务提交失败 (尝试 {attempt + 1}/{max_retries + 1}): {error_msg}")
                    
                    # 🔒 特别处理TASK_QUEUE_MAXED错误
                    if 'TASK_QUEUE_MAXED' in error_msg:
                        logger.error(f"🚨 检测到TASK_QUEUE_MAXED错误：服务器队列已满")
                        logger.error(f"📝 建议：请等待现有任务完成后再提交新任务")
                        logger.error(f"🔧 已启用极保守模式，一次只允许一个任务")
                    
                    if use_concurrency_control:
                        # 🔒 关键修复：API已响应，说明已与服务器通信，视为任务已提交但失败
                        _video_concurrency_manager.task_finished()
                    if attempt < max_retries:
                        continue  # 重试
                    else:
                        logger.error(f"❌ 任务提交失败，已达到最大重试次数: {error_msg}")
                        return None  # 达到最大重试次数
                    
            except Exception as e:
                logger.warning(f"⚠️ 视频增强异常 (尝试 {attempt + 1}/{max_retries + 1}): {e}")
                if use_concurrency_control:
                    # 🔒 关键修复：由于在开始就调用了task_submitted()，
                    # 所以所有异常都应该被视为任务已提交但失败
                    _video_concurrency_manager.task_finished()
                if attempt < max_retries:
                    continue  # 重试
                else:
                    logger.error(f"❌ 视频增强失败，已达到最大重试次数: {e}")
                    return None  # 达到最大重试次数
        
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
    
    def _get_task_outputs(self, task_id: str, max_retries: int = 3, retry_delay: int = 5) -> Optional[Dict[str, Any]]:
        """
        获取任务输出结果
        
        Args:
            task_id: 任务ID
            max_retries: 最大重试次数，默认3次
            retry_delay: 重试间隔时间（秒），默认5秒
            
        Returns:
            任务输出结果，失败返回None
        """
        # 重试逻辑
        for attempt in range(max_retries + 1):  # +1 因为包含初始尝试
            try:
                if attempt > 0:
                    logger.info(f"🔄 获取任务输出第 {attempt} 次重试（总共最多 {max_retries} 次重试）...")
                    time.sleep(retry_delay)
                
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
                    logger.warning(f"⚠️ 获取任务输出失败 (尝试 {attempt + 1}/{max_retries + 1})，错误代码: {outputs_result.get('code')}, 错误信息: {outputs_result.get('msg', '未知错误')}")
                    if attempt < max_retries:
                        continue  # 重试
                    else:
                        logger.error(f"❌ 获取任务输出失败，已达到最大重试次数")
                        return None
                
                # 获取视频输出数据
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
                    
                    # 寻找视频文件输出
                    for item in data:
                        file_url = item.get('fileUrl', '')
                        if file_url and ('.mp4' in file_url.lower() or '.mov' in file_url.lower() or item.get('fileType') == 'video'):
                            logger.info(f"✅ 找到视频输出: {file_url}")
                            return {
                                'code': 0,
                                'data': {
                                    'videos': [{'videoUrl': file_url}]
                                }
                            }
                    
                    # 如果没找到明确的视频文件，使用第一个结果
                    first_file_url = data[0].get('fileUrl')
                    if first_file_url:
                        logger.info(f"⚠️ 未找到明确的视频文件，使用第一个输出: {first_file_url}")
                        return {
                            'code': 0,
                            'data': {
                                'videos': [{'videoUrl': first_file_url}]
                            }
                        }
                    else:
                        logger.warning(f"⚠️ 未获取到有效的输出URL (尝试 {attempt + 1}/{max_retries + 1})")
                        if attempt < max_retries:
                            continue  # 重试
                        else:
                            logger.error("❌ 未获取到有效的输出URL，已达到最大重试次数")
                            return None
                else:
                    logger.warning(f"⚠️ 未获取到输出结果 (尝试 {attempt + 1}/{max_retries + 1})")
                    if attempt < max_retries:
                        continue  # 重试
                    else:
                        logger.error("❌ 未获取到输出结果，已达到最大重试次数")
                        return None
                    
            except Exception as e:
                logger.warning(f"⚠️ 获取任务输出异常 (尝试 {attempt + 1}/{max_retries + 1}): {e}")
                if attempt < max_retries:
                    continue  # 重试
                else:
                    logger.error(f"❌ 获取任务输出失败，已达到最大重试次数: {e}")
                    return None
        
        return None
    
    def generate_video(self, 
                      first_frame_path: str,
                      last_frame_path: str,
                      prompt: str,
                      video_name: str,
                      scene_id: str,
                      duration: int = 5,
                      resolution: int = 720,
                      use_smart_prompt: bool = True,
                      output_dir: Optional[str] = None,
                      max_retries: int = 3,
                      retry_delay: int = 5) -> Optional[str]:
        """
        生成视频的便利方法
        
        Args:
            first_frame_path: 首帧图片路径
            last_frame_path: 尾帧图片路径
            prompt: 视频生成提示词
            video_name: 视频名称（用于文件夹命名）
            scene_id: 场景ID（用于文件命名）
            duration: 视频时长（秒），默认5秒
            resolution: 分辨率，默认720
            use_smart_prompt: 是否使用智能提示词（True=手写提示词，False=自动提示词），默认True
            output_dir: 输出根目录，如果为None则使用默认的stylized_video
            max_retries: 最大重试次数，默认3次
            retry_delay: 重试间隔时间（秒），默认5秒
            
        Returns:
            输出视频文件路径，失败返回None
        """
        try:
            # 确定输出路径
            if not output_dir:
                output_dir = "stylized_video"
            
            video_output_dir = os.path.join(output_dir, video_name)
            os.makedirs(video_output_dir, exist_ok=True)
            
            output_path = os.path.join(video_output_dir, f"{scene_id}.mp4")
            
            # 检查输出文件是否已存在
            if os.path.exists(output_path):
                logger.info(f"视频文件已存在，跳过生成: {output_path}")
                return output_path
            
            # 上传首帧和尾帧
            logger.info("开始上传首帧图片...")
            first_frame_file_name = self.upload_image(first_frame_path)
            if not first_frame_file_name:
                logger.error("首帧图片上传失败")
                return None
            
            logger.info("开始上传尾帧图片...")
            last_frame_file_name = self.upload_image(last_frame_path)
            if not last_frame_file_name:
                logger.error("尾帧图片上传失败")
                return None
            
            # 执行视频生成
            result = self.generate_img2video(
                first_frame_file_name=first_frame_file_name,
                last_frame_file_name=last_frame_file_name,
                prompt=prompt,
                duration=duration,
                resolution=resolution,
                use_smart_prompt=use_smart_prompt,
                max_retries=max_retries,
                retry_delay=retry_delay
            )
            
            # 检查返回结果
            if not result:
                logger.error("视频生成失败，未获取到返回结果")
                return None
            
            # 检查code字段
            if result.get('code') != 0:
                logger.error(f"视频生成失败，错误代码: {result.get('code')}, 错误信息: {result.get('msg', '未知错误')}")
                return None
            
            # 检查videos数据
            if not result.get('data', {}).get('videos'):
                logger.error("视频生成失败，未获取到结果视频")
                return None
            
            # 下载生成的视频
            generated_videos = result['data']['videos']
            first_video_info = None
            
            for video_info in generated_videos:
                if video_info and isinstance(video_info, dict) and video_info.get('videoUrl'):
                    first_video_info = video_info
                    break
                elif isinstance(video_info, str) and video_info:
                    # 兼容旧格式，直接是URL字符串
                    first_video_info = {'videoUrl': video_info}
                    break
            
            if not first_video_info:
                logger.error("未找到有效的生成视频URL")
                return None
            
            first_video_url = first_video_info['videoUrl']
            
            return self._download_video(first_video_url, output_path)
            
        except Exception as e:
            logger.error(f"生成视频失败: {e}")
            return None

    def enhance_video_file(self,
                          video_path: str,
                          output_path: str,
                          resolution_output: int = 1,
                          enable_interpolation: bool = True,
                          interpolation_rate: int = 2,
                          max_retries: int = 3,
                          retry_delay: int = 5) -> Optional[str]:
        """
        对视频文件进行补帧和超分处理的便利方法
        
        Args:
            video_path: 输入视频路径
            output_path: 输出视频路径
            resolution_output: 输出分辨率（0为原始尺寸，1为放大一倍，2为1080P输出）
            enable_interpolation: 是否插帧
            interpolation_rate: 插帧倍率（默认2倍）
            max_retries: 最大重试次数，默认3次
            retry_delay: 重试间隔时间（秒），默认5秒
            
        Returns:
            输出视频文件路径，失败返回None
        """
        try:
            # 检查输出文件是否已存在
            if os.path.exists(output_path):
                logger.info(f"视频文件已存在，跳过处理: {output_path}")
                return output_path
            
            # 上传视频
            logger.info("开始上传视频...")
            video_file_name = self.upload_video(video_path)
            if not video_file_name:
                logger.error("视频上传失败")
                return None
            
            # 执行视频增强
            result = self.enhance_video(
                video_file_name=video_file_name,
                resolution_output=resolution_output,
                enable_interpolation=enable_interpolation,
                interpolation_rate=interpolation_rate,
                max_retries=max_retries,
                retry_delay=retry_delay
            )
            
            # 检查返回结果
            if not result:
                logger.error("视频增强失败，未获取到返回结果")
                return None
            
            # 检查code字段
            if result.get('code') != 0:
                logger.error(f"视频增强失败，错误代码: {result.get('code')}, 错误信息: {result.get('msg', '未知错误')}")
                return None
            
            # 检查videos数据
            if not result.get('data', {}).get('videos'):
                logger.error("视频增强失败，未获取到结果视频")
                return None
            
            # 下载处理后的视频
            generated_videos = result['data']['videos']
            first_video_info = None
            
            for video_info in generated_videos:
                if video_info and isinstance(video_info, dict) and video_info.get('videoUrl'):
                    first_video_info = video_info
                    break
                elif isinstance(video_info, str) and video_info:
                    # 兼容旧格式，直接是URL字符串
                    first_video_info = {'videoUrl': video_info}
                    break
            
            if not first_video_info:
                logger.error("未找到有效的处理后视频URL")
                return None
            
            first_video_url = first_video_info['videoUrl']
            
            return self._download_video(first_video_url, output_path)
            
        except Exception as e:
            logger.error(f"视频增强失败: {e}")
            return None

    def _download_video(self, video_url: str, output_path: str, max_retries: int = 3) -> Optional[str]:
        """
        下载视频到本地（使用流式下载，支持大文件和重试机制）
        
        Args:
            video_url: 视频URL
            output_path: 输出路径
            max_retries: 最大重试次数
            
        Returns:
            下载成功返回文件路径，失败返回None
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"开始下载视频 (尝试 {attempt + 1}/{max_retries}): {video_url}")
                
                # 创建输出目录
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # 使用流式下载，避免内存问题
                with requests.get(video_url, stream=True, timeout=(30, 300)) as response:
                    response.raise_for_status()
                    
                    # 获取文件大小
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded_size = 0
                    
                    logger.info(f"视频文件大小: {total_size / (1024*1024):.1f} MB" if total_size > 0 else "视频文件大小: 未知")
                    
                    # 分块下载
                    chunk_size = 8192  # 8KB chunks
                    with open(output_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=chunk_size):
                            if chunk:  # 过滤掉keep-alive chunks
                                f.write(chunk)
                                downloaded_size += len(chunk)
                                
                                # 显示下载进度（每10MB显示一次）
                                if total_size > 0 and downloaded_size % (10 * 1024 * 1024) == 0:
                                    progress = (downloaded_size / total_size) * 100
                                    logger.info(f"下载进度: {progress:.1f}% ({downloaded_size / (1024*1024):.1f}/{total_size / (1024*1024):.1f} MB)")
                
                # 验证下载文件
                if not os.path.exists(output_path):
                    raise Exception("下载文件不存在")
                
                file_size = os.path.getsize(output_path)
                if file_size == 0:
                    raise Exception("下载的文件为空")
                
                # 如果有content-length头，验证文件大小
                if total_size > 0 and file_size != total_size:
                    raise Exception(f"文件大小不匹配: 期望 {total_size} 字节，实际 {file_size} 字节")
                
                logger.info(f"✅ 视频下载完成: {output_path} ({file_size / (1024*1024):.1f} MB)")
                return output_path
                
            except requests.exceptions.Timeout:
                logger.warning(f"下载超时 (尝试 {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
                else:
                    logger.error("下载超时，已达到最大重试次数")
            except requests.exceptions.RequestException as e:
                logger.warning(f"网络请求错误 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
                else:
                    logger.error(f"网络请求失败，已达到最大重试次数: {e}")
            except Exception as e:
                logger.warning(f"下载失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                # 清理部分下载的文件
                if os.path.exists(output_path):
                    try:
                        os.remove(output_path)
                        logger.info("已清理部分下载的文件")
                    except:
                        pass
                
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
                else:
                    logger.error(f"视频下载失败，已达到最大重试次数: {e}")
        
        return None
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            模型信息字典
        """
        return {
            "model_name": "Wan Vace v2.2",
            "provider": "RunningHub",
            "type": "img2video",
            "webapp_id": self.webapp_id,
            "base_url": self.base_url,
            "first_frame_node_id": self.first_frame_node_id,
            "last_frame_node_id": self.last_frame_node_id,
            "prompt_node_id": self.prompt_node_id,
            "duration_node_id": self.duration_node_id,
            "resolution_node_id": self.resolution_node_id,
            "prompt_mode_node_id": self.prompt_mode_node_id,
            "video_enhance_webapp_id": self.video_enhance_webapp_id,
            "video_load_node_id": self.video_load_node_id,
            "resolution_output_node_id": self.resolution_output_node_id,
            "interpolation_node_id": self.interpolation_node_id,
            "interpolation_rate_node_id": self.interpolation_rate_node_id
        }


def create_wan_vace_generator_rh(api_key: Optional[str] = None) -> WanVaceImg2VideoRH:
    """
    创建 WanVaceImg2VideoRH 实例的便利函数
    
    Args:
        api_key: RunningHub API Key
        
    Returns:
        WanVaceImg2VideoRH实例
    """
    return WanVaceImg2VideoRH(api_key=api_key)


def generate_video_with_wan_vace_rh(first_frame_path: str,
                                   last_frame_path: str,
                                   prompt: str,
                                   video_name: str,
                                   scene_id: str,
                                   duration: int = 5,
                                   resolution: int = 720,
                                   use_smart_prompt: bool = True,
                                   output_dir: Optional[str] = None,
                                   max_retries: int = 3,
                                   retry_delay: int = 5) -> Optional[str]:
    """
    使用RunningHub Wan Vace v2.2生成视频的便利函数
    
    Args:
        first_frame_path: 首帧图片路径
        last_frame_path: 尾帧图片路径
        prompt: 视频生成提示词
        video_name: 视频名称（用于文件夹命名）
        scene_id: 场景ID（用于文件命名）
        duration: 视频时长（秒），默认5秒
        resolution: 分辨率，默认720
        use_smart_prompt: 是否使用智能提示词（True=手写提示词，False=自动提示词），默认True
        output_dir: 输出根目录
        max_retries: 最大重试次数，默认3次
        retry_delay: 重试间隔时间（秒），默认5秒
        
    Returns:
        输出视频文件路径，失败返回None
    """
    generator = create_wan_vace_generator_rh()
    return generator.generate_video(
        first_frame_path=first_frame_path,
        last_frame_path=last_frame_path,
        prompt=prompt,
        video_name=video_name,
        scene_id=scene_id,
        duration=duration,
        resolution=resolution,
        use_smart_prompt=use_smart_prompt,
        output_dir=output_dir,
        max_retries=max_retries,
        retry_delay=retry_delay
    )


def enhance_video_with_wan_vace_rh(video_path: str,
                                  output_path: str,
                                  resolution_output: int = 1,
                                  enable_interpolation: bool = True,
                                  interpolation_rate: int = 2,
                                  max_retries: int = 3,
                                  retry_delay: int = 5) -> Optional[str]:
    """
    使用RunningHub Wan Vace进行视频增强（补帧和超分）的便利函数
    
    Args:
        video_path: 输入视频路径
        output_path: 输出视频路径
        resolution_output: 输出分辨率（0为原始尺寸，1为放大一倍，2为1080P输出）
        enable_interpolation: 是否插帧
        interpolation_rate: 插帧倍率（默认2倍）
        max_retries: 最大重试次数，默认3次
        retry_delay: 重试间隔时间（秒），默认5秒
        
    Returns:
        输出视频文件路径，失败返回None
    """
    generator = create_wan_vace_generator_rh()
    return generator.enhance_video_file(
        video_path=video_path,
        output_path=output_path,
        resolution_output=resolution_output,
        enable_interpolation=enable_interpolation,
        interpolation_rate=interpolation_rate,
        max_retries=max_retries,
        retry_delay=retry_delay
    )


if __name__ == "__main__":
    # 测试代码
    generator = create_wan_vace_generator_rh()
    print("模型信息:", generator.get_model_info())
    
    # 注意：需要提供有效的本地图片路径进行测试
    test_first_frame = "test_first_frame.jpg"
    test_last_frame = "test_last_frame.jpg"
    test_prompt = "相关的单词是：黄昏时分，水边草地，戴帽女子站在燃烧的椅子旁。镜头缓缓推进，从全景聚焦到人物特写，阳光勾勒出她的轮廓，火光映在脸上。她抬手轻扶帽檐，眼神望向燃烧的椅子，水面倒映着火光与身影，氛围静谧又略带怅惘，光线随镜头推进渐变，从环境光笼罩到暖光集中在人物，展现情绪流动"
    print(f"测试首帧路径: {test_first_frame}")
    print(f"测试尾帧路径: {test_last_frame}")
    print(f"测试提示词: {test_prompt}")