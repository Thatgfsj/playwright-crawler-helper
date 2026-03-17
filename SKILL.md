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

# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium
```

### 基础用法

```python
from crawler import load_config, create_browser

# 加载配置
load_config("config.yaml")

# 创建浏览器
with create_browser(headless=False) as browser:
    browser.goto("https://example.com")
    browser.wait_for_selector("#content")
    browser.screenshot("screenshot.png")
    
    # 获取拦截的请求
    requests = browser.get_xhr_requests()
    print(requests)
```

## 📖 配置说明

所有配置在 `config.yaml` 中管理：

- **browser**: 浏览器配置（headless、viewport 等）
- **request**: 请求配置（超时、重试、并发）
- **anticrawler**: 反爬配置（UA、代理、指纹）
- **logging**: 日志配置（级别、文件）
- **output**: 数据输出配置
- **queue**: 任务队列配置
- **checkpoint**: 断点续爬配置

## 📚 模块说明

| 模块 | 功能 |
|------|------|
| `crawler.config` | 配置管理 |
| `crawler.logger` | 日志体系 |
| `crawler.anticrawler` | 反爬伪装 |
| `crawler.browser` | 浏览器封装 |
| `crawler.queue` | 任务队列 |
| `crawler.checkpoint` | 断点续爬 |
| `crawler.output` | 数据导出 |

## 🧪 运行测试

```bash
python -m pytest tests/ -v
```

## ⚠️ 注意事项

- 请遵守 robots.txt 和网站服务条款
- 添加请求间隔，避免对目标网站造成负担
- 不要爬取敏感或受版权保护的内容
