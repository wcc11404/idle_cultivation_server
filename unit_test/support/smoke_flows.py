from __future__ import annotations

from unit_test.presets.test_presets import build_preset
from unit_test.support.db_support import (
    set_alchemy_elapsed_seconds,
    set_battle_elapsed_seconds,
)
from unit_test.support.test_api_client import TestApiClient
from unit_test.support.test_support_config import (
    PRESET_ALCHEMY_READY,
    PRESET_BREAKTHROUGH_READY,
    PRESET_FULL_UNLOCK,
    PRESET_LIANLI_READY,
    PRESET_SPELL_READY,
)


def assert_success(result: dict, label: str) -> dict:
    if not result.get("success", False):
        raise AssertionError(f"{label} 失败: {result}")
    return result


def _log(verbose: bool, message: str) -> None:
    if verbose:
        print(message)


def _inventory_counts(inventory_dict: dict) -> dict[str, int]:
    slots = inventory_dict.get("slots", {})
    counts: dict[str, int] = {}
    for slot in slots.values():
        item_id = str(slot.get("id", ""))
        counts[item_id] = counts.get(item_id, 0) + int(slot.get("count", 0))
    return counts


def run_initial_state_smoke(client: TestApiClient, verbose: bool = False) -> dict:
    _log(verbose, "\n=== 验证基础状态与测试礼包 ===")
    assert_success(client.reset_account(), "reset_account")
    state_result = assert_success(client.get_state_summary(), "get_state_summary")
    counts = _inventory_counts(state_result.get("state_summary", {}).get("inventory", {}))
    assert counts.get("starter_pack", 0) == 1, f"初始状态缺少 starter_pack: {state_result}"
    assert counts.get("test_pack", 0) == 1, f"初始状态缺少 test_pack: {state_result}"
    return state_result


def run_breakthrough_smoke(client: TestApiClient, verbose: bool = False) -> dict:
    _log(verbose, "\n=== 突破 smoke ===")
    assert_success(client.reset_account(), "reset_account")
    assert_success(client.apply_preset(PRESET_BREAKTHROUGH_READY), "apply_preset breakthrough_ready")
    result = assert_success(client.breakthrough(), "breakthrough")
    reason_data = result.get("reason_data", {})
    assert reason_data.get("new_realm"), f"突破结果缺少 new_realm: {result}"
    assert int(reason_data.get("new_level", 0)) >= 1, f"突破结果缺少 new_level: {result}"
    return result


def run_alchemy_smoke(client: TestApiClient, verbose: bool = False) -> dict:
    _log(verbose, "\n=== 炼丹 smoke ===")
    assert_success(client.reset_account(), "reset_account")
    assert_success(client.apply_preset(PRESET_ALCHEMY_READY), "apply_preset alchemy_ready")
    assert_success(client.alchemy_recipes(), "alchemy_recipes")
    assert_success(client.alchemy_start(), "alchemy_start")
    set_alchemy_elapsed_seconds(client.account_id, 10.0)
    result = assert_success(client.alchemy_report("health_pill", 1), "alchemy_report")
    assert int(result.get("success_count", 0)) + int(result.get("fail_count", 0)) == 1, (
        f"炼丹结果数量不正确: {result}"
    )
    assert_success(client.alchemy_stop(), "alchemy_stop")
    return result


def run_spell_smoke(client: TestApiClient, verbose: bool = False) -> dict:
    _log(verbose, "\n=== 术法 smoke ===")
    assert_success(client.reset_account(), "reset_account")
    assert_success(client.apply_preset(PRESET_SPELL_READY), "apply_preset spell_ready")
    assert_success(client.spell_list(), "spell_list")
    assert_success(client.spell_unequip("thunder_strike"), "spell_unequip")
    assert_success(client.spell_equip("thunder_strike"), "spell_equip")
    assert_success(client.spell_charge("thunder_strike", 10), "spell_charge")
    result = assert_success(client.spell_upgrade("basic_boxing_techniques"), "spell_upgrade")
    return result


def run_lianli_smoke(client: TestApiClient, verbose: bool = False) -> dict:
    _log(verbose, "\n=== 历练 smoke ===")
    assert_success(client.reset_account(), "reset_account")
    assert_success(client.apply_preset(PRESET_LIANLI_READY), "apply_preset lianli_ready")
    battle_result = assert_success(client.lianli_simulate("area_1"), "lianli_simulate")
    set_battle_elapsed_seconds(client.account_id, float(battle_result.get("total_time", 0.0)) + 1.0)
    finish_result = assert_success(client.lianli_finish(1.0, 9999), "lianli_finish")
    assert finish_result.get("reason_code") in {
        "LIANLI_FINISH_FULLY_SETTLED",
        "LIANLI_FINISH_PARTIALLY_SETTLED",
    }, f"历练结算 reason_code 异常: {finish_result}"
    return finish_result


def run_full_unlock_smoke(client: TestApiClient, verbose: bool = False) -> dict:
    _log(verbose, "\n=== 排行榜与设置 smoke ===")
    assert_success(client.reset_account(), "reset_account")
    assert_success(client.apply_preset(PRESET_FULL_UNLOCK), "apply_preset full_unlock")
    nickname_result = assert_success(client.change_nickname("青松明月"), "change_nickname")
    rank_result = assert_success(client.get_rank(), "get_rank")
    return {
        "nickname": nickname_result,
        "rank": rank_result,
    }


def get_breakthrough_preset_items() -> dict:
    return build_preset(PRESET_BREAKTHROUGH_READY).get("inventory_items", {})
