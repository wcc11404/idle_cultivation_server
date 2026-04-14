from app.modules.lianli.AreasData import AreasData
from app.modules.cultivation.RealmData import RealmData
from app.modules.inventory.InventorySystem import InventorySystem
from app.modules.player.PlayerSystem import PlayerSystem
from unit_test.support.db_support import set_alchemy_elapsed_seconds, set_offline_seconds


def test_test_api_validation_edges(reset_client_state):
    invalid_realm = reset_client_state.set_player_state(realm="不存在境界")
    assert invalid_realm["success"] is False
    assert invalid_realm["reason_code"] == "TEST_SET_PLAYER_STATE_REALM_INVALID"

    negative_count = reset_client_state.set_inventory_items({"health_pill": -1})
    assert negative_count["success"] is False
    assert negative_count["reason_code"] == "TEST_SET_INVENTORY_ITEMS_NEGATIVE_COUNT"

    invalid_item = reset_client_state.set_inventory_items({"not_exists_item": 1})
    assert invalid_item["success"] is False
    assert invalid_item["reason_code"] == "TEST_SET_INVENTORY_ITEMS_ITEM_NOT_FOUND"

    invalid_unlock_spell = reset_client_state.unlock_content(spell_ids=["not_exists_spell"])
    assert invalid_unlock_spell["success"] is False
    assert invalid_unlock_spell["reason_code"] == "TEST_UNLOCK_CONTENT_SPELL_NOT_FOUND"

    invalid_unlock_recipe = reset_client_state.unlock_content(recipe_ids=["not_exists_recipe"])
    assert invalid_unlock_recipe["success"] is False
    assert invalid_unlock_recipe["reason_code"] == "TEST_UNLOCK_CONTENT_RECIPE_NOT_FOUND"

    invalid_unlock_furnace = reset_client_state.unlock_content(furnace_ids=["not_exists_furnace"])
    assert invalid_unlock_furnace["success"] is False
    assert invalid_unlock_furnace["reason_code"] == "TEST_UNLOCK_CONTENT_FURNACE_NOT_FOUND"

    invalid_progress_dungeon = reset_client_state.set_progress_state(
        daily_dungeon_remaining_counts={"not_exists_dungeon": 1}
    )
    assert invalid_progress_dungeon["success"] is False
    assert invalid_progress_dungeon["reason_code"] == "TEST_SET_PROGRESS_STATE_DUNGEON_NOT_FOUND"


def test_cultivation_repeat_and_breakthrough_not_ready(reset_client_state):
    start = reset_client_state.cultivation_start()
    assert start["success"] is True

    start_again = reset_client_state.cultivation_start()
    assert start_again["success"] is False
    assert start_again["reason_code"] == "CULTIVATION_START_ALREADY_ACTIVE"

    reset_client_state.reset_account()
    final_realm = RealmData.get_all_realms()[-1]
    reset_client_state.set_player_state(realm=final_realm, realm_level=RealmData.get_max_level(final_realm))
    breakthrough = reset_client_state.breakthrough()
    assert breakthrough["success"] is False
    assert breakthrough["reason_code"] == "CULTIVATION_BREAKTHROUGH_NOT_AVAILABLE"


def test_inventory_duplicate_unlock_edges(reset_client_state):
    set_items = reset_client_state.set_inventory_items({
        "spell_basic_health": 2,
        "recipe_health_pill": 2,
        "alchemy_furnace": 2,
    })
    assert set_items["success"] is True

    first_spell = reset_client_state.inventory_use("spell_basic_health")
    assert first_spell["success"] is True
    second_spell = reset_client_state.inventory_use("spell_basic_health")
    assert second_spell["success"] is False
    assert second_spell["reason_code"] == "INVENTORY_USE_ALREADY_USED"

    first_recipe = reset_client_state.inventory_use("recipe_health_pill")
    assert first_recipe["success"] is True
    second_recipe = reset_client_state.inventory_use("recipe_health_pill")
    assert second_recipe["success"] is False
    assert second_recipe["reason_code"] == "INVENTORY_USE_ALREADY_USED"

    first_furnace = reset_client_state.inventory_use("alchemy_furnace")
    assert first_furnace["success"] is True
    second_furnace = reset_client_state.inventory_use("alchemy_furnace")
    assert second_furnace["success"] is False
    assert second_furnace["reason_code"] == "INVENTORY_USE_ALREADY_USED"


