"""测试状态辅助工具。"""

from __future__ import annotations

import copy
import time
from typing import Any, Dict, Optional

from app.game.application.GameContext import GameContext
from app.game.application.InitPlayerInfo import get_initial_player_data
from app.game.domain import (
    AccountSystem,
    AlchemySystem,
    AreasData,
    HerbGatherSystem,
    HerbPointData,
    InventorySystem,
    ItemData,
    LianliSystem,
    PlayerSystem,
    RealmData,
    RecipeData,
    SpellData,
    SpellSystem,
)

from unit_test.presets.TestPresets import build_preset
from unit_test.support.TestSupportConfig import TEST_PACK_ITEM_ID, TEST_USERNAMES, TEST_USERNAME_PREFIX


def is_test_account(ctx: GameContext) -> bool:
    username = str(ctx.account.username)
    return username in TEST_USERNAMES or username.startswith(TEST_USERNAME_PREFIX)


def hydrate_context_from_data(ctx: GameContext, db_data: Dict[str, Any]) -> None:
    ctx.db_data = copy.deepcopy(db_data)
    ctx.spell_system = SpellSystem.from_dict(ctx.db_data.get("spell_system", {}))
    ctx.inventory_system = InventorySystem.from_dict(ctx.db_data.get("inventory", {}))
    ctx.alchemy_system = AlchemySystem.from_dict(ctx.db_data.get("alchemy_system", {}))
    ctx.lianli_system = LianliSystem.from_dict(ctx.db_data.get("lianli_system", {}))
    ctx.herb_system = HerbGatherSystem.from_dict(ctx.db_data.get("herb_system", {}))
    ctx.account_system = AccountSystem.from_dict(ctx.db_data.get("account_info", {}))

    player_data = ctx.db_data.get("player", {})
    ctx.player = PlayerSystem(
        health=float(player_data.get("health", 100.0)),
        spirit_energy=float(player_data.get("spirit_energy", 0.0)),
        realm=player_data.get("realm", RealmData.get_first_realm()),
        realm_level=int(player_data.get("realm_level", 1)),
        spell_system=ctx.spell_system
    )
    ctx.player.is_cultivating = bool(player_data.get("is_cultivating", False))
    ctx.player.last_cultivation_report_time = float(player_data.get("last_cultivation_report_time", 0.0))
    ctx.player.cultivation_effect_carry_seconds = float(player_data.get("cultivation_effect_carry_seconds", 0.0))


def build_state_summary(ctx: GameContext) -> Dict[str, Any]:
    owned_spells = sorted([
        spell_id for spell_id, spell_info in ctx.spell_system.player_spells.items()
        if spell_info.get("obtained", False)
    ])
    current_area_id = ""
    if isinstance(ctx.lianli_system.current_battle_data, dict):
        current_area_id = str(ctx.lianli_system.current_battle_data.get("area_id", ""))

    return {
        "account": {
            "username": ctx.account.username,
            "nickname": ctx.account_system.nickname,
        },
        "player": ctx.player.to_dict(),
        "inventory": ctx.inventory_system.to_dict(),
        "spell_system": {
            "owned_spells": owned_spells,
            "equipped_spells": copy.deepcopy(ctx.spell_system.equipped_spells),
        },
        "alchemy_system": ctx.alchemy_system.to_dict(),
        "herb_system": ctx.herb_system.to_dict(),
        "lianli_system": {
            "tower_highest_floor": ctx.lianli_system.tower_highest_floor,
            "daily_dungeon_data": copy.deepcopy(ctx.lianli_system.daily_dungeon_data),
            "is_battling": ctx.lianli_system.is_battling,
            "is_in_lianli": ctx.lianli_system.current_battle_data is not None,
            "current_area_id": current_area_id,
        }
    }


def reset_context_to_initial(ctx: GameContext, include_test_pack: bool = True) -> Dict[str, Any]:
    initial_data = get_initial_player_data(
        str(ctx.account.id),
        ctx.account.username,
        include_test_pack=include_test_pack
    )
    hydrate_context_from_data(ctx, initial_data)
    ctx.account_system.reset_suspicious_operations()
    return build_state_summary(ctx)


def set_player_state(
    ctx: GameContext,
    realm: Optional[str] = None,
    realm_level: Optional[int] = None,
    spirit_energy: Optional[float] = None,
    health: Optional[float] = None,
) -> Dict[str, Any]:
    if realm is not None:
        ctx.player.realm = realm

    if realm_level is not None:
        ctx.player.realm_level = realm_level

    ctx.player.reload_attributes()
    ctx.player.set_health(max(0.0, float(health)) if health is not None else ctx.player.health)
    current_spirit = float(spirit_energy) if spirit_energy is not None else float(ctx.player.spirit_energy)
    ctx.player.spirit_energy = round(max(0.0, min(current_spirit, ctx.player.static_max_spirit_energy)), 2)
    return build_state_summary(ctx)


