"""
历练相关 API

包含开始历练、执行战斗、结束历练等功能
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from app.schemas.game import (
    LianliBattleRequest, LianliBattleResponse,
    LianliSettleRequest, LianliSettleResponse
)
from app.db.Models import PlayerData as DBPlayerData
from app.core.Security import get_current_user, decode_token, security
from app.core.Dependencies import get_game_context, get_token_info, GameContext
from app.core.Logger import logger
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
    ctx: GameContext = Depends(get_game_context),
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
            battle_timeline=[],
            total_time=0.0,
            player_health_before=0.0,
            player_health_after=0.0,
            enemy_health_after=0.0,
            enemy_data={},
            victory=False,
            loot=[],
            message="正在修炼中，无法开始战斗"
        )
        logger.info(f"[OUT] POST /game/lianli/battle - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    if ctx.alchemy_system.is_alchemizing:
        response_data = LianliBattleResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            battle_timeline=[],
            total_time=0.0,
            player_health_before=0.0,
            player_health_after=0.0,
            enemy_health_after=0.0,
            enemy_data={},
            victory=False,
            loot=[],
            message="正在炼丹中，无法开始战斗"
        )
        logger.info(f"[OUT] POST /game/lianli/battle - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    result = ctx.lianli_system.start_battle_simulation(
        request.area_id, ctx.player, ctx.spell_system
    )
    
    if result["success"]:
        ctx.db_data["lianli_system"] = ctx.lianli_system.to_dict()
        ctx.player_data.data = ctx.db_data
        ctx.player_data.last_online_at = datetime.now(timezone.utc)
        await ctx.player_data.save()
        
        logger.info(f"[GAME] 战斗模拟成功 - account_id: {ctx.account.id} - area_id: {request.area_id}")
    
    response_data = LianliBattleResponse(
        success=result["success"],
        operation_id=request.operation_id,
        timestamp=request.timestamp,
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
    logger.info(f"[OUT] POST /game/lianli/battle - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/lianli/finish", response_model=LianliSettleResponse)
async def finish_battle(
    request: LianliSettleRequest,
    ctx: GameContext = Depends(get_game_context),
    token_info: dict = Depends(get_token_info)
):
    """历练战斗结算"""
    start_time = time.time()
    logger.info(f"[IN] POST /game/lianli/finish - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token_info['token']} - account_id: {token_info['account_id']} - token_version: {token_info['token_version']}")
    
    result = ctx.lianli_system.finish_battle(
        request.speed, request.index, ctx.player, ctx.spell_system, ctx.inventory_system, ctx.account_system
    )
    
    if result["success"]:
        ctx.save()
        ctx.player_data.data = ctx.db_data
        ctx.player_data.last_online_at = datetime.now(timezone.utc)
        await ctx.player_data.save()
        
        logger.info(f"[GAME] 战斗结算成功 - account_id: {ctx.account.id} - settled_index: {result.get('settled_index', 0)}")
    
    response_data = LianliSettleResponse(
        success=result["success"],
        operation_id=request.operation_id,
        timestamp=request.timestamp,
        settled_index=result.get("settled_index", 0),
        total_index=result.get("total_index", 0),
        player_health_after=result.get("player_health_after", 0.0),
        loot_gained=result.get("loot_gained", []),
        exp_gained=result.get("exp_gained", 0),
        message=result.get("reason", result.get("message", ""))
    )
    logger.info(f"[OUT] POST /game/lianli/finish - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.get("/dungeon/foundation_herb_cave", response_model=dict)
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="玩家数据不存在"
        )
    
    db_data = player_data.data
    
    lianli_system = LianliSystem.from_dict(db_data.get("lianli_system", {}))
    
    dungeon_data = lianli_system.daily_dungeon_data.get("foundation_herb_cave", {})
    
    response_data = {
        "success": True,
        "remaining_count": dungeon_data.get("remaining_count", 3),
        "max_count": dungeon_data.get("max_count", 3)
    }
    logger.info(f"[OUT] GET /game/dungeon/foundation_herb_cave - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.get("/tower/highest_floor", response_model=dict)
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="玩家数据不存在"
        )
    
    db_data = player_data.data
    
    lianli_system = LianliSystem.from_dict(db_data.get("lianli_system", {}))
    
    response_data = {
        "success": True,
        "highest_floor": lianli_system.tower_highest_floor
    }
    logger.info(f"[OUT] GET /game/tower/highest_floor - 耗时：{time.time() - start_time:.4f}s")
    return response_data
