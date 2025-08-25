#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志管理模块
"""

import logging
import os
from datetime import datetime

def setup_logger(log_dir: str = 'logs') -> logging.Logger:
    """设置日志记录器
    
    Args:
        log_dir: 日志目录
        
    Returns:
        配置好的日志记录器
    """
    # 确保日志目录存在
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 创建日志文件名
    log_filename = f"crawler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_filepath = os.path.join(log_dir, log_filename)
    
    # 配置日志记录器
    logger = logging.getLogger('detik_crawler')
    logger.setLevel(logging.INFO)
    
    # 清除现有的处理器
    logger.handlers.clear()
    
    # 文件处理器
    file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 设置格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_logger() -> logging.Logger:
    """获取日志记录器"""
    return logging.getLogger('detik_crawler')
