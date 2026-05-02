from tortoise import Tortoise
from app.core.config.ServerConfig import settings


async def init_db():
    """初始化数据库连接"""
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={"models": ["app.core.db.Models", "app.ops.models"]},
        use_tz=True,
        timezone="Asia/Shanghai"
    )
    await Tortoise.generate_schemas(safe=True)


async def close_db():
    """关闭数据库连接"""
    await Tortoise.close_connections()
