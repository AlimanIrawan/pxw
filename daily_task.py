#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务脚本 - 每日自动爬取新闻
用于Render Cron Job
"""

import os
import sys
import shutil
import subprocess
from datetime import datetime, timedelta

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from detik_crawler import DetikCrawler
from data_processor import DataProcessor
from config import ConfigManager
from logger import get_logger

def main():
    """主函数 - 执行每日爬取任务"""
    logger = get_logger()
    
    try:
        # 计算昨天的日期
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        logger.info(f"开始执行每日爬取任务，目标日期: {yesterday}")
        
        # 初始化组件
        config = ConfigManager()
        crawler = DetikCrawler(config)
        processor = DataProcessor(config)
        
        # 爬取新闻
        logger.info("开始爬取新闻...")
        news_data = crawler.crawl_news(yesterday)
        
        if not news_data:
            logger.warning("未获取到新闻数据")
            return False
        
        logger.info(f"成功爬取 {len(news_data)} 篇新闻")
        
        # 保存数据
        logger.info("开始保存数据...")
        output_file = processor.save_news_data(news_data, yesterday)
        logger.info(f"数据已保存到: {output_file}")
        
        # 组织文件结构并提交到GitHub
        organize_and_commit_files(yesterday, logger)
        
        logger.info("每日爬取任务执行完成")
        return True
        
    except Exception as e:
        logger.error(f"每日爬取任务失败: {e}", exc_info=True)
        return False

def organize_and_commit_files(target_date, logger):
    """组织文件结构并提交到GitHub"""
    try:
        output_dir = 'output'
        
        # 1. 创建日期目录
        date_dir = os.path.join(output_dir, target_date)
        os.makedirs(date_dir, exist_ok=True)
        logger.info(f"创建日期目录: {date_dir}")
        
        # 2. 移动文件到日期目录
        files_moved = []
        for filename in os.listdir(output_dir):
            if target_date in filename and filename.endswith('.txt'):
                src = os.path.join(output_dir, filename)
                dst = os.path.join(date_dir, filename)
                if os.path.isfile(src):
                    shutil.move(src, dst)
                    files_moved.append(filename)
                    logger.info(f"移动文件: {filename} -> {date_dir}/")
        
        if not files_moved:
            logger.warning("没有找到需要移动的文件")
            return
        
        # 3. 复制到latest目录
        latest_dir = os.path.join(output_dir, 'latest')
        os.makedirs(latest_dir, exist_ok=True)
        
        for filename in files_moved:
            src = os.path.join(date_dir, filename)
            # 重命名为latest版本
            dst_name = filename.replace(target_date, 'latest')
            dst = os.path.join(latest_dir, dst_name)
            shutil.copy2(src, dst)
            logger.info(f"复制到latest: {dst_name}")
        
        # 4. 提交到GitHub（仅在云端环境）
        if is_cloud_environment():
            commit_to_github(target_date, files_moved, logger)
        else:
            logger.info("本地环境，跳过GitHub提交")
            
    except Exception as e:
        logger.error(f"组织文件结构失败: {e}")

def is_cloud_environment():
    """检查是否在云端环境中"""
    return any(key in os.environ for key in ['RENDER', 'HEROKU', 'RAILWAY'])

def commit_to_github(target_date, files, logger):
    """提交文件到GitHub"""
    try:
        logger.info("开始提交到GitHub...")
        
        # 配置Git用户信息（如果未设置）
        subprocess.run(['git', 'config', '--global', 'user.email', 'crawler@detik.com'], 
                      check=False, capture_output=True)
        subprocess.run(['git', 'config', '--global', 'user.name', 'Detik Crawler'], 
                      check=False, capture_output=True)
        
        # 添加文件到Git
        subprocess.run(['git', 'add', 'output/'], check=True)
        logger.info("文件已添加到Git")
        
        # 检查是否有变更
        result = subprocess.run(['git', 'diff', '--staged', '--name-only'], 
                              capture_output=True, text=True)
        
        if not result.stdout.strip():
            logger.info("没有文件变更，跳过提交")
            return
        
        # 提交更改
        commit_msg = f"Daily crawl: {target_date} - {len(files)} files"
        subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
        logger.info(f"提交消息: {commit_msg}")
        
        # 推送到远程仓库
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)
        logger.info("成功推送到GitHub")
        
        # 记录提交的文件
        logger.info("提交的文件:")
        for filename in files:
            logger.info(f"  - {filename}")
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Git操作失败: {e}")
        logger.error(f"返回码: {e.returncode}")
        if e.stdout:
            logger.error(f"标准输出: {e.stdout}")
        if e.stderr:
            logger.error(f"错误输出: {e.stderr}")
    except Exception as e:
        logger.error(f"GitHub提交过程中出现错误: {e}")

def cleanup_old_files(logger, keep_days=30):
    """清理旧文件，保留最近N天的数据"""
    try:
        output_dir = 'output'
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        
        for item in os.listdir(output_dir):
            item_path = os.path.join(output_dir, item)
            if os.path.isdir(item_path) and item != 'latest':
                try:
                    # 尝试解析日期
                    item_date = datetime.strptime(item, '%Y-%m-%d')
                    if item_date < cutoff_date:
                        shutil.rmtree(item_path)
                        logger.info(f"清理旧目录: {item}")
                except ValueError:
                    # 不是日期格式的目录，跳过
                    continue
                    
    except Exception as e:
        logger.error(f"清理旧文件失败: {e}")

if __name__ == '__main__':
    success = main()
    
    # 清理旧文件
    logger = get_logger()
    cleanup_old_files(logger)
    
    # 设置退出码
    sys.exit(0 if success else 1)
