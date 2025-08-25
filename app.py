#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask Web应用 - 新闻爬虫控制界面
用于云端部署的Web控制台
"""

import os
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_file
from threading import Thread
import logging
import schedule
import time

from detik_crawler import DetikCrawler
from simple_crawler import SimpleCrawler
from data_processor import DataProcessor
from config import ConfigManager
from logger import get_logger

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = get_logger()

def add_task_log(message, level='info'):
    """添加日志到任务状态"""
    from datetime import datetime
    timestamp = datetime.now().strftime('%H:%M:%S')
    log_entry = {
        'timestamp': timestamp,
        'level': level,
        'message': message
    }
    task_status['logs'].append(log_entry)
    
    # 只保留最近100条日志
    if len(task_status['logs']) > 100:
        task_status['logs'] = task_status['logs'][-100:]
    
    # 同时写入标准日志
    if level == 'error':
        logger.error(message)
    elif level == 'warning':
        logger.warning(message)
    else:
        logger.info(message)

# 全局变量存储任务状态
task_status = {
    'running': False,
    'progress': 0,
    'message': '准备就绪',
    'total_news': 0,
    'current_news': 0,
    'output_files': [],
    'logs': []  # 实时日志缓存
}

@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')

@app.route('/start_crawl', methods=['POST'])
def start_crawl():
    """开始爬取任务"""
    global task_status
    
    if task_status['running']:
        return jsonify({'error': '爬虫正在运行中，请等待完成'})
    
    data = request.get_json()
    target_date = data.get('date')
    
    if not target_date:
        return jsonify({'error': '请选择日期'})
    
    # 重置任务状态
    task_status = {
        'running': True,
        'progress': 0,
        'message': '正在初始化...',
        'total_news': 0,
        'current_news': 0,
        'output_files': [],
        'logs': []
    }
    
    # 在后台线程中运行爬虫
    thread = Thread(target=run_crawler, args=(target_date,))
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'message': '爬虫已启动'})

@app.route('/status')
def get_status():
    """获取任务状态"""
    return jsonify(task_status)

@app.route('/download/<filename>')
def download_file(filename):
    """下载文件"""
    file_path = os.path.join('output', filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return jsonify({'error': '文件不存在'})

@app.route('/logs')
def get_logs():
    """获取最新日志"""
    try:
        log_files = [f for f in os.listdir('logs') if f.endswith('.log')]
        if log_files:
            latest_log = max(log_files)
            log_path = os.path.join('logs', latest_log)
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # 返回最后50行日志
                return jsonify({'logs': lines[-50:]})
    except Exception as e:
        logger.error(f"获取日志失败: {e}")
    
    return jsonify({'logs': []})

def run_crawler(target_date):
    """运行爬虫的后台任务"""
    global task_status
    
    try:
        # 步骤1: 初始化
        task_status['message'] = '🔧 正在初始化爬虫组件...'
        task_status['progress'] = 5
        task_status['logs'] = []  # 清空之前的日志
        add_task_log(f"🚀 开始爬取任务，目标日期: {target_date}")
        
        # 初始化组件
        config = ConfigManager()
        task_status['progress'] = 10
        task_status['message'] = '🔧 正在设置爬虫配置...'
        add_task_log("📝 初始化配置管理器")
        
        processor = DataProcessor(config)
        task_status['progress'] = 15
        add_task_log("💾 初始化数据处理器")
        
        # 尝试使用Chrome爬虫，失败则使用简化爬虫
        crawler = None
        use_simple_crawler = False
        
        if os.environ.get('RENDER'):
            # 云端环境：直接使用简化爬虫
            task_status['message'] = '🔧 云端环境，使用简化爬虫...'
            add_task_log("☁️ 检测到云端环境，使用简化爬虫")
            crawler = SimpleCrawler(config)
            use_simple_crawler = True
            task_status['progress'] = 20
        else:
            # 本地环境：尝试Chrome爬虫
            try:
                task_status['message'] = '🕷️ 正在启动Chrome浏览器...'
                add_task_log("🌐 本地环境，尝试启动Chrome爬虫")
                crawler = DetikCrawler(config)
                task_status['progress'] = 20
            except Exception as e:
                add_task_log(f"⚠️ Chrome爬虫初始化失败: {e}", "warning")
                task_status['message'] = '🔧 Chrome失败，使用简化爬虫...'
                add_task_log("🔄 切换到简化爬虫")
                crawler = SimpleCrawler(config)
                use_simple_crawler = True
                task_status['progress'] = 20
        
        # 自定义进度回调
        def progress_callback(current, total, message):
            if total > 0:
                crawl_progress = 20 + (current / total) * 50  # 20-70%的进度用于爬取
                task_status['progress'] = int(crawl_progress)
                task_status['current_news'] = current
                task_status['total_news'] = total
                task_status['message'] = message
        
        # 爬取新闻
        add_task_log(f"🚀 开始爬取新闻数据")
        news_data = crawler.crawl_news(target_date)
        
        if not news_data:
            task_status['running'] = False
            task_status['message'] = '❌ 未获取到新闻数据，请检查日期或网络连接'
            task_status['progress'] = 0
            add_task_log("❌ 爬取结果为空", "error")
            return
        
        task_status['total_news'] = len(news_data)
        task_status['current_news'] = len(news_data)
        task_status['progress'] = 70
        task_status['message'] = f'✅ 爬取完成！共获取 {len(news_data)} 篇新闻'
        add_task_log(f"✅ 爬取成功，共获取 {len(news_data)} 篇新闻", "success")
        
        # 步骤3: 保存数据
        task_status['message'] = '💾 正在保存数据文件...'
        task_status['progress'] = 75
        add_task_log("💾 开始保存数据到文件")
        
        try:
            output_file = processor.save_news_data(news_data, target_date)
            task_status['progress'] = 80
            task_status['message'] = '✅ 数据文件保存完成'
            add_task_log(f"✅ 数据文件保存成功: {output_file}", "success")
        except Exception as e:
            add_task_log(f"❌ 数据文件保存失败: {e}", "error")
            task_status['running'] = False
            task_status['message'] = '❌ 数据文件保存失败'
            return
        
        # 记录输出文件
        output_dir = config.get_output_dir()
        files = []
        for filename in os.listdir(output_dir):
            if target_date in filename and filename.endswith('.txt'):
                file_path = os.path.join(output_dir, filename)
                if os.path.exists(file_path):
                    files.append({
                        'name': filename,
                        'size': os.path.getsize(file_path),
                        'url': f'/download/{filename}'
                    })
        
        task_status['output_files'] = files
        task_status['progress'] = 85
        logger.info(f"生成文件: {[f['name'] for f in files]}")
        
        # 步骤4: 提交到GitHub（如果在云端环境）
        if os.environ.get('RENDER'):
            task_status['message'] = '📤 正在上传到GitHub...'
            task_status['progress'] = 90
            commit_to_github(target_date, files)
            task_status['message'] = '✅ GitHub上传完成'
            task_status['progress'] = 95
        else:
            task_status['progress'] = 95
        
        # 完成
        task_status['progress'] = 100
        task_status['message'] = f'🎉 任务完成！共爬取 {len(news_data)} 篇新闻，生成 {len(files)} 个文件'
        logger.info(f"爬取任务完成: {len(news_data)}篇新闻, {len(files)}个文件")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"爬虫任务失败: {error_msg}", exc_info=True)
        task_status['message'] = f'❌ 任务失败: {error_msg}'
        task_status['progress'] = 0
        
        # 根据错误类型提供更具体的提示
        if 'ChromeDriver' in error_msg or 'Chrome' in error_msg:
            task_status['message'] += ' (Chrome浏览器问题)'
        elif 'timeout' in error_msg.lower():
            task_status['message'] += ' (网络超时)'
        elif 'connection' in error_msg.lower():
            task_status['message'] += ' (网络连接问题)'
            
    finally:
        task_status['running'] = False

def commit_to_github(target_date, files):
    """提交文件到GitHub"""
    try:
        import subprocess
        import shutil
        
        # 创建日期目录
        date_dir = os.path.join('output', target_date)
        os.makedirs(date_dir, exist_ok=True)
        
        # 移动文件到日期目录
        for file_info in files:
            filename = file_info['name']
            src = os.path.join('output', filename)
            dst = os.path.join(date_dir, filename)
            if os.path.exists(src):
                shutil.move(src, dst)
        
        # 复制到latest目录
        latest_dir = os.path.join('output', 'latest')
        os.makedirs(latest_dir, exist_ok=True)
        
        for file_info in files:
            filename = file_info['name']
            src = os.path.join(date_dir, filename)
            # 重命名为latest
            dst_name = filename.replace(target_date, 'latest')
            dst = os.path.join(latest_dir, dst_name)
            if os.path.exists(src):
                shutil.copy2(src, dst)
        
        # Git操作
        subprocess.run(['git', 'add', 'output/'], check=True)
        commit_msg = f"Auto crawl: {target_date} - {len(files)} files"
        subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
        subprocess.run(['git', 'push'], check=True)
        
        logger.info(f"成功提交到GitHub: {commit_msg}")
        
    except Exception as e:
        logger.error(f"GitHub提交失败: {e}")

def daily_auto_crawl():
    """每日自动爬取任务"""
    try:
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        logger.info(f"开始执行每日自动爬取任务，目标日期: {yesterday}")
        
        config = ConfigManager()
        crawler = DetikCrawler(config)
        processor = DataProcessor(config)
        
        # 爬取新闻
        news_data = crawler.crawl_news(yesterday)
        
        if news_data:
            # 保存数据
            processor.save_news_data(news_data, yesterday)
            
            # 提交到GitHub（如果在云端环境）
            if os.environ.get('RENDER'):
                from daily_task import organize_and_commit_files
                organize_and_commit_files(yesterday, logger)
            
            logger.info(f"每日自动爬取完成，共获取 {len(news_data)} 篇新闻")
        else:
            logger.warning("每日自动爬取未获取到数据")
            
    except Exception as e:
        logger.error(f"每日自动爬取失败: {e}")

def setup_scheduler():
    """设置定时任务"""
    # 每天凌晨3点UTC执行（北京时间11点）
    schedule.every().day.at("03:00").do(daily_auto_crawl)
    logger.info("定时任务已设置：每天凌晨3点UTC自动爬取")
    
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
    
    # 在后台线程中运行定时器
    scheduler_thread = Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

def ensure_directories():
    """确保必要的目录存在"""
    directories = ['output', 'logs', 'templates', 'output/latest']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        if logger:
            logger.info(f"确保目录存在: {directory}")

# 在应用启动时创建目录
ensure_directories()

if __name__ == '__main__':
    # 应用已经创建了目录
    
    # 设置定时任务（仅在云端环境）
    if os.environ.get('RENDER'):
        setup_scheduler()
        logger.info("云端环境：定时任务已启动")
    else:
        logger.info("本地环境：跳过定时任务设置")
    
    # 运行应用
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
