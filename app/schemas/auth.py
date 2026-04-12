from pydantic import BaseModel, Field
from app.schemas.base import BaseRequest, BaseResponse


class RegisterRequest(BaseRequest):
    """注册请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class LoginRequest(BaseRequest):
    """登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class AccountInfo(BaseModel):
    """账号信息"""
    id: str
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


class RegisterResponse(BaseResponse):
    """注册响应"""
    token: str = ""


class RefreshResponse(BaseResponse):
    """Token续期响应"""
    token: str
    expires_in: int


class ChangePasswordRequest(BaseRequest):
    """修改密码请求"""
    username: str = Field(..., description="用户名")
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., description="新密码")


class ChangeNicknameRequest(BaseRequest):
    """修改昵称请求"""
    nickname: str = Field(..., description="昵称")


class ChangeAvatarRequest(BaseRequest):
    """修改头像请求"""
    avatar_id: str = Field(..., description="头像ID")


class ChangePasswordResponse(BaseResponse):
    """修改密码响应"""
    pass


class ChangeNicknameResponse(BaseResponse):
    """修改昵称响应"""
    nickname: str


class ChangeAvatarResponse(BaseResponse):
    """修改头像响应"""
    avatar_id: str


class LogoutResponse(BaseResponse):
    """登出响应"""
    pass
