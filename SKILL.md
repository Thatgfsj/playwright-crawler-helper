# Playwright Crawler Helper

基于 Playwright 真实浏览器引擎的爬虫工具。用于需要 JavaScript 渲染的动态页面、网络请求分析、或需要绕过反爬检测的场景。

## 快速开始

```python
from ai_crawler import fetch

# 浏览器渲染获取页面
result = fetch("https://www.example.com")
print(result["data"]["title"])
print(result["data"]["text"][:500])

# 使用 CSS 选择器提取元素
result = fetch("https://news.ycombinator.com", sel=".athing .titleline a")
for item in result["data"]:
    print(item["text"])
```

## 核心 API

| 函数 | 用途 | 使用浏览器 |
|------|------|:----------:|
| `fetch(url, sel, ...)` | 获取页面内容（JS 渲染） | ✅ |
| `crawl(urls, sel, ...)` | 批量爬取，自动去重 | ✅ |
| `links(url, sel, ...)` | 提取页面链接 | ✅ |
| `screenshot(url, ...)` | 页面截图（Base64 / 文件） | ✅ |
| `intercept(url, patterns, ...)` | 拦截 XHR/Fetch 网络请求 | ✅ |
| `stream(urls, sel, ...)` | 流式爬取（逐个 yield） | ✅ |
| `json_api(url)` | 获取 JSON API | ❌（requests） |

## 常用参数

- `headless=True` — 无头模式；遇到强反爬设 `False`
- `stealth=True` — 注入反检测脚本（隐藏 webdriver）
- `wait_until="domcontentloaded"` — 可选 `load` / `networkidle`
- `screenshot=False` — 设为 `True` 返回页面截图 Base64
- `capture_network=False` — 设为 `True` 或传入关键词列表捕获 API 请求
- `scroll=False` — 设为 `True` 自动滚到底部触发懒加载

## 使用场景

1. **动态页面爬取** — React / Vue / SPA 页面
2. **API 分析** — 通过 `intercept()` 捕获页面的 XHR/Fetch 请求
3. **反爬对抗** — 隐藏 webdriver、Chrome 启动参数、有头模式
4. **页面截图** — Canvas / WebGL 内容的截图
5. **批量采集** — `crawl()` 和 `stream()` 支持去重大规模爬取
