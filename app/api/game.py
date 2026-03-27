from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas.game import SaveGameRequest, SaveGameResponse, LoadGameResponse, BreakthroughRequest, BreakthroughResponse, UseItemRequest, UseItemResponse, BattleVictoryRequest, BattleVictoryResponse, DungeonInfoResponse, EnterDungeonRequest, EnterDungeonResponse, RankResponse, RankItem
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
    
    return account


@router.get("/data", response_model=LoadGameResponse)
async def load_game(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """加载游戏数据"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] GET /game/data - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
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
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] POST /game/save - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
    player_data = await PlayerData.get_or_none(account_id=current_user.id)
    
    # 允许更新的字段列表
    allowed_fields = ["account_info", "player", "inventory", "spell_system", "alchemy_system", "lianli_system"]
    
    # 不做数据类型转换，由客户端保证数据类型的正确性
    game_data = request.data
    
    if not player_data:
        # 创建新数据
        logger.info(f"[GAME] 首次保存，创建数据 - account_id: {current_user.id}")
        player_data = await PlayerData.create(
            account_id=current_user.id,
            data=game_data
        )
    else:
        # 更新数据 - 字段级别更新
        existing_data = player_data.data
        
        # 遍历入参中的字段，只更新允许的字段
        for field in allowed_fields:
            if field in game_data:
                if field == "lianli_system":
                    # lianli_system 特殊处理：保留 daily_dungeon_data
                    if "lianli_system" not in existing_data:
                        existing_data["lianli_system"] = {}
                    
                    # 保存原有的 daily_dungeon_data
                    original_daily_dungeon = existing_data["lianli_system"].get("daily_dungeon_data", {})
                    
                    # 更新 lianli_system 的其他字段
                    for sub_field in game_data["lianli_system"]:
                        if sub_field != "daily_dungeon_data":
                            existing_data["lianli_system"][sub_field] = game_data["lianli_system"][sub_field]
                    
                    # 恢复原有的 daily_dungeon_data
                    existing_data["lianli_system"]["daily_dungeon_data"] = original_daily_dungeon
                else:
                    # 其他字段直接更新
                    existing_data[field] = game_data[field]
        
        player_data.data = existing_data
        player_data.last_online_at = datetime.now(timezone.utc)
        await player_data.save()
    
    response_data = SaveGameResponse(
        success=True,
        last_online_at=int(player_data.last_online_at.timestamp())
    )
    logger.info(f"[OUT] POST /game/save - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时: {time.time() - start_time:.4f}s")
    return response_data


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
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] POST /game/inventory/use_item - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
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
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] POST /game/battle/victory - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
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
                player_data.last_online_at = datetime.now(timezone.utc)
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
async def claim_offline_reward(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """领取离线奖励"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] POST /game/claim_offline_reward - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
    # 获取玩家数据
    player_data = await PlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        initial_data = get_initial_player_data(str(current_user.id))
        player_data = await PlayerData.create(
            account_id=current_user.id,
            data=initial_data
        )
    
    # 计算离线时间
    current_time = datetime.now(timezone.utc)
    last_online_time = player_data.last_online_at
    
    # 检查是否是第一次登录（last_online_at 为 epoch 时间0）
    epoch_time = datetime.fromtimestamp(0, timezone.utc)
    if last_online_time == epoch_time:
        # 第一次登录，不计算离线奖励
        offline_seconds = 0
    else:
        # 正常计算离线时间
        offline_seconds = int((current_time - last_online_time).total_seconds())
    
    # 验证离线时间合理性
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
    
    # 计算奖励
    # 与客户端计算方式对齐
    
    # 灵气获取速度：默认1.0每秒
    spirit_per_second = 1.0
    # 可以根据玩家境界调整灵气获取速度
    player_realm = player_data.data.get("player", {}).get("realm", "")
    # 简单的境界加成
    realm_bonus = 1.0
    if player_realm == "筑基期":
        realm_bonus = 1.5
    elif player_realm == "金丹期":
        realm_bonus = 2.0
    spirit_per_second *= realm_bonus
    
    # 效率固定为1.0
    efficiency = 1.0
    
    # 计算灵气
    total_spirit = spirit_per_second * offline_seconds * efficiency
    
    # 灵气上限：最大灵气值 × 60
    max_spirit = player_data.data.get("player", {}).get("max_spirit_energy", 100) * 60
    total_spirit = min(total_spirit, max_spirit)
    
    # 计算灵石：1每分钟
    offline_minutes = offline_seconds / 60.0
    total_minutes = int(offline_minutes)
    stone_per_minute = 1.0
    total_stone = int(stone_per_minute * total_minutes)
    
    # 处理灵气格式：保留两位小数，去除尾零
    total_spirit = round(float(total_spirit), 2)
    if total_spirit.is_integer():
        total_spirit = int(total_spirit)
    
    offline_reward = {
        "spirit_energy": total_spirit,
        "spirit_stones": total_stone
    }
    
    # 应用奖励到玩家数据
    if offline_seconds > 60:
        # 处理灵气奖励（浮点数）
        player_data.data["player"]["spirit_energy"] += float(offline_reward["spirit_energy"])
        # 保留两位小数并去除尾零
        player_data.data["player"]["spirit_energy"] = round(player_data.data["player"]["spirit_energy"], 2)
        if player_data.data["player"]["spirit_energy"].is_integer():
            player_data.data["player"]["spirit_energy"] = int(player_data.data["player"]["spirit_energy"])
        
        # 处理灵石奖励（整数）
        if "spirit_stones" in player_data.data["inventory"]["slots"]:
            current_stones = player_data.data["inventory"]["slots"]["spirit_stones"]
            # 确保是整数类型
            if isinstance(current_stones, str):
                current_stones = int(current_stones)
            player_data.data["inventory"]["slots"]["spirit_stones"] = current_stones + offline_reward["spirit_stones"]
        else:
            player_data.data["inventory"]["slots"]["spirit_stones"] = offline_reward["spirit_stones"]
    
    # 更新最后在线时间
    player_data.last_online_at = datetime.now(timezone.utc)
    
    if offline_seconds <= 60:
        response_data = {
            "success": True,
            "offline_reward": None,
            "offline_seconds": offline_seconds,
            "last_online_at": int(player_data.last_online_at.timestamp()),
            "message": "离线时间不足，无法领取奖励"
        }
    else:
        response_data = {
            "success": True,
            "offline_reward": offline_reward,
            "offline_seconds": offline_seconds,
            "last_online_at": int(player_data.last_online_at.timestamp()),
            "message": "领取成功"
        }
    logger.info(f"[OUT] POST /game/claim_offline_reward - {json.dumps(response_data, ensure_ascii=False)} - 耗时: {time.time() - start_time:.4f}s")
    return response_data


@router.get("/dungeon/info", response_model=DungeonInfoResponse)
async def get_dungeon_info(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取副本信息"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] GET /game/dungeon/info - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
    # 获取玩家数据
    player_data = await PlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        initial_data = get_initial_player_data(str(current_user.id))
        player_data = await PlayerData.create(
            account_id=current_user.id,
            data=initial_data
        )
    
    # 获取副本数据
    dungeon_data = player_data.data.get("lianli_system", {}).get("daily_dungeon_data", {})
    
    response_data = DungeonInfoResponse(
        success=True,
        dungeon_data=dungeon_data
    )
    logger.info(f"[OUT] GET /game/dungeon/info - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时: {time.time() - start_time:.4f}s")
    return response_data


@router.post("/dungeon/finish", response_model=EnterDungeonResponse)
async def finish_dungeon(request: EnterDungeonRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """完成副本（扣减次数）"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] POST /game/dungeon/finish - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
    # 获取玩家数据
    player_data = await PlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        initial_data = get_initial_player_data(str(current_user.id))
        player_data = await PlayerData.create(
            account_id=current_user.id,
            data=initial_data
        )
    
    # 检查副本数据
    lianli_system = player_data.data.get("lianli_system", {})
    daily_dungeon_data = lianli_system.get("daily_dungeon_data", {})
    dungeon_info = daily_dungeon_data.get(request.dungeon_id)
    
    if not dungeon_info:
        logger.warning(f"[OUT] POST /game/dungeon/enter - DUNGEON_NOT_FOUND - account_id: {current_user.id} - dungeon_id: {request.dungeon_id} - 耗时: {time.time() - start_time:.4f}s")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="副本不存在"
        )
    
    # 检查剩余次数
    remaining_count = dungeon_info.get("remaining_count", 0)
    if remaining_count <= 0:
        response_data = EnterDungeonResponse(
            success=False,
            remaining_count=0,
            message="副本次数已用完"
        )
        logger.info(f"[OUT] POST /game/dungeon/finish - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时: {time.time() - start_time:.4f}s")
        return response_data
    
    # 扣减次数
    dungeon_info["remaining_count"] = remaining_count - 1
    player_data.last_online_at = datetime.now(timezone.utc)
    await player_data.save()
    
    response_data = EnterDungeonResponse(
        success=True,
        remaining_count=dungeon_info["remaining_count"],
        message="完成副本成功"
    )
    logger.info(f"[OUT] POST /game/dungeon/finish - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时: {time.time() - start_time:.4f}s")
    return response_data


@router.get("/rank", response_model=RankResponse)
async def get_rank(server_id: str = "default"):
    """获取排行榜"""
    start_time = time.time()
    logger.info(f"[IN] GET /game/rank - server_id: {server_id}")
    
    # 获取所有玩家数据
    accounts = await Account.filter(server_id=server_id).all()
    
    # 构建排行榜数据
    rank_data = []
    for account in accounts:
        player_data = await PlayerData.get_or_none(account_id=account.id)
        if player_data:
            # 从account_info获取nickname和title_id
            account_info = player_data.data.get("account_info", {})
            nickname = account_info.get("nickname", "")
            title_id = account_info.get("title_id", "")
            
            # 从player获取其他数据
            player = player_data.data.get("player", {})
            realm = player.get("realm", "")
            level = player.get("realm_level", 0)
            spirit_energy = player.get("spirit_energy", 0.0)
            
            # 转换spirit_energy为浮点数
            if isinstance(spirit_energy, str):
                spirit_energy = float(spirit_energy)
            
            rank_data.append({
                "nickname": nickname,
                "realm": realm,
                "level": level,
                "spirit_energy": spirit_energy,
                "title_id": title_id,
                "created_at": account.created_at
            })
    
    # 按照境界和层数排序
    # 这里需要一个境界优先级映射
    realm_priority = {
        "练气期": 1,
        "筑基期": 2,
        "金丹期": 3,
        "元婴期": 4,
        "化神期": 5,
        "炼虚期": 6,
        "合体期": 7,
        "大乘期": 8,
        "渡劫期": 9
    }
    
    # 排序逻辑：先按境界优先级倒序，再按层数倒序，再按灵气倒序，最后按创建时间正序（创建时间早的排前面）
    rank_data.sort(key=lambda x: (
        -realm_priority.get(x["realm"], 0),  # 境界优先级倒序
        -x["level"],  # 层数倒序
        -x["spirit_energy"],  # 灵气倒序
        x["created_at"]  # 创建时间正序
    ))
    
    # 构建排行榜响应，最多返回前20个记录
    ranks = []
    for i, item in enumerate(rank_data[:20], 1):  # 限制最多20个记录
        ranks.append(RankItem(
            nickname=item["nickname"],
            realm=item["realm"],
            level=item["level"],
            spirit_energy=item["spirit_energy"],
            title_id=item["title_id"],
            rank=i
        ))
    
    response_data = RankResponse(
        success=True,
        ranks=ranks
    )
    logger.info(f"[OUT] GET /game/rank - 排行数量: {len(ranks)} - 耗时: {time.time() - start_time:.4f}s")
    return response_data