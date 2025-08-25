#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化爬虫模块 - 不依赖Chrome/Selenium
作为云端环境的备用方案
"""

import time
import requests
from datetime import datetime, timedelta
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import pytz
import re
from logger import get_logger

class SimpleCrawler:
    """简化版爬虫 - 只使用requests和BeautifulSoup"""
    
    def __init__(self, config):
        self.config = config
        self.logger = get_logger()
        self.base_url = config.get_detik_base_url()
        self.request_delay = config.get_request_delay()
        self.max_retries = config.get_max_retries()
        self.request_timeout = config.get_request_timeout()
        
        # 设置请求会话
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def crawl_news(self, target_date: str) -> List[Dict]:
        """爬取指定日期的新闻数据"""
        self.logger.info(f"使用简化爬虫爬取 {target_date} 的新闻数据")
        
        try:
            # 获取新闻列表页面的URL列表
            news_urls = self._get_news_urls(target_date)
            
            if not news_urls:
                self.logger.warning(f"未找到 {target_date} 的新闻链接")
                return []
            
            self.logger.info(f"找到 {len(news_urls)} 个新闻链接")
            
            # 爬取每篇新闻的详细内容
            news_data = []
            for i, url in enumerate(news_urls, 1):
                self.logger.info(f"正在爬取第 {i}/{len(news_urls)} 篇新闻: {url}")
                
                article_data = self._crawl_article(url)
                if article_data:
                    news_data.append(article_data)
                else:
                    self.logger.warning(f"爬取新闻失败: {url}")
                
                # 请求延迟
                time.sleep(self.request_delay)
            
            self.logger.info(f"爬取完成，共获取 {len(news_data)} 篇新闻")
            return news_data
            
        except Exception as e:
            self.logger.error(f"爬取新闻时出错: {e}", exc_info=True)
            return []
    
    def _get_news_urls(self, target_date: str) -> List[str]:
        """获取指定日期的新闻URL列表"""
        try:
            target_date_obj = datetime.strptime(target_date, '%Y-%m-%d')
            all_urls = []
            
            # 简化版：只爬取前5页
            for page in range(1, 6):
                url = f"{self.base_url}/indeks?page={page}"
                self.logger.info(f"正在爬取第 {page} 页: {url}")
                
                try:
                    response = self.session.get(url, timeout=self.request_timeout)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    page_urls = self._extract_news_urls(soup, target_date_obj)
                    
                    if page_urls:
                        all_urls.extend(page_urls)
                        self.logger.info(f"第 {page} 页找到 {len(page_urls)} 个新闻链接")
                    else:
                        self.logger.info(f"第 {page} 页没有找到相关新闻")
                        
                except Exception as e:
                    self.logger.error(f"爬取第 {page} 页失败: {e}")
                    continue
                
                time.sleep(1)  # 页面间延迟
            
            self.logger.info(f"总共找到 {len(all_urls)} 个新闻链接")
            return list(set(all_urls))  # 去重
            
        except Exception as e:
            self.logger.error(f"获取新闻URL列表时出错: {e}")
            return []
    
    def _extract_news_urls(self, soup: BeautifulSoup, target_date: datetime) -> List[str]:
        """从页面中提取新闻URL"""
        urls = []
        
        try:
            # 查找新闻链接
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link.get('href')
                if href and '/berita/' in href and 'detik.com' in href:
                    # 只处理 news.detik.com/berita 开头的链接
                    if href.startswith('https://news.detik.com/berita'):
                        urls.append(href)
                    elif href.startswith('/berita/'):
                        full_url = urljoin(self.base_url, href)
                        urls.append(full_url)
            
            # 简化日期筛选：取前50个链接
            return urls[:50]
            
        except Exception as e:
            self.logger.error(f"提取新闻URL时出错: {e}")
            return []
    
    def _crawl_article(self, url: str) -> Optional[Dict]:
        """爬取单篇新闻文章"""
        # 只处理 https://news.detik.com/berita 开头的链接
        if not url.startswith('https://news.detik.com/berita'):
            self.logger.info(f"跳过不符合条件的链接: {url}")
            return None
            
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.request_timeout)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 提取标题
                title = self._extract_title(soup)
                if not title:
                    continue
                
                # 提取发布时间
                publish_time = self._extract_publish_time(soup)
                
                # 提取正文内容
                content = self._extract_content(soup)
                if not content:
                    continue
                
                return {
                    'title': title.strip(),
                    'publish_time': publish_time.strip() if publish_time else '',
                    'content': content.strip(),
                    'url': url
                }
                
            except Exception as e:
                self.logger.warning(f"爬取文章失败 (尝试 {attempt + 1}/{self.max_retries}): {url}, 错误: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
        
        return None
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """提取新闻标题"""
        selectors = [
            'h1.detail__title',
            'h1[class*="title"]',
            '.detail__title',
            'h1',
            '.entry-title'
        ]
        
        for selector in selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                return title_elem.get_text(strip=True)
        
        return None
    
    def _extract_publish_time(self, soup: BeautifulSoup) -> Optional[str]:
        """提取发布时间"""
        selectors = [
            '.detail__date',
            '[class*="date"]',
            '[class*="time"]',
            'time',
            '.published-date'
        ]
        
        for selector in selectors:
            time_elem = soup.select_one(selector)
            if time_elem:
                datetime_attr = time_elem.get('datetime')
                if datetime_attr:
                    return datetime_attr
                return time_elem.get_text(strip=True)
        
        return None
    
    def _extract_content(self, soup: BeautifulSoup) -> Optional[str]:
        """提取新闻正文内容"""
        selectors = [
            '.detail__body-text',
            '.itp_bodycontent',
            '.detail-content',
            '[class*="content"]',
            '.entry-content'
        ]
        
        for selector in selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # 移除不需要的元素
                for unwanted in content_elem.select('script, style, .ads, .advertisement'):
                    unwanted.decompose()
                
                # 获取文本内容
                text = content_elem.get_text(separator='\n', strip=True)
                if text and len(text) > 50:
                    return self._clean_text(text)
        
        return None
    
    def _clean_text(self, text: str) -> str:
        """清理文本内容"""
        if not text:
            return ""
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()
