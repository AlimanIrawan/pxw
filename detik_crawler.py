#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detik网站爬虫模块
负责从detik.com爬取新闻数据
"""

import time
import os
import requests
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import pytz
import re
from logger import get_logger

class DetikCrawler:
    """Detik网站爬虫"""
    
    def __init__(self, config):
        """初始化爬虫
        
        Args:
            config: 配置管理器实例
        """
        self.config = config
        self.logger = get_logger()
        self.base_url = config.get_detik_base_url()
        self.request_delay = config.get_request_delay()
        self.max_retries = config.get_max_retries()
        self.request_timeout = config.get_request_timeout()
        
        # 设置请求会话
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def _is_cloud_environment(self) -> bool:
        """检测是否在云端环境中"""
        cloud_indicators = [
            'RENDER',           # Render
            'HEROKU',           # Heroku  
            'RAILWAY',          # Railway
            'VERCEL',           # Vercel
            'NETLIFY',          # Netlify
            'GOOGLE_CLOUD_PROJECT',  # Google Cloud
            'AWS_LAMBDA_FUNCTION_NAME',  # AWS Lambda
        ]
        return any(os.environ.get(key) for key in cloud_indicators)
    
    def _setup_driver(self) -> webdriver.Chrome:
        """设置Chrome WebDriver
        
        Returns:
            配置好的Chrome WebDriver实例
        """
        chrome_options = Options()
        
        # 检测环境类型
        is_cloud = self._is_cloud_environment()
        
        if is_cloud:
            # 云端环境配置（Linux）
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-software-rasterizer')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            chrome_options.add_argument('--disable-features=TranslateUI')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--virtual-time-budget=5000')
            chrome_options.add_argument('--run-all-compositor-stages-before-draw')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            self.logger.info("使用云端Linux环境配置")
        else:
            # 本地macOS环境配置
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            chrome_options.add_argument('--disable-ipc-flooding-protection')
            self.logger.info("使用本地macOS环境配置")
        
        # 通用配置
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--no-default-browser-check')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--disable-popup-blocking')
        chrome_options.add_argument('--disable-translate')
        chrome_options.add_argument('--disable-background-downloads')
        chrome_options.add_argument('--disable-client-side-phishing-detection')
        chrome_options.add_argument('--disable-component-extensions-with-background-pages')
        chrome_options.add_argument('--disable-background-networking')
        chrome_options.add_argument('--disable-sync')
        chrome_options.add_argument('--metrics-recording-only')
        chrome_options.add_argument('--disable-logging')
        chrome_options.add_argument('--silent')
        chrome_options.add_argument('--log-level=3')
        
        # 禁用自动化检测
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.logger.info(f"尝试初始化ChromeDriver (第{attempt + 1}/{max_retries}次)")
                
                # 清理旧的ChromeDriver缓存
                if attempt > 0:
                    self.logger.info("清理ChromeDriver缓存...")
                    import shutil
                    cache_dir = os.path.expanduser("~/.wdm")
                    if os.path.exists(cache_dir):
                        try:
                            shutil.rmtree(cache_dir)
                        except Exception as e:
                            self.logger.warning(f"清理缓存失败: {e}")
                
                # 杀死可能存在的Chrome进程
                try:
                    import subprocess
                    subprocess.run(['pkill', '-f', 'chromedriver'], capture_output=True, check=False)
                    subprocess.run(['pkill', '-f', 'Google Chrome'], capture_output=True, check=False)
                    time.sleep(2)  # 等待进程完全退出
                except Exception as e:
                    self.logger.debug(f"清理进程时出错: {e}")
                
                # 使用webdriver-manager自动管理ChromeDriver
                driver_path = ChromeDriverManager().install()
                
                # 修复webdriver-manager路径问题
                if 'THIRD_PARTY_NOTICES.chromedriver' in driver_path:
                    driver_dir = os.path.dirname(driver_path)
                    actual_driver_path = os.path.join(driver_dir, 'chromedriver')
                    if os.path.exists(actual_driver_path):
                        driver_path = actual_driver_path
                
                # 设置ChromeDriver权限
                self.logger.info(f"设置ChromeDriver权限: {driver_path}")
                os.chmod(driver_path, 0o755)
                
                # 移除macOS安全属性
                try:
                    import subprocess
                    subprocess.run(['xattr', '-d', 'com.apple.quarantine', driver_path], 
                                 capture_output=True, check=False)
                    subprocess.run(['xattr', '-d', 'com.apple.provenance', driver_path], 
                                 capture_output=True, check=False)
                    subprocess.run(['xattr', '-c', driver_path], 
                                 capture_output=True, check=False)
                except Exception as e:
                    self.logger.warning(f"移除安全属性失败: {e}")
                
                # 创建Service对象
                service = Service(driver_path)
                
                # 尝试不同的Chrome选项组合
                if attempt == 1:
                    # 第二次尝试：降级到旧的无头模式
                    chrome_options.arguments = [arg.replace('--headless=new', '--headless') for arg in chrome_options.arguments]
                    self.logger.info("第二次尝试：使用传统无头模式")
                elif attempt == 2:
                    # 第三次尝试：最小化选项
                    chrome_options = Options()
                    chrome_options.add_argument('--headless')
                    chrome_options.add_argument('--no-sandbox')
                    chrome_options.add_argument('--disable-dev-shm-usage')
                    chrome_options.add_argument('--disable-gpu')
                    chrome_options.add_argument('--disable-web-security')
                    chrome_options.add_argument('--disable-features=VizDisplayCompositor')
                    self.logger.info("第三次尝试：使用最小化Chrome选项")
                
                driver = webdriver.Chrome(service=service, options=chrome_options)
                
                # 从配置文件获取超时设置
                page_load_timeout = self.config.get_webdriver_page_load_timeout()
                implicit_wait = self.config.get_webdriver_implicit_wait()
                
                driver.set_page_load_timeout(page_load_timeout)
                driver.implicitly_wait(implicit_wait)
                
                self.logger.info(f"WebDriver配置: 页面加载超时={page_load_timeout}秒, 隐式等待={implicit_wait}秒")
                self.logger.info("ChromeDriver初始化成功")
                return driver
                
            except Exception as e:
                self.logger.error(f"Chrome WebDriver初始化失败 (第{attempt + 1}/{max_retries}次): {e}")
                
                # 清理可能残留的进程
                try:
                    import subprocess
                    subprocess.run(['pkill', '-f', 'chromedriver'], capture_output=True, check=False)
                    subprocess.run(['pkill', '-f', 'Google Chrome'], capture_output=True, check=False)
                except:
                    pass
                
                if attempt < max_retries - 1:
                    retry_delay = 5 + (attempt * 2)  # 递增延迟
                    self.logger.info(f"等待{retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                else:
                    self.logger.error("ChromeDriver初始化失败，已达到最大重试次数")
                    self.logger.error("可能的解决方案：")
                    self.logger.error("1. 检查Chrome浏览器是否已安装")
                    self.logger.error("2. 重启Terminal和程序")
                    self.logger.error("3. 在系统偏好设置->安全性与隐私中允许ChromeDriver运行")
                    raise
    
    def crawl_news(self, target_date: str) -> List[Dict]:
        """爬取指定日期的新闻数据
        
        Args:
            target_date: 目标日期，格式：YYYY-MM-DD
            
        Returns:
            新闻数据列表
        """
        self.logger.info(f"开始爬取 {target_date} 的新闻数据")
        
        # 首先尝试Chrome模式
        try:
            self.logger.info("尝试使用Chrome模式（完整功能）")
            return self._crawl_with_chrome(target_date)
        except Exception as e:
            self.logger.warning(f"Chrome模式失败: {e}")
            self.logger.info("切换到requests模式（保持日期筛选功能）")
            return self._crawl_with_requests(target_date)
    
    def _crawl_with_chrome(self, target_date: str) -> List[Dict]:
        """使用Chrome WebDriver爬取（原有逻辑）"""
        driver = None
        try:
            # 设置WebDriver
            driver = self._setup_driver()
            
            # 获取新闻列表页面的URL列表
            news_urls = self._get_news_urls(driver, target_date)
            
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
                    self.logger.debug(f"成功爬取新闻: {article_data['title'][:50]}...")
                else:
                    self.logger.warning(f"爬取新闻失败: {url}")
                
                # 请求延迟
                time.sleep(self.request_delay)
            
            self.logger.info(f"Chrome模式爬取完成，共获取 {len(news_data)} 篇新闻")
            return news_data
            
        except Exception as e:
            self.logger.error(f"Chrome模式爬取时出错: {e}", exc_info=True)
            raise  # 重新抛出异常，让主方法切换到requests模式
        finally:
            if driver:
                driver.quit()
    
    def _crawl_with_requests(self, target_date: str) -> List[Dict]:
        """使用requests爬取（保持日期筛选逻辑）"""
        try:
            # 获取新闻列表页面的URL列表
            news_urls = self._get_news_urls_with_requests(target_date)
            
            if not news_urls:
                self.logger.warning(f"未找到 {target_date} 的新闻链接")
                return []
            
            self.logger.info(f"找到 {len(news_urls)} 个新闻链接")
            
            # 爬取每篇新闻的详细内容
            news_data = []
            for i, url in enumerate(news_urls, 1):
                self.logger.info(f"正在爬取第 {i}/{len(news_urls)} 篇新闻: {url}")
                
                article_data = self._crawl_article_with_requests(url)
                if article_data:
                    news_data.append(article_data)
                    self.logger.debug(f"成功爬取新闻: {article_data['title'][:50]}...")
                else:
                    self.logger.warning(f"爬取新闻失败: {url}")
                
                # 请求延迟
                time.sleep(self.request_delay)
            
            self.logger.info(f"requests模式爬取完成，共获取 {len(news_data)} 篇新闻")
            return news_data
            
        except Exception as e:
            self.logger.error(f"requests模式爬取失败: {e}")
            return []
    
    def _get_news_urls(self, driver: webdriver.Chrome, target_date: str) -> List[str]:
        """获取指定日期的新闻URL列表
        
        Args:
            driver: WebDriver实例
            target_date: 目标日期，格式：YYYY-MM-DD
            
        Returns:
            新闻URL列表
        """
        try:
            # 将目标日期转换为datetime对象
            target_date_obj = datetime.strptime(target_date, '%Y-%m-%d')
            
            all_urls = []
            page = 1  # 从第1页开始
            consecutive_empty_pages = 0
            found_target_news = False  # 标记是否已经找到过目标日期的新闻
            
            self.logger.info(f"开始爬取 {target_date} 的新闻，使用通用索引页面策略，从第{page}页开始")
            
            while True:
                # 构建索引页面URL
                url = f"{self.base_url}/indeks?page={page}"
                
                self.logger.info(f"正在爬取第 {page} 页: {url}")
                
                # 重试机制加载页面
                page_loaded = False
                max_retries = self.config.get_webdriver_max_retries()
                explicit_wait = self.config.get_webdriver_explicit_wait()
                
                for attempt in range(max_retries):
                    try:
                        self.logger.debug(f"尝试加载页面 (第{attempt+1}/{max_retries}次): {url}")
                        driver.get(url)
                        
                        # 等待页面加载完成
                        WebDriverWait(driver, explicit_wait).until(
                            EC.presence_of_element_located((By.TAG_NAME, "body"))
                        )
                        
                        # 额外等待确保内容加载
                        time.sleep(2)
                        page_loaded = True
                        self.logger.debug(f"页面加载成功: {url}")
                        break
                        
                    except TimeoutException as e:
                        self.logger.warning(f"页面加载超时 (第{attempt+1}/{max_retries}次尝试): {url} - {e}")
                        if attempt < max_retries - 1:  # 不是最后一次尝试
                            retry_delay = min(5 * (attempt + 1), 15)  # 递增延迟，最多15秒
                            self.logger.info(f"等待{retry_delay}秒后重试...")
                            time.sleep(retry_delay)
                        continue
                    except Exception as e:
                        self.logger.error(f"页面加载出错 (第{attempt+1}/{max_retries}次尝试): {url} - {e}")
                        if attempt < max_retries - 1:
                            retry_delay = min(3 * (attempt + 1), 10)
                            time.sleep(retry_delay)
                        continue
                
                if not page_loaded:
                    self.logger.error(f"页面加载失败，跳过第 {page} 页: {url}")
                    page += 1
                    continue
                
                # 获取当前页面的新闻项目（包含链接和时间信息）
                page_urls = self._extract_news_urls_with_time_filter(driver, target_date_obj)
                
                if not page_urls:
                    consecutive_empty_pages += 1
                    self.logger.info(f"第 {page} 页没有找到目标日期的新闻")
                    
                    # 如果已经找到过目标日期的新闻，现在又没有了，说明已经过了目标日期，直接停止
                    if found_target_news:
                        self.logger.info(f"已找到目标日期新闻后出现空页，说明已过目标日期，停止爬取")
                        break
                    
                    # 如果从开始就连续20页都没有找到目标日期的新闻，停止爬取
                    if consecutive_empty_pages >= 20:
                        self.logger.info(f"连续{consecutive_empty_pages}页没有找到目标日期的新闻，停止爬取")
                        break
                else:
                    consecutive_empty_pages = 0
                    found_target_news = True  # 标记已经找到过目标日期的新闻
                    # 添加到总列表，去重
                    new_urls = [url for url in page_urls if url not in all_urls]
                    all_urls.extend(new_urls)
                    
                    self.logger.info(f"第 {page} 页找到 {len(new_urls)} 个目标日期的新闻链接")
                
                page += 1
                
                # 安全限制：最多爬取50页
                if page > 50:
                    self.logger.warning("已达到最大页数限制(50页)")
                    break
            
            self.logger.info(f"总共找到 {len(all_urls)} 个目标日期的新闻链接")
            return all_urls
            
        except Exception as e:
            self.logger.error(f"获取新闻URL列表时出错: {e}", exc_info=True)
            return []
    
    def _parse_time_info(self, time_text: str, title_text: str, target_date: datetime) -> bool:
        """解析时间信息，判断是否为目标日期的新闻
        
        Args:
            time_text: 显示的时间文本
            title_text: title属性中的完整时间信息
            target_date: 目标日期
            
        Returns:
            bool: 是否为目标日期的新闻
        """
        try:
            # 设置雅加达时区
            jakarta_tz = pytz.timezone('Asia/Jakarta')
            now_jakarta = datetime.now(jakarta_tz)
            
            # 印尼语月份映射（支持更多格式）
            month_map = {
                'Jan': 1, 'Januari': 1,
                'Feb': 2, 'Februari': 2,
                'Mar': 3, 'Maret': 3,
                'Apr': 4, 'April': 4,
                'Mei': 5, 'May': 5,
                'Jun': 6, 'Juni': 6,
                'Jul': 7, 'Juli': 7,
                'Agu': 8, 'Agustus': 8,
                'Sep': 9, 'September': 9,
                'Okt': 10, 'Oktober': 10,
                'Nov': 11, 'November': 11,
                'Des': 12, 'Desember': 12
            }
            
            # 印尼语星期映射
            day_map = {
                'Minggu': 'Sunday', 'Senin': 'Monday', 'Selasa': 'Tuesday',
                'Rabu': 'Wednesday', 'Kamis': 'Thursday', 'Jumat': 'Friday',
                'Sabtu': 'Saturday'
            }
            
            # 检查绝对时间格式 - 同时检查time_text和title_text
            text_to_check = time_text if time_text else title_text
            if text_to_check and ('WIB' in text_to_check or 'WITA' in text_to_check or 'WIT' in text_to_check):
                self.logger.info(f"🔍 解析绝对时间格式: {text_to_check}")
                
                # 格式1: Minggu, 03 Agu 2025 13:54 WIB
                pattern1 = r'\w+,\s*(\d{1,2})\s+(\w+)\s+(\d{4})\s+\d{1,2}:\d{2}\s+WI[BTA]'
                match1 = re.search(pattern1, text_to_check)
                if match1:
                    day, month_str, year = match1.groups()
                    if month_str in month_map:
                        try:
                            news_date = datetime(int(year), month_map[month_str], int(day))
                            is_match = news_date.date() == target_date.date()
                            if is_match:
                                self.logger.info(f"✅ 找到匹配日期(格式1): {text_to_check}")
                            else:
                                self.logger.info(f"❌ 日期不匹配(格式1): {news_date.date()} vs {target_date.date()}")
                            return is_match
                        except ValueError as e:
                            self.logger.info(f"⚠️ 解析日期失败: {e}")
                
                # 格式2: 03 Agustus 2025, 13:54 WIB
                pattern2 = r'(\d{1,2})\s+(\w+)\s+(\d{4}),\s*\d{1,2}:\d{2}\s+WI[BTA]'
                match2 = re.search(pattern2, text_to_check)
                if match2:
                    day, month_str, year = match2.groups()
                    if month_str in month_map:
                        try:
                            news_date = datetime(int(year), month_map[month_str], int(day))
                            is_match = news_date.date() == target_date.date()
                            if is_match:
                                self.logger.info(f"✅ 找到匹配日期(格式2): {text_to_check}")
                            else:
                                self.logger.info(f"❌ 日期不匹配(格式2): {news_date.date()} vs {target_date.date()}")
                            return is_match
                        except ValueError as e:
                            self.logger.info(f"⚠️ 解析日期失败: {e}")
                
                # 格式3: 2025-08-03 13:54:00
                pattern3 = r'(\d{4})-(\d{1,2})-(\d{1,2})\s+\d{1,2}:\d{2}:\d{2}'
                match3 = re.search(pattern3, text_to_check)
                if match3:
                    year, month, day = match3.groups()
                    try:
                        news_date = datetime(int(year), int(month), int(day))
                        is_match = news_date.date() == target_date.date()
                        if is_match:
                            self.logger.info(f"✅ 找到匹配日期(格式3): {text_to_check}")
                        else:
                            self.logger.info(f"❌ 日期不匹配(格式3): {news_date.date()} vs {target_date.date()}")
                        return is_match
                    except ValueError as e:
                        self.logger.info(f"⚠️ 解析日期失败: {e}")
                
                self.logger.info(f"⚠️ 未匹配任何绝对时间格式: {text_to_check}")
            
            # 处理相对时间格式（增强版）
            if 'yang lalu' in time_text or 'lalu' in time_text:
                self.logger.debug(f"处理相对时间: {time_text}")
                
                # 提取数字和时间单位
                time_patterns = [
                    (r'(\d+)\s*menit\s+yang\s+lalu', 'minutes'),
                    (r'(\d+)\s*jam\s+yang\s+lalu', 'hours'),
                    (r'(\d+)\s*hari\s+yang\s+lalu', 'days'),
                    (r'(\d+)\s*minggu\s+yang\s+lalu', 'weeks'),
                    (r'(\d+)\s*bulan\s+yang\s+lalu', 'months'),
                    (r'(\d+)\s*menit\s+lalu', 'minutes'),
                    (r'(\d+)\s*jam\s+lalu', 'hours'),
                    (r'(\d+)\s*hari\s+lalu', 'days')
                ]
                
                for pattern, unit in time_patterns:
                    match = re.search(pattern, time_text, re.IGNORECASE)
                    if match:
                        time_value = int(match.group(1))
                        
                        if unit == 'minutes':
                            news_time = now_jakarta - timedelta(minutes=time_value)
                        elif unit == 'hours':
                            news_time = now_jakarta - timedelta(hours=time_value)
                        elif unit == 'days':
                            news_time = now_jakarta - timedelta(days=time_value)
                        elif unit == 'weeks':
                            news_time = now_jakarta - timedelta(weeks=time_value)
                        elif unit == 'months':
                            # 近似计算月份（30天）
                            news_time = now_jakarta - timedelta(days=time_value * 30)
                        else:
                            continue
                        
                        self.logger.debug(f"计算时间: {time_value} {unit} 前 = {news_time}")
                        
                        # 检查日期是否匹配
                        is_match = news_time.date() == target_date.date()
                        self.logger.debug(f"日期匹配检查: {news_time.date()} vs {target_date.date()} = {is_match}")
                        if is_match:
                            self.logger.info(f"找到匹配日期(相对时间): {time_text} -> {news_time}")
                        return is_match
            
            # 处理"今天"、"昨天"等特殊词汇
            special_time_map = {
                'hari ini': 0,
                'today': 0,
                'kemarin': 1,
                'yesterday': 1,
                'kemarin dulu': 2,
                'lusa': -1  # 明天（通常不会出现在新闻中）
            }
            
            time_text_lower = time_text.lower()
            for special_word, days_offset in special_time_map.items():
                if special_word in time_text_lower:
                    news_date = now_jakarta.date() - timedelta(days=days_offset)
                    is_match = news_date == target_date.date()
                    if is_match:
                        self.logger.info(f"找到匹配日期(特殊词汇): {time_text} -> {news_date}")
                    return is_match
            
            # 尝试解析其他可能的日期格式
            date_patterns = [
                r'(\d{1,2})/(\d{1,2})/(\d{4})',  # DD/MM/YYYY
                r'(\d{1,2})-(\d{1,2})-(\d{4})',  # DD-MM-YYYY
                r'(\d{4})/(\d{1,2})/(\d{1,2})',  # YYYY/MM/DD
                r'(\d{4})-(\d{1,2})-(\d{1,2})'   # YYYY-MM-DD
            ]
            
            combined_text = f"{time_text} {title_text}"
            for pattern in date_patterns:
                match = re.search(pattern, combined_text)
                if match:
                    try:
                        if pattern.startswith(r'(\d{4})'):
                            # YYYY format
                            year, month, day = match.groups()
                            news_date = datetime(int(year), int(month), int(day))
                        else:
                            # DD format (assume DD/MM/YYYY)
                            day, month, year = match.groups()
                            news_date = datetime(int(year), int(month), int(day))
                        
                        is_match = news_date.date() == target_date.date()
                        if is_match:
                            self.logger.info(f"找到匹配日期(数字格式): {match.group(0)} -> {news_date}")
                        return is_match
                    except ValueError as e:
                        self.logger.debug(f"解析数字日期失败: {match.group(0)} - {e}")
                        continue
            
            # 如果所有解析都失败，记录调试信息
            self.logger.debug(f"无法解析时间信息: time_text='{time_text}', title_text='{title_text}'")
            return False
            
        except Exception as e:
            self.logger.error(f"解析时间信息时出错: {time_text}, {title_text} - {e}")
            return False

    def _extract_news_urls_with_time_filter(self, driver: webdriver.Chrome, target_date: datetime) -> List[str]:
        """从页面中提取新闻URL并按时间筛选
        
        Args:
            driver: WebDriver实例
            target_date: 目标日期
            
        Returns:
            符合目标日期的新闻URL列表
        """
        news_urls = []
        
        try:
            # 等待新闻列表加载（减少超时时间）
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "article, .media, .list-content__item, .media-artikel"))
                )
            except TimeoutException:
                self.logger.warning("等待新闻列表加载超时，尝试继续处理")
                # 不直接返回，尝试查找已加载的元素
                pass
            
            # 查找所有新闻项目容器
            news_items = driver.find_elements(By.CSS_SELECTOR, "article, .media, .list-content__item, .media-artikel")
            
            for item in news_items:
                try:
                    # 查找新闻链接
                    link_elem = item.find_element(By.CSS_SELECTOR, "a[href*='/berita/'], a[href*='/news/'], a[href*='detik.com']")
                    href = link_elem.get_attribute('href')
                    
                    if not href or 'detik.com' not in href:
                        continue
                    
                    # 查找时间信息
                    time_elem = None
                    time_selectors = [
                        '.media__date', '.date', '.time', 'time', 
                        '[class*="date"]', '[class*="time"]',
                        '.media__subtitle', '.subtitle'
                    ]
                    
                    for selector in time_selectors:
                        try:
                            time_elem = item.find_element(By.CSS_SELECTOR, selector)
                            if time_elem:
                                break
                        except:
                            continue
                    
                    if time_elem:
                         time_text = time_elem.text.strip()
                         # 尝试获取title属性（包含完整时间信息）
                         title_text = time_elem.get_attribute("title") or ""
                         
                         # 如果time_elem没有title属性，尝试查找子元素的title属性
                         if not title_text:
                             try:
                                 span_elem = time_elem.find_element(By.TAG_NAME, "span")
                                 title_text = span_elem.get_attribute("title") or ""
                             except:
                                 pass
                         
                         # 检查是否是目标日期的新闻
                         if self._parse_time_info(time_text, title_text, target_date):
                             full_url = urljoin(self.base_url, href)
                             if full_url not in news_urls:
                                 news_urls.append(full_url)
                                 self.logger.debug(f"找到目标日期新闻: {time_text} ({title_text}) - {href}")
                    else:
                        # 如果没有找到时间信息，也添加到列表中（后续通过文章页面验证）
                        full_url = urljoin(self.base_url, href)
                        if full_url not in news_urls:
                            news_urls.append(full_url)
                            self.logger.debug(f"无时间信息的新闻: {href}")
                            
                except Exception as e:
                    self.logger.debug(f"处理新闻项目时出错: {e}")
                    continue
            
            self.logger.info(f"提取到 {len(news_urls)} 个符合条件的新闻链接")
            return news_urls
            
        except Exception as e:
            self.logger.error(f"提取新闻URL时出错: {e}")
            return []
    
    def _validate_article_data(self, article_data: Dict) -> bool:
        """验证文章数据的完整性和质量
        
        Args:
            article_data: 文章数据字典
            
        Returns:
            bool: 数据是否有效
        """
        try:
            # 检查必需字段
            required_fields = ['title', 'publish_time', 'content', 'url']
            for field in required_fields:
                if field not in article_data or not article_data[field]:
                    self.logger.warning(f"文章数据缺少必需字段: {field}")
                    return False
            
            # 检查标题长度（至少5个字符，最多200个字符）
            title = article_data['title'].strip()
            if len(title) < 5 or len(title) > 200:
                self.logger.warning(f"标题长度异常: {len(title)} 字符 - {title[:50]}...")
                return False
            
            # 检查内容长度（至少50个字符，视频新闻例外）
            content = article_data['content'].strip()
            # 视频新闻特殊处理
            if '[VIDEO新闻]' in content:
                if len(content) < 20:  # 视频新闻最少20字符
                    self.logger.warning(f"视频新闻内容过短: {len(content)} 字符 - {content[:50]}...")
                    return False
            else:
                if len(content) < 50:  # 普通新闻至少50字符
                    self.logger.warning(f"内容过短: {len(content)} 字符 - {content[:50]}...")
                    return False
            
            # 检查URL格式
            url = article_data['url']
            if not url.startswith('https://') or 'detik.com' not in url:
                self.logger.warning(f"URL格式异常: {url}")
                return False
            
            # 检查是否包含常见的错误内容
            error_indicators = [
                '404', 'not found', 'error', 'halaman tidak ditemukan',
                'access denied', 'forbidden', 'server error'
            ]
            
            content_lower = content.lower()
            title_lower = title.lower()
            
            for indicator in error_indicators:
                if indicator in content_lower or indicator in title_lower:
                    self.logger.warning(f"检测到错误内容指示器: {indicator}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"验证文章数据时出错: {e}")
            return False
    
    def _crawl_article(self, url: str) -> Optional[Dict]:
        """爬取单篇新闻文章
        
        Args:
            url: 新闻文章URL
            
        Returns:
            新闻数据字典，包含title、publish_time、content
        """
        # 只处理 https://news.detik.com/berita 开头的链接
        if not url.startswith('https://news.detik.com/berita'):
            self.logger.info(f"跳过不符合条件的链接: {url}")
            return None
        
        # 检查是否为video新闻（20.detik.com开头）
        if url.startswith('https://20.detik.com'):
            self.logger.info(f"识别到video新闻: {url}")
            try:
                response = self.session.get(url, timeout=self.request_timeout)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 提取标题
                title = self._extract_title(soup)
                if not title:
                    title = "Video新闻（无法提取标题）"
                
                # 提取发布时间
                publish_time = self._extract_publish_time(soup)
                
                article_data = {
                    'title': title.strip(),
                    'publish_time': publish_time.strip() if publish_time else '',
                    'content': '[VIDEO新闻]',
                    'url': url
                }
                
                # 验证数据质量
                if self._validate_article_data(article_data):
                    return article_data
                else:
                    self.logger.warning(f"Video新闻数据验证失败: {url}")
                    return None
            except Exception as e:
                self.logger.warning(f"爬取video新闻失败: {url}, 错误: {e}")
                return {
                    'title': 'Video新闻（无法提取标题）',
                    'publish_time': '',
                    'content': '[VIDEO新闻]',
                    'url': url
                }
        
        # 处理普通新闻
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.request_timeout)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # 提取标题
                title = self._extract_title(soup)
                if not title:
                    self.logger.warning(f"无法提取标题: {url}")
                    continue
                
                # 提取发布时间
                publish_time = self._extract_publish_time(soup)
                
                # 提取正文内容
                content = self._extract_content(soup)
                if not content:
                    self.logger.warning(f"无法提取内容: {url}")
                    continue
                
                article_data = {
                    'title': title.strip(),
                    'publish_time': publish_time.strip() if publish_time else '',
                    'content': content.strip(),
                    'url': url
                }
                
                # 验证数据质量
                if self._validate_article_data(article_data):
                    return article_data
                else:
                    self.logger.warning(f"文章数据验证失败: {url}")
                    continue
                
            except Exception as e:
                self.logger.warning(f"爬取文章失败 (尝试 {attempt + 1}/{self.max_retries}): {url}, 错误: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
        
        return None
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """提取新闻标题
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            新闻标题
        """
        # 尝试多种标题选择器
        title_selectors = [
            'h1.detail__title',
            'h1[class*="title"]',
            '.detail__title',
            'h1',
            '.entry-title',
            '[class*="headline"]'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                return title_elem.get_text(strip=True)
        
        return None
    
    def _extract_publish_time(self, soup: BeautifulSoup) -> Optional[str]:
        """提取发布时间
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            发布时间
        """
        # 尝试多种时间选择器
        time_selectors = [
            '.detail__date',
            '[class*="date"]',
            '[class*="time"]',
            'time',
            '.published-date',
            '.entry-date'
        ]
        
        for selector in time_selectors:
            time_elem = soup.select_one(selector)
            if time_elem:
                # 尝试获取datetime属性
                datetime_attr = time_elem.get('datetime')
                if datetime_attr:
                    return datetime_attr
                return time_elem.get_text(strip=True)
        
        return None
    
    def _clean_text(self, text: str) -> str:
        """清理文本内容
        
        Args:
            text: 原始文本
            
        Returns:
            清理后的文本
        """
        if not text:
            return ""
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除HTML实体
        import html
        text = html.unescape(text)
        
        # 移除特殊字符和控制字符
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # 移除常见的广告和无关文本
        unwanted_patterns = [
            r'Baca juga:.*?(?=\n|$)',
            r'ADVERTISEMENT.*?(?=\n|$)',
            r'Simak Video.*?(?=\n|$)',
            r'\(\w+/\w+\)',  # 移除类似 (detik/detik) 的标记
            r'Halaman selanjutnya.*?(?=\n|$)',
            r'Lanjutkan membaca.*?(?=\n|$)'
        ]
        
        for pattern in unwanted_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # 清理多余的换行符
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()
    
    def _extract_content(self, soup: BeautifulSoup) -> Optional[str]:
        """提取新闻正文内容
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            新闻正文内容
        """
        # 尝试多种内容选择器（按优先级排序）
        content_selectors = [
            '.detail__body-text',
            '.itp_bodycontent',
            '.detail-content',
            '[class*="content"]',
            '[class*="body"]',
            '.entry-content',
            '.article-content',
            '.post-content',
            '.content',
            'article'
        ]
        
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # 移除不需要的元素
                unwanted_selectors = [
                    'script', 'style', 'noscript',
                    '.ads', '.advertisement', '.related', '.share',
                    '.social', '.comment', '.navigation',
                    '[class*="ad"]', '[id*="ad"]',
                    '.widget', '.sidebar'
                ]
                
                for unwanted_selector in unwanted_selectors:
                    for unwanted in content_elem.select(unwanted_selector):
                        unwanted.decompose()
                
                # 获取所有段落文本
                paragraphs = content_elem.find_all(['p', 'div', 'span'])
                if paragraphs:
                    content_parts = []
                    for p in paragraphs:
                        text = p.get_text(strip=True)
                        # 过滤太短的文本和无意义的文本
                        if text and len(text) > 15 and not text.isdigit():
                            # 检查是否包含实际内容（不只是标点符号）
                            if re.search(r'[a-zA-Z\u00C0-\u017F\u0100-\u024F]', text):
                                cleaned_text = self._clean_text(text)
                                if cleaned_text and len(cleaned_text) > 10:
                                    content_parts.append(cleaned_text)
                    
                    if content_parts:
                        full_content = '\n\n'.join(content_parts)
                        return self._clean_text(full_content)
                
                # 如果没有找到段落，直接获取文本
                raw_text = content_elem.get_text(strip=True)
                if raw_text:
                    return self._clean_text(raw_text)
        
        return None
    
    # ===== 使用requests的方法（Chrome失败时的备用方案）=====
    
    def _get_news_urls_with_requests(self, target_date: str) -> List[str]:
        """使用requests获取指定日期的新闻URL列表（保持原有的日期筛选逻辑）"""
        try:
            target_date_obj = datetime.strptime(target_date, '%Y-%m-%d')
            all_urls = []
            page = 1
            consecutive_empty_pages = 0
            found_target_news = False
            
            self.logger.info(f"开始使用requests爬取 {target_date} 的新闻，从第{page}页开始")
            
            while True:
                url = f"{self.base_url}/indeks?page={page}"
                self.logger.info(f"正在爬取第 {page} 页: {url}")
                
                try:
                    response = self.session.get(url, timeout=self.request_timeout)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    page_urls = self._extract_news_urls_with_requests(soup, target_date_obj)
                    
                    if not page_urls:
                        consecutive_empty_pages += 1
                        self.logger.info(f"第 {page} 页没有找到目标日期的新闻")
                        
                        # 如果已经找到过目标日期的新闻，现在又没有了，说明已经过了目标日期，直接停止
                        if found_target_news:
                            self.logger.info(f"已找到目标日期新闻后出现空页，说明已过目标日期，停止爬取")
                            break
                        
                        # 如果从开始就连续20页都没有找到目标日期的新闻，停止爬取
                        if consecutive_empty_pages >= 20:
                            self.logger.info(f"连续{consecutive_empty_pages}页没有找到目标日期的新闻，停止爬取")
                            break
                    else:
                        consecutive_empty_pages = 0
                        found_target_news = True
                        # 添加到总列表，去重
                        new_urls = [url for url in page_urls if url not in all_urls]
                        all_urls.extend(new_urls)
                        
                        self.logger.info(f"第 {page} 页找到 {len(new_urls)} 个目标日期的新闻链接")
                    
                    page += 1
                    
                    # 安全限制：最多爬取50页
                    if page > 50:
                        self.logger.info("已达到最大页面数限制（50页），停止爬取")
                        break
                    
                    time.sleep(1)  # 页面间延迟
                    
                except Exception as e:
                    self.logger.error(f"爬取第 {page} 页失败: {e}")
                    consecutive_empty_pages += 1
                    if consecutive_empty_pages >= 5:
                        break
                    continue
            
            self.logger.info(f"requests模式共找到 {len(all_urls)} 个新闻链接")
            return all_urls
            
        except Exception as e:
            self.logger.error(f"使用requests获取新闻URL列表时出错: {e}")
            return []
    
    def _extract_news_urls_with_requests(self, soup: BeautifulSoup, target_date: datetime) -> List[str]:
        """从BeautifulSoup对象中提取新闻URL并按时间筛选"""
        news_urls = []
        
        try:
            # 查找所有新闻项目容器
            news_items = soup.select("article, .media, .list-content__item, .media-artikel")
            
            for item in news_items:
                try:
                    # 查找新闻链接
                    link_element = item.select_one("a[href*='/berita/']")
                    if not link_element:
                        continue
                    
                    href = link_element.get('href')
                    if not href:
                        continue
                    
                    # 构建完整URL
                    if href.startswith('/'):
                        full_url = urljoin(self.base_url, href)
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        continue
                    
                    # 只处理 news.detik.com/berita 开头的链接
                    if not full_url.startswith('https://news.detik.com/berita'):
                        continue
                    
                    # 查找时间信息 - 扩展选择器
                    time_element = item.select_one(".media__date, .list-content__date, [class*='date'], [class*='time'], time, .date, .time, .timestamp")
                    title_element = item.select_one(".media__title, .list-content__title, h2, h3, h4, a")
                    
                    time_text = time_element.get_text(strip=True) if time_element else ""
                    title_text = title_element.get_text(strip=True) if title_element else ""
                    
                    # 如果没有找到时间元素，尝试从整个项目中查找时间信息
                    if not time_text:
                        # 查找包含时间格式的所有文本
                        all_text = item.get_text()
                        import re
                        # 查找WIB格式的时间
                        wib_match = re.search(r'[^.]*\d{1,2}\s+\w+\s+\d{4}\s+\d{1,2}:\d{2}\s+WIB[^.]*', all_text)
                        if wib_match:
                            time_text = wib_match.group(0).strip()
                    
                    # 调试日志 - 记录提取到的信息（改为INFO级别便于调试）
                    if time_text or title_text:
                        self.logger.info(f"🔍 检查新闻项目 - 时间: '{time_text}', 标题: '{title_text[:30]}...'")
                    
                    # 使用原有的时间解析逻辑
                    if self._parse_time_info(time_text, title_text, target_date):
                        news_urls.append(full_url)
                        self.logger.info(f"✅ 找到目标日期新闻: {title_text[:50]}...")
                    elif time_text:
                        self.logger.info(f"❌ 时间不匹配: '{time_text}' vs 目标日期: {target_date.strftime('%Y-%m-%d')}")
                    
                except Exception as e:
                    self.logger.debug(f"处理新闻项目时出错: {e}")
                    continue
            
            return news_urls
            
        except Exception as e:
            self.logger.error(f"从页面提取新闻URL时出错: {e}")
            return []
    
    def _crawl_article_with_requests(self, url: str) -> Optional[Dict]:
        """使用requests爬取单篇新闻文章"""
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
                title = self._extract_title_with_requests(soup)
                if not title:
                    continue
                
                # 提取发布时间
                publish_time = self._extract_publish_time_with_requests(soup)
                
                # 提取正文内容
                content = self._extract_content_with_requests(soup)
                if not content:
                    continue
                
                # 生成文章ID
                article_id = len(url.split('/'))  # 简单的ID生成
                
                return {
                    'id': article_id,
                    'title': title.strip(),
                    'publish_time': publish_time.strip() if publish_time else '',
                    'content': content.strip(),
                    'url': url,
                    'word_count': len(content.split())
                }
                
            except Exception as e:
                self.logger.warning(f"爬取文章失败 (尝试 {attempt + 1}/{self.max_retries}): {url}, 错误: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
        
        return None
    
    def _extract_title_with_requests(self, soup: BeautifulSoup) -> Optional[str]:
        """使用BeautifulSoup提取新闻标题"""
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
    
    def _extract_publish_time_with_requests(self, soup: BeautifulSoup) -> Optional[str]:
        """使用BeautifulSoup提取发布时间"""
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
    
    def _extract_content_with_requests(self, soup: BeautifulSoup) -> Optional[str]:
        """使用BeautifulSoup提取新闻正文内容"""
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
                    return self._clean_text_requests(text)
        
        return None
    
    def _clean_text_requests(self, text: str) -> str:
        """清理文本内容（requests版本）"""
        if not text:
            return ""
        
        # 移除多余的空白字符
        import re
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()
