#!/usr/bin/env python3
"""
注册测试账号脚本
用于创建测试账号 wcc_test
"""

import requests
import json

BASE_URL = "http://localhost:8444/api"

# 注册测试账号
def register_test_account():
    url = f"{BASE_URL}/auth/register"
    payload = {
        "username": "wcc_test",
        "password": "wcc_test"
    }
    
    try:
        response = requests.post(url, json=payload)
        result = response.json()
        print(f"注册结果: {json.dumps(result, ensure_ascii=False)}")
        
        if result.get("success"):
            print("测试账号注册成功！")
        else:
            print(f"注册失败: {result.get('message')}")
            
    except Exception as e:
        print(f"注册失败: {str(e)}")

if __name__ == "__main__":
    print("开始注册测试账号...")
    register_test_account()
