"""
炼丹相关 API

包含炼制丹药、学习丹方等功能
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.db.models import Account, PlayerData as DBPlayerData
from app.core.security import decode_token
from app.core.logger import logger
from app.modules import PlayerData, AlchemySystem, RecipeData, SpellSystem, InventorySystem
from .AlchemyWorkshop import AlchemyWorkshop
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


@router.post("/alchemy/craft", response_model=dict)
async def craft_pills(request: dict, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """炼制丹药"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] POST /game/alchemy/craft - {json.dumps(request, ensure_ascii=False)} - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
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
    alchemy_system = AlchemySystem.from_db_data(
        db_data.get("alchemy_system", {})
    )
    
    recipe_id = request.get("recipe_id")
    count = request.get("count", 1)
    
    result = AlchemyWorkshop.craft_pills(
        alchemy_system, recipe_id, count, player, spell_system, inventory_system
    )
    
    if result["success"]:
        db_data["player"] = player.to_dict()
        db_data["inventory"] = inventory_system.to_db_data()
        db_data["alchemy_system"] = alchemy_system.to_db_data()
        
        player_data.data = db_data
        player_data.last_online_at = datetime.now(timezone.utc)
        await player_data.save()
        
        logger.info(f"[GAME] 炼制丹药成功 - account_id: {current_user.id} - recipe_id: {recipe_id} - success_count: {result.get('success_count', 0)}")
    
    response_data = {
        "success": result["success"],
        "reason": result.get("reason", ""),
        "recipe_id": recipe_id,
        "success_count": result.get("success_count", 0),
        "fail_count": result.get("fail_count", 0),
        "products": result.get("products", {})
    }
    logger.info(f"[OUT] POST /game/alchemy/craft - {json.dumps(response_data, ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/alchemy/learn_recipe", response_model=dict)
async def learn_recipe(request: dict, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """学习丹方"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] POST /game/alchemy/learn_recipe - {json.dumps(request, ensure_ascii=False)} - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
    player_data = await DBPlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        logger.warning(f"[GAME] 玩家数据不存在 - account_id: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="玩家数据不存在"
        )
    
    db_data = player_data.data
    
    alchemy_system = AlchemySystem.from_db_data(
        db_data.get("alchemy_system", {}),
        SpellSystem.from_db_data(db_data.get("spell_system", {})),
        InventorySystem.from_db_data(db_data.get("inventory", {}))
    )
    
    recipe_id = request.get("recipe_id")
    
    result = alchemy_system.learn_recipe(recipe_id)
    
    if result["success"]:
        db_data["alchemy_system"] = alchemy_system.to_db_data()
        
        player_data.data = db_data
        player_data.last_online_at = datetime.now(timezone.utc)
        await player_data.save()
        
        logger.info(f"[GAME] 学习丹方成功 - account_id: {current_user.id} - recipe_id: {recipe_id}")
    
    response_data = {
        "success": result["success"],
        "reason": result.get("reason", ""),
        "recipe_id": recipe_id
    }
    logger.info(f"[OUT] POST /game/alchemy/learn_recipe - {json.dumps(response_data, ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.get("/alchemy/recipes", response_model=dict)
async def get_recipes(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取丹方列表"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] GET /game/alchemy/recipes - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
    player_data = await DBPlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        logger.warning(f"[GAME] 玩家数据不存在 - account_id: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="玩家数据不存在"
        )
    
    db_data = player_data.data
    
    alchemy_system = AlchemySystem.from_db_data(
        db_data.get("alchemy_system", {}),
        SpellSystem.from_db_data(db_data.get("spell_system", {})),
        InventorySystem.from_db_data(db_data.get("inventory", {}))
    )
    
    learned_recipes = alchemy_system.get_learned_recipes()
    
    response_data = {
        "success": True,
        "learned_recipes": learned_recipes,
        "recipes_config": RecipeData.get_recipes_config()
    }
    logger.info(f"[OUT] GET /game/alchemy/recipes - 耗时：{time.time() - start_time:.4f}s")
    return response_data
