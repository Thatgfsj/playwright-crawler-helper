# Playwright Crawler Helper

🕷️ 基于 Playwright 真实浏览器的爬虫辅助工具 —— 单文件、零配置，专为 AI 代理设计的即导即用接口。

## 为什么用浏览器

`requests` + `BeautifulSoup` 只能拿到静态 HTML。面对以下场景，必须使用真实浏览器：

- **JavaScript 渲染页面**（React / Vue / SPA）
- **反爬检测**（检查 `navigator.webdriver`、Canvas 指纹等）
- **需要分析 XHR/Fetch API 调用**
- **页面截图**（含 Canvas / WebGL 内容）

本项目在 Playwright 之上封装了极简的函数式接口，同时保留了浏览器的高级能力。

## 技术栈

<p align="left">
  <img src="https://img.shields.io/badge/Python-3.8%2B-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Playwright-1.48-2EAD33?style=flat-square&logo=playwright&logoColor=white" alt="Playwright">
  <img src="https://img.shields.io/badge/Chromium-Engine-4285F4?style=flat-square&logo=googlechrome&logoColor=white" alt="Chromium">
  <img src="https://img.shields.io/badge/BeautifulSoup-4.12-59666C?style=flat-square" alt="BeautifulSoup">
</p>

## 快速开始

### 安装

```bash
pip install playwright beautifulsoup4
playwright install chromium
```

### 基本用法

```python
from ai_crawler import fetch

# 浏览器渲染获取页面
result = fetch("https://www.example.com")
print(result["data"]["title"])
print(result["data"]["text"][:500])
```

每个函数返回统一结构：`{"ok": True/False, "data": ..., "error": "", "code": "OK", "meta": {...}}`

## API 参考

### `fetch(url, sel=None, *, headless=True, ...)`

使用真实浏览器获取页面，完整渲染 JavaScript。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `url` | `str` | — | 目标 URL |
| `sel` | `str` | `None` | CSS 选择器，不指定则返回全文 |
| `headless` | `bool` | `True` | 无头模式；遇到强反爬时设 `False` |
| `wait_until` | `str` | `"domcontentloaded"` | `domcontentloaded` / `load` / `networkidle` |
| `timeout` | `int` | `30000` | 超时毫秒数 |
| `screenshot` | `bool` | `False` | 是否附带页面截图（Base64） |
| `stealth` | `bool` | `True` | 是否注入反检测脚本 |
| `capture_network` | `bool \| list` | `False` | 捕获 XHR/Fetch；`True` 全捕获，或传关键词列表 |
| `scroll` | `bool` | `False` | 是否滚到底部触发懒加载 |

```python
# 提取所有标题
result = fetch("https://news.ycombinator.com", sel=".athing .titleline a")

# 捕获 API 请求
result = fetch("https://example.com", capture_network=["api/", ".json"])
print(result["data"]["_network"])

# 有头模式 + 截图
result = fetch("https://example.com", headless=False, screenshot=True)
```

### `crawl(urls, sel=None, *, limit=10, ...)`

批量爬取，自动去重，复用浏览器进程。

```python
from ai_crawler import crawl

result = crawl([
    "https://example.com/page/1",
    "https://example.com/page/2",
], sel="article h2", limit=20)
```

### `links(url, sel="a", *, same_domain=False, ...)`

提取 JS 渲染后的所有链接。

```python
from ai_crawler import links

result = links("https://example.com", same_domain=True)
# ["https://example.com/about", "https://example.com/contact", ...]
```

### `screenshot(url, *, full_page=True, output_path=None, ...)`

对页面截图，返回 Base64 或保存到文件。

```python
from ai_crawler import screenshot

# 保存到文件
result = screenshot("https://example.com", output_path="./page.png")

# 仅获取 Base64
result = screenshot("https://example.com")
print(result["data"]["base64"][:100])
```

### `intercept(url, patterns=None, *, wait_actions=None, ...)`

打开页面并拦截网络请求，用于分析目标网站的 API 调用。

```python
from ai_crawler import intercept

# 拦截所有 JSON API
result = intercept("https://example.com", patterns=["api/", ".json"])
for req in result["data"]:
    print(req["url"], req["status"], req["body_preview"][:200])

# 支持交互操作后捕获
result = intercept(
    "https://example.com",
    patterns=["api/"],
    wait_actions=["click #load-more", "scroll"],
)
```

### `json_api(url, *, timeout=15)`

轻量级 JSON API 获取——使用 `requests`，不启动浏览器。对纯 JSON 接口最高效。

```python
from ai_crawler import json_api

result = json_api("https://api.github.com/users/octocat")
print(result["data"]["login"])
```

### `stream(urls, sel=None, ...)`

流式爬取，逐个 yield 结果，适合大数据集。

```python
from ai_crawler import stream

for item in stream(huge_url_list, "p.content"):
    print(item)
```

## 反爬设计

- **隐藏 `navigator.webdriver`** —— 在页面加载前通过 `add_init_script` 注入 JS 覆盖
- **真实 User-Agent** —— 使用最新 Chrome 的 UA
- **Chromium 启动参数** —— `--disable-blink-features=AutomationControlled`
- **标准化视口** —— 1920×1080 + 中文 locale
- **遇到强反爬** → 设 `headless=False` 启动有头浏览器，或在 `wait_actions` 中加入模拟操作

## 浏览器生命周期

浏览器进程在首次调用时自动启动，后续请求复用同一进程。每个爬取任务创建独立的浏览器上下文（相当于无痕窗口），互不干扰。

```python
from ai_crawler import close_browser

# 手动释放资源（通常在脚本结束时调用）
close_browser()
```

## 错误码

| code | 含义 |
|------|------|
| `OK` | 成功 |
| `TIMEOUT` | 页面加载超时 |
| `NETWORK` | DNS / 连接 / SSL 错误 |
| `BLOCKED` | HTTP 非 200 / 被反爬拦截 |
| `BAD_URL` | URL 格式无效 |
| `PARSE` | 解析响应内容失败 |
| `BROWSER_CRASH` | 浏览器进程异常 |

## 依赖

- Python 3.8+
- [playwright](https://playwright.dev/python/) ≥ 1.48
- [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/) ≥ 4.12（`json_api` 使用）

## License

MIT
