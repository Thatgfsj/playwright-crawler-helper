#!/usr/bin/env python3
"""
AI Crawler - 浏览器爬虫接口
基于 Playwright 真实浏览器引擎，支持 JS 渲染、网络拦截、反爬对抗。
专为 AI 代理设计：单文件、零配置、即导即用。
"""

import json
import time
import base64
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Iterator, Optional, Union
from urllib.parse import urlparse

# ========== 错误码 ==========

E = {
    "OK":              "成功",
    "TIMEOUT":         "请求超时",
    "NETWORK":         "网络错误",
    "BLOCKED":         "被拦截 / 反爬",
    "BAD_URL":         "无效 URL",
    "TOO_BIG":         "内容过大",
    "PARSE":           "解析失败",
    "HEADLESS":        "无头模式限制（部分站点强制要求有头浏览器）",
    "BROWSER_CRASH":   "浏览器进程异常退出",
}

def ok(data, meta=None):
    return {"ok": True, "data": data, "error": "", "code": "OK", "meta": meta or {}}

def err(msg, code="UNKNOWN", meta=None):
    return {"ok": False, "data": None, "error": msg, "code": code, "meta": meta or {}}


# ========== 浏览器管理器（单例，复用进程） ==========

class _BrowserManager:
    """Playwright 浏览器单例管理器。

    首次调用时启动浏览器进程，后续调用复用同一进程。
    每个爬取任务创建独立的浏览器上下文（相当于无痕窗口），互不干扰。
    """
    _instance = None
    _playwright = None
    _browser = None
    _launch_args = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _default_launch_args(self) -> dict:
        return {
            "headless": True,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
            ],
        }

    def start(self, headless: bool = None, **kwargs):
        """启动浏览器（如已启动则忽略）。"""
        from playwright.sync_api import sync_playwright

        if self._browser is not None and self._browser.is_connected():
            return

        args = self._default_launch_args()
        if headless is not None:
            args["headless"] = headless
        args.update(kwargs)
        self._launch_args = args

        try:
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(
                headless=args["headless"],
                args=args["args"],
            )
        except Exception:
            self._playwright = None
            self._browser = None
            raise

    def new_context(self, **kwargs) -> "BrowserContext":
        """创建新的浏览器上下文（隔离的会话环境）。"""
        if self._browser is None:
            self.start()
        defaults = {
            "viewport": {"width": 1920, "height": 1080},
            "locale": "zh-CN",
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        }
        defaults.update(kwargs)
        return self._browser.new_context(**defaults)

    def close(self):
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None

    @property
    def is_running(self) -> bool:
        return self._browser is not None and self._browser.is_connected()


_browser_mgr = _BrowserManager()


# ========== 反爬注入脚本 ==========

_STEALTH_JS = """
// 隐藏 webdriver 痕迹，对抗最常见的自动化检测
Object.defineProperty(navigator, 'webdriver', { get: () => false });
Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en'] });
window.chrome = { runtime: {} };
"""


def _inject_stealth(page):
    """在页面加载前注入反检测脚本。"""
    page.add_init_script(_STEALTH_JS)


def _capture_network(page, patterns: List[str] = None) -> List[dict]:
    """在页面导航期间捕获匹配的网络请求。"""
    captured = []
    def _on_response(response):
        url = response.url
        if patterns:
            if not any(p in url for p in patterns):
                return
        try:
            captured.append({
                "url": url,
                "status": response.status,
                "method": response.request.method,
                "headers": dict(response.headers)[:500],
                "body_preview": response.text()[:2000] if response.ok else "",
            })
        except Exception:
            pass
    page.on("response", _on_response)
    return captured


# ========== 核心 API ==========

