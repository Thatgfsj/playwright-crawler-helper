# 🕷️ Playwright Crawler Helper

通过 Playwright 控制浏览器，记录和分析网络请求，辅助编写爬虫脚本。

> ⚠️ **免责声明**: 此工具仅供学习研究使用，请遵守相关法律法规和目标网站的 robots.txt 及服务条款。

## ✨ 功能特性

| 功能 | 描述 |
|------|------|
| 🎯 网络请求监听 | 捕获页面所有请求，分析 URL、Headers、Method 等 |
| 🔄 请求重放测试 | 复制请求参数，验证爬虫脚本能否正常获取数据 |
| 🛡️ 反爬伪装 | 代理池、随机 UA、指纹伪装 |
| 📊 任务队列 | 支持并发控制、失败重试 |
| 💾 断点续爬 | 去重机制、状态保存 |
| 📁 数据导出 | 支持 JSON/CSV/SQLite |
| 📝 日志体系 | DEBUG/INFO/WARNING/ERROR 分级 |
| ⚙️ 配置管理 | YAML/JSON 配置文件 |

## 🚀 快速开始

### 安装依赖

```bash
# 克隆仓库
git clone https://github.com/Thatgfsj/playwright-crawler-helper.git
cd playwright-crawler-helper

# 创建虚拟环境（推荐）
uv venv crawler-env
source crawler-env/bin/activate  # Linux/macOS
# 或 crawler-env\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium
```

### 基础用法

```python
from crawler import load_config, create_browser

# 加载配置（可选）
load_config("config.yaml")

# 创建浏览器
with create_browser(headless=False) as browser:
    # 访问页面
    browser.goto("https://example.com")
    
    # 等待元素
    browser.wait_for_selector("#content")
    
    # 点击元素
    browser.click("button.submit")
    
    # 输入文本
    browser.type("input#keyword", "Python")
    
    # 截图
    browser.screenshot("screenshot.png")
    
    # 获取拦截的请求
    requests = browser.get_xhr_requests()
    print(requests)
```

### 分析请求

```python
from crawler.browser import PlaywrightBrowser

with PlaywrightBrowser() as browser:
    browser.goto("https://api.example.com/data")
    
    # 获取所有请求
    all_requests = browser.get_requests()
    
    # 获取 XHR 请求
    xhr_requests = browser.get_xhr_requests()
    
    # 获取 API 响应
    response = browser.get_api_response()
    print(response)
```

## 📖 配置说明

### config.yaml

```yaml
# 浏览器配置
browser:
  headless: false
  viewport:
    width: 1280
    height: 720
  slow_mo: 0

# 请求配置
request:
  timeout: 30
  retry:
    max: 3
    delay: 1
  interval: 1
  max_concurrency: 3

# 反爬配置
anticrawler:
  random_ua: true
  ua_list:
    - "Mozilla/5.0 ..."
  proxies:
    - "http://user:pass@host:port"
  fingerprint:
    timezone: "Asia/Shanghai"
    locale: "zh-CN"

# 日志配置
logging:
  level: INFO
  file:
    enabled: true
    path: "./logs/crawler.log"

# 数据输出
output:
  default_format: json
  directory: "./data"

# 断点续爬
checkpoint:
  enabled: true
  file: "./data/checkpoint.json"
  dedup_fields: ["url", "id"]
```

## 📚 API 参考

### 浏览器操作

```python
from crawler import create_browser

with create_browser() as browser:
    # 导航
    browser.goto(url, wait_until="networkidle")
    browser.wait_for_load_state("networkidle")
    
    # 等待
    browser.wait_for_selector(selector, timeout=10000)
    
    # 操作
    browser.click(selector)
    browser.type(selector, text)
    browser.fill(selector, value)
    browser.select(selector, value)
    
    # 滚动
    browser.scroll_down(times=3)
    browser.scroll_to(selector="#footer")
    
    # 获取内容
    text = browser.get_text(selector)
    attr = browser.get_attribute(selector, "href")
    
    # 截图
    browser.screenshot("page.png", full_page=True)
    
    # 请求拦截
    requests = browser.get_xhr_requests()
    response = browser.get_api_response(url)
```

### 任务队列

```python
from crawler import get_queue, Task

queue = get_queue()

# 添加任务
queue.add_task("爬取首页", url="https://example.com")

# 启动工作线程
def worker(task):
    # 处理任务
    return {"result": "success"}

queue.start_workers(worker, num_workers=3)

# 等待一段时间后停止
import time
time.sleep(60)
queue.stop()
```

### 数据导出

```python
from crawler import DataCollector, create_exporter

# 收集数据
collector = DataCollector()
collector.add({"title": "文章1", "url": "https://example.com/1"})
collector.add({"title": "文章2", "url": "https://example.com/2"})

# 导出
collector.export(filename="articles")

# 或使用快捷函数
from crawler import collect_and_export

data = [{"title": "文章1"}, {"title": "文章2"}]
collect_and_export(data, format="csv", filename="articles")
```

### 断点续爬

```python
from crawler import get_checkpoint

checkpoint = get_checkpoint()

# 检查是否已访问
item = {"url": "https://example.com/1", "id": "123"}
if not checkpoint.is_visited(item):
    # 处理...
    checkpoint.mark_visited(item)

# 保存断点
checkpoint.save()
```

## 🧪 运行测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试
python -m pytest tests/test_core.py::TestConfig -v

# 带覆盖率
python -m pytest tests/ --cov=crawler --cov-report=html
```

## 📁 项目结构

```
playwright-crawler-helper/
├── config.yaml           # 配置文件
├── requirements.txt      # 依赖
├── README.md            # 文档
├── crawler/
│   ├── __init__.py      # 入口
│   ├── config.py        # 配置管理
│   ├── logger.py        # 日志模块
│   ├── anticrawler.py   # 反爬伪装
│   ├── browser.py       # 浏览器封装
│   ├── queue.py         # 任务队列
│   ├── checkpoint.py    # 断点续爬
│   └── output.py        # 数据导出
├── tests/
│   └── test_core.py    # 单元测试
├── examples/
│   └── demo.py         # 示例代码
└── data/                # 数据输出目录
    └── logs/            # 日志目录
```

## ⚠️ 注意事项

- 使用无头模式时，部分网站可能检测到自动化工具
- 某些请求需要登录态或特定 Cookie，记得处理
- 请遵守 robots.txt 和网站服务条款
- 添加请求间隔，避免对目标网站造成负担

## 📄 许可证

MIT License
