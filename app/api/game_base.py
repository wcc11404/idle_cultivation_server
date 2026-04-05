"""
游戏基础 API

包含加载、保存、离线奖励等基础功能
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from app.schemas.game import SaveGameRequest, SaveGameResponse, LoadGameResponse, ClaimOfflineRewardRequest, GetRankRequest, RankResponse, RankItem
from app.db.Models import PlayerData, Account
from app.core.Security import get_current_user, decode_token, security
from app.core.InitPlayerInfo import get_initial_player_data
from app.core.Logger import logger
from datetime import datetime, timezone
import time
import json
import os

router = APIRouter()


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
    logger.info(f"[OUT] GET /game/data - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
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
    
    allowed_fields = ["account_info", "player", "inventory", "spell_system", "alchemy_system", "lianli_system"]
    
    game_data = request.data
    
    if not player_data:
        logger.info(f"[GAME] 首次保存，创建数据 - account_id: {current_user.id}")
        player_data = await PlayerData.create(
            account_id=current_user.id,
            data=game_data
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
        last_online_at=int(player_data.last_online_at.timestamp())
    )
    logger.info(f"[OUT] POST /game/save - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
    return response_data


@router.post("/claim_offline_reward", response_model=dict)
async def claim_offline_reward(request: ClaimOfflineRewardRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """领取离线奖励"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] POST /game/claim_offline_reward - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
    player_data = await PlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        initial_data = get_initial_player_data(str(current_user.id))
        player_data = await PlayerData.create(
            account_id=current_user.id,
            data=initial_data
        )
    
    current_time = datetime.now(timezone.utc)
    last_online_time = player_data.last_online_at
    
    epoch_time = datetime.fromtimestamp(0, timezone.utc)
    if last_online_time == epoch_time:
        offline_seconds = 0
    else:
        offline_seconds = int((current_time - last_online_time).total_seconds())
    
    if offline_seconds < 0:
        logger.warning(f"[OUT] POST /game/claim_offline_reward - INVALID_OFFLINE_SECONDS_NEGATIVE - account_id: {current_user.id} - offline_seconds: {offline_seconds} - 耗时：{time.time() - start_time:.4f}s")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="离线时间不能为负数"
        )
    if offline_seconds > 4 * 3600:
        logger.warning(f"[OUT] POST /game/claim_offline_reward - INVALID_OFFLINE_SECONDS_TOO_LONG - account_id: {current_user.id} - offline_seconds: {offline_seconds} - 耗时：{time.time() - start_time:.4f}s")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="离线时间不能超过 4 小时（14400 秒）"
        )
    
    spirit_per_second = 1.0
    player_realm = player_data.data.get("player", {}).get("realm", "")
    realm_bonus = 1.0
    if player_realm == "筑基期":
        realm_bonus = 1.5
    elif player_realm == "金丹期":
        realm_bonus = 2.0
    spirit_per_second *= realm_bonus
    
    efficiency = 1.0
    total_spirit = spirit_per_second * offline_seconds * efficiency
    
    max_spirit = player_data.data.get("player", {}).get("max_spirit_energy", 100) * 60
    total_spirit = min(total_spirit, max_spirit)
    
    offline_minutes = offline_seconds / 60.0
    total_minutes = int(offline_minutes)
    stone_per_minute = 1.0
    total_stone = int(stone_per_minute * total_minutes)
    
    total_spirit = round(float(total_spirit), 2)
    if total_spirit.is_integer():
        total_spirit = int(total_spirit)
    
    offline_reward = {
        "spirit_energy": total_spirit,
        "spirit_stones": total_stone
    }
    
    if offline_seconds > 60:
        player_data.data["player"]["spirit_energy"] += float(offline_reward["spirit_energy"])
        player_data.data["player"]["spirit_energy"] = round(player_data.data["player"]["spirit_energy"], 2)
        if player_data.data["player"]["spirit_energy"].is_integer():
            player_data.data["player"]["spirit_energy"] = int(player_data.data["player"]["spirit_energy"])
        
        if "spirit_stones" in player_data.data["inventory"]["slots"]:
            current_stones = player_data.data["inventory"]["slots"]["spirit_stones"]
            if isinstance(current_stones, str):
                current_stones = int(current_stones)
            player_data.data["inventory"]["slots"]["spirit_stones"] = current_stones + offline_reward["spirit_stones"]
        else:
            player_data.data["inventory"]["slots"]["spirit_stones"] = offline_reward["spirit_stones"]
    
    player_data.last_online_at = datetime.now(timezone.utc)
    
    if offline_seconds <= 60:
        response_data = {
            "success": True,
            "operation_id": request.operation_id,
            "timestamp": request.timestamp,
            "offline_reward": None,
            "offline_seconds": offline_seconds,
            "last_online_at": int(player_data.last_online_at.timestamp()),
            "message": "离线时间不足，无法领取奖励"
        }
    else:
        response_data = {
            "success": True,
            "operation_id": request.operation_id,
            "timestamp": request.timestamp,
            "offline_reward": offline_reward,
            "offline_seconds": offline_seconds,
            "last_online_at": int(player_data.last_online_at.timestamp()),
            "message": "领取成功"
        }
    logger.info(f"[OUT] POST /game/claim_offline_reward - {json.dumps(response_data, ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
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
        ranks=rank_items
    )
    logger.info(f"[OUT] GET /game/rank - 返回{len(rank_items)}条排行榜数据 - 耗时：{time.time() - start_time:.4f}s")
    return response_data
