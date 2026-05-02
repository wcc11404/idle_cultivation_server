from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.core.db.Models import Account, PlayerData
from app.ops.models import OpsLoginWhitelist, OpsSystemState
from tortoise.expressions import F


class SystemOpsService:
    @staticmethod
    def _is_uuid_like(value: str) -> bool:
        try:
            UUID(str(value))
            return True
        except (TypeError, ValueError):
            return False

    @staticmethod
    async def _find_account_by_identifier(identifier: str) -> Account | None:
        normalized = str(identifier).strip()
        if not normalized:
            return None
        if SystemOpsService._is_uuid_like(normalized):
            account = await Account.get_or_none(id=normalized)
            if account:
                return account
        return await Account.get_or_none(username=normalized)

    @staticmethod
    async def get_health() -> dict[str, Any]:
        account_count = await Account.all().count()
        return {
            "success": True,
            "reason_code": "OPS_SYSTEM_HEALTH_SUCCEEDED",
            "reason_data": {},
            "health": {
                "status": "ok",
                "account_count": account_count,
                "time": datetime.now(timezone.utc).isoformat(),
            },
        }

    @staticmethod
    async def get_summary() -> dict[str, Any]:
        state = await OpsSystemState.get(id=1)
        return {
            "success": True,
            "reason_code": "OPS_SYSTEM_SUMMARY_SUCCEEDED",
            "reason_data": {},
            "summary": {
                "login_gate_enabled": bool(state.login_gate_enabled),
                "login_gate_updated_by": state.login_gate_updated_by,
                "login_gate_updated_at": state.login_gate_updated_at.isoformat() if state.login_gate_updated_at else None,
                "ops_whitelist_count": await OpsLoginWhitelist.all().count(),
                "players_total": await Account.all().count(),
                "players_banned": await Account.filter(is_banned=True).count(),
                "players_active_recent": await PlayerData.all().count(),
            },
        }

    @staticmethod
    async def update_login_gate(*, enabled: bool, operator_username: str, note: str | None = None) -> dict[str, Any]:
        state = await OpsSystemState.get(id=1)
        state.login_gate_enabled = bool(enabled)
        state.login_gate_updated_by = operator_username
        state.login_gate_updated_at = datetime.now(timezone.utc)
        state.login_gate_note = note or ""
        await state.save()
        return {
            "success": True,
            "reason_code": "OPS_LOGIN_GATE_UPDATE_SUCCEEDED",
            "reason_data": {"login_gate_enabled": bool(enabled)},
        }

    @staticmethod
    async def list_whitelist() -> dict[str, Any]:
        rows = await OpsLoginWhitelist.all().order_by("-created_at")
        return {
            "success": True,
            "reason_code": "OPS_WHITELIST_LIST_SUCCEEDED",
            "reason_data": {"count": len(rows)},
            "items": [
                {
                    "id": str(row.id),
                    "account_id": str(row.account_id),
                    "account_username_snapshot": row.account_username_snapshot,
                    "note": row.note,
                    "created_by": row.created_by,
                    "created_at": row.created_at.isoformat(),
                }
                for row in rows
            ],
        }

    @staticmethod
    async def update_whitelist(*, action: str, account_id: str, operator_username: str, note: str | None = None) -> dict[str, Any]:
        identifier = str(account_id).strip()
        if action == "remove":
            account = await SystemOpsService._find_account_by_identifier(identifier)
            if account:
                deleted = await OpsLoginWhitelist.filter(account_id=account.id).delete()
            elif SystemOpsService._is_uuid_like(identifier):
                deleted = await OpsLoginWhitelist.filter(account_id=identifier).delete()
            else:
                deleted = 0
            return {
                "success": True,
                "reason_code": "OPS_WHITELIST_REMOVE_SUCCEEDED",
                "reason_data": {"deleted": int(deleted), "account_identifier": identifier},
            }
        account = await SystemOpsService._find_account_by_identifier(identifier)
        if not account:
            return {"success": False, "reason_code": "OPS_ACCOUNT_NOT_FOUND", "reason_data": {"account_id": identifier}}
        await OpsLoginWhitelist.update_or_create(
            defaults={
                "account_username_snapshot": account.username,
                "note": note or "",
                "created_by": operator_username,
            },
            account_id=account.id,
        )
        return {
            "success": True,
            "reason_code": "OPS_WHITELIST_ADD_SUCCEEDED",
            "reason_data": {"account_id": str(account.id), "username": account.username},
        }

    @staticmethod
    async def kick_all_players() -> dict[str, Any]:
        affected = await Account.all().update(token_version=F("token_version") + 1)
        return {
            "success": True,
            "reason_code": "OPS_PLAYER_KICK_ALL_SUCCEEDED",
            "reason_data": {"affected_count": int(affected)},
        }
