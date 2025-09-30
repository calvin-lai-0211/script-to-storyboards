#!/usr/bin/env python3
"""
YiZhan LLM API Module
易站大语言模型API模块，支持文本对话和图片输入
"""

import base64
import requests
import json
from typing import Optional, Union, Generator, Tuple, List, Callable, Dict
from PIL import Image
from io import BytesIO

# 导入配置
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import YIZHAN_API_CONFIG

# API密钥配置
OPENAI_API_KEY = 'sk-MKLACC640iS1xVNwBb77Ae4251114d4f9aBd31Da26B4298e'
DEFAULT_API_KEY = 'sk-xFi3kt8xeS5BiE2hC0169f1aD9E04eB195D958599840825a'
BASE_URL = "https://hk.yi-zhan.top/v1"


def resize_image_to_square(image: Image.Image, target_size: int = 1024) -> Image.Image:
    """
    将图片处理成正方形格式，先等比例缩放，然后用黑边填充
    
    参数:
        image: PIL Image对象
        target_size: 目标尺寸（正方形边长），默认1024
        
    返回:
        处理后的PIL Image对象（正方形）
    """
    # 获取原始尺寸
    original_width, original_height = image.size
    
    # 计算缩放比例（保持长宽比，以较大边为准）
    scale = min(target_size / original_width, target_size / original_height)
    
    # 计算缩放后的尺寸
    new_width = int(original_width * scale)
    new_height = int(original_height * scale)
    
    # 等比例缩放
    resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # 创建黑色背景的正方形画布
    square_image = Image.new('RGB', (target_size, target_size), (0, 0, 0))
    
    # 计算居中位置
    paste_x = (target_size - new_width) // 2
    paste_y = (target_size - new_height) // 2
    
    # 将缩放后的图片粘贴到黑色背景上
    square_image.paste(resized_image, (paste_x, paste_y))
    
    return square_image


def image_to_base64(image_input: Union[str, Image.Image]) -> str:
    """
    将图片转换为base64编码（底层操作）
    
    参数:
        image_input: 图片路径(str)或PIL Image对象
        
    返回:
        base64编码的图片字符串
    """
    try:
        if isinstance(image_input, str):
            # 如果是文件路径
            with open(image_input, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        elif isinstance(image_input, Image.Image):
            # 如果是PIL Image对象
            buffer = BytesIO()
            # 保存为JPEG格式
            if image_input.mode in ("RGBA", "P"):
                image_input = image_input.convert("RGB")
            image_input.save(buffer, format="JPEG", quality=95)
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
        else:
            raise ValueError("image_input 必须是文件路径(str)或PIL Image对象")
    except Exception as e:
        print(f"✗ 图片base64编码失败: {e}")
        raise


def preprocess_image_for_llm_original_size(image_input: Union[str, Image.Image]) -> Tuple[str, int, int]:
    """
    为LLM预处理图片：保持原始尺寸并转换为base64
    
    参数:
        image_input: 图片路径(str)或PIL Image对象
        
    返回:
        (base64_string, width, height) 元组
    """
    try:
        # 加载图片
        if isinstance(image_input, str):
            image = Image.open(image_input)
        elif isinstance(image_input, Image.Image):
            image = image_input.copy()
        else:
            raise ValueError("image_input 必须是文件路径(str)或PIL Image对象")
        
        # 转换为RGB模式（如果需要）
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        
        # 获取原始尺寸
        original_width, original_height = image.size
        
        # 直接转换为base64，不进行尺寸调整
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=95)
        base64_string = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return base64_string, original_width, original_height
        
    except Exception as e:
        print(f"✗ 图片预处理失败: {e}")
        raise


def preprocess_image_for_llm(image_input: Union[str, Image.Image], target_size: int = 1024) -> Tuple[str, int, int]:
    """
    为LLM预处理图片：处理成正方形并转换为base64
    
    参数:
        image_input: 图片路径(str)或PIL Image对象
        target_size: 目标尺寸，默认1024
        
    返回:
        (base64_string, width, height) 元组
    """
    try:
        # 加载图片
        if isinstance(image_input, str):
            image = Image.open(image_input)
        elif isinstance(image_input, Image.Image):
            image = image_input.copy()
        else:
            raise ValueError("image_input 必须是文件路径(str)或PIL Image对象")
        
        # 转换为RGB模式（如果需要）
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        
        # 处理成正方形
        square_image = resize_image_to_square(image, target_size)
        
        # 转换为base64
        buffer = BytesIO()
        square_image.save(buffer, format="JPEG", quality=95)
        base64_string = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return base64_string, target_size, target_size
        
    except Exception as e:
        print(f"✗ 图片预处理失败: {e}")
        raise


