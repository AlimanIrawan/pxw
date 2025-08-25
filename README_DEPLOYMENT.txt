Detik新闻爬虫 - 云端部署指南

=== 部署准备 ===

1. GitHub仓库准备：
   - 在GitHub创建新仓库（例如：detik-crawler）
   - 将本项目代码推送到仓库

2. Render账号准备：
   - 注册Render账号（https://render.com）
   - 连接GitHub账号

=== 部署步骤 ===

第一步：推送代码到GitHub
```bash
cd /Users/LW/Documents/AIPLUS/新闻播报/detik_crawler
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/你的用户名/detik-crawler.git
git push -u origin main
```

第二步：在Render部署
1. 登录Render控制台
2. 点击"New" -> "Blueprint"
3. 连接GitHub仓库
4. 选择刚创建的detik-crawler仓库
5. Render会自动读取render.yaml配置
6. 点击"Apply"开始部署

第三步：配置环境变量（可选）
在Render控制台的Environment设置中添加：
- SECRET_KEY: 随机字符串（用于Flask会话）

=== 使用方式 ===

部署完成后，你将获得：

1. Web控制界面：
   - 访问Render提供的网址
   - 可以手动选择日期进行爬取
   - 实时查看爬取进度
   - 下载生成的文件

2. 自动定时任务：
   - 每天凌晨3点（UTC时间）自动爬取前一天的新闻
   - 相当于北京时间上午11点
   - 自动提交到GitHub仓库

=== 文件下载 ===

方式1：GitHub直接下载
- 访问GitHub仓库的output目录
- 按日期查找文件
- 或在latest目录下载最新文件

方式2：Web界面下载
- 手动运行爬虫后可直接下载

=== 文件结构 ===

GitHub仓库的output目录结构：
```
output/
├── 2025-08-24/
│   ├── detik_news_2025-08-24.txt          # 完整版
│   └── detik_news_2025-08-24_summary.txt  # 摘要版
├── 2025-08-25/
│   ├── detik_news_2025-08-25.txt
│   └── detik_news_2025-08-25_summary.txt
└── latest/
    ├── detik_news_latest.txt               # 最新完整版
    └── detik_news_latest_summary.txt       # 最新摘要版
```

=== 成本 ===

- GitHub：免费
- Render免费套餐：
  - Web服务：750小时/月（足够使用）
  - Cron任务：免费
  - 总成本：$0/月

=== 注意事项 ===

1. 时区设置：
   - Render使用UTC时间
   - 凌晨3点UTC = 北京时间上午11点

2. 文件保存：
   - 所有爬取的文件都保存在GitHub
   - Render服务器重启时本地文件会丢失
   - 但GitHub中的文件永久保存

3. 手动运行：
   - 可以通过Web界面随时手动运行爬虫
   - 不受定时任务限制

=== 故障排除 ===

如果部署失败：
1. 检查render.yaml语法
2. 确认requirements.txt中的包版本
3. 查看Render的部署日志

如果爬虫失败：
1. 查看Web界面的日志输出
2. 检查GitHub提交权限
3. 确认Chrome在Linux环境下的兼容性

=== 联系 ===

部署过程中如有问题，请检查：
1. Render部署日志
2. GitHub Actions（如果启用）
3. Web界面的实时日志
