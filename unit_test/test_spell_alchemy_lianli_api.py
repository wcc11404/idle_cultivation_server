from unit_test.support.db_support import (
    set_alchemy_elapsed_seconds,
    set_battle_elapsed_seconds,
)


def test_spell_endpoints_and_battle_lock(reset_client_state):
    preset = reset_client_state.apply_preset("spell_ready")
    assert preset["success"] is True

    spell_list = reset_client_state.spell_list()
    assert spell_list["success"] is True
    assert spell_list["reason_code"] == "SPELL_LIST_SUCCEEDED"

    unequip = reset_client_state.spell_unequip("thunder_strike")
    assert unequip["success"] is True
    assert unequip["reason_code"] == "SPELL_UNEQUIP_SUCCEEDED"

    equip = reset_client_state.spell_equip("thunder_strike")
    assert equip["success"] is True
    assert equip["reason_code"] == "SPELL_EQUIP_SUCCEEDED"

    charge = reset_client_state.spell_charge("thunder_strike", 10)
    assert charge["success"] is True

    upgrade = reset_client_state.spell_upgrade("basic_boxing_techniques")
    assert upgrade["success"] is True

    reset_client_state.apply_preset("lianli_ready")
    simulate = reset_client_state.lianli_simulate("area_1")
    assert simulate["success"] is True

    for result in [
        reset_client_state.spell_equip("basic_boxing_techniques"),
        reset_client_state.spell_unequip("basic_boxing_techniques"),
        reset_client_state.spell_upgrade("basic_boxing_techniques"),
        reset_client_state.spell_charge("basic_boxing_techniques", 10),
    ]:
        assert result["success"] is False
        assert result["reason_code"] == "SPELL_ACTION_BATTLE_LOCKED"

    set_battle_elapsed_seconds(reset_client_state.account_id, float(simulate["total_time"]) + 1.0)
    finish = reset_client_state.lianli_finish(1.0, 9999)
    assert finish["success"] is True


def test_alchemy_endpoints(reset_client_state):
    preset = reset_client_state.apply_preset("alchemy_ready")
    assert preset["success"] is True

    recipes = reset_client_state.alchemy_recipes()
    assert recipes["success"] is True
    assert recipes["reason_code"] == "ALCHEMY_RECIPES_SUCCEEDED"

    start = reset_client_state.alchemy_start()
    assert start["success"] is True
    assert start["reason_code"] == "ALCHEMY_START_SUCCEEDED"

    bad_recipe = reset_client_state.alchemy_report("missing_recipe", 1)
    assert bad_recipe["success"] is False
    assert bad_recipe["reason_code"] == "ALCHEMY_REPORT_RECIPE_NOT_FOUND"

    set_alchemy_elapsed_seconds(reset_client_state.account_id, 10.0)
    report = reset_client_state.alchemy_report("health_pill", 1)
    assert report["success"] is True
    assert report["reason_code"] == "ALCHEMY_REPORT_SUCCEEDED"
    assert report["success_count"] + report["fail_count"] == 1

    stop = reset_client_state.alchemy_stop()
    assert stop["success"] is True
    assert stop["reason_code"] == "ALCHEMY_STOP_SUCCEEDED"

    not_active = reset_client_state.alchemy_report("health_pill", 1)
    assert not_active["success"] is False
    assert not_active["reason_code"] == "ALCHEMY_REPORT_NOT_ACTIVE"


