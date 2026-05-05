#!/usr/bin/env python3
"""复杂端到端集成测试脚本。"""

from __future__ import annotations

import json
import os

from unit_test.support.DbSupport import (
    set_alchemy_elapsed_seconds,
    set_battle_elapsed_seconds,
    set_cultivation_elapsed_seconds,
)
from unit_test.support.TestApiClient import TestApiClient
TARGET_REALM = "筑基期"
TARGET_LEVEL = 1


def _integration_test_username() -> str:
    override = os.getenv("IDLE_INTEGRATION_TEST_USERNAME", "").strip()
    if override:
        return override
    return f"test_{os.getpid()}_it"


def expect_success(result: dict, label: str, reason_code: str | None = None) -> dict:
    if not result.get("success", False):
        raise AssertionError(f"{label} 失败: {result}")
    if reason_code is not None and result.get("reason_code") != reason_code:
        raise AssertionError(f"{label} reason_code 异常: {result}")
    return result


def expect_failure(result: dict, label: str, reason_code: str | None = None) -> dict:
    if result.get("success", False):
        raise AssertionError(f"{label} 预期失败但成功: {result}")
    if reason_code is not None and result.get("reason_code") != reason_code:
        raise AssertionError(f"{label} 失败 reason_code 异常: {result}")
    return result


def print_step(title: str) -> None:
    print(f"\n=== {title} ===")


def get_player_info(client: TestApiClient) -> dict:
    data_result = expect_success(client.get_game_data(), "get_game_data", "GAME_LOAD_SUCCEEDED")
    return data_result.get("data", {}).get("player", {})


def open_test_pack(client: TestApiClient) -> None:
    print_step("打开测试礼包")
    result = expect_success(
        client.inventory_use("test_pack"),
        "inventory_use test_pack",
        "INVENTORY_USE_GIFT_SUCCEEDED",
    )
    contents = result.get("reason_data", {}).get("contents", {})
    print(f"礼包内容: {contents}")


def run_breakthrough_to_target(client: TestApiClient) -> None:
    print_step("连续突破到筑基一层")
    for step_index in range(10):
        player = get_player_info(client)
        realm = str(player.get("realm", ""))
        level = int(player.get("realm_level", 0))
        spirit = player.get("spirit_energy", 0)
        print(f"第{step_index + 1}次突破前: {realm}{level}层, 灵气={spirit}")

        if realm == TARGET_REALM and level == TARGET_LEVEL:
            print("已达到目标境界")
            return

        result = expect_success(
            client.breakthrough(),
            f"breakthrough 第{step_index + 1}次",
            "CULTIVATION_BREAKTHROUGH_SUCCEEDED",
        )
        reason_data = result.get("reason_data", {})
        new_realm = str(reason_data.get("new_realm", ""))
        new_level = int(reason_data.get("new_level", 0))
        print(f"第{step_index + 1}次突破后: {new_realm}{new_level}层")

        if new_realm == TARGET_REALM and new_level == TARGET_LEVEL:
            return

    final_player = get_player_info(client)
    raise AssertionError(f"突破后仍未达到目标境界: {final_player}")


def craft_health_pill(client: TestApiClient) -> None:
    print_step("炼制补血丹")
    expect_success(client.alchemy_start(), "alchemy_start", "ALCHEMY_START_SUCCEEDED")
    set_alchemy_elapsed_seconds(client.account_id, 10.0)
    report = expect_success(
        client.alchemy_report("health_pill", 1),
        "alchemy_report health_pill",
        "ALCHEMY_REPORT_SUCCEEDED",
    )
    total_count = int(report.get("success_count", 0)) + int(report.get("fail_count", 0))
    if total_count != 1:
        raise AssertionError(f"炼丹次数异常: {report}")
    print(
        "炼丹结果: "
        f"成功={report.get('success_count', 0)}, "
        f"失败={report.get('fail_count', 0)}, "
        f"products={report.get('products', {})}, "
        f"returned_materials={report.get('returned_materials', {})}"
    )
    expect_success(client.alchemy_stop(), "alchemy_stop", "ALCHEMY_STOP_SUCCEEDED")


