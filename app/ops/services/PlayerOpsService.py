from __future__ import annotations

from typing import Any

from app.core.db.Models import Account, PlayerData
from app.ops.services.Common import get_account_or_404, get_player_data_or_404, summarize_player_data


class PlayerOpsService:
    @staticmethod
    def _extract_nickname(player_data: PlayerData | None) -> str:
        if not player_data or not isinstance(player_data.data, dict):
            return ""
        account_info = player_data.data.get("account_info", {})
        if not isinstance(account_info, dict):
            return ""
        return str(account_info.get("nickname", "") or "")

    @staticmethod
    async def list_players(*, query: str = "", page: int = 1, page_size: int = 20) -> dict[str, Any]:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        normalized_query = str(query).strip().lower()
        account_query = Account.all().order_by("-created_at")
        accounts = await account_query
        player_rows = await PlayerData.filter(account_id__in=[row.id for row in accounts]) if accounts else []
        player_map = {str(row.account_id): row for row in player_rows}

        filtered_accounts: list[Account] = []
        for account in accounts:
            player_data = player_map.get(str(account.id))
            nickname = PlayerOpsService._extract_nickname(player_data)
            if normalized_query and normalized_query not in account.username.lower() and normalized_query not in nickname.lower():
                continue
            filtered_accounts.append(account)

        total = len(filtered_accounts)
        page_accounts = filtered_accounts[(page - 1) * page_size : page * page_size]
        items: list[dict[str, Any]] = []
        for account in page_accounts:
            player_data = player_map.get(str(account.id))
            summary = summarize_player_data(player_data) if player_data else {}
            items.append(
                {
                    "account_id": str(account.id),
                    "username": account.username,
                    "nickname": PlayerOpsService._extract_nickname(player_data),
                    "server_id": account.server_id,
                    "is_banned": bool(account.is_banned),
                    "created_at": account.created_at.isoformat(),
                    "last_online_at": player_data.last_online_at.isoformat() if player_data and player_data.last_online_at else None,
                    "realm": summary.get("realm", ""),
                    "realm_level": summary.get("realm_level", 0),
                }
            )
        return {
            "success": True,
            "reason_code": "OPS_PLAYERS_LIST_SUCCEEDED",
            "reason_data": {"total": total},
            "items": items,
            "page": page,
            "page_size": page_size,
            "total": total,
        }

    @staticmethod
    async def get_player_detail(account_id: str) -> dict[str, Any]:
        account = await get_account_or_404(account_id)
        player_data = await get_player_data_or_404(account_id)
        summary = summarize_player_data(player_data)
        return {
            "success": True,
            "reason_code": "OPS_PLAYER_DETAIL_SUCCEEDED",
            "reason_data": {"account_id": account_id},
            "player": {
                "account_id": str(account.id),
                "username": account.username,
                "nickname": PlayerOpsService._extract_nickname(player_data),
                "server_id": account.server_id,
                "is_banned": bool(account.is_banned),
                "created_at": account.created_at.isoformat(),
                "updated_at": account.updated_at.isoformat(),
                "last_online_at": player_data.last_online_at.isoformat() if player_data.last_online_at else None,
                "summary": summary,
                "game_data": player_data.data,
            },
        }

    @staticmethod
    async def ban_player(account_id: str) -> dict[str, Any]:
        account = await get_account_or_404(account_id)
        account.is_banned = True
        account.token_version += 1
        await account.save()
        return {
            "success": True,
            "reason_code": "OPS_PLAYER_BAN_SUCCEEDED",
            "reason_data": {"account_id": account_id, "username": account.username},
        }

    @staticmethod
    async def unban_player(account_id: str) -> dict[str, Any]:
        account = await get_account_or_404(account_id)
        account.is_banned = False
        await account.save()
        return {
            "success": True,
            "reason_code": "OPS_PLAYER_UNBAN_SUCCEEDED",
            "reason_data": {"account_id": account_id, "username": account.username},
        }

    @staticmethod
    async def kick_player(account_id: str) -> dict[str, Any]:
        account = await get_account_or_404(account_id)
        account.token_version += 1
        await account.save()
        return {
            "success": True,
            "reason_code": "OPS_PLAYER_KICK_SUCCEEDED",
            "reason_data": {"account_id": account_id, "username": account.username},
        }
