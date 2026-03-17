# 🕷️ Playwright 爬虫辅助工具

通过 Playwright 控制浏览器，记录和分析网络请求，辅助编写爬虫脚本。

## 功能概述

1. **网络请求监听** - 捕获页面所有请求，分析 URL、Headers、Method 等
2. **响应内容提取** - 直接获取 JSON/图片/视频/文本等响应内容
3. **请求重放测试** - 复制请求参数，验证爬虫脚本能否正常获取数据
4. **自动生成代码** - 根据捕获的请求生成 Python 爬虫代码片段

## 使用方法

### 1. 启动网络监听

使用 `browser` 技能控制浏览器，访问目标页面后捕获网络请求：

```
使用 browser 技能打开目标网页，然后告诉我需要分析哪个请求
```

### 2. 分析请求并生成爬虫代码

当需要分析特定请求时，使用 `analyze-request` 命令：

```bash
# 分析并生成爬虫代码
python analyze-request.py --url "https://api.example.com/data" --method GET --output crawler.py
```

### 3. 测试请求

```bash
# 测试请求是否成功
python test-request.py --url "https://api.example.com/data" --headers '{"Authorization": "Bearer xxx"}'
```

## 核心脚本

### analyze-request.py

分析网络请求并生成爬虫代码：

```bash
python analyze-request.py --url "请求URL" --method GET --output result.py
```

选项：
- `--url`: 请求的完整 URL
- `--method`: 请求方法 (GET/POST)
- `--headers`: 请求头 (JSON 格式)
- `--body`: 请求体 (JSON 格式)
- `--output`: 输出文件路径
- `--parse-json`: 是否解析 JSON 响应

### test-request.py

测试请求是否可用：

```bash
python test-request.py --url "https://api.example.com/data"
```

选项：
- `--url`: 请求 URL
- `--method`: 请求方法
- `--headers`: 请求头 (JSON)
- `--body`: 请求体 (JSON)
- `--save`: 保存响应到文件

### generate-crawler.py

根据分析结果生成完整爬虫脚本：

```bash
python generate-crawler.py --url "目标URL" --data-selector ".content" --output my_crawler.py
```

## 典型工作流

1. **用 browser 技能打开网页**
   - 访问目标站点
   - 触发需要爬取的内容加载

2. **打开开发者工具 F12**
   - 切换到 Network 标签
   - 找到关键的 API 请求

3. **复制请求信息**
   - 右键请求 → Copy → Copy as cURL

4. **用本工具生成代码**
   ```bash
   python analyze-request.py --curl "curl内容" --output crawler.py
   ```

5. **测试并调整**
   ```bash
   python test-request.py --url "生成的URL"
   ```

## 依赖安装

```bash
# 使用 uv
uv venv crawler-env
source crawler-env/bin/activate
uv pip install playwright requests

# 或使用 pip
pip install playwright requests
playwright install chromium
```

## 注意事项

- 使用无头模式时，部分网站可能检测到自动化工具
- 某些请求需要登录态或特定 Cookie，记得一并复制
- 图片/视频爬取可能需要处理二进制响应
- 建议先用 test-request.py 测试，确认能获取数据后再写完整爬虫
