#!/bin/bash
# 在Render云端环境安装Chrome浏览器

echo "检测操作系统..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "检测到Linux环境，开始安装Chrome..."
    
    # 更新包列表
    apt-get update
    
    # 安装依赖
    apt-get install -y wget gnupg2 software-properties-common
    
    # 添加Google Chrome仓库
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
    
    # 更新包列表
    apt-get update
    
    # 安装Chrome
    apt-get install -y google-chrome-stable
    
    # 验证安装
    if which google-chrome-stable > /dev/null; then
        echo "✅ Chrome安装成功"
        google-chrome-stable --version
    else
        echo "❌ Chrome安装失败"
        exit 1
    fi
    
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "检测到macOS环境，Chrome应该已经安装"
    if which google-chrome > /dev/null || which "Google Chrome" > /dev/null; then
        echo "✅ Chrome已安装"
    else
        echo "❌ macOS环境下请手动安装Chrome"
        exit 1
    fi
else
    echo "❌ 不支持的操作系统: $OSTYPE"
    exit 1
fi

echo "Chrome安装检查完成"
