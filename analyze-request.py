#!/usr/bin/env python3
"""
分析网络请求并生成爬虫代码框架
⚠️ 仅供学习研究使用，请遵守相关法律法规和网站服务条款
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


def generate_template(req: Dict[str, Any], parse_json: bool = False) -> str:
    """生成爬虫代码模板 - 需要用户自行修改参数"""
    url = req.get("url", "")
    method = req.get("method", "GET")
    headers = req.get("headers", {})
    body = req.get("body")
    
    # 脱敏处理
    safe_headers = {}
    for k, v in headers.items():
        lower_k = k.lower()
        if any(x in lower_k for x in ['cookie', 'authorization', 'token', 'secret', 'key']):
            safe_headers[k] = "YOUR_" + k.upper() + "_HERE"
        else:
            safe_headers[k] = v
    
    code = f"""#!/usr/bin/env python3
\"\"\"
爬虫代码模板 - 需要根据目标网站自行修改
⚠️ 请遵守 robots.txt 和网站服务条款，仅供学习研究使用
\"\"\"

import requests

# TODO: 填写目标 URL
url = "{url}"

# TODO: 根据实际请求填写 headers，敏感信息需要自行替换
headers = {json.dumps(safe_headers, indent=4, ensure_ascii=False)}

# TODO: 如果是 POST 请求，填写请求体
# data = {{}}
# 或
# json_data = {json.dumps(body, indent=4, ensure_ascii=False) if body else "{}"}

def fetch():
    \"\"\"发送请求 - 根据实际情况修改\"\"\"
    
    # TODO: 添加错误处理、反爬策略应对等
    # TODO: 添加请求间隔，避免对目标网站造成负担
    
    try:
"""
    
    if method == "GET":
        code += '        response = requests.get(url, headers=headers, timeout=10)\n'
    else:
        code += '        # response = requests.post(url, headers=headers, json=json_data, timeout=10)\n'
    
    code += """        # TODO: 处理响应
        # if response.status_code == 200:
        #     content = response.text  # 或 response.json()
        #     # TODO: 解析内容
        
        pass
        
    except requests.RequestException as e:
        print(f"请求失败: {{e}}")

if __name__ == "__main__":
    fetch()
"""
    
    return code


def generate_curl_code(req: Dict[str, Any]) -> str:
    """生成脱敏的 curl 命令"""
    url = req.get("url", "")
    method = req.get("method", "GET")
    headers = req.get("headers", {})
    body = req.get("body")
    
    # 脱敏
    safe_headers = {}
    for k, v in headers.items():
        lower_k = k.lower()
        if any(x in lower_k for x in ['cookie', 'authorization', 'token', 'secret', 'key']):
            safe_headers[k] = "YOUR_" + k.upper() + "_HERE"
        else:
            safe_headers[k] = v
    
    curl = f"curl -X {method} '{url}'"
    
    for name, value in safe_headers.items():
        curl += f" \\\n  -H '{name}: {value}'"
    
    if body:
        if isinstance(body, dict):
            body_str = json.dumps(body)
        else:
            body_str = str(body)
        curl += f" \\\n  -d '{body_str}'"
    
    return """# 示例 curl 命令 - 请替换敏感信息
# ⚠️ 请遵守网站服务条款
""" + curl


def main():
    parser = argparse.ArgumentParser(
        description="分析网络请求并生成爬虫代码框架",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python analyze-request.py --curl "curl 'https://example.com/api' -H 'Cookie: xxx'"
  python analyze-request.py --url "https://example.com/api" --method GET

⚠️ 警告: 请仅将此工具用于学习研究，遵守相关法律法规
        """
    )
    parser.add_argument("--url", help="请求的 URL")
    parser.add_argument("--method", default="GET", help="请求方法")
    parser.add_argument("--headers", help="请求头 (JSON 格式)")
    parser.add_argument("--body", help="请求体 (JSON 格式)")
    parser.add_argument("--curl", help="curl 命令字符串")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--parse-json", action="store_true", help="生成 JSON 解析示例")
    
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
    code = generate_template(req, args.parse_json)
    
    # 输出
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"代码模板已保存到: {args.output}")
        print("⚠️ 请根据实际情况修改代码，添加必要的错误处理和反爬策略")
    else:
        print(code)


if __name__ == "__main__":
    main()
