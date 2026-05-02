from __future__ import annotations

from fastapi import APIRouter, Depends

from app.ops.audit import OpsAuditService
from app.ops.auth import require_ops_permission
from app.ops.models import OpsUser

router = APIRouter()


@router.get("/audit/list", response_model=dict)
async def ops_audit_list(
    action_type: str = "",
    operator_username: str = "",
    page: int = 1,
    page_size: int = 20,
    _: OpsUser = Depends(require_ops_permission("audit.view")),
):
    return await OpsAuditService.list_logs(
        action_type=action_type,
        operator_username=operator_username,
        page=page,
        page_size=page_size,
    )
