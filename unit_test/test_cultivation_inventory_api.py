from unit_test.support.db_support import set_cultivation_elapsed_seconds
from unit_test.support.smoke_flows import get_breakthrough_preset_items


def test_cultivation_success_and_caps(reset_client_state):
    baseline = reset_client_state.set_player_state(health=999999.0, spirit_energy=999999.0)
    assert baseline["success"] is True
    baseline_player = baseline["state_summary"]["player"]

    start = reset_client_state.cultivation_start()
    assert start["success"] is True
    assert start["reason_code"] == "CULTIVATION_START_SUCCEEDED"

    set_cultivation_elapsed_seconds(reset_client_state.account_id, 3.0)
    report = reset_client_state.cultivation_report(3)
    assert report["success"] is True
    assert report["reason_code"] == "CULTIVATION_REPORT_SUCCEEDED"

    state = reset_client_state.get_state_summary()["state_summary"]["player"]
    assert state["health"] == baseline_player["health"]
    assert state["spirit_energy"] == baseline_player["spirit_energy"]

    stop = reset_client_state.cultivation_stop()
    assert stop["success"] is True
    assert stop["reason_code"] == "CULTIVATION_STOP_SUCCEEDED"


def test_cultivation_blockers_and_anticheat(reset_client_state):
    blocked_by_battle = reset_client_state.set_runtime_state(
        is_in_lianli=True,
        is_battling=True,
        current_area_id="qi_refining_outer",
    )
    assert blocked_by_battle["success"] is True
    start = reset_client_state.cultivation_start()
    assert start["success"] is False
    assert start["reason_code"] == "CULTIVATION_START_BLOCKED_BY_BATTLE"

    reset_client_state.reset_account()
    reset_client_state.set_runtime_state(is_alchemizing=True)
    alchemy_block = reset_client_state.cultivation_start()
    assert alchemy_block["success"] is False
    assert alchemy_block["reason_code"] == "CULTIVATION_START_BLOCKED_BY_ALCHEMY"

    reset_client_state.reset_account()
    report_not_active = reset_client_state.cultivation_report(1)
    assert report_not_active["success"] is False
    assert report_not_active["reason_code"] == "CULTIVATION_REPORT_NOT_ACTIVE"

    stop_not_active = reset_client_state.cultivation_stop()
    assert stop_not_active["success"] is False
    assert stop_not_active["reason_code"] == "CULTIVATION_STOP_NOT_ACTIVE"

    reset_client_state.cultivation_start()
    invalid_report = reset_client_state.cultivation_report(5)
    assert invalid_report["success"] is False
    assert invalid_report["reason_code"] == "CULTIVATION_REPORT_TIME_INVALID"
    assert int(invalid_report["reason_data"]["invalid_report_count"]) == 1

    for _ in range(9):
        invalid_report = reset_client_state.cultivation_report(5)
    assert invalid_report["success"] is False
    assert invalid_report["reason_code"] == "CULTIVATION_REPORT_TIME_INVALID"
    assert int(invalid_report["reason_data"]["invalid_report_count"]) == 10
    assert bool(invalid_report["reason_data"]["kicked_out"]) is True

    kicked = reset_client_state.cultivation_stop()
    assert kicked.get("detail") == "KICKED_OUT"


def test_breakthrough_success_and_missing_resources(reset_client_state):
    preset_items = get_breakthrough_preset_items()

    ready = reset_client_state.apply_preset("breakthrough_ready")
    assert ready["success"] is True

    missing = reset_client_state.set_inventory_items({})
    assert missing["success"] is True
    failure = reset_client_state.breakthrough()
    assert failure["success"] is False
    assert failure["reason_code"] == "CULTIVATION_BREAKTHROUGH_INSUFFICIENT_RESOURCES"
    assert failure["reason_data"]["missing_resources"]

    reset_client_state.apply_preset("breakthrough_ready")
    reset_client_state.set_inventory_items(preset_items)
    success = reset_client_state.breakthrough()
    assert success["success"] is True
    assert success["reason_code"] == "CULTIVATION_BREAKTHROUGH_SUCCEEDED"
    assert success["reason_data"]["consumed_resources"]
    assert success["reason_data"]["new_realm"]
    assert int(success["reason_data"]["new_level"]) >= 1


def test_inventory_use_paths(reset_client_state):
    missing = reset_client_state.inventory_use("not_exists_item")
    assert missing["success"] is False
    assert missing["reason_code"] == "INVENTORY_USE_ITEM_NOT_FOUND"

    gift = reset_client_state.inventory_use("test_pack")
    assert gift["success"] is True
    assert gift["reason_code"] == "INVENTORY_USE_GIFT_SUCCEEDED"
    assert gift["reason_data"]["contents"]

    health = reset_client_state.inventory_use("health_pill")
    assert health["success"] is True
    assert health["reason_code"] == "INVENTORY_USE_CONSUMABLE_SUCCEEDED"
    assert health["reason_data"]["effect"]["type"] == "add_health"

    unlock_spell = reset_client_state.inventory_use("spell_basic_health")
    assert unlock_spell["success"] is True
    assert unlock_spell["reason_code"] == "INVENTORY_USE_UNLOCK_SPELL_SUCCEEDED"
    assert unlock_spell["reason_data"]["effect"]["type"] == "unlock_spell"

    unlock_recipe = reset_client_state.inventory_use("recipe_health_pill")
    assert unlock_recipe["success"] is True
    assert unlock_recipe["reason_code"] == "INVENTORY_USE_UNLOCK_RECIPE_SUCCEEDED"
    assert unlock_recipe["reason_data"]["effect"]["type"] == "unlock_recipe"

    unlock_furnace = reset_client_state.inventory_use("alchemy_furnace")
    assert unlock_furnace["success"] is True
    assert unlock_furnace["reason_code"] == "INVENTORY_USE_UNLOCK_FURNACE_SUCCEEDED"
    assert unlock_furnace["reason_data"]["effect"]["type"] == "unlock_furnace"


def test_inventory_misc_endpoints(reset_client_state):
    reset_client_state.set_inventory_items({"spirit_stone": 1})
    not_usable = reset_client_state.inventory_use("spirit_stone")
    assert not_usable["success"] is False
    assert not_usable["reason_code"] == "INVENTORY_USE_ITEM_NOT_USABLE"

    organize = reset_client_state.inventory_organize()
    assert organize["success"] is True
    assert organize["reason_code"] == "INVENTORY_ORGANIZE_SUCCEEDED"

    discard_fail = reset_client_state.inventory_discard("health_pill", 1)
    assert discard_fail["success"] is False
    assert discard_fail["reason_code"] == "INVENTORY_DISCARD_ITEM_NOT_ENOUGH"

    reset_client_state.reset_account()
    reset_client_state.inventory_use("test_pack")
    discard_success = reset_client_state.inventory_discard("bug_pill", 1)
    assert discard_success["success"] is True
    assert discard_success["reason_code"] == "INVENTORY_DISCARD_SUCCEEDED"

    inventory_list = reset_client_state.inventory_list()
    assert inventory_list["success"] is True
    assert inventory_list["reason_code"] == "INVENTORY_LIST_SUCCEEDED"
    assert "inventory" in inventory_list

    last_result = {}
    for _ in range(16):
        last_result = reset_client_state.inventory_expand()
    assert last_result["success"] is False
    assert last_result["reason_code"] == "INVENTORY_EXPAND_CAPACITY_MAX"
