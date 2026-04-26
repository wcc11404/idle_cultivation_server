"""
游戏基础 API

包含加载、保存、离线奖励等基础功能
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from app.schemas.Game import (
    SaveGameRequest, SaveGameResponse, LoadGameResponse,
    ClaimOfflineRewardRequest, ClaimOfflineRewardResponse,
    RankResponse, RankItem
)
from app.db.Models import PlayerData, Account
from app.core.Security import get_current_user, decode_token, security
from app.core.InitPlayerInfo import create_initial_player_data_record
from app.core.Dependencies import get_game_context, get_write_game_context, get_token_info, GameContext
from app.core.Logger import logger
from app.modules.herb.HerbGatherSystem import HerbGatherSystem
from app.modules.task.TaskSystem import TaskSystem
from datetime import datetime, timezone
import time
import json
import os

router = APIRouter()


EPOCH_TIME = datetime.fromtimestamp(0, timezone.utc)


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
        player_data = await create_initial_player_data_record(current_user, EPOCH_TIME)
    else:
        migrated = False
        migrated_data = player_data.data
        if "herb_system" not in migrated_data:
            migrated_data["herb_system"] = HerbGatherSystem().to_dict()
            migrated = True
        if "task_system" not in migrated_data:
            migrated_data["task_system"] = TaskSystem().to_dict()
            migrated = True
        if migrated:
            player_data.data = migrated_data
            await player_data.save()
    
    response_data = LoadGameResponse(
        success=True,
        reason_code="GAME_LOAD_SUCCEEDED",
        reason_data={},
        data=player_data.data
    )
    logger.info(f"[OUT] GET /game/data - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/save", response_model=SaveGameResponse)
async def save_game(
    request: SaveGameRequest,
    ctx: GameContext = Depends(get_write_game_context),
    token_info: dict = Depends(get_token_info)
):
    """保存游戏数据"""
    start_time = time.time()
    token = token_info["token"]
    account_id = token_info["account_id"]
    token_version = token_info["token_version"]
    logger.info(f"[IN] POST /game/save - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token} - account_id: {account_id} - token_version: {token_version}")

    player_data = ctx.player_data
    
    allowed_fields = ["account_info", "player", "inventory", "spell_system", "alchemy_system", "lianli_system", "herb_system", "task_system"]
    
    game_data = request.data
    
    if not player_data:
        logger.info(f"[GAME] 首次保存，创建数据 - account_id: {ctx.account.id}")
        player_data = await PlayerData.create(
            account_id=ctx.account.id,
            data=game_data,
            last_online_at=EPOCH_TIME
        )
    else:
        existing_data = player_data.data
        
        for field in allowed_fields:
            if field in game_data:
                if field == "lianli_system":
                    if "lianli_system" not in existing_data:
                        existing_data["lianli_system"] = {}
                    
                    original_daily_dungeon = existing_data["lianli_system"].get("daily_dungeon_data", {})
                    
                    for sub_field in game_data["lianli_system"]:
                        if sub_field != "daily_dungeon_data":
                            existing_data["lianli_system"][sub_field] = game_data["lianli_system"][sub_field]
                    
                    existing_data["lianli_system"]["daily_dungeon_data"] = original_daily_dungeon
                else:
                    existing_data[field] = game_data[field]
        
        player_data.data = existing_data
        player_data.last_online_at = datetime.now(timezone.utc)
        await player_data.save()
    
    response_data = SaveGameResponse(
        success=True,
        operation_id=request.operation_id,
        timestamp=request.timestamp,
        reason_code="GAME_SAVE_SUCCEEDED",
        reason_data={},
        last_online_at=int(player_data.last_online_at.timestamp())
    )
    logger.info(f"[OUT] POST /game/save - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/claim_offline_reward", response_model=ClaimOfflineRewardResponse)
async def claim_offline_reward(
    request: ClaimOfflineRewardRequest,
    ctx: GameContext = Depends(get_write_game_context),
    token_info: dict = Depends(get_token_info)
):
    """领取离线奖励"""
    start_time = time.time()
    token = token_info["token"]
    account_id = token_info["account_id"]
    token_version = token_info["token_version"]
    logger.info(f"[IN] POST /game/claim_offline_reward - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
    current_time = datetime.now(timezone.utc)
    last_online_time = ctx.player_data.last_online_at
    
    if last_online_time == EPOCH_TIME:
        offline_seconds = 0
    else:
        offline_seconds = int((current_time - last_online_time).total_seconds())
    
    if offline_seconds < 0:
        logger.warning(f"[OUT] POST /game/claim_offline_reward - INVALID_OFFLINE_SECONDS_NEGATIVE - account_id: {account_id} - offline_seconds: {offline_seconds} - 耗时：{time.time() - start_time:.4f}s")
        response_data = ClaimOfflineRewardResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            reason_code="GAME_OFFLINE_REWARD_INVALID_TIME",
            reason_data={"offline_seconds": offline_seconds},
            offline_reward=None,
            offline_seconds=offline_seconds,
            last_online_at=int(ctx.player_data.last_online_at.timestamp())
        )
        logger.info(f"[OUT] POST /game/claim_offline_reward - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    max_offline_seconds = 4 * 3600
    if offline_seconds > max_offline_seconds:
        logger.info(
            f"[GAME] 离线奖励按上限结算 - account_id: {account_id} - "
            f"raw_offline_seconds: {offline_seconds} - capped_offline_seconds: {max_offline_seconds}"
        )
        offline_seconds = max_offline_seconds
    
    spirit_gain_speed = ctx.player.static_spirit_gain_speed if ctx.player else 1.0
    total_spirit = spirit_gain_speed * offline_seconds
    
    # 离线灵石：每 5 分钟结算 1 个
    total_stone = int(offline_seconds / 300)
    
    total_spirit = round(float(total_spirit), 2)
    if total_spirit.is_integer():
        total_spirit = int(total_spirit)
    
    offline_reward = {
        "spirit_energy": total_spirit,
        "spirit_stones": total_stone
    }
    
    if offline_seconds > 60:
        if ctx.player:
            ctx.player.add_spirit_energy(total_spirit)
        
        if ctx.inventory_system:
            ctx.inventory_system.add_item("spirit_stone", total_stone)
    
    ctx.player_data.last_online_at = current_time
    ctx.save()
    await ctx.player_data.save()
    
    if offline_seconds <= 60:
        response_data = ClaimOfflineRewardResponse(
            success=True,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            reason_code="GAME_OFFLINE_REWARD_SKIPPED_SHORT_OFFLINE",
            reason_data={},
            offline_reward=None,
            offline_seconds=offline_seconds,
            last_online_at=int(ctx.player_data.last_online_at.timestamp())
        )
    else:
        response_data = ClaimOfflineRewardResponse(
            success=True,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            reason_code="GAME_OFFLINE_REWARD_GRANTED",
            reason_data={},
            offline_reward=offline_reward,
            offline_seconds=offline_seconds,
            last_online_at=int(ctx.player_data.last_online_at.timestamp())
        )
    logger.info(f"[OUT] POST /game/claim_offline_reward - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


def _load_realm_config():
    """加载境界配置"""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "modules/cultivation/realms.json"
    )
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_realm_order(realm_name: str, realm_order: list) -> int:
    """获取境界排序值"""
    try:
        return realm_order.index(realm_name)
    except ValueError:
        return len(realm_order)


@router.get("/rank", response_model=RankResponse)
async def get_rank(server_id: str = "default"):
    """获取排行榜"""
    start_time = time.time()
    logger.info(f"[IN] GET /game/rank - server_id: {server_id}")
    
    realm_config = _load_realm_config()
    realm_order = realm_config.get("realm_order", [])
    
    all_players = await PlayerData.filter(server_id=server_id).all()
    
    rank_list = []
    for player_data in all_players:
        account = await Account.get_or_none(id=player_data.account_id)
        if not account or account.is_banned:
            continue
        
        player_info = player_data.data.get("player", {})
        account_info = player_data.data.get("account_info", {})
        
        realm = player_info.get("realm", "炼气期")
        level = player_info.get("realm_level", 1)
        spirit_energy = player_info.get("spirit_energy", 0)
        nickname = account_info.get("nickname", f"修仙者{str(player_data.account_id)[:6]}")
        title_id = account_info.get("title_id", "")
        
        rank_list.append({
            "realm": realm,
            "level": level,
            "spirit_energy": spirit_energy,
            "nickname": nickname,
            "title_id": title_id,
            "created_at": account.created_at
        })
    
    rank_list.sort(key=lambda x: (
        -_get_realm_order(x["realm"], realm_order),
        -x["level"],
        -x["spirit_energy"],
        x["created_at"]
    ))
    
    rank_items = []
    for index, item in enumerate(rank_list[:100], start=1):
        rank_items.append(RankItem(
            rank=index,
            nickname=item["nickname"],
            realm=item["realm"],
            level=item["level"],
            spirit_energy=item["spirit_energy"],
            title_id=item["title_id"]
        ))
    
    response_data = RankResponse(
        success=True,
        operation_id="",
        timestamp=time.time(),
        reason_code="GAME_RANK_SUCCEEDED",
        reason_data={},
        ranks=rank_items
    )
    logger.info(f"[OUT] GET /game/rank - 返回{len(rank_items)}条排行榜数据 - 耗时：{time.time() - start_time:.4f}s")
    return response_data
