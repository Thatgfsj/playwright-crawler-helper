#!/usr/bin/env python3
"""
AI Crawler - 轻量级爬虫框架
参考 Crawlee 核心设计，适配 AI 沙箱环境
纯函数式、无状态、统一返回格式
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

# ========== 统一返回格式 ==========

@dataclass
class CrawlResult:
    """爬虫结果"""
    success: bool
    data: Any = None
    error: str = ""
    error_code: str = "SUCCESS"
    meta: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "error_code": self.error_code,
            "meta": self.meta
        }


ERROR_CODES = {
    "SUCCESS": "成功",
    "TIMEOUT": "请求超时",
    "NETWORK_ERROR": "网络错误",
    "BLOCKED": "被拦截",
    "INVALID_URL": "无效URL",
    "TOO_MANY": "请求过多",
    "LARGE": "资源过大",
    "PARSE_ERROR": "解析错误",
}


# ========== 核心组件 ==========

class CrawlingContext:
    """爬虫上下文 - 类似 Crawlee 的 context"""
    
    def __init__(self, url: str, response, soup=None, page=None):
        self.url = url
        self.response = response
        self.soup = soup  # BeautifulSoup
        self.page = page  # Playwright page
        self._data: List[Dict] = []
        self._links: List[str] = []
    
    @property
    def html(self) -> str:
        return self.response.text[:100000] if self.response else ""
    
    @property
    def title(self) -> str:
        return self.soup.title.string if self.soup and self.soup.title else ""
    
    def get_text(self, selector: str) -> List[str]:
        """CSS 选择器提取文本"""
        if not self.soup:
            return []
        return [el.get_text(strip=True) for el in self.soup.select(selector)]
    
    def get_attr(self, selector: str, attr: str) -> List[str]:
        """CSS 选择器提取属性"""
        if not self.soup:
            return []
        return [el.get(attr, "") for el in self.soup.select(selector)]
    
    def get_links(self, selector: str = "a") -> List[str]:
        """提取链接"""
        if not self.soup:
            return []
        base = urlparse(self.url).scheme + "://" + urlparse(self.url).netloc
        links = []
        for el in self.soup.select(selector):
            href = el.get("href", "")
            if href:
                if href.startswith("http"):
                    links.append(href)
                elif href.startswith("/"):
                    links.append(base + href)
        return links
    
    def push_data(self, item: Dict):
        """收集数据"""
        self._data.append(item)
    
    def enqueue_links(self, selector: str = "a"):
        """收集链接"""
        self._links = self.get_links(selector)
    
    @property
    def collected_data(self) -> List[Dict]:
        return self._data
    
    @property
    def collected_links(self) -> List[str]:
        return self._links


# ========== 爬虫基类 ==========

class BaseCrawler:
    """爬虫基类 - 参考 Crawlee 设计"""
    
    def __init__(
        self,
        max_requests: int = 10,
        timeout: int = 30,
        max_size: int = 1024 * 1024,
    ):
        self.max_requests = max_requests
        self.timeout = timeout
        self.max_size = max_size
        
        self._visited: set = set()
        self._collected: List[Dict] = []
        self._handler: Optional[Callable] = None
    
    def router(self, handler: Callable):
        """装饰器注册 handler"""
        self._handler = handler
        return handler
    
    async def run(self, urls: List[str]) -> List[Dict]:
        """运行爬虫"""
        self._visited.clear()
        self._collected.clear()
        
        for url in urls:
            if len(self._collected) >= self.max_requests:
                break
            await self._crawl(url)
        
        return self._collected
    
    async def _crawl(self, url: str):
        """爬取单个 URL"""
        if url in self._visited:
            return
        self._visited.add(url)
        
        try:
            context = await self._fetch(url)
            if context and self._handler:
                await self._handler(context)
                self._collected.extend(context.collected_data)
        except Exception as e:
            print(f"Crawl error: {e}")
    
    async def _fetch(self, url: str) -> Optional[CrawlingContext]:
        """子类实现"""
        raise NotImplementedError


class BeautifulSoupCrawler(BaseCrawler):
    """HTTP + BeautifulSoup 爬虫 - 类似 Crawlee"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.session = None
    
    async def _fetch(self, url: str) -> Optional[CrawlingContext]:
        import requests
        from bs4 import BeautifulSoup
        
        try:
            resp = requests.get(url, timeout=self.timeout)
            if resp.status_code != 200:
                return None
            
            if len(resp.content) > self.max_size:
                return None
            
            soup = BeautifulSoup(resp.text, "html.parser")
            return CrawlingContext(url, resp, soup)
            
        except Exception as e:
            print(f"Fetch error: {e}")
            return None