def test_lianli_endpoints(reset_client_state):
    progress = reset_client_state.set_progress_state(
        tower_highest_floor=9,
        daily_dungeon_remaining_counts={"foundation_herb_cave": 2},
    )
    assert progress["success"] is True

    dungeon_info = reset_client_state.dungeon_info()
    assert dungeon_info["success"] is True
    assert dungeon_info["reason_code"] == "LIANLI_DUNGEON_INFO_SUCCEEDED"
    assert dungeon_info["remaining_count"] == 2

    tower = reset_client_state.tower_highest_floor()
    assert tower["success"] is True
    assert tower["reason_code"] == "LIANLI_TOWER_INFO_SUCCEEDED"
    assert tower["highest_floor"] == 9

    reset_client_state.set_runtime_state(is_cultivating=True)
    blocked_by_cultivation = reset_client_state.lianli_simulate("area_1")
    assert blocked_by_cultivation["success"] is False
    assert blocked_by_cultivation["reason_code"] == "LIANLI_SIMULATE_BLOCKED_BY_CULTIVATION"

    reset_client_state.reset_account()
    reset_client_state.set_runtime_state(is_alchemizing=True)
    blocked_by_alchemy = reset_client_state.lianli_simulate("area_1")
    assert blocked_by_alchemy["success"] is False
    assert blocked_by_alchemy["reason_code"] == "LIANLI_SIMULATE_BLOCKED_BY_ALCHEMY"

    reset_client_state.apply_preset("lianli_ready")
    simulate = reset_client_state.lianli_simulate("area_1")
    assert simulate["success"] is True
    assert simulate["reason_code"] == "LIANLI_SIMULATE_SUCCEEDED"
    assert simulate["battle_timeline"]

    cancel_before_action = reset_client_state.lianli_finish(1.0, -1)
    assert cancel_before_action["success"] is True
    assert cancel_before_action["reason_code"] == "LIANLI_FINISH_PARTIALLY_SETTLED"
    assert int(cancel_before_action["settled_index"]) == 0
    assert bool(cancel_before_action["reason_data"].get("cancel_before_action", False)) is True

    simulate = reset_client_state.lianli_simulate("area_1")
    assert simulate["success"] is True

    set_battle_elapsed_seconds(reset_client_state.account_id, float(simulate["total_time"]) + 1.0)
    finish = reset_client_state.lianli_finish(1.0, 9999)
    assert finish["success"] is True
    assert finish["reason_code"] == "LIANLI_FINISH_FULLY_SETTLED"
    assert finish["settled_index"] == finish["total_index"]


def test_lianli_finish_keeps_runtime_heal_delta(reset_client_state):
    reset_client_state.apply_preset("lianli_ready")
    reset_client_state.set_player_state(health=40.0)
    reset_client_state.set_inventory_items({"health_pill": 1})

    simulate = reset_client_state.lianli_simulate("area_1")
    assert simulate["success"] is True

    heal_result = reset_client_state.inventory_use("health_pill")
    assert heal_result["success"] is True

    state_after_heal = reset_client_state.get_state_summary()
    assert state_after_heal["success"] is True
    realtime_health_after_heal = float(state_after_heal["state_summary"]["player"]["health"])
    assert realtime_health_after_heal > 40.0

    set_battle_elapsed_seconds(reset_client_state.account_id, float(simulate["total_time"]) + 1.0)
    finish = reset_client_state.lianli_finish(1.0, 9999)
    assert finish["success"] is True

    simulated_delta = round(float(simulate["player_health_after"]) - float(simulate["player_health_before"]), 2)
    expected_health = round(max(0.0, realtime_health_after_heal + simulated_delta), 2)
    assert float(finish["player_health_after"]) == expected_health


def test_lianli_finish_skips_health_delta_when_realm_changed(reset_client_state):
    reset_client_state.apply_preset("lianli_ready")
    simulate = reset_client_state.lianli_simulate("area_1")
    assert simulate["success"] is True

    # 战斗中突破/改境界后，结算不再应用该场战斗的扣血增量。
    realm_changed = reset_client_state.set_player_state(realm="筑基期", realm_level=1, health=220.0)
    assert realm_changed["success"] is True

    state_after_realm_change = reset_client_state.get_state_summary()
    assert state_after_realm_change["success"] is True
    health_after_realm_change = float(state_after_realm_change["state_summary"]["player"]["health"])

    set_battle_elapsed_seconds(reset_client_state.account_id, float(simulate["total_time"]) + 1.0)
    finish = reset_client_state.lianli_finish(1.0, 9999)
    assert finish["success"] is True
    assert bool(finish.get("reason_data", {}).get("realm_changed_during_battle", False)) is True
    assert float(finish["player_health_after"]) == health_after_realm_change
