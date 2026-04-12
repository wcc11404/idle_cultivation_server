#!/usr/bin/env python3
"""测试接口客户端。"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict

import requests

from unit_test.support.test_support_config import TEST_PASSWORD, TEST_USERNAME

BASE_URL = "http://localhost:8444/api"


class TestApiClient:
    __test__ = False

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.token: str | None = None
        self.account_id: str = ""
        self.username: str = ""

    def _request_params(self) -> Dict[str, Any]:
        return {
            "operation_id": str(uuid.uuid4()),
            "timestamp": time.time(),
        }

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def _post(self, path: str, payload: Dict[str, Any] | None = None, auth: bool = True) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}{path}",
            json=payload or {},
            headers=self._headers() if auth else {},
        )
        return response.json()

    def _get(self, path: str, params: Dict[str, Any] | None = None, auth: bool = True) -> Dict[str, Any]:
        response = requests.get(
            f"{self.base_url}{path}",
            params=params or {},
            headers=self._headers() if auth else {},
        )
        return response.json()

    def register_user(self, username: str, password: str) -> Dict[str, Any]:
        payload = {
            "username": username,
            "password": password,
            **self._request_params(),
        }
        result = self._post("/auth/register", payload, auth=False)
        if result.get("success"):
            self.token = str(result.get("token", ""))
            self.username = username
        return result

    def login_user(self, username: str, password: str) -> Dict[str, Any]:
        payload = {
            "username": username,
            "password": password,
            **self._request_params(),
        }
        result = self._post("/auth/login", payload, auth=False)
        if result.get("success"):
            self.token = str(result.get("token", ""))
            self.account_id = str(result.get("account_info", {}).get("id", ""))
            self.username = username
        return result

    def login_test_account(self) -> Dict[str, Any]:
        return self.login_user(TEST_USERNAME, TEST_PASSWORD)

    def get_game_data(self) -> Dict[str, Any]:
        return self._get("/game/data")

    def save_game(self, data: Dict[str, Any]) -> Dict[str, Any]:
        payload = {"data": data, **self._request_params()}
        return self._post("/game/save", payload)

    def claim_offline_reward(self) -> Dict[str, Any]:
        return self._post("/game/claim_offline_reward", self._request_params())

    def reset_account(self) -> Dict[str, Any]:
        return self._post("/test/reset_account", self._request_params())

    def apply_preset(self, preset_name: str) -> Dict[str, Any]:
        payload = {
            "preset_name": preset_name,
            **self._request_params(),
        }
        return self._post("/test/apply_preset", payload)

    def set_player_state(self, **kwargs: Any) -> Dict[str, Any]:
        payload = {**kwargs, **self._request_params()}
        return self._post("/test/set_player_state", payload)

    def set_inventory_items(self, items: Dict[str, int]) -> Dict[str, Any]:
        payload = {"items": items, **self._request_params()}
        return self._post("/test/set_inventory_items", payload)

    def unlock_content(self, spell_ids=None, recipe_ids=None, furnace_ids=None) -> Dict[str, Any]:
        payload = {
            "spell_ids": spell_ids or [],
            "recipe_ids": recipe_ids or [],
            "furnace_ids": furnace_ids or [],
            **self._request_params(),
        }
        return self._post("/test/unlock_content", payload)

    def set_equipped_spells(self, breathing=None, active=None, opening=None) -> Dict[str, Any]:
        payload = {
            "breathing": breathing or [],
            "active": active or [],
            "opening": opening or [],
            **self._request_params(),
        }
        return self._post("/test/set_equipped_spells", payload)

    def set_progress_state(self, tower_highest_floor=None, daily_dungeon_remaining_counts=None) -> Dict[str, Any]:
        payload = {
            "tower_highest_floor": tower_highest_floor,
            "daily_dungeon_remaining_counts": daily_dungeon_remaining_counts or {},
            **self._request_params(),
        }
        return self._post("/test/set_progress_state", payload)

    def set_runtime_state(self, **kwargs: Any) -> Dict[str, Any]:
        payload = {**kwargs, **self._request_params()}
        return self._post("/test/set_runtime_state", payload)

    def grant_test_pack(self) -> Dict[str, Any]:
        return self._post("/test/grant_test_pack", self._request_params())

    def get_state_summary(self) -> Dict[str, Any]:
        return self._get("/test/state_summary")

    def breakthrough(self) -> Dict[str, Any]:
        return self._post("/game/player/breakthrough", self._request_params())

    def cultivation_start(self) -> Dict[str, Any]:
        return self._post("/game/player/cultivation/start", self._request_params())

    def cultivation_report(self, count: int) -> Dict[str, Any]:
        payload = {"count": count, **self._request_params()}
        return self._post("/game/player/cultivation/report", payload)

    def cultivation_stop(self) -> Dict[str, Any]:
        return self._post("/game/player/cultivation/stop", self._request_params())

    def inventory_use(self, item_id: str) -> Dict[str, Any]:
        payload = {"item_id": item_id, **self._request_params()}
        return self._post("/game/inventory/use", payload)

    def inventory_organize(self) -> Dict[str, Any]:
        return self._post("/game/inventory/organize", self._request_params())

    def inventory_discard(self, item_id: str, count: int = 1) -> Dict[str, Any]:
        payload = {"item_id": item_id, "count": count, **self._request_params()}
        return self._post("/game/inventory/discard", payload)

    def inventory_expand(self) -> Dict[str, Any]:
        return self._post("/game/inventory/expand", self._request_params())

    def inventory_list(self) -> Dict[str, Any]:
        return self._get("/game/inventory/list")

    def alchemy_start(self) -> Dict[str, Any]:
        return self._post("/game/alchemy/start", self._request_params())

    def alchemy_recipes(self) -> Dict[str, Any]:
        return self._get("/game/alchemy/recipes")

    def alchemy_report(self, recipe_id: str, count: int = 1) -> Dict[str, Any]:
        payload = {"recipe_id": recipe_id, "count": count, **self._request_params()}
        return self._post("/game/alchemy/report", payload)

    def alchemy_stop(self) -> Dict[str, Any]:
        return self._post("/game/alchemy/stop", self._request_params())

    def spell_equip(self, spell_id: str) -> Dict[str, Any]:
        payload = {"spell_id": spell_id, **self._request_params()}
        return self._post("/game/spell/equip", payload)

    def spell_unequip(self, spell_id: str) -> Dict[str, Any]:
        payload = {"spell_id": spell_id, **self._request_params()}
        return self._post("/game/spell/unequip", payload)

    def spell_upgrade(self, spell_id: str) -> Dict[str, Any]:
        payload = {"spell_id": spell_id, **self._request_params()}
        return self._post("/game/spell/upgrade", payload)

    def spell_charge(self, spell_id: str, amount: int) -> Dict[str, Any]:
        payload = {"spell_id": spell_id, "amount": amount, **self._request_params()}
        return self._post("/game/spell/charge", payload)

    def spell_list(self) -> Dict[str, Any]:
        return self._get("/game/spell/list")

    def lianli_simulate(self, area_id: str) -> Dict[str, Any]:
        payload = {"area_id": area_id, **self._request_params()}
        return self._post("/game/lianli/simulate", payload)

    def lianli_finish(self, speed: float = 1.0, index: int | None = 9999) -> Dict[str, Any]:
        payload = {"speed": speed, "index": index, **self._request_params()}
        return self._post("/game/lianli/finish", payload)

    def dungeon_info(self) -> Dict[str, Any]:
        return self._get("/game/dungeon/foundation_herb_cave")

    def tower_highest_floor(self) -> Dict[str, Any]:
        return self._get("/game/tower/highest_floor")

    def get_rank(self) -> Dict[str, Any]:
        return self._get("/game/rank", auth=False)

    def change_nickname(self, nickname: str) -> Dict[str, Any]:
        payload = {"nickname": nickname, **self._request_params()}
        return self._post("/auth/change_nickname", payload)

    def change_avatar(self, avatar_id: str) -> Dict[str, Any]:
        payload = {"avatar_id": avatar_id, **self._request_params()}
        return self._post("/auth/change_avatar", payload)

    def refresh(self) -> Dict[str, Any]:
        return self._post("/auth/refresh", {}, auth=True)

    def logout(self) -> Dict[str, Any]:
        return self._post("/auth/logout", {}, auth=True)