def extract_content_from_stream(stream_generator: Union[Generator[Tuple[str, str], None, None], Tuple[str, str]]) -> str:
    """
    从流式返回结果中提取完整的content内容
    
    参数:
        stream_generator: 流式生成器，产生(content_chunk, reasoning_chunk)元组
        
    返回:
        完整的content字符串
    """
    # If it's already a tuple (non-streaming response), return the first element
    if isinstance(stream_generator, tuple):
        return stream_generator[0]
    
    # Otherwise process as a generator (streaming response)
    full_content = ""
    try:
        for content_chunk, reasoning_chunk in stream_generator:
            if content_chunk:
                full_content += content_chunk
    except Exception as e:
        print(f"✗ 流式结果处理失败: {e}")
        raise
    
    return full_content


def extract_content_from_stream_with_callback(
    stream_generator: Union[Generator[Tuple[str, str], None, None], Tuple[str, str]],
    content_callback: Optional[Callable] = None,
    reasoning_callback: Optional[Callable] = None
) -> str:
    """
    从流式返回结果中提取content，并支持回调函数实时处理
    
    参数:
        stream_generator: 流式生成器，产生(content_chunk, reasoning_chunk)元组
        content_callback: 处理content chunk的回调函数
        reasoning_callback: 处理reasoning chunk的回调函数
        
    返回:
        完整的content字符串
    """
    full_content = ""
    try:
        for content_chunk, reasoning_chunk in stream_generator:
            if reasoning_chunk and reasoning_callback:
                reasoning_callback(reasoning_chunk)
            if content_chunk:
                full_content += content_chunk
                if content_callback:
                    content_callback(content_chunk)
    except Exception as e:
        print(f"✗ 流式结果处理失败: {e}")
        raise
    
    return full_content


