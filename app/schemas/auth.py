from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from app.schemas.base import BaseRequest, BaseResponse


class RegisterRequest(BaseRequest):
    """注册请求"""
    username: str = Field(..., min_length=4, max_length=20, description="用户名")
    password: str = Field(..., min_length=6, max_length=20, description="密码")


class LoginRequest(BaseRequest):
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


class LoginResponse(BaseResponse):
    """登录响应"""
    token: str
    expires_in: int
    account_info: AccountInfo
    data: dict
    offline_reward: Optional[dict] = None
    offline_seconds: int = 0


class RefreshResponse(BaseModel):
    """Token续期响应"""
    success: bool = True
    token: str
    expires_in: int


class ErrorResponse(BaseResponse):
    """错误响应"""
    error_code: int
    message: str


class ChangePasswordRequest(BaseRequest):
    """修改密码请求"""
    username: str = Field(..., description="用户名")
    old_password: str = Field(..., min_length=6, max_length=20, description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=20, description="新密码")


class ChangeNicknameRequest(BaseRequest):
    """修改昵称请求"""
    nickname: str = Field(..., min_length=4, max_length=10, description="昵称")


class ChangeAvatarRequest(BaseRequest):
    """修改头像请求"""
    avatar_id: str = Field(..., description="头像ID")


class ChangePasswordResponse(BaseResponse):
    """修改密码响应"""
    message: str


class ChangeNicknameResponse(BaseResponse):
    """修改昵称响应"""
    nickname: str
    message: str


class ChangeAvatarResponse(BaseResponse):
    """修改头像响应"""
    avatar_id: str
    message: str