"""
Nano Banana MCP 服务器

使用 Gemini 2.5 Flash Image 模型进行图片生成和编辑的 MCP 服务器

用法:
    uv run nano_banana_mcp.server stdio
"""

import os
import base64
import io
import uuid
from typing import Optional, List, Dict, Any
from pathlib import Path

import google.generativeai as genai
from PIL import Image
from mcp.server.fastmcp import FastMCP

# 环境变量配置
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_BASE = os.getenv("GEMINI_API_BASE", "https://generativelanguage.googleapis.com")
OUTPUT_IMAGE_PATH = os.getenv("OUTPUT_IMAGE_PATH", "./generated_images")

# 创建 MCP 服务器
mcp = FastMCP("Nano Banana Image Generator")

# 配置 Gemini AI
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # 如果有自定义 API 基础地址，这里可以配置
    if GEMINI_API_BASE != "https://generativelanguage.googleapis.com":
        # 注意：google-generativeai 库可能不直接支持自定义基础 URL
        # 这里只是预留接口，实际使用时可能需要其他方法
        pass

# 确保输出目录存在
os.makedirs(OUTPUT_IMAGE_PATH, exist_ok=True)


def save_image_base64(image_data: bytes, filename: str = None) -> str:
    """保存 base64 编码的图片数据到本地文件"""
    if filename is None:
        filename = f"generated_{uuid.uuid4().hex}.png"
    
    filepath = os.path.join(OUTPUT_IMAGE_PATH, filename)
    
    with open(filepath, "wb") as f:
        f.write(image_data)
    
    return filepath


