#!/bin/bash

# ChromeDriver权限修复脚本

echo "=== ChromeDriver权限修复脚本 ==="

# 查找所有ChromeDriver文件
echo "查找ChromeDriver文件..."
chromedriver_files=$(find /Users/LW/.wdm -name "chromedriver" -type f 2>/dev/null)

if [ -z "$chromedriver_files" ]; then
    echo "未找到ChromeDriver文件"
    exit 1
fi

# 为每个ChromeDriver文件设置权限
for file in $chromedriver_files; do
    echo "处理文件: $file"
    
    # 设置执行权限
    chmod +x "$file"
    echo "  ✓ 已设置执行权限"
    
    # 移除macOS安全属性
    xattr -d com.apple.quarantine "$file" 2>/dev/null
    xattr -d com.apple.provenance "$file" 2>/dev/null
    echo "  ✓ 已移除安全属性"
    
    # 验证权限
    if [ -x "$file" ]; then
        echo "  ✓ 文件可执行"
    else
        echo "  ✗ 文件不可执行"
    fi
done

echo ""
echo "ChromeDriver权限修复完成！"
echo ""
echo "如果仍有问题，请尝试："
echo "1. 清理ChromeDriver缓存: rm -rf ~/.wdm"
echo "2. 重新启动程序"
