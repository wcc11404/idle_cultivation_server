"""邮箱业务逻辑。"""

from __future__ import annotations

from datetime import datetime, timezone
import uuid
from typing import Any

from app.db.Models import MailData
from app.modules.inventory.ItemData import ItemData


class MailSystem:
    CAPACITY = 100
    MAX_ATTACHMENT_TYPES = 10

    @staticmethod
    def _fmt_time(dt: datetime | None) -> int:
        if not dt:
            return 0
        return int(dt.timestamp())

    @classmethod
    def _sanitize_attachments(cls, attachments: list[dict[str, Any]] | None) -> list[dict[str, int]]:
        if not isinstance(attachments, list):
            return []
        result: list[dict[str, int]] = []
        seen: set[str] = set()
        for row in attachments:
            if not isinstance(row, dict):
                continue
            item_id = str(row.get("item_id", "")).strip()
            count = int(row.get("count", 0))
            if not item_id or count <= 0:
                continue
            if not ItemData.item_exists(item_id):
                continue
            if item_id in seen:
                continue
            seen.add(item_id)
            result.append({"item_id": item_id, "count": count})
            if len(result) >= cls.MAX_ATTACHMENT_TYPES:
                break
        return result

    @classmethod
    async def count_active_mails(cls, account_id: str) -> int:
        return await MailData.filter(account_id=account_id, is_deleted=False).count()

    @classmethod
    async def create_mail(
        cls,
        account_id: str,
        title: str,
        content: str,
        attachments: list[dict[str, Any]] | None = None,
        expire_at: datetime | None = None,
    ) -> dict[str, Any]:
        if await cls.count_active_mails(account_id) >= cls.CAPACITY:
            return {"success": False, "reason_code": "MAIL_CAPACITY_REACHED", "reason_data": {"capacity": cls.CAPACITY}}

        safe_attachments = cls._sanitize_attachments(attachments)
        mail = await MailData.create(
            mail_id=uuid.uuid4().hex,
            account_id=account_id,
            title=str(title)[:100],
            content=str(content),
            attachments=safe_attachments,
            expire_at=expire_at,
        )
        return {
            "success": True,
            "reason_code": "MAIL_SEND_SUCCEEDED",
            "reason_data": {"mail_id": mail.mail_id},
        }

    @classmethod
    async def list_mails(cls, account_id: str) -> dict[str, Any]:
        rows = await MailData.filter(account_id=account_id, is_deleted=False).order_by("-created_at", "-mail_id")
        now_ts = int(datetime.now(timezone.utc).timestamp())
        mails: list[dict[str, Any]] = []
        unread_count = 0
        for row in rows:
            if row.expire_at and row.expire_at.timestamp() <= now_ts:
                continue
            attachments = row.attachments if isinstance(row.attachments, list) else []
            first_attachment = attachments[0] if attachments else None
            if not row.is_read:
                unread_count += 1
            preview = str(row.content).splitlines()[0] if str(row.content) else ""
            mails.append({
                "mail_id": row.mail_id,
                "title": row.title,
                "preview": preview[:60],
                "created_at": cls._fmt_time(row.created_at),
                "is_read": bool(row.is_read),
                "is_claimed": bool(row.is_claimed),
                "has_attachment": len(attachments) > 0,
                "first_attachment": first_attachment,
            })
        return {
            "success": True,
            "reason_code": "MAIL_LIST_SUCCEEDED",
            "reason_data": {},
            "mails": mails,
            "count": len(mails),
            "capacity": cls.CAPACITY,
            "unread_count": unread_count,
        }

    @classmethod
    async def get_mail_detail_and_mark_read(cls, account_id: str, mail_id: str) -> dict[str, Any]:
        row = await MailData.get_or_none(mail_id=mail_id, account_id=account_id, is_deleted=False)
        if not row:
            return {"success": False, "reason_code": "MAIL_NOT_FOUND", "reason_data": {"mail_id": mail_id}}

        if row.expire_at and row.expire_at.timestamp() <= datetime.now(timezone.utc).timestamp():
            return {"success": False, "reason_code": "MAIL_NOT_FOUND", "reason_data": {"mail_id": mail_id}}

        if not row.is_read:
            row.is_read = True
            await row.save()

        attachments = row.attachments if isinstance(row.attachments, list) else []
        return {
            "success": True,
            "reason_code": "MAIL_DETAIL_SUCCEEDED",
            "reason_data": {"mail_id": row.mail_id},
            "mail": {
                "mail_id": row.mail_id,
                "title": row.title,
                "content": row.content,
                "created_at": cls._fmt_time(row.created_at),
                "is_read": bool(row.is_read),
                "is_claimed": bool(row.is_claimed),
                "attachments": attachments,
            },
        }

    @classmethod
    async def claim_mail(cls, account_id: str, mail_id: str, inventory_system) -> dict[str, Any]:
        row = await MailData.get_or_none(mail_id=mail_id, account_id=account_id, is_deleted=False)
        if not row:
            return {"success": False, "reason_code": "MAIL_NOT_FOUND", "reason_data": {"mail_id": mail_id}}
        attachments = row.attachments if isinstance(row.attachments, list) else []
        if not attachments:
            return {"success": False, "reason_code": "MAIL_CLAIM_NO_ATTACHMENT", "reason_data": {"mail_id": mail_id}}
        if row.is_claimed:
            return {"success": False, "reason_code": "MAIL_CLAIM_ALREADY_CLAIMED", "reason_data": {"mail_id": mail_id}}

        # 事务回滚：先加，再失败就减回去
        applied: dict[str, int] = {}
        for entry in attachments:
            item_id = str(entry.get("item_id", ""))
            count = int(entry.get("count", 0))
            if not item_id or count <= 0:
                continue
            added = int(inventory_system.add_item(item_id, count))
            if added < count:
                # 回滚
                for rollback_item_id, rollback_count in applied.items():
                    inventory_system.remove_item(rollback_item_id, rollback_count)
                if added > 0:
                    inventory_system.remove_item(item_id, added)
                return {
                    "success": False,
                    "reason_code": "MAIL_CLAIM_INVENTORY_FULL",
                    "reason_data": {"mail_id": mail_id, "item_id": item_id},
                }
            applied[item_id] = applied.get(item_id, 0) + added

        row.is_claimed = True
        row.claimed_at = datetime.now(timezone.utc)
        await row.save()
        return {
            "success": True,
            "reason_code": "MAIL_CLAIM_SUCCEEDED",
            "reason_data": {"mail_id": mail_id},
            "rewards_granted": applied,
        }

    @classmethod
    async def delete_mails(
        cls,
        account_id: str,
        delete_mode: str,
        mail_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        deleted_count = 0

        if delete_mode == "read_and_claimed":
            rows = await MailData.filter(
                account_id=account_id,
                is_deleted=False,
                is_read=True,
            )
            for row in rows:
                has_attachment = isinstance(row.attachments, list) and len(row.attachments) > 0
                # 一键删除：删除“已读且非未领取”邮件
                # 保留：有附件但未领取（is_claimed=False）
                if has_attachment and (not row.is_claimed):
                    continue
                row.is_deleted = True
                row.deleted_at = now
                await row.save()
                deleted_count += 1
            return {
                "success": True,
                "reason_code": "MAIL_DELETE_BATCH_SUCCEEDED",
                "reason_data": {"deleted_count": deleted_count},
            }

        # manual
        mail_ids = mail_ids or []
        for mail_id in mail_ids:
            row = await MailData.get_or_none(mail_id=mail_id, account_id=account_id, is_deleted=False)
            if not row:
                continue
            has_attachment = isinstance(row.attachments, list) and len(row.attachments) > 0
            # 有附件且未领取时禁止手动删除，已领取可删
            if has_attachment and (not row.is_claimed):
                return {
                    "success": False,
                    "reason_code": "MAIL_DELETE_FORBIDDEN_UNREAD_UNCLAIMED",
                    "reason_data": {"mail_id": mail_id},
                }
            row.is_deleted = True
            row.deleted_at = now
            await row.save()
            deleted_count += 1

        return {
            "success": True,
            "reason_code": "MAIL_DELETE_SUCCEEDED",
            "reason_data": {"deleted_count": deleted_count},
        }
