"""
账号系统模块

管理玩家的账号信息
"""

from typing import Optional
from datetime import datetime


class AccountSystem:
    """
    账号系统类 - 负责管理玩家的账号信息
    
    存储：
    - 昵称、头像、称号
    - VIP 状态
    - 可疑操作次数
    """
    
    def __init__(self):
        self.nickname: str = ""
        self.avatar_id: str = "abstract"
        self.title_id: str = ""
        self.is_vip: bool = False
        self.vip_expire_time: Optional[datetime] = None
        self.suspicious_operations_count: int = 0
    
    def set_nickname(self, nickname: str) -> bool:
        """
        设置昵称
        
        Args:
            nickname: 新昵称
        
        Returns:
            是否设置成功
        """
        if not nickname or len(nickname) > 20:
            return False
        
        self.nickname = nickname
        return True
    
    def set_avatar(self, avatar_id: str) -> bool:
        """
        设置头像
        
        Args:
            avatar_id: 头像ID
        
        Returns:
            是否设置成功
        """
        if not avatar_id:
            return False
        
        self.avatar_id = avatar_id
        return True
    
    def set_title(self, title_id: str) -> bool:
        """
        设置称号
        
        Args:
            title_id: 称号ID
        
        Returns:
            是否设置成功
        """
        self.title_id = title_id
        return True
    
    def activate_vip(self, duration_days: int) -> None:
        """
        激活 VIP
        
        Args:
            duration_days: VIP 时长（天）
        """
        from datetime import timedelta
        
        if self.vip_expire_time and self.vip_expire_time > datetime.now():
            self.vip_expire_time += timedelta(days=duration_days)
        else:
            self.vip_expire_time = datetime.now() + timedelta(days=duration_days)
        
        self.is_vip = True
    
    def check_vip_status(self) -> bool:
        """
        检查 VIP 状态
        
        Returns:
            是否是 VIP
        """
        if self.vip_expire_time and self.vip_expire_time > datetime.now():
            self.is_vip = True
            return True
        
        self.is_vip = False
        return False
    
    def increment_suspicious_operations(self) -> int:
        """
        增加可疑操作次数
        
        Returns:
            当前可疑操作次数
        """
        self.suspicious_operations_count += 1
        return self.suspicious_operations_count
    
    def reset_suspicious_operations(self) -> None:
        """重置可疑操作次数"""
        self.suspicious_operations_count = 0
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "nickname": self.nickname,
            "avatar_id": self.avatar_id,
            "title_id": self.title_id,
            "is_vip": self.is_vip,
            "vip_expire_time": self.vip_expire_time.isoformat() if self.vip_expire_time else None,
            "suspicious_operations_count": self.suspicious_operations_count
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AccountSystem':
        """从字典创建"""
        instance = cls()
        instance.nickname = data.get("nickname", "")
        instance.avatar_id = data.get("avatar_id", "abstract")
        instance.title_id = data.get("title_id", "")
        instance.is_vip = data.get("is_vip", False)
        
        vip_expire_time_str = data.get("vip_expire_time")
        if vip_expire_time_str:
            try:
                instance.vip_expire_time = datetime.fromisoformat(vip_expire_time_str)
            except (ValueError, TypeError):
                instance.vip_expire_time = None
        
        instance.suspicious_operations_count = data.get("suspicious_operations_count", 0)
        
        return instance
    
    @classmethod
    def create_with_nickname(cls, nickname: str) -> 'AccountSystem':
        """
        通过昵称创建账号系统实例
        
        Args:
            nickname: 昵称
        
        Returns:
            AccountSystem 实例
        """
        instance = cls()
        instance.nickname = nickname
        return instance
