from pydantic import BaseModel
from typing import Optional
from app.game.schemas.BaseSchema import BaseRequest, BaseResponse


class SaveGameRequest(BaseRequest):
    data: dict


class SaveGameResponse(BaseResponse):
    last_online_at: int


class LoadGameResponse(BaseResponse):
    data: dict


class RankItem(BaseModel):
    nickname: str
    realm: str
    level: int
    spirit_energy: float
    title_id: str
    rank: int


class RankResponse(BaseResponse):
    ranks: list[RankItem]


class DungeonInfoQueryResponse(BaseResponse):
    remaining_count: int
    max_count: int


class TowerHighestFloorResponse(BaseResponse):
    highest_floor: int


class ClaimOfflineRewardRequest(BaseRequest):
    pass


class ClaimOfflineRewardResponse(BaseResponse):
    offline_reward: Optional[dict] = None
    offline_seconds: int
    last_online_at: int
