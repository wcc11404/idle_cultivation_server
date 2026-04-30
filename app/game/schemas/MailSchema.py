from pydantic import Field
from app.game.schemas.BaseSchema import BaseRequest, BaseResponse


class MailListResponse(BaseResponse):
    mails: list[dict]
    count: int
    capacity: int
    unread_count: int


class MailDetailResponse(BaseResponse):
    mail: dict


class MailClaimRequest(BaseRequest):
    mail_id: str


class MailClaimResponse(BaseResponse):
    rewards_granted: dict


class MailDeleteRequest(BaseRequest):
    delete_mode: str
    mail_ids: list[str] = Field(default_factory=list)


class MailDeleteResponse(BaseResponse):
    deleted_count: int
