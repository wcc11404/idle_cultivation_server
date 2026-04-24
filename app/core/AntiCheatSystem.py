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
    MAX_CONSECUTIVE_INVALID_REPORTS: int = 10
    
    @staticmethod
    def validate_cultivation_report(
        current_time: float,
        last_report_time: float,
        reported_elapsed_seconds: float,
        tolerance: float = 0.1
    ) -> Tuple[bool, str]:
        """
        验证修炼上报是否合理
        
        规则：
        - 如果上报秒数 <= 实际时间差 * (1 + tolerance)：合理
        - 如果上报秒数 > 实际时间差 * (1 + tolerance)：不合理（超过容差）
        
        Args:
            current_time: 当前时间戳（秒）
            last_report_time: 上次上报时间戳（秒）
            reported_elapsed_seconds: 本次上报的修炼累计秒数
            tolerance: 容差比例（默认 0.1 即 10%）
        
        Returns:
            (是否合理, 原因说明)
        """
        if last_report_time == 0:
            return True, "首次上报"
        
        actual_interval = current_time - last_report_time
        max_acceptable = actual_interval * (1 + tolerance)
        
        if reported_elapsed_seconds > max_acceptable:
            reason = f"上报秒数异常：上报{reported_elapsed_seconds:.2f}秒，实际间隔{actual_interval:.2f}秒，最大允许{max_acceptable:.2f}秒"
            return False, reason
        
        return True, "验证通过"
    
    @staticmethod
    async def record_suspicious_operation(
        account_id: str,
        operation_type: str,
        detail: str,
        account_system: 'AccountSystem',
        db_player_data,
        db_account
    ) -> Dict[str, Any]:
        """
        记录可疑操作
        
        Args:
            account_id: 账号ID
            operation_type: 操作类型（如 "cultivation_report"）
            detail: 详细信息
            account_system: 账号系统实例
            db_player_data: 数据库玩家数据实例
        
        Returns:
            dict: {
                "invalid_count": int,  # 本次累计后的非法次数（触发踢下线时为触发阈值前的计数）
                "kicked_out": bool,    # 是否触发强制下线
                "threshold": int
            }
        """
        before_count = int(account_system.suspicious_operations_count)
        before_type = str(account_system.suspicious_operation_type)
        before_token_version = int(db_account.token_version)
        invalid_count = account_system.increment_suspicious_operations(operation_type)
        kicked_out = False

        logger.warning(
            f"[ANTI_CHEAT] 可疑操作 - account_id: {account_id} - "
            f"type: {operation_type} - detail: {detail} - "
            f"before_count: {before_count} - before_type: {before_type} - "
            f"after_count: {invalid_count} - threshold: {AntiCheatSystem.MAX_CONSECUTIVE_INVALID_REPORTS}"
        )

        if invalid_count >= AntiCheatSystem.MAX_CONSECUTIVE_INVALID_REPORTS:
            db_account.token_version += 1
            await db_account.save(update_fields=["token_version"])
            kicked_out = True
            logger.warning(
                f"[ANTI_CHEAT] 连续非法上报达到阈值，执行踢下线 - account_id: {account_id} "
                f"- old_token_version: {before_token_version} - new_token_version: {db_account.token_version}"
            )
            # 触发踢下线后重置计数，避免重新登录后立即再次触发
            account_system.reset_suspicious_operations()
            db_player_data.data["account_info"] = account_system.to_dict()
        else:
            db_player_data.data["account_info"] = account_system.to_dict()

        await db_player_data.save()

        return {
            "invalid_count": invalid_count,
            "kicked_out": kicked_out,
            "threshold": AntiCheatSystem.MAX_CONSECUTIVE_INVALID_REPORTS,
        }
    
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
        if account_system.suspicious_operations_count <= 0:
            return

        old_count = int(account_system.suspicious_operations_count)
        old_type = str(account_system.suspicious_operation_type)
        account_system.reset_suspicious_operations()

        logger.info(
            f"[ANTI_CHEAT] 重置可疑操作次数 - account_id: {account_id} "
            f"- old_count: {old_count} - old_type: {old_type}"
        )
        
        db_player_data.data["account_info"] = account_system.to_dict()
        await db_player_data.save()
