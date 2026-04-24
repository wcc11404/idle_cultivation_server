import asyncio
import sys
import os
import json
from datetime import datetime, timezone, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tortoise import Tortoise
from app.db.Models import Account, PlayerData
from app.core.ServerConfig import settings

# 东八区时区
CST = timezone(timedelta(hours=8))

async def get_user_info(username):
    # 初始化数据库连接
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={"models": ["app.db.Models"]}
    )
    await Tortoise.generate_schemas()
    
    try:
        # 查询账号
        account = await Account.get_or_none(username=username)
        if not account:
            print(f"用户 {username} 不存在")
            return
        
        # 查询游戏数据
        player_data = await PlayerData.get_or_none(account_id=account.id)
        
        # 打印账号信息
        print("=== 账号信息 ===")
        print(f"账号ID: {account.id}")
        print(f"用户名: {account.username}")
        print(f"密码哈希: {account.password_hash}")
        print(f"Token版本: {account.token_version}")
        print(f"服务器ID: {account.server_id}")
        print(f"是否封禁: {'是' if account.is_banned else '否'}")
        print(f"创建时间: {account.created_at.astimezone(CST).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"更新时间: {account.updated_at.astimezone(CST).strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 打印游戏数据
        print("\n=== 游戏数据 ===")
        if player_data:
            print(f"最后更新时间: {player_data.updated_at.astimezone(CST).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"最后在线时间: {player_data.last_online_at.astimezone(CST).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"游戏版本: {player_data.game_version}")
            print("\n详细游戏数据:")
            print(json.dumps(player_data.data, indent=2, ensure_ascii=False))
        else:
            print("该用户尚未创建游戏数据")
            
    finally:
        # 关闭数据库连接
        await Tortoise.close_connections()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("使用方法: python util/get_user_info.py <用户名>")
        sys.exit(1)
    
    username = sys.argv[1]
    asyncio.run(get_user_info(username))
