#!/usr/bin/env python3
"""
删除测试账号脚本
用于删除测试账号 wcc_test
"""

import asyncio
import sys
import os

# 添加项目根目录到 Python 导入路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tortoise import Tortoise
from app.core.ServerConfig import settings
from app.db.Models import Account, PlayerData

async def delete_test_account():
    """删除测试账号"""
    try:
        # 初始化数据库连接
        await Tortoise.init(
            db_url=settings.DATABASE_URL,
            modules={"models": ["app.db.Models"]}
        )
        
        # 查找测试账号
        account = await Account.get_or_none(username="wcc_test")
        if account:
            # 删除关联的玩家数据
            await PlayerData.filter(account_id=account.id).delete()
            # 删除账号
            await account.delete()
            print("测试账号删除成功！")
        else:
            print("测试账号不存在")
            
    except Exception as e:
        print(f"删除失败: {str(e)}")
    finally:
        # 关闭数据库连接
        await Tortoise.close_connections()

if __name__ == "__main__":
    print("开始删除测试账号...")
    asyncio.run(delete_test_account())
