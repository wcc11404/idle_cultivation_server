from __future__ import annotations

from unit_test.support.TestApiClient import TestApiClient
from unit_test.support.DbSupport import (
    set_alchemy_elapsed_seconds,
    set_cultivation_elapsed_seconds,
    set_herb_elapsed_seconds,
    set_last_daily_reset_seconds_ago,
    set_offline_seconds,
)


def _find_task(tasks: list[dict], task_id: str) -> dict:
    for task in tasks:
        if str(task.get("task_id", "")) == task_id:
            return task
    return {}


def _count_item_in_slots(data: dict, item_id: str) -> int:
    slots = data.get("data", {}).get("inventory", {}).get("slots", {})
    total = 0
    if isinstance(slots, dict):
        for slot in slots.values():
            if isinstance(slot, dict) and str(slot.get("id", "")) == item_id:
                total += int(slot.get("count", 0))
    return total


def test_task_list_and_claim_edge_cases(reset_client_state: TestApiClient):
    listed = reset_client_state.task_list()
    assert listed["success"] is True
    assert listed["reason_code"] == "TASK_LIST_SUCCEEDED"
    assert isinstance(listed.get("daily_tasks", []), list)
    assert isinstance(listed.get("newbie_tasks", []), list)

    not_completed = reset_client_state.task_claim("daily_battle_count")
    assert not_completed["success"] is False
    assert not_completed["reason_code"] == "TASK_CLAIM_NOT_COMPLETED"

    not_found = reset_client_state.task_claim("not_exists_task")
    assert not_found["success"] is False
    assert not_found["reason_code"] == "TASK_CLAIM_TASK_NOT_FOUND"


def test_task_newbie_pack_progress_and_claim(reset_client_state: TestApiClient):
    use_pack = reset_client_state.inventory_use("starter_pack")
    assert use_pack["success"] is True

    listed = reset_client_state.task_list()
    newbie_task = _find_task(listed.get("newbie_tasks", []), "newbie_open_starter_pack_1")
    assert newbie_task
    assert int(newbie_task.get("progress", 0)) == 1
    assert int(newbie_task.get("target", 0)) == 1
    assert bool(newbie_task.get("completed", False)) is True
    assert bool(newbie_task.get("claimed", False)) is False

    before_data = reset_client_state.get_game_data()
    before_count = _count_item_in_slots(before_data, "spirit_stone")

    claimed = reset_client_state.task_claim("newbie_open_starter_pack_1")
    assert claimed["success"] is True
    assert claimed["reason_code"] == "TASK_CLAIM_SUCCEEDED"
    assert int(claimed.get("rewards_granted", {}).get("spirit_stone", 0)) == 1

    claimed_again = reset_client_state.task_claim("newbie_open_starter_pack_1")
    assert claimed_again["success"] is False
    assert claimed_again["reason_code"] == "TASK_CLAIM_ALREADY_CLAIMED"

    after_data = reset_client_state.get_game_data()
    after_count = _count_item_in_slots(after_data, "spirit_stone")
    assert after_count >= before_count + 1


def test_task_daily_progress_capped(reset_client_state: TestApiClient):
    reset_client_state.set_player_state(realm="金丹期", realm_level=1, spirit_energy=0.0, health=99999.0)
    start = reset_client_state.cultivation_start()
    assert start["success"] is True

    # 一次大秒数上报，进度也应封顶到 60 / 60。
    set_cultivation_elapsed_seconds(reset_client_state.account_id, 120.0)
    report = reset_client_state.cultivation_report(120.0)
    assert report["success"] is True

    listed = reset_client_state.task_list()
    daily_task = _find_task(listed.get("daily_tasks", []), "daily_cultivation_seconds")
    assert daily_task
    assert int(daily_task.get("progress", 0)) == 60
    assert int(daily_task.get("target", 0)) == 60


def test_task_daily_reset_only_resets_daily(reset_client_state: TestApiClient, base_url: str):
    use_pack = reset_client_state.inventory_use("starter_pack")
    assert use_pack["success"] is True
    reset_client_state.set_player_state(realm="金丹期", realm_level=1, spirit_energy=0.0, health=99999.0)
    assert reset_client_state.cultivation_start()["success"] is True
    set_cultivation_elapsed_seconds(reset_client_state.account_id, 70.0)
    assert reset_client_state.cultivation_report(70.0)["success"] is True

    before_reset = reset_client_state.task_list()
    before_daily = _find_task(before_reset.get("daily_tasks", []), "daily_cultivation_seconds")
    before_newbie = _find_task(before_reset.get("newbie_tasks", []), "newbie_open_starter_pack_1")
    assert int(before_daily.get("progress", 0)) > 0
    assert int(before_newbie.get("progress", 0)) == 1

    assert reset_client_state.logout().get("success") is True
    set_offline_seconds(reset_client_state.account_id, 90000)
    set_last_daily_reset_seconds_ago(reset_client_state.account_id, 90000)

    login_client = TestApiClient(base_url)
    login_result = login_client.login_test_account()
    assert login_result.get("success") is True
    listed_after = login_client.task_list()

    after_daily = _find_task(listed_after.get("daily_tasks", []), "daily_cultivation_seconds")
    after_newbie = _find_task(listed_after.get("newbie_tasks", []), "newbie_open_starter_pack_1")
    assert int(after_daily.get("progress", 0)) == 0
    assert bool(after_daily.get("claimed", False)) is False
    assert int(after_newbie.get("progress", 0)) == 1