def set_inventory_items_exact(ctx: GameContext, items: Dict[str, int]) -> Dict[str, Any]:
    inventory = InventorySystem()
    for item_id, count in items.items():
        count_int = int(count)
        if count_int <= 0:
            continue
        added = inventory.add_item(item_id, count_int)
        if added != count_int:
            raise ValueError(f"INVENTORY_CAPACITY_EXCEEDED:{item_id}")
    ctx.inventory_system = inventory
    return build_state_summary(ctx)


def unlock_content(
    ctx: GameContext,
    spell_ids: Optional[list[str]] = None,
    recipe_ids: Optional[list[str]] = None,
    furnace_ids: Optional[list[str]] = None,
) -> Dict[str, Any]:
    for spell_id in spell_ids or []:
        if not ctx.spell_system.has_spell(spell_id):
            ctx.spell_system.unlock_spell(spell_id)

    for recipe_id in recipe_ids or []:
        if not ctx.alchemy_system.has_recipe(recipe_id):
            ctx.alchemy_system.learn_recipe(recipe_id)

    for furnace_id in furnace_ids or []:
        ctx.alchemy_system.equip_furnace(furnace_id)

    ctx.player.reload_attributes()
    ctx.player.set_health(ctx.player.health)
    ctx.player.spirit_energy = round(min(ctx.player.spirit_energy, ctx.player.static_max_spirit_energy), 2)
    return build_state_summary(ctx)


