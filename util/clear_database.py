#!/usr/bin/env python3
"""
清空数据库脚本

该脚本用于清空Idle Cultivation游戏的数据库表数据
"""

import asyncio
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tortoise import Tortoise
from app.core.config import settings

async def init_db():
    """初始化数据库连接"""
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={"models": ["app.db.models"]},
        use_tz=True,
        timezone="Asia/Shanghai"
    )

async def clear_database():
    """清空数据库所有表的数据"""
    try:
        # 初始化数据库连接
        await init_db()
        
        print("正在清空数据库...")
        
        # 获取所有模型
        from app.db.models import Account, PlayerData
        
        # 清空每个模型的数据（先删除 player_data，再删除 account，避免外键约束错误）
        models = [PlayerData, Account]
        for model in models:
            print(f"清空表: {model.__name__}")
            await model.all().delete()
        
        print("\n数据库清空成功！")
        
    except Exception as e:
        print(f"数据库操作错误: {e}")
        sys.exit(1)
    finally:
        await Tortoise.close_connections()

async def drop_and_recreate_tables():
    """删除并重新创建表结构"""
    try:
        # 初始化数据库连接
        await Tortoise.init(
            db_url=settings.DATABASE_URL,
            modules={"models": ["app.db.models"]}
        )
        
        print("正在删除并重新创建表结构...")
        
        # 删除所有表
        await Tortoise._drop_databases()
        print("所有表已删除")
        
        # 重新创建表结构
        print("\n重新创建表结构...")
        await Tortoise.generate_schemas()
        
        print("\n表结构重新创建成功！")
        
    except Exception as e:
        print(f"数据库操作错误: {e}")
        sys.exit(1)
    finally:
        await Tortoise.close_connections()

def main():
    """主函数"""
    print("Idle Cultivation 数据库管理工具")
    print("==============================")
    print("1. 清空数据库所有表的数据")
    print("2. 删除并重新创建表结构")
    print("3. 退出")
    
    choice = input("请选择操作 (1-3): ")
    
    if choice == "1":
        confirm = input("确定要清空所有数据吗？(y/n): ")
        if confirm.lower() == "y":
            asyncio.run(clear_database())
    elif choice == "2":
        confirm = input("确定要删除并重新创建表结构吗？(y/n): ")
        if confirm.lower() == "y":
            asyncio.run(drop_and_recreate_tables())
    elif choice == "3":
        print("退出程序")
    else:
        print("无效的选择")

if __name__ == "__main__":
    main()
