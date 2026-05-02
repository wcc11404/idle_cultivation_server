from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import HTTPException, status

from app.core.db.Models import Account, PlayerData
from app.core.locks.WriteLock import begin_write_lock_by_account_id
from app.game.application.Dependencies import build_game_context
from app.game.application.DailyReset import run_daily_reset_if_needed


@asynccontextmanager
async def begin_ops_game_context(account_id: str, endpoint: str):
    async with begin_write_lock_by_account_id(
        endpoint=endpoint,
        account_id=account_id,
        token_version=None,
        lock_player=True,
        allow_missing_account=True,
    ) as locked:
        if not locked.account:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OPS_ACCOUNT_NOT_FOUND")
        if not locked.player_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OPS_PLAYER_DATA_NOT_FOUND")
        run_daily_reset_if_needed(locked.player_data)
        ctx = build_game_context(locked.account, locked.player_data)
        yield locked, ctx


async def save_game_context(ctx) -> None:
    ctx.save()
    await ctx.player_data.save()


async def get_account_or_404(account_id: str) -> Account:
    account = await Account.get_or_none(id=account_id)
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OPS_ACCOUNT_NOT_FOUND")
    return account


async def get_player_data_or_404(account_id: str) -> PlayerData:
    player_data = await PlayerData.get_or_none(account_id=account_id)
    if not player_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OPS_PLAYER_DATA_NOT_FOUND")
    return player_data


def summarize_player_data(player_data: PlayerData) -> dict[str, Any]:
    data = player_data.data if isinstance(player_data.data, dict) else {}
    player = data.get("player", {}) if isinstance(data.get("player", {}), dict) else {}
    inventory = data.get("inventory", {}) if isinstance(data.get("inventory", {}), dict) else {}
    task_system = data.get("task_system", {}) if isinstance(data.get("task_system", {}), dict) else {}
    return {
        "realm": player.get("realm", ""),
        "realm_level": int(player.get("realm_level", 0) or 0),
        "health": float(player.get("health", 0.0) or 0.0),
        "spirit_energy": float(player.get("spirit_energy", 0.0) or 0.0),
        "inventory_capacity": int(inventory.get("capacity", 0) or 0),
        "task_count": len(task_system.get("tasks", {})) if isinstance(task_system.get("tasks", {}), dict) else 0,
    }
