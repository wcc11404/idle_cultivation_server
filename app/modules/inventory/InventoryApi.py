"""
背包相关 API

包含使用物品、打开物品、扩容、整理、丢弃等功能
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas.game import UseItemRequest, UseItemResponse
from app.db.models import Account, PlayerData as DBPlayerData
from app.core.security import decode_token
from app.core.logger import logger
from app.modules import PlayerData, InventorySystem, SpellSystem, AlchemySystem
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
    
    player = PlayerData.from_dict(db_data.get("player", {}))
    inventory_system = InventorySystem.from_db_data(db_data.get("inventory", {}))
    spell_system = SpellSystem.from_db_data(db_data.get("spell_system", {}))
    alchemy_system = AlchemySystem.from_db_data(
        db_data.get("alchemy_system", {}),
        spell_system,
        inventory_system
    )
    
    result = inventory_system.use_item(request.item_id, player, spell_system, alchemy_system)
    
    if result["success"]:
        db_data["player"] = player.to_dict()
        db_data["inventory"] = inventory_system.to_db_data()
        db_data["spell_system"] = spell_system.to_db_data()
        db_data["alchemy_system"] = alchemy_system.to_db_data()
        
        player_data.data = db_data
        player_data.last_online_at = datetime.now(timezone.utc)
        await player_data.save()
        
        logger.info(f"[GAME] 使用物品成功 - account_id: {current_user.id} - item_id: {request.item_id}")
    
    response_data = UseItemResponse(
        success=result["success"],
        effect=result.get("effect", {}),
        contents=None
    )
    logger.info(f"[OUT] POST /game/inventory/use - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/inventory/organize", response_model=dict)
async def organize_inventory(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """整理背包"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] POST /game/inventory/organize - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
    player_data = await DBPlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        logger.warning(f"[GAME] 玩家数据不存在 - account_id: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="玩家数据不存在"
        )
    
    db_data = player_data.data
    
    inventory_system = InventorySystem.from_db_data(db_data.get("inventory", {}))
    
    result = inventory_system.organize_inventory()
    
    if result["success"]:
        db_data["inventory"] = inventory_system.to_db_data()
        
        player_data.data = db_data
        player_data.last_online_at = datetime.now(timezone.utc)
        await player_data.save()
        
        logger.info(f"[GAME] 整理背包成功 - account_id: {current_user.id}")
    
    response_data = {
        "success": result["success"],
        "reason": result.get("reason", "")
    }
    logger.info(f"[OUT] POST /game/inventory/organize - {json.dumps(response_data, ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/inventory/discard", response_model=dict)
async def discard_item(request: UseItemRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
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
    
    inventory_system = InventorySystem.from_db_data(db_data.get("inventory", {}))
    
    result = inventory_system.discard_item(request.item_id, 1)
    
    if result["success"]:
        db_data["inventory"] = inventory_system.to_db_data()
        
        player_data.data = db_data
        player_data.last_online_at = datetime.now(timezone.utc)
        await player_data.save()
        
        logger.info(f"[GAME] 丢弃物品成功 - account_id: {current_user.id} - item_id: {request.item_id}")
    
    response_data = {
        "success": result["success"],
        "item_id": request.item_id,
        "discarded_count": result.get("discarded_count", 0)
    }
    logger.info(f"[OUT] POST /game/inventory/discard - {json.dumps(response_data, ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data
