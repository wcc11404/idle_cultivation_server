from app.game.schemas.BaseSchema import BaseRequest, BaseResponse


class BreakthroughRequest(BaseRequest):
    pass


class BreakthroughResponse(BaseResponse):
    pass


class CultivationStartRequest(BaseRequest):
    pass


class CultivationStartResponse(BaseResponse):
    pass


class CultivationReportRequest(BaseRequest):
    elapsed_seconds: float


class CultivationReportResponse(BaseResponse):
    spirit_gained: float
    health_gained: float
    used_count_gained: int = 0


class CultivationStopRequest(BaseRequest):
    pass


class CultivationStopResponse(BaseResponse):
    pass
