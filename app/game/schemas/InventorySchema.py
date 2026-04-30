from app.game.schemas.BaseSchema import BaseRequest, BaseResponse


class UseItemRequest(BaseRequest):
    item_id: str
    count: int = 1


class UseItemResponse(BaseResponse):
    pass


class OrganizeInventoryRequest(BaseRequest):
    pass


class OrganizeInventoryResponse(BaseResponse):
    pass


class DiscardItemRequest(BaseRequest):
    item_id: str
    count: int = 1


class ExpandInventoryRequest(BaseRequest):
    pass


class ExpandInventoryResponse(BaseResponse):
    pass


class InventoryListResponse(BaseResponse):
    inventory: dict
