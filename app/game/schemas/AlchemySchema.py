from pydantic import Field
from app.game.schemas.BaseSchema import BaseRequest, BaseResponse


class AlchemyRecipesResponse(BaseResponse):
    learned_recipes: list[str]
    recipes_config: dict


class CraftPillsRequest(BaseRequest):
    recipe_id: str
    count: int = 1


class AlchemyStartRequest(BaseRequest):
    pass


class AlchemyStartResponse(BaseResponse):
    pass


class AlchemyReportRequest(BaseRequest):
    recipe_id: str
    count: int


class AlchemyReportResponse(BaseResponse):
    success_count: int
    fail_count: int
    products: dict
    returned_materials: dict = Field(default_factory=dict)


class AlchemyStopRequest(BaseRequest):
    pass


class AlchemyStopResponse(BaseResponse):
    pass
