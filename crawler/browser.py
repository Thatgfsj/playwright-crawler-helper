#!/usr/bin/env python3
"""
Playwright 浏览器封装
提供常用操作：等待、点击、输入、滑动、截图、XHR拦截等
兼容同步/异步写法
"""

import time
import json
from typing import Optional, Dict, List, Any, Callable
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext, Playwright

from .config import get_config
from .logger import get_logger
from .anticrawler import get_anticrawler

logger = get_logger("browser")


class PlaywrightBrowser:
    """Playwright 浏览器封装"""
    
    def __init__(self, headless: bool = None):
        config = get_config()
        self.headless = headless if headless is not None else config.browser.headless
        self.slow_mo = config.browser.slow_mo
        
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # 请求拦截
        self.intercepted_requests: List[Dict] = []
        self.response_data: Dict[str, Any] = {}
    
    def start(self):
        """启动浏览器"""
        logger.info("启动浏览器...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo
        )
        
        # 获取反爬配置
        anticrawler = get_anticrawler()
        context_options = anticrawler.get_context_options()
        
        # 创建上下文
        self.context = self.browser.new_context(
            viewport=anticrawler.get_viewport(),
            **context_options
        )
        
        # 设置额外请求头
        self.context.set_extra_http_headers(anticrawler.get_headers())
        
        # 新建页面
        self.page = self.context.new_page()
        
        # 监听请求
        self._setup_listeners()
        
        logger.info("浏览器启动成功")
        return self
    
    def _setup_listeners(self):
        """设置监听器"""
        # 请求监听
        self.page.on("request", lambda request: self._on_request(request))
        # 响应监听
        self.page.on("response", lambda response: self._on_response(response))
    
    def _on_request(self, request):
        """请求回调"""
        self.intercepted_requests.append({
            "url": request.url,
            "method": request.method,
            "headers": dict(request.headers),
            "post_data": request.post_data,
            "resource_type": request.resource_type,
            "timestamp": time.time()
        })
    
    def _on_response(self, response):
        """响应回调"""
        try:
            self.response_data[response.url] = {
                "status": response.status,
                "headers": dict(response.headers),
                "body": response.text[:10000] if response.status < 400 else None
            }
        except Exception as e:
            logger.warning(f"获取响应内容失败: {e}")
    
    def goto(self, url: str, wait_until: str = "networkidle", timeout: int = None):
        """导航到URL"""
        config = get_config()
        timeout = timeout or config.request.timeout * 1000
        
        logger.info(f"访问: {url}")
        self.page.goto(url, wait_until=wait_until, timeout=timeout)
        return self
    
    def wait_for_selector(self, selector: str, timeout: int = None, state: str = "visible"):
        """等待元素"""
        config = get_config()
        timeout = timeout or config.request.timeout * 1000
        
        logger.debug(f"等待元素: {selector}")
        self.page.wait_for_selector(selector, timeout=timeout, state=state)
        return self
    
    def wait_for_load_state(self, state: str = "networkidle"):
        """等待加载状态"""
        self.page.wait_for_load_state(state)
        return self
    
    def click(self, selector: str, **kwargs):
        """点击元素"""
        logger.debug(f"点击: {selector}")
        self.page.click(selector, **kwargs)
        return self
    
    def type(self, selector: str, text: str, delay: int = 50):
        """输入文本"""
        logger.debug(f"输入: {selector} -> {text[:20]}...")
        self.page.type(selector, text, delay=delay)
        return self
    
    def fill(self, selector: str, value: str):
        """填充表单"""
        logger.debug(f"填充: {selector}")
        self.page.fill(selector, value)
        return self
    
    def select(self, selector: str, value: str):
        """选择选项"""
        logger.debug(f"选择: {selector} -> {value}")
        self.page.select_option(selector, value)
        return self
    
    def scroll_to(self, selector: str = None, y: int = None):
        """滚动页面"""
        if selector:
            logger.debug(f"滚动到元素: {selector}")
            self.page.locator(selector).scroll_into_view_if_needed()
        elif y is not None:
            logger.debug(f"滚动到 Y: {y}")
            self.page.evaluate(f"window.scrollTo(0, {y})")
        return self
    
    def scroll_down(self, times: int = 1, distance: int = 500):
        """向下滚动"""
        for i in range(times):
            self.page.evaluate(f"window.scrollBy(0, {distance})")
            time.sleep(0.5)
        return self
    
    def screenshot(self, path: str = None, full_page: bool = False):
        """截图"""
        if path:
            logger.debug(f"截图: {path}")
            self.page.screenshot(path=path, full_page=full_page)
        return self
    
    def get_text(self, selector: str) -> str:
        """获取元素文本"""
        return self.page.locator(selector).text_content()
    
    def get_attribute(self, selector: str, attr: str) -> str:
        """获取元素属性"""
        return self.page.locator(selector).get_attribute(attr)
    
    def get_all_text(self, selector: str) -> List[str]:
        """获取所有匹配元素的文本"""
        return self.page.locator(selector).all_text_contents()
    
    def evaluate(self, script: str):
        """执行 JavaScript"""
        return self.page.evaluate(script)
    
    # ========== 请求拦截相关 ==========
    
    def get_requests(self, url_pattern: str = None) -> List[Dict]:
        """获取拦截的请求"""
        if url_pattern:
            return [r for r in self.intercepted_requests if url_pattern in r["url"]]
        return self.intercepted_requests
    
    def get_xhr_requests(self) -> List[Dict]:
        """获取 XHR 请求"""
        return [r for r in self.intercepted_requests if r.get("resource_type") in ("xhr", "fetch")]
    
    def get_api_response(self, url: str = None) -> Optional[Dict]:
        """获取 API 响应"""
        if url:
            return self.response_data.get(url)
        # 返回最后一个请求的响应
        if self.response_data:
            return list(self.response_data.values())[-1]
        return None
    
    def clear_requests(self):
        """清空拦截数据"""
        self.intercepted_requests.clear()
        self.response_data.clear()
    
    # ========== 上下文管理 ==========
    
    def new_page(self):
        """新建页面"""
        self.page = self.context.new_page()
        self._setup_listeners()
        return self
    
    def close_page(self):
        """关闭当前页面"""
        if self.page:
            self.page.close()
    
    def stop(self):
        """关闭浏览器"""
        logger.info("关闭浏览器...")
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("浏览器已关闭")
    
    def __enter__(self):
        return self.start()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


# 便捷函数
def create_browser(headless: bool = None) -> PlaywrightBrowser:
    """创建浏览器实例"""
    return PlaywrightBrowser(headless=headless)
