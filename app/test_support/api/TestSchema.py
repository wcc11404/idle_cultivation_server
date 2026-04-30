from typing import Optional

from pydantic import Field

from app.game.schemas.BaseSchema import BaseRequest, BaseResponse


class TestActionResponse(BaseResponse):
    """测试接口统一响应。"""
    state_summary: dict = Field(default_factory=dict)


class ResetTestAccountRequest(BaseRequest):
    """重置测试账号请求。"""
    pass


class SetPlayerStateRequest(BaseRequest):
    """设置玩家状态请求。"""
    realm: Optional[str] = None
    realm_level: Optional[int] = None
    spirit_energy: Optional[float] = None
    health: Optional[float] = None


class SetInventoryItemsRequest(BaseRequest):
    """精确设置背包物品请求。"""
    items: dict[str, int] = Field(default_factory=dict)


class UnlockContentRequest(BaseRequest):
    """解锁内容请求。"""
    spell_ids: list[str] = Field(default_factory=list)
    recipe_ids: list[str] = Field(default_factory=list)
    furnace_ids: list[str] = Field(default_factory=list)


class SetEquippedSpellsRequest(BaseRequest):
    """设置装备术法请求。"""
    breathing: list[str] = Field(default_factory=list)
    active: list[str] = Field(default_factory=list)
    opening: list[str] = Field(default_factory=list)


class SetProgressStateRequest(BaseRequest):
    """设置进度状态请求。"""
    tower_highest_floor: Optional[int] = None
    daily_dungeon_remaining_counts: dict[str, int] = Field(default_factory=dict)


class SetRuntimeStateRequest(BaseRequest):
    """设置运行状态请求。"""
    is_cultivating: Optional[bool] = None
    is_alchemizing: Optional[bool] = None
    is_gathering: Optional[bool] = None
    is_in_lianli: Optional[bool] = None
    is_battling: Optional[bool] = None
    current_area_id: Optional[str] = None
    current_herb_point_id: Optional[str] = None
    herb_elapsed_seconds: Optional[float] = None


class ApplyPresetRequest(BaseRequest):
    """应用测试预设请求。"""
    preset_name: str


class GrantTestPackRequest(BaseRequest):
    """补发测试礼包请求。"""
    pass
