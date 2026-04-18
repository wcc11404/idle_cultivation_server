"""
炼丹相关 API

包含炼制丹药相关功能
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from app.schemas.game import (
    AlchemyRecipesResponse,
    AlchemyStartRequest, AlchemyStartResponse,
    AlchemyReportRequest, AlchemyReportResponse,
    AlchemyStopRequest, AlchemyStopResponse
)
from app.db.Models import PlayerData as DBPlayerData
from app.core.Security import get_current_user, decode_token, security
from app.core.Dependencies import get_game_context, get_write_game_context, get_token_info, GameContext
from app.core.Logger import logger
from app.core.AntiCheatSystem import AntiCheatSystem
from app.modules import PlayerSystem, AlchemySystem, RecipeData, SpellSystem, InventorySystem, LianliSystem
from .AlchemyWorkshop import AlchemyWorkshop
from datetime import datetime, timezone
import time
import json

router = APIRouter()


@router.get("/alchemy/recipes", response_model=AlchemyRecipesResponse)
async def get_recipes(
    ctx: GameContext = Depends(get_game_context),
    token_info: dict = Depends(get_token_info)
):
    """获取丹方列表"""
    start_time = time.time()
    logger.info(f"[IN] GET /game/alchemy/recipes - token: {token_info['token']} - account_id: {token_info['account_id']} - token_version: {token_info['token_version']}")
    
    learned_recipes = ctx.alchemy_system.get_learned_recipes()
    
    response_data = AlchemyRecipesResponse(
        success=True,
        operation_id="",
        timestamp=time.time(),
        reason_code="ALCHEMY_RECIPES_SUCCEEDED",
        reason_data={},
        learned_recipes=learned_recipes,
        recipes_config=RecipeData.get_recipes_config()
    )
    logger.info(f"[OUT] GET /game/alchemy/recipes - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/alchemy/start", response_model=AlchemyStartResponse)
async def start_alchemy(
    request: AlchemyStartRequest,
    ctx: GameContext = Depends(get_write_game_context),
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
            reason_code="ALCHEMY_START_ALREADY_ACTIVE",
            reason_data={}
        )
        logger.info(f"[OUT] POST /game/alchemy/start - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    if ctx.player.is_cultivating:
        response_data = AlchemyStartResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            reason_code="ALCHEMY_START_BLOCKED_BY_CULTIVATION",
            reason_data={}
        )
        logger.info(f"[OUT] POST /game/alchemy/start - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    if ctx.lianli_system.is_battling:
        response_data = AlchemyStartResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            reason_code="ALCHEMY_START_BLOCKED_BY_BATTLE",
            reason_data={}
        )
        logger.info(f"[OUT] POST /game/alchemy/start - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    current_time = time.time()
    ctx.alchemy_system.is_alchemizing = True
    ctx.alchemy_system.last_alchemy_report_time = current_time
    await AntiCheatSystem.reset_suspicious_operations(
        account_id=str(ctx.account.id),
        account_system=ctx.account_system,
        db_player_data=ctx.player_data
    )
    
    ctx.db_data["alchemy_system"] = ctx.alchemy_system.to_dict()
    ctx.db_data["account_info"] = ctx.account_system.to_dict()
    
    ctx.player_data.data = ctx.db_data
    ctx.player_data.last_online_at = datetime.now(timezone.utc)
    await ctx.player_data.save()
    
    response_data = AlchemyStartResponse(
        success=True,
        operation_id=request.operation_id,
        timestamp=request.timestamp,
        reason_code="ALCHEMY_START_SUCCEEDED",
        reason_data={}
    )
    logger.info(f"[OUT] POST /game/alchemy/start - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/alchemy/report", response_model=AlchemyReportResponse)
async def report_alchemy(
    request: AlchemyReportRequest,
    ctx: GameContext = Depends(get_write_game_context),
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
            reason_code="ALCHEMY_REPORT_NOT_ACTIVE",
            reason_data={},
            success_count=0,
            fail_count=0,
            products={},
            returned_materials={}
        )
        logger.info(f"[OUT] POST /game/alchemy/report - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    recipe_config = RecipeData.get_recipe(request.recipe_id)
    if not recipe_config:
        response_data = AlchemyReportResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            reason_code="ALCHEMY_REPORT_RECIPE_NOT_FOUND",
            reason_data={"recipe_id": request.recipe_id},
            success_count=0,
            fail_count=0,
            products={},
            returned_materials={}
        )
        logger.info(f"[OUT] POST /game/alchemy/report - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    current_time = time.time()
    craft_time = AlchemyWorkshop.calculate_craft_time(ctx.alchemy_system, request.recipe_id, ctx.spell_system)
    
    actual_interval = current_time - ctx.alchemy_system.last_alchemy_report_time
    expected_interval = request.count * craft_time
    min_allowed_interval = expected_interval * 0.9
    
    if actual_interval < min_allowed_interval:
        anti_cheat_result = await AntiCheatSystem.record_suspicious_operation(
            account_id=str(ctx.account.id),
            operation_type="alchemy_report",
            detail=(
                f"上报次数{request.count}，配方{request.recipe_id}，"
                f"实际间隔{actual_interval:.2f}s，小于最小允许{min_allowed_interval:.2f}s"
            ),
            account_system=ctx.account_system,
            db_player_data=ctx.player_data,
            db_account=ctx.account
        )
        response_data = AlchemyReportResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            reason_code="ALCHEMY_REPORT_TIME_INVALID",
            reason_data={
                "recipe_id": request.recipe_id,
                "reported_count": request.count,
                "actual_interval": round(actual_interval, 2),
                "min_allowed_interval": round(min_allowed_interval, 2),
                "invalid_report_count": anti_cheat_result.get("invalid_count", 0),
                "kicked_out": bool(anti_cheat_result.get("kicked_out", False)),
                "kick_threshold": anti_cheat_result.get("threshold", 10),
            },
            success_count=0,
            fail_count=0,
            products={},
            returned_materials={}
        )
        logger.info(f"[OUT] POST /game/alchemy/report - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    result = AlchemyWorkshop.craft_pills(
        ctx.alchemy_system, request.recipe_id, request.count, ctx.player, ctx.spell_system, ctx.inventory_system
    )
    
    if result["success"]:
        await AntiCheatSystem.reset_suspicious_operations(
            account_id=str(ctx.account.id),
            account_system=ctx.account_system,
            db_player_data=ctx.player_data
        )
        ctx.alchemy_system.last_alchemy_report_time = current_time
        
        ctx.db_data["player"] = ctx.player.to_dict()
        ctx.db_data["inventory"] = ctx.inventory_system.to_dict()
        ctx.db_data["alchemy_system"] = ctx.alchemy_system.to_dict()
        ctx.db_data["account_info"] = ctx.account_system.to_dict()
        
        ctx.player_data.data = ctx.db_data
        ctx.player_data.last_online_at = datetime.now(timezone.utc)
        await ctx.player_data.save()
    
    response_data = AlchemyReportResponse(
        success=result["success"],
        operation_id=request.operation_id,
        timestamp=request.timestamp,
        reason_code=result.get("reason_code", ""),
        reason_data=result.get("reason_data", {}),
        success_count=result.get("success_count", 0),
        fail_count=result.get("fail_count", 0),
        products=result.get("products", {}),
        returned_materials=result.get("returned_materials", {})
    )
    logger.info(f"[OUT] POST /game/alchemy/report - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/alchemy/stop", response_model=AlchemyStopResponse)
async def stop_alchemy(
    request: AlchemyStopRequest,
    ctx: GameContext = Depends(get_write_game_context),
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
            reason_code="ALCHEMY_STOP_NOT_ACTIVE",
            reason_data={}
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
        reason_code="ALCHEMY_STOP_SUCCEEDED",
        reason_data={}
    )
    logger.info(f"[OUT] POST /game/alchemy/stop - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data
