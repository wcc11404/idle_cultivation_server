from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas.game import SaveGameRequest, SaveGameResponse, LoadGameResponse, BreakthroughRequest, BreakthroughResponse, UseItemRequest, UseItemResponse, BattleVictoryRequest, BattleVictoryResponse
from app.db.models import Account, PlayerData
from app.core.security import decode_token
from app.core.config_loader import get_initial_player_data
from app.core.logger import logger
from datetime import datetime, timezone
import random
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
        logger.warning(f"[AUTH] KICKED_OUT - account_id: {account_id} - token_version_from_token: {token_version} - token_version_in_db: {account.token_version}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="KICKED_OUT"
        )
    
    logger.info(f"[AUTH] 认证成功 - account_id: {account_id}")
    return account


@router.get("/data", response_model=LoadGameResponse)
async def load_game(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """加载游戏数据"""
    start_time = time.time()
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] GET /game/data - token: {credentials.credentials}")
    
    player_data = await PlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        logger.info(f"[GAME] 首次加载，创建初始数据 - account_id: {current_user.id}")
        initial_data = get_initial_player_data(str(current_user.id))
        player_data = await PlayerData.create(
            account_id=current_user.id,
            data=initial_data
        )
    
    response_data = LoadGameResponse(
        success=True,
        data=player_data.data
    )
    logger.info(f"[OUT] GET /game/data - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时: {time.time() - start_time:.4f}s")
    return response_data


@router.post("/save", response_model=SaveGameResponse)
async def save_game(request: SaveGameRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """保存游戏数据"""
    start_time = time.time()
    token = credentials.credentials
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] POST /game/save - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token}")
    
    player_data = await PlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        # 创建新数据
        logger.info(f"[GAME] 首次保存，创建数据 - account_id: {current_user.id}")
        player_data = await PlayerData.create(
            account_id=current_user.id,
            data=request.data
        )
    else:
        # 更新数据
        player_data.data = request.data
        await player_data.save()
    
    response_data = SaveGameResponse(
        success=True,
        last_online_at=int(player_data.updated_at.timestamp())
    )
    logger.info(f"[OUT] POST /game/save - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时: {time.time() - start_time:.4f}s")
    return response_data


@router.post("/player/breakthrough", response_model=BreakthroughResponse)
async def breakthrough(request: BreakthroughRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """突破境界"""
    start_time = time.time()
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] POST /game/player/breakthrough - {json.dumps(request.dict(), ensure_ascii=False)} - token: {credentials.credentials}")
    
    # 这里可以添加突破逻辑验证
    # 简化实现，直接返回成功
    new_realm = request.current_realm
    new_level = request.current_level + 1
    
    # 模拟突破消耗材料
    materials_used = {}
    if new_level > 10:
        new_realm = "筑基期"
        new_level = 1
        materials_used = {"spirit_stone": 100}
    
    response_data = BreakthroughResponse(
        success=True,
        new_realm=new_realm,
        new_level=new_level,
        remaining_spirit_energy=0.0,
        materials_used=materials_used
    )
    logger.info(f"[OUT] POST /game/player/breakthrough - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时: {time.time() - start_time:.4f}s")
    return response_data


@router.post("/inventory/use_item", response_model=UseItemResponse)
async def use_item(request: UseItemRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """使用物品"""
    start_time = time.time()
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] POST /game/inventory/use_item - {json.dumps(request.dict(), ensure_ascii=False)} - token: {credentials.credentials}")
    
    # 简化实现，直接返回成功
    effect = {}
    contents = None
    
    if request.item_id == "starter_pack":
        contents = {
            "spirit_stone": 100,
            "health_pill": 5
        }
    elif request.item_id == "health_pill":
        effect = {"health": 100}
    
    response_data = UseItemResponse(
        success=True,
        effect=effect,
        contents=contents
    )
    logger.info(f"[OUT] POST /game/inventory/use_item - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时: {time.time() - start_time:.4f}s")
    return response_data