class PlaywrightCrawler(BaseCrawler):
    """Playwright 爬虫 - 类似 Crawlee"""
    
    def __init__(self, headless: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.headless = headless
        self.playwright = None
        self.browser = None
    
    async def _fetch(self, url: str) -> Optional[CrawlingContext]:
        from playwright.async_api import async_playwright
        
        try:
            if not self.playwright:
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(headless=self.headless)
            
            page = await self.browser.new_page()
            resp = await page.goto(url, wait_until="domcontentloaded", timeout=self.timeout * 1000)
            
            content = await page.content()
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, "html.parser")
            
            return CrawlingContext(url, type('Response', (), {'text': content, 'status_code': resp.status if resp else 200})(), soup, page)
            
        except Exception as e:
            print(f"Playwright error: {e}")
            return None
    
    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()


# ========== 主入口函数 ==========

def crawl(
    urls: List[str],
    selector: str = None,
    max_requests: int = 10,
    headless: bool = True,
) -> Dict:
    """
    主入口函数 - 参考 Crawlee 风格
    
    Args:
        urls: URL 列表
        selector: CSS 选择器
        max_requests: 最大请求数
        headless: 是否无头(Playwright用)
    
    Returns:
        {"success": bool, "data": List[Dict], "count": int, "error_code": str}
    
    Usage:
        result = crawl(["https://example.com"])
        result = crawl(["https://example.com"], ".article")
        result = crawl(["https://example.com", "https://example.org"], "h2")
    """
    import requests
    from bs4 import BeautifulSoup
    
    results = []
    visited = set()
    
    for url in urls:
        if len(results) >= max_requests:
            break
        if url in visited:
            continue
        visited.add(url)
        
        try:
            resp = requests.get(url, timeout=30)
            if resp.status_code != 200:
                continue
            
            soup = BeautifulSoup(resp.text, "html.parser")
            
            if selector:
                items = soup.select(selector)
                for el in items:
                    results.append({
                        "url": url,
                        "text": el.get_text(strip=True)[:1000],
                        "html": str(el)[:500]
                    })
            else:
                results.append({
                    "url": url,
                    "title": soup.title.string if soup.title else "",
                    "text": soup.get_text()[:5000]
                })
        except Exception as e:
            continue
    
    return {
        "success": True,
        "data": results,
        "count": len(results),
        "error_code": "SUCCESS"
    }


# ========== 便捷函数 ==========

def fetch(url: str, selector: str = None) -> Dict:
    """
    最简调用 - 1行搞定
    
    Usage:
        result = fetch("https://example.com")
        result = fetch("https://example.com", ".title")
    """
    return crawl([url], selector, max_requests=1)


async def crawl_soup(url: str, selector: str = None) -> Dict:
    """异步爬取"""
    crawler = BeautifulSoupCrawler(max_requests=1)
    
    @crawler.router
    async def handler(ctx: CrawlingContext):
        if selector:
            ctx.push_data({"text": ctx.get_text(selector)})
        else:
            ctx.push_data({"title": ctx.title, "html": ctx.html[:5000]})
    
    results = await crawler.run([url])
    return results[0] if results else {"error": "no data"}


def get_json(url: str) -> Dict:
    """获取 JSON"""
    return crawl([url])


def get_links(url: str, selector: str = "a") -> List[str]:
    """获取链接"""
    result = crawl([url])
    if result.get("success") and result.get("data"):
        return result["data"][0].get("links", [])
    return []


# ========== 导出 ==========

__all__ = [
    "CrawlResult",
    "CrawlingContext",
    "BeautifulSoupCrawler", 
    "PlaywrightCrawler",
    "crawl",
    "fetch",
    "get_json",
    "get_links",
]


# ========== 用法示例 ==========
"""
# 方式1: 简单调用
result = crawl(["https://example.com"])
print(result["data"])

# 方式2: 带选择器
result = crawl(["https://example.com"], ".article h2")

# 方式3: Crawlee 风格 (异步)
import asyncio
from ai_crawler import BeautifulSoupCrawler

crawler = BeautifulSoupCrawler(max_requests=5)

@crawler.router
async def handler(ctx):
    ctx.push_data({
        "url": ctx.url,
        "title": ctx.title,
        "headings": ctx.get_text("h2")
    })
    ctx.enqueue_links("a")

results = asyncio.run(crawler.run(["https://example.com"]))
"""
