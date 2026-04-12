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
    simulate = reset_client_state.lianli_simulate("qi_refining_outer")
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
    blocked_by_cultivation = reset_client_state.lianli_simulate("qi_refining_outer")
    assert blocked_by_cultivation["success"] is False
    assert blocked_by_cultivation["reason_code"] == "LIANLI_SIMULATE_BLOCKED_BY_CULTIVATION"

    reset_client_state.reset_account()
    reset_client_state.set_runtime_state(is_alchemizing=True)
    blocked_by_alchemy = reset_client_state.lianli_simulate("qi_refining_outer")
    assert blocked_by_alchemy["success"] is False
    assert blocked_by_alchemy["reason_code"] == "LIANLI_SIMULATE_BLOCKED_BY_ALCHEMY"

    reset_client_state.apply_preset("lianli_ready")
    simulate = reset_client_state.lianli_simulate("qi_refining_outer")
    assert simulate["success"] is True
    assert simulate["reason_code"] == "LIANLI_SIMULATE_SUCCEEDED"
    assert simulate["battle_timeline"]

    set_battle_elapsed_seconds(reset_client_state.account_id, float(simulate["total_time"]) + 1.0)
    finish = reset_client_state.lianli_finish(1.0, 9999)
    assert finish["success"] is True
    assert finish["reason_code"] == "LIANLI_FINISH_FULLY_SETTLED"
    assert finish["settled_index"] == finish["total_index"]
