#!/usr/bin/env python3
"""
日志模块
统一的日志体系，支持 DEBUG/INFO/WARNING/ERROR
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional
from .config import get_config


class ColoredFormatter(logging.Formatter):
    """彩色日志Formatter"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # 青色
        'INFO': '\033[32m',      # 绿色
        'WARNING': '\033[33m',   # 黄色
        'ERROR': '\033[31m',     # 红色
        'CRITICAL': '\033[35m',  # 紫色
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # 添加颜色
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
        return super().format(record)


class Logger:
    """日志管理器"""
    
    _loggers = {}
    
    def __init__(self, name: str = "crawler"):
        self.name = name
        self._logger = None
        self._setup()
    
    def _setup(self):
        """设置日志"""
        config = get_config()
        log_config = config.logging
        
        # 创建 logger
        logger = logging.getLogger(self.name)
        logger.setLevel(getattr(logging, log_config.level.upper()))
        logger.handlers.clear()
        
        # 避免重复添加 handler
        if logger.handlers:
            self._logger = logger
            return
        
        # 日志格式
        fmt = log_config.format
        datefmt = log_config.date_format
        
        # 控制台 Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_formatter = ColoredFormatter(fmt, datefmt=datefmt)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # 文件 Handler
        if log_config.file.get("enabled", True):
            log_file = log_config.file.get("path", "./logs/crawler.log")
            log_dir = os.path.dirname(log_file)
            
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=log_config.file.get("max_bytes", 10 * 1024 * 1024),
                backupCount=log_config.file.get("backup_count", 5),
                encoding="utf-8"
            )
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(fmt, datefmt=datefmt)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        
        self._logger = logger
    
    def debug(self, msg, *args, **kwargs):
        """DEBUG 级别"""
        self._logger.debug(msg, *args, **kwargs)
    
    def info(self, msg, *args, **kwargs):
        """INFO 级别"""
        self._logger.info(msg, *args, **kwargs)
    
    def warning(self, msg, *args, **kwargs):
        """WARNING 级别"""
        self._logger.warning(msg, *args, **kwargs)
    
    def error(self, msg, *args, **kwargs):
        """ERROR 级别"""
        self._logger.error(msg, *args, **kwargs)
    
    def critical(self, msg, *args, **kwargs):
        """CRITICAL 级别"""
        self._logger.critical(msg, *args, **kwargs)
    
    def exception(self, msg, *args, **kwargs):
        """异常信息"""
        self._logger.exception(msg, *args, **kwargs)


def get_logger(name: str = "crawler") -> Logger:
    """获取日志实例"""
    if name not in Logger._loggers:
        Logger._loggers[name] = Logger(name)
    return Logger._loggers[name]


# 导出常用函数
debug = lambda msg, *args, **kwargs: get_logger().debug(msg, *args, **kwargs)
info = lambda msg, *args, **kwargs: get_logger().info(msg, *args, **kwargs)
warning = lambda msg, *args, **kwargs: get_logger().warning(msg, *args, **kwargs)
error = lambda msg, *args, **kwargs: get_logger().error(msg, *args, **kwargs)
critical = lambda msg, *args, **kwargs: get_logger().critical(msg, *args, **kwargs)
