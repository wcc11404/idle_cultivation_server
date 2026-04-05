"""
API响应构建辅助函数

提供统一的响应构建函数，减少API中的重复代码
"""

from typing import Any, Dict, List, Optional
from app.schemas.game import (
    LianliBattleResponse, LianliSettleResponse,
    CultivationStartResponse, CultivationReportResponse, CultivationStopResponse,
    AlchemyStartResponse, AlchemyReportResponse, AlchemyStopResponse
)


def build_lianli_battle_failure_response(
    operation_id: str,
    timestamp: float,
    message: str
) -> LianliBattleResponse:
    """构建历练战斗失败响应"""
    return LianliBattleResponse(
        success=False,
        operation_id=operation_id,
        timestamp=timestamp,
        battle_timeline=[],
        total_time=0.0,
        player_health_before=0.0,
        player_health_after=0.0,
        enemy_health_after=0.0,
        enemy_data={},
        victory=False,
        loot=[],
        message=message
    )


def build_lianli_battle_success_response(
    operation_id: str,
    timestamp: float,
    result: Dict[str, Any]
) -> LianliBattleResponse:
    """构建历练战斗成功响应"""
    return LianliBattleResponse(
        success=result.get("success", True),
        operation_id=operation_id,
        timestamp=timestamp,
        battle_timeline=result.get("battle_timeline", []),
        total_time=result.get("total_time", 0.0),
        player_health_before=result.get("player_health_before", 0.0),
        player_health_after=result.get("player_health_after", 0.0),
        enemy_health_after=result.get("enemy_health_after", 0.0),
        enemy_data=result.get("enemy_data", {}),
        victory=result.get("victory", False),
        loot=result.get("loot", []),
        message=result.get("reason", "战斗模拟完成")
    )


def build_lianli_settle_response(
    operation_id: str,
    timestamp: float,
    result: Dict[str, Any]
) -> LianliSettleResponse:
    """构建历练战斗结算响应"""
    return LianliSettleResponse(
        success=result["success"],
        operation_id=operation_id,
        timestamp=timestamp,
        settled_index=result.get("settled_index", 0),
        total_index=result.get("total_index", 0),
        player_health_after=result.get("player_health_after", 0.0),
        loot_gained=result.get("loot_gained", []),
        exp_gained=result.get("exp_gained", 0),
        message=result.get("reason", result.get("message", ""))
    )


def build_cultivation_start_failure_response(
    operation_id: str,
    timestamp: float,
    message: str
) -> CultivationStartResponse:
    """构建开始修炼失败响应"""
    return CultivationStartResponse(
        success=False,
        operation_id=operation_id,
        timestamp=timestamp,
        message=message,
        spirit_energy_gained=0.0,
        duration=0
    )


def build_cultivation_report_response(
    operation_id: str,
    timestamp: float,
    result: Dict[str, Any]
) -> CultivationReportResponse:
    """构建修炼汇报响应"""
    return CultivationReportResponse(
        success=result["success"],
        operation_id=operation_id,
        timestamp=timestamp,
        message=result.get("reason", result.get("message", "")),
        spirit_energy_gained=result.get("spirit_energy_gained", 0.0),
        duration=result.get("duration", 0)
    )


def build_cultivation_stop_response(
    operation_id: str,
    timestamp: float,
    result: Dict[str, Any]
) -> CultivationStopResponse:
    """构建停止修炼响应"""
    return CultivationStopResponse(
        success=result["success"],
        operation_id=operation_id,
        timestamp=timestamp,
        message=result.get("reason", result.get("message", "")),
        spirit_energy_gained=result.get("spirit_energy_gained", 0.0),
        duration=result.get("duration", 0)
    )


def build_alchemy_start_failure_response(
    operation_id: str,
    timestamp: float,
    message: str
) -> AlchemyStartResponse:
    """构建开始炼丹失败响应"""
    return AlchemyStartResponse(
        success=False,
        operation_id=operation_id,
        timestamp=timestamp,
        message=message,
        pills_produced=0,
        duration=0
    )


def build_alchemy_report_response(
    operation_id: str,
    timestamp: float,
    result: Dict[str, Any]
) -> AlchemyReportResponse:
    """构建炼丹汇报响应"""
    return AlchemyReportResponse(
        success=result["success"],
        operation_id=operation_id,
        timestamp=timestamp,
        message=result.get("reason", result.get("message", "")),
        pills_produced=result.get("pills_produced", 0),
        duration=result.get("duration", 0)
    )


def build_alchemy_stop_response(
    operation_id: str,
    timestamp: float,
    result: Dict[str, Any]
) -> AlchemyStopResponse:
    """构建停止炼丹响应"""
    return AlchemyStopResponse(
        success=result["success"],
        operation_id=operation_id,
        timestamp=timestamp,
        message=result.get("reason", result.get("message", "")),
        pills_produced=result.get("pills_produced", 0),
        duration=result.get("duration", 0)
    )
