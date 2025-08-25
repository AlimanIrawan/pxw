#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detik新闻爬虫GUI界面
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import os
import time
import logging
import subprocess
from datetime import datetime, timedelta
from config import ConfigManager
from detik_crawler import DetikCrawler
from data_processor import DataProcessor
from logger import setup_logger

class GUILogHandler(logging.Handler):
    """GUI日志处理器，将日志信息发送到GUI界面"""
    
    def __init__(self, gui_instance):
        super().__init__()
        self.gui = gui_instance
        self.setLevel(logging.INFO)
        
        # 创建格式化器
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.setFormatter(formatter)
    
    def emit(self, record):
        """发送日志记录到GUI"""
        try:
            msg = self.format(record)
            # 在主线程中更新GUI
            self.gui.root.after(0, self.gui.log_message, msg)
        except Exception:
            pass

class DetikCrawlerGUI:
    """Detik新闻爬虫GUI界面"""
    
    def __init__(self):
        """初始化GUI界面"""
        self.root = tk.Tk()
        self.root.title("Detik新闻爬虫")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # 初始化配置和组件
        self.config = ConfigManager()
        self.logger = setup_logger()
        self.crawler = None
        self.processor = None
        
        # 添加超时和检查相关变量
        self.crawling_start_time = None
        self.last_log_time = None
        self.check_timer = None
        self.is_crawling = False
        
        # 创建界面
        self.create_widgets()
        
        # 设置GUI日志处理器
        self.setup_gui_logging()
        
        # 设置默认日期（昨天）
        yesterday = datetime.now() - timedelta(days=1)
        self.date_var.set(yesterday.strftime('%Y-%m-%d'))
    
    def setup_gui_logging(self):
        """设置GUI日志处理"""
        # 添加GUI日志处理器到detik_crawler日志器
        gui_handler = GUILogHandler(self)
        detik_logger = logging.getLogger('detik_crawler')
        detik_logger.addHandler(gui_handler)
        self.gui_handler = gui_handler
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="Detik新闻爬虫", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 日期选择区域
        date_frame = ttk.LabelFrame(main_frame, text="日期选择", padding="10")
        date_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        date_frame.columnconfigure(1, weight=1)
        
        ttk.Label(date_frame, text="目标日期:").grid(row=0, column=0, padx=(0, 10))
        
        self.date_var = tk.StringVar()
        self.date_entry = ttk.Entry(date_frame, textvariable=self.date_var, width=15)
        self.date_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # 快速日期按钮
        button_frame = ttk.Frame(date_frame)
        button_frame.grid(row=0, column=2)
        
        ttk.Button(button_frame, text="昨天", command=self.set_yesterday).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="前天", command=self.set_day_before_yesterday).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="今天", command=self.set_today).pack(side=tk.LEFT)
        
        # 输出格式选择
        format_frame = ttk.LabelFrame(main_frame, text="输出设置", padding="10")
        format_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(format_frame, text="输出格式:").grid(row=0, column=0, padx=(0, 10))
        
        self.format_var = tk.StringVar(value="txt")
        format_combo = ttk.Combobox(format_frame, textvariable=self.format_var, 
                                   values=["txt", "json", "csv"], state="readonly", width=10)
        format_combo.grid(row=0, column=1, padx=(0, 20))
        
        ttk.Button(format_frame, text="选择输出目录", command=self.select_output_dir).grid(row=0, column=2, padx=(0, 10))
        
        self.output_dir_var = tk.StringVar(value=self.config.get_output_dir())
        ttk.Label(format_frame, textvariable=self.output_dir_var, foreground="blue").grid(row=0, column=3)
        
        # 控制按钮
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=3, column=0, columnspan=3, pady=(0, 10))
        
        self.start_button = ttk.Button(control_frame, text="开始爬取", command=self.start_crawling)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(control_frame, text="停止", command=self.stop_crawling, state="disabled")
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.open_output_button = ttk.Button(control_frame, text="打开输出目录", command=self.open_output_dir)
        self.open_output_button.pack(side=tk.LEFT)
        
        # 进度条
        self.progress_var = tk.StringVar(value="就绪")
        ttk.Label(main_frame, textvariable=self.progress_var).grid(row=4, column=0, columnspan=3, pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress_bar.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 日志显示区域
        log_frame = ttk.LabelFrame(main_frame, text="运行日志", padding="10")
        log_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def set_yesterday(self):
        """设置为昨天"""
        yesterday = datetime.now() - timedelta(days=1)
        self.date_var.set(yesterday.strftime('%Y-%m-%d'))
    
    def set_day_before_yesterday(self):
        """设置为前天"""
        day_before = datetime.now() - timedelta(days=2)
        self.date_var.set(day_before.strftime('%Y-%m-%d'))
    
    def set_today(self):
        """设置为今天"""
        today = datetime.now()
        self.date_var.set(today.strftime('%Y-%m-%d'))
    
    def select_output_dir(self):
        """选择输出目录"""
        directory = filedialog.askdirectory(initialdir=self.config.get_output_dir())
        if directory:
            self.output_dir_var.set(directory)
            # 更新配置
            self.config.config['OUTPUT_DIR'] = directory
    
    def log_message(self, message):
        """在日志区域显示消息"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
        # 更新最后日志时间
        self.last_log_time = time.time()
    
    def start_crawling(self):
        """开始爬取"""
        # 验证日期格式
        try:
            target_date = self.date_var.get()
            datetime.strptime(target_date, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("错误", "请输入正确的日期格式 (YYYY-MM-DD)")
            return
        
        # 更新界面状态
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.progress_bar.start()
        self.progress_var.set("正在爬取...")
        self.status_var.set("运行中")
        
        # 设置爬取状态
        self.is_crawling = True
        self.crawling_start_time = time.time()
        self.last_log_time = time.time()
        
        # 清空日志
        self.log_text.delete(1.0, tk.END)
        
        # 开始自动检查
        self.start_auto_check()
        
        # 在新线程中运行爬取任务
        self.crawling_thread = threading.Thread(target=self.crawl_task, args=(target_date,))
        self.crawling_thread.daemon = True
        self.crawling_thread.start()
    
    def stop_crawling(self):
        """停止爬取"""
        self.progress_var.set("正在停止...")
        self.status_var.set("停止中")
        self.is_crawling = False
        
        # 停止自动检查
        if self.check_timer:
            self.root.after_cancel(self.check_timer)
            self.check_timer = None
        
        # 这里可以添加停止逻辑
        self.finish_crawling("用户停止")
    
    def start_auto_check(self):
        """开始自动检查"""
        if not self.is_crawling:
            return
        
        # 检查是否超时
        current_time = time.time()
        if self.crawling_start_time and (current_time - self.crawling_start_time) > 300:  # 5分钟超时
            self.log_message("⚠️ 检测到爬取超时，正在尝试诊断问题...")
            self.diagnose_problems()
            return
        
        # 检查日志是否停滞
        if self.last_log_time and (current_time - self.last_log_time) > 60:  # 1分钟无日志
            self.log_message("⚠️ 检测到日志停滞，正在检查网络连接...")
            self.check_network_connection()
            return
        
        # 继续检查
        self.check_timer = self.root.after(10000, self.start_auto_check)  # 每10秒检查一次
    
    def diagnose_problems(self):
        """诊断问题"""
        self.log_message("🔍 开始自动诊断...")
        
        # 检查网络连接
        if not self.check_network_connection():
            return
        
        # 检查ChromeDriver
        if not self.check_chromedriver():
            return
        
        # 检查网站可访问性
        if not self.check_website_access():
            return
        
        self.log_message("❌ 无法自动诊断问题，建议手动停止并重试")
    
    def check_network_connection(self):
        """检查网络连接"""
        try:
            self.log_message("🌐 检查网络连接...")
            result = subprocess.run(['ping', '-c', '3', '8.8.8.8'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.log_message("✅ 网络连接正常")
                return True
            else:
                self.log_message("❌ 网络连接异常")
                return False
        except Exception as e:
            self.log_message(f"❌ 网络检查失败: {e}")
            return False
    
    def check_chromedriver(self):
        """检查ChromeDriver"""
        try:
            self.log_message("🔧 检查ChromeDriver...")
            chromedriver_files = subprocess.run(['find', '/Users/LW/.wdm', '-name', 'chromedriver', '-type', 'f'], 
                                              capture_output=True, text=True)
            if chromedriver_files.returncode == 0 and chromedriver_files.stdout.strip():
                # 检查权限和安全属性
                for file in chromedriver_files.stdout.strip().split('\n'):
                    if file:
                        # 检查权限
                        result = subprocess.run(['ls', '-la', file], capture_output=True, text=True)
                        if result.returncode == 0:
                            permissions = result.stdout.split()[0]
                            if 'x' not in permissions:
                                self.log_message("🔧 修复ChromeDriver权限...")
                                subprocess.run(['chmod', '+x', file])
                        
                        # 检查并移除安全属性
                        try:
                            xattr_result = subprocess.run(['xattr', '-l', file], capture_output=True, text=True)
                            if xattr_result.returncode == 0 and xattr_result.stdout.strip():
                                self.log_message("🔧 移除ChromeDriver安全属性...")
                                subprocess.run(['xattr', '-d', 'com.apple.quarantine', file], 
                                            capture_output=True, check=False)
                                subprocess.run(['xattr', '-d', 'com.apple.provenance', file], 
                                            capture_output=True, check=False)
                        except Exception:
                            pass
                
                # 清理缓存并重新下载
                self.log_message("🔄 清理ChromeDriver缓存...")
                cache_dir = os.path.expanduser("~/.wdm")
                if os.path.exists(cache_dir):
                    import shutil
                    shutil.rmtree(cache_dir)
                
                self.log_message("✅ ChromeDriver检查完成，将重新下载")
                return True
            else:
                self.log_message("❌ 未找到ChromeDriver")
                return False
        except Exception as e:
            self.log_message(f"❌ ChromeDriver检查失败: {e}")
            return False
    
    def check_website_access(self):
        """检查网站可访问性"""
        try:
            self.log_message("🌍 检查网站可访问性...")
            import requests
            response = requests.get('https://news.detik.com', timeout=10)
            if response.status_code == 200:
                self.log_message("✅ 网站可正常访问")
                return True
            else:
                self.log_message(f"❌ 网站访问异常，状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_message(f"❌ 网站访问失败: {e}")
            return False
    
    def crawl_task(self, target_date):
        """爬取任务"""
        try:
            self.log_message("开始初始化爬虫...")
            
            # 初始化爬虫和处理器
            self.crawler = DetikCrawler(self.config)
            self.processor = DataProcessor(self.config)
            
            self.log_message(f"开始爬取 {target_date} 的新闻数据...")
            
            # 爬取新闻
            news_data = self.crawler.crawl_news(target_date)
            
            if not news_data:
                self.log_message("未获取到任何新闻数据")
                self.finish_crawling("未获取到数据")
                return
            
            self.log_message(f"成功爬取 {len(news_data)} 条新闻")
            
            # 保存数据
            self.log_message("开始保存数据...")
            output_file = self.processor.save_news_data(news_data, target_date)
            
            self.log_message(f"数据保存完成: {output_file}")
            
            # 显示统计信息
            stats = self.processor.get_statistics(news_data)
            self.log_message(f"统计信息: 总新闻数 {stats['total_count']} 篇, 总字数 {stats['total_words']} 词")
            
            self.finish_crawling("爬取完成", success=True)
            
        except Exception as e:
            self.log_message(f"爬取过程中出现错误: {str(e)}")
            self.finish_crawling(f"错误: {str(e)}")
    
    def finish_crawling(self, message, success=False):
        """完成爬取"""
        # 停止自动检查
        self.is_crawling = False
        if self.check_timer:
            self.root.after_cancel(self.check_timer)
            self.check_timer = None
        
        # 在主线程中更新界面
        self.root.after(0, self._update_ui_after_crawling, message, success)
    
    def _update_ui_after_crawling(self, message, success):
        """在主线程中更新界面"""
        self.progress_bar.stop()
        self.progress_var.set(message)
        self.status_var.set("完成" if success else "错误")
        
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        
        if success:
            messagebox.showinfo("完成", f"爬取完成！\n{message}")
        else:
            messagebox.showerror("错误", f"爬取失败！\n{message}")
    
    def open_output_dir(self):
        """打开输出目录"""
        output_dir = self.output_dir_var.get()
        if os.path.exists(output_dir):
            os.system(f"open '{output_dir}'")  # macOS
        else:
            messagebox.showwarning("警告", "输出目录不存在")
    
    def run(self):
        """运行GUI"""
        self.root.mainloop()

def main():
    """主函数"""
    app = DetikCrawlerGUI()
    app.run()

if __name__ == "__main__":
    main()