class YiZhanLLM:
    """易站大语言模型API客户端类"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        初始化YiZhan LLM客户端
        
        参数:
            api_key: API密钥，如果不提供则使用配置文件中的密钥
            base_url: API基础URL，如果不提供则使用配置文件中的URL
        """
        self.deepseek_api_key = YIZHAN_API_CONFIG.get("deepseek_api_key", OPENAI_API_KEY)
        self.gemini_api_key = YIZHAN_API_CONFIG.get("gemini_api_key")
        self.default_api_key = YIZHAN_API_CONFIG.get("default_api_key", DEFAULT_API_KEY)
        self.base_url = base_url or YIZHAN_API_CONFIG.get("base_url", BASE_URL)
        
        print(f"✓ YiZhan LLM客户端初始化完成")
    
    def _get_api_key(self, model: str) -> str:
        """
        根据模型选择合适的API密钥
        
        参数:
            model: 模型名称
            
        返回:
            API密钥
        """
        model_lower = model.lower()
        if 'gemini' in model_lower:
            return self.gemini_api_key
        elif 'deepseek' in model_lower or 'doubao' in model_lower:
            return self.deepseek_api_key
        else:
            return self.default_api_key
    
    def chat(self, 
             user_message: str,
             model: Optional[str] = None,
             stream: bool = True,
             max_tokens: int = 4096) -> Union[Generator[Tuple[str, str], None, None], Tuple[str, str]]:
        """
        纯文本对话接口
        
        参数:
            user_message: 用户输入的消息
            model: 使用的模型名称，默认使用配置中的默认模型
            stream: 是否流式输出，默认为True
            max_tokens: 最大token数量
            
        返回:
            如果stream=True: 生成器，产生(content_chunk, reasoning_chunk)元组
            如果stream=False: (content, reasoning)元组
        """
        if model is None:
            model = YIZHAN_API_CONFIG.get("default_model", "deepseek-reasoner")
        
        api_key = self._get_api_key(model)
        messages = [{'role': 'user', 'content': user_message}]
        
        # 如果是gemini模型，使用更大的max_tokens
        final_max_tokens = 16000 if 'gemini' in model.lower() else max_tokens
            
        return self._make_request(api_key, model, messages, stream, final_max_tokens)
    
    def chat_with_image(self, 
                       user_message: str,
                       image_input: Union[str, Image.Image],
                       model: Optional[str] = None,
                       stream: bool = True,
                       max_tokens: int = 4096) -> Union[Generator[Tuple[str, str], None, None], Tuple[str, str]]:
        """
        带图片输入的对话接口
        
        参数:
            user_message: 用户输入的消息
            image_input: 输入图片(文件路径或PIL Image对象)
            model: 使用的模型名称，默认使用图片模型
            stream: 是否流式输出，默认为True
            max_tokens: 最大token数量
            
        返回:
            如果stream=True: 生成器，产生(content_chunk, reasoning_chunk)元组
            如果stream=False: (content, reasoning)元组
        """
        if model is None:
            model = YIZHAN_API_CONFIG.get("image_model", "gpt-4o-image-vip")
        
        api_key = self._get_api_key(model)
        
        # 如果是gemini模型，使用更大的max_tokens
        final_max_tokens = 16000 if 'gemini' in model.lower() else max_tokens
        
        # 预处理图片：压缩并添加黑边处理成1024x1024
        base64_image, width, height = preprocess_image_for_llm(image_input, target_size=1024)
        print(f"✓ 图片已预处理为 {width}x{height} 尺寸")
        
        # 构建包含图片的消息
        messages = [
            {
                'role': 'user', 
                'content': [
                    {
                        "type": "text",
                        "text": user_message
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "high"
                        },
                        
                    }
                ]
            }
        ]
        
        return self._make_request(api_key, model, messages, stream, final_max_tokens)
    
    def chat_with_images(self, 
                        user_message: str,
                        image_inputs: List[Union[str, Image.Image]],
                        model: Optional[str] = None,
                        stream: bool = True,
                        max_tokens: int = 4096,
                        preserve_original_size: bool = False) -> Union[Generator[Tuple[str, str], None, None], Tuple[str, str]]:
        """
        带多张图片输入的对话接口
        
        参数:
            user_message: 用户输入的消息
            image_inputs: 输入图片列表(文件路径或PIL Image对象的列表)
            model: 使用的模型名称，默认使用图片模型
            stream: 是否流式输出，默认为True
            max_tokens: 最大token数量
            preserve_original_size: 是否保持图片原始尺寸，默认为False
            
        返回:
            如果stream=True: 生成器，产生(content_chunk, reasoning_chunk)元组
            如果stream=False: (content, reasoning)元组
        """
        if model is None:
            model = YIZHAN_API_CONFIG.get("image_model", "gpt-4o-image-vip")
            
        api_key = self._get_api_key(model)

        # 如果是gemini模型，使用更大的max_tokens
        final_max_tokens = 16000 if 'gemini' in model.lower() else max_tokens
        
        # 构建消息内容列表
        content_list: List[Dict[str, Union[str, Dict[str, str]]]] = [
            {
                "type": "text",
                "text": user_message
            }
        ]
        
        # 处理每张图片并添加到内容列表
        for i, image_input in enumerate(image_inputs):
            if preserve_original_size:
                # 保持原始尺寸
                base64_image, width, height = preprocess_image_for_llm_original_size(image_input)
                print(f"✓ 图片{i+1}保持原始尺寸 {width}x{height}")
            else:
                # 预处理图片：压缩并添加黑边处理成1024x1024
                base64_image, width, height = preprocess_image_for_llm(image_input, target_size=1024)
                print(f"✓ 图片{i+1}已预处理为 {width}x{height} 尺寸")
            
            # Create the image URL object with explicit typing
            image_url_entry: Dict[str, Union[str, Dict[str, str]]] = {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}",
                    "detail": "high"
                }
            }
            content_list.append(image_url_entry)
        
        # 构建包含多张图片的消息
        messages = [
            {
                'role': 'user', 
                'content': content_list
            }
        ]
        
        return self._make_request(api_key, model, messages, stream, final_max_tokens)
    
    def _stream_request(self, headers: dict, data: dict) -> Generator[Tuple[str, str], None, None]:
        """
        执行流式API请求的生成器方法
        """
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=data,
            stream=True
        )
        # Immediately raise an exception for bad status codes (4xx or 5xx)
        response.raise_for_status()

        content_generated = False
        reasoning_finished = False
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    line = line[6:]
                    if line.strip() == '[DONE]':
                        break
                    try:
                        chunk_data = json.loads(line)
                        if 'choices' in chunk_data and chunk_data['choices']:
                            delta = chunk_data['choices'][0].get('delta', {})
                            
                            # 处理推理内容
                            if 'model_extra' in delta and 'reasoning_content' in delta['model_extra']:
                                reasoning_chunk = delta['model_extra']['reasoning_content']
                                yield '', reasoning_chunk
                            
                            # 当开始接收最终答案时，标记推理完成
                            if 'content' in delta and delta['content'] and not reasoning_finished:
                                reasoning_finished = True
                                yield '', ''
                            
                            # 流式输出最终答案
                            if 'content' in delta and delta['content']:
                                content_generated = True
                                yield delta['content'], ''
                    except json.JSONDecodeError:
                        continue
        
        if not content_generated:
            raise ValueError("API returned a successful but empty response stream.")

    def _make_request(self, 
                     api_key: str,
                     model: str,
                     messages: list,
                     stream: bool,
                     max_tokens: int) -> Union[Generator[Tuple[str, str], None, None], Tuple[str, str]]:
        """
        执行API请求的通用方法
        
        参数:
            api_key: API密钥
            model: 模型名称
            messages: 消息列表
            stream: 是否流式输出
            max_tokens: 最大token数量
            
        返回:
            响应结果
        """
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "extra_body": {
                "return_reasoning": True,
                "max_completion_tokens": max_tokens
            }
        }
        
        # 不同的模型使用不同的max_tokens参数
        if 'gemini' in model.lower():
            data["max_tokens"] = max_tokens
        else:
            data["extra_body"] = {
                "return_reasoning": True,
                "max_completion_tokens": max_tokens
            }
        
        if stream:
            return self._stream_request(headers, data)
        else:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data
            )
            # Immediately raise an exception for bad status codes (4xx or 5xx)
            response.raise_for_status()

            result = response.json()
            content = result['choices'][0]['message']['content']
            reasoning = result['choices'][0]['message'].get('reasoning_content', '')
            return content, reasoning