def test_task_daily_reset_triggers_on_write_after_cross_day_while_online(reset_client_state: TestApiClient):
    reset_client_state.set_player_state(realm="金丹期", realm_level=1, spirit_energy=0.0, health=99999.0)
    assert reset_client_state.cultivation_start()["success"] is True
    set_cultivation_elapsed_seconds(reset_client_state.account_id, 70.0)
    assert reset_client_state.cultivation_report(70.0)["success"] is True

    before_reset = reset_client_state.task_list()
    before_daily = _find_task(before_reset.get("daily_tasks", []), "daily_cultivation_seconds")
    assert int(before_daily.get("progress", 0)) > 0

    set_last_daily_reset_seconds_ago(reset_client_state.account_id, 90000)

    # 不重新登录，直接写接口触发公共写上下文中的每日重置
    sort_result = reset_client_state.inventory_organize()
    assert sort_result.get("success") is True

    after_reset = reset_client_state.task_list()
    after_daily = _find_task(after_reset.get("daily_tasks", []), "daily_cultivation_seconds")
    assert int(after_daily.get("progress", 0)) == 0
    assert bool(after_daily.get("claimed", False)) is False


def test_task_newbie_herb_gather_10_and_20_claim_rewards(reset_client_state: TestApiClient):
    start_result = reset_client_state.herb_start("point_low_yield")
    assert start_result.get("success") is True

    for _ in range(10):
        set_herb_elapsed_seconds(reset_client_state.account_id, 20.0, point_id="point_low_yield")
        report = reset_client_state.herb_report()
        assert report.get("success") is True

    listed_10 = reset_client_state.task_list()
    task_10 = _find_task(listed_10.get("newbie_tasks", []), "newbie_herb_gather_10")
    assert task_10
    assert int(task_10.get("progress", 0)) == 10
    assert bool(task_10.get("completed", False)) is True
    claim_10 = reset_client_state.task_claim("newbie_herb_gather_10")
    assert claim_10.get("success") is True
    assert int(claim_10.get("rewards_granted", {}).get("recipe_health_pill", 0)) == 1

    for _ in range(10):
        set_herb_elapsed_seconds(reset_client_state.account_id, 20.0, point_id="point_low_yield")
        report = reset_client_state.herb_report()
        assert report.get("success") is True

    listed = reset_client_state.task_list()
    task = _find_task(listed.get("newbie_tasks", []), "newbie_herb_gather_20")
    assert task
    assert int(task.get("progress", 0)) == 20
    assert bool(task.get("completed", False)) is True
    assert bool(task.get("claimed", False)) is False

    claim_result = reset_client_state.task_claim("newbie_herb_gather_20")
    assert claim_result.get("success") is True
    assert int(claim_result.get("rewards_granted", {}).get("spell_alchemy", 0)) == 1


def test_task_newbie_craft_foundation_pill_and_claim_furnace(reset_client_state: TestApiClient):
    preset = reset_client_state.apply_preset("alchemy_ready")
    assert preset.get("success") is True

    start_result = reset_client_state.alchemy_start()
    assert start_result.get("success") is True

    crafted = False
    for _ in range(12):
        set_alchemy_elapsed_seconds(reset_client_state.account_id, 60.0)
        report = reset_client_state.alchemy_report("foundation_pill", 1)
        assert report.get("success") is True
        if int(report.get("success_count", 0)) > 0:
            crafted = True
            break

    assert crafted is True

    listed = reset_client_state.task_list()
    task = _find_task(listed.get("newbie_tasks", []), "newbie_craft_foundation_pill_once")
    assert task
    assert int(task.get("progress", 0)) == 1
    assert bool(task.get("completed", False)) is True
    assert bool(task.get("claimed", False)) is False

    claim_result = reset_client_state.task_claim("newbie_craft_foundation_pill_once")
    assert claim_result.get("success") is True
    assert int(claim_result.get("rewards_granted", {}).get("alchemy_furnace", 0)) == 1


def test_task_newbie_craft_health_pill_20_and_claim_recipe(reset_client_state: TestApiClient):
    preset = reset_client_state.apply_preset("alchemy_ready")
    assert preset.get("success") is True

    start_result = reset_client_state.alchemy_start()
    assert start_result.get("success") is True

    total_success = 0
    for _ in range(4):
        set_alchemy_elapsed_seconds(reset_client_state.account_id, 120.0)
        report = reset_client_state.alchemy_report("health_pill", 20)
        assert report.get("success") is True
        total_success += int(report.get("success_count", 0))
        if total_success >= 20:
            break

    assert total_success >= 20

    listed = reset_client_state.task_list()
    task = _find_task(listed.get("newbie_tasks", []), "newbie_craft_health_pill_20")
    assert task
    assert int(task.get("progress", 0)) == 20
    assert bool(task.get("completed", False)) is True
    assert bool(task.get("claimed", False)) is False

    claim_result = reset_client_state.task_claim("newbie_craft_health_pill_20")
    assert claim_result.get("success") is True
    assert int(claim_result.get("rewards_granted", {}).get("recipe_spirit_pill", 0)) == 1
