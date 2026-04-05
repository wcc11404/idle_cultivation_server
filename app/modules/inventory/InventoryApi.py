"""
背包相关 API

包含使用物品、打开物品、扩容、整理、丢弃等功能
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from app.schemas.game import UseItemRequest, UseItemResponse, OrganizeInventoryRequest, DiscardItemRequest, ExpandInventoryRequest, ExpandInventoryResponse
from app.db.Models import PlayerData as DBPlayerData
from app.core.Security import get_current_user, decode_token, security
from app.core.Logger import logger
from app.modules import PlayerSystem, InventorySystem, SpellSystem, AlchemySystem
from datetime import datetime, timezone
import time
import json

router = APIRouter()


@router.post("/inventory/use", response_model=UseItemResponse)
async def use_item(request: UseItemRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """使用物品"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] POST /game/inventory/use - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
    player_data = await DBPlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        logger.warning(f"[GAME] 玩家数据不存在 - account_id: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="玩家数据不存在"
        )
    
    db_data = player_data.data
    
    player = PlayerSystem.from_dict(db_data.get("player", {}))
    inventory_system = InventorySystem.from_dict(db_data.get("inventory", {}))
    spell_system = SpellSystem.from_dict(db_data.get("spell_system", {}))
    alchemy_system = AlchemySystem.from_dict(
        db_data.get("alchemy_system", {})
    )
    
    result = inventory_system.use_item(request.item_id, player, spell_system, alchemy_system)
    
    if result["success"]:
        db_data["player"] = player.to_dict()
        db_data["inventory"] = inventory_system.to_dict()
        db_data["spell_system"] = spell_system.to_dict()
        db_data["alchemy_system"] = alchemy_system.to_dict()
        
        player_data.data = db_data
        player_data.last_online_at = datetime.now(timezone.utc)
        await player_data.save()
        
        logger.info(f"[GAME] 使用物品成功 - account_id: {current_user.id} - item_id: {request.item_id}")
    
    response_data = UseItemResponse(
        success=result["success"],
        operation_id=request.operation_id,
        timestamp=request.timestamp,
        effect=result.get("effect", {}),
        contents=None
    )
    logger.info(f"[OUT] POST /game/inventory/use - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/inventory/organize", response_model=dict)
async def organize_inventory(request: OrganizeInventoryRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """整理背包"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] POST /game/inventory/organize - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
    player_data = await DBPlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        logger.warning(f"[GAME] 玩家数据不存在 - account_id: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="玩家数据不存在"
        )
    
    db_data = player_data.data
    
    inventory_system = InventorySystem.from_dict(db_data.get("inventory", {}))
    
    result = inventory_system.organize_inventory()
    
    if result["success"]:
        db_data["inventory"] = inventory_system.to_dict()
        
        player_data.data = db_data
        player_data.last_online_at = datetime.now(timezone.utc)
        await player_data.save()
        
        logger.info(f"[GAME] 整理背包成功 - account_id: {current_user.id}")
    
    response_data = {
        "success": result["success"],
        "operation_id": request.operation_id,
        "timestamp": request.timestamp,
        "reason": result.get("reason", "")
    }
    logger.info(f"[OUT] POST /game/inventory/organize - {json.dumps(response_data, ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/inventory/discard", response_model=dict)
async def discard_item(request: DiscardItemRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """丢弃物品"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] POST /game/inventory/discard - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
    player_data = await DBPlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        logger.warning(f"[GAME] 玩家数据不存在 - account_id: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="玩家数据不存在"
        )
    
    db_data = player_data.data
    
    inventory_system = InventorySystem.from_dict(db_data.get("inventory", {}))
    
    result = inventory_system.discard_item(request.item_id, request.count)
    
    if result["success"]:
        db_data["inventory"] = inventory_system.to_dict()
        
        player_data.data = db_data
        player_data.last_online_at = datetime.now(timezone.utc)
        await player_data.save()
        
        logger.info(f"[GAME] 丢弃物品成功 - account_id: {current_user.id} - item_id: {request.item_id}")
    
    response_data = {
        "success": result["success"],
        "operation_id": request.operation_id,
        "timestamp": request.timestamp,
        "item_id": request.item_id,
        "discarded_count": result.get("discarded_count", 0)
    }
    logger.info(f"[OUT] POST /game/inventory/discard - {json.dumps(response_data, ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/inventory/expand", response_model=ExpandInventoryResponse)
async def expand_inventory(request: ExpandInventoryRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """扩容背包"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] POST /game/inventory/expand - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
    player_data = await DBPlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        logger.warning(f"[GAME] 玩家数据不存在 - account_id: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="玩家数据不存在"
        )
    
    db_data = player_data.data
    
    inventory_system = InventorySystem.from_dict(db_data.get("inventory", {}))
    
    result = inventory_system.expand_capacity()
    
    if result["success"]:
        db_data["inventory"] = inventory_system.to_dict()
        
        player_data.data = db_data
        player_data.last_online_at = datetime.now(timezone.utc)
        await player_data.save()
        
        logger.info(f"[GAME] 扩容背包成功 - account_id: {current_user.id} - new_capacity: {result.get('new_capacity', 0)}")
    
    response_data = ExpandInventoryResponse(
        success=result["success"],
        operation_id=request.operation_id,
        timestamp=request.timestamp,
        new_capacity=result.get("new_capacity", 0),
        message=result.get("reason", "")
    )
    logger.info(f"[OUT] POST /game/inventory/expand - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.get("/inventory/list", response_model=dict)
async def get_inventory_list(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取背包列表"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] GET /game/inventory/list - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
    player_data = await DBPlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        logger.warning(f"[GAME] 玩家数据不存在 - account_id: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="玩家数据不存在"
        )
    
    db_data = player_data.data
    
    inventory_system = InventorySystem.from_dict(db_data.get("inventory", {}))
    
    response_data = {
        "success": True,
        "inventory": inventory_system.to_dict()
    }
    logger.info(f"[OUT] GET /game/inventory/list - 耗时：{time.time() - start_time:.4f}s")
    return response_data