# 全局实例（可选，便于使用）
_yizhan_llm_instance = None

def get_yizhan_llm() -> YiZhanLLM:
    """获取YiZhan LLM全局实例"""
    global _yizhan_llm_instance
    if _yizhan_llm_instance is None:
        _yizhan_llm_instance = YiZhanLLM()
    return _yizhan_llm_instance


# 便利函数
def chat(user_message: str, 
         model: Optional[str] = None,
         stream: bool = True) -> Union[Generator[Tuple[str, str], None, None], Tuple[str, str]]:
    """
    便利函数：纯文本对话
    
    参数:
        user_message: 用户输入的消息
        model: 使用的模型名称
        stream: 是否流式输出
        
    返回:
        响应结果
    """
    llm = get_yizhan_llm()
    return llm.chat(user_message, model, stream)


def chat_with_image(user_message: str,
                   image_input: Union[str, Image.Image],
                   model: Optional[str] = None,
                   stream: bool = True) -> Union[Generator[Tuple[str, str], None, None], Tuple[str, str]]:
    """
    便利函数：带图片的对话
    
    参数:
        user_message: 用户输入的消息
        image_input: 输入图片
        model: 使用的模型名称
        stream: 是否流式输出
        
    返回:
        响应结果
    """
    llm = get_yizhan_llm()
    return llm.chat_with_image(user_message, image_input, model, stream)


