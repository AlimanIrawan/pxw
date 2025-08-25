#!/bin/bash

# Detik新闻爬虫 - 一键部署到GitHub脚本

echo "🚀 Detik新闻爬虫 - 云端部署脚本"
echo "=================================="

# 检查Git是否已安装
if ! command -v git &> /dev/null; then
    echo "❌ Git未安装，请先安装Git"
    exit 1
fi

# 设置仓库信息
REPO_URL="https://github.com/AlimanIrawan/pxw.git"
REPO_NAME="pxw"

echo "📋 目标仓库: $REPO_URL"
echo ""

# 检查当前目录
CURRENT_DIR=$(pwd)
echo "📁 当前目录: $CURRENT_DIR"

# 初始化Git仓库（如果未初始化）
if [ ! -d ".git" ]; then
    echo "🔧 初始化Git仓库..."
    git init
    echo "✅ Git仓库初始化完成"
else
    echo "✅ Git仓库已存在"
fi

# 添加远程仓库
echo "🔗 配置远程仓库..."
git remote remove origin 2>/dev/null || true
git remote add origin $REPO_URL
echo "✅ 远程仓库配置完成"

# 配置Git用户信息（如果未配置）
if [ -z "$(git config user.name)" ]; then
    echo "👤 请输入你的GitHub用户名:"
    read -r git_username
    git config user.name "$git_username"
fi

if [ -z "$(git config user.email)" ]; then
    echo "📧 请输入你的GitHub邮箱:"
    read -r git_email
    git config user.email "$git_email"
fi

echo "✅ Git用户信息配置完成"

# 创建必要的目录结构
echo "📁 创建目录结构..."
mkdir -p output/latest
mkdir -p logs
mkdir -p templates

# 创建output目录的README
cat > output/README.txt << EOF
Detik新闻爬虫输出目录

此目录用于存储爬取的新闻文件：

目录结构：
- 日期目录（如2025-08-24）：存储指定日期的新闻文件
- latest/：存储最新一次爬取的文件

文件类型：
- detik_news_YYYY-MM-DD.txt：完整新闻内容
- detik_news_YYYY-MM-DD_summary.txt：新闻摘要（仅标题、时间、链接）

注意：此目录会被Git跟踪，用于云端文件存储
EOF

echo "✅ 目录结构创建完成"

# 添加所有文件到Git
echo "📦 添加文件到Git..."
git add .

# 检查是否有文件需要提交
if git diff --staged --quiet; then
    echo "⚠️  没有新文件需要提交"
else
    echo "📝 提交文件..."
    git commit -m "🚀 Initial deployment: Detik新闻爬虫云端版

特性：
- ✅ Web控制界面（Flask + HTML）
- ✅ 自动定时爬取（每日凌晨3点UTC）
- ✅ GitHub自动存储
- ✅ 双文件输出（完整版+摘要版）
- ✅ 云端Linux环境优化
- ✅ ChromeDriver兼容性修复

部署平台：Render.com
成本：完全免费

使用方式：
1. Web界面手动爬取
2. 定时任务自动爬取
3. GitHub下载文件"

    echo "✅ 文件提交完成"
fi

# 推送到远程仓库
echo "🌐 推送到GitHub..."
echo "注意：首次推送可能需要输入GitHub用户名和密码/Token"

if git push -u origin main; then
    echo "✅ 推送成功！"
else
    echo "⚠️  推送失败，尝试强制推送..."
    if git push -u origin main --force; then
        echo "✅ 强制推送成功！"
    else
        echo "❌ 推送失败，请检查："
        echo "   1. GitHub用户名和密码/Token是否正确"
        echo "   2. 仓库权限是否正确"
        echo "   3. 网络连接是否正常"
        exit 1
    fi
fi

echo ""
echo "🎉 部署完成！"
echo "=================================="
echo "📱 接下来的步骤："
echo ""
echo "1. 📁 GitHub仓库地址："
echo "   $REPO_URL"
echo ""
echo "2. 🌐 部署到Render："
echo "   - 访问 https://render.com"
echo "   - 注册并登录账号"
echo "   - 点击 'New' -> 'Blueprint'"
echo "   - 连接GitHub仓库: AlimanIrawan/pxw"
echo "   - 点击 'Apply' 开始部署"
echo ""
echo "3. ✨ 部署完成后你将获得："
echo "   - 🕸️  Web控制界面（手动爬取）"
echo "   - ⏰ 定时任务（每日凌晨3点UTC自动爬取）"
echo "   - 📁 GitHub文件存储（永久保存）"
echo ""
echo "4. 💡 使用提示："
echo "   - Web界面可以随时手动爬取"
echo "   - 文件自动保存到GitHub的output目录"
echo "   - 每天自动爬取前一天的新闻"
echo ""
echo "🎯 总成本：免费（GitHub免费 + Render免费套餐）"
echo ""
echo "❓ 如果需要帮助，请查看 README_DEPLOYMENT.txt 文件"
