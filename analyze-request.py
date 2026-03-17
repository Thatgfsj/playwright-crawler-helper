#!/usr/bin/env python3
"""
分析网络请求并生成爬虫代码
支持从 URL、cURL 或手动输入的参数生成代码
"""

import argparse
import json
import re
import sys
import urllib.parse
from typing import Optional, Dict, Any


def parse_curl(curl_cmd: str) -> Dict[str, Any]:
    """解析 curl 命令，提取请求信息"""
    result = {
        "url": "",
        "method": "GET",
        "headers": {},
        "body": None
    }
    
    # 提取 URL
    url_match = re.search(r"curl\s+['\"]?(https?://[^\s'\"жа]+)", curl_cmd)
    if not url_match:
        url_match = re.search(r"(https?://[^\s'\"жа]+)", curl_cmd)
    if url_match:
        result["url"] = url_match.group(1).rstrip("'\"")
    
    # 提取 method
    if "-X " in curl_cmd or "--request " in curl_cmd:
        method_match = re.search(r"-X\s+(\w+)|--request\s+(\w+)", curl_cmd)
        if method_match:
            result["method"] = method_match.group(1) or method_match.group(2)
    
    # 提取 headers
    header_matches = re.findall(r"-H\s+['\"]([^:]+):\s*([^'\"]+)['\"]", curl_cmd)
    for name, value in header_matches:
        result["headers"][name.strip()] = value.strip()
    
    # 提取 body
    body_match = re.search(r"-d\s+['\"]([^'\"]+)['\"]|--data['\"]?\s+['\"]([^'\"]+)['\"]", curl_cmd)
    if body_match:
        body_str = body_match.group(1) or body_match.group(2)
        try:
            result["body"] = json.loads(body_str)
        except:
            result["body"] = body_str
        result["method"] = "POST"
    
    return result


def generate_requests_code(req: Dict[str, Any], parse_json: bool = False) -> str:
    """生成使用 requests 库的爬虫代码"""
    url = req.get("url", "")
    method = req.get("method", "GET")
    headers = req.get("headers", {})
    body = req.get("body")
    
    code = f"""import requests

url = "{url}"

headers = {json.dumps(headers, indent=4, ensure_ascii=False)}

"""
    
    if method == "GET":
        code += """response = requests.get(url, headers=headers)
"""
    else:
        code += f"""data = {json.dumps(body, indent=4, ensure_ascii=False)}

response = requests.post(url, headers=headers, json=data)
"""
    
    if parse_json:
        code += """
# 解析 JSON 响应
result = response.json()
print(json.dumps(result, indent=2, ensure_ascii=False))
"""
    else:
        code += """
# 打印响应状态和内容
print(f"Status: {response.status_code}")
print(response.text)
"""
    
    return code


def generate_playwright_code(req: Dict[str, Any], parse_json: bool = False) -> str:
    """生成使用 Playwright 的爬虫代码"""
    url = req.get("url", "")
    method = req.get("method", "GET")
    headers = req.get("headers", {})
    body = req.get("body")
    
    headers_str = json.dumps(headers, indent=6, ensure_ascii=False)
    
    code = f"""from playwright.sync_api import sync_playwright

def crawl():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        # 设置额外的请求头
        page.set_extra_http_headers({headers_str})
        
        # 发送请求
        response = page.goto("{url}")
        
        # 获取响应内容
        content = response.text()
        
        print(f"Status: {{response.status}}")
        print(content[:1000])  # 打印前1000字符
        
        browser.close()

if __name__ == "__main__":
    crawl()
"""
    
    return code


def generate_curl_code(req: Dict[str, Any]) -> str:
    """生成 curl 命令"""
    url = req.get("url", "")
    method = req.get("method", "GET")
    headers = req.get("headers", {})
    body = req.get("body")
    
    curl = f"curl -X {method} '{url}'"
    
    for name, value in headers.items():
        curl += f" \\\n  -H '{name}: {value}'"
    
    if body:
        if isinstance(body, dict):
            body_str = json.dumps(body)
        else:
            body_str = str(body)
        curl += f" \\\n  -d '{body_str}'"
    
    return curl


def main():
    parser = argparse.ArgumentParser(description="分析网络请求并生成爬虫代码")
    parser.add_argument("--url", help="请求的 URL")
    parser.add_argument("--method", default="GET", help="请求方法")
    parser.add_argument("--headers", help="请求头 (JSON 格式)")
    parser.add_argument("--body", help="请求体 (JSON 格式)")
    parser.add_argument("--curl", help="curl 命令字符串")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--parse-json", action="store_true", help="解析 JSON 响应")
    parser.add_argument("--lib", choices=["requests", "playwright", "curl"], 
                       default="requests", help="生成的代码库类型")
    
    args = parser.parse_args()
    
    # 解析请求信息
    if args.curl:
        req = parse_curl(args.curl)
    elif args.url:
        req = {
            "url": args.url,
            "method": args.method,
            "headers": json.loads(args.headers) if args.headers else {},
            "body": json.loads(args.body) if args.body else None
        }
    else:
        print("Error: 请提供 --url 或 --curl 参数")
        sys.exit(1)
    
    # 生成代码
    if args.lib == "requests":
        code = generate_requests_code(req, args.parse_json)
    elif args.lib == "playwright":
        code = generate_playwright_code(req, args.parse_json)
    else:
        code = generate_curl_code(req)
    
    # 输出
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"代码已保存到: {args.output}")
    else:
        print(code)


if __name__ == "__main__":
    main()
