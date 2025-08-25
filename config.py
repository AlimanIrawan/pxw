#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
"""

import os
from typing import Dict, Any

class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        """初始化配置管理器"""
        self.config = self._set_defaults()
    
    def _set_defaults(self) -> Dict[str, Any]:
        """设置默认配置值"""
        return {
            'DETIK_BASE_URL': 'https://news.detik.com',
            'OUTPUT_DIR': 'output',
            'LOG_LEVEL': 'INFO',
            'REQUEST_DELAY': 1,
            'MAX_RETRIES': 3,
            'REQUEST_TIMEOUT': 30,
            'OUTPUT_FORMAT': 'txt',
            'INCLUDE_TIMESTAMP': True,
            # WebDriver相关配置
            'WEBDRIVER_PAGE_LOAD_TIMEOUT': 120,
            'WEBDRIVER_IMPLICIT_WAIT': 15,
            'WEBDRIVER_EXPLICIT_WAIT': 45,
            'WEBDRIVER_MAX_RETRIES': 3,
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)
    
    def get_detik_base_url(self) -> str:
        """获取detik基础URL"""
        return self.get('DETIK_BASE_URL')
    
    def get_output_dir(self) -> str:
        """获取输出目录"""
        return self.get('OUTPUT_DIR')
    
    def get_request_delay(self) -> int:
        """获取请求延迟时间（秒）"""
        return self.get('REQUEST_DELAY')
    
    def get_max_retries(self) -> int:
        """获取最大重试次数"""
        return self.get('MAX_RETRIES')
    
    def get_request_timeout(self) -> int:
        """获取请求超时时间（秒）"""
        return self.get('REQUEST_TIMEOUT')
    
    def get_output_format(self) -> str:
        """获取输出格式"""
        return self.get('OUTPUT_FORMAT')
    
    def get_include_timestamp(self) -> bool:
        """是否包含时间戳"""
        return self.get('INCLUDE_TIMESTAMP')
    
    def get_log_level(self) -> str:
        """获取日志级别"""
        return self.get('LOG_LEVEL')
    
    def get_webdriver_page_load_timeout(self) -> int:
        """获取WebDriver页面加载超时时间（秒）"""
        return self.get('WEBDRIVER_PAGE_LOAD_TIMEOUT')
    
    def get_webdriver_implicit_wait(self) -> int:
        """获取WebDriver隐式等待时间（秒）"""
        return self.get('WEBDRIVER_IMPLICIT_WAIT')
    
    def get_webdriver_explicit_wait(self) -> int:
        """获取WebDriver显式等待时间（秒）"""
        return self.get('WEBDRIVER_EXPLICIT_WAIT')
    
    def get_webdriver_max_retries(self) -> int:
        """获取WebDriver最大重试次数"""
        return self.get('WEBDRIVER_MAX_RETRIES')
