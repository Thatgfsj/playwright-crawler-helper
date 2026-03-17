#!/usr/bin/env python3
"""
AI Crawler - 轻量级爬虫接口
专为 Claude Code / OpenClaw 沙箱环境设计
纯函数式、无状态、统一返回格式
"""

import json
import time
import uuid
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

# ========== 统一返回格式 ==========

@dataclass
class CrawlResult:
    """爬虫结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
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
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


# ========== 错误码定义 ==========

ERROR_CODES = {
    "SUCCESS": "成功",
    "TIMEOUT": "请求超时",
    "NETWORK_ERROR": "网络错误",
    "PARSE_ERROR": "解析错误",
    "BLOCKED": "被拦截",
    "INVALID_URL": "无效URL",
    "TOO_MANY_REQUESTS": "请求过多",
    "RESOURCE_TOO_LARGE": "资源过大",
    "UNKNOWN": "未知错误"
}


# ========== 轻量级爬虫函数 ==========

def crawl(
    url: str,
    method: str = "GET",
    headers: Dict = None,
    body: Any = None,
    timeout: int = 30,
    max_size: int = 1024 * 1024,  # 1MB 限制
    wait_for: str = None,
    extract_selector: str = None,
    extract_type: str = "text",  # text, html, json, links, images
) -> CrawlResult:
    """
    轻量级爬虫接口
    
    Args:
        url: 目标 URL
        method: 请求方法
        headers: 请求头
        body: 请求体
        timeout: 超时秒数
        max_size: 最大响应大小
        wait_for: 等待元素选择器
        extract_selector: 提取元素选择器
        extract_type: 提取类型 text/html/json/links/images
    
    Returns:
        CrawlResult: 统一格式结果
    """
    import requests
    
    # 参数校验
    if not url or not url.startswith(("http://", "https://")):
        return CrawlResult(
            success=False,
            error="无效URL，请提供以 http:// 或 https:// 开头的URL",
            error_code="INVALID_URL"
        )
    
    # 默认 headers
    if headers is None:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    try:
        # 发送请求
        start_time = time.time()
        
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=timeout)
        else:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=body if isinstance(body, dict) else None,
                data=body if not isinstance(body, dict) else None,
                timeout=timeout
            )
        
        elapsed = time.time() - start_time
        
        # 检查状态码
        if response.status_code >= 400:
            return CrawlResult(
                success=False,
                error=f"HTTP {response.status_code}: {response.reason}",
                error_code="BLOCKED" if response.status_code == 403 or response.status_code == 429 else "NETWORK_ERROR",
                meta={"status_code": response.status_code, "elapsed": elapsed}
            )
        
        # 检查大小
        content_length = len(response.content)
        if content_length > max_size:
            return CrawlResult(
                success=False,
                error=f"响应过大 ({content_length} bytes)，超过限制 {max_size}",
                error_code="RESOURCE_TOO_LARGE",
                meta={"size": content_length}
            )
        
        # 解析内容
        content_type = response.headers.get("Content-Type", "")
        data = None
        
        if "application/json" in content_type:
            # JSON
            try:
                data = response.json()
                extract_type = "json"
            except:
                data = response.text
        elif "text/html" in content_type:
            # HTML
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, "html.parser")
            
            if extract_selector:
                elements = soup.select(extract_selector)
                if extract_type == "text":
                    data = [el.get_text(strip=True) for el in elements]
                elif extract_type == "html":
                    data = [str(el) for el in elements]
                elif extract_type == "links":
                    data = [el.get("href") for el in elements if el.get("href")]
                elif extract_type == "images":
                    data = [el.get("src") for el in elements if el.get("src")]
                else:
                    data = [el.get_text(strip=True) for el in elements]
            else:
                data = response.text[:10000]  # 默认返回部分文本
        else:
            # 其他
            data = response.text[:10000]
        
        return CrawlResult(
            success=True,
            data=data,
            meta={
                "url": url,
                "status_code": response.status_code,
                "elapsed": elapsed,
                "size": content_length,
                "content_type": content_type,
                "extract_type": extract_type
            }
        )
        
    except requests.Timeout:
        return CrawlResult(
            success=False,
            error=f"请求超时 ({timeout}s)",
            error_code="TIMEOUT",
            meta={"timeout": timeout}
        )
    except requests.RequestException as e:
        return CrawlResult(
            success=False,
            error=str(e),
            error_code="NETWORK_ERROR"
        )
    except Exception as e:
        return CrawlResult(
            success=False,
            error=str(e),
            error_code="UNKNOWN"
        )


def crawl_list(
    urls: List[str],
    max_concurrent: int = 3,
    interval: float = 1.0,
    **kwargs
) -> List[CrawlResult]:
    """
    批量爬取
    
    Args:
        urls: URL 列表
        max_concurrent: 最大并发数
        interval: 请求间隔
        **kwargs: crawl() 其他参数
    
    Returns:
        List[CrawlResult]: 结果列表
    """
    import concurrent.futures
    
    results = []
    seen = set()
    
    for url in urls:
        # 防重复
        if url in seen:
            continue
        seen.add(url)
        
        result = crawl(url, **kwargs)
        results.append(result)
        
        # 间隔
        if interval > 0:
            time.sleep(interval)
    
    return results


# ========== 便捷单函数入口 ==========

def fetch(url: str, selector: str = None, wait: int = 5) -> Dict:
    """
    单函数入口 - 最简调用
    
    Usage:
        result = fetch("https://example.com")
        result = fetch("https://example.com", selector="title")
        result = fetch("https://example.com", selector=".content a", wait=10)
    
    Returns:
        Dict: {"success": bool, "data": Any, "error": str, "error_code": str}
    """
    import requests
    from bs4 import BeautifulSoup
    
    try:
        response = requests.get(url, timeout=wait)
        
        if response.status_code != 200:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}",
                "error_code": "BLOCKED"
            }
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        if selector:
            elements = soup.select(selector)
            data = [el.get_text(strip=True) for el in elements]
        else:
            data = soup.get_text(strip=True)[:5000]  # 默认返回前5000字符
        
        return {
            "success": True,
            "data": data,
            "error_code": "SUCCESS"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_code": "UNKNOWN"
        }


def get_json(url: str, timeout: int = 10) -> Dict:
    """
    快速获取 JSON API
    
    Usage:
        data = get_json("https://api.github.com/users/octocat")
    """
    return crawl(url, timeout=timeout).to_dict()


def get_links(url: str, selector: str = "a", timeout: int = 10) -> List[str]:
    """
    获取页面所有链接
    
    Usage:
        links = get_links("https://example.com")
    """
    result = crawl(url, extract_selector=selector, extract_type="links", timeout=timeout)
    if result.success:
        return result.data or []
    return []


def get_images(url: str, selector: str = "img", timeout: int = 10) -> List[str]:
    """
    获取页面所有图片链接
    """
    result = crawl(url, extract_selector=selector, extract_type="images", timeout=timeout)
    if result.success:
        return result.data or []
    return []


# ========== AI 极简调用示例 ==========

"""
# 方式1: 最简调用
result = fetch("https://example.com")
print(result["data"])

# 方式2: 获取 JSON API
result = get_json("https://api.github.com/users/octocat")
print(result["data"]["login"])

# 方式3: 获取页面链接
links = get_links("https://example.com")
print(links[:5])

# 方式4: 完整控制
result = crawl(
    url="https://example.com",
    extract_selector=".article",
    extract_type="text",
    timeout=20
)
print(result.to_dict())
"""
