# 🕷️ AI Crawler

极简爬虫框架，专为 AI 代理设计。单文件、无状态、纯内存。

> ⚠️ 仅供学习研究，遵守 robots.txt

## 🚀 3 行跑通

```python
from ai_crawler import fetch
result = fetch("https://example.com")
print(result["data"]["title"])
```

## 📖 接口

| 函数 | 用途 |
|------|------|
| `fetch(url, sel)` | 单页爬取 |
| `crawl(urls, sel, limit)` | 批量爬取 |
| `links(url)` | 获取链接 |
| `json_api(url)` | JSON API |
| `stream(urls, sel)` | 流式返回 |

## 示例

```python
# 带选择器
result = fetch("https://example.com", "h2")
# {"ok": true, "data": [{"text": "..."}]}

# 批量
result = crawl(["https://a.com", "https://b.com"], "article")

# 链接
result = links("https://example.com")

# JSON
result = json_api("https://api.github.com/users/octocat")

# 流式
for item in stream(["https://a.com"], "p"):
    print(item)
```

## 返回格式

```python
{"ok": True, "data": ..., "error": "", "code": "OK", "meta": {...}}
{"ok": False, "data": None, "error": "...", "code": "TIMEOUT", "meta": {}}
```

## 错误码

- `OK` - 成功
- `TIMEOUT` - 超时
- `NETWORK` - 网络错误
- `BLOCKED` - 被拦截
- `BAD_URL` - 无效URL
- `TOO_BIG` - 内容过大
- `PARSE` - 解析失败

## 安装

```bash
pip install requests beautifulsoup4
```