def chat_with_images(user_message: str,
                    image_inputs: List[Union[str, Image.Image]],
                    model: Optional[str] = None,
                    stream: bool = True,
                    preserve_original_size: bool = False) -> Union[Generator[Tuple[str, str], None, None], Tuple[str, str]]:
    """
    便利函数：带多张图片的对话
    
    参数:
        user_message: 用户输入的消息
        image_inputs: 输入图片列表
        model: 使用的模型名称
        stream: 是否流式输出
        preserve_original_size: 是否保持图片原始尺寸
        
    返回:
        响应结果
    """
    llm = get_yizhan_llm()
    return llm.chat_with_images(user_message, image_inputs, model, stream, preserve_original_size=preserve_original_size)


def get_prompt_from_images(user_message: str,
                          image_inputs: List[Union[str, Image.Image]],
                          model: Optional[str] = None,
                          preserve_original_size: bool = False) -> str:
    """
    便利函数：从多张图片获取完整的prompt（非流式）
    
    参数:
        user_message: 用户输入的消息
        image_inputs: 输入图片列表
        model: 使用的模型名称
        preserve_original_size: 是否保持图片原始尺寸
        
    返回:
        完整的prompt字符串
    """
    llm = get_yizhan_llm()
    stream_generator = llm.chat_with_images(user_message, image_inputs, model, stream=True, preserve_original_size=preserve_original_size)
    return extract_content_from_stream(stream_generator)


def get_prompt_from_images_with_callback(user_message: str,
                                        image_inputs: List[Union[str, Image.Image]],
                                        model: Optional[str] = None,
                                        content_callback: Optional[Callable] = None,
                                        reasoning_callback: Optional[Callable] = None) -> str:
    """
    便利函数：从多张图片获取完整的prompt，支持实时回调
    
    参数:
        user_message: 用户输入的消息
        image_inputs: 输入图片列表
        model: 使用的模型名称
        content_callback: 处理content chunk的回调函数
        reasoning_callback: 处理reasoning chunk的回调函数
        
    返回:
        完整的prompt字符串
    """
    llm = get_yizhan_llm()
    stream_generator = llm.chat_with_images(user_message, image_inputs, model, stream=True)
    return extract_content_from_stream_with_callback(stream_generator, content_callback, reasoning_callback)


def single_round_chat(user_message, model="deepseek-reasoner", stream=True):
    """
    使用易站API进行单轮对话
    
    参数:
        user_message: 用户输入的消息
        model: 使用的模型名称,默认为deepseek-reasoner
        stream: 是否流式输出
        
    返回:
        模型的回复内容
    """
    if 'deepseek' in model.lower() or 'doubao' in model.lower():
        api_key = OPENAI_API_KEY
    else:
        api_key = DEFAULT_API_KEY
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    messages = [{'role': 'user', 'content': user_message}]
    
    data = {
        "model": model,
        "messages": messages,
        "stream": stream,
        "extra_body": {
            "return_reasoning": True,
            "max_completion_tokens": 4000
        }
    }
    
    if stream:
        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers=headers,
            json=data,
            stream=True
        )
        
        reasoning_finished = False
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    line = line[6:]
                    if line.strip() == '[DONE]':
                        break
                    try:
                        chunk_data = json.loads(line)
                        if 'choices' in chunk_data and chunk_data['choices']:
                            delta = chunk_data['choices'][0].get('delta', {})
                            
                            # 处理推理内容
                            if 'model_extra' in delta and 'reasoning_content' in delta['model_extra']:
                                reasoning_chunk = delta['model_extra']['reasoning_content']
                                yield '', reasoning_chunk
                            
                            # 当开始接收最终答案时，标记推理完成
                            if 'content' in delta and delta['content'] and not reasoning_finished:
                                reasoning_finished = True
                                yield '', ''
                            
                            # 流式输出最终答案
                            if 'content' in delta and delta['content']:
                                yield delta['content'], ''
                    except json.JSONDecodeError:
                        continue
        return True
    else:
        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers=headers,
            json=data
        )
        
        result = response.json()
        return result['choices'][0]['message']['content'], result['choices'][0]['message'].get('reasoning_content', '')


# 兼容性函数（保持向后兼容）
def single_round_chat_with_image(user_message: str, 
                                image_input: Optional[Union[str, Image.Image]] = None,
                                model: Optional[str] = "gpt-4o-image-vip", 
                                stream: bool = True,
                                **kwargs) -> Union[Generator[Tuple[str, str], None, None], Tuple[str, str]]:
    """
    兼容性函数：带图片的单轮对话
    """
    if image_input is None:
        return chat(user_message, model, stream)
    else:
        return chat_with_image(user_message, image_input, model, stream)


