"""Setup script for nano-banana-mcp-server."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="google-nano-banana-mcp-server",
    version="1.0.0",
    author="AI Assistant",
    author_email="ai@example.com",
    description="一个使用 Gemini 2.5 Flash Image 模型的图片生成和编辑 MCP 服务器",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/nano-banana-mcp-server",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "nano-banana-mcp=nano_banana_mcp.__main__:main",
        ],
    },
    include_package_data=True,
    package_data={
        "nano_banana_mcp": ["*.py"],
    },
)
