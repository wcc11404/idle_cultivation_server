"""
术法相关 API

包含装备术法、卸下术法、升级术法、充灵气等功能
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from app.schemas.game import EquipSpellRequest, UnequipSpellRequest, UpgradeSpellRequest, ChargeSpellRequest
from app.db.Models import PlayerData as DBPlayerData
from app.core.Security import get_current_user, decode_token, security
from app.core.Logger import logger
from app.modules import PlayerSystem, SpellSystem, SpellData
from datetime import datetime, timezone
import time
import json

router = APIRouter()


@router.post("/spell/equip", response_model=dict)
async def equip_spell(request: EquipSpellRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """装备术法"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] POST /game/spell/equip - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
    player_data = await DBPlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        logger.warning(f"[GAME] 玩家数据不存在 - account_id: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="玩家数据不存在"
        )
    
    db_data = player_data.data
    
    spell_system = SpellSystem.from_dict(db_data.get("spell_system", {}))
    
    result = spell_system.equip_spell(request.spell_id)
    
    if result["success"]:
        db_data["spell_system"] = spell_system.to_dict()
        
        player_data.data = db_data
        player_data.last_online_at = datetime.now(timezone.utc)
        await player_data.save()
        
        logger.info(f"[GAME] 装备术法成功 - account_id: {current_user.id} - spell_id: {request.spell_id}")
    
    response_data = {
        "success": result["success"],
        "operation_id": request.operation_id,
        "timestamp": request.timestamp,
        "reason": result.get("reason", ""),
        "spell_id": request.spell_id,
        "spell_type": result.get("spell_type", "")
    }
    logger.info(f"[OUT] POST /game/spell/equip - {json.dumps(response_data, ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/spell/unequip", response_model=dict)
async def unequip_spell(request: UnequipSpellRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """卸下术法"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] POST /game/spell/unequip - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
    player_data = await DBPlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        logger.warning(f"[GAME] 玩家数据不存在 - account_id: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="玩家数据不存在"
        )
    
    db_data = player_data.data
    
    spell_system = SpellSystem.from_dict(db_data.get("spell_system", {}))
    
    result = spell_system.unequip_spell(request.spell_id)
    
    if result["success"]:
        db_data["spell_system"] = spell_system.to_dict()
        
        player_data.data = db_data
        player_data.last_online_at = datetime.now(timezone.utc)
        await player_data.save()
        
        logger.info(f"[GAME] 卸下术法成功 - account_id: {current_user.id} - spell_id: {request.spell_id}")
    
    response_data = {
        "success": result["success"],
        "operation_id": request.operation_id,
        "timestamp": request.timestamp,
        "reason": result.get("reason", ""),
        "spell_id": request.spell_id,
        "spell_type": result.get("spell_type", "")
    }
    logger.info(f"[OUT] POST /game/spell/unequip - {json.dumps(response_data, ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/spell/upgrade", response_model=dict)
async def upgrade_spell(request: UpgradeSpellRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """升级术法"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] POST /game/spell/upgrade - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
    player_data = await DBPlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        logger.warning(f"[GAME] 玩家数据不存在 - account_id: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="玩家数据不存在"
        )
    
    db_data = player_data.data
    
    player = PlayerSystem.from_dict(db_data.get("player", {}))
    spell_system = SpellSystem.from_dict(db_data.get("spell_system", {}))
    
    result = spell_system.upgrade_spell(request.spell_id, player)
    
    if result["success"]:
        db_data["player"] = player.to_dict()
        db_data["spell_system"] = spell_system.to_dict()
        
        player_data.data = db_data
        player_data.last_online_at = datetime.now(timezone.utc)
        await player_data.save()
        
        logger.info(f"[GAME] 升级术法成功 - account_id: {current_user.id} - spell_id: {request.spell_id} - new_level: {result.get('new_level', 0)}")
    
    response_data = {
        "success": result["success"],
        "operation_id": request.operation_id,
        "timestamp": request.timestamp,
        "reason": result.get("reason", ""),
        "spell_id": request.spell_id,
        "new_level": result.get("new_level", 0)
    }
    logger.info(f"[OUT] POST /game/spell/upgrade - {json.dumps(response_data, ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/spell/charge", response_model=dict)
async def charge_spell(request: ChargeSpellRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """给术法充灵气"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] POST /game/spell/charge - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
    player_data = await DBPlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        logger.warning(f"[GAME] 玩家数据不存在 - account_id: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="玩家数据不存在"
        )
    
    db_data = player_data.data
    
    player = PlayerSystem.from_dict(db_data.get("player", {}))
    spell_system = SpellSystem.from_dict(db_data.get("spell_system", {}))
    
    result = spell_system.charge_spell_spirit(request.spell_id, request.amount, player)
    
    if result["success"]:
        db_data["player"] = player.to_dict()
        db_data["spell_system"] = spell_system.to_dict()
        
        player_data.data = db_data
        player_data.last_online_at = datetime.now(timezone.utc)
        await player_data.save()
        
        logger.info(f"[GAME] 充灵气成功 - account_id: {current_user.id} - spell_id: {request.spell_id} - amount: {request.amount}")
    
    response_data = {
        "success": result["success"],
        "operation_id": request.operation_id,
        "timestamp": request.timestamp,
        "reason": result.get("reason", ""),
        "spell_id": request.spell_id,
        "charged_amount": result.get("charged_amount", 0)
    }
    logger.info(f"[OUT] POST /game/spell/charge - {json.dumps(response_data, ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.get("/spell/list", response_model=dict)
async def get_spell_list(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取术法列表"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] GET /game/spell/list - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
    player_data = await DBPlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        logger.warning(f"[GAME] 玩家数据不存在 - account_id: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="玩家数据不存在"
        )
    
    db_data = player_data.data
    
    spell_system = SpellSystem.from_dict(db_data.get("spell_system", {}))
    
    response_data = {
        "success": True,
        "spells": spell_system.player_spells,
        "equipped_spells": spell_system.equipped_spells,
        "spells_config": SpellData.get_spells_config()
    }
    logger.info(f"[OUT] GET /game/spell/list - 耗时：{time.time() - start_time:.4f}s")
    return response_data
