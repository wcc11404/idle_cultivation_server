"""
背包相关 API

包含使用物品、打开物品、扩容、整理、丢弃等功能
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from app.schemas.game import (
    UseItemRequest, UseItemResponse,
    OrganizeInventoryRequest, OrganizeInventoryResponse,
    DiscardItemRequest,
    ExpandInventoryRequest, ExpandInventoryResponse,
    InventoryListResponse
)
from app.db.Models import PlayerData as DBPlayerData
from app.core.Security import get_current_user, decode_token, security
from app.core.Dependencies import get_game_context, get_write_game_context, get_token_info, GameContext
from app.core.Logger import logger
from app.modules import PlayerSystem, InventorySystem, SpellSystem, AlchemySystem
from datetime import datetime, timezone
import time
import json

router = APIRouter()


@router.post("/inventory/use", response_model=UseItemResponse)
async def use_item(
    request: UseItemRequest,
    ctx: GameContext = Depends(get_write_game_context),
    token_info: dict = Depends(get_token_info)
):
    """使用物品"""
    start_time = time.time()
    logger.info(f"[IN] POST /game/inventory/use - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token_info['token']} - account_id: {token_info['account_id']} - token_version: {token_info['token_version']}")
    
    result = ctx.inventory_system.use_item(request.item_id, ctx.player, ctx.spell_system, ctx.alchemy_system)
    
    if result["success"]:
        ctx.db_data["player"] = ctx.player.to_dict()
        ctx.db_data["inventory"] = ctx.inventory_system.to_dict()
        ctx.db_data["spell_system"] = ctx.spell_system.to_dict()
        ctx.db_data["alchemy_system"] = ctx.alchemy_system.to_dict()
        
        ctx.player_data.data = ctx.db_data
        ctx.player_data.last_online_at = datetime.now(timezone.utc)
        await ctx.player_data.save()
        
        logger.info(f"[GAME] 使用物品成功 - account_id: {ctx.account.id} - item_id: {request.item_id}")
    
    response_data = UseItemResponse(
        success=result["success"],
        operation_id=request.operation_id,
        timestamp=request.timestamp,
        reason_code=result.get("reason_code", ""),
        reason_data=result.get("reason_data", {})
    )
    logger.info(f"[OUT] POST /game/inventory/use - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/inventory/organize", response_model=OrganizeInventoryResponse)
async def organize_inventory(
    request: OrganizeInventoryRequest,
    ctx: GameContext = Depends(get_write_game_context),
    token_info: dict = Depends(get_token_info)
):
    """整理背包"""
    start_time = time.time()
    logger.info(f"[IN] POST /game/inventory/organize - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token_info['token']} - account_id: {token_info['account_id']} - token_version: {token_info['token_version']}")
    
    result = ctx.inventory_system.organize_inventory()
    
    if result["success"]:
        ctx.db_data["inventory"] = ctx.inventory_system.to_dict()
        
        ctx.player_data.data = ctx.db_data
        ctx.player_data.last_online_at = datetime.now(timezone.utc)
        await ctx.player_data.save()
        
        logger.info(f"[GAME] 整理背包成功 - account_id: {ctx.account.id}")
    
    response_data = OrganizeInventoryResponse(
        success=result["success"],
        operation_id=request.operation_id,
        timestamp=request.timestamp,
        reason_code=result.get("reason_code", ""),
        reason_data=result.get("reason_data", {})
    )
    logger.info(f"[OUT] POST /game/inventory/organize - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/inventory/discard", response_model=dict)
async def discard_item(
    request: DiscardItemRequest,
    ctx: GameContext = Depends(get_write_game_context),
    token_info: dict = Depends(get_token_info)
):
    """丢弃物品"""
    start_time = time.time()
    logger.info(f"[IN] POST /game/inventory/discard - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token_info['token']} - account_id: {token_info['account_id']} - token_version: {token_info['token_version']}")
    
    result = ctx.inventory_system.discard_item(request.item_id, request.count)
    
    if result["success"]:
        ctx.db_data["inventory"] = ctx.inventory_system.to_dict()
        
        ctx.player_data.data = ctx.db_data
        ctx.player_data.last_online_at = datetime.now(timezone.utc)
        await ctx.player_data.save()
        
        logger.info(f"[GAME] 丢弃物品成功 - account_id: {ctx.account.id} - item_id: {request.item_id}")
    
    response_data = {
        "success": result["success"],
        "operation_id": request.operation_id,
        "timestamp": request.timestamp,
        "reason_code": result.get("reason_code", ""),
        "reason_data": result.get("reason_data", {})
    }
    logger.info(f"[OUT] POST /game/inventory/discard - {json.dumps(response_data, ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/inventory/expand", response_model=ExpandInventoryResponse)
async def expand_inventory(
    request: ExpandInventoryRequest,
    ctx: GameContext = Depends(get_write_game_context),
    token_info: dict = Depends(get_token_info)
):
    """扩容背包"""
    start_time = time.time()
    logger.info(f"[IN] POST /game/inventory/expand - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token_info['token']} - account_id: {token_info['account_id']} - token_version: {token_info['token_version']}")
    
    result = ctx.inventory_system.expand_capacity()
    
    if result["success"]:
        ctx.db_data["inventory"] = ctx.inventory_system.to_dict()
        
        ctx.player_data.data = ctx.db_data
        ctx.player_data.last_online_at = datetime.now(timezone.utc)
        await ctx.player_data.save()
        
        logger.info(
            f"[GAME] 扩容背包成功 - account_id: {ctx.account.id} - "
            f"new_capacity: {result.get('reason_data', {}).get('new_capacity', 0)}"
        )
    
    response_data = ExpandInventoryResponse(
        success=result["success"],
        operation_id=request.operation_id,
        timestamp=request.timestamp,
        reason_code=result.get("reason_code", ""),
        reason_data=result.get("reason_data", {})
    )
    logger.info(f"[OUT] POST /game/inventory/expand - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.get("/inventory/list", response_model=InventoryListResponse)
async def get_inventory_list(
    ctx: GameContext = Depends(get_game_context),
    token_info: dict = Depends(get_token_info)
):
    """获取背包列表"""
    start_time = time.time()
    logger.info(f"[IN] GET /game/inventory/list - token: {token_info['token']} - account_id: {token_info['account_id']} - token_version: {token_info['token_version']}")
    
    response_data = InventoryListResponse(
        success=True,
        operation_id="",
        timestamp=time.time(),
        reason_code="INVENTORY_LIST_SUCCEEDED",
        reason_data={},
        inventory=ctx.inventory_system.to_dict()
    )
    logger.info(f"[OUT] GET /game/inventory/list - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data