def encode_image_to_base64(image_path: str) -> str:
    """将图片文件编码为 base64 字符串"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def load_image_from_path(image_path: str) -> Image.Image:
    """从路径加载图片"""
    return Image.open(image_path)


@mcp.tool()
def generate_image(
    prompt: str,
    negative_prompt: str = "",
    width: int = 1024,
    height: int = 1024,
    guidance_scale: float = 7.0,
    num_inference_steps: int = 20,
    seed: Optional[int] = None,
    output_filename: Optional[str] = None
) -> str:
    """
    使用 Gemini 2.5 Flash Image 模型生成图片
    
    Args:
        prompt: 图片生成提示词
        negative_prompt: 负面提示词（要避免的内容）
        width: 图片宽度（默认1024）
        height: 图片高度（默认1024）
        guidance_scale: 引导强度（默认7.0）
        num_inference_steps: 推理步数（默认20）
        seed: 随机种子（可选）
        output_filename: 输出文件名（可选，默认自动生成）
    
    Returns:
        生成图片的本地路径
    """
    try:
        if not GEMINI_API_KEY:
            return "错误：未设置 GEMINI_API_KEY 环境变量"
        
        # 创建模型实例
        model = genai.GenerativeModel('gemini-2.5-flash-image-preview')
        
        # 构建完整的提示词
        full_prompt = prompt
        if negative_prompt:
            full_prompt += f" (避免: {negative_prompt})"
        
        # 添加图片尺寸和质量要求
        full_prompt += f" 图片尺寸: {width}x{height}像素，高质量，清晰"
        
        # 生成图片
        response = model.generate_content([full_prompt])
        
        # 检查响应
        if not response or not hasattr(response, 'parts') or not response.parts:
            return "错误：模型未返回有效响应"
        
        # 查找图片数据
        image_data = None
        for part in response.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                if part.inline_data.mime_type.startswith('image/'):
                    image_data = part.inline_data.data
                    break
        
        if not image_data:
            return "错误：模型响应中未找到图片数据"
        
        # 解码并保存图片
        image_bytes = base64.b64decode(image_data)
        filepath = save_image_base64(image_bytes, output_filename)
        
        return f"图片生成成功！保存路径: {filepath}"
        
    except Exception as e:
        return f"生成图片时发生错误: {str(e)}"


@mcp.tool()
def edit_image(
    image_path: str,
    prompt: str,
    negative_prompt: str = "",
    guidance_scale: float = 7.0,
    num_inference_steps: int = 20,
    strength: float = 0.8,
    seed: Optional[int] = None,
    output_filename: Optional[str] = None
) -> str:
    """
    使用 Gemini 2.5 Flash Image 模型编辑现有图片
    
    Args:
        image_path: 原始图片路径
        prompt: 编辑提示词（描述如何修改图片）
        negative_prompt: 负面提示词（要避免的内容）
        guidance_scale: 引导强度（默认7.0）
        num_inference_steps: 推理步数（默认20）
        strength: 编辑强度（0.0-1.0，越高修改越大，默认0.8）
        seed: 随机种子（可选）
        output_filename: 输出文件名（可选，默认自动生成）
    
    Returns:
        编辑后图片的本地路径
    """
    try:
        if not GEMINI_API_KEY:
            return "错误：未设置 GEMINI_API_KEY 环境变量"
        
        if not os.path.exists(image_path):
            return f"错误：图片文件不存在: {image_path}"
        
        # 加载原始图片
        try:
            original_image = load_image_from_path(image_path)
        except Exception as e:
            return f"错误：无法加载图片 {image_path}: {str(e)}"
        
        # 创建模型实例
        model = genai.GenerativeModel('gemini-2.5-flash-image-preview')
        
        # 构建编辑提示词
        edit_prompt = f"编辑这张图片: {prompt}"
        if negative_prompt:
            edit_prompt += f" (避免: {negative_prompt})"
        
        # 编码图片为 base64
        image_base64 = encode_image_to_base64(image_path)
        
        # 构建请求内容
        content = [
            edit_prompt,
            {
                "mime_type": "image/png",
                "data": image_base64
            }
        ]
        
        # 生成编辑后的图片
        response = model.generate_content(content)
        
        # 检查响应
        if not response or not hasattr(response, 'parts') or not response.parts:
            return "错误：模型未返回有效响应"
        
        # 查找图片数据
        image_data = None
        for part in response.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                if part.inline_data.mime_type.startswith('image/'):
                    image_data = part.inline_data.data
                    break
        
        if not image_data:
            return "错误：模型响应中未找到图片数据"
        
        # 解码并保存图片
        image_bytes = base64.b64decode(image_data)
        
        # 生成输出文件名
        if output_filename is None:
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            output_filename = f"{base_name}_edited_{uuid.uuid4().hex[:8]}.png"
        
        filepath = save_image_base64(image_bytes, output_filename)
        
        return f"图片编辑成功！保存路径: {filepath}"
        
    except Exception as e:
        return f"编辑图片时发生错误: {str(e)}"


@mcp.tool()
def get_image_info(image_path: str) -> str:
    """
    获取图片的基本信息
    
    Args:
        image_path: 图片路径
    
    Returns:
        图片信息的文本描述
    """
    try:
        if not os.path.exists(image_path):
            return f"错误：图片文件不存在: {image_path}"
        
        # 加载图片
        image = load_image_from_path(image_path)
        
        # 获取图片信息
        info = []
        info.append(f"图片路径: {image_path}")
        info.append(f"尺寸: {image.size[0]}x{image.size[1]} 像素")
        info.append(f"模式: {image.mode}")
        info.append(f"格式: {image.format or '未知'}")
        
        # 获取文件大小
        file_size = os.path.getsize(image_path)
        if file_size < 1024:
            size_str = f"{file_size} 字节"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size / 1024:.1f} KB"
        else:
            size_str = f"{file_size / (1024 * 1024):.1f} MB"
        
        info.append(f"文件大小: {size_str}")
        
        return "\n".join(info)
        
    except Exception as e:
        return f"获取图片信息时发生错误: {str(e)}"


@mcp.tool()
def list_generated_images() -> str:
    """
    列出输出目录中的所有生成的图片
    
    Returns:
        图片列表的文本描述
    """
    try:
        if not os.path.exists(OUTPUT_IMAGE_PATH):
            return f"输出目录不存在: {OUTPUT_IMAGE_PATH}"
        
        # 支持的图片格式
        image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp'}
        
        # 获取所有图片文件
        image_files = []
        for filename in os.listdir(OUTPUT_IMAGE_PATH):
            if any(filename.lower().endswith(ext) for ext in image_extensions):
                filepath = os.path.join(OUTPUT_IMAGE_PATH, filename)
                file_size = os.path.getsize(filepath)
                
                # 获取图片尺寸
                try:
                    image = Image.open(filepath)
                    dimensions = f"{image.size[0]}x{image.size[1]}"
                    image.close()
                except:
                    dimensions = "未知"
                
                # 格式化文件大小
                if file_size < 1024 * 1024:
                    size_str = f"{file_size / 1024:.1f} KB"
                else:
                    size_str = f"{file_size / (1024 * 1024):.1f} MB"
                
                image_files.append({
                    'filename': filename,
                    'path': filepath,
                    'size': size_str,
                    'dimensions': dimensions
                })
        
        if not image_files:
            return f"输出目录中没有找到图片文件: {OUTPUT_IMAGE_PATH}"
        
        # 按文件名排序
        image_files.sort(key=lambda x: x['filename'])
        
        # 格式化输出
        result = [f"输出目录: {OUTPUT_IMAGE_PATH}"]
        result.append(f"找到 {len(image_files)} 个图片文件:")
        result.append("-" * 50)
        
        for img in image_files:
            result.append(f"文件名: {img['filename']}")
            result.append(f"路径: {img['path']}")
            result.append(f"尺寸: {img['dimensions']}")
            result.append(f"大小: {img['size']}")
            result.append("")
        
        return "\n".join(result)
        
    except Exception as e:
        return f"列出图片时发生错误: {str(e)}"


@mcp.resource("image://{path}")
def get_image_resource(path: str) -> str:
    """
    获取图片作为资源
    
    Args:
        path: 图片路径
    
    Returns:
        图片的 base64 编码数据或错误信息
    """
    try:
        if not os.path.exists(path):
            return f"错误：图片文件不存在: {path}"
        
        image_base64 = encode_image_to_base64(path)
        return f"data:image/png;base64,{image_base64}"
        
    except Exception as e:
        return f"读取图片资源时发生错误: {str(e)}"


@mcp.prompt()
def create_image_prompt(
    subject: str,
    style: str = "现实主义",
    mood: str = "中性",
    quality: str = "高质量"
) -> str:
    """
    生成图片创建提示词
    
    Args:
        subject: 主题内容（必需）
        style: 艺术风格（默认"现实主义"）
        mood: 情绪氛围（默认"中性"）
        quality: 质量要求（默认"高质量"）
    
    Returns:
        格式化的图片生成提示词
    """
    prompt_parts = []
    
    # 主题
    prompt_parts.append(f"主题: {subject}")
    
    # 风格
    prompt_parts.append(f"风格: {style}")
    
    # 情绪
    prompt_parts.append(f"氛围: {mood}")
    
    # 质量
    prompt_parts.append(f"质量: {quality}，详细，清晰，专业")
    
    return "，".join(prompt_parts)


def run_server():
    """运行 MCP 服务器"""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run_server()
