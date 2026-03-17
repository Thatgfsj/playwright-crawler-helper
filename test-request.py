#!/usr/bin/env python3
"""
测试网络请求是否可用
支持 GET/POST 方法，可自定义 headers 和 body
"""

import argparse
import json
import sys
import requests
from typing import Optional, Dict, Any


def test_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    body: Optional[Any] = None,
    save: Optional[str] = None,
    timeout: int = 30
) -> bool:
    """测试网络请求"""
    
    if headers is None:
        headers = {}
    
    # 默认 User-Agent
    if "User-Agent" not in headers:
        headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    print(f"🔍 发送请求: {method} {url}")
    print(f"📋 Headers: {json.dumps(headers, ensure_ascii=False, indent=2)}")
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=timeout)
        elif method.upper() == "POST":
            if isinstance(body, dict):
                response = requests.post(url, headers=headers, json=body, timeout=timeout)
            else:
                response = requests.post(url, headers=headers, data=body, timeout=timeout)
        else:
            print(f"❌ 不支持的请求方法: {method}")
            return False
        
        print(f"\n✅ 响应状态: {response.status_code}")
        print(f"📄 响应头: {json.dumps(dict(response.headers), ensure_ascii=False, indent=2)}")
        
        # 检测内容类型
        content_type = response.headers.get("Content-Type", "")
        print(f"📝 Content-Type: {content_type}")
        
        # 保存响应
        if save:
            with open(save, "wb") as f:
                f.write(response.content)
            print(f"💾 响应已保存到: {save}")
        
        # 打印响应内容预览
        if "image" in content_type:
            print(f"\n🖼️ 图片内容，大小: {len(response.content)} bytes")
        elif "video" in content_type:
            print(f"\n🎬 视频内容，大小: {len(response.content)} bytes")
        elif "application/json" in content_type:
            try:
                data = response.json()
                print(f"\n📊 JSON 响应:")
                print(json.dumps(data, ensure_ascii=False, indent=2)[:2000])
            except:
                print(f"\n📄 响应内容:")
                print(response.text[:2000])
        else:
            print(f"\n📄 响应内容:")
            print(response.text[:2000])
        
        return response.ok
        
    except requests.exceptions.Timeout:
        print(f"❌ 请求超时 ({timeout}s)")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 连接失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="测试网络请求是否可用")
    parser.add_argument("--url", required=True, help="请求的 URL")
    parser.add_argument("--method", default="GET", help="请求方法 (GET/POST)")
    parser.add_argument("--headers", help="请求头 (JSON 格式)")
    parser.add_argument("--body", help="请求体 (JSON 格式)")
    parser.add_argument("--save", help="保存响应到文件")
    parser.add_argument("--timeout", type=int, default=30, help="超时时间(秒)")
    
    args = parser.parse_args()
    
    # 解析 headers 和 body
    headers = json.loads(args.headers) if args.headers else {}
    body = json.loads(args.body) if args.body else None
    
    # 发送测试请求
    success = test_request(
        url=args.url,
        method=args.method,
        headers=headers,
        body=body,
        save=args.save,
        timeout=args.timeout
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
