#!/usr/bin/env python3
"""
注册角色脚本

提供用户名和密码，调用API注册角色

使用方法:
    python register_user.py <username> <password> [url]
    
示例:
    python register_user.py testuser testpass
    python register_user.py testuser testpass http://localhost:8000
"""

import requests
import json
import sys


def register_user(username: str, password: str, base_url: str = "http://localhost:8444"):
    """
    注册用户
    
    Args:
        username: 用户名
        password: 密码
        base_url: API基础URL
    
    Returns:
        注册结果
    """
    url = f"{base_url}/api/auth/register"
    data = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        result = response.json()
        return result
    except requests.RequestException as e:
        return {
            "success": False,
            "error_code": 500,
            "message": f"请求失败: {str(e)}"
        }


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("使用方法: python register_user.py <username> <password> [url]")
        print("示例: python register_user.py testuser testpass")
        print("示例: python register_user.py testuser testpass http://localhost:8444")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    base_url = sys.argv[3] if len(sys.argv) > 3 else "http://localhost:8444"
    
    print(f"正在注册用户: {username}")
    result = register_user(username, password, base_url)
    
    print("注册结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result.get("success"):
        print(f"\n注册成功！账号ID: {result.get('account_id')}")
        print(f"Token: {result.get('token')}")
    else:
        print(f"\n注册失败: {result.get('message')}")
