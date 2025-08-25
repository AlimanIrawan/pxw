#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据处理模块
负责处理爬取的新闻数据并保存为结构化文件
"""

import os
import json
import csv
from datetime import datetime
from typing import List, Dict, Optional
from logger import get_logger

class DataProcessor:
    """数据处理器"""
    
    def __init__(self, config):
        """初始化数据处理器
        
        Args:
            config: 配置管理器实例
        """
        self.config = config
        self.logger = get_logger()
        self.output_dir = config.get_output_dir()
        self.output_format = config.get_output_format()
        self.include_timestamp = config.get_include_timestamp()
        
        # 确保输出目录存在
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            self.logger.info(f"创建输出目录: {self.output_dir}")
    
    def save_news_data(self, news_data: List[Dict], target_date: str) -> str:
        """保存新闻数据
        
        Args:
            news_data: 新闻数据列表
            target_date: 目标日期
            
        Returns:
            输出文件路径
        """
        if not news_data:
            self.logger.warning("没有新闻数据需要保存")
            return ""
        
        # 数据清洗和验证
        cleaned_data = self._clean_news_data(news_data)
        
        # 根据配置的格式保存数据
        if self.output_format.lower() == 'json':
            return self._save_as_json(cleaned_data, target_date)
        elif self.output_format.lower() == 'csv':
            return self._save_as_csv(cleaned_data, target_date)
        else:  # 默认为txt格式
            return self._save_as_txt(cleaned_data, target_date)
    
    def _clean_news_data(self, news_data: List[Dict]) -> List[Dict]:
        """清洗新闻数据
        
        Args:
            news_data: 原始新闻数据
            
        Returns:
            清洗后的新闻数据
        """
        cleaned_data = []
        
        for i, article in enumerate(news_data, 1):
            try:
                # 验证必要字段
                if not article.get('title') or not article.get('content'):
                    self.logger.warning(f"第 {i} 篇新闻缺少必要字段，跳过")
                    continue
                
                cleaned_article = {
                    'id': i,
                    'title': self._clean_text(article['title']),
                    'publish_time': self._format_publish_time(article.get('publish_time', '')),
                    'content': self._clean_text(article['content']),
                    'url': article.get('url', ''),
                    'word_count': len(article['content'].split()),
                    'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S') if self.include_timestamp else ''
                }
                
                cleaned_data.append(cleaned_article)
                
            except Exception as e:
                self.logger.error(f"清洗第 {i} 篇新闻时出错: {e}")
                continue
        
        self.logger.info(f"数据清洗完成，有效新闻: {len(cleaned_data)} 篇")
        return cleaned_data
    
    def _clean_text(self, text: str) -> str:
        """清洗文本内容
        
        Args:
            text: 原始文本
            
        Returns:
            清洗后的文本
        """
        if not text:
            return ""
        
        # 移除多余的空白字符
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _format_publish_time(self, publish_time: str) -> str:
        """格式化发布时间
        
        Args:
            publish_time: 原始发布时间
            
        Returns:
            格式化后的发布时间
        """
        if not publish_time:
            return ""
        
        # 这里可以添加时间格式标准化逻辑
        # 目前直接返回原始时间
        return publish_time.strip()
    
    def _save_as_txt(self, news_data: List[Dict], target_date: str) -> str:
        """保存为TXT格式
        
        Args:
            news_data: 新闻数据
            target_date: 目标日期
            
        Returns:
            输出文件路径
        """
        filename = f"detik_news_{target_date}.txt"
        filepath = os.path.join(self.output_dir, filename)
        
        # 简化版文件路径
        summary_filename = f"detik_news_{target_date}_summary.txt"
        summary_filepath = os.path.join(self.output_dir, summary_filename)
        
        try:
            # 保存完整版文件
            with open(filepath, 'w', encoding='utf-8') as f:
                # 写入文件头
                f.write(f"Detik新闻数据 - {target_date}\n")
                f.write(f"新闻总数: {len(news_data)} 篇\n")
                f.write("=" * 80 + "\n\n")
                
                # 写入每篇新闻
                for article in news_data:
                    f.write(f"【新闻 {article['id']}】\n")
                    f.write(f"标题: {article['title']}\n")
                    
                    if article['publish_time']:
                        f.write(f"发布时间: {article['publish_time']}\n")
                    
                    if article['url']:
                        f.write(f"链接: {article['url']}\n")
                    
                    f.write(f"字数: {article['word_count']} 词\n")
                    
                    f.write("\n内容:\n")
                    f.write(article['content'])
                    f.write("\n\n" + "-" * 80 + "\n\n")
                
                # 写入统计信息
                total_words = sum(article['word_count'] for article in news_data)
                f.write("\n=== 统计信息 ===\n")
                f.write(f"总新闻数: {len(news_data)} 篇\n")
                f.write(f"总字数: {total_words} 词\n")
                f.write(f"平均字数: {total_words // len(news_data) if news_data else 0} 词/篇\n")
            
            # 保存简化版文件（只包含标题、发布时间、链接）
            with open(summary_filepath, 'w', encoding='utf-8') as f:
                # 写入文件头
                f.write(f"Detik新闻数据摘要 - {target_date}\n")
                f.write(f"新闻总数: {len(news_data)} 篇\n")
                f.write("=" * 80 + "\n\n")
                
                # 写入每篇新闻的摘要信息
                for article in news_data:
                    f.write(f"【新闻 {article['id']}】\n")
                    f.write(f"标题: {article['title']}\n")
                    
                    if article['publish_time']:
                        f.write(f"发布时间: {article['publish_time']}\n")
                    
                    if article['url']:
                        f.write(f"链接: {article['url']}\n")
                    
                    f.write("\n" + "-" * 80 + "\n\n")
                
                # 写入统计信息
                f.write("=== 统计信息 ===\n")
                f.write(f"总新闻数: {len(news_data)} 篇\n")
            
            self.logger.info(f"新闻数据已保存为TXT格式: {filepath}")
            self.logger.info(f"新闻摘要已保存为TXT格式: {summary_filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"保存TXT文件时出错: {e}")
            raise
    
    def _save_as_json(self, news_data: List[Dict], target_date: str) -> str:
        """保存为JSON格式
        
        Args:
            news_data: 新闻数据
            target_date: 目标日期
            
        Returns:
            输出文件路径
        """
        filename = f"detik_news_{target_date}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            output_data = {
                'metadata': {
                    'target_date': target_date,
                    'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'total_count': len(news_data),
                    'source': 'detik.com'
                },
                'news': news_data
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"新闻数据已保存为JSON格式: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"保存JSON文件时出错: {e}")
            raise
    
    def _save_as_csv(self, news_data: List[Dict], target_date: str) -> str:
        """保存为CSV格式
        
        Args:
            news_data: 新闻数据
            target_date: 目标日期
            
        Returns:
            输出文件路径
        """
        filename = f"detik_news_{target_date}.csv"
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            fieldnames = ['id', 'title', 'publish_time', 'content', 'url', 'word_count', 'crawl_time']
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(news_data)
            
            self.logger.info(f"新闻数据已保存为CSV格式: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"保存CSV文件时出错: {e}")
            raise
    
    def get_statistics(self, news_data: List[Dict]) -> Dict:
        """获取新闻数据统计信息
        
        Args:
            news_data: 新闻数据
            
        Returns:
            统计信息字典
        """
        if not news_data:
            return {}
        
        total_words = sum(article.get('word_count', 0) for article in news_data)
        
        return {
            'total_count': len(news_data),
            'total_words': total_words,
            'average_words': total_words // len(news_data),
            'longest_article': max(news_data, key=lambda x: x.get('word_count', 0)),
            'shortest_article': min(news_data, key=lambda x: x.get('word_count', 0))
        }
