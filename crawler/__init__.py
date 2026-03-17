#!/usr/bin/env python3
"""
Playwright Crawler - 爬虫框架
统一入口，封装常用操作
"""

from .config import load_config, get_config, Config
from .logger import get_logger
from .anticrawler import get_anticrawler, AnticrawlerManager
from .browser import PlaywrightBrowser, create_browser
from .queue import TaskQueue, Task, get_queue
from .checkpoint import Checkpoint, RetryManager, get_checkpoint, get_retry_manager
from .output import DataExporter, DataCollector, create_exporter, collect_and_export

__version__ = "1.0.0"

__all__ = [
    # 配置
    "load_config",
    "get_config",
    "Config",
    # 日志
    "get_logger",
    # 反爬
    "get_anticrawler",
    "AnticrawlerManager",
    # 浏览器
    "PlaywrightBrowser",
    "create_browser",
    # 任务队列
    "TaskQueue",
    "Task",
    "get_queue",
    # 断点续爬
    "Checkpoint",
    "RetryManager",
    "get_checkpoint",
    "get_retry_manager",
    # 数据输出
    "DataExporter",
    "DataCollector",
    "create_exporter",
    "collect_and_export",
]