def test_inventory_internal_dependency_errors_use_generic_code():
    player = PlayerSystem(health=100.0, spirit_energy=100.0, realm="炼气期", realm_level=1)

    spell_inventory = InventorySystem()
    spell_inventory.add_item("spell_basic_health", 1)
    spell_result = spell_inventory.use_item("spell_basic_health", player, spell_system=None)
    assert spell_result["success"] is False
    assert spell_result["reason_code"] == "INVENTORY_USE_SYSTEM_ERROR"

    recipe_inventory = InventorySystem()
    recipe_inventory.add_item("recipe_health_pill", 1)
    recipe_result = recipe_inventory.use_item("recipe_health_pill", player, alchemy_system=None)
    assert recipe_result["success"] is False
    assert recipe_result["reason_code"] == "INVENTORY_USE_SYSTEM_ERROR"

    furnace_inventory = InventorySystem()
    furnace_inventory.add_item("alchemy_furnace", 1)
    furnace_result = furnace_inventory.use_item("alchemy_furnace", player, alchemy_system=None)
    assert furnace_result["success"] is False
    assert furnace_result["reason_code"] == "INVENTORY_USE_SYSTEM_ERROR"


def test_spell_error_edges(reset_client_state):
    not_found = reset_client_state.spell_equip("not_exists_spell")
    assert not_found["success"] is False
    assert not_found["reason_code"] == "SPELL_EQUIP_NOT_FOUND"

    not_owned = reset_client_state.spell_equip("basic_health")
    assert not_owned["success"] is False
    assert not_owned["reason_code"] == "SPELL_EQUIP_NOT_OWNED"

    reset_client_state.inventory_use("test_pack")
    reset_client_state.inventory_use("spell_alchemy")
    production = reset_client_state.spell_equip("alchemy")
    assert production["success"] is False
    assert production["reason_code"] == "SPELL_EQUIP_PRODUCTION_FORBIDDEN"

    reset_client_state.inventory_use("spell_basic_health")
    equip = reset_client_state.spell_equip("basic_health")
    assert equip["success"] is True
    already_equipped = reset_client_state.spell_equip("basic_health")
    assert already_equipped["success"] is False
    assert already_equipped["reason_code"] == "SPELL_EQUIP_ALREADY_EQUIPPED"

    reset_client_state.inventory_use("spell_basic_steps")
    equip_steps = reset_client_state.spell_equip("basic_steps")
    assert equip_steps["success"] is True

    reset_client_state.inventory_use("spell_basic_defense")
    slot_limit = reset_client_state.spell_equip("basic_defense")
    assert slot_limit["success"] is False
    assert slot_limit["reason_code"] == "SPELL_SLOT_LIMIT_REACHED"

    not_equipped = reset_client_state.spell_unequip("basic_steps")
    assert not_equipped["success"] is True
    assert not_equipped["reason_code"] == "SPELL_UNEQUIP_SUCCEEDED"

    not_equipped_again = reset_client_state.spell_unequip("basic_steps")
    assert not_equipped_again["success"] is False
    assert not_equipped_again["reason_code"] == "SPELL_UNEQUIP_NOT_EQUIPPED"

    upgrade_not_owned = reset_client_state.spell_upgrade("thunder_strike")
    assert upgrade_not_owned["success"] is False
    assert upgrade_not_owned["reason_code"] == "SPELL_UPGRADE_NOT_OWNED"

    reset_client_state.inventory_use("spell_basic_boxing_techniques")
    upgrade_use_count = reset_client_state.spell_upgrade("basic_boxing_techniques")
    assert upgrade_use_count["success"] is False
    assert upgrade_use_count["reason_code"] == "SPELL_UPGRADE_USE_COUNT_INSUFFICIENT"

    charge_not_owned = reset_client_state.spell_charge("thunder_strike", 10)
    assert charge_not_owned["success"] is False
    assert charge_not_owned["reason_code"] == "SPELL_CHARGE_NOT_OWNED"

    reset_client_state.set_player_state(spirit_energy=0)
    charge_no_spirit = reset_client_state.spell_charge("basic_boxing_techniques", 10)
    assert charge_no_spirit["success"] is False
    assert charge_no_spirit["reason_code"] == "SPELL_CHARGE_PLAYER_SPIRIT_INSUFFICIENT"

    reset_client_state.apply_preset("spell_ready")
    first_charge = reset_client_state.spell_charge("thunder_strike", 9999)
    assert first_charge["success"] is True
    already_full = reset_client_state.spell_charge("thunder_strike", 1)
    assert already_full["success"] is False
    assert already_full["reason_code"] == "SPELL_CHARGE_ALREADY_FULL"


