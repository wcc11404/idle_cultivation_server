from app.game.schemas.BaseSchema import BaseRequest, BaseResponse


class TaskListResponse(BaseResponse):
    daily_tasks: list[dict]
    newbie_tasks: list[dict]


class TaskClaimRequest(BaseRequest):
    task_id: str


class TaskClaimResponse(BaseResponse):
    rewards_granted: dict
