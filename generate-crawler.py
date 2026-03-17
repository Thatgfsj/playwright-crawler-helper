#!/usr/bin/env python3
"""
根据分析结果生成完整的爬虫脚本
支持图片、视频、文本等多种内容类型的爬取
"""

import argparse
import json
import sys
from typing import Optional, List, Dict, Any


def generate_image_crawler(url: str, save_dir: str = "images") -> str:
    """生成图片爬虫"""
    return f'''#!/usr/bin/env python3
"""
图片爬虫 - 从 {url}
"""

import os
import requests
from urllib.parse import urljoin, urlparse
from pathlib import Path

SAVE_DIR = "{save_dir}"

def download_image(url: str, filename: str = None) -> bool:
    """下载单张图片"""
    try:
        response = requests.get(url, timeout=30)
        if not response.ok:
            print(f"❌ 下载失败: {{url}} - {{response.status_code}}")
            return False
        
        # 解析文件名
        if not filename:
            parsed = urlparse(url)
            filename = os.path.basename(parsed.path) or "image.jpg"
        
        # 确保目录存在
        os.makedirs(SAVE_DIR, exist_ok=True)
        filepath = os.path.join(SAVE_DIR, filename)
        
        with open(filepath, "wb") as f:
            f.write(response.content)
        
        print(f"✅ 已保存: {{filepath}}")
        return True
        
    except Exception as e:
        print(f"❌ 下载出错: {{url}} - {{e}}")
        return False

def main():
    # 图片 URL 列表
    image_urls = [
        "{url}",
        # 添加更多图片 URL
    ]
    
    for i, url in enumerate(image_urls):
        ext = url.split(".")[-1][:4]  # 获取扩展名
        filename = f"image_{{i+1}}.{{ext}}"
        download_image(url, filename)

if __name__ == "__main__":
    main()
'''


def generate_video_crawler(url: str, save_dir: str = "videos") -> str:
    """生成视频爬虫"""
    return f'''#!/usr/bin/env python3
"""
视频爬虫 - 从 {url}
"""

import os
import requests
from pathlib import Path

SAVE_DIR = "{save_dir}"

def download_video(url: str, filename: str = None) -> bool:
    """下载视频"""
    try:
        # 使用流式下载，处理大文件
        response = requests.get(url, stream=True, timeout=300)
        if not response.ok:
            print(f"❌ 下载失败: {{url}} - {{response.status_code}}")
            return False
        
        # 解析文件名
        if not filename:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            filename = os.path.basename(parsed.path) or "video.mp4"
        
        os.makedirs(SAVE_DIR, exist_ok=True)
        filepath = os.path.join(SAVE_DIR, filename)
        
        # 流式写入
        total = int(response.headers.get("Content-Length", 0))
        downloaded = 0
        
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        print(f"\\r下载进度: {{downloaded}}/{{total}} ({{100*downloaded//total}}%)", end="")
        
        print(f"\\n✅ 已保存: {{filepath}}")
        return True
        
    except Exception as e:
        print(f"❌ 下载出错: {{url}} - {{e}}")
        return False

def main():
    video_urls = [
        "{url}",
        # 添加更多视频 URL
    ]
    
    for i, url in enumerate(video_urls):
        ext = url.split(".")[-1][:4]
        filename = f"video_{{i+1}}.{{ext}}"
        download_video(url, filename)

if __name__ == "__main__":
    main()
'''


def generate_api_crawler(url: str, headers: Dict[str, str] = None, body: Any = None) -> str:
    """生成 API 数据爬虫"""
    headers_str = json.dumps(headers, indent=4, ensure_ascii=False) if headers else "{}"
    body_str = json.dumps(body, indent=4, ensure_ascii=False) if body else "None"
    
    return f'''#!/usr/bin/env python3
"""
API 数据爬虫 - {url}
"""

import requests
import json

url = "{url}"

headers = {headers_str}

# 请求体 (POST 请求时使用)
body = {body_str}

def fetch_data():
    """获取数据"""
    try:
        if body:
            response = requests.post(url, headers=headers, json=body)
        else:
            response = requests.get(url, headers=headers)
        
        print(f"Status: {{response.status_code}}")
        
        # 解析 JSON
        data = response.json()
        
        # 保存到文件
        with open("data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print("✅ 数据已保存到 data.json")
        return data
        
    except Exception as e:
        print(f"❌ 请求失败: {{e}}")
        return None

def parse_items(data):
    """解析数据项 - 根据实际响应结构调整"""
    # 示例: 如果响应是 {{"data": [...]}}
    # items = data.get("data", [])
    
    # 示例: 如果响应是数组
    items = data if isinstance(data, list) else [data]
    
    for item in items:
        print(json.dumps(item, ensure_ascii=False, indent=2))
    
    return items

if __name__ == "__main__":
    data = fetch_data()
    if data:
        parse_items(data)
'''


def generate_page_crawler(url: str, selectors: List[str] = None) -> str:
    """生成网页内容爬虫"""
    selectors_str = json.dumps(selectors, ensure_ascii=False) if selectors else '["article", "div.content", "main"]'
    
    return f'''#!/usr/bin/env python3
"""
网页内容爬虫 - {url}
"""

from playwright.sync_api import sync_playwright

url = "{url}"

# 要提取的元素选择器
SELECTORS = {selectors_str}

def crawl_page():
    """爬取页面内容"""
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 设置 User-Agent
        page.set_extra_http_headers({{
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }})
        
        # 访问页面
        print(f"🔍 访问: {{url}}")
        page.goto(url, wait_until="networkidle")
        
        # 提取内容
        results = {{}}
        for selector in SELECTORS:
            elements = page.query_selector_all(selector)
            texts = [el.text_content().strip() for el in elements if el.text_content()]
            if texts:
                results[selector] = texts
                print(f"✅ 找到 {{len(texts)}} 个元素: {{selector}}")
        
        # 保存结果
        import json
        with open("page_content.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print("✅ 内容已保存到 page_content.json")
        browser.close()
        
        return results

if __name__ == "__main__":
    crawl_page()
'''


def main():
    parser = argparse.ArgumentParser(description="生成完整爬虫脚本")
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
        code = generate_image_crawler(args.url, args.save_dir)
    elif args.type == "video":
        code = generate_video_crawler(args.url, args.save_dir)
    elif args.type == "api":
        code = generate_api_crawler(args.url, headers, body)
    else:
        code = generate_page_crawler(args.url, selectors)
    
    # 保存
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"✅ 爬虫脚本已保存到: {args.output}")
    else:
        print(code)


if __name__ == "__main__":
    main()
