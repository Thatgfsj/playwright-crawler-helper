#!/usr/bin/env python3
"""
根据分析结果生成爬虫脚本模板
⚠️ 仅供学习研究使用，请遵守相关法律法规和网站服务条款
"""

import argparse
import json
import sys
from typing import Optional, List, Dict, Any


def generate_image_template(url: str, save_dir: str = "images") -> str:
    """生成图片爬虫模板"""
    return f'''#!/usr/bin/env python3
"""
图片爬虫模板 - 需要根据目标网站自行修改
⚠️ 请遵守 robots.txt 和网站服务条款，仅供学习研究使用
"""

import os
import requests
from pathlib import Path

SAVE_DIR = "{save_dir}"

def download_image(url: str, filename: str = None) -> bool:
    \"\"\"下载单张图片 - 根据实际情况修改\"\"\"
    try:
        # TODO: 添加反爬处理：headers、代理、间隔等
        response = requests.get(url, timeout=30)
        if not response.ok:
            print(f"下载失败: {{url}} - {{response.status_code}}")
            return False
        
        # 解析文件名
        if not filename:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            filename = os.path.basename(parsed.path) or "image.jpg"
        
        # 确保目录存在
        os.makedirs(SAVE_DIR, exist_ok=True)
        filepath = os.path.join(SAVE_DIR, filename)
        
        with open(filepath, "wb") as f:
            f.write(response.content)
        
        print(f"已保存: {{filepath}}")
        return True
        
    except Exception as e:
        print(f"下载出错: {{url}} - {{e}}")
        return False

def main():
    # TODO: 填写要下载的图片 URL 列表
    image_urls = [
        "{url}",
        # "https://example.com/image1.jpg",
        # "https://example.com/image2.jpg",
    ]
    
    for i, url in enumerate(image_urls):
        # TODO: 根据实际 URL 结构调整文件名
        ext = url.split(".")[-1][:4] if "." in url else "jpg"
        filename = f"image_{{i+1}}.{{ext}}"
        download_image(url, filename)
        
        # TODO: 添加下载间隔，避免请求过快
        # time.sleep(1)

if __name__ == "__main__":
    main()
'''


def generate_video_template(url: str, save_dir: str = "videos") -> str:
    """生成视频爬虫模板"""
    return f'''#!/usr/bin/env python3
"""
视频爬虫模板 - 需要根据目标网站自行修改
⚠️ 请遵守 robots.txt 和网站服务条款，仅供学习研究使用
"""

import os
import requests
from pathlib import Path

SAVE_DIR = "{save_dir}"

def download_video(url: str, filename: str = None) -> bool:
    \"\"\"下载视频 - 根据实际情况修改\"\"\"
    try:
        # TODO: 添加反爬处理
        # TODO: 大文件建议使用流式下载
        
        response = requests.get(url, stream=True, timeout=300)
        if not response.ok:
            print(f"下载失败: {{url}} - {{response.status_code}}")
            return False
        
        # 解析文件名
        if not filename:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            filename = os.path.basename(parsed.path) or "video.mp4"
        
        os.makedirs(SAVE_DIR, exist_ok=True)
        filepath = os.path.join(SAVE_DIR, filename)
        
        # 流式写入，处理大文件
        total = int(response.headers.get("Content-Length", 0))
        downloaded = 0
        
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        print(f"\\r下载进度: {{downloaded}}/{{total}} ({{100*downloaded//total}}%)", end="")
        
        print(f"\\n已保存: {{filepath}}")
        return True
        
    except Exception as e:
        print(f"下载出错: {{url}} - {{e}}")
        return False

def main():
    # TODO: 填写要下载的视频 URL 列表
    video_urls = [
        "{url}",
        # "https://example.com/video1.mp4",
    ]
    
    for i, url in enumerate(video_urls):
        ext = url.split(".")[-1][:4] if "." in url else "mp4"
        filename = f"video_{{i+1}}.{{ext}}"
        download_video(url, filename)
        
        # TODO: 添加下载间隔
        # time.sleep(2)

if __name__ == "__main__":
    main()
'''


