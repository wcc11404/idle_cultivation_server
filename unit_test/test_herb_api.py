from unit_test.support.db_support import (
    set_herb_elapsed_seconds,
)


def test_herb_points_and_start_stop(reset_client_state):
    points = reset_client_state.herb_points()
    assert points["success"] is True
    assert points["reason_code"] == "HERB_POINTS_SUCCEEDED"
    assert "point_low_yield" in points.get("points_config", {})
    assert "point_high_yield" in points.get("points_config", {})

    start = reset_client_state.herb_start("point_low_yield")
    assert start["success"] is True
    assert start["reason_code"] == "HERB_START_SUCCEEDED"

    repeat = reset_client_state.herb_start("point_high_yield")
    assert repeat["success"] is False
    assert repeat["reason_code"] == "HERB_START_ALREADY_ACTIVE"

    stop = reset_client_state.herb_stop()
    assert stop["success"] is True
    assert stop["reason_code"] == "HERB_STOP_SUCCEEDED"

    stop_again = reset_client_state.herb_stop()
    assert stop_again["success"] is False
    assert stop_again["reason_code"] == "HERB_STOP_NOT_ACTIVE"


def test_herb_start_validation_and_mutual_block(reset_client_state):
    not_found = reset_client_state.herb_start("missing_point")
    assert not_found["success"] is False
    assert not_found["reason_code"] == "HERB_START_POINT_NOT_FOUND"

    reset_client_state.set_runtime_state(is_cultivating=True)
    blocked_by_cultivation = reset_client_state.herb_start("point_low_yield")
    assert blocked_by_cultivation["success"] is False
    assert blocked_by_cultivation["reason_code"] == "HERB_START_BLOCKED_BY_CULTIVATION"

    reset_client_state.reset_account()
    reset_client_state.set_runtime_state(is_alchemizing=True)
    blocked_by_alchemy = reset_client_state.herb_start("point_low_yield")
    assert blocked_by_alchemy["success"] is False
    assert blocked_by_alchemy["reason_code"] == "HERB_START_BLOCKED_BY_ALCHEMY"

    reset_client_state.reset_account()
    reset_client_state.set_runtime_state(is_battling=True, is_in_lianli=True, current_area_id="area_1")
    blocked_by_lianli = reset_client_state.herb_start("point_low_yield")
    assert blocked_by_lianli["success"] is False
    assert blocked_by_lianli["reason_code"] == "HERB_START_BLOCKED_BY_LIANLI"


def test_herb_report_success_and_invalid(reset_client_state):
    open_pack = reset_client_state.inventory_use("test_pack")
    assert open_pack["success"] is True
    unlock = reset_client_state.inventory_use("spell_herb_gathering")
    assert unlock["success"] is True

    start = reset_client_state.herb_start("point_low_yield")
    assert start["success"] is True

    invalid = reset_client_state.herb_report()
    assert invalid["success"] is False
    assert invalid["reason_code"] == "HERB_REPORT_TIME_INVALID"

    set_herb_elapsed_seconds(reset_client_state.account_id, 8.0, "point_low_yield")
    report = reset_client_state.herb_report()
    assert report["success"] is True
    assert report["reason_code"] == "HERB_REPORT_SUCCEEDED"
    assert report["point_id"] == "point_low_yield"
    assert isinstance(report.get("drops_gained", {}), dict)

    spell_list = reset_client_state.spell_list()
    assert spell_list["success"] is True
    herb_spell = spell_list["player_spells"].get("herb_gathering", {})
    assert int(herb_spell.get("use_count", 0)) >= 1

    points = reset_client_state.herb_points()
    assert points["success"] is True
    point_cfg = points.get("points_config", {}).get("point_low_yield", {})
    assert float(point_cfg.get("report_interval_seconds", 0.0)) <= float(point_cfg.get("base_report_interval_seconds", 0.0))


def test_herb_report_not_active(reset_client_state):
    result = reset_client_state.herb_report()
    assert result["success"] is False
    assert result["reason_code"] == "HERB_REPORT_NOT_ACTIVE"


def test_double_side_mutual_exclusion_with_herb(reset_client_state):
    start = reset_client_state.herb_start("point_high_yield")
    assert start["success"] is True

    cultivation = reset_client_state.cultivation_start()
    assert cultivation["success"] is False
    assert cultivation["reason_code"] == "CULTIVATION_START_BLOCKED_BY_HERB_GATHERING"

    alchemy = reset_client_state.alchemy_start()
    assert alchemy["success"] is False
    assert alchemy["reason_code"] == "ALCHEMY_START_BLOCKED_BY_HERB_GATHERING"

    lianli = reset_client_state.lianli_simulate("area_1")
    assert lianli["success"] is False
    assert lianli["reason_code"] == "LIANLI_SIMULATE_BLOCKED_BY_HERB_GATHERING"
