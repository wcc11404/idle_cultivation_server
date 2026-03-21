from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    # 服务器配置
    APP_NAME: str = "Idle Cultivation Server"
    APP_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # 数据库配置
    DATABASE_URL: str = "postgres://hsams:hsams@localhost:5432/idle_cultivation_game"
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7
    
    # 服务端配置
    SERVER_HOST: str = "127.0.0.1"
    SERVER_PORT: int = 8444
    
    class Config:
        env_file = ".env"


# 创建全局配置实例
settings = Settings()