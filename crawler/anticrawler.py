#!/usr/bin/env python3
"""
反爬伪装模块
提供代理池、随机UA、指纹伪装等功能
"""

import random
from typing import Dict, List, Optional
from .config import get_config
from .logger import get_logger

logger = get_logger("anticrawler")


class UserAgentManager:
    """User-Agent 管理器"""
    
    def __init__(self, ua_list: List[str] = None):
        config = get_config()
        self.ua_list = ua_list or config.anticrawler.ua_list or [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        ]
    
    def get_random(self) -> str:
        """获取随机 User-Agent"""
        ua = random.choice(self.ua_list)
        logger.debug(f"使用 UA: {ua[:50]}...")
        return ua
    
    def get(self) -> str:
        """获取 User-Agent（根据配置随机或固定）"""
        config = get_config()
        if config.anticrawler.random_ua:
            return self.get_random()
        return self.ua_list[0] if self.ua_list else ""


class ProxyManager:
    """代理管理器"""
    
    def __init__(self, proxies: List[str] = None):
        config = get_config()
        self.proxies = proxies or config.anticrawler.proxies or []
        self.current_index = 0
    
    def get_random(self) -> Optional[str]:
        """随机获取代理"""
        if not self.proxies:
            return None
        proxy = random.choice(self.proxies)
        logger.debug(f"使用代理: {proxy}")
        return proxy
    
    def get_next(self) -> Optional[str]:
        """轮换获取代理"""
        if not self.proxies:
            return None
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        logger.debug(f"使用代理: {proxy}")
        return proxy
    
    def get(self) -> Optional[str]:
        """获取代理"""
        return self.get_random()


class FingerprintManager:
    """指纹管理器"""
    
    def __init__(self, fingerprint: Dict = None):
        config = get_config()
        self.fingerprint = fingerprint or config.anticrawler.fingerprint or {}
    
    def get_context_options(self) -> Dict:
        """获取浏览器上下文选项"""
        options = {}
        
        # 时区
        if "timezone" in self.fingerprint:
            options["timezone_id"] = self.fingerprint["timezone"]
        
        # 语言
        if "locale" in self.fingerprint:
            options["locale"] = self.fingerprint["locale"]
        
        # 权限
        if "permissions" in self.fingerprint:
            options["permissions"] = self.fingerprint["permissions"]
        
        # 地理位置
        if "geolocation" in self.fingerprint:
            geo = self.fingerprint["geolocation"]
            options["geolocation"] = {
                "latitude": geo.get("latitude", 0),
                "longitude": geo.get("longitude", 0),
            }
        
        logger.debug(f"指纹配置: {options}")
        return options
    
    def get_viewport(self) -> Dict:
        """获取视口配置"""
        config = get_config()
        return config.browser.viewport


class AnticrawlerManager:
    """反爬综合管理器"""
    
    def __init__(self):
        self.ua_manager = UserAgentManager()
        self.proxy_manager = ProxyManager()
        self.fingerprint_manager = FingerprintManager()
    
    def get_headers(self) -> Dict:
        """获取请求头"""
        return {
            "User-Agent": self.ua_manager.get()
        }
    
    def get_context_options(self) -> Dict:
        """获取浏览器上下文选项"""
        return self.fingerprint_manager.get_context_options()
    
    def get_viewport(self) -> Dict:
        """获取视口"""
        return self.fingerprint_manager.get_viewport()
    
    def get_proxy(self) -> Optional[str]:
        """获取代理"""
        return self.proxy_manager.get()


# 全局实例
_anticrawler: Optional[AnticrawlerManager] = None


def get_anticrawler() -> AnticrawlerManager:
    """获取反爬管理器"""
    global _anticrawler
    if _anticrawler is None:
        _anticrawler = AnticrawlerManager()
    return _anticrawler
