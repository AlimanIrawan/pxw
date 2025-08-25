#!/bin/bash

# Detik新闻爬虫GUI启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "脚本目录: $SCRIPT_DIR"

# 切换到脚本所在目录
cd "$SCRIPT_DIR"
echo "已切换到工作目录: $(pwd)"

echo "=== Detik新闻爬虫GUI启动脚本 ==="
echo "正在检查Python环境..."

# 检查Python版本
python_version=$(python3 --version 2>&1)
echo "Python版本: $python_version"

# 检查虚拟环境
if [ -d "venv" ]; then
    echo "发现虚拟环境，正在激活..."
    source venv/bin/activate
    echo "虚拟环境已激活"
    
    # 检查虚拟环境中的Python路径
    venv_python=$(which python3)
    echo "虚拟环境Python路径: $venv_python"
    
    # 检查依赖包
    echo "检查依赖包..."
    if ! python3 -c "import requests, beautifulsoup4, selenium, webdriver_manager, pytz" 2>/dev/null; then
        echo "依赖包不完整，正在重新安装..."
        # 检查pip是否可用
        if ! command -v pip &> /dev/null; then
            echo "❌ pip不可用，请检查虚拟环境"
            echo "尝试重新创建虚拟环境..."
            cd ..
            rm -rf venv
            python3 -m venv venv
            cd "$SCRIPT_DIR"
            source venv/bin/activate
            pip install --upgrade pip
        fi
        
        if pip install -r requirements.txt; then
            echo "✅ 依赖包安装完成"
        else
            echo "❌ 依赖包安装失败，请检查网络连接和requirements.txt文件"
            exit 1
        fi
    else
        echo "✅ 依赖包检查通过"
    fi
else
    echo "未发现虚拟环境，正在创建..."
    python3 -m venv venv
    source venv/bin/activate
    echo "虚拟环境已创建并激活"
    
    echo "正在安装依赖包..."
    pip install --upgrade pip
    if pip install -r requirements.txt; then
        echo "✅ 依赖包安装完成"
    else
        echo "❌ 依赖包安装失败，请检查网络连接和requirements.txt文件"
        exit 1
    fi
fi

# 检查tkinter
echo "检查tkinter支持..."
if python3 -c "import tkinter; print('✅ tkinter可用')" 2>/dev/null; then
    echo ""
else
    echo "❌ tkinter不可用，请使用命令行版本: ./启动爬虫.sh"
    echo "或者安装tkinter支持: brew install python-tk@3.13"
    exit 1
fi

# 检查Chrome浏览器
if [ -d "/Applications/Google Chrome.app" ]; then
    echo "✅ Chrome浏览器已安装"
elif command -v google-chrome &> /dev/null; then
    echo "✅ Chrome浏览器已安装"
elif command -v chromium-browser &> /dev/null; then
    echo "✅ Chromium浏览器已安装"
else
    echo "⚠️  警告: 未检测到Chrome或Chromium浏览器"
    echo "   请确保已安装Chrome浏览器"
    echo "   下载链接: https://www.google.com/chrome/"
fi

# 修复ChromeDriver权限
echo "检查ChromeDriver权限..."
if [ -f "fix_chromedriver.sh" ]; then
    ./fix_chromedriver.sh
else
    echo "ChromeDriver修复脚本不存在，跳过权限修复"
fi

echo "启动GUI界面..."
if python3 main.py; then
    echo "✅ 程序正常退出"
else
    echo "❌ 程序执行出错，请查看错误信息"
    echo "如需帮助，请查看logs目录中的日志文件"
    exit 1
fi
