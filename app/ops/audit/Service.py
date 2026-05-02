from __future__ import annotations

from typing import Any

from fastapi import Request

from app.ops.models import OpsAuditLog, OpsUser


class OpsAuditService:
    @staticmethod
    async def write_log(
        *,
        operator: OpsUser | None,
        action_type: str,
        target_scope: str,
        target_payload: dict[str, Any] | None,
        request_payload: dict[str, Any] | None,
        result: str,
        reason_code: str | None,
        request: Request | None = None,
    ) -> None:
        headers = request.headers if request else {}
        client = request.client if request else None
        await OpsAuditLog.create(
            operator_user_id=operator.id if operator else None,
            operator_username=operator.username if operator else None,
            action_type=action_type,
            target_scope=target_scope,
            target_payload=target_payload or {},
            request_payload=request_payload or {},
            result=result,
            reason_code=reason_code,
            ip=client.host if client else None,
            user_agent=headers.get("user-agent") if headers else None,
        )

    @staticmethod
    async def list_logs(*, action_type: str = "", operator_username: str = "", page: int = 1, page_size: int = 20) -> dict[str, Any]:
        query = OpsAuditLog.all().order_by("-created_at")
        if action_type:
            query = query.filter(action_type=action_type)
        if operator_username:
            query = query.filter(operator_username__icontains=operator_username)
        total = await query.count()
        rows = await query.offset(max(page - 1, 0) * page_size).limit(page_size)
        items = [
            {
                "id": str(row.id),
                "operator_user_id": str(row.operator_user_id) if row.operator_user_id else "",
                "operator_username": row.operator_username or "",
                "action_type": row.action_type,
                "target_scope": row.target_scope,
                "target_payload": row.target_payload,
                "request_payload": row.request_payload,
                "result": row.result,
                "reason_code": row.reason_code,
                "ip": row.ip,
                "user_agent": row.user_agent,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
        return {
            "success": True,
            "reason_code": "OPS_AUDIT_LIST_SUCCEEDED",
            "reason_data": {"total": total},
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
        }
