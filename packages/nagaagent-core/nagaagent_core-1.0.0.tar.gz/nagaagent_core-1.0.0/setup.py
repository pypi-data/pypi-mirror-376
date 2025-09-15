"""
NagaAgent_core 包安装脚本

按照PyPI发布教程的标准格式
"""

from setuptools import setup, find_packages
import os

# 读取README文件
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# 读取requirements文件
def read_requirements():
    requirements = []
    if os.path.exists("requirements.txt"):
        with open("requirements.txt", "r", encoding="utf-8") as fh:
            requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]
    return requirements

setup(
    name="nagaagent-core",
    version="1.0.0",
    author="NagaAgent Team",
    author_email="naga@example.com",
    description="娜迦AI助手核心功能包 - 基础框架，包含API服务器、Agent框架、日志管理等核心组件",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/Xxiii8322766509/NagaAgent",
    project_urls={
        "Bug Tracker": "https://github.com/Xxiii8322766509/NagaAgent/issues",
        "Documentation": "https://github.com/Xxiii8322766509/NagaAgent",
        "Source Code": "https://github.com/Xxiii8322766509/NagaAgent",
    },
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
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pydantic>=2.0.0",
        "asyncio-mqtt>=0.11.0",
        "aiohttp>=3.8.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.20.0",
        "websockets>=11.0.0",
        "psutil>=5.9.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "coverage>=7.0.0",
        ],
        "docs": [
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.2.0",
            "myst-parser>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "nagaagent-core=NagaAgent_core.cli:main",
            "naga-api=NagaAgent_core.api.server:run_api_server",
        ],
    },
    include_package_data=True,
    package_data={
        "NagaAgent_core": ["py.typed"],
    },
    zip_safe=False,
)