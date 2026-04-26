"""任务系统状态与领奖逻辑。"""

from __future__ import annotations

from typing import Any

from .TaskData import TaskData


class TaskSystem:
    def __init__(self, daily_tasks: dict[str, dict[str, Any]] | None = None, newbie_tasks: dict[str, dict[str, Any]] | None = None):
        self.daily_tasks: dict[str, dict[str, Any]] = daily_tasks or {}
        self.newbie_tasks: dict[str, dict[str, Any]] = newbie_tasks or {}
        self.ensure_task_states()

    @staticmethod
    def _default_state() -> dict[str, Any]:
        return {
            "progress": 0,
            "claimed": False,
        }

    @staticmethod
    def _normalize_state(raw_state: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(raw_state, dict):
            return TaskSystem._default_state()
        return {
            "progress": max(0, int(raw_state.get("progress", 0))),
            "claimed": bool(raw_state.get("claimed", False)),
        }

    def ensure_task_states(self) -> None:
        for task in TaskData.get_daily_tasks():
            task_id = str(task.get("task_id", ""))
            if not task_id:
                continue
            self.daily_tasks[task_id] = self._normalize_state(self.daily_tasks.get(task_id))
        for task in TaskData.get_newbie_tasks():
            task_id = str(task.get("task_id", ""))
            if not task_id:
                continue
            self.newbie_tasks[task_id] = self._normalize_state(self.newbie_tasks.get(task_id))

    def reset_daily_state(self) -> None:
        self.daily_tasks = {}
        for task in TaskData.get_daily_tasks():
            task_id = str(task.get("task_id", ""))
            if task_id:
                self.daily_tasks[task_id] = self._default_state()

    def _get_state_bucket(self, task_type: str) -> dict[str, dict[str, Any]]:
        return self.daily_tasks if task_type == "daily" else self.newbie_tasks

    def add_progress(self, task_id: str, delta: int) -> int:
        if delta <= 0:
            return 0
        task_type, task_def = TaskData.get_task_definition(task_id)
        if not task_def:
            return 0
        bucket = self._get_state_bucket(task_type)
        state = self._normalize_state(bucket.get(task_id))
        target = max(0, int(task_def.get("target", 0)))
        current = int(state.get("progress", 0))
        next_progress = min(target, current + int(delta))
        state["progress"] = next_progress
        bucket[task_id] = state
        return next_progress - current

    def _is_completed(self, task_id: str, task_type: str, task_def: dict[str, Any]) -> bool:
        bucket = self._get_state_bucket(task_type)
        state = self._normalize_state(bucket.get(task_id))
        return int(state.get("progress", 0)) >= int(task_def.get("target", 0))

    def get_task_list_payload(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        daily_payload: list[dict[str, Any]] = []
        newbie_payload: list[dict[str, Any]] = []

        for task in TaskData.get_daily_tasks():
            task_id = str(task.get("task_id", ""))
            state = self._normalize_state(self.daily_tasks.get(task_id))
            target = int(task.get("target", 0))
            progress = min(int(state.get("progress", 0)), target)
            daily_payload.append({
                "task_id": task_id,
                "name": str(task.get("name", "")),
                "description": str(task.get("description", "")),
                "task_type": "daily",
                "progress": progress,
                "target": target,
                "completed": progress >= target,
                "claimed": bool(state.get("claimed", False)),
                "sort_order": int(task.get("sort_order", 0)),
                "rewards": task.get("rewards", {}),
            })

        for task in TaskData.get_newbie_tasks():
            task_id = str(task.get("task_id", ""))
            state = self._normalize_state(self.newbie_tasks.get(task_id))
            target = int(task.get("target", 0))
            progress = min(int(state.get("progress", 0)), target)
            newbie_payload.append({
                "task_id": task_id,
                "name": str(task.get("name", "")),
                "description": str(task.get("description", "")),
                "task_type": "newbie",
                "progress": progress,
                "target": target,
                "completed": progress >= target,
                "claimed": bool(state.get("claimed", False)),
                "sort_order": int(task.get("sort_order", 0)),
                "rewards": task.get("rewards", {}),
            })

        return daily_payload, newbie_payload

    def claim_task(self, task_id: str, inventory_system) -> dict[str, Any]:
        task_type, task_def = TaskData.get_task_definition(task_id)
        if not task_def:
            return {
                "success": False,
                "reason_code": "TASK_CLAIM_TASK_NOT_FOUND",
                "reason_data": {"task_id": task_id},
                "rewards_granted": {},
            }

        bucket = self._get_state_bucket(task_type)
        state = self._normalize_state(bucket.get(task_id))
        target = int(task_def.get("target", 0))
        if int(state.get("progress", 0)) < target:
            return {
                "success": False,
                "reason_code": "TASK_CLAIM_NOT_COMPLETED",
                "reason_data": {"task_id": task_id},
                "rewards_granted": {},
            }
        if bool(state.get("claimed", False)):
            return {
                "success": False,
                "reason_code": "TASK_CLAIM_ALREADY_CLAIMED",
                "reason_data": {"task_id": task_id},
                "rewards_granted": {},
            }

        rewards = task_def.get("rewards", {})
        rewards_granted: dict[str, int] = {}
        if isinstance(rewards, dict):
            for item_id, amount in rewards.items():
                added = int(inventory_system.add_item(str(item_id), int(amount)))
                if added > 0:
                    rewards_granted[str(item_id)] = added

        state["claimed"] = True
        bucket[task_id] = state
        return {
            "success": True,
            "reason_code": "TASK_CLAIM_SUCCEEDED",
            "reason_data": {"task_id": task_id},
            "rewards_granted": rewards_granted,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "daily_tasks": self.daily_tasks,
            "newbie_tasks": self.newbie_tasks,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TaskSystem":
        if not isinstance(data, dict):
            return cls()
        return cls(
            daily_tasks=data.get("daily_tasks", {}),
            newbie_tasks=data.get("newbie_tasks", {}),
        )