def set_spell_states(ctx: GameContext, spell_states: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    for spell_id, state in spell_states.items():
        if spell_id not in ctx.spell_system.player_spells:
            continue
        current = ctx.spell_system.player_spells[spell_id]
        current["obtained"] = bool(state.get("obtained", True))
        current["level"] = max(1, int(state.get("level", current.get("level", 1))))
        current["use_count"] = max(0, int(state.get("use_count", current.get("use_count", 0))))
        current["charged_spirit"] = max(0, int(state.get("charged_spirit", current.get("charged_spirit", 0))))

    ctx.spell_system.recalculate_bonuses()
    ctx.player.reload_attributes()
    ctx.player.set_health(ctx.player.health)
    ctx.player.spirit_energy = round(min(ctx.player.spirit_energy, ctx.player.static_max_spirit_energy), 2)
    return build_state_summary(ctx)


def set_equipped_spells(
    ctx: GameContext,
    breathing: Optional[list[str]] = None,
    active: Optional[list[str]] = None,
    opening: Optional[list[str]] = None,
) -> Dict[str, Any]:
    breathing = breathing or []
    active = active or []
    opening = opening or []

    ctx.spell_system.equipped_spells = {
        SpellData.SPELL_TYPE_BREATHING: list(breathing),
        SpellData.SPELL_TYPE_ACTIVE: list(active),
        SpellData.SPELL_TYPE_OPENING: list(opening),
    }
    return build_state_summary(ctx)


def set_progress_state(
    ctx: GameContext,
    tower_highest_floor: Optional[int] = None,
    daily_dungeon_remaining_counts: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    if tower_highest_floor is not None:
        max_floor = AreasData.get_tower_max_floor()
        ctx.lianli_system.tower_highest_floor = max(0, min(int(tower_highest_floor), max_floor))

    for area_id, remaining in (daily_dungeon_remaining_counts or {}).items():
        area_info = AreasData.get_area_info(area_id)
        max_count = int(area_info.get("daily_count", 3))
        ctx.lianli_system.daily_dungeon_data[area_id] = {
            "max_count": max_count,
            "remaining_count": max(0, min(int(remaining), max_count))
        }

    return build_state_summary(ctx)


def set_runtime_state(
    ctx: GameContext,
    is_cultivating: Optional[bool] = None,
    is_alchemizing: Optional[bool] = None,
    is_gathering: Optional[bool] = None,
    is_in_lianli: Optional[bool] = None,
    is_battling: Optional[bool] = None,
    current_area_id: Optional[str] = None,
    current_herb_point_id: Optional[str] = None,
    herb_elapsed_seconds: Optional[float] = None,
) -> Dict[str, Any]:
    if is_cultivating is not None:
        ctx.player.is_cultivating = bool(is_cultivating)
        ctx.player.last_cultivation_report_time = time.time() if ctx.player.is_cultivating else 0.0
        if not ctx.player.is_cultivating:
            ctx.player.cultivation_effect_carry_seconds = 0.0

    if is_alchemizing is not None:
        ctx.alchemy_system.is_alchemizing = bool(is_alchemizing)
        ctx.alchemy_system.last_alchemy_report_time = time.time() if ctx.alchemy_system.is_alchemizing else 0.0

    if is_gathering is not None:
        ctx.herb_system.is_gathering = bool(is_gathering)
        if ctx.herb_system.is_gathering:
            point_id = current_herb_point_id
            if not point_id:
                points = HerbPointData.get_all_points()
                point_id = next(iter(points.keys()), "")
            ctx.herb_system.current_point_id = str(point_id)
            if herb_elapsed_seconds is not None:
                ctx.herb_system.last_report_time = time.time() - float(herb_elapsed_seconds)
            else:
                ctx.herb_system.last_report_time = time.time()
        else:
            ctx.herb_system.reset_gather_state()

    current_area = current_area_id
    if not current_area:
        if isinstance(ctx.lianli_system.current_battle_data, dict):
            current_area = str(ctx.lianli_system.current_battle_data.get("area_id", ""))
        if not current_area:
            normal_areas = AreasData.get_normal_area_ids()
            current_area = normal_areas[0] if normal_areas else AreasData.get_tower_area_id()

    effective_is_battling = bool(is_battling) if is_battling is not None else bool(ctx.lianli_system.is_battling)
    effective_is_in_lianli = bool(is_in_lianli) if is_in_lianli is not None else (ctx.lianli_system.current_battle_data is not None)

    if effective_is_battling:
        effective_is_in_lianli = True

    ctx.lianli_system.is_battling = effective_is_battling
    ctx.lianli_system.battle_start_time = time.time() if effective_is_battling else None

    if effective_is_in_lianli:
        ctx.lianli_system.current_battle_data = {
            "area_id": current_area,
            "enemy_data": {},
            "battle_timeline": [],
            "loot": [],
            "victory": False,
            "player_health_before": ctx.player.health,
            "player_health_after": ctx.player.health,
            "player_max_health_before": ctx.player.static_max_health,
        }
    else:
        ctx.lianli_system.current_battle_data = None

    return build_state_summary(ctx)


def apply_preset(ctx: GameContext, preset_name: str) -> Dict[str, Any]:
    preset = build_preset(preset_name)
    if not preset:
        raise ValueError("PRESET_NOT_FOUND")

    reset_context_to_initial(ctx, include_test_pack=True)

    player_state = preset.get("player_state", {})
    if player_state:
        set_player_state(
            ctx,
            realm=player_state.get("realm"),
            realm_level=player_state.get("realm_level"),
            spirit_energy=player_state.get("spirit_energy"),
            health=player_state.get("health"),
        )

    if "inventory_items" in preset:
        set_inventory_items_exact(ctx, preset.get("inventory_items", {}))

    unlock_content(
        ctx,
        spell_ids=preset.get("unlock_content", {}).get("spell_ids", []),
        recipe_ids=preset.get("unlock_content", {}).get("recipe_ids", []),
        furnace_ids=preset.get("unlock_content", {}).get("furnace_ids", []),
    )

    spell_states = preset.get("spell_states", {})
    if spell_states:
        set_spell_states(ctx, spell_states)

    if "equipped_spells" in preset:
        set_equipped_spells(
            ctx,
            breathing=preset.get("equipped_spells", {}).get("breathing", []),
            active=preset.get("equipped_spells", {}).get("active", []),
            opening=preset.get("equipped_spells", {}).get("opening", []),
        )

    if "progress_state" in preset:
        set_progress_state(
            ctx,
            tower_highest_floor=preset.get("progress_state", {}).get("tower_highest_floor"),
            daily_dungeon_remaining_counts=preset.get("progress_state", {}).get("daily_dungeon_remaining_counts", {}),
        )

    if "runtime_state" in preset:
        set_runtime_state(
            ctx,
            is_cultivating=preset.get("runtime_state", {}).get("is_cultivating"),
            is_alchemizing=preset.get("runtime_state", {}).get("is_alchemizing"),
            is_gathering=preset.get("runtime_state", {}).get("is_gathering"),
            is_in_lianli=preset.get("runtime_state", {}).get("is_in_lianli"),
            is_battling=preset.get("runtime_state", {}).get("is_battling"),
            current_area_id=preset.get("runtime_state", {}).get("current_area_id"),
            current_herb_point_id=preset.get("runtime_state", {}).get("current_herb_point_id"),
        )

    return build_state_summary(ctx)


def validate_realm_and_level(realm: Optional[str], realm_level: Optional[int]) -> Optional[str]:
    effective_realm = realm
    effective_level = realm_level

    if effective_realm is None and effective_level is None:
        return None

    if effective_realm is None or effective_realm not in RealmData.get_all_realms():
        return "TEST_SET_PLAYER_STATE_REALM_INVALID"

    if effective_level is None:
        return None

    max_level = RealmData.get_max_level(effective_realm)
    if effective_level < 1 or effective_level > max_level:
        return "TEST_SET_PLAYER_STATE_LEVEL_INVALID"
    return None


def validate_inventory_items(items: Dict[str, int]) -> Optional[str]:
    for item_id, count in items.items():
        if not ItemData.item_exists(item_id):
            return "TEST_SET_INVENTORY_ITEMS_ITEM_NOT_FOUND"
        if int(count) < 0:
            return "TEST_SET_INVENTORY_ITEMS_NEGATIVE_COUNT"
    return None


def validate_unlock_content(spell_ids: list[str], recipe_ids: list[str], furnace_ids: list[str]) -> Optional[str]:
    for spell_id in spell_ids:
        if not SpellData.spell_exists(spell_id):
            return "TEST_UNLOCK_CONTENT_SPELL_NOT_FOUND"
    for recipe_id in recipe_ids:
        if not RecipeData.recipe_exists(recipe_id):
            return "TEST_UNLOCK_CONTENT_RECIPE_NOT_FOUND"
    for furnace_id in furnace_ids:
        if furnace_id not in AlchemySystem.FURNACE_CONFIGS:
            return "TEST_UNLOCK_CONTENT_FURNACE_NOT_FOUND"
    return None


def validate_equipped_spells(ctx: GameContext, breathing: list[str], active: list[str], opening: list[str]) -> Optional[str]:
    groups = {
        SpellData.SPELL_TYPE_BREATHING: breathing,
        SpellData.SPELL_TYPE_ACTIVE: active,
        SpellData.SPELL_TYPE_OPENING: opening,
    }
    seen = set()

    for slot_type, spell_ids in groups.items():
        if len(spell_ids) > ctx.spell_system.slot_limits.get(slot_type, 0):
            return "TEST_SET_EQUIPPED_SPELLS_SLOT_LIMIT_EXCEEDED"

        for spell_id in spell_ids:
            if spell_id in seen:
                return "TEST_SET_EQUIPPED_SPELLS_DUPLICATED"
            seen.add(spell_id)

            if not SpellData.spell_exists(spell_id):
                return "TEST_SET_EQUIPPED_SPELLS_SPELL_NOT_FOUND"
            if not ctx.spell_system.has_spell(spell_id):
                return "TEST_SET_EQUIPPED_SPELLS_NOT_OWNED"
            if SpellData.get_spell_type(spell_id) != slot_type:
                return "TEST_SET_EQUIPPED_SPELLS_TYPE_MISMATCH"

    return None


def validate_progress_state(tower_highest_floor: Optional[int], daily_counts: Dict[str, int]) -> Optional[str]:
    if tower_highest_floor is not None and int(tower_highest_floor) < 0:
        return "TEST_SET_PROGRESS_STATE_TOWER_FLOOR_INVALID"

    for area_id, remaining in daily_counts.items():
        if not AreasData.is_daily_area(area_id):
            return "TEST_SET_PROGRESS_STATE_DUNGEON_NOT_FOUND"
        if int(remaining) < 0:
            return "TEST_SET_PROGRESS_STATE_REMAINING_COUNT_INVALID"
    return None


def validate_runtime_state(current_area_id: Optional[str], current_herb_point_id: Optional[str]) -> Optional[str]:
    if current_area_id and current_area_id not in AreasData.get_all_area_ids() and current_area_id != AreasData.get_tower_area_id():
        return "TEST_SET_RUNTIME_STATE_AREA_NOT_FOUND"
    if current_herb_point_id and not HerbPointData.point_exists(current_herb_point_id):
        return "TEST_SET_RUNTIME_STATE_HERB_POINT_NOT_FOUND"
    return None


def grant_test_pack(ctx: GameContext) -> Dict[str, Any]:
    added = ctx.inventory_system.add_item(TEST_PACK_ITEM_ID, 1)
    if added != 1:
        raise ValueError("TEST_GRANT_TEST_PACK_INVENTORY_FULL")
    return build_state_summary(ctx)
