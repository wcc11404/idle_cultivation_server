from typing import Optional
from app.game.schemas.BaseSchema import BaseRequest, BaseResponse


class LianliBattleRequest(BaseRequest):
    area_id: str


class LianliBattleResponse(BaseResponse):
    battle_timeline: list
    total_time: float
    player_health_before: float
    player_health_after: float
    enemy_health_after: float
    enemy_data: dict
    victory: bool
    loot: list


class LianliSpeedOptionsResponse(BaseResponse):
    available_speeds: list[float]
    default_speed: float


class LianliSettleRequest(BaseRequest):
    speed: float
    index: Optional[int] = None


class LianliSettleResponse(BaseResponse):
    settled_index: int
    total_index: int
    player_health_after: float
    loot_gained: list
    exp_gained: int
