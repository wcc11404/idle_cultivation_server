from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

import asyncpg

from app.core.ServerConfig import settings


JsonMutator = Callable[[dict[str, Any]], None]


async def _with_connection(callback: Callable[[asyncpg.Connection], Any]) -> Any:
    conn = await asyncpg.connect(settings.DATABASE_URL)
    try:
        return await callback(conn)
    finally:
        await conn.close()


async def _patch_player_data(account_id: str, mutator: JsonMutator, last_online_at: datetime | None = None) -> None:
    async def _callback(conn: asyncpg.Connection) -> None:
        row = await conn.fetchrow(
            "SELECT data, last_online_at FROM player_data WHERE account_id = $1",
            account_id,
        )
        if row is None:
            raise ValueError(f"player_data not found for account_id={account_id}")
        raw_data = row["data"]
        if isinstance(raw_data, str):
            data = json.loads(raw_data)
        else:
            data = raw_data
        mutator(data)
        await conn.execute(
            """
            UPDATE player_data
            SET data = $2::jsonb,
                last_online_at = COALESCE($3, last_online_at)
            WHERE account_id = $1
            """,
            account_id,
            json.dumps(data, ensure_ascii=False),
            last_online_at,
        )

    await _with_connection(_callback)


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


def set_offline_seconds(account_id: str, offline_seconds: int) -> None:
    last_online_at = datetime.now(timezone.utc) - timedelta(seconds=int(offline_seconds))
    _run(_patch_player_data(account_id, lambda data: None, last_online_at=last_online_at))


def set_cultivation_elapsed_seconds(account_id: str, elapsed_seconds: float) -> None:
    def _mutate(data: dict[str, Any]) -> None:
        player = data.setdefault("player", {})
        player["is_cultivating"] = True
        player["last_cultivation_report_time"] = time.time() - float(elapsed_seconds)
        player["cultivation_effect_carry_seconds"] = float(player.get("cultivation_effect_carry_seconds", 0.0))

    _run(_patch_player_data(account_id, _mutate))


def set_alchemy_elapsed_seconds(account_id: str, elapsed_seconds: float) -> None:
    def _mutate(data: dict[str, Any]) -> None:
        alchemy_system = data.setdefault("alchemy_system", {})
        alchemy_system["is_alchemizing"] = True
        alchemy_system["last_alchemy_report_time"] = time.time() - float(elapsed_seconds)

    _run(_patch_player_data(account_id, _mutate))


def set_battle_elapsed_seconds(account_id: str, elapsed_seconds: float) -> None:
    def _mutate(data: dict[str, Any]) -> None:
        lianli_system = data.setdefault("lianli_system", {})
        lianli_system["is_battling"] = True
        lianli_system["battle_start_time"] = time.time() - float(elapsed_seconds)

    _run(_patch_player_data(account_id, _mutate))


def set_herb_elapsed_seconds(account_id: str, elapsed_seconds: float, point_id: str = "point_low_yield") -> None:
    def _mutate(data: dict[str, Any]) -> None:
        herb_system = data.setdefault("herb_system", {})
        herb_system["is_gathering"] = True
        herb_system["current_point_id"] = point_id
        herb_system["last_report_time"] = time.time() - float(elapsed_seconds)

    _run(_patch_player_data(account_id, _mutate))


def set_herb_spell_level(account_id: str, level: int) -> None:
    def _mutate(data: dict[str, Any]) -> None:
        spell_system = data.setdefault("spell_system", {})
        player_spells = spell_system.setdefault("player_spells", {})
        herb_spell = player_spells.setdefault(
            "herb_gathering",
            {"obtained": True, "level": 1, "use_count": 0, "charged_spirit": 0},
        )
        herb_spell["obtained"] = True
        herb_spell["level"] = max(1, int(level))

    _run(_patch_player_data(account_id, _mutate))


def set_account_vip_days(account_id: str, days: int) -> None:
    def _mutate(data: dict[str, Any]) -> None:
        account_info = data.setdefault("account_info", {})
        if days > 0:
            expire_at = datetime.now() + timedelta(days=int(days))
            account_info["is_vip"] = True
            account_info["vip_expire_time"] = expire_at.isoformat()
        else:
            account_info["is_vip"] = False
            account_info["vip_expire_time"] = None

    _run(_patch_player_data(account_id, _mutate))
