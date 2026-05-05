"""
术法系统

负责管理玩家的术法数据，包括装备、升级、充灵气、升星和战斗内术法效果。
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
import random

from app.game.domain.player.AttributeCalculator import AttributeCalculator
from .SpellData import SpellData

if TYPE_CHECKING:
    from ..player.PlayerSystem import PlayerSystem
    from ..inventory.InventorySystem import InventorySystem


class SpellSystem:
    """术法系统"""

    MAX_TOTAL_TRIGGER_CHANCE = 0.80

    MULTIPLICATIVE_ATTRS = {"health", "attack", "defense", "max_spirit", "spirit_gain", "penetration", "crit_damage"}
    ADDITIVE_ATTRS = {"speed", "hit", "dodge", "crit", "anti_crit"}

    def __init__(self):
        self.player_spells: Dict[str, Dict[str, Any]] = {}
        self.equipped_spells: Dict[str, List[str]] = {
            SpellData.SPELL_TYPE_BREATHING: [],
            SpellData.SPELL_TYPE_ACTIVE: [],
            SpellData.SPELL_TYPE_OPENING: []
        }
        self.slot_limits: Dict[str, int] = {
            SpellData.SPELL_TYPE_BREATHING: 1,
            SpellData.SPELL_TYPE_ACTIVE: 2,
            SpellData.SPELL_TYPE_OPENING: 2
        }
        self._cached_bonuses: Dict[str, float] = {
            "health": 1.0,
            "attack": 1.0,
            "defense": 1.0,
            "speed": 0.0,
            "max_spirit": 1.0,
            "spirit_gain": 1.0,
            "hit": 0.0,
            "dodge": 0.0,
            "crit": 0.0,
            "anti_crit": 0.0,
            "penetration": 1.0,
            "crit_damage": 1.0,
        }

    @staticmethod
    def _build_result(success: bool, reason_code: str, reason_data: Dict[str, Any] = None, **extra: Any) -> Dict[str, Any]:
        result = {
            "success": success,
            "reason_code": reason_code,
            "reason_data": reason_data or {}
        }
        result.update(extra)
        return result

    def _ensure_spell_state(self, spell_id: str) -> Dict[str, Any]:
        state = self.player_spells.setdefault(spell_id, {
            "obtained": False,
            "level": 0,
            "star": 0,
            "use_count": 0,
            "charged_spirit": 0,
        })
        state.setdefault("star", 0)
        state.setdefault("use_count", 0)
        state.setdefault("charged_spirit", 0)
        state.setdefault("level", 0)
        state.setdefault("obtained", False)
        return state

    def _apply_bonus_map(self, bonuses: Dict[str, float], bonus_map: Dict[str, Any]):
        for attr, raw_value in bonus_map.items():
            value = float(raw_value)
            if attr in self.MULTIPLICATIVE_ATTRS:
                bonuses[attr] = float(bonuses.get(attr, 1.0)) * value
            else:
                bonuses[attr] = float(bonuses.get(attr, 0.0)) + value

    def _apply_total_star_bonus_map(self, bonuses: Dict[str, float], bonus_map: Dict[str, Any]):
        for attr, raw_value in bonus_map.items():
            value = float(raw_value)
            if attr in self.MULTIPLICATIVE_ATTRS:
                bonuses[attr] = float(bonuses.get(attr, 1.0)) + value
            else:
                bonuses[attr] = float(bonuses.get(attr, 0.0)) + value

    def _get_current_level_data(self, spell_id: str, spell_info: Dict[str, Any]) -> Dict[str, Any]:
        return SpellData.get_spell_level_data(spell_id, int(spell_info.get("level", 0)))

    def _get_current_effects(self, spell_id: str, spell_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        return SpellData.get_spell_effects(spell_id, int(spell_info.get("level", 0)))

    def recalculate_bonuses(self):
        bonuses = {
            "health": 1.0,
            "attack": 1.0,
            "defense": 1.0,
            "speed": 0.0,
            "max_spirit": 1.0,
            "spirit_gain": 1.0,
            "hit": 0.0,
            "dodge": 0.0,
            "crit": 0.0,
            "anti_crit": 0.0,
            "penetration": 1.0,
            "crit_damage": 1.0,
        }

        for spell_id, spell_info in self.player_spells.items():
            if not spell_info.get("obtained", False) or int(spell_info.get("level", 0)) <= 0:
                continue

            level_data = self._get_current_level_data(spell_id, spell_info)
            combined_bonus = dict(level_data.get("attribute_bonus", {}))

            current_star = int(spell_info.get("star", 0))
            if current_star >= 0:
                var_star_key = min(current_star, 5)
                star_data = SpellData.get_spell_star_data(spell_id, var_star_key)
                self._apply_total_star_bonus_map(combined_bonus, star_data.get("attribute_bonus", {}))

            self._apply_bonus_map(bonuses, combined_bonus)
        self._cached_bonuses = bonuses

    def get_attribute_bonuses(self) -> Dict[str, float]:
        return self._cached_bonuses

    def unlock_spell(self, spell_id: str) -> Dict[str, Any]:
        if not SpellData.spell_exists(spell_id):
            return {"success": False, "reason": "术法不存在"}
        spell_info = self._ensure_spell_state(spell_id)
        if spell_info.get("obtained", False):
            return {"success": False, "reason": "已获取该术法"}
        spell_info.update({"obtained": True, "level": 1, "star": 0, "use_count": 0, "charged_spirit": 0})
        self.recalculate_bonuses()
        return {"success": True, "reason": "获取成功"}

    def has_spell(self, spell_id: str) -> bool:
        return spell_id in self.player_spells and self.player_spells[spell_id].get("obtained", False)

    def equip_spell(self, spell_id: str) -> Dict[str, Any]:
        if not SpellData.spell_exists(spell_id):
            return self._build_result(False, "SPELL_EQUIP_NOT_FOUND", {"spell_id": spell_id, "slot_type": ""}, spell_type="")
        if not self.has_spell(spell_id):
            return self._build_result(False, "SPELL_EQUIP_NOT_OWNED", {"spell_id": spell_id, "slot_type": ""}, spell_type="")
        if self.is_spell_equipped(spell_id):
            return self._build_result(False, "SPELL_EQUIP_ALREADY_EQUIPPED", {"spell_id": spell_id, "slot_type": ""}, spell_type="")

        spell_type = SpellData.get_spell_type(spell_id)
        if spell_type == SpellData.SPELL_TYPE_PRODUCTION:
            return self._build_result(False, "SPELL_EQUIP_PRODUCTION_FORBIDDEN", {"spell_id": spell_id, "slot_type": spell_type}, spell_type=spell_type)

        limit = self.slot_limits.get(spell_type, 0)
        current_count = len(self.equipped_spells.get(spell_type, []))
        if limit >= 0 and current_count >= limit:
            return self._build_result(False, "SPELL_SLOT_LIMIT_REACHED", {
                "spell_id": spell_id,
                "slot_type": spell_type,
                "limit": limit,
                "current_count": current_count,
            }, spell_type=spell_type)
        self.equipped_spells.setdefault(spell_type, []).append(spell_id)
        return self._build_result(True, "SPELL_EQUIP_SUCCEEDED", {"spell_id": spell_id, "slot_type": spell_type}, spell_type=spell_type)

    def unequip_spell(self, spell_id: str) -> Dict[str, Any]:
        if not SpellData.spell_exists(spell_id):
            return self._build_result(False, "SPELL_UNEQUIP_NOT_FOUND", {"spell_id": spell_id, "slot_type": ""}, spell_type="")
        if not self.is_spell_equipped(spell_id):
            return self._build_result(False, "SPELL_UNEQUIP_NOT_EQUIPPED", {"spell_id": spell_id, "slot_type": ""}, spell_type="")
        spell_type = SpellData.get_spell_type(spell_id)
        if spell_type in self.equipped_spells and spell_id in self.equipped_spells[spell_type]:
            self.equipped_spells[spell_type].remove(spell_id)
        return self._build_result(True, "SPELL_UNEQUIP_SUCCEEDED", {"spell_id": spell_id, "slot_type": spell_type}, spell_type=spell_type)

    def is_spell_equipped(self, spell_id: str) -> bool:
        return any(spell_id in equipped for equipped in self.equipped_spells.values())

    def upgrade_spell(self, spell_id: str) -> Dict[str, Any]:
        if not self.has_spell(spell_id):
            return self._build_result(False, "SPELL_UPGRADE_NOT_OWNED", {"spell_id": spell_id}, new_level=0)
        spell_info = self.player_spells[spell_id]
        max_level = SpellData.get_spell_max_level(spell_id)
        if int(spell_info.get("level", 0)) >= max_level:
            return self._build_result(False, "SPELL_UPGRADE_AT_MAX_LEVEL", {"spell_id": spell_id, "current_level": spell_info["level"], "max_level": max_level}, new_level=spell_info["level"])

        current_level = int(spell_info.get("level", 0))
        level_data = SpellData.get_spell_level_data(spell_id, current_level)
        use_count_required = int(level_data.get("use_count_required", 0))
        spirit_cost = int(level_data.get("spirit_cost", 0))

        if int(spell_info.get("use_count", 0)) < use_count_required:
            return self._build_result(False, "SPELL_UPGRADE_USE_COUNT_INSUFFICIENT", {
                "spell_id": spell_id,
                "current_level": current_level,
                "current_use_count": int(spell_info.get("use_count", 0)),
                "required_use_count": use_count_required,
            }, new_level=current_level)
        if int(spell_info.get("charged_spirit", 0)) < spirit_cost:
            return self._build_result(False, "SPELL_UPGRADE_CHARGED_SPIRIT_INSUFFICIENT", {
                "spell_id": spell_id,
                "current_level": current_level,
                "current_charged_spirit": int(spell_info.get("charged_spirit", 0)),
                "required_charged_spirit": spirit_cost,
            }, new_level=current_level)

        spell_info["charged_spirit"] = int(spell_info.get("charged_spirit", 0)) - spirit_cost
        spell_info["level"] = current_level + 1
        spell_info["use_count"] = 0
        self.recalculate_bonuses()
        return self._build_result(True, "SPELL_UPGRADE_SUCCEEDED", {"spell_id": spell_id, "new_level": spell_info["level"]}, new_level=spell_info["level"])

    def charge_spell_spirit(self, spell_id: str, amount: int, player_data: 'PlayerSystem') -> Dict[str, Any]:
        if not self.has_spell(spell_id):
            return self._build_result(False, "SPELL_CHARGE_NOT_OWNED", {"spell_id": spell_id}, charged_amount=0)
        spell_info = self.player_spells[spell_id]
        max_level = SpellData.get_spell_max_level(spell_id)
        if int(spell_info.get("level", 0)) >= max_level:
            return self._build_result(False, "SPELL_CHARGE_AT_MAX_LEVEL", {"spell_id": spell_id, "current_level": spell_info["level"], "max_level": max_level}, charged_amount=0)
        level_data = SpellData.get_spell_level_data(spell_id, int(spell_info.get("level", 0)))
        spirit_cost = int(level_data.get("spirit_cost", 0))
        need = spirit_cost - int(spell_info.get("charged_spirit", 0))
        if need <= 0:
            return self._build_result(False, "SPELL_CHARGE_ALREADY_FULL", {"spell_id": spell_id, "current_charged_spirit": int(spell_info.get('charged_spirit', 0)), "required_charged_spirit": spirit_cost}, charged_amount=0)
        available = min(int(amount), need)
        if float(player_data.spirit_energy) < available:
            available = int(player_data.spirit_energy)
        if available <= 0:
            return self._build_result(False, "SPELL_CHARGE_PLAYER_SPIRIT_INSUFFICIENT", {"spell_id": spell_id, "current_spirit": player_data.spirit_energy}, charged_amount=0)
        player_data.reduce_spirit_energy(float(available))
        spell_info["charged_spirit"] = int(spell_info.get("charged_spirit", 0)) + available
        return self._build_result(True, "SPELL_CHARGE_SUCCEEDED", {"spell_id": spell_id, "charged_amount": available}, charged_amount=available)

    def star_up_spell(self, spell_id: str, inventory_system: 'InventorySystem') -> Dict[str, Any]:
        if not self.has_spell(spell_id):
            return self._build_result(False, "SPELL_STAR_UP_NOT_OWNED", {"spell_id": spell_id}, new_star=0)
        spell_info = self.player_spells[spell_id]
        current_star = int(spell_info.get("star", 0))
        max_star = SpellData.get_spell_max_star(spell_id)
        if current_star >= max_star:
            return self._build_result(False, "SPELL_STAR_UP_AT_MAX_STAR", {"spell_id": spell_id, "current_star": current_star, "max_star": max_star}, new_star=current_star)
        star_data = SpellData.get_spell_star_data(spell_id, current_star)
        requirements = star_data.get("requirements", {})
        unlock_item_id = SpellData.get_spell_unlock_item_id(spell_id)
        unlock_item_count = int(requirements.get("unlock_item_count", 0))
        star_material_count = int(requirements.get("star_material_count", 0))
        if unlock_item_count > 0 and not inventory_system.has_item(unlock_item_id, unlock_item_count):
            return self._build_result(False, "SPELL_STAR_UP_UNLOCK_ITEM_INSUFFICIENT", {"spell_id": spell_id, "required_unlock_item_id": unlock_item_id, "required_unlock_item_count": unlock_item_count, "current_unlock_item_count": inventory_system.get_item_count(unlock_item_id)}, new_star=current_star)
        if star_material_count > 0 and not inventory_system.has_item("blank_jade_slip", star_material_count):
            return self._build_result(False, "SPELL_STAR_UP_STAR_MATERIAL_INSUFFICIENT", {"spell_id": spell_id, "required_star_material_count": star_material_count, "current_star_material_count": inventory_system.get_item_count('blank_jade_slip')}, new_star=current_star)
        if unlock_item_count > 0:
            inventory_system.remove_item(unlock_item_id, unlock_item_count)
        if star_material_count > 0:
            inventory_system.remove_item("blank_jade_slip", star_material_count)
        spell_info["star"] = current_star + 1
        self.recalculate_bonuses()
        return self._build_result(True, "SPELL_STAR_UP_SUCCEEDED", {"spell_id": spell_id, "new_star": spell_info["star"], "consumed_unlock_item_id": unlock_item_id, "consumed_unlock_item_count": unlock_item_count, "consumed_star_material_count": star_material_count}, new_star=spell_info["star"])

    def add_spell_use_count(self, spell_id: str, count: int = 1):
        count_gained = 0
        if spell_id in self.player_spells:
            spell_info = self.player_spells[spell_id]
            if spell_info.get("obtained", False):
                max_level = SpellData.get_spell_max_level(spell_id)
                if int(spell_info.get("level", 0)) < max_level:
                    level_data = SpellData.get_spell_level_data(spell_id, int(spell_info.get("level", 0)))
                    required = int(level_data.get("use_count_required", 0))
                    current = int(spell_info.get("use_count", 0))
                    if current < required:
                        count_gained = min(int(count), required - current)
                        spell_info["use_count"] = current + count_gained
        return count_gained

    def get_breathing_heal_bonus(self) -> float:
        total_heal = 0.0
        for spell_id in self.equipped_spells.get(SpellData.SPELL_TYPE_BREATHING, []):
            spell_info = self.player_spells.get(spell_id, {})
            if not spell_info.get("obtained", False) or int(spell_info.get("level", 0)) <= 0:
                continue
            for effect in self._get_current_effects(spell_id, spell_info):
                if effect.get("effect_type", "") == "passive_heal":
                    total_heal += float(effect.get("heal_percent", 0.0))
        return total_heal

    def get_herb_gather_efficiency_bonus(self) -> float:
        spell_info = self.player_spells.get("herb_gathering", {})
        if not spell_info.get("obtained", False) or int(spell_info.get("level", 0)) <= 0:
            return 0.0
        for effect in self._get_current_effects("herb_gathering", spell_info):
            if effect.get("effect_type", "") in {"herb_gathering", "gathering"}:
                return max(float(effect.get("efficiency_rate", 0.0)), 0.0)
        return 0.0

    def get_herb_gather_success_rate_bonus(self) -> float:
        spell_info = self.player_spells.get("herb_gathering", {})
        if not spell_info.get("obtained", False) or int(spell_info.get("level", 0)) <= 0:
            return 0.0
        for effect in self._get_current_effects("herb_gathering", spell_info):
            if effect.get("effect_type", "") in {"herb_gathering", "gathering"}:
                return max(float(effect.get("success_rate_bonus", 0.0)), 0.0)
        return 0.0

    def trigger_opening_spell(self) -> List[Dict[str, Any]]:
        results = []
        for spell_id in self.equipped_spells.get(SpellData.SPELL_TYPE_OPENING, []):
            spell_info = self.player_spells.get(spell_id, {})
            if not spell_info.get("obtained", False) or int(spell_info.get("level", 0)) <= 0:
                continue
            if self._get_current_effects(spell_id, spell_info):
                results.append({"triggered": True, "spell_id": spell_id})
        return results

    def trigger_active_spell(self) -> Dict[str, Any]:
        active_spells = self.equipped_spells.get(SpellData.SPELL_TYPE_ACTIVE, [])
        if not active_spells:
            return {"triggered": False, "spell_id": ""}
        spell_chances = []
        total_chance = 0.0
        for spell_id in active_spells:
            spell_info = self.player_spells.get(spell_id, {})
            if not spell_info.get("obtained", False) or int(spell_info.get("level", 0)) <= 0:
                continue
            effects = self._get_current_effects(spell_id, spell_info)
            chance = 0.0
            for effect in effects:
                chance = max(chance, float(effect.get("trigger_chance", 0.0)))
            if chance > 0:
                spell_chances.append({"spell_id": spell_id, "chance": chance})
                total_chance += chance
        if not spell_chances:
            return {"triggered": False, "spell_id": ""}
        if total_chance > self.MAX_TOTAL_TRIGGER_CHANCE:
            scale_factor = self.MAX_TOTAL_TRIGGER_CHANCE / total_chance
            total_chance = self.MAX_TOTAL_TRIGGER_CHANCE
            for item in spell_chances:
                item["chance"] *= scale_factor
        trigger_roll = random.random()
        if trigger_roll >= total_chance:
            return {"triggered": False, "spell_id": ""}
        cursor = 0.0
        for item in spell_chances:
            cursor += float(item["chance"])
            if trigger_roll < cursor:
                return {"triggered": True, "spell_id": item["spell_id"]}
        return {"triggered": True, "spell_id": spell_chances[-1]["spell_id"]}

    def use_spell(self, spell_id: str, self_attributes: dict, target_attributes: dict = None) -> Dict[str, Any]:
        if spell_id not in self.player_spells:
            return {"used": False, "effect_type": "", "effects": [], "log": {}}
        spell_info = self.player_spells[spell_id]
        if not spell_info.get("obtained", False) or int(spell_info.get("level", 0)) <= 0:
            return {"used": False, "effect_type": "", "effects": [], "log": {}}

        effects = self._get_current_effects(spell_id, spell_info)
        if not effects:
            return {"used": False, "effect_type": "", "effects": [], "log": {}}

        log = {
            "spell_id": spell_id,
            "effects": [],
        }
        any_used = False
        turn_gauge_delta = 0.0
        for effect in effects:
            effect_type = effect.get("effect_type", "")
            if effect_type == "instant_damage":
                result = self._resolve_instant_damage(effect, self_attributes, target_attributes)
                log["effects"].append(result)
                any_used = True
            elif effect_type == "drain_health":
                if log["effects"]:
                    drained = self._apply_drain_health(effect, self_attributes, log["effects"][-1].get("damage", 0.0))
                    log["effects"].append(drained)
                    any_used = True
            elif effect_type == "turn_gauge_delta":
                delta = float(effect.get("delta", 0.0))
                turn_gauge_delta += delta
                log["effects"].append({"effect_type": "turn_gauge_delta", "delta": round(delta, 4)})
                any_used = True
            elif effect_type == "undispellable_buff":
                buff_result = self._use_undispellable_buff_effect(effect, self_attributes)
                log["effects"].append(buff_result)
                any_used = any_used or buff_result.get("used", False)
            else:
                log["effects"].append({"effect_type": effect_type, "used": False})

        if turn_gauge_delta != 0.0:
            log["turn_gauge_delta"] = round(turn_gauge_delta, 4)

        primary_effect_type = effects[0].get("effect_type", "")
        return {
            "used": any_used,
            "effect_type": primary_effect_type,
            "effects": effects,
            "log": log,
            "turn_gauge_delta": round(turn_gauge_delta, 4),
        }

    def _resolve_instant_damage(self, effect: Dict[str, Any], self_attributes: dict, target_attributes: dict) -> Dict[str, Any]:
        attack = float(self_attributes.get("attack", 0.0))
        defense = float((target_attributes or {}).get("defense", 0.0))
        penetration = float(self_attributes.get("penetration", 0.0))
        hit = float(self_attributes.get("hit", 1.0))
        dodge = float((target_attributes or {}).get("dodge", 0.0))
        crit = float(self_attributes.get("crit", 0.0))
        anti_crit = float((target_attributes or {}).get("anti_crit", 0.0))
        crit_damage = float(self_attributes.get("crit_damage", 1.0))

        damage_min = float(effect.get("damage_percent_min", effect.get("damage_percent", 1.0)))
        damage_max = float(effect.get("damage_percent_max", damage_min))
        damage_percent = random.uniform(damage_min, damage_max)

        damage_result = AttributeCalculator.resolve_damage(
            attack,
            defense,
            hit,
            dodge,
            crit,
            anti_crit,
            crit_damage,
            damage_percent,
            penetration,
        )
        is_hit = bool(damage_result.get("hit", False))
        if not is_hit:
            return {
                "effect_type": "instant_damage",
                "hit": False,
                "crit": False,
                "damage": 0.0,
                "damage_percent": round(damage_percent, 4),
                "target_health_after": round(float((target_attributes or {}).get("health", 0.0)), 2),
            }
        damage = float(damage_result.get("damage", 0.0))
        is_crit = bool(damage_result.get("crit", False))
        if target_attributes is not None:
            target_attributes["health"] = round(max(0.0, float(target_attributes.get("health", 0.0)) - damage), 2)
        return {
            "effect_type": "instant_damage",
            "hit": True,
            "crit": is_crit,
            "damage": round(damage, 2),
            "damage_percent": round(damage_percent, 4),
            "target_health_after": round(float((target_attributes or {}).get("health", 0.0)), 2),
        }

    def _apply_drain_health(self, effect: Dict[str, Any], self_attributes: dict, damage: float) -> Dict[str, Any]:
        drain_percent = float(effect.get("drain_percent", 0.0))
        heal_amount = round(max(damage, 0.0) * drain_percent, 2)
        max_health = float(self_attributes.get("max_health", 0.0))
        self_attributes["health"] = min(max_health, float(self_attributes.get("health", 0.0)) + heal_amount)
        return {
            "effect_type": "drain_health",
            "heal_amount": heal_amount,
            "self_health_after": round(float(self_attributes.get("health", 0.0)), 2),
        }

    def _use_undispellable_buff_effect(self, effect: Dict[str, Any], self_attributes: dict) -> Dict[str, Any]:
        buff_type = str(effect.get("buff_type", ""))
        buff_percent = float(effect.get("buff_percent", 0.0))
        buff_value = float(effect.get("buff_value", 0.0))
        result = {"effect_type": "undispellable_buff", "buff_type": buff_type, "used": False}

        if buff_type in {"attack", "defense", "penetration", "crit_damage"} and buff_percent > 0:
            self_attributes[buff_type] = round(float(self_attributes.get(buff_type, 0.0)) * (1.0 + buff_percent), 4 if buff_type == 'crit_damage' else 2)
            result["used"] = True
            result["buff_percent"] = buff_percent
        elif buff_type == "health" and buff_percent > 0:
            max_health_increase = float(self_attributes.get("max_health", 0.0)) * buff_percent
            self_attributes["max_health"] += max_health_increase
            self_attributes["health"] += max_health_increase
            result["used"] = True
            result["buff_percent"] = buff_percent
            result["self_health_after"] = round(float(self_attributes.get("health", 0.0)), 2)
            result["self_max_health_after"] = round(float(self_attributes.get("max_health", 0.0)), 2)
        elif buff_type == "speed" and buff_value > 0:
            self_attributes[buff_type] = round(float(self_attributes.get(buff_type, 0.0)) + buff_value, 4)
            result["used"] = True
            result["buff_value"] = buff_value
        elif buff_type in {"hit", "dodge", "crit", "anti_crit"}:
            additive_percent = buff_percent if buff_percent > 0 else buff_value
            if additive_percent > 0:
                self_attributes[buff_type] = round(float(self_attributes.get(buff_type, 0.0)) + additive_percent, 4)
                result["used"] = True
                result["buff_percent"] = additive_percent
        return result

    def build_spell_snapshot(self, spell_id: str) -> Dict[str, Any]:
        spell_info = self.player_spells.get(spell_id, {})
        level = int(spell_info.get("level", 0))
        star = int(spell_info.get("star", 0))
        return {
            "id": spell_id,
            "name": SpellData.get_spell_name(spell_id),
            "type": SpellData.get_spell_type(spell_id),
            "rarity": SpellData.get_spell_rarity(spell_id),
            "quality": SpellData.get_spell_quality(spell_id),
            "element": SpellData.get_spell_element(spell_id),
            "description": SpellData.get_spell_description(spell_id),
            "obtained": bool(spell_info.get("obtained", False)),
            "level": level,
            "star": star,
            "max_level": SpellData.get_spell_max_level(spell_id),
            "max_star": SpellData.get_spell_max_star(spell_id),
            "use_count": int(spell_info.get("use_count", 0)),
            "charged_spirit": int(spell_info.get("charged_spirit", 0)),
            "equipped": self.is_spell_equipped(spell_id),
            "current_level_data": SpellData.get_spell_level_data(spell_id, level) if level > 0 else {},
            "current_effects": SpellData.get_spell_effects(spell_id, level) if level > 0 else [],
            "next_star_data": SpellData.get_spell_star_data(spell_id, star) if star < SpellData.get_spell_max_star(spell_id) else {},
        }

    def to_dict(self) -> dict:
        return {
            "player_spells": self.player_spells,
            "equipped_spells": self.equipped_spells,
            "slot_limits": self.slot_limits,
        }

    @classmethod
    def from_dict(cls, db_data: dict) -> 'SpellSystem':
        instance = cls()
        raw_player_spells = db_data.get("player_spells", {})
        for spell_id, spell_info in raw_player_spells.items():
            if not isinstance(spell_info, dict):
                continue
            instance.player_spells[spell_id] = {
                "obtained": bool(spell_info.get("obtained", False) or int(spell_info.get("level", 0)) > 0),
                "level": int(spell_info.get("level", 0)),
                "star": int(spell_info.get("star", 0)),
                "use_count": int(spell_info.get("use_count", 0)),
                "charged_spirit": int(spell_info.get("charged_spirit", 0)),
            }
        instance.equipped_spells = db_data.get("equipped_spells", {
            SpellData.SPELL_TYPE_BREATHING: [],
            SpellData.SPELL_TYPE_ACTIVE: [],
            SpellData.SPELL_TYPE_OPENING: []
        })
        instance.slot_limits = db_data.get("slot_limits", {
            SpellData.SPELL_TYPE_BREATHING: 1,
            SpellData.SPELL_TYPE_ACTIVE: 2,
            SpellData.SPELL_TYPE_OPENING: 2
        })
        instance.recalculate_bonuses()
        return instance