def single_round_chat_with_images(user_message: str, 
                                 image_inputs: List[Union[str, Image.Image]],
                                 model: Optional[str] = "gpt-4o-image-vip", 
                                 stream: bool = True,
                                 **kwargs) -> Union[Generator[Tuple[str, str], None, None], Tuple[str, str]]:
    """
    兼容性函数：带多张图片的单轮对话
    
    参数:
        user_message: 用户输入的消息
        image_inputs: 输入图片列表
        model: 使用的模型名称
        stream: 是否流式输出
        
    返回:
        如果stream=True: 生成器，产生(content_chunk, reasoning_chunk)元组
        如果stream=False: (content, reasoning)元组
    """
    return chat_with_images(user_message, image_inputs, model, stream)


if __name__ == '__main__':
    # 测试代码
    # 测试YizhanLLM的对话功能
    test_prompt = "请解释一下什么是人工智能，并举例说明其应用领域。"

    print("\n=== 测试YiZhan LLM对话功能 ===")
    
    # 测试1: 普通文本对话（流式输出）
    """
    print("\n--- 测试1: 文本对话（流式输出）---")
    try:
        print(f"用户问题: {test_prompt}")
        print("AI回答:")
        
        full_content = ""
        full_reasoning = ""
        
        for content_chunk, reasoning_chunk in single_round_chat(test_prompt, model='deepseek-reasoner', stream=True):
            if reasoning_chunk:
                # 推理过程（可选择是否显示）
                full_reasoning += reasoning_chunk
            elif content_chunk:
                print(content_chunk, end='', flush=True)
                full_content += content_chunk
        
        print("\n--- 对话完成 ---")
        print(f"完整回答长度: {len(full_content)} 字符")
        
    except Exception as e:
        print(f"文本对话测试失败: {e}")
    
    """
    
    # 测试3: 带图片的对话（如果有图片的话）
    print("\n--- 测试3: 图片对话功能（预处理为1024x1024）---")
    try:
        # 这里可以添加图片路径进行测试
        image_path = "video_temp/1/0154_500.jpeg"  # 替换为实际图片路径
        if os.path.exists(image_path):
             print(f"正在测试图片对话功能，图片路径: {image_path}")
             print("图片将被自动预处理为1024x1024尺寸（等比例缩放+黑边填充）")
             for content_chunk, reasoning_chunk in chat_with_image("进行图片风格转换，将这张图片转换成彩色的画家Inceoglu的插画风格。", 
                                                                   image_path, stream=True):
                 if content_chunk:
                     print(content_chunk, end='', flush=True)
             print("\n图片对话测试完成")
        else:
             print(f"测试图片不存在: {image_path}")
             print("你可以将任意图片路径替换到代码中进行测试")

        
    except Exception as e:
        print(f"图片对话测试失败: {e}")
    
    # 测试4: 多图对话功能
    print("\n--- 测试4: 多图对话功能 ---")
    try:
        # 测试多图功能
        image_paths: List[str] = ["video_temp/1/0154_500.jpeg", "video_temp/1/0155_000.jpeg"]
        existing_images: List[Union[str, Image.Image]] = [path for path in image_paths if os.path.exists(path)]
        
        if len(existing_images) >= 2:
            print(f"正在测试多图对话功能，图片路径: {existing_images}")
            print("所有图片将被自动预处理为1024x1024尺寸")
            
            # 使用流式处理并提取完整内容
            prompt = get_prompt_from_images(
                "请分析这些图片，描述它们的共同特征和差异，并生成一个统一的风格化prompt。",
                existing_images
            )
            print(f"完整的Prompt: {prompt}")
            
        elif len(existing_images) == 1:
            print(f"只找到一张图片: {existing_images[0]}")
            print("使用单图功能进行测试")
            
        else:
            print("未找到测试图片，跳过多图测试")
            print("可以将实际图片路径添加到代码中进行测试")

        
    except Exception as e:
        print(f"多图对话测试失败: {e}")
    
    print("\n=== 所有测试完成 ===")
