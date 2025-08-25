#!/bin/bash

# Detik新闻爬虫启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "脚本目录: $SCRIPT_DIR"

# 切换到脚本所在目录
cd "$SCRIPT_DIR"
echo "已切换到工作目录: $(pwd)"

echo "=== Detik新闻爬虫启动脚本 ==="
echo "正在检查Python环境..."

# 检查Python版本
python_version=$(python3 --version 2>&1)
echo "Python版本: $python_version"

# 检查虚拟环境
if [ -d "venv" ]; then
    echo "发现虚拟环境，正在激活..."
    source venv/bin/activate
    echo "虚拟环境已激活"
else
    echo "未发现虚拟环境，正在创建..."
    python3 -m venv venv
    source venv/bin/activate
    echo "虚拟环境已创建并激活"
    
    echo "正在安装依赖包..."
    pip install -r requirements.txt
    echo "依赖包安装完成"
fi

# 检查Chrome浏览器
if command -v google-chrome &> /dev/null; then
    echo "Chrome浏览器已安装"
elif command -v chromium-browser &> /dev/null; then
    echo "Chromium浏览器已安装"
else
    echo "警告: 未检测到Chrome或Chromium浏览器"
    echo "请确保已安装Chrome浏览器"
fi

echo "启动命令行界面..."
python3 cli.py

echo "程序已退出"
