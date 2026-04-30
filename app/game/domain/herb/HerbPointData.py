"""采集点配置查询。"""

import json
import os
from typing import Any, Dict
from pathlib import Path


class HerbPointData:
    _POINTS_CONFIG: Dict[str, Any] = {}
    _LOADED: bool = False

    @classmethod
    def _load_config(cls):
        if cls._LOADED:
            return
        path = Path(__file__).resolve().parents[2] / "content" / "herb" / "herb_points.json"
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            cls._POINTS_CONFIG = data.get("points", {})
            cls._LOADED = True
        except Exception:
            cls._POINTS_CONFIG = {}

    @classmethod
    def point_exists(cls, point_id: str) -> bool:
        cls._load_config()
        return point_id in cls._POINTS_CONFIG

    @classmethod
    def get_point(cls, point_id: str) -> Dict[str, Any]:
        cls._load_config()
        return dict(cls._POINTS_CONFIG.get(point_id, {}))

    @classmethod
    def get_all_points(cls) -> Dict[str, Any]:
        cls._load_config()
        return {k: dict(v) for k, v in cls._POINTS_CONFIG.items()}
