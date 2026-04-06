"""
术法相关 API

包含装备术法、卸下术法、升级术法、充灵气等功能
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from app.schemas.game import EquipSpellRequest, UnequipSpellRequest, UpgradeSpellRequest, ChargeSpellRequest
from app.db.Models import PlayerData as DBPlayerData
from app.core.Security import get_current_user, decode_token, security
from app.core.Dependencies import get_game_context, get_token_info, GameContext
from app.core.Logger import logger
from app.modules import PlayerSystem, SpellSystem, SpellData
from datetime import datetime, timezone
import time
import json

router = APIRouter()


@router.post("/spell/equip", response_model=dict)
async def equip_spell(
    request: EquipSpellRequest,
    ctx: GameContext = Depends(get_game_context),
    token_info: dict = Depends(get_token_info)
):
    """装备术法"""
    start_time = time.time()
    logger.info(f"[IN] POST /game/spell/equip - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token_info['token']} - account_id: {token_info['account_id']} - token_version: {token_info['token_version']}")
    
    result = ctx.spell_system.equip_spell(request.spell_id)
    
    if result["success"]:
        ctx.db_data["spell_system"] = ctx.spell_system.to_dict()
        
        ctx.player_data.data = ctx.db_data
        ctx.player_data.last_online_at = datetime.now(timezone.utc)
        await ctx.player_data.save()
        
        logger.info(f"[GAME] 装备术法成功 - account_id: {ctx.account.id} - spell_id: {request.spell_id}")
    
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
async def unequip_spell(
    request: UnequipSpellRequest,
    ctx: GameContext = Depends(get_game_context),
    token_info: dict = Depends(get_token_info)
):
    """卸下术法"""
    start_time = time.time()
    logger.info(f"[IN] POST /game/spell/unequip - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token_info['token']} - account_id: {token_info['account_id']} - token_version: {token_info['token_version']}")
    
    result = ctx.spell_system.unequip_spell(request.spell_id)
    
    if result["success"]:
        ctx.db_data["spell_system"] = ctx.spell_system.to_dict()
        
        ctx.player_data.data = ctx.db_data
        ctx.player_data.last_online_at = datetime.now(timezone.utc)
        await ctx.player_data.save()
        
        logger.info(f"[GAME] 卸下术法成功 - account_id: {ctx.account.id} - spell_id: {request.spell_id}")
    
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
async def upgrade_spell(
    request: UpgradeSpellRequest,
    ctx: GameContext = Depends(get_game_context),
    token_info: dict = Depends(get_token_info)
):
    """升级术法"""
    start_time = time.time()
    logger.info(f"[IN] POST /game/spell/upgrade - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token_info['token']} - account_id: {token_info['account_id']} - token_version: {token_info['token_version']}")
    
    result = ctx.spell_system.upgrade_spell(request.spell_id, ctx.player)
    
    if result["success"]:
        ctx.db_data["player"] = ctx.player.to_dict()
        ctx.db_data["spell_system"] = ctx.spell_system.to_dict()
        
        ctx.player_data.data = ctx.db_data
        ctx.player_data.last_online_at = datetime.now(timezone.utc)
        await ctx.player_data.save()
        
        logger.info(f"[GAME] 升级术法成功 - account_id: {ctx.account.id} - spell_id: {request.spell_id} - new_level: {result.get('new_level', 0)}")
    
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
async def charge_spell(
    request: ChargeSpellRequest,
    ctx: GameContext = Depends(get_game_context),
    token_info: dict = Depends(get_token_info)
):
    """给术法充灵气"""
    start_time = time.time()
    logger.info(f"[IN] POST /game/spell/charge - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token_info['token']} - account_id: {token_info['account_id']} - token_version: {token_info['token_version']}")
    
    result = ctx.spell_system.charge_spell_spirit(request.spell_id, request.amount, ctx.player)
    
    if result["success"]:
        ctx.db_data["player"] = ctx.player.to_dict()
        ctx.db_data["spell_system"] = ctx.spell_system.to_dict()
        
        ctx.player_data.data = ctx.db_data
        ctx.player_data.last_online_at = datetime.now(timezone.utc)
        await ctx.player_data.save()
        
        logger.info(f"[GAME] 充灵气成功 - account_id: {ctx.account.id} - spell_id: {request.spell_id} - amount: {request.amount}")
    
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
async def get_spell_list(
    ctx: GameContext = Depends(get_game_context),
    token_info: dict = Depends(get_token_info)
):
    """获取术法列表"""
    start_time = time.time()
    logger.info(f"[IN] GET /game/spell/list - token: {token_info['token']} - account_id: {token_info['account_id']} - token_version: {token_info['token_version']}")
    
    response_data = {
        "success": True,
        "spells": ctx.spell_system.player_spells,
        "equipped_spells": ctx.spell_system.equipped_spells,
        "spells_config": SpellData.get_spells_config()
    }
    logger.info(f"[OUT] GET /game/spell/list - 耗时：{time.time() - start_time:.4f}s")
    return response_data
