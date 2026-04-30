"""百草山采集 API。"""

from datetime import datetime, timezone
import json
import time

from fastapi import APIRouter, Depends

from app.game.application.AntiCheatSystem import AntiCheatSystem
from app.game.application.Dependencies import GameContext, get_game_context, get_token_info, get_write_game_context
from app.core.logging.Logger import logger
from app.game.schemas.HerbSchema import (
    HerbPointsResponse,
    HerbStartRequest,
    HerbStartResponse,
    HerbReportRequest,
    HerbReportResponse,
    HerbStopRequest,
    HerbStopResponse,
)
from app.game.domain.herb.HerbGatherSystem import HerbGatherSystem
from app.game.domain.herb.HerbPointData import HerbPointData

router = APIRouter()

def _get_gather_spell_level(ctx: GameContext) -> int:
    if not ctx.spell_system:
        return 0
    spell_info = ctx.spell_system.player_spells.get("herb_gathering", {})
    if not spell_info.get("obtained", False):
        return 0
    return max(int(spell_info.get("level", 0)), 0)


def _get_gather_efficiency_bonus(ctx: GameContext) -> float:
    if not ctx.spell_system:
        return 0.0
    if not hasattr(ctx.spell_system, "get_herb_gather_efficiency_bonus"):
        return 0.0
    return max(float(ctx.spell_system.get_herb_gather_efficiency_bonus()), 0.0)


def _get_gather_success_rate_bonus(ctx: GameContext) -> float:
    if not ctx.spell_system:
        return 0.0
    if not hasattr(ctx.spell_system, "get_herb_gather_success_rate_bonus"):
        return 0.0
    return max(float(ctx.spell_system.get_herb_gather_success_rate_bonus()), 0.0)


def _effective_interval(base_interval: float, efficiency_bonus: float) -> float:
    return round(base_interval / (1.0 + efficiency_bonus), 2)

def _effective_success_rate(base_success_rate: float, success_rate_bonus: float) -> float:
    return round(max(0.0, min(base_success_rate + success_rate_bonus, 1.0)), 4)


def _build_points_for_player(ctx: GameContext) -> dict:
    raw_points = HerbPointData.get_all_points()
    gather_level = _get_gather_spell_level(ctx)
    efficiency_bonus = _get_gather_efficiency_bonus(ctx)
    success_rate_bonus = _get_gather_success_rate_bonus(ctx)
    points = {}
    for point_id, point in raw_points.items():
        if not isinstance(point, dict):
            continue
        point_copy = dict(point)
        base_interval = float(point_copy.get("report_interval_seconds", 0.0))
        base_success_rate = float(point_copy.get("success_rate", 0.0))
        effective_interval = _effective_interval(base_interval, efficiency_bonus)
        effective_success_rate = _effective_success_rate(base_success_rate, success_rate_bonus)
        point_copy["base_report_interval_seconds"] = base_interval
        point_copy["report_interval_seconds"] = effective_interval
        point_copy["effective_report_interval_seconds"] = effective_interval
        point_copy["base_success_rate"] = base_success_rate
        point_copy["success_rate"] = effective_success_rate
        point_copy["effective_success_rate"] = effective_success_rate
        point_copy["herb_gathering_level"] = gather_level
        point_copy["efficiency_bonus_rate"] = efficiency_bonus
        point_copy["success_rate_bonus"] = success_rate_bonus
        points[point_id] = point_copy
    return points