def fetch(
    url: str,
    sel: str = None,
    *,
    headless: bool = True,
    wait_until: str = "domcontentloaded",
    timeout: int = 30000,
    screenshot: bool = False,
    stealth: bool = True,
    capture_network: Union[bool, List[str]] = False,
    scroll: bool = False,
) -> Dict:
    """使用真实浏览器获取页面内容，支持 JS 渲染。

    Args:
        url:       目标 URL（必须以 http:// 或 https:// 开头）
        sel:       CSS 选择器，指定后只提取匹配元素
        headless:  是否无头模式（默认 True）
        wait_until: 页面加载等待策略: domcontentloaded / load / networkidle
        timeout:   超时毫秒数
        screenshot: 是否附带页面截图（Base64）
        stealth:   是否启用反检测脚本
        capture_network: True 捕获全部 XHR/Fetch，或传入关键词列表过滤
        scroll:    是否自动滚动到底部（触发懒加载）

    Returns:
        {"ok": True, "data": ..., "code": "OK", "meta": {...}, "error": ""}
    """
    if not url.startswith(("http://", "https://")):
        return err("URL 需以 http:// 或 https:// 开头", "BAD_URL")

    from playwright.sync_api import TimeoutError as PTimeout

    try:
        _browser_mgr.start(headless=headless)
        ctx = _browser_mgr.new_context()
        page = ctx.new_page()

        if stealth:
            _inject_stealth(page)

        # 网络拦截
        network_log = []
        if capture_network:
            patterns = None if capture_network is True else (
                capture_network if isinstance(capture_network, list) else None
            )
            network_log = _capture_network(page, patterns)

        page.goto(url, wait_until=wait_until, timeout=timeout)

        if scroll:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(500)

        # 截图
        screenshot_b64 = None
        if screenshot:
            screenshot_b64 = base64.b64encode(
                page.screenshot(full_page=True, type="png")
            ).decode()

        # 提取内容
        if sel:
            elements = page.query_selector_all(sel)
            data = []
            for el in elements[:50]:
                try:
                    data.append({
                        "text": el.inner_text()[:1000],
                        "html": el.inner_html()[:500],
                    })
                except Exception:
                    continue
        else:
            data = {
                "title": page.title(),
                "url": page.url,
                "text": page.inner_text("body")[:5000],
                "html": page.content()[:10000],
            }

        meta = {
            "url": page.url,
            "status": 200,
            "network_captured": len(network_log),
        }
        if screenshot_b64:
            meta["screenshot_base64"] = screenshot_b64[:200] + "..."  # 预览截断
            data["_screenshot"] = screenshot_b64
        if network_log:
            data["_network"] = network_log

        ctx.close()
        return ok(data, meta)

    except PTimeout:
        return err(f"页面加载超时 ({timeout}ms)", "TIMEOUT")
    except Exception as e:
        msg = str(e)[:200]
        if "net::ERR" in msg or "NS_ERROR" in msg:
            return err(msg, "NETWORK")
        return err(msg, "BROWSER_CRASH")


def crawl(
    urls: List[str],
    sel: str = None,
    *,
    limit: int = 10,
    headless: bool = True,
    timeout: int = 30000,
    stealth: bool = True,
) -> Dict:
    """批量爬取多个 URL，自动去重，复用浏览器进程。

    Args:
        urls:     URL 列表
        sel:      CSS 选择器
        limit:    最多爬取条数
        headless: 无头模式
        timeout:  每个页面的超时毫秒数
        stealth:  反检测开关

    Returns:
        {"ok": True, "data": [...], "meta": {"count": N, "total_visited": N}}
    """
    visited = set()
    results = []
    errors = []

    for url in urls:
        if len(results) >= limit:
            break
        if url in visited:
            continue
        visited.add(url)

        r = fetch(url, sel=sel, headless=headless, timeout=timeout, stealth=stealth)
        if r["ok"]:
            item = r["data"]
            if isinstance(item, dict):
                item["_source_url"] = url
            results.append(item)
        else:
            errors.append({"url": url, "error": r["error"]})

    return ok(results, {
        "count": len(results),
        "total_visited": len(visited),
        "errors": errors,
    })


def links(
    url: str,
    sel: str = "a",
    *,
    headless: bool = True,
    timeout: int = 30000,
    stealth: bool = True,
    same_domain: bool = False,
) -> Dict:
    """提取页面中的链接（JS 渲染后的最终 DOM）。

    Args:
        url:         目标 URL
        sel:         选择链接的 CSS 选择器（默认所有 <a>）
        headless:    无头模式
        timeout:     超时毫秒数
        stealth:     反检测开关
        same_domain: 仅返回同域名链接

    Returns:
        {"ok": True, "data": ["https://...", ...]}
    """
    if not url.startswith(("http://", "https://")):
        return err("URL 需以 http:// 或 https:// 开头", "BAD_URL")

    base_domain = urlparse(url).netloc

    try:
        _browser_mgr.start(headless=headless)
        ctx = _browser_mgr.new_context()
        page = ctx.new_page()
        if stealth:
            _inject_stealth(page)

        page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        elements = page.query_selector_all(sel)

        out = []
        for el in elements:
            href = el.get_attribute("href")
            if not href:
                continue
            if href.startswith("javascript:") or href.startswith("#"):
                continue

            full_url = href
            if href.startswith("/"):
                full_url = f"{urlparse(url).scheme}://{base_domain}{href}"
            elif not href.startswith("http"):
                full_url = f"{urlparse(url).scheme}://{base_domain}/{href}"

            if same_domain and urlparse(full_url).netloc != base_domain:
                continue

            if full_url not in out:
                out.append(full_url)

        ctx.close()
        return ok(out[:100], {"count": len(out[:100])})

    except Exception as e:
        return err(str(e)[:200], "PARSE")


def screenshot(
    url: str,
    *,
    headless: bool = True,
    full_page: bool = True,
    timeout: int = 30000,
    stealth: bool = True,
    output_path: str = None,
) -> Dict:
    """对目标页面截图，返回 Base64 或保存到文件。

    Args:
        url:         目标 URL
        headless:    无头模式
        full_page:   是否全页截图（含滚动区域）
        timeout:     超时毫秒数
        stealth:     反检测开关
        output_path: 保存路径（可选），不指定则仅返回 Base64

    Returns:
        {"ok": True, "data": {"base64": "...", "path": "..."}}
    """
    if not url.startswith(("http://", "https://")):
        return err("URL 需以 http:// 或 https:// 开头", "BAD_URL")

    try:
        _browser_mgr.start(headless=headless)
        ctx = _browser_mgr.new_context()
        page = ctx.new_page()
        if stealth:
            _inject_stealth(page)

        page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        img_bytes = page.screenshot(full_page=full_page, type="png")
        ctx.close()

        result = {"base64": base64.b64encode(img_bytes).decode()}
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_path).write_bytes(img_bytes)
            result["path"] = str(Path(output_path).resolve())

        return ok(result, {"size_bytes": len(img_bytes)})

    except Exception as e:
        return err(str(e)[:200], "BROWSER_CRASH")


