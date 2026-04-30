"""采集运行态系统。"""

from __future__ import annotations

from random import randint, random
from typing import Any, Dict

from .HerbPointData import HerbPointData


class HerbGatherSystem:
    def __init__(self):
        self.is_gathering: bool = False
        self.current_point_id: str = ""
        self.last_report_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_gathering": self.is_gathering,
            "current_point_id": self.current_point_id,
            "last_report_time": self.last_report_time,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HerbGatherSystem":
        obj = cls()
        if not isinstance(data, dict):
            return obj
        obj.is_gathering = bool(data.get("is_gathering", False))
        obj.current_point_id = str(data.get("current_point_id", ""))
        obj.last_report_time = float(data.get("last_report_time", 0.0))
        return obj

    def reset_gather_state(self):
        self.is_gathering = False
        self.current_point_id = ""
        self.last_report_time = 0.0

    @staticmethod
    def settle_once(point_id: str, success_rate_bonus: float = 0.0) -> Dict[str, Any]:
        point = HerbPointData.get_point(point_id)
        if not point:
            return {
                "success": False,
                "reason_code": "HERB_REPORT_POINT_NOT_FOUND",
                "drops_gained": {},
                "success_roll": False,
                "point_id": point_id,
            }

        base_success_rate = float(point.get("success_rate", 0.0))
        success_rate = max(0.0, min(base_success_rate + max(success_rate_bonus, 0.0), 1.0))
        success_roll = random() <= success_rate
        drops_gained: Dict[str, int] = {}
        if success_roll:
            for drop in point.get("drops", []):
                item_id = str(drop.get("item_id", ""))
                if not item_id:
                    continue
                chance = float(drop.get("chance", 0.0))
                if random() > chance:
                    continue
                min_amount = int(drop.get("min", 0))
                max_amount = int(drop.get("max", 0))
                if min_amount <= 0 or max_amount < min_amount:
                    continue
                drops_gained[item_id] = drops_gained.get(item_id, 0) + randint(min_amount, max_amount)

        return {
            "success": True,
            "reason_code": "HERB_REPORT_SUCCEEDED",
            "drops_gained": drops_gained,
            "success_roll": success_roll,
            "point_id": point_id,
            "base_success_rate": base_success_rate,
            "effective_success_rate": success_rate,
        }
