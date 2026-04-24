"""
历练相关 API

包含开始历练、执行战斗、结束历练等功能
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from app.schemas.Game import (
    LianliBattleRequest, LianliBattleResponse,
    LianliSettleRequest, LianliSettleResponse,
    DungeonInfoQueryResponse, TowerHighestFloorResponse
)
from app.db.Models import PlayerData as DBPlayerData
from app.core.Security import get_current_user, decode_token, security
from app.core.Dependencies import get_game_context, get_write_game_context, get_token_info, GameContext
from app.core.Logger import logger
from app.core.AntiCheatSystem import AntiCheatSystem
from app.modules import (
    PlayerSystem, LianliSystem, SpellSystem, InventorySystem, AlchemySystem, AccountSystem
)
from datetime import datetime, timezone
import time
import json

router = APIRouter()


@router.post("/lianli/simulate", response_model=LianliBattleResponse)
async def simulate_battle(
    request: LianliBattleRequest,
    ctx: GameContext = Depends(get_write_game_context),
    token_info: dict = Depends(get_token_info)
):
    """历练战斗模拟"""
    start_time = time.time()
    logger.info(f"[IN] POST /game/lianli/battle - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token_info['token']} - account_id: {token_info['account_id']} - token_version: {token_info['token_version']}")
    
    if ctx.player.is_cultivating:
        response_data = LianliBattleResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            reason_code="LIANLI_SIMULATE_BLOCKED_BY_CULTIVATION",
            reason_data={},
            battle_timeline=[],
            total_time=0.0,
            player_health_before=0.0,
            player_health_after=0.0,
            enemy_health_after=0.0,
            enemy_data={},
            victory=False,
            loot=[]
        )
        logger.info(f"[OUT] POST /game/lianli/battle - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    if ctx.alchemy_system.is_alchemizing:
        response_data = LianliBattleResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            reason_code="LIANLI_SIMULATE_BLOCKED_BY_ALCHEMY",
            reason_data={},
            battle_timeline=[],
            total_time=0.0,
            player_health_before=0.0,
            player_health_after=0.0,
            enemy_health_after=0.0,
            enemy_data={},
            victory=False,
            loot=[]
        )
        logger.info(f"[OUT] POST /game/lianli/battle - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data

    if ctx.herb_system.is_gathering:
        response_data = LianliBattleResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            reason_code="LIANLI_SIMULATE_BLOCKED_BY_HERB_GATHERING",
            reason_data={},
            battle_timeline=[],
            total_time=0.0,
            player_health_before=0.0,
            player_health_after=0.0,
            enemy_health_after=0.0,
            enemy_data={},
            victory=False,
            loot=[]
        )
        logger.info(f"[OUT] POST /game/lianli/battle - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    result = ctx.lianli_system.start_battle_simulation(
        request.area_id, ctx.player, ctx.spell_system
    )
    
    if result["success"]:
        await AntiCheatSystem.reset_suspicious_operations(
            account_id=str(ctx.account.id),
            account_system=ctx.account_system,
            db_player_data=ctx.player_data
        )
        ctx.db_data["account_info"] = ctx.account_system.to_dict()
        ctx.db_data["lianli_system"] = ctx.lianli_system.to_dict()
        ctx.player_data.data = ctx.db_data
        ctx.player_data.last_online_at = datetime.now(timezone.utc)
        await ctx.player_data.save()
        
        logger.info(f"[GAME] 战斗模拟成功 - account_id: {ctx.account.id} - area_id: {request.area_id}")
    
    response_data = LianliBattleResponse(
        success=result["success"],
        operation_id=request.operation_id,
        timestamp=request.timestamp,
        reason_code=result.get("reason_code", ""),
        reason_data=result.get("reason_data", {}),
        battle_timeline=result.get("battle_timeline", []),
        total_time=result.get("total_time", 0.0),
        player_health_before=result.get("player_health_before", 0.0),
        player_health_after=result.get("player_health_after", 0.0),
        enemy_health_after=result.get("enemy_health_after", 0.0),
        enemy_data=result.get("enemy_data", {}),
        victory=result.get("victory", False),
        loot=result.get("loot", [])
    )
    logger.info(f"[OUT] POST /game/lianli/battle - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/lianli/finish", response_model=LianliSettleResponse)
async def finish_battle(
    request: LianliSettleRequest,
    ctx: GameContext = Depends(get_write_game_context),
    token_info: dict = Depends(get_token_info)
):
    """历练战斗结算"""
    start_time = time.time()
    logger.info(f"[IN] POST /game/lianli/finish - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token_info['token']} - account_id: {token_info['account_id']} - token_version: {token_info['token_version']}")
    
    result = ctx.lianli_system.finish_battle(
        request.speed, request.index, ctx.player, ctx.spell_system, ctx.inventory_system, ctx.account_system
    )

    if (not result.get("success", False)) and result.get("reason_code") == "LIANLI_FINISH_TIME_INVALID":
        anti_cheat_result = await AntiCheatSystem.record_suspicious_operation(
            account_id=str(ctx.account.id),
            operation_type="lianli_finish",
            detail=(
                f"speed={request.speed}, index={request.index}, "
                f"actual={result.get('reason_data', {}).get('actual_time')}, "
                f"min_allowed={result.get('reason_data', {}).get('min_allowed_time')}"
            ),
            account_system=ctx.account_system,
            db_player_data=ctx.player_data,
            db_account=ctx.account
        )
        reason_data = result.get("reason_data", {})
        reason_data["invalid_report_count"] = anti_cheat_result.get("invalid_count", 0)
        reason_data["kicked_out"] = bool(anti_cheat_result.get("kicked_out", False))
        reason_data["kick_threshold"] = anti_cheat_result.get("threshold", 10)
        result["reason_data"] = reason_data
    
    if result["success"]:
        await AntiCheatSystem.reset_suspicious_operations(
            account_id=str(ctx.account.id),
            account_system=ctx.account_system,
            db_player_data=ctx.player_data
        )
        ctx.save()
        ctx.player_data.data = ctx.db_data
        ctx.player_data.last_online_at = datetime.now(timezone.utc)
        await ctx.player_data.save()
        
        logger.info(f"[GAME] 战斗结算成功 - account_id: {ctx.account.id} - settled_index: {result.get('settled_index', 0)}")
    
    response_data = LianliSettleResponse(
        success=result["success"],
        operation_id=request.operation_id,
        timestamp=request.timestamp,
        reason_code=result.get("reason_code", ""),
        reason_data=result.get("reason_data", {}),
        settled_index=result.get("settled_index", 0),
        total_index=result.get("total_index", 0),
        player_health_after=result.get("player_health_after", 0.0),
        loot_gained=result.get("loot_gained", []),
        exp_gained=result.get("exp_gained", 0)
    )
    logger.info(f"[OUT] POST /game/lianli/finish - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.get("/dungeon/foundation_herb_cave", response_model=DungeonInfoQueryResponse)
async def get_foundation_herb_cave_info(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取破镜草洞穴信息"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] GET /game/dungeon/foundation_herb_cave - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
    player_data = await DBPlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        logger.warning(f"[GAME] 玩家数据不存在 - account_id: {current_user.id}")
        response_data = DungeonInfoQueryResponse(
            success=False,
            operation_id="",
            timestamp=time.time(),
            reason_code="LIANLI_DUNGEON_INFO_PLAYER_NOT_FOUND",
            reason_data={"dungeon_id": "foundation_herb_cave"},
            remaining_count=0,
            max_count=0
        )
        logger.info(f"[OUT] GET /game/dungeon/foundation_herb_cave - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    db_data = player_data.data
    
    lianli_system = LianliSystem.from_dict(db_data.get("lianli_system", {}))
    
    dungeon_data = lianli_system.daily_dungeon_data.get("foundation_herb_cave", {})
    
    response_data = DungeonInfoQueryResponse(
        success=True,
        operation_id="",
        timestamp=time.time(),
        reason_code="LIANLI_DUNGEON_INFO_SUCCEEDED",
        reason_data={"dungeon_id": "foundation_herb_cave"},
        remaining_count=dungeon_data.get("remaining_count", 3),
        max_count=dungeon_data.get("max_count", 3)
    )
    logger.info(f"[OUT] GET /game/dungeon/foundation_herb_cave - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.get("/tower/highest_floor", response_model=TowerHighestFloorResponse)
async def get_tower_highest_floor(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取无尽塔最高层数"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] GET /game/tower/highest_floor - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
    player_data = await DBPlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        logger.warning(f"[GAME] 玩家数据不存在 - account_id: {current_user.id}")
        response_data = TowerHighestFloorResponse(
            success=False,
            operation_id="",
            timestamp=time.time(),
            reason_code="LIANLI_TOWER_INFO_PLAYER_NOT_FOUND",
            reason_data={},
            highest_floor=0
        )
        logger.info(f"[OUT] GET /game/tower/highest_floor - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    db_data = player_data.data
    
    lianli_system = LianliSystem.from_dict(db_data.get("lianli_system", {}))
    
    response_data = TowerHighestFloorResponse(
        success=True,
        operation_id="",
        timestamp=time.time(),
        reason_code="LIANLI_TOWER_INFO_SUCCEEDED",
        reason_data={},
        highest_floor=lianli_system.tower_highest_floor
    )
    logger.info(f"[OUT] GET /game/tower/highest_floor - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data
