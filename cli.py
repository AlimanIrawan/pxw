#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detik新闻爬虫命令行版本
"""

import sys
import os
import argparse
from datetime import datetime, timedelta
from config import ConfigManager
from detik_crawler import DetikCrawler
from data_processor import DataProcessor
from logger import setup_logger

class DetikCrawlerCLI:
    """Detik新闻爬虫命令行版本"""
    
    def __init__(self):
        """初始化CLI"""
        self.config = ConfigManager()
        self.logger = setup_logger()
        self.crawler = None
        self.processor = None
    
    def parse_arguments(self):
        """解析命令行参数"""
        parser = argparse.ArgumentParser(description="Detik新闻爬虫")
        parser.add_argument('--date', '-d', type=str, 
                          help='目标日期 (YYYY-MM-DD格式，默认为昨天)')
        parser.add_argument('--format', '-f', type=str, choices=['txt', 'json', 'csv'],
                          default='txt', help='输出格式 (默认: txt)')
        parser.add_argument('--output-dir', '-o', type=str,
                          help='输出目录 (默认: output)')
        parser.add_argument('--list-formats', action='store_true',
                          help='显示支持的输出格式')
        
        return parser.parse_args()
    
    def get_target_date(self, date_arg):
        """获取目标日期"""
        if date_arg:
            try:
                datetime.strptime(date_arg, '%Y-%m-%d')
                return date_arg
            except ValueError:
                print(f"错误: 无效的日期格式 '{date_arg}'，请使用 YYYY-MM-DD 格式")
                sys.exit(1)
        else:
            # 默认为昨天
            yesterday = datetime.now() - timedelta(days=1)
            return yesterday.strftime('%Y-%m-%d')
    
    def show_quick_dates(self):
        """显示快速日期选项"""
        print("\n=== 快速日期选择 ===")
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        day_before = today - timedelta(days=2)
        
        print(f"1. 今天: {today.strftime('%Y-%m-%d')}")
        print(f"2. 昨天: {yesterday.strftime('%Y-%m-%d')}")
        print(f"3. 前天: {day_before.strftime('%Y-%m-%d')}")
        print("4. 自定义日期")
        
        choice = input("\n请选择 (1-4): ").strip()
        
        if choice == '1':
            return today.strftime('%Y-%m-%d')
        elif choice == '2':
            return yesterday.strftime('%Y-%m-%d')
        elif choice == '3':
            return day_before.strftime('%Y-%m-%d')
        elif choice == '4':
            custom_date = input("请输入日期 (YYYY-MM-DD): ").strip()
            try:
                datetime.strptime(custom_date, '%Y-%m-%d')
                return custom_date
            except ValueError:
                print("错误: 无效的日期格式")
                return self.show_quick_dates()
        else:
            print("无效选择，使用昨天")
            return yesterday.strftime('%Y-%m-%d')
    
    def crawl_news(self, target_date, output_format, output_dir):
        """爬取新闻"""
        try:
            print(f"\n=== 开始爬取 {target_date} 的新闻 ===")
            
            # 更新配置
            if output_dir:
                self.config.config['OUTPUT_DIR'] = output_dir
            self.config.config['OUTPUT_FORMAT'] = output_format
            
            # 初始化爬虫和处理器
            print("初始化爬虫...")
            self.crawler = DetikCrawler(self.config)
            self.processor = DataProcessor(self.config)
            
            # 开始爬取
            print("开始爬取新闻数据...")
            news_data = self.crawler.crawl_news(target_date)
            
            if not news_data:
                print("❌ 未获取到任何新闻数据")
                return False
            
            print(f"✅ 成功爬取 {len(news_data)} 条新闻")
            
            # 保存数据
            print("保存数据...")
            output_file = self.processor.save_news_data(news_data, target_date)
            
            print(f"✅ 数据保存完成: {output_file}")
            
            # 显示统计信息
            stats = self.processor.get_statistics(news_data)
            print(f"\n=== 统计信息 ===")
            print(f"总新闻数: {stats['total_count']} 篇")
            print(f"总字数: {stats['total_words']} 词")
            print(f"平均字数: {stats['average_words']} 词/篇")
            
            return True
            
        except KeyboardInterrupt:
            print("\n⚠️  用户中断操作")
            return False
        except Exception as e:
            print(f"❌ 爬取过程中出现错误: {str(e)}")
            self.logger.error(f"爬取失败: {e}", exc_info=True)
            return False
    
    def run(self):
        """运行CLI程序"""
        print("=== Detik新闻爬虫命令行版本 ===")
        
        args = self.parse_arguments()
        
        if args.list_formats:
            print("支持的输出格式:")
            print("- txt: 文本格式 (默认)")
            print("- json: JSON格式")
            print("- csv: CSV表格格式")
            return
        
        # 获取目标日期
        target_date = self.get_target_date(args.date)
        
        # 如果没有指定日期，显示快速选择
        if not args.date:
            target_date = self.show_quick_dates()
        
        print(f"\n目标日期: {target_date}")
        print(f"输出格式: {args.format}")
        print(f"输出目录: {args.output_dir or self.config.get_output_dir()}")
        
        # 确认开始
        confirm = input("\n是否开始爬取? (y/n): ").strip().lower()
        if confirm not in ['y', 'yes', '是']:
            print("操作已取消")
            return
        
        # 开始爬取
        success = self.crawl_news(target_date, args.format, args.output_dir)
        
        if success:
            print("\n🎉 爬取完成！")
            print("您可以在输出目录中查看生成的新闻文件。")
        else:
            print("\n❌ 爬取失败")
            sys.exit(1)

def main():
    """主函数"""
    cli = DetikCrawlerCLI()
    cli.run()

if __name__ == "__main__":
    main()
