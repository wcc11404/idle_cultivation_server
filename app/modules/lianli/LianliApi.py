"""
历练相关 API

包含开始历练、执行战斗、结束历练等功能
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.db.models import Account, PlayerData as DBPlayerData
from app.core.security import decode_token
from app.core.logger import logger
from app.modules import (
    PlayerData, LianliSystem, LianliData, SpellSystem, InventorySystem
)
from datetime import datetime, timezone
import time
import json

router = APIRouter()
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Account:
    """获取当前用户"""
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        logger.warning("[AUTH] INVALID_TOKEN")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INVALID_TOKEN"
        )
    
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    
    account = await Account.get_or_none(id=account_id)
    if not account:
        logger.warning(f"[AUTH] ACCOUNT_NOT_FOUND - account_id: {account_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ACCOUNT_NOT_FOUND"
        )
    
    if account.token_version != token_version:
        logger.warning(f"[AUTH] KICKED_OUT - account_id: {account_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="KICKED_OUT"
        )
    
    return account


@router.get("/lianli/status", response_model=dict)
async def get_lianli_status(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取历练状态"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] GET /game/lianli/status - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
    player_data = await DBPlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        logger.warning(f"[GAME] 玩家数据不存在 - account_id: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="玩家数据不存在"
        )
    
    db_data = player_data.data
    
    lianli_system = LianliSystem.from_db_data(
        db_data.get("lianli_system", {}),
        SpellSystem.from_db_data(db_data.get("spell_system", {})),
        InventorySystem.from_db_data(db_data.get("inventory", {}))
    )
    
    response_data = {
        "success": True,
        "tower_highest_floor": lianli_system.tower_highest_floor,
        "daily_dungeon_data": lianli_system.daily_dungeon_data,
        "areas_config": LianliData.get_areas_config()
    }
    logger.info(f"[OUT] GET /game/lianli/status - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/lianli/battle", response_model=dict)
async def execute_battle(request: dict, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """执行战斗"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] POST /game/lianli/battle - {json.dumps(request, ensure_ascii=False)} - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
    player_data = await DBPlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        logger.warning(f"[GAME] 玩家数据不存在 - account_id: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="玩家数据不存在"
        )
    
    db_data = player_data.data
    
    player = PlayerData.from_dict(db_data.get("player", {}))
    spell_system = SpellSystem.from_db_data(db_data.get("spell_system", {}))
    inventory_system = InventorySystem.from_db_data(db_data.get("inventory", {}))
    
    lianli_system = LianliSystem.from_db_data(
        db_data.get("lianli_system", {}),
        spell_system,
        inventory_system
    )
    
    area_id = request.get("area_id")
    floor = request.get("floor")
    is_tower = request.get("is_tower", False)
    
    if is_tower:
        enemy_data = lianli_system.generate_enemy(area_id, floor)
    else:
        enemy_data = lianli_system.generate_enemy(area_id)
    
    if not enemy_data:
        logger.warning(f"[GAME] 生成敌人失败 - account_id: {current_user.id} - area_id: {area_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="生成敌人失败"
        )
    
    combat_buffs = {}
    
    result = lianli_system.execute_battle(
        player, 
        enemy_data, 
        combat_buffs
    )
    
    if result["victory"]:
        if is_tower:
            lianli_system.finish_tower_battle(floor, True)
        elif lianli_system.is_special_area(area_id) or lianli_system.is_daily_dungeon(area_id):
            lianli_system.use_daily_dungeon_count(area_id)
        
        db_data["player"] = player.to_dict()
        db_data["inventory"] = inventory_system.to_db_data()
        db_data["lianli_system"] = lianli_system.to_db_data()
        
        player_data.data = db_data
        player_data.last_online_at = datetime.now(timezone.utc)
        await player_data.save()
        
        logger.info(f"[GAME] 战斗胜利 - account_id: {current_user.id} - area_id: {area_id} - loot: {result.get('loot', [])}")
    else:
        db_data["player"] = player.to_dict()
        player_data.data = db_data
        player_data.last_online_at = datetime.now(timezone.utc)
        await player_data.save()
        
        logger.info(f"[GAME] 战斗失败 - account_id: {current_user.id} - area_id: {area_id}")
    
    response_data = {
        "success": True,
        "victory": result["victory"],
        "battle_timeline": result["battle_timeline"],
        "total_time": result["total_time"],
        "loot": result["loot"],
        "player_health_after": result["player_health_after"],
        "enemy_health_after": result["enemy_health_after"]
    }
    logger.info(f"[OUT] POST /game/lianli/battle - {json.dumps(response_data, ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.get("/dungeon/info", response_model=dict)
async def get_dungeon_info(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取副本信息"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] GET /game/dungeon/info - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
    player_data = await DBPlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        logger.warning(f"[GAME] 玩家数据不存在 - account_id: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="玩家数据不存在"
        )
    
    db_data = player_data.data
    
    lianli_system = LianliSystem.from_db_data(
        db_data.get("lianli_system", {}),
        SpellSystem.from_db_data(db_data.get("spell_system", {})),
        InventorySystem.from_db_data(db_data.get("inventory", {}))
    )
    
    response_data = {
        "success": True,
        "dungeon_data": lianli_system.daily_dungeon_data,
        "areas_config": LianliData.get_areas_config()
    }
    logger.info(f"[OUT] GET /game/dungeon/info - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/dungeon/finish", response_model=dict)
async def finish_dungeon(request: dict, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """完成副本（扣减次数）"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] POST /game/dungeon/finish - {json.dumps(request, ensure_ascii=False)} - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
    player_data = await DBPlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        logger.warning(f"[GAME] 玩家数据不存在 - account_id: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="玩家数据不存在"
        )
    
    db_data = player_data.data
    
    lianli_system = LianliSystem.from_db_data(
        db_data.get("lianli_system", {}),
        SpellSystem.from_db_data(db_data.get("spell_system", {})),
        InventorySystem.from_db_data(db_data.get("inventory", {}))
    )
    
    dungeon_id = request.get("dungeon_id")
    victory = request.get("victory", True)
    
    if victory:
        lianli_system.use_daily_dungeon_count(dungeon_id)
    
    db_data["lianli_system"] = lianli_system.to_db_data()
    
    player_data.data = db_data
    player_data.last_online_at = datetime.now(timezone.utc)
    await player_data.save()
    
    response_data = {
        "success": True,
        "remaining_count": lianli_system.get_daily_dungeon_count(dungeon_id)
    }
    logger.info(f"[OUT] POST /game/dungeon/finish - 耗时：{time.time() - start_time:.4f}s")
    return response_data
