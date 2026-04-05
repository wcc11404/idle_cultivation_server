"""
炼丹相关 API

包含炼制丹药、学习丹方等功能
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from app.schemas.game import (
    CraftPillsRequest, LearnRecipeRequest,
    AlchemyStartRequest, AlchemyStartResponse,
    AlchemyReportRequest, AlchemyReportResponse,
    AlchemyStopRequest, AlchemyStopResponse
)
from app.db.Models import PlayerData as DBPlayerData
from app.core.Security import get_current_user, decode_token, security
from app.core.Logger import logger
from app.modules import PlayerSystem, AlchemySystem, RecipeData, SpellSystem, InventorySystem, LianliSystem
from .AlchemyWorkshop import AlchemyWorkshop
from datetime import datetime, timezone
import time
import json

router = APIRouter()


@router.post("/alchemy/learn_recipe", response_model=dict)
async def learn_recipe(request: LearnRecipeRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """学习丹方"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] POST /game/alchemy/learn_recipe - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
    player_data = await DBPlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        logger.warning(f"[GAME] 玩家数据不存在 - account_id: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="玩家数据不存在"
        )
    
    db_data = player_data.data
    
    alchemy_system = AlchemySystem.from_dict(
        db_data.get("alchemy_system", {}),
        SpellSystem.from_dict(db_data.get("spell_system", {})),
        InventorySystem.from_dict(db_data.get("inventory", {}))
    )
    
    result = alchemy_system.learn_recipe(request.recipe_id)
    
    if result["success"]:
        db_data["alchemy_system"] = alchemy_system.to_dict()
        
        player_data.data = db_data
        player_data.last_online_at = datetime.now(timezone.utc)
        await player_data.save()
        
        logger.info(f"[GAME] 学习丹方成功 - account_id: {current_user.id} - recipe_id: {request.recipe_id}")
    
    response_data = {
        "success": result["success"],
        "operation_id": request.operation_id,
        "timestamp": request.timestamp,
        "reason": result.get("reason", ""),
        "recipe_id": request.recipe_id
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
    
    alchemy_system = AlchemySystem.from_dict(
        db_data.get("alchemy_system", {}),
        SpellSystem.from_dict(db_data.get("spell_system", {})),
        InventorySystem.from_dict(db_data.get("inventory", {}))
    )
    
    learned_recipes = alchemy_system.get_learned_recipes()
    
    response_data = {
        "success": True,
        "learned_recipes": learned_recipes,
        "recipes_config": RecipeData.get_recipes_config()
    }
    logger.info(f"[OUT] GET /game/alchemy/recipes - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/alchemy/start", response_model=AlchemyStartResponse)
async def start_alchemy(request: AlchemyStartRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """开始炼丹"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] POST /game/alchemy/start - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
    player_data = await DBPlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        logger.warning(f"[GAME] 玩家数据不存在 - account_id: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="玩家数据不存在"
        )
    
    db_data = player_data.data
    
    player = PlayerSystem.from_dict(db_data.get("player", {}))
    alchemy_system = AlchemySystem.from_dict(db_data.get("alchemy_system", {}))
    lianli_system = LianliSystem.from_dict(db_data.get("lianli_system", {}))
    
    if alchemy_system.is_alchemizing:
        response_data = AlchemyStartResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            is_alchemizing=True,
            message="已在炼丹状态"
        )
        logger.info(f"[OUT] POST /game/alchemy/start - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    if player.is_cultivating:
        response_data = AlchemyStartResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            is_alchemizing=False,
            message="正在修炼中，无法开始炼丹"
        )
        logger.info(f"[OUT] POST /game/alchemy/start - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    if lianli_system.is_battling:
        response_data = AlchemyStartResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            is_alchemizing=False,
            message="正在战斗中，无法开始炼丹"
        )
        logger.info(f"[OUT] POST /game/alchemy/start - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    current_time = time.time()
    alchemy_system.is_alchemizing = True
    alchemy_system.last_alchemy_report_time = current_time
    
    db_data["alchemy_system"] = alchemy_system.to_dict()
    
    player_data.data = db_data
    player_data.last_online_at = datetime.now(timezone.utc)
    await player_data.save()
    
    response_data = AlchemyStartResponse(
        success=True,
        operation_id=request.operation_id,
        timestamp=request.timestamp,
        is_alchemizing=True,
        message="开始炼丹"
    )
    logger.info(f"[OUT] POST /game/alchemy/start - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/alchemy/report", response_model=AlchemyReportResponse)
async def report_alchemy(request: AlchemyReportRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """炼丹上报"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] POST /game/alchemy/report - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
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
    inventory_system = InventorySystem.from_dict(db_data.get("inventory", {}))
    alchemy_system = AlchemySystem.from_dict(db_data.get("alchemy_system", {}))
    
    if not alchemy_system.is_alchemizing:
        response_data = AlchemyReportResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            success_count=0,
            fail_count=0,
            products={},
            materials_consumed={},
            message="当前未在炼丹状态"
        )
        logger.info(f"[OUT] POST /game/alchemy/report - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    recipe_config = RecipeData.get_recipe(request.recipe_id)
    if not recipe_config:
        response_data = AlchemyReportResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            success_count=0,
            fail_count=0,
            products={},
            materials_consumed={},
            message="丹方不存在"
        )
        logger.info(f"[OUT] POST /game/alchemy/report - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    current_time = time.time()
    craft_time = recipe_config.get("base_time", 10.0)
    
    actual_interval = current_time - alchemy_system.last_alchemy_report_time
    expected_interval = request.count * craft_time
    min_allowed_interval = expected_interval * 0.9
    
    if actual_interval < min_allowed_interval:
        response_data = AlchemyReportResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            success_count=0,
            fail_count=0,
            products={},
            materials_consumed={},
            message=f"炼丹上报异常：上报{request.count}次，实际间隔{actual_interval:.1f}秒，最小允许{min_allowed_interval:.1f}秒"
        )
        logger.info(f"[OUT] POST /game/alchemy/report - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    result = AlchemyWorkshop.craft_pills(
        alchemy_system, request.recipe_id, request.count, player, spell_system, inventory_system
    )
    
    if result["success"]:
        alchemy_system.last_alchemy_report_time = current_time
        
        db_data["player"] = player.to_dict()
        db_data["inventory"] = inventory_system.to_dict()
        db_data["alchemy_system"] = alchemy_system.to_dict()
        
        player_data.data = db_data
        player_data.last_online_at = datetime.now(timezone.utc)
        await player_data.save()
    
    response_data = AlchemyReportResponse(
        success=result["success"],
        operation_id=request.operation_id,
        timestamp=request.timestamp,
        success_count=result.get("success_count", 0),
        fail_count=result.get("fail_count", 0),
        products=result.get("products", {}),
        materials_consumed=result.get("materials_consumed", {}),
        message=result.get("reason", "炼丹完成")
    )
    logger.info(f"[OUT] POST /game/alchemy/report - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/alchemy/stop", response_model=AlchemyStopResponse)
async def stop_alchemy(request: AlchemyStopRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """停止炼丹"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] POST /game/alchemy/stop - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
    player_data = await DBPlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        logger.warning(f"[GAME] 玩家数据不存在 - account_id: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="玩家数据不存在"
        )
    
    db_data = player_data.data
    
    alchemy_system = AlchemySystem.from_dict(db_data.get("alchemy_system", {}))
    
    if not alchemy_system.is_alchemizing:
        response_data = AlchemyStopResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            is_alchemizing=False,
            message="当前未在炼丹状态"
        )
        logger.info(f"[OUT] POST /game/alchemy/stop - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    alchemy_system.is_alchemizing = False
    alchemy_system.last_alchemy_report_time = 0.0
    
    db_data["alchemy_system"] = alchemy_system.to_dict()
    
    player_data.data = db_data
    player_data.last_online_at = datetime.now(timezone.utc)
    await player_data.save()
    
    response_data = AlchemyStopResponse(
        success=True,
        operation_id=request.operation_id,
        timestamp=request.timestamp,
        is_alchemizing=False,
        message="停止炼丹"
    )
    logger.info(f"[OUT] POST /game/alchemy/stop - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data
