"""
修炼相关 API

包含突破境界等功能
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas.game import BreakthroughRequest, BreakthroughResponse
from app.db.models import Account, PlayerData as DBPlayerData
from app.core.security import decode_token
from app.core.logger import logger
from app.modules import PlayerData, CultivationSystem, InventorySystem
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


@router.post("/player/breakthrough", response_model=BreakthroughResponse)
async def breakthrough(request: BreakthroughRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """突破境界"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] POST /game/player/breakthrough - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
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
    
    check_result = CultivationSystem.can_breakthrough(player, inventory_system)
    
    if not check_result["can"]:
        response_data = BreakthroughResponse(
            success=False,
            new_realm=player.realm,
            new_level=player.realm_level,
            remaining_spirit_energy=player.spirit_energy,
            materials_used={}
        )
        logger.info(f"[OUT] POST /game/player/breakthrough - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    result = CultivationSystem.execute_breakthrough(player, inventory_system)
    
    if result["success"]:
        db_data["player"]["realm"] = player.realm
        db_data["player"]["realm_level"] = player.realm_level
        db_data["player"]["spirit_energy"] = player.spirit_energy
        db_data["inventory"] = inventory_system.to_db_data()
        
        player_data.data = db_data
        player_data.last_online_at = datetime.now(timezone.utc)
        await player_data.save()
        
        logger.info(f"[GAME] 突破成功 - account_id: {current_user.id} - new_realm: {player.realm} - new_level: {player.realm_level} - costs: {result.get('costs', {})}")
    
    response_data = BreakthroughResponse(
        success=result["success"],
        new_realm=result.get("new_realm", player.realm),
        new_level=result.get("new_level", player.realm_level),
        remaining_spirit_energy=player.spirit_energy,
        materials_used=result.get("costs", {})
    )
    logger.info(f"[OUT] POST /game/player/breakthrough - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data
