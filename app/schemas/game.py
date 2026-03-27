from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class SaveGameRequest(BaseModel):
    """保存游戏请求"""
    data: dict


class SaveGameResponse(BaseModel):
    """保存游戏响应"""
    success: bool
    last_online_at: int


class LoadGameResponse(BaseModel):
    """加载游戏响应"""
    success: bool
    data: dict


class BreakthroughRequest(BaseModel):
    """突破境界请求"""
    current_realm: str
    current_level: int
    spirit_energy: float
    inventory_items: dict


class BreakthroughResponse(BaseModel):
    """突破境界响应"""
    success: bool
    new_realm: str
    new_level: int
    remaining_spirit_energy: float
    materials_used: dict


class UseItemRequest(BaseModel):
    """使用物品请求"""
    item_id: str
    count: int = 1
    current_inventory: dict


class UseItemResponse(BaseModel):
    """使用物品响应"""
    success: bool
    effect: dict
    contents: Optional[dict] = None


class BattleVictoryRequest(BaseModel):
    """战斗胜利请求"""
    area_id: str
    enemy_id: str
    enemy_level: int
    is_tower: bool = False
    tower_floor: int = 0


class BattleVictoryResponse(BaseModel):
    """战斗胜利响应"""
    success: bool
    loot: list
    new_highest_floor: Optional[int] = None


class DungeonInfoResponse(BaseModel):
    """副本信息响应"""
    success: bool
    dungeon_data: dict


class EnterDungeonRequest(BaseModel):
    """进入副本请求"""
    dungeon_id: str


class EnterDungeonResponse(BaseModel):
    """进入副本响应"""
    success: bool
    remaining_count: int
    message: str


class RankItem(BaseModel):
    """排行榜项目"""
    nickname: str
    realm: str
    level: int
    spirit_energy: float
    title_id: str
    rank: int


class RankResponse(BaseModel):
    """排行榜响应"""
    success: bool
    ranks: list[RankItem]