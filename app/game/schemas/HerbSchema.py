from app.game.schemas.BaseSchema import BaseRequest, BaseResponse


class HerbPointsResponse(BaseResponse):
    points_config: dict
    current_state: dict


class HerbStartRequest(BaseRequest):
    point_id: str


class HerbStartResponse(BaseResponse):
    pass


class HerbReportRequest(BaseRequest):
    pass


class HerbReportResponse(BaseResponse):
    point_id: str
    success_roll: bool
    drops_gained: dict


class HerbStopRequest(BaseRequest):
    pass


class HerbStopResponse(BaseResponse):
    pass
