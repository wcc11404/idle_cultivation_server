"""测试预设定义。"""

from __future__ import annotations

from typing import Any, Dict

from app.game.domain import AreasData, RealmData, RecipeData, SpellData

from unit_test.support.TestSupportConfig import (
    PRESET_ALCHEMY_READY,
    PRESET_BREAKTHROUGH_READY,
    PRESET_FULL_UNLOCK,
    PRESET_LIANLI_READY,
    PRESET_SPELL_READY,
    PRESET_TOWER_READY,
)


def _get_breakthrough_ready_preset() -> Dict[str, Any]:
    realm = RealmData.get_first_realm()
    level = RealmData.get_max_level(realm)
    breakthrough_info = RealmData.get_breakthrough_info(realm, level)
    items = {}

    spirit_stone_cost = int(breakthrough_info.get("spirit_stone_cost", 0))
    if spirit_stone_cost > 0:
        items["spirit_stone"] = spirit_stone_cost

    for item_id, count in breakthrough_info.get("materials", {}).items():
        items[item_id] = int(count)

    return {
        "player_state": {
            "realm": realm,
            "realm_level": level,
            "spirit_energy": float(breakthrough_info.get("spirit_energy_cost", 0)),
        },
        "inventory_items": items,
    }


def _get_alchemy_ready_preset() -> Dict[str, Any]:
    return {
        "player_state": {
            "realm": "筑基期",
            "realm_level": 1,
            "health": 1000000.0,
            "spirit_energy": 5000.0,
        },
        "inventory_items": {
            "spirit_stone": 50000,
            "mat_herb": 9999,
            "foundation_herb": 99,
            "health_pill": 5,
            "spirit_pill": 5,
        },
        "unlock_content": {
            "spell_ids": ["alchemy"],
            "recipe_ids": ["health_pill", "spirit_pill", "foundation_pill", "golden_core_pill"],
            "furnace_ids": ["alchemy_furnace"],
        },
    }


def _get_spell_ready_preset() -> Dict[str, Any]:
    boxing_upgrade = SpellData.get_spell_level_data("basic_boxing_techniques", 1)
    health_upgrade = SpellData.get_spell_level_data("basic_health", 1)

    return {
        "player_state": {
            "realm": "筑基期",
            "realm_level": 3,
            "health": 1000000.0,
            "spirit_energy": 5000.0,
        },
        "unlock_content": {
            "spell_ids": [
                "basic_breathing",
                "basic_boxing_techniques",
                "basic_defense",
                "basic_health",
                "basic_steps",
                "gold_split_finger",
                "alchemy",
            ]
        },
        "equipped_spells": {
            "breathing": ["basic_breathing"],
            "active": ["basic_boxing_techniques", "gold_split_finger"],
            "opening": ["basic_health", "basic_steps"],
        },
        "spell_states": {
            "basic_boxing_techniques": {
                "level": 1,
                "use_count": int(boxing_upgrade.get("use_count_required", 0)),
                "charged_spirit": int(boxing_upgrade.get("spirit_cost", 0)),
            },
            "basic_health": {
                "level": 1,
                "use_count": int(health_upgrade.get("use_count_required", 0)),
                "charged_spirit": int(health_upgrade.get("spirit_cost", 0)),
            },
        },
    }


def _get_lianli_ready_preset() -> Dict[str, Any]:
    return {
        "player_state": {
            "realm": "筑基期",
            "realm_level": 5,
            "health": 1000000.0,
            "spirit_energy": 1000.0,
        },
        "unlock_content": {
            "spell_ids": [
                "basic_breathing",
                "basic_boxing_techniques",
                "basic_defense",
                "basic_health",
                "basic_steps",
            ]
        },
        "equipped_spells": {
            "breathing": ["basic_breathing"],
            "active": ["basic_boxing_techniques"],
            "opening": ["basic_health", "basic_defense"],
        },
    }


def _get_tower_ready_preset() -> Dict[str, Any]:
    preset = _get_lianli_ready_preset()
    preset["progress_state"] = {
        "tower_highest_floor": 9,
    }
    return preset


def _get_full_unlock_preset() -> Dict[str, Any]:
    realms = RealmData.get_all_realms()
    final_realm = realms[-1] if realms else "炼气期"
    final_level = RealmData.get_max_level(final_realm)

    all_spell_ids = SpellData.get_all_spells()
    all_recipe_ids = list(RecipeData.get_recipes_config().keys())
    all_daily_counts = {}
    for area_id in AreasData.get_daily_area_ids():
        area_info = AreasData.get_area_info(area_id)
        all_daily_counts[area_id] = int(area_info.get("daily_count", 3))

    return {
        "player_state": {
            "realm": final_realm,
            "realm_level": final_level,
            "health": 9999999.0,
            "spirit_energy": 9999999.0,
        },
        "inventory_items": {
            "spirit_stone": 100000000,
            "bug_pill": 5,
            "health_pill": 20,
            "spirit_pill": 20,
            "foundation_pill": 20,
            "golden_core_pill": 20,
            "nascent_soul_pill": 20,
            "spirit_separation_pill": 20,
            "void_refining_pill": 20,
            "body_integration_pill": 20,
            "mahayana_pill": 20,
            "tribulation_pill": 20,
            "mat_herb": 9999,
            "foundation_herb": 99,
        },
        "unlock_content": {
            "spell_ids": all_spell_ids,
            "recipe_ids": all_recipe_ids,
            "furnace_ids": ["alchemy_furnace"],
        },
        "equipped_spells": {
            "breathing": ["basic_breathing"] if "basic_breathing" in all_spell_ids else [],
            "active": [spell_id for spell_id in ["basic_boxing_techniques", "gold_split_finger"] if spell_id in all_spell_ids],
            "opening": [spell_id for spell_id in ["basic_health", "basic_defense"] if spell_id in all_spell_ids],
        },
        "progress_state": {
            "tower_highest_floor": 10,
            "daily_dungeon_remaining_counts": all_daily_counts,
        },
    }


_PRESET_BUILDERS = {
    PRESET_BREAKTHROUGH_READY: _get_breakthrough_ready_preset,
    PRESET_ALCHEMY_READY: _get_alchemy_ready_preset,
    PRESET_SPELL_READY: _get_spell_ready_preset,
    PRESET_LIANLI_READY: _get_lianli_ready_preset,
    PRESET_TOWER_READY: _get_tower_ready_preset,
    PRESET_FULL_UNLOCK: _get_full_unlock_preset,
}


def get_supported_presets() -> list[str]:
    return list(_PRESET_BUILDERS.keys())


def build_preset(name: str) -> Dict[str, Any]:
    builder = _PRESET_BUILDERS.get(name)
    if not builder:
        return {}
    return builder()
