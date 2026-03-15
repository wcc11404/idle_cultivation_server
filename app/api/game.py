from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas.game import SaveGameRequest, SaveGameResponse, LoadGameResponse, BreakthroughRequest, BreakthroughResponse, UseItemRequest, UseItemResponse, BattleVictoryRequest, BattleVictoryResponse
from app.db.models import Account, PlayerData
from app.core.security import decode_token
from app.core.config_loader import get_initial_player_data
from app.core.logger import logger
from datetime import datetime
import random
import time

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
    
    logger.info(f"[AUTH] 认证成功 - account_id: {account_id}")
    return account


@router.get("/data", response_model=LoadGameResponse)
async def load_game(current_user: Account = Depends(get_current_user)):
    """加载游戏数据"""
    start_time = time.time()
    logger.info(f"[IN] GET /game/data - account_id: {current_user.id}")
    
    player_data = await PlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        logger.info(f"[GAME] 首次加载，创建初始数据 - account_id: {current_user.id}")
        initial_data = get_initial_player_data(str(current_user.id))
        player_data = await PlayerData.create(
            account_id=current_user.id,
            data=initial_data
        )
    
    logger.info(f"[OUT] GET /game/data - 加载成功 - account_id: {current_user.id} - 耗时: {time.time() - start_time:.4f}s")
    return LoadGameResponse(
        success=True,
        data=player_data.data
    )


@router.post("/save", response_model=SaveGameResponse)
async def save_game(request: SaveGameRequest, current_user: Account = Depends(get_current_user)):
    """保存游戏数据"""
    start_time = time.time()
    logger.info(f"[IN] POST /game/save - account_id: {current_user.id}")
    
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
    
    logger.info(f"[OUT] POST /game/save - 保存成功 - account_id: {current_user.id} - 耗时: {time.time() - start_time:.4f}s")
    return SaveGameResponse(
        success=True,
        last_online_at=int(player_data.updated_at.timestamp())
    )


@router.post("/player/breakthrough", response_model=BreakthroughResponse)
async def breakthrough(request: BreakthroughRequest, current_user: Account = Depends(get_current_user)):
    """突破境界"""
    start_time = time.time()
    logger.info(f"[IN] POST /game/player/breakthrough - account_id: {current_user.id} - current_realm: {request.current_realm} - current_level: {request.current_level}")
    
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
    
    logger.info(f"[OUT] POST /game/player/breakthrough - 突破成功 - account_id: {current_user.id} - new_realm: {new_realm} - new_level: {new_level} - 耗时: {time.time() - start_time:.4f}s")
    return BreakthroughResponse(
        success=True,
        new_realm=new_realm,
        new_level=new_level,
        remaining_spirit_energy=0.0,
        materials_used=materials_used
    )


@router.post("/inventory/use_item", response_model=UseItemResponse)
async def use_item(request: UseItemRequest, current_user: Account = Depends(get_current_user)):
    """使用物品"""
    start_time = time.time()
    logger.info(f"[IN] POST /game/inventory/use_item - account_id: {current_user.id} - item_id: {request.item_id}")
    
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
    
    logger.info(f"[OUT] POST /game/inventory/use_item - 使用成功 - account_id: {current_user.id} - item_id: {request.item_id} - 耗时: {time.time() - start_time:.4f}s")
    return UseItemResponse(
        success=True,
        effect=effect,
        contents=contents
    )


@router.post("/battle/victory", response_model=BattleVictoryResponse)
async def battle_victory(request: BattleVictoryRequest, current_user: Account = Depends(get_current_user)):
    """战斗胜利"""
    start_time = time.time()
    logger.info(f"[IN] POST /game/battle/victory - account_id: {current_user.id} - is_tower: {request.is_tower} - tower_floor: {request.tower_floor if request.is_tower else 'N/A'}")
    
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
    
    logger.info(f"[OUT] POST /game/battle/victory - 战斗胜利 - account_id: {current_user.id} - 掉落: {len(loot)} 件物品 - 耗时: {time.time() - start_time:.4f}s")
    return BattleVictoryResponse(
        success=True,
        loot=loot,
        new_highest_floor=new_highest_floor
    )