def equip_spells(client: TestApiClient) -> None:
    print_step("装备法术")
    equip_plan = [
        ("basic_boxing_techniques", "SPELL_EQUIP_SUCCEEDED"),
        ("gold_split_finger", "SPELL_EQUIP_SUCCEEDED"),
        ("basic_health", "SPELL_EQUIP_SUCCEEDED"),
        ("basic_defense", "SPELL_EQUIP_SUCCEEDED"),
        ("basic_breathing", "SPELL_EQUIP_SUCCEEDED"),
    ]
    for spell_id, reason_code in equip_plan:
        expect_success(client.spell_equip(spell_id), f"spell_equip {spell_id}", reason_code)
        print(f"{spell_id} 装备成功")

    limit_result = expect_failure(
        client.spell_equip("basic_steps"),
        "spell_equip basic_steps",
        "SPELL_SLOT_LIMIT_REACHED",
    )
    print(f"基础步法装备失败，reason_code={limit_result.get('reason_code')}")


def run_lianli_flow(client: TestApiClient) -> None:
    print_step("测试历练系统")
    simulate_result = expect_success(
        client.lianli_simulate("foundation_herb_cave"),
        "lianli_simulate foundation_herb_cave",
        "LIANLI_SIMULATE_SUCCEEDED",
    )
    battle_timeline = simulate_result.get("battle_timeline", [])
    total_time = float(simulate_result.get("total_time", 0.0))
    print(f"战斗总时长: {total_time:.2f}s, 回合数: {len(battle_timeline)}")

    expect_failure(
        client.lianli_finish(1.0, 9999),
        "lianli_finish immediate",
        "LIANLI_FINISH_TIME_INVALID",
    )
    print("立即结算被正确拒绝")

    for index, action in enumerate(battle_timeline, start=1):
        info = action.get("info", {})
        print(
            f"回合{index}: time={action.get('time', 0):.2f}, "
            f"type={action.get('type', '')}, info={info}"
        )

    set_battle_elapsed_seconds(client.account_id, total_time + 1.0)
    finish_result = expect_success(
        client.lianli_finish(1.0, 9999),
        "lianli_finish settled",
        "LIANLI_FINISH_FULLY_SETTLED",
    )
    print(
        "战斗结算成功: "
        f"settled={finish_result.get('settled_index')}/{finish_result.get('total_index')}, "
        f"player_health_after={finish_result.get('player_health_after')}, "
        f"loot={finish_result.get('loot_gained', [])}"
    )


