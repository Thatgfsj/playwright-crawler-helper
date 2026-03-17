# 🕷️ Playwright Crawler Helper

通过 Playwright 控制浏览器，记录和分析网络请求，辅助编写爬虫脚本。

> ⚠️ **免责声明**: 此工具仅供学习研究使用，请遵守相关法律法规和目标网站的 robots.txt 及服务条款。

## ✨ 功能特性

| 功能 | 描述 |
|------|------|
| 🎯 网络请求监听 | 捕获页面所有请求 |
| 🔄 Crawlee 风格 | Context、Router、Decorator 模式 |
| 🛡️ 反爬伪装 | 代理池、随机 UA、指纹伪装 |
| 📊 任务队列 | 并发控制、失败重试 |
| 💾 断点续爬 | 去重机制、状态保存 |
| 📁 数据导出 | JSON/CSV/SQLite |
| 📝 日志体系 | DEBUG/INFO/WARNING/ERROR |
| ⚙️ 配置管理 | YAML 配置 |

## 🚀 快速开始

### 安装

```bash
pip install -r requirements.txt
```

### AI 轻量接口 (推荐)

```python
from ai_crawler import crawl, fetch, get_links

# 最简调用
result = fetch("https://example.com")
print(result["data"])

# 批量爬取 + CSS 选择器
result = crawl(["https://example.com"], ".article h2")

# 获取页面链接
links = get_links("https://example.com")
```

### Crawlee 风格 (异步)

```python
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
```

## 📚 模块说明

| 模块 | 功能 |
|------|------|
| `ai_crawler.py` | AI 轻量爬虫接口 |
| `crawler/` | 完整爬虫框架 |
| `config.yaml` | 配置文件 |

## ⚠️ 注意

- 请遵守 robots.txt 和网站服务条款
