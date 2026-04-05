"""
防作弊系统

统一处理可疑操作和作弊检测
"""

from typing import Dict, Any, Tuple
from app.core.Logger import logger


class AntiCheatSystem:
    """
    防作弊系统 - 负责检测和处理可疑操作
    """
    
    @staticmethod
    def validate_cultivation_report(
        current_time: float,
        last_report_time: float,
        reported_count: int,
        tolerance: float = 0.1
    ) -> Tuple[bool, str]:
        """
        验证修炼上报是否合理
        
        规则：
        - 如果上报次数 < 实际时间差：合理（不管小多少）
        - 如果上报次数 > 实际时间差 * (1 + tolerance)：不合理（超过容差）
        
        Args:
            current_time: 当前时间戳（秒）
            last_report_time: 上次上报时间戳（秒）
            reported_count: 本次上报的修炼次数
            tolerance: 容差比例（默认 0.1 即 10%）
        
        Returns:
            (是否合理, 原因说明)
        """
        if last_report_time == 0:
            return True, "首次上报"
        
        actual_interval = current_time - last_report_time
        max_acceptable = actual_interval * (1 + tolerance)
        
        if reported_count > max_acceptable:
            reason = f"上报次数异常：上报{reported_count}次，实际间隔{actual_interval:.1f}秒，最大允许{max_acceptable:.1f}次"
            return False, reason
        
        return True, "验证通过"
    
    @staticmethod
    async def record_suspicious_operation(
        account_id: str,
        operation_type: str,
        detail: str,
        account_system: 'AccountSystem',
        db_player_data
    ) -> int:
        """
        记录可疑操作
        
        Args:
            account_id: 账号ID
            operation_type: 操作类型（如 "cultivation_report"）
            detail: 详细信息
            account_system: 账号系统实例
            db_player_data: 数据库玩家数据实例
        
        Returns:
            当前可疑操作次数
        """
        count = account_system.increment_suspicious_operations()
        
        logger.warning(
            f"[ANTI_CHEAT] 可疑操作 - account_id: {account_id} - "
            f"type: {operation_type} - detail: {detail} - "
            f"count: {count}"
        )
        
        db_player_data.data["account_info"]["suspicious_operations_count"] = count
        await db_player_data.save()
        
        return count
    
    @staticmethod
    async def reset_suspicious_operations(
        account_id: str,
        account_system: 'AccountSystem',
        db_player_data
    ) -> None:
        """
        重置可疑操作次数
        
        Args:
            account_id: 账号ID
            account_system: 账号系统实例
            db_player_data: 数据库玩家数据实例
        """
        account_system.reset_suspicious_operations()
        
        logger.info(f"[ANTI_CHEAT] 重置可疑操作次数 - account_id: {account_id}")
        
        db_player_data.data["account_info"]["suspicious_operations_count"] = 0
        await db_player_data.save()
