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
from app.core.Dependencies import get_game_context, get_token_info, GameContext
from app.core.Logger import logger
from app.modules import PlayerSystem, AlchemySystem, RecipeData, SpellSystem, InventorySystem, LianliSystem
from .AlchemyWorkshop import AlchemyWorkshop
from datetime import datetime, timezone
import time
import json

router = APIRouter()


@router.post("/alchemy/learn_recipe", response_model=dict)
async def learn_recipe(
    request: LearnRecipeRequest,
    ctx: GameContext = Depends(get_game_context),
    token_info: dict = Depends(get_token_info)
):
    """学习丹方"""
    start_time = time.time()
    logger.info(f"[IN] POST /game/alchemy/learn_recipe - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token_info['token']} - account_id: {token_info['account_id']} - token_version: {token_info['token_version']}")
    
    result = ctx.alchemy_system.learn_recipe(request.recipe_id)
    
    if result["success"]:
        ctx.db_data["alchemy_system"] = ctx.alchemy_system.to_dict()
        
        ctx.player_data.data = ctx.db_data
        ctx.player_data.last_online_at = datetime.now(timezone.utc)
        await ctx.player_data.save()
        
        logger.info(f"[GAME] 学习丹方成功 - account_id: {ctx.account.id} - recipe_id: {request.recipe_id}")
    
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
async def get_recipes(
    ctx: GameContext = Depends(get_game_context),
    token_info: dict = Depends(get_token_info)
):
    """获取丹方列表"""
    start_time = time.time()
    logger.info(f"[IN] GET /game/alchemy/recipes - token: {token_info['token']} - account_id: {token_info['account_id']} - token_version: {token_info['token_version']}")
    
    learned_recipes = ctx.alchemy_system.get_learned_recipes()
    
    response_data = {
        "success": True,
        "learned_recipes": learned_recipes,
        "recipes_config": RecipeData.get_recipes_config()
    }
    logger.info(f"[OUT] GET /game/alchemy/recipes - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/alchemy/start", response_model=AlchemyStartResponse)
async def start_alchemy(
    request: AlchemyStartRequest,
    ctx: GameContext = Depends(get_game_context),
    token_info: dict = Depends(get_token_info)
):
    """开始炼丹"""
    start_time = time.time()
    logger.info(f"[IN] POST /game/alchemy/start - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token_info['token']} - account_id: {token_info['account_id']} - token_version: {token_info['token_version']}")
    
    if ctx.alchemy_system.is_alchemizing:
        response_data = AlchemyStartResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            is_alchemizing=True,
            message="已在炼丹状态"
        )
        logger.info(f"[OUT] POST /game/alchemy/start - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    if ctx.player.is_cultivating:
        response_data = AlchemyStartResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            is_alchemizing=False,
            message="正在修炼中，无法开始炼丹"
        )
        logger.info(f"[OUT] POST /game/alchemy/start - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    if ctx.lianli_system.is_battling:
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
    ctx.alchemy_system.is_alchemizing = True
    ctx.alchemy_system.last_alchemy_report_time = current_time
    
    ctx.db_data["alchemy_system"] = ctx.alchemy_system.to_dict()
    
    ctx.player_data.data = ctx.db_data
    ctx.player_data.last_online_at = datetime.now(timezone.utc)
    await ctx.player_data.save()
    
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
async def report_alchemy(
    request: AlchemyReportRequest,
    ctx: GameContext = Depends(get_game_context),
    token_info: dict = Depends(get_token_info)
):
    """炼丹上报"""
    start_time = time.time()
    logger.info(f"[IN] POST /game/alchemy/report - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token_info['token']} - account_id: {token_info['account_id']} - token_version: {token_info['token_version']}")
    
    if not ctx.alchemy_system.is_alchemizing:
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
    craft_time = AlchemyWorkshop.calculate_craft_time(ctx.alchemy_system, request.recipe_id, ctx.spell_system)
    
    actual_interval = current_time - ctx.alchemy_system.last_alchemy_report_time
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
        ctx.alchemy_system, request.recipe_id, request.count, ctx.player, ctx.spell_system, ctx.inventory_system
    )
    
    if result["success"]:
        ctx.alchemy_system.last_alchemy_report_time = current_time
        
        ctx.db_data["player"] = ctx.player.to_dict()
        ctx.db_data["inventory"] = ctx.inventory_system.to_dict()
        ctx.db_data["alchemy_system"] = ctx.alchemy_system.to_dict()
        
        ctx.player_data.data = ctx.db_data
        ctx.player_data.last_online_at = datetime.now(timezone.utc)
        await ctx.player_data.save()
    
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
async def stop_alchemy(
    request: AlchemyStopRequest,
    ctx: GameContext = Depends(get_game_context),
    token_info: dict = Depends(get_token_info)
):
    """停止炼丹"""
    start_time = time.time()
    logger.info(f"[IN] POST /game/alchemy/stop - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token_info['token']} - account_id: {token_info['account_id']} - token_version: {token_info['token_version']}")
    
    if not ctx.alchemy_system.is_alchemizing:
        response_data = AlchemyStopResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            is_alchemizing=False,
            message="当前未在炼丹状态"
        )
        logger.info(f"[OUT] POST /game/alchemy/stop - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    ctx.alchemy_system.is_alchemizing = False
    ctx.alchemy_system.last_alchemy_report_time = 0.0
    
    ctx.db_data["alchemy_system"] = ctx.alchemy_system.to_dict()
    
    ctx.player_data.data = ctx.db_data
    ctx.player_data.last_online_at = datetime.now(timezone.utc)
    await ctx.player_data.save()
    
    response_data = AlchemyStopResponse(
        success=True,
        operation_id=request.operation_id,
        timestamp=request.timestamp,
        is_alchemizing=False,
        message="停止炼丹"
    )
    logger.info(f"[OUT] POST /game/alchemy/stop - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data