def test_alchemy_error_edges(reset_client_state):
    stop_not_active = reset_client_state.alchemy_stop()
    assert stop_not_active["success"] is False
    assert stop_not_active["reason_code"] == "ALCHEMY_STOP_NOT_ACTIVE"

    reset_client_state.set_runtime_state(is_cultivating=True)
    cultivation_block = reset_client_state.alchemy_start()
    assert cultivation_block["success"] is False
    assert cultivation_block["reason_code"] == "ALCHEMY_START_BLOCKED_BY_CULTIVATION"

    reset_client_state.reset_account()
    reset_client_state.set_runtime_state(is_in_lianli=True, is_battling=True, current_area_id="qi_refining_outer")
    battle_block = reset_client_state.alchemy_start()
    assert battle_block["success"] is False
    assert battle_block["reason_code"] == "ALCHEMY_START_BLOCKED_BY_BATTLE"

    reset_client_state.apply_preset("alchemy_ready")
    start = reset_client_state.alchemy_start()
    assert start["success"] is True
    start_again = reset_client_state.alchemy_start()
    assert start_again["success"] is False
    assert start_again["reason_code"] == "ALCHEMY_START_ALREADY_ACTIVE"

    reset_client_state.reset_account()
    reset_client_state.unlock_content(spell_ids=["alchemy"], furnace_ids=["alchemy_furnace"])
    reset_client_state.set_player_state(realm="筑基期", realm_level=1, health=1000.0, spirit_energy=1000.0)
    reset_client_state.set_inventory_items({"mat_herb": 999, "foundation_herb": 99, "spirit_stone": 50000})
    start_without_recipe = reset_client_state.alchemy_start()
    assert start_without_recipe["success"] is True
    set_alchemy_elapsed_seconds(reset_client_state.account_id, 10.0)
    recipe_not_learned = reset_client_state.alchemy_report("health_pill", 1)
    assert recipe_not_learned["success"] is False
    assert recipe_not_learned["reason_code"] == "ALCHEMY_REPORT_RECIPE_NOT_LEARNED"

    reset_client_state.apply_preset("alchemy_ready")
    reset_client_state.set_inventory_items({"spirit_stone": 50000})
    reset_client_state.alchemy_start()
    set_alchemy_elapsed_seconds(reset_client_state.account_id, 10.0)
    materials_insufficient = reset_client_state.alchemy_report("health_pill", 1)
    assert materials_insufficient["success"] is False
    assert materials_insufficient["reason_code"] == "ALCHEMY_REPORT_MATERIALS_INSUFFICIENT"

    reset_client_state.apply_preset("alchemy_ready")
    reset_client_state.set_player_state(spirit_energy=0)
    reset_client_state.alchemy_start()
    set_alchemy_elapsed_seconds(reset_client_state.account_id, 10.0)
    spirit_insufficient = reset_client_state.alchemy_report("health_pill", 1)
    assert spirit_insufficient["success"] is False
    assert spirit_insufficient["reason_code"] == "ALCHEMY_REPORT_SPIRIT_INSUFFICIENT"

    reset_client_state.apply_preset("alchemy_ready")
    reset_client_state.alchemy_start()
    too_fast = reset_client_state.alchemy_report("health_pill", 1)
    assert too_fast["success"] is False
    assert too_fast["reason_code"] == "ALCHEMY_REPORT_TIME_INVALID"
    assert int(too_fast["reason_data"]["invalid_report_count"]) == 1

    for _ in range(9):
        too_fast = reset_client_state.alchemy_report("health_pill", 1)
    assert too_fast["success"] is False
    assert too_fast["reason_code"] == "ALCHEMY_REPORT_TIME_INVALID"
    assert int(too_fast["reason_data"]["invalid_report_count"]) == 10
    assert bool(too_fast["reason_data"]["kicked_out"]) is True
    assert reset_client_state.alchemy_stop().get("detail") == "KICKED_OUT"


