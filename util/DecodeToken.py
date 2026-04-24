import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.Security import decode_token

def main(token):
    """解析token并提取account_id和token_version"""
    payload = decode_token(token)
    
    if not payload:
        print("无效的token")
        return
    
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    exp = payload.get("exp")
    
    print("=== Token解析结果 ===")
    print(f"账号ID: {account_id}")
    print(f"Token版本: {token_version}")
    if exp:
        from datetime import datetime, timezone
        exp_time = datetime.fromtimestamp(exp, timezone.utc)
        # 转换为东八区时间
        from datetime import timedelta
        cst = timezone(timedelta(hours=8))
        exp_time_cst = exp_time.astimezone(cst)
        print(f"过期时间: {exp_time_cst.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("使用方法: python util/decode_token.py <token>")
        sys.exit(1)
    
    token = sys.argv[1]
    main(token)
