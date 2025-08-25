#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detik新闻爬虫主程序
"""

import sys
import os
from gui import main as gui_main
from logger import setup_logger

def main():
    """主函数"""
    try:
        # 设置日志
        logger = setup_logger()
        logger.info("=== Detik新闻爬虫启动 ===")
        
        # 启动GUI界面
        gui_main()
        
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
