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

from detik_crawler import DetikCrawler
from data_processor import DataProcessor
from config import ConfigManager
from logger import get_logger

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = get_logger()

# 全局变量存储任务状态
task_status = {
    'running': False,
    'progress': 0,
    'message': '准备就绪',
    'total_news': 0,
    'current_news': 0,
    'output_files': []
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
        'output_files': []
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
        task_status['message'] = '正在初始化爬虫...'
        task_status['progress'] = 10
        
        # 初始化组件
        config = ConfigManager()
        crawler = DetikCrawler(config)
        processor = DataProcessor(config)
        
        task_status['message'] = '开始爬取新闻...'
        task_status['progress'] = 20
        
        # 爬取新闻
        news_data = crawler.crawl_news(target_date)
        
        if not news_data:
            task_status['running'] = False
            task_status['message'] = '未获取到新闻数据'
            return
        
        task_status['total_news'] = len(news_data)
        task_status['progress'] = 70
        task_status['message'] = f'爬取完成，共获取 {len(news_data)} 篇新闻'
        
        # 保存数据
        task_status['message'] = '正在保存数据...'
        task_status['progress'] = 80
        
        output_file = processor.save_news_data(news_data, target_date)
        
        # 记录输出文件
        output_dir = config.get_output_dir()
        files = []
        for filename in os.listdir(output_dir):
            if target_date in filename:
                files.append({
                    'name': filename,
                    'size': os.path.getsize(os.path.join(output_dir, filename)),
                    'url': f'/download/{filename}'
                })
        
        task_status['output_files'] = files
        task_status['progress'] = 90
        
        # 提交到GitHub（如果在云端环境）
        if os.environ.get('RENDER'):
            task_status['message'] = '正在提交到GitHub...'
            commit_to_github(target_date, files)
        
        task_status['progress'] = 100
        task_status['message'] = f'任务完成！共爬取 {len(news_data)} 篇新闻'
        
    except Exception as e:
        logger.error(f"爬虫任务失败: {e}")
        task_status['message'] = f'任务失败: {str(e)}'
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

if __name__ == '__main__':
    # 创建必要的目录
    os.makedirs('output', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    
    # 运行应用
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
