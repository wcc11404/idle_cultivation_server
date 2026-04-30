from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.logging.Logger import logger
from app.core.config.ServerConfig import settings
from app.core.db.Models import PlayerData
from app.game.domain.lianli.LianliSystem import LianliSystem
from app.game.domain.task.TaskSystem import TaskSystem


def _get_reset_marker(ts: datetime) -> datetime:
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    else:
        ts = ts.astimezone(timezone.utc)
    reset_time = ts.replace(hour=settings.DAILY_RESET_HOUR, minute=0, second=0, microsecond=0)
    if ts < reset_time:
        return reset_time - timedelta(days=1)
    return reset_time


def run_daily_reset_if_needed(player_data: PlayerData, now: datetime | None = None) -> bool:
    current_time = now or datetime.now(timezone.utc)
    last_daily_reset_at = player_data.last_daily_reset_at

    if last_daily_reset_at.tzinfo is None:
        last_daily_reset_at = last_daily_reset_at.replace(tzinfo=timezone.utc)
    else:
        last_daily_reset_at = last_daily_reset_at.astimezone(timezone.utc)

    if _get_reset_marker(last_daily_reset_at) == _get_reset_marker(current_time):
        return False

    logger.info(f"[GAME] 执行每日重置 - account_id: {player_data.account_id}")

    db_data = player_data.data if isinstance(player_data.data, dict) else {}

    lianli_system = LianliSystem.from_dict(db_data.get("lianli_system", {}))
    lianli_system.reset_daily_dungeons()
    db_data["lianli_system"] = lianli_system.to_dict()

    task_system = TaskSystem.from_dict(db_data.get("task_system", {}))
    task_system.reset_daily_state()
    db_data["task_system"] = task_system.to_dict()

    player_data.data = db_data
    player_data.last_daily_reset_at = current_time
    return True
