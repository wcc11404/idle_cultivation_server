from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=4, max_length=20, description="用户名")
    password: str = Field(..., min_length=6, max_length=20, description="密码")


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class AccountInfo(BaseModel):
    """账号信息"""
    id: UUID
    username: str
    server_id: str

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """登录响应"""
    success: bool
    token: str
    expires_in: int
    account_info: AccountInfo
    data: dict
    offline_reward: Optional[dict] = None
    offline_seconds: int = 0


class RefreshResponse(BaseModel):
    """Token续期响应"""
    success: bool
    token: str
    expires_in: int


class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = False
    error_code: int
    message: str