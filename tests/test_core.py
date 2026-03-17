#!/usr/bin/env python3
"""
单元测试
覆盖核心页面操作与请求拦截逻辑
"""

import unittest
import os
import sys
import json
import tempfile
import time
from unittest.mock import Mock, patch, MagicMock

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from crawler.config import (
    Config, BrowserConfig, RequestConfig, AnticrawlerConfig,
    LoggingConfig, OutputConfig, QueueConfig, CheckpointConfig,
    ConfigManager, load_config
)
from crawler.logger import Logger, get_logger
from crawler.checkpoint import Checkpoint, RetryManager
from crawler.output import DataExporter, DataCollector
from crawler.anticrawler import UserAgentManager, ProxyManager, FingerprintManager


class TestConfig(unittest.TestCase):
    """配置模块测试"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = Config()
        self.assertIsInstance(config.browser, BrowserConfig)
        self.assertIsInstance(config.request, RequestConfig)
        self.assertEqual(config.browser.headless, False)
    
    def test_config_from_dict(self):
        """测试从字典加载配置"""
        data = {
            "browser": {"headless": True},
            "request": {"timeout": 60},
            "anticrawler": {"random_ua": False}
        }
        config = Config.from_dict(data)
        self.assertEqual(config.browser.headless, True)
        self.assertEqual(config.request.timeout, 60)
        self.assertEqual(config.anticrawler.random_ua, False)


class TestLogger(unittest.TestCase):
    """日志模块测试"""
    
    def test_logger_creation(self):
        """测试日志器创建"""
        logger = Logger("test")
        self.assertIsNotNone(logger._logger)
    
    def test_log_levels(self):
        """测试日志级别"""
        logger = Logger("test")
        # 应该不会抛出异常
        logger.debug("debug message")
        logger.info("info message")
        logger.warning("warning message")
        logger.error("error message")


class TestAnticrawler(unittest.TestCase):
    """反爬模块测试"""
    
    def test_user_agent_manager(self):
        """测试 UA 管理器"""
        ua_list = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        ]
        manager = UserAgentManager(ua_list)
        
        # 测试随机获取
        ua1 = manager.get_random()
        ua2 = manager.get_random()
        self.assertIn(ua1, ua_list)
        self.assertIn(ua2, ua_list)
    
    def test_proxy_manager(self):
        """测试代理管理器"""
        proxies = [
            "http://proxy1.com:8080",
            "socks5://proxy2.com:1080",
        ]
        manager = ProxyManager(proxies)
        
        # 测试获取
        proxy = manager.get_random()
        self.assertIn(proxy, proxies)
        
        # 测试轮换
        proxy1 = manager.get_next()
        proxy2 = manager.get_next()
        self.assertNotEqual(proxy1, proxy2)
    
    def test_fingerprint_manager(self):
        """测试指纹管理器"""
        fingerprint = {
            "timezone": "Asia/Shanghai",
            "locale": "zh-CN",
        }
        manager = FingerprintManager(fingerprint)
        
        options = manager.get_context_options()
        self.assertEqual(options.get("timezone_id"), "Asia/Shanghai")
        self.assertEqual(options.get("locale"), "zh-CN")


class TestCheckpoint(unittest.TestCase):
    """断点续爬测试"""
    
    def setUp(self):
        """创建临时文件"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.checkpoint = Checkpoint(self.temp_file.name)
    
    def tearDown(self):
        """清理临时文件"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_mark_and_check_visited(self):
        """测试标记和检查访问"""
        item = {"url": "https://example.com", "id": "123"}
        
        # 初始应该未访问
        self.assertFalse(self.checkpoint.is_visited(item))
        
        # 标记后应该已访问
        self.checkpoint.mark_visited(item)
        self.assertTrue(self.checkpoint.is_visited(item))
    
    def test_different_items(self):
        """测试不同项目"""
        item1 = {"url": "https://example.com/1", "id": "1"}
        item2 = {"url": "https://example.com/2", "id": "2"}
        
        self.checkpoint.mark_visited(item1)
        self.assertTrue(self.checkpoint.is_visited(item1))
        self.assertFalse(self.checkpoint.is_visited(item2))
    
    def test_save_and_clear(self):
        """测试保存和清空"""
        item = {"url": "https://example.com", "id": "123"}
        self.checkpoint.mark_visited(item)
        self.checkpoint.save()
        
        # 创建新实例应该能加载
        checkpoint2 = Checkpoint(self.temp_file.name)
        self.assertTrue(checkpoint2.is_visited(item))
        
        # 清空
        checkpoint2.clear()
        self.assertFalse(checkpoint2.is_visited(item))


class TestRetryManager(unittest.TestCase):
    """重试管理器测试"""
    
    def test_should_retry(self):
        """测试是否应该重试"""
        manager = RetryManager(max_retries=3)
        
        self.assertTrue(manager.should_retry("task1"))
        
        manager.record_attempt("task1")
        manager.record_attempt("task1")
        manager.record_attempt("task1")
        
        self.assertFalse(manager.should_retry("task1"))
    
    def test_exponential_backoff(self):
        """测试指数退避"""
        manager = RetryManager(max_retries=3, delay=1)
        
        manager.record_attempt("task1")
        delay1 = manager.get_delay("task1")
        
        manager.record_attempt("task1")
        delay2 = manager.get_delay("task1")
        
        self.assertEqual(delay1, 1)  # 2^0 = 1
        self.assertEqual(delay2, 2)  # 2^1 = 2
    
    def test_reset(self):
        """测试重置"""
        manager = RetryManager(max_retries=3)
        
        manager.record_attempt("task1")
        manager.record_attempt("task1")
        
        self.assertTrue(manager.should_retry("task1"))
        
        manager.reset("task1")
        
        # 重置后应该重新计算
        manager.record_attempt("task1")
        self.assertEqual(manager._attempts.get("task1"), 1)


class TestOutput(unittest.TestCase):
    """数据输出测试"""
    
    def setUp(self):
        """创建临时目录"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """清理临时目录"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_export_json(self):
        """测试 JSON 导出"""
        exporter = DataExporter(format="json", directory=self.temp_dir)
        
        data = [
            {"name": "Alice", "age": 25},
            {"name": "Bob", "age": 30},
        ]
        
        filepath = exporter.export(data, "test")
        
        self.assertTrue(os.path.exists(filepath))
        
        with open(filepath, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0]["name"], "Alice")
    
    def test_export_csv(self):
        """测试 CSV 导出"""
        exporter = DataExporter(format="csv", directory=self.temp_dir)
        
        data = [
            {"name": "Alice", "age": 25},
            {"name": "Bob", "age": 30},
        ]
        
        filepath = exporter.export(data, "test")
        
        self.assertTrue(os.path.exists(filepath))
        
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        self.assertIn("name", content)
        self.assertIn("Alice", content)
    
    def test_export_sqlite(self):
        """测试 SQLite 导出"""
        exporter = DataExporter(format="sqlite", directory=self.temp_dir)
        
        data = [
            {"name": "Alice", "age": 25},
            {"name": "Bob", "age": 30},
        ]
        
        filepath = exporter.export(data, "test", table="users")
        
        self.assertTrue(os.path.exists(filepath))
        
        # 验证数据
        import sqlite3
        conn = sqlite3.connect(filepath)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        conn.close()
        
        self.assertEqual(len(rows), 2)
    
    def test_data_collector(self):
        """测试数据收集器"""
        collector = DataCollector()
        
        collector.add({"name": "Alice", "age": 25})
        collector.add({"name": "Bob", "age": 30})
        
        self.assertEqual(len(collector), 2)
        
        # 测试过滤
        result = collector.filter(age=25)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Alice")


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_full_workflow(self):
        """测试完整工作流"""
        # 配置
        config = Config()
        self.assertIsNotNone(config)
        
        # 日志
        logger = get_logger("integration_test")
        logger.info("集成测试开始")
        
        # 反爬
        anticrawler = get_anticrawler()
        headers = anticrawler.get_headers()
        self.assertIn("User-Agent", headers)
        
        # 断点
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        temp_file.close()
        
        checkpoint = Checkpoint(temp_file.name)
        item = {"url": "https://test.com", "id": "1"}
        checkpoint.mark_visited(item)
        
        self.assertTrue(checkpoint.is_visited(item))
        
        os.unlink(temp_file.name)
        
        # 输出
        temp_dir = tempfile.mkdtemp()
        exporter = DataExporter(directory=temp_dir)
        data = [{"name": "test"}]
        exporter.export(data, "test")
        
        import shutil
        shutil.rmtree(temp_dir)
        
        logger.info("集成测试完成")


if __name__ == "__main__":
    unittest.main()