def main() -> int:
    client = TestApiClient()

    print_step("登录测试账号")
    login_result = expect_success(
        client.login_test_account(_integration_test_username()),
        "login_test_account",
        "ACCOUNT_LOGIN_SUCCEEDED",
    )
    player = login_result.get("data", {}).get("player", {})
    print(f"登录成功，当前境界: {player.get('realm')} {player.get('realm_level')}层, 灵气: {player.get('spirit_energy')}")

    print_step("重置测试账号")
    expect_success(client.reset_account(), "reset_account", "TEST_RESET_ACCOUNT_SUCCEEDED")

    print_step("测试使用不存在的 bug 丹")
    expect_failure(
        client.inventory_use("bug_pill"),
        "inventory_use bug_pill before pack",
        "INVENTORY_USE_ITEM_NOT_ENOUGH",
    )
    print("缺少 bug 丹时被正确拒绝")

    print_step("测试丢弃不存在的补血丹")
    expect_failure(
        client.inventory_discard("health_pill", 1),
        "inventory_discard health_pill before pack",
        "INVENTORY_DISCARD_ITEM_NOT_ENOUGH",
    )
    print("缺少补血丹时被正确拒绝")

    print_step("开始修炼并测试防作弊")
    expect_success(client.cultivation_start(), "cultivation_start", "CULTIVATION_START_SUCCEEDED")
    expect_failure(
        client.cultivation_report(5.0),
        "cultivation_report immediate",
        "CULTIVATION_REPORT_TIME_INVALID",
    )
    print("立即上报修炼被正确拒绝")

    open_test_pack(client)

    print_step("使用 bug 丹")
    bug_result = expect_success(
        client.inventory_use("bug_pill"),
        "inventory_use bug_pill",
        "INVENTORY_USE_CONSUMABLE_SUCCEEDED",
    )
    print(f"bug 丹效果: {bug_result.get('reason_data', {}).get('effect', {})}")

    print_step("修炼 5 秒后上报")
    set_cultivation_elapsed_seconds(client.account_id, 5.0)
    report_result = expect_success(
        client.cultivation_report(5.0),
        "cultivation_report valid",
        "CULTIVATION_REPORT_SUCCEEDED",
    )
    print(
        "修炼上报成功: "
        f"spirit_gained={report_result.get('spirit_gained')}, "
        f"health_gained={report_result.get('health_gained')}, "
        f"used_count_gained={report_result.get('used_count_gained')}"
    )

    run_breakthrough_to_target(client)

    print_step("丢弃一个聚气丹")
    expect_success(
        client.inventory_discard("spirit_pill", 1),
        "inventory_discard spirit_pill",
        "INVENTORY_DISCARD_SUCCEEDED",
    )

    print_step("解锁所有丹方")
    for recipe_item in [
        "recipe_health_pill",
        "recipe_spirit_pill",
        "recipe_foundation_pill",
        "recipe_golden_core_pill",
    ]:
        expect_success(
            client.inventory_use(recipe_item),
            f"inventory_use {recipe_item}",
            "INVENTORY_USE_UNLOCK_RECIPE_SUCCEEDED",
        )
        print(f"{recipe_item} 解锁成功")

    print_step("解锁炼丹炉")
    expect_success(
        client.inventory_use("alchemy_furnace"),
        "inventory_use alchemy_furnace",
        "INVENTORY_USE_UNLOCK_FURNACE_SUCCEEDED",
    )

    print_step("测试修炼与炼丹互斥")
    expect_failure(
        client.alchemy_start(),
        "alchemy_start while cultivating",
        "ALCHEMY_START_BLOCKED_BY_CULTIVATION",
    )
    print("修炼中开始炼丹被正确拒绝")

    print_step("停止修炼")
    expect_success(client.cultivation_stop(), "cultivation_stop", "CULTIVATION_STOP_SUCCEEDED")

    craft_health_pill(client)

    print_step("解锁所有法术")
    for spell_item in [
        "spell_basic_breathing",
        "spell_basic_boxing_techniques",
        "spell_gold_split_finger",
        "spell_basic_health",
        "spell_basic_defense",
        "spell_basic_steps",
        "spell_alchemy",
    ]:
        expect_success(
            client.inventory_use(spell_item),
            f"inventory_use {spell_item}",
            "INVENTORY_USE_UNLOCK_SPELL_SUCCEEDED",
        )
        print(f"{spell_item} 解锁成功")

    equip_spells(client)
    run_lianli_flow(client)

    print_step("测试排行榜")
    rank_result = expect_success(client.get_rank(), "get_rank", "GAME_RANK_SUCCEEDED")
    assert len(rank_result.get("ranks", [])) <= 30, f"排行榜返回条目不应超过30: {len(rank_result.get('ranks', []))}"
    print(f"排行榜条目数: {len(rank_result.get('ranks', []))}")

    print_step("打印最终游戏状态")
    final_data = expect_success(client.get_game_data(), "get_game_data final", "GAME_LOAD_SUCCEEDED")
    print(json.dumps(final_data.get("data", {}), ensure_ascii=False, indent=2))

    print("\n=== 所有复杂集成测试通过！===")
    return 0


def test_complex_integration_flow() -> None:
    assert main() == 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(exc)
        raise SystemExit(1)
