from pydantic import BaseModel, Field
from typing import Optional


class BaseRequest(BaseModel):
    """基础请求模型（需要认证的接口）"""
    operation_id: str = Field(..., description="客户端生成的UUID，用于追踪请求")
    timestamp: float = Field(..., description="客户端触发操作的时间戳（秒）")


class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool
    operation_id: Optional[str] = None
    timestamp: Optional[float] = None
    reason_code: Optional[str] = None
    reason_data: dict = Field(default_factory=dict)
