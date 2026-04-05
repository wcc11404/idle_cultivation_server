from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from app.schemas.base import BaseRequest, BaseResponse


class SaveGameRequest(BaseRequest):
    """保存游戏请求"""
    data: dict


class SaveGameResponse(BaseResponse):
    """保存游戏响应"""
    last_online_at: int


class LoadGameResponse(BaseResponse):
    """加载游戏响应"""
    data: dict


class BreakthroughRequest(BaseRequest):
    """突破境界请求"""
    current_realm: str
    current_level: int
    spirit_energy: float
    inventory_items: dict


class BreakthroughResponse(BaseResponse):
    """突破境界响应"""
    new_realm: str
    new_level: int
    remaining_spirit_energy: float
    materials_used: dict
    health: float
    inventory: dict


class UseItemRequest(BaseRequest):
    """使用物品请求"""
    item_id: str
    count: int = 1


class UseItemResponse(BaseResponse):
    """使用物品响应"""
    effect: dict
    contents: Optional[dict] = None


class BattleVictoryRequest(BaseRequest):
    """战斗胜利请求"""
    area_id: str
    enemy_id: str
    enemy_level: int
    is_tower: bool = False
    tower_floor: int = 0


class BattleVictoryResponse(BaseResponse):
    """战斗胜利响应"""
    loot: list
    new_highest_floor: Optional[int] = None


class DungeonInfoResponse(BaseResponse):
    """副本信息响应"""
    dungeon_data: dict


class EnterDungeonRequest(BaseRequest):
    """进入副本请求"""
    dungeon_id: str


class EnterDungeonResponse(BaseResponse):
    """进入副本响应"""
    remaining_count: int
    message: str


class GetRankRequest(BaseRequest):
    """获取排行榜请求"""
    server_id: Optional[str] = Field(default="default", description="区服ID")


class RankItem(BaseModel):
    """排行榜项目"""
    nickname: str
    realm: str
    level: int
    spirit_energy: float
    title_id: str
    rank: int


class RankResponse(BaseResponse):
    """排行榜响应"""
    ranks: list[RankItem]


class CultivationStartRequest(BaseRequest):
    """开始修炼请求"""
    pass


class CultivationStartResponse(BaseResponse):
    """开始修炼响应"""
    spirit_gained: float = 0.0
    health_gained: float = 0.0
    used_count_gained: int = 0
    message: str


class CultivationReportRequest(BaseRequest):
    """修炼上报请求"""
    count: int


class CultivationReportResponse(BaseResponse):
    """修炼上报响应"""
    spirit_gained: float
    health_gained: float
    used_count_gained: int = 0
    message: str


class CultivationStopRequest(BaseRequest):
    """停止修炼请求"""
    pass


class CultivationStopResponse(BaseResponse):
    """停止修炼响应"""
    message: str


class OrganizeInventoryRequest(BaseRequest):
    """整理背包请求"""
    pass


class DiscardItemRequest(BaseRequest):
    """丢弃物品请求"""
    item_id: str
    count: int = 1


class EquipSpellRequest(BaseRequest):
    """装备术法请求"""
    spell_id: str


class UnequipSpellRequest(BaseRequest):
    """卸下术法请求"""
    spell_id: str


class UpgradeSpellRequest(BaseRequest):
    """升级术法请求"""
    spell_id: str


class ChargeSpellRequest(BaseRequest):
    """充灵气请求"""
    spell_id: str
    amount: float


class CraftPillsRequest(BaseRequest):
    """炼制丹药请求"""
    recipe_id: str
    count: int = 1


class AlchemyStartRequest(BaseRequest):
    """开始炼丹请求"""
    pass


class AlchemyStartResponse(BaseResponse):
    """开始炼丹响应"""
    is_alchemizing: bool
    message: str


class AlchemyReportRequest(BaseRequest):
    """炼丹上报请求"""
    recipe_id: str
    count: int


class AlchemyReportResponse(BaseResponse):
    """炼丹上报响应"""
    success_count: int
    fail_count: int
    products: dict
    materials_consumed: dict
    message: str


class AlchemyStopRequest(BaseRequest):
    """停止炼丹请求"""
    pass


class AlchemyStopResponse(BaseResponse):
    """停止炼丹响应"""
    is_alchemizing: bool
    message: str


class LearnRecipeRequest(BaseRequest):
    """学习丹方请求"""
    recipe_id: str


class ExecuteBattleRequest(BaseRequest):
    """执行战斗请求"""
    area_id: str
    floor: int = 1
    is_tower: bool = False


class LianliBattleRequest(BaseRequest):
    """历练战斗模拟请求"""
    area_id: str


class LianliBattleResponse(BaseResponse):
    """历练战斗模拟响应"""
    battle_timeline: list
    total_time: float
    player_health_before: float
    player_health_after: float
    enemy_health_after: float
    enemy_data: dict
    victory: bool
    loot: list
    message: str


class LianliSettleRequest(BaseRequest):
    """历练战斗结算请求"""
    speed: float
    index: Optional[int] = None


class LianliSettleResponse(BaseResponse):
    """历练战斗结算响应"""
    settled_index: int
    total_index: int
    player_health_after: float
    loot_gained: list
    exp_gained: int
    message: str


class FinishDungeonRequest(BaseRequest):
    """完成副本请求"""
    dungeon_id: str
    victory: bool = True


class ClaimOfflineRewardRequest(BaseRequest):
    """领取离线奖励请求"""
    pass