def intercept(
    url: str,
    patterns: List[str] = None,
    *,
    headless: bool = True,
    timeout: int = 30000,
    stealth: bool = True,
    wait_actions: List[str] = None,
) -> Dict:
    """打开页面并拦截所有（或匹配的）网络请求。

    适用于分析目标网站的 XHR/Fetch API 调用。

    Args:
        url:          目标 URL
        patterns:     过滤关键词列表，如 ["api/", ".json", "graphql"]
        headless:     无头模式
        timeout:      超时毫秒数
        stealth:      反检测开关
        wait_actions: 导航后执行的额外操作，如 ["click #btn", "scroll"]

    Returns:
        {"ok": True, "data": [{"url": "...", "status": 200, "body_preview": "..."}]}
    """
    if not url.startswith(("http://", "https://")):
        return err("URL 需以 http:// 或 https:// 开头", "BAD_URL")

    try:
        _browser_mgr.start(headless=headless)
        ctx = _browser_mgr.new_context()
        page = ctx.new_page()
        if stealth:
            _inject_stealth(page)

        captured = []
        def _on_response(response):
            resp_url = response.url
            if patterns and not any(p in resp_url for p in patterns):
                return
            try:
                captured.append({
                    "url": resp_url,
                    "status": response.status,
                    "method": response.request.method,
                    "content_type": response.headers.get("content-type", ""),
                    "body_preview": response.text()[:3000],
                })
            except Exception:
                pass

        page.on("response", _on_response)
        page.goto(url, wait_until="networkidle", timeout=timeout)

        # 执行额外交互操作
        if wait_actions:
            for action in wait_actions:
                if action.startswith("click "):
                    page.click(action[6:].strip())
                elif action.startswith("scroll"):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(1000)

        ctx.close()
        return ok(captured, {"captured": len(captured)})

    except Exception as e:
        return err(str(e)[:200], "NETWORK")


def json_api(url: str, *, timeout: int = 15) -> Dict:
    """快速获取 JSON API（轻量级，不使用浏览器）。

    对纯 JSON 接口使用 requests 比启动浏览器高效得多。
    """
    import requests as req

    try:
        r = req.get(url, timeout=timeout, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        if r.status_code != 200:
            return err(f"HTTP {r.status_code}", "BLOCKED")
        return ok(r.json())
    except req.Timeout:
        return err("请求超时", "TIMEOUT")
    except Exception as e:
        return err(str(e)[:200], "NETWORK")


def stream(
    urls: List[str],
    sel: str = None,
    *,
    headless: bool = True,
    timeout: int = 30000,
    stealth: bool = True,
) -> Iterator[Dict]:
    """流式爬取，逐个 yield 结果，避免大数据集内存溢出。

    >>> for item in stream(["https://a.com", "https://b.com"], "h2"):
    ...     print(item)
    """
    seen = set()
    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        yield fetch(url, sel=sel, headless=headless, timeout=timeout, stealth=stealth)


def close_browser():
    """手动关闭浏览器进程，释放资源。"""
    _browser_mgr.close()


# ========== 使用示例（给 AI 看） ==========

"""
# ===== 基本用法：浏览器渲染 =====
from ai_crawler import fetch

result = fetch("https://www.example.com")
print(result["data"]["title"])        # 页面标题
print(result["data"]["text"][:500])   # 正文前 500 字符

# ===== 带 CSS 选择器 =====
result = fetch("https://news.ycombinator.com", sel=".athing .titleline a")
for item in result["data"]:
    print(item["text"])  # 每条新闻标题

# ===== 有头浏览器（调试 / 遇到强反爬时） =====
result = fetch("https://example.com", headless=False)

# ===== 截图 =====
from ai_crawler import screenshot
result = screenshot("https://example.com", output_path="./page.png")

# ===== 拦截 API 请求 =====
from ai_crawler import intercept
result = intercept("https://example.com", patterns=["api/", ".json"])
for req in result["data"]:
    print(req["url"], req["status"])

# ===== 批量爬取 =====
from ai_crawler import crawl
result = crawl([
    "https://example.com",
    "https://example.org",
], sel="h2", limit=20)

# ===== 提取链接 =====
from ai_crawler import links
result = links("https://example.com", same_domain=True)
print(result["data"])  # 所有同域链接

# ===== 流式爬取（大数据集） =====
from ai_crawler import stream
for item in stream(url_list, "p.content"):
    print(item)

# ===== JSON API（轻量，不用浏览器） =====
from ai_crawler import json_api
result = json_api("https://api.github.com/users/octocat")
print(result["data"]["login"])
"""
