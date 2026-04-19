from app.modules.inventory.ItemData import ItemData


def _inventory_counts(state_summary: dict) -> dict[str, int]:
    counts: dict[str, int] = {}
    for slot in state_summary.get("inventory", {}).get("slots", {}).values():
        item_id = str(slot.get("id", ""))
        counts[item_id] = counts.get(item_id, 0) + int(slot.get("count", 0))
    return counts


def test_reset_account_restores_initial_inventory(reset_client_state):
    open_pack = reset_client_state.inventory_use("test_pack")
    assert open_pack["success"] is True

    reset_result = reset_client_state.reset_account()
    assert reset_result["success"] is True
    counts = _inventory_counts(reset_result["state_summary"])
    assert counts.get("starter_pack", 0) == 1
    assert counts.get("test_pack", 0) == 1


def test_set_player_state_clamps_values(reset_client_state):
    result = reset_client_state.set_player_state(
        realm="炼气期",
        realm_level=1,
        spirit_energy=999999.0,
        health=999999.0,
    )
    assert result["success"] is True
    player = result["state_summary"]["player"]
    assert player["realm"] == "炼气期"
    assert player["realm_level"] == 1
    assert player["health"] < 999999.0
    assert player["spirit_energy"] < 999999.0


def test_set_player_state_rejects_invalid_level(reset_client_state):
    result = reset_client_state.set_player_state(realm="炼气期", realm_level=999)
    assert result["success"] is False
    assert result["reason_code"] == "TEST_SET_PLAYER_STATE_LEVEL_INVALID"


def test_set_inventory_items_exact_and_remove_zero(reset_client_state):
    result = reset_client_state.set_inventory_items({
        "health_pill": 2,
        "spirit_pill": 0,
    })
    assert result["success"] is True
    counts = _inventory_counts(result["state_summary"])
    assert counts.get("health_pill", 0) == 2
    assert counts.get("spirit_pill", 0) == 0


def test_set_inventory_items_rejects_capacity_overflow(reset_client_state):
    max_stack = ItemData.get_max_stack("spell_basic_breathing")
    result = reset_client_state.set_inventory_items({"spell_basic_breathing": max_stack * 51})
    assert result["success"] is False
    assert result["reason_code"] == "TEST_SET_INVENTORY_ITEMS_CAPACITY_EXCEEDED"


def test_unlock_content_and_set_equipped_spells_validation(reset_client_state):
    not_owned = reset_client_state.set_equipped_spells(breathing=["basic_breathing"])
    assert not_owned["success"] is False
    assert not_owned["reason_code"] == "TEST_SET_EQUIPPED_SPELLS_NOT_OWNED"

    unlock = reset_client_state.unlock_content(
        spell_ids=["basic_breathing", "basic_boxing_techniques", "thunder_strike", "basic_health", "basic_defense", "basic_steps"]
    )
    assert unlock["success"] is True

    duplicated = reset_client_state.set_equipped_spells(active=["basic_boxing_techniques", "basic_boxing_techniques"])
    assert duplicated["success"] is False
    assert duplicated["reason_code"] == "TEST_SET_EQUIPPED_SPELLS_DUPLICATED"

    type_mismatch = reset_client_state.set_equipped_spells(breathing=["basic_boxing_techniques"])
    assert type_mismatch["success"] is False
    assert type_mismatch["reason_code"] == "TEST_SET_EQUIPPED_SPELLS_TYPE_MISMATCH"

    slot_limit = reset_client_state.set_equipped_spells(opening=["basic_health", "basic_defense", "basic_steps"])
    assert slot_limit["success"] is False
    assert slot_limit["reason_code"] == "TEST_SET_EQUIPPED_SPELLS_SLOT_LIMIT_EXCEEDED"

    success = reset_client_state.set_equipped_spells(
        breathing=["basic_breathing"],
        active=["basic_boxing_techniques", "thunder_strike"],
        opening=["basic_health", "basic_steps"],
    )
    assert success["success"] is True
    equipped = success["state_summary"]["spell_system"]["equipped_spells"]
    assert equipped["breathing"] == ["basic_breathing"]


def test_progress_runtime_preset_and_state_summary(reset_client_state):
    bad_progress = reset_client_state.set_progress_state(tower_highest_floor=-1)
    assert bad_progress["success"] is False
    assert bad_progress["reason_code"] == "TEST_SET_PROGRESS_STATE_TOWER_FLOOR_INVALID"

    progress = reset_client_state.set_progress_state(
        tower_highest_floor=5,
        daily_dungeon_remaining_counts={"foundation_herb_cave": 1},
    )
    assert progress["success"] is True
    assert progress["state_summary"]["lianli_system"]["tower_highest_floor"] == 5

    bad_runtime = reset_client_state.set_runtime_state(current_area_id="not_exists_area")
    assert bad_runtime["success"] is False
    assert bad_runtime["reason_code"] == "TEST_SET_RUNTIME_STATE_AREA_NOT_FOUND"

    bad_herb_runtime = reset_client_state.set_runtime_state(current_herb_point_id="missing_point")
    assert bad_herb_runtime["success"] is False
    assert bad_herb_runtime["reason_code"] == "TEST_SET_RUNTIME_STATE_HERB_POINT_NOT_FOUND"

    runtime = reset_client_state.set_runtime_state(
        is_cultivating=True,
        is_gathering=True,
        current_herb_point_id="point_low_yield",
        herb_elapsed_seconds=8,
        is_in_lianli=True,
        is_battling=True,
        current_area_id="area_1",
    )
    assert runtime["success"] is True
    assert runtime["state_summary"]["herb_system"]["is_gathering"] is True
    assert runtime["state_summary"]["lianli_system"]["is_battling"] is True
    assert runtime["state_summary"]["lianli_system"]["current_area_id"] == "area_1"

    bad_preset = reset_client_state.apply_preset("missing_preset")
    assert bad_preset["success"] is False
    assert bad_preset["reason_code"] == "TEST_APPLY_PRESET_NOT_FOUND"

    preset = reset_client_state.apply_preset("full_unlock")
    assert preset["success"] is True
    assert preset["reason_code"] == "TEST_APPLY_PRESET_SUCCEEDED"

    grant = reset_client_state.grant_test_pack()
    assert grant["success"] is True
    assert grant["reason_code"] == "TEST_GRANT_TEST_PACK_SUCCEEDED"

    summary = reset_client_state.get_state_summary()
    assert summary["success"] is True
    assert summary["reason_code"] == "TEST_STATE_SUMMARY_SUCCEEDED"
