# 🕷️ Playwright 爬虫辅助工具

通过 Playwright 控制浏览器，记录和分析网络请求，辅助编写爬虫脚本。

> ⚠️ **免责声明**: 此工具仅供学习研究使用，请遵守相关法律法规和目标网站的 robots.txt 及服务条款。

## 功能概述

1. **网络请求监听** - 捕获页面所有请求，分析 URL、Headers、Method 等
2. **响应内容提取** - 直接获取 JSON/图片/视频/文本等响应内容
3. **请求重放测试** - 复制请求参数，验证爬虫脚本能否正常获取数据
4. **自动生成代码** - 根据捕获的请求生成 Python 爬虫代码模板（需用户自行修改）

## 使用方法

### 1. 启动网络监听

使用 `browser` 技能控制浏览器，访问目标页面后捕获网络请求：

```
使用 browser 技能打开目标网页，然后告诉我需要分析哪个请求
```

### 2. 分析请求并生成爬虫代码

当需要分析特定请求时，使用 `analyze-request` 命令：

```bash
# 分析并生成爬虫代码模板
python analyze-request.py --url "https://api.example.com/data" --method GET --output crawler.py
```

### 3. 测试请求

```bash
# 测试请求是否成功
python test-request.py --url "https://api.example.com/data"
```

### 4. 生成完整爬虫模板

```bash
# 生成图片爬虫模板
python generate-crawler.py --url "https://example.com/image.jpg" --type image --output image_crawler.py

# 生成视频爬虫模板
python generate-crawler.py --url "https://example.com/video.mp4" --type video --output video_crawler.py

# 生成 API 爬虫模板
python generate-crawler.py --url "https://api.example.com/data" --type api --output api_crawler.py

# 生成网页爬虫模板
python generate-crawler.py --url "https://example.com" --type page --selectors '["article", "div.content"]'
```

## 核心脚本

### analyze-request.py

分析网络请求并生成爬虫代码模板：

```bash
python analyze-request.py --url "请求URL" --method GET --output result.py
```

选项：
- `--url`: 请求的完整 URL
- `--method`: 请求方法 (GET/POST)
- `--headers`: 请求头 (JSON 格式)
- `--body`: 请求体 (JSON 格式)
- `--curl`: 直接解析 curl 命令
- `--output`: 输出文件路径

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

根据分析结果生成爬虫脚本模板：

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

5. **修改模板**
   - 替换敏感信息（Cookie、Token 等）
   - 添加错误处理
   - 添加请求间隔
   - 根据目标网站反爬策略调整

6. **测试并运行**
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

## ⚠️ 注意事项

- 使用无头模式时，部分网站可能检测到自动化工具
- 某些请求需要登录态或特定 Cookie，记得一并处理
- 图片/视频爬取可能需要处理二进制响应
- 建议先用 test-request.py 测试，确认能获取数据后再运行完整爬虫
- **请遵守 robots.txt 和网站服务条款**
- **添加请求间隔，避免对目标网站造成负担**
- **不要爬取敏感或受版权保护的内容**