def generate_api_template(url: str, headers: Dict[str, str] = None, body: Any = None) -> str:
    """生成 API 数据爬虫模板"""
    headers_str = json.dumps(headers, indent=4, ensure_ascii=False) if headers else "{}"
    body_str = json.dumps(body, indent=4, ensure_ascii=False) if body else "None"
    
    return f'''#!/usr/bin/env python3
"""
API 数据爬虫模板 - 需要根据目标网站自行修改
⚠️ 请遵守 API 使用条款，仅供学习研究使用
"""

import requests
import json

# TODO: 填写目标 API URL
url = "{url}"

# TODO: 填写请求头，敏感信息需要替换
headers = {headers_str}

# TODO: 如果是 POST 请求，填写请求体
body = {body_str}

def fetch_data():
    \"\"\"获取数据 - 根据实际情况修改\"\"\"
    try:
        if body:
            response = requests.post(url, headers=headers, json=body, timeout=10)
        else:
            response = requests.get(url, headers=headers, timeout=10)
        
        print(f"Status: {{response.status_code}}")
        
        # TODO: 根据实际响应格式解析
        # 如果是 JSON
        # data = response.json()
        
        # 如果是文本/HTML
        # content = response.text
        
        return response
        
    except Exception as e:
        print(f"请求失败: {{e}}")
        return None

def parse_items(response):
    \"\"\"解析数据 - 根据实际响应结构修改\"\"\"
    if not response or not response.ok:
        return []
    
    # TODO: 根据实际响应结构调整解析逻辑
    # 示例: 如果响应是 {{"data": [...]}}
    # try:
    #     data = response.json()
    #     items = data.get("data", [])
    # except:
    #     items = []
    
    # 示例: 如果响应是数组
    # try:
    #     items = response.json()
    # except:
    #     items = []
    
    items = []
    return items

def save_data(items):
    \"\"\"保存数据 - 根据需要修改\"\"\"
    # TODO: 选择合适的存储方式
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"已保存 {{len(items)}} 条数据到 data.json")

if __name__ == "__main__":
    response = fetch_data()
    if response:
        items = parse_items(response)
        save_data(items)
'''


def generate_page_template(url: str, selectors: List[str] = None) -> str:
    """生成网页内容爬虫模板"""
    selectors_str = json.dumps(selectors, ensure_ascii=False) if selectors else '["article", "div.content", "main"]'
    
    return f'''#!/usr/bin/env python3
"""
网页内容爬虫模板 - 需要根据目标网站自行修改
⚠️ 请遵守 robots.txt 和网站服务条款，仅供学习研究使用
"""

from playwright.sync_api import sync_playwright

# TODO: 填写目标 URL
url = "{url}"

# TODO: 填写要提取的元素选择器
SELECTORS = {selectors_str}

def crawl_page():
    \"\"\"爬取页面内容 - 根据实际情况修改\"\"\"
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 设置 User-Agent 和其他 headers
        page.set_extra_http_headers({{
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64;64) AppleWebKit/537.36"
        }})
        
        # 访问页面
        print(f"访问: {{url}}")
        page.goto(url, wait_until="networkidle")
        
        # 提取内容
        results = {{}}
        for selector in SELECTORS:
            # TODO: 选择合适的提取方法
            elements = page.query_selector_all(selector)
            texts = [el.text_content().strip() for el in elements if el.text_content()]
            if texts:
                results[selector] = texts
                print(f"找到 {{len(texts)}} 个元素: {{selector}}")
        
        # 保存结果
        import json
        with open("page_content.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print("内容已保存到 page_content.json")
        browser.close()
        
        return results

if __name__ == "__main__":
    crawl_page()
'''


def main():
    parser = argparse.ArgumentParser(
        description="生成爬虫脚本模板",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
⚠️ 警告: 请仅将此工具用于学习研究
        - 遵守目标网站的 robots.txt
        - 遵守网站服务条款
        - 不要对目标网站造成负担（添加间隔）
        - 敏感信息自行替换
        """
    )
    parser.add_argument("--url", required=True, help="目标 URL")
    parser.add_argument("--type", choices=["image", "video", "api", "page"], 
                       default="page", help="爬取内容类型")
    parser.add_argument("--save-dir", default="downloads", help="保存目录")
    parser.add_argument("--headers", help="请求头 (JSON)")
    parser.add_argument("--body", help="请求体 (JSON)")
    parser.add_argument("--selectors", help="CSS 选择器列表 (JSON)")
    parser.add_argument("--output", "-o", help="输出文件路径")
    
    args = parser.parse_args()
    
    # 解析参数
    headers = json.loads(args.headers) if args.headers else None
    body = json.loads(args.body) if args.body else None
    selectors = json.loads(args.selectors) if args.selectors else None
    
    # 生成代码
    if args.type == "image":
        code = generate_image_template(args.url, args.save_dir)
    elif args.type == "video":
        code = generate_video_template(args.url, args.save_dir)
    elif args.type == "api":
        code = generate_api_template(args.url, headers, body)
    else:
        code = generate_page_template(args.url, selectors)
    
    # 保存
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"✅ 爬虫脚本模板已保存到: {args.output}")
        print("⚠️ 请根据实际情况修改代码，添加反爬处理和错误处理")
    else:
        print(code)


if __name__ == "__main__":
    main()
