from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.Base import BaseRequest, BaseResponse


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
    pass


class BreakthroughResponse(BaseResponse):
    """突破境界响应"""
    pass


class UseItemRequest(BaseRequest):
    """使用物品请求"""
    item_id: str
    count: int = 1


class UseItemResponse(BaseResponse):
    """使用物品响应"""
    pass


class OrganizeInventoryResponse(BaseResponse):
    """整理背包响应"""
    pass


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


class AlchemyRecipesResponse(BaseResponse):
    """丹方列表响应"""
    learned_recipes: list[str]
    recipes_config: dict


class DungeonInfoQueryResponse(BaseResponse):
    """副本信息查询响应"""
    remaining_count: int
    max_count: int


class TowerHighestFloorResponse(BaseResponse):
    """无尽塔信息响应"""
    highest_floor: int


class CultivationStartRequest(BaseRequest):
    """开始修炼请求"""
    pass


class CultivationStartResponse(BaseResponse):
    """开始修炼响应"""
    pass


class CultivationReportRequest(BaseRequest):
    """修炼上报请求"""
    elapsed_seconds: float


class CultivationReportResponse(BaseResponse):
    """修炼上报响应"""
    spirit_gained: float
    health_gained: float
    used_count_gained: int = 0


class CultivationStopRequest(BaseRequest):
    """停止修炼请求"""
    pass


class CultivationStopResponse(BaseResponse):
    """停止修炼响应"""
    pass


class OrganizeInventoryRequest(BaseRequest):
    """整理背包请求"""
    pass


class DiscardItemRequest(BaseRequest):
    """丢弃物品请求"""
    item_id: str
    count: int = 1


class ExpandInventoryRequest(BaseRequest):
    """扩容背包请求"""
    pass


class ExpandInventoryResponse(BaseResponse):
    """扩容背包响应"""
    pass


class InventoryListResponse(BaseResponse):
    """背包列表响应"""
    inventory: dict


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
    amount: int


class CraftPillsRequest(BaseRequest):
    """炼制丹药请求"""
    recipe_id: str
    count: int = 1


class AlchemyStartRequest(BaseRequest):
    """开始炼丹请求"""
    pass


class AlchemyStartResponse(BaseResponse):
    """开始炼丹响应"""
    pass


class AlchemyReportRequest(BaseRequest):
    """炼丹上报请求"""
    recipe_id: str
    count: int


class AlchemyReportResponse(BaseResponse):
    """炼丹上报响应"""
    success_count: int
    fail_count: int
    products: dict
    returned_materials: dict = Field(default_factory=dict)


class AlchemyStopRequest(BaseRequest):
    """停止炼丹请求"""
    pass


class AlchemyStopResponse(BaseResponse):
    """停止炼丹响应"""
    pass


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


class LianliSpeedOptionsResponse(BaseResponse):
    """历练倍速选项响应"""
    available_speeds: list[float]
    default_speed: float


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


class ClaimOfflineRewardRequest(BaseRequest):
    """领取离线奖励请求"""
    pass


class ClaimOfflineRewardResponse(BaseResponse):
    """领取离线奖励响应"""
    offline_reward: Optional[dict] = None
    offline_seconds: int
    last_online_at: int


class SpellListResponse(BaseResponse):
    """术法列表响应"""
    player_spells: dict
    equipped_spells: dict
    spells_config: dict


class HerbPointsResponse(BaseResponse):
    """采集点列表响应"""
    points_config: dict
    current_state: dict


class HerbStartRequest(BaseRequest):
    """开始采集请求"""
    point_id: str


class HerbStartResponse(BaseResponse):
    """开始采集响应"""
    pass


class HerbReportRequest(BaseRequest):
    """采集上报请求"""
    pass


class HerbReportResponse(BaseResponse):
    """采集上报响应"""
    point_id: str
    success_roll: bool
    drops_gained: dict


class HerbStopRequest(BaseRequest):
    """停止采集请求"""
    pass


class HerbStopResponse(BaseResponse):
    """停止采集响应"""
    pass


class TaskListResponse(BaseResponse):
    """任务列表响应"""
    daily_tasks: list[dict]
    newbie_tasks: list[dict]


class TaskClaimRequest(BaseRequest):
    """领取任务奖励请求"""
    task_id: str


class TaskClaimResponse(BaseResponse):
    """领取任务奖励响应"""
    rewards_granted: dict


class MailListResponse(BaseResponse):
    """邮件列表响应"""
    mails: list[dict]
    count: int
    capacity: int
    unread_count: int


class MailDetailResponse(BaseResponse):
    """邮件详情响应"""
    mail: dict


class MailClaimRequest(BaseRequest):
    """领取邮件请求"""
    mail_id: str


class MailClaimResponse(BaseResponse):
    """领取邮件响应"""
    rewards_granted: dict


class MailDeleteRequest(BaseRequest):
    """删除邮件请求"""
    delete_mode: str
    mail_ids: list[str] = Field(default_factory=list)


class MailDeleteResponse(BaseResponse):
    """删除邮件响应"""
    deleted_count: int
