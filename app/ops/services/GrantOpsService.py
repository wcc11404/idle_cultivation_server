from __future__ import annotations

from datetime import datetime, timedelta, timezone
import uuid
from typing import Any

from app.core.db.Models import Account
from app.game.domain.inventory.ItemData import ItemData
from app.game.domain.mail.MailSystem import MailSystem
from app.ops.models import OpsActionConfirm


class GrantOpsService:
    CONFIRM_EXPIRE_MINUTES = 10

    @staticmethod
    async def _resolve_targets(account_ids: list[str] | None, all_accounts: bool) -> list[str]:
        if all_accounts:
            accounts = await Account.all()
            return [str(row.id) for row in accounts]
        result = []
        for account_id in account_ids or []:
            account_id = str(account_id).strip()
            if account_id and account_id not in result:
                result.append(account_id)
        return result

    @staticmethod
    async def preview_mail(*, operator_user_id: str, title: str, content: str, attachments: list[dict[str, Any]], account_ids: list[str] | None, all_accounts: bool) -> dict[str, Any]:
        targets = await GrantOpsService._resolve_targets(account_ids, all_accounts)
        sanitized_attachments = []
        for row in attachments:
            item_id = str(row.get("item_id", "")).strip()
            count = int(row.get("count", 0) or 0)
            if not item_id or count <= 0 or not ItemData.item_exists(item_id):
                continue
            sanitized_attachments.append({"item_id": item_id, "count": count})
        confirm_token = uuid.uuid4().hex
        payload = {
            "mode": "mail",
            "title": title,
            "content": content,
            "attachments": sanitized_attachments,
            "account_ids": targets,
            "all_accounts": bool(all_accounts),
        }
        await OpsActionConfirm.create(
            operator_user_id=operator_user_id,
            action_type="grant_mail",
            confirm_token=confirm_token,
            request_payload=payload,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=GrantOpsService.CONFIRM_EXPIRE_MINUTES),
        )
        return {
            "success": True,
            "reason_code": "OPS_GRANT_MAIL_PREVIEW_SUCCEEDED",
            "reason_data": {"target_count": len(targets)},
            "confirm_token": confirm_token,
            "preview": {
                "target_count": len(targets),
                "all_accounts": bool(all_accounts),
                "title": title,
                "attachments": sanitized_attachments,
            },
        }

    @staticmethod
    async def confirm_mail(*, confirm_token: str) -> dict[str, Any]:
        row = await OpsActionConfirm.get_or_none(confirm_token=confirm_token, action_type="grant_mail")
        if not row or row.used_at is not None or row.expires_at <= datetime.now(timezone.utc):
            return {"success": False, "reason_code": "OPS_CONFIRM_TOKEN_INVALID", "reason_data": {"confirm_token": confirm_token}}
        payload = row.request_payload if isinstance(row.request_payload, dict) else {}
        targets = [str(x) for x in payload.get("account_ids", [])]
        sent_count = 0
        skipped_capacity = 0
        for account_id in targets:
            result = await MailSystem.create_mail(
                account_id=account_id,
                title=str(payload.get("title", "")),
                content=str(payload.get("content", "")),
                attachments=payload.get("attachments", []),
            )
            if result.get("success"):
                sent_count += 1
            elif result.get("reason_code") == "MAIL_CAPACITY_REACHED":
                skipped_capacity += 1
        row.used_at = datetime.now(timezone.utc)
        await row.save()
        return {
            "success": True,
            "reason_code": "OPS_GRANT_MAIL_CONFIRM_SUCCEEDED",
            "reason_data": {
                "target_count": len(targets),
                "sent_count": sent_count,
                "skipped_capacity": skipped_capacity,
            },
        }

    @staticmethod
    def list_mail_attachment_options() -> dict[str, Any]:
        items = [
            {
                "item_id": item_id,
                "item_name": ItemData.get_item_name(item_id),
            }
            for item_id in ItemData.get_all_items()
        ]
        items.sort(key=lambda row: (str(row.get("item_name", "")), str(row.get("item_id", ""))))
        return {
            "success": True,
            "reason_code": "OPS_GRANT_ITEM_OPTIONS_SUCCEEDED",
            "reason_data": {"count": len(ItemData.get_all_items())},
            "items": items,
        }

    @staticmethod
    def direct_item_grant_disabled() -> dict[str, Any]:
        return {
            "success": False,
            "reason_code": "OPS_DIRECT_ITEM_GRANT_DISABLED",
            "reason_data": {},
        }
