"""任务配置读取。"""

from __future__ import annotations

import json
import os
from typing import Any


class TaskData:
    _config: dict[str, Any] | None = None

    @classmethod
    def _config_path(cls) -> str:
        return os.path.join(os.path.dirname(__file__), "tasks.json")

    @classmethod
    def _load_config(cls) -> dict[str, Any]:
        if cls._config is None:
            with open(cls._config_path(), "r", encoding="utf-8") as f:
                cls._config = json.load(f)
        return cls._config

    @classmethod
    def get_daily_tasks(cls) -> list[dict[str, Any]]:
        cfg = cls._load_config()
        return list(cfg.get("daily_tasks", []))

    @classmethod
    def get_newbie_tasks(cls) -> list[dict[str, Any]]:
        cfg = cls._load_config()
        return list(cfg.get("newbie_tasks", []))

    @classmethod
    def get_task_definition(cls, task_id: str) -> tuple[str, dict[str, Any] | None]:
        for item in cls.get_daily_tasks():
            if str(item.get("task_id", "")) == task_id:
                return "daily", item
        for item in cls.get_newbie_tasks():
            if str(item.get("task_id", "")) == task_id:
                return "newbie", item
        return "", None