@router.get("/herb/points", response_model=HerbPointsResponse)
async def herb_points(
    ctx: GameContext = Depends(get_game_context),
    token_info: dict = Depends(get_token_info),
):
    start_time = time.time()
    logger.info(
        f"[IN] GET /game/herb/points - token: {token_info['token']} - "
        f"account_id: {token_info['account_id']} - token_version: {token_info['token_version']}"
    )
    response = HerbPointsResponse(
        success=True,
        operation_id="",
        timestamp=time.time(),
        reason_code="HERB_POINTS_SUCCEEDED",
        reason_data={
            "herb_gathering_level": _get_gather_spell_level(ctx),
            "efficiency_bonus_rate": _get_gather_efficiency_bonus(ctx),
            "success_rate_bonus": _get_gather_success_rate_bonus(ctx),
        },
        points_config=_build_points_for_player(ctx),
        current_state=ctx.herb_system.to_dict(),
    )
    logger.info(f"[OUT] GET /game/herb/points - {json.dumps(response.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response


@router.post("/herb/start", response_model=HerbStartResponse)
async def herb_start(
    request: HerbStartRequest,
    ctx: GameContext = Depends(get_write_game_context),
    token_info: dict = Depends(get_token_info),
):
    start_time = time.time()
    logger.info(
        f"[IN] POST /game/herb/start - {json.dumps(request.dict(), ensure_ascii=False)} - "
        f"token: {token_info['token']} - account_id: {token_info['account_id']} - token_version: {token_info['token_version']}"
    )

    if not HerbPointData.point_exists(request.point_id):
        response = HerbStartResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            reason_code="HERB_START_POINT_NOT_FOUND",
            reason_data={"point_id": request.point_id},
        )
        logger.info(f"[OUT] POST /game/herb/start - {json.dumps(response.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response

    if ctx.herb_system.is_gathering:
        response = HerbStartResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            reason_code="HERB_START_ALREADY_ACTIVE",
            reason_data={"point_id": ctx.herb_system.current_point_id},
        )
        logger.info(f"[OUT] POST /game/herb/start - {json.dumps(response.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response

    if ctx.player.is_cultivating:
        response = HerbStartResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            reason_code="HERB_START_BLOCKED_BY_CULTIVATION",
            reason_data={},
        )
        logger.info(f"[OUT] POST /game/herb/start - {json.dumps(response.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response

    if ctx.alchemy_system.is_alchemizing:
        response = HerbStartResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            reason_code="HERB_START_BLOCKED_BY_ALCHEMY",
            reason_data={},
        )
        logger.info(f"[OUT] POST /game/herb/start - {json.dumps(response.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response

    if ctx.lianli_system.is_battling:
        response = HerbStartResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            reason_code="HERB_START_BLOCKED_BY_LIANLI",
            reason_data={},
        )
        logger.info(f"[OUT] POST /game/herb/start - {json.dumps(response.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response

    ctx.herb_system.is_gathering = True
    ctx.herb_system.current_point_id = request.point_id
    ctx.herb_system.last_report_time = time.time()
    await AntiCheatSystem.reset_suspicious_operations(
        account_id=str(ctx.account.id),
        account_system=ctx.account_system,
        db_player_data=ctx.player_data,
    )
    ctx.db_data["herb_system"] = ctx.herb_system.to_dict()
    ctx.db_data["account_info"] = ctx.account_system.to_dict()
    ctx.player_data.data = ctx.db_data
    ctx.player_data.last_online_at = datetime.now(timezone.utc)
    await ctx.player_data.save()

    response = HerbStartResponse(
        success=True,
        operation_id=request.operation_id,
        timestamp=request.timestamp,
        reason_code="HERB_START_SUCCEEDED",
        reason_data={
            "point_id": request.point_id,
            "herb_gathering_level": _get_gather_spell_level(ctx),
            "efficiency_bonus_rate": _get_gather_efficiency_bonus(ctx),
            "success_rate_bonus": _get_gather_success_rate_bonus(ctx),
            "effective_interval_seconds": _effective_interval(
                float(HerbPointData.get_point(request.point_id).get("report_interval_seconds", 0.0)),
                _get_gather_efficiency_bonus(ctx),
            ),
            "effective_success_rate": _effective_success_rate(
                float(HerbPointData.get_point(request.point_id).get("success_rate", 0.0)),
                _get_gather_success_rate_bonus(ctx),
            ),
        },
    )
    logger.info(f"[OUT] POST /game/herb/start - {json.dumps(response.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response


@router.post("/herb/report", response_model=HerbReportResponse)
async def herb_report(
    request: HerbReportRequest,
    ctx: GameContext = Depends(get_write_game_context),
    token_info: dict = Depends(get_token_info),
):
    start_time = time.time()
    logger.info(
        f"[IN] POST /game/herb/report - {json.dumps(request.dict(), ensure_ascii=False)} - "
        f"token: {token_info['token']} - account_id: {token_info['account_id']} - token_version: {token_info['token_version']}"
    )

    if not ctx.herb_system.is_gathering:
        response = HerbReportResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            reason_code="HERB_REPORT_NOT_ACTIVE",
            reason_data={},
            point_id="",
            success_roll=False,
            drops_gained={},
        )
        logger.info(f"[OUT] POST /game/herb/report - {json.dumps(response.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response

    point_id = ctx.herb_system.current_point_id
    point = HerbPointData.get_point(point_id)
    if not point:
        response = HerbReportResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            reason_code="HERB_REPORT_POINT_NOT_FOUND",
            reason_data={"point_id": point_id},
            point_id=point_id,
            success_roll=False,
            drops_gained={},
        )
        logger.info(f"[OUT] POST /game/herb/report - {json.dumps(response.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response

    current_time = time.time()
    actual_interval = current_time - float(ctx.herb_system.last_report_time)
    efficiency_bonus = _get_gather_efficiency_bonus(ctx)
    success_rate_bonus = _get_gather_success_rate_bonus(ctx)
    expected_interval = _effective_interval(float(point.get("report_interval_seconds", 0.0)), efficiency_bonus)
    expected_success_rate = _effective_success_rate(float(point.get("success_rate", 0.0)), success_rate_bonus)
    gather_level = _get_gather_spell_level(ctx)
    min_allowed_interval = expected_interval * 0.9
    if actual_interval < min_allowed_interval:
        anti_cheat_result = await AntiCheatSystem.record_suspicious_operation(
            account_id=str(ctx.account.id),
            operation_type="herb_report",
            detail=(
                f"point={point_id}, actual={actual_interval:.2f}, "
                f"min_allowed={min_allowed_interval:.2f}"
            ),
            account_system=ctx.account_system,
            db_player_data=ctx.player_data,
            db_account=ctx.account,
        )
        response = HerbReportResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            reason_code="HERB_REPORT_TIME_INVALID",
            reason_data={
                "point_id": point_id,
                "herb_gathering_level": gather_level,
                "efficiency_bonus_rate": efficiency_bonus,
                "success_rate_bonus": success_rate_bonus,
                "effective_interval_seconds": expected_interval,
                "effective_success_rate": expected_success_rate,
                "actual_interval": round(actual_interval, 2),
                "min_allowed_interval": round(min_allowed_interval, 2),
                "invalid_report_count": anti_cheat_result.get("invalid_count", 0),
                "kicked_out": bool(anti_cheat_result.get("kicked_out", False)),
                "kick_threshold": anti_cheat_result.get("threshold", 10),
            },
            point_id=point_id,
            success_roll=False,
            drops_gained={},
        )
        logger.info(f"[OUT] POST /game/herb/report - {json.dumps(response.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response

    settle_result = HerbGatherSystem.settle_once(point_id, success_rate_bonus=success_rate_bonus)
    drops_gained = settle_result.get("drops_gained", {})
    applied_drops = {}
    for item_id, amount in drops_gained.items():
        added = ctx.inventory_system.add_item(item_id, int(amount))
        if added > 0:
            applied_drops[item_id] = int(added)

    if ctx.spell_system:
        ctx.spell_system.add_spell_use_count("herb_gathering")
    ctx.task_system.add_progress("daily_herb_count", 1)
    ctx.task_system.add_progress("newbie_herb_gather_10", 1)
    ctx.task_system.add_progress("newbie_herb_gather_20", 1)

    ctx.herb_system.last_report_time = current_time
    await AntiCheatSystem.reset_suspicious_operations(
        account_id=str(ctx.account.id),
        account_system=ctx.account_system,
        db_player_data=ctx.player_data,
    )
    ctx.db_data["inventory"] = ctx.inventory_system.to_dict()
    ctx.db_data["herb_system"] = ctx.herb_system.to_dict()
    ctx.db_data["spell_system"] = ctx.spell_system.to_dict()
    ctx.db_data["task_system"] = ctx.task_system.to_dict()
    ctx.db_data["account_info"] = ctx.account_system.to_dict()
    ctx.player_data.data = ctx.db_data
    ctx.player_data.last_online_at = datetime.now(timezone.utc)
    await ctx.player_data.save()

    response = HerbReportResponse(
        success=True,
        operation_id=request.operation_id,
        timestamp=request.timestamp,
        reason_code="HERB_REPORT_SUCCEEDED",
        reason_data={
            "point_id": point_id,
            "herb_gathering_level": gather_level,
            "efficiency_bonus_rate": efficiency_bonus,
            "success_rate_bonus": success_rate_bonus,
            "effective_interval_seconds": expected_interval,
            "effective_success_rate": expected_success_rate,
        },
        point_id=point_id,
        success_roll=bool(settle_result.get("success_roll", False)),
        drops_gained=applied_drops,
    )
    logger.info(f"[OUT] POST /game/herb/report - {json.dumps(response.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response


@router.post("/herb/stop", response_model=HerbStopResponse)
async def herb_stop(
    request: HerbStopRequest,
    ctx: GameContext = Depends(get_write_game_context),
    token_info: dict = Depends(get_token_info),
):
    start_time = time.time()
    logger.info(
        f"[IN] POST /game/herb/stop - {json.dumps(request.dict(), ensure_ascii=False)} - "
        f"token: {token_info['token']} - account_id: {token_info['account_id']} - token_version: {token_info['token_version']}"
    )

    if not ctx.herb_system.is_gathering:
        response = HerbStopResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            reason_code="HERB_STOP_NOT_ACTIVE",
            reason_data={},
        )
        logger.info(f"[OUT] POST /game/herb/stop - {json.dumps(response.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response

    previous_point_id = ctx.herb_system.current_point_id
    ctx.herb_system.reset_gather_state()
    ctx.db_data["herb_system"] = ctx.herb_system.to_dict()
    ctx.player_data.data = ctx.db_data
    ctx.player_data.last_online_at = datetime.now(timezone.utc)
    await ctx.player_data.save()

    response = HerbStopResponse(
        success=True,
        operation_id=request.operation_id,
        timestamp=request.timestamp,
        reason_code="HERB_STOP_SUCCEEDED",
        reason_data={"point_id": previous_point_id},
    )
    logger.info(f"[OUT] POST /game/herb/stop - {json.dumps(response.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response
