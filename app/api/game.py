from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.schemas.game import SaveGameRequest, SaveGameResponse, LoadGameResponse, BreakthroughRequest, BreakthroughResponse, UseItemRequest, UseItemResponse, BattleVictoryRequest, BattleVictoryResponse
from app.db.models import Account, PlayerData
from app.core.security import decode_token
from datetime import datetime
import random

router = APIRouter()
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Account:
    """获取当前用户"""
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INVALID_TOKEN"
        )
    
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    
    account = await Account.get_or_none(id=account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ACCOUNT_NOT_FOUND"
        )
    
    if account.token_version != token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="KICKED_OUT"
        )
    
    return account


@router.get("/data", response_model=LoadGameResponse)
async def load_game(current_user: Account = Depends(get_current_user)):
    """加载游戏数据"""
    player_data = await PlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        # 创建初始数据
        initial_data = {
            "player": {
                "realm": "炼气期",
                "realm_level": 1,
                "health": 500.0,
                "spirit_energy": 0.0,
                "nickname": f"修仙者{current_user.id[:6]}",
                "avatar_id": "default_1",
                "title_id": ""
            },
            "inventory": {
                "capacity": 50,
                "slots": {}
            },
            "spell_system": {
                "player_spells": {},
                "equipped_spells": {
                    "tuna": None,
                    "active": [],
                    "passive": []
                }
            },
            "alchemy_system": {
                "equipped_furnace_id": "",
                "learned_recipes": ["health_pill"]
            },
            "lianli_system": {
                "tower_highest_floor": 0,
                "daily_dungeon_data": {}
            },
            "timestamp": int(datetime.now().timestamp())
        }
        player_data = await PlayerData.create(
            account_id=current_user.id,
            data=initial_data
        )
    
    return LoadGameResponse(
        success=True,
        data=player_data.data
    )


@router.post("/save", response_model=SaveGameResponse)
async def save_game(request: SaveGameRequest, current_user: Account = Depends(get_current_user)):
    """保存游戏数据"""
    player_data = await PlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        # 创建新数据
        player_data = await PlayerData.create(
            account_id=current_user.id,
            data=request.data
        )
    else:
        # 更新数据
        player_data.data = request.data
        player_data.last_online_at = datetime.now()
        player_data.updated_at = datetime.now()
        await player_data.save()
    
    return SaveGameResponse(
        success=True,
        last_online_at=int(player_data.last_online_at.timestamp())
    )


@router.post("/player/breakthrough", response_model=BreakthroughResponse)
async def breakthrough(request: BreakthroughRequest, current_user: Account = Depends(get_current_user)):
    """突破境界"""
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
    
    return UseItemResponse(
        success=True,
        effect=effect,
        contents=contents
    )


@router.post("/battle/victory", response_model=BattleVictoryResponse)
async def battle_victory(request: BattleVictoryRequest, current_user: Account = Depends(get_current_user)):
    """战斗胜利"""
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
    
    return BattleVictoryResponse(
        success=True,
        loot=loot,
        new_highest_floor=new_highest_floor
    )