# Nano Banana MCP Server

一个使用 Gemini 2.5 Flash Image（又称 Nano Banana）模型进行图片生成和编辑的 MCP (Model Context Protocol) 服务器。该服务可与支持 MCP 的 AI 助手（如 Claude）集成，使其能够生成和编辑图片。

## 功能特性

* **图片生成**：根据文本提示词生成高质量图片
* **图片编辑**：编辑现有图片，支持各种修改操作
* **图片信息查看**：获取图片的基本信息（尺寸、格式、大小等）
* **图片列表管理**：列出生成目录中的所有图片
* **资源访问**：通过 `image://` URL 方案访问图片
* **提示词助手**：帮助生成优化的图片生成提示词

## 环境变量配置

在使用前，请设置以下环境变量：

```bash
# 必需
export GEMINI_API_KEY="your_gemini_api_key_here"

# 可选
export GEMINI_API_BASE="https://generativelanguage.googleapis.com"  # 默认值
export OUTPUT_IMAGE_PATH="./generated_images"  # 默认值
```

## 安装

### 使用 pip 安装依赖

```bash
cd nano_banana_mcp_server
pip install -r requirements.txt
```

### 使用 uv 安装（推荐）

```bash
cd nano_banana_mcp_server
uv install
```

## 使用方法

### 作为 MCP 服务器运行

```bash
# 本地开发使用 uv run（推荐）
uv run nano-banana-mcp

# 或使用 Python
python -m nano_banana_mcp

# 如果包已发布到 PyPI，可以使用 uvx
uvx --from nano-banana-mcp-server nano-banana-mcp
```

### MCP 客户端配置

在支持 MCP 的应用中，添加以下配置：

```json
{
  "mcpServers": {
    "nano-banana-image": {
      "command": "uvx",
      "args": [
        "--from",
        "nano-banana-mcp-server",
        "nano-banana-mcp"
      ],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here",
        "OUTPUT_IMAGE_PATH": "./generated_images"
      }
    }
  }
}
```

或者使用本地开发版本：

```json
{
  "mcpServers": {
    "nano-banana-image": {
      "command": "uv",
      "args": [
        "run",
        "nano-banana-mcp"
      ],
      "cwd": "/path/to/nano_banana_mcp_server",
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here"
      }
    }
  }
}
```

## 可用工具

### 1. generate_image
生成新图片

**参数：**
- `prompt` (必需): 图片生成提示词
- `negative_prompt` (可选): 负面提示词
- `width` (可选): 图片宽度，默认 1024
- `height` (可选): 图片高度，默认 1024
- `guidance_scale` (可选): 引导强度，默认 7.0
- `num_inference_steps` (可选): 推理步数，默认 20
- `seed` (可选): 随机种子
- `output_filename` (可选): 输出文件名

**示例：**
```python
generate_image(
    prompt="一只可爱的橙色小猫坐在阳光明媚的窗台上",
    width=1024,
    height=1024
)
```

### 2. edit_image
编辑现有图片

**参数：**
- `image_path` (必需): 原始图片路径
- `prompt` (必需): 编辑提示词
- `negative_prompt` (可选): 负面提示词
- `guidance_scale` (可选): 引导强度，默认 7.0
- `num_inference_steps` (可选): 推理步数，默认 20
- `strength` (可选): 编辑强度 (0.0-1.0)，默认 0.8
- `seed` (可选): 随机种子
- `output_filename` (可选): 输出文件名

**示例：**
```python
edit_image(
    image_path="./generated_images/cat.png",
    prompt="给猫咪添加一个红色的蝴蝶结"
)
```

### 3. get_image_info
获取图片信息

**参数：**
- `image_path` (必需): 图片路径

### 4. list_generated_images
列出所有生成的图片

### 5. create_image_prompt
生成优化的图片提示词

**参数：**
- `subject` (必需): 主题内容
- `style` (可选): 艺术风格，默认"现实主义"
- `mood` (可选): 情绪氛围，默认"中性"
- `quality` (可选): 质量要求，默认"高质量"

## 资源类型

### image://
通过 `image://path/to/image.png` 访问图片资源，返回 base64 编码的图片数据。

## 技术细节

- **模型**: Gemini 2.5 Flash Image Preview (gemini-2.5-flash-image-preview)
- **支持格式**: PNG, JPG, JPEG, BMP, GIF, TIFF, WebP
- **默认输出**: PNG 格式
- **API**: Google Generative AI API

## 错误处理

服务器包含完善的错误处理机制：
- API 密钥验证
- 文件路径验证
- 图片格式验证
- 网络请求错误处理
- 模型响应验证

## 许可证

MIT License

## 开发

### 项目结构
```
nano_banana_mcp_server/
├── nano_banana_mcp/
│   ├── __init__.py
│   ├── __main__.py
│   └── server.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

### 贡献

欢迎提交 Issues 和 Pull Requests！

## 故障排除

### 常见问题

1. **API 密钥错误**
   - 确保设置了正确的 `GEMINI_API_KEY` 环境变量
   - 验证 API 密钥有效性

2. **图片生成失败**
   - 检查网络连接
   - 确保提示词不包含违规内容
   - 尝试简化提示词

3. **文件路径错误**
   - 确保图片文件存在
   - 检查文件权限
   - 使用绝对路径

4. **内存不足**
   - 降低图片分辨率
   - 减少并发请求数量

### 日志和调试

运行时使用 `-v` 参数启用详细日志：

```bash
nano-banana-mcp -v
```