@router.post("/battle/victory", response_model=BattleVictoryResponse)
async def battle_victory(request: BattleVictoryRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """战斗胜利"""
    start_time = time.time()
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] POST /game/battle/victory - {json.dumps(request.dict(), ensure_ascii=False)} - token: {credentials.credentials}")
    
    # 生成随机掉落
    loot = []
    if random.random() > 0.5:
        loot.append({"item_id": "spirit_stone", "amount": random.randint(10, 50)})
    if random.random() > 0.7:
        loot.append({"item_id": "health_pill", "amount": random.randint(1, 3)})
    
    # 检查是否是新的最高层
    new_highest_floor = None
    if request.is_tower:
        player_data = await PlayerData.get_or_none(account_id=current_user.id)
        if player_data:
            current_highest = player_data.data.get("lianli_system", {}).get("tower_highest_floor", 0)
            if request.tower_floor > current_highest:
                new_highest_floor = request.tower_floor
                # 更新最高层
                player_data.data["lianli_system"]["tower_highest_floor"] = new_highest_floor
                await player_data.save()
                logger.info(f"[GAME] 新的最高层 - account_id: {current_user.id} - floor: {new_highest_floor}")
    
    response_data = BattleVictoryResponse(
        success=True,
        loot=loot,
        new_highest_floor=new_highest_floor
    )
    logger.info(f"[OUT] POST /game/battle/victory - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时: {time.time() - start_time:.4f}s")
    return response_data


@router.post("/claim_offline_reward", response_model=dict)
async def claim_offline_reward(request: dict, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """领取离线奖励"""
    start_time = time.time()
    current_user = await get_current_user(credentials)
    offline_seconds = request.get("offline_seconds", 0)
    logger.info(f"[IN] POST /game/claim_offline_reward - {json.dumps(request, ensure_ascii=False)} - token: {credentials.credentials}")
    
    # 验证离线时间合理性
    if isinstance(offline_seconds, float):
        # 尝试将浮点数转换为整数
        offline_seconds = int(offline_seconds)
        logger.info(f"[IN] POST /game/claim_offline_reward - 自动转换离线时间为整数: {offline_seconds}")
    elif not isinstance(offline_seconds, int):
        logger.warning(f"[OUT] POST /game/claim_offline_reward - INVALID_OFFLINE_SECONDS_TYPE - account_id: {current_user.id} - offline_seconds: {offline_seconds} (type: {type(offline_seconds).__name__}) - 耗时: {time.time() - start_time:.4f}s")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="离线时间必须是整数或浮点数"
        )
    if offline_seconds < 0:
        logger.warning(f"[OUT] POST /game/claim_offline_reward - INVALID_OFFLINE_SECONDS_NEGATIVE - account_id: {current_user.id} - offline_seconds: {offline_seconds} - 耗时: {time.time() - start_time:.4f}s")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="离线时间不能为负数"
        )
    if offline_seconds > 4 * 3600:
        logger.warning(f"[OUT] POST /game/claim_offline_reward - INVALID_OFFLINE_SECONDS_TOO_LONG - account_id: {current_user.id} - offline_seconds: {offline_seconds} - 耗时: {time.time() - start_time:.4f}s")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="离线时间不能超过4小时（14400秒）"
        )
    
    player_data = await PlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        initial_data = get_initial_player_data(str(current_user.id))
        player_data = await PlayerData.create(
            account_id=current_user.id,
            data=initial_data
        )
    
    # 计算奖励
    offline_reward = {
        "spirit_energy": int(offline_seconds * 0.1),
        "spirit_stones": int(offline_seconds * 10 / 3600)
    }
    
    # 应用奖励到玩家数据
    if offline_seconds > 60:
        player_data.data["player"]["spirit_energy"] += offline_reward["spirit_energy"]
        if "spirit_stones" in player_data.data["inventory"]["slots"]:
            player_data.data["inventory"]["slots"]["spirit_stones"] += offline_reward["spirit_stones"]
        else:
            player_data.data["inventory"]["slots"]["spirit_stones"] = offline_reward["spirit_stones"]
    
    await player_data.save()
    
    if offline_seconds <= 60:
        response_data = {
            "success": True,
            "offline_reward": None,
            "offline_seconds": offline_seconds,
            "message": "离线时间不足，无法领取奖励"
        }
    else:
        response_data = {
            "success": True,
            "offline_reward": offline_reward,
            "offline_seconds": offline_seconds,
            "message": "领取成功"
        }
    logger.info(f"[OUT] POST /game/claim_offline_reward - {json.dumps(response_data, ensure_ascii=False)} - 耗时: {time.time() - start_time:.4f}s")
    return response_data