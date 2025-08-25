#!/bin/bash

# 自动推送Git脚本

echo "=== 自动推送Git脚本 ==="

# 检查是否在Git仓库中
if [ ! -d ".git" ]; then
    echo "初始化Git仓库..."
    git init
    echo "Git仓库已初始化"
fi

# 添加所有文件到暂存区
echo "添加文件到暂存区..."
git add .

# 检查是否有文件需要提交
if git diff --cached --quiet; then
    echo "没有文件需要提交"
    exit 0
fi

# 提交更改
echo "提交更改..."
git commit -m "初始提交: Detik新闻爬虫独立版

- 创建独立的Detik新闻爬虫程序
- 包含GUI界面和完整的爬取功能
- 支持多种输出格式
- 智能时间解析和内容清洗
- 详细的日志记录系统"

echo "提交完成"

# 询问是否要添加远程仓库
echo ""
echo "是否要添加远程仓库？(y/n)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "请输入远程仓库URL:"
    read -r remote_url
    
    if [ -n "$remote_url" ]; then
        echo "添加远程仓库..."
        git remote add origin "$remote_url"
        
        echo "推送到远程仓库..."
        git push -u origin main
        
        if [ $? -eq 0 ]; then
            echo "推送成功！"
        else
            echo "推送失败，请检查远程仓库URL和网络连接"
        fi
    else
        echo "未输入远程仓库URL，跳过推送"
    fi
else
    echo "跳过远程仓库设置"
fi

echo "Git操作完成"