def test_lianli_error_edges(reset_client_state):
    finish_not_active = reset_client_state.lianli_finish(1.0, 0)
    assert finish_not_active["success"] is False
    assert finish_not_active["reason_code"] == "LIANLI_FINISH_NOT_ACTIVE"

    reset_client_state.apply_preset("lianli_ready")
    simulate = reset_client_state.lianli_simulate("qi_refining_outer")
    assert simulate["success"] is True
    finish_too_fast = reset_client_state.lianli_finish(1.0, 9999)
    assert finish_too_fast["success"] is False
    assert finish_too_fast["reason_code"] == "LIANLI_FINISH_TIME_INVALID"
    assert int(finish_too_fast["reason_data"]["invalid_report_count"]) == 1

    for _ in range(9):
        finish_too_fast = reset_client_state.lianli_finish(1.0, 9999)
    assert finish_too_fast["success"] is False
    assert finish_too_fast["reason_code"] == "LIANLI_FINISH_TIME_INVALID"
    assert int(finish_too_fast["reason_data"]["invalid_report_count"]) == 10
    assert bool(finish_too_fast["reason_data"]["kicked_out"]) is True
    assert reset_client_state.get_game_data().get("detail") == "KICKED_OUT"
    relogin = reset_client_state.login_test_account()
    assert relogin["success"] is True
    reset_client_state.reset_account()

    reset_client_state.set_player_state(health=0)
    health_insufficient = reset_client_state.lianli_simulate("qi_refining_outer")
    assert health_insufficient["success"] is False
    assert health_insufficient["reason_code"] == "LIANLI_SIMULATE_HEALTH_INSUFFICIENT"

    reset_client_state.reset_account()
    reset_client_state.set_progress_state(daily_dungeon_remaining_counts={"foundation_herb_cave": 0})
    daily_limit = reset_client_state.lianli_simulate("foundation_herb_cave")
    assert daily_limit["success"] is False
    assert daily_limit["reason_code"] == "LIANLI_SIMULATE_DAILY_LIMIT_REACHED"

    reset_client_state.reset_account()
    reset_client_state.set_progress_state(tower_highest_floor=AreasData.get_tower_max_floor())
    tower_cleared = reset_client_state.lianli_simulate(AreasData.get_tower_area_id())
    assert tower_cleared["success"] is False
    assert tower_cleared["reason_code"] == "LIANLI_SIMULATE_TOWER_CLEARED"


def test_auth_and_offline_edge_cases(reset_client_state):
    nickname_with_space = reset_client_state.change_nickname("道友 甲")
    assert nickname_with_space["success"] is False
    assert nickname_with_space["reason_code"] == "ACCOUNT_NICKNAME_CONTAINS_SPACE"

    nickname_with_invisible = reset_client_state.change_nickname("道友\u200b甲")
    assert nickname_with_invisible["success"] is False
    assert nickname_with_invisible["reason_code"] == "ACCOUNT_NICKNAME_INVALID_CHARACTER"

    set_offline_seconds(reset_client_state.account_id, 30)
    short_offline = reset_client_state.claim_offline_reward()
    assert short_offline["success"] is True
    assert short_offline["reason_code"] == "GAME_OFFLINE_REWARD_SKIPPED_SHORT_OFFLINE"
    assert short_offline["offline_reward"] is None

    set_offline_seconds(reset_client_state.account_id, -30)
    invalid_offline = reset_client_state.claim_offline_reward()
    assert invalid_offline["success"] is False
    assert invalid_offline["reason_code"] == "GAME_OFFLINE_REWARD_INVALID_TIME"
