from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import platform


class Settings(BaseSettings):
    """应用配置"""
    model_config = SettingsConfigDict(env_file=".env")

    # 服务器配置
    APP_NAME: str = "Idle Cultivation Server"
    APP_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # 数据库配置
    @property
    def DATABASE_URL(self) -> str:
        # 根据操作系统使用不同的数据库用户
        if platform.system() == "Darwin":  # macOS
            return "postgres://hsams:hsams@localhost:5432/idle_cultivation_game"
        else:  # Linux
            return "postgres://postgres:postgres@localhost:5432/idle_cultivation_game"
    
    # JWT配置
    SECRET_KEY: str = "e68891f1323f5579e79adf3f9e1852336e22e5761b12e9f6a2fd6bf3eca827b5"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7
    
    # 服务端配置
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8444
    
    # 每日重置时间（小时）
    DAILY_RESET_HOUR: int = 4
    
# 创建全局配置实例
settings = Settings()
