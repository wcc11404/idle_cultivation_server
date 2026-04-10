"""
术法系统

负责管理玩家的术法数据，包括装备、升级、充灵气等功能
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
import random

from app.modules.player.AttributeCalculator import AttributeCalculator
from .SpellData import SpellData

if TYPE_CHECKING:
    from ..player.PlayerSystem import PlayerSystem


class SpellSystem:
    """术法系统"""
    
    MAX_TOTAL_TRIGGER_CHANCE = 0.80
    
    def __init__(self):
        """初始化术法系统"""
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
            "spirit_gain": 1.0
        }
    
    def recalculate_bonuses(self):
        """重新计算并缓存属性加成"""
        bonuses = {
            "health": 1.0,
            "attack": 1.0,
            "defense": 1.0,
            "speed": 0.0,
            "max_spirit": 1.0,
            "spirit_gain": 1.0
        }
        
        for spell_id, spell_info in self.player_spells.items():
            if not spell_info.get("obtained", False) or spell_info.get("level", 0) <= 0:
                continue
            
            level_data = SpellData.get_spell_level_data(spell_id, spell_info["level"])
            attribute_bonus = level_data.get("attribute_bonus", {})
            
            for attr, value in attribute_bonus.items():
                if attr == "speed":
                    bonuses[attr] += value
                else:
                    bonuses[attr] *= value
        
        self._cached_bonuses = bonuses
    
    def get_attribute_bonuses(self) -> Dict[str, float]:
        """获取缓存的属性加成"""
        return self._cached_bonuses
    
    def unlock_spell(self, spell_id: str) -> Dict[str, Any]:
        """
        解锁术法
        
        Args:
            spell_id: 术法ID
        
        Returns:
            {
                "success": bool,
                "reason": str
            }
        """
        if not SpellData.spell_exists(spell_id):
            return {"success": False, "reason": "术法不存在"}
        
        if spell_id in self.player_spells and self.player_spells[spell_id].get("obtained", False):
            return {"success": False, "reason": "已获取该术法"}
        
        self.player_spells[spell_id] = {
            "obtained": True,
            "level": 1,
            "use_count": 0,
            "charged_spirit": 0
        }
        
        self.recalculate_bonuses()
        
        return {"success": True, "reason": "获取成功"}
    
    def has_spell(self, spell_id: str) -> bool:
        """检查是否已获取术法"""
        return spell_id in self.player_spells and self.player_spells[spell_id].get("obtained", False)
    
    def equip_spell(self, spell_id: str) -> Dict[str, Any]:
        """
        装备术法
        
        Args:
            spell_id: 术法ID
        
        Returns:
            {
                "success": bool,
                "reason": str,
                "spell_type": str
            }
        """
        if not SpellData.spell_exists(spell_id):
            return {"success": False, "reason": "术法不存在", "spell_type": ""}
        
        if not self.has_spell(spell_id):
            return {"success": False, "reason": "未获取该术法", "spell_type": ""}
        
        if self.is_spell_equipped(spell_id):
            return {"success": False, "reason": "术法已装备", "spell_type": ""}
        
        spell_type = SpellData.get_spell_type(spell_id)
        
        if spell_type == SpellData.SPELL_TYPE_PRODUCTION:
            return {"success": False, "reason": "杂学术法无法装备", "spell_type": spell_type}
        
        # 槽位类型与术法类型一致
        slot_type = spell_type
        
        limit = self.slot_limits.get(slot_type, 0)
        current_count = len(self.equipped_spells.get(slot_type, []))
        
        if limit >= 0 and current_count >= limit:
            return {
                "success": False,
                "reason": f"{slot_type}槽位已达上限",
                "spell_type": spell_type
            }
        
        if slot_type not in self.equipped_spells:
            self.equipped_spells[slot_type] = []
        
        self.equipped_spells[slot_type].append(spell_id)
        
        return {
            "success": True,
            "reason": "装备成功",
            "spell_type": spell_type
        }
    
    def unequip_spell(self, spell_id: str) -> Dict[str, Any]:
        """
        卸下术法
        
        Args:
            spell_id: 术法ID
        
        Returns:
            {
                "success": bool,
                "reason": str,
                "spell_type": str
            }
        """
        if not SpellData.spell_exists(spell_id):
            return {"success": False, "reason": "术法不存在", "spell_type": ""}
        
        if not self.is_spell_equipped(spell_id):
            return {"success": False, "reason": "术法未装备", "spell_type": ""}
        
        spell_type = SpellData.get_spell_type(spell_id)
        
        # 槽位类型与术法类型一致
        slot_type = spell_type
        
        if slot_type != "" and slot_type in self.equipped_spells and spell_id in self.equipped_spells[slot_type]:
            self.equipped_spells[slot_type].remove(spell_id)
        
        return {
            "success": True,
            "reason": "卸下成功",
            "spell_type": spell_type
        }
    
    def is_spell_equipped(self, spell_id: str) -> bool:
        """检查术法是否已装备"""
        for slot_type in self.equipped_spells:
            if spell_id in self.equipped_spells[slot_type]:
                return True
        return False
    
    def upgrade_spell(self, spell_id: str) -> Dict[str, Any]:
        """
        升级术法
        
        Args:
            spell_id: 术法ID
        
        Returns:
            {
                "success": bool,
                "reason": str,
                "new_level": int
            }
        """
        if not self.has_spell(spell_id):
            return {"success": False, "reason": "未获取该术法", "new_level": 0}
        
        spell_info = self.player_spells[spell_id]
        max_level = SpellData.get_spell_max_level(spell_id)
        
        if spell_info["level"] >= max_level:
            return {"success": False, "reason": "已达到最高等级", "new_level": spell_info["level"]}
        
        current_level = spell_info["level"]
        level_data = SpellData.get_spell_level_data(spell_id, current_level)
        
        use_count_required = level_data.get("use_count_required", 0)
        spirit_cost = level_data.get("spirit_cost", 0)
        
        if spell_info["use_count"] < use_count_required:
            return {
                "success": False,
                "reason": f"使用次数不足（{spell_info['use_count']}/{use_count_required}）",
                "new_level": current_level
            }
        
        if spell_info["charged_spirit"] < spirit_cost:
            return {
                "success": False,
                "reason": f"充灵气不足（{spell_info['charged_spirit']}/{spirit_cost}）",
                "new_level": current_level
            }
        
        spell_info["charged_spirit"] -= spirit_cost
        spell_info["level"] = current_level + 1
        spell_info["use_count"] = 0
        
        self.recalculate_bonuses()
        
        return {
            "success": True,
            "reason": "升级成功",
            "new_level": spell_info["level"]
        }
    
    def charge_spell_spirit(self, spell_id: str, amount: int, player_data: 'PlayerSystem') -> Dict[str, Any]:
        """
        给术法充灵气
        
        Args:
            spell_id: 术法ID
            amount: 充灵气数量
            player_data: 玩家数据（用于扣除灵气）
        
        Returns:
            {
                "success": bool,
                "reason": str,
                "charged_amount": int
            }
        """
        if not self.has_spell(spell_id):
            return {"success": False, "reason": "未获取该术法", "charged_amount": 0}
        
        spell_info = self.player_spells[spell_id]
        max_level = SpellData.get_spell_max_level(spell_id)
        
        if spell_info["level"] >= max_level:
            return {"success": False, "reason": "已达到最高等级", "charged_amount": 0}
        
        current_level = spell_info["level"]
        level_data = SpellData.get_spell_level_data(spell_id, current_level)
        spirit_cost = level_data.get("spirit_cost", 0)
        
        need = spirit_cost - spell_info["charged_spirit"]
        if need <= 0:
            return {"success": False, "reason": "灵气已充足", "charged_amount": 0}
        
        available = min(amount, need)
        if player_data.spirit_energy < available:
            available = int(player_data.spirit_energy)
        
        if available <= 0:
            return {"success": False, "reason": "自身灵气不足", "charged_amount": 0}
        
        player_data.reduce_spirit_energy(float(available))
        spell_info["charged_spirit"] += available
        
        return {
            "success": True,
            "reason": "充灵气成功",
            "charged_amount": available
        }
    
    def add_spell_use_count(self, spell_id: str, count: int = 1):
        """增加术法使用次数"""
        count_gained = 0
        if spell_id in self.player_spells:
            spell_info = self.player_spells[spell_id]
            if spell_info.get("obtained", False):
                max_level = SpellData.get_spell_max_level(spell_id)
                
                if spell_info["level"] < max_level:
                    current_level = spell_info["level"]
                    level_data = SpellData.get_spell_level_data(spell_id, current_level)
                    use_count_required = level_data.get("use_count_required", 0)
                    
                    if spell_info["use_count"] < use_count_required:
                        count_gained = min(count, use_count_required - spell_info["use_count"])
                        spell_info["use_count"] += count_gained
        return count_gained
    
    def get_breathing_heal_bonus(self) -> float:
        """获取吐纳术法的气血恢复加成"""
        total_heal = 0.0
        
        for spell_id in self.equipped_spells.get(SpellData.SPELL_TYPE_BREATHING, []):
            if spell_id not in self.player_spells:
                continue
            
            spell_info = self.player_spells[spell_id]
            if not spell_info.get("obtained", False) or spell_info.get("level", 0) <= 0:
                continue
            
            level_data = SpellData.get_spell_level_data(spell_id, spell_info["level"])
            effect = level_data.get("effect", {})
            
            if effect.get("effect_type", "") == "passive_heal":
                heal_percent = effect.get("heal_percent", 0.0)
                total_heal += heal_percent
        
        return total_heal
    
    def trigger_opening_spell(self) -> List[Dict[str, Any]]:
        """
        触发开场术法（被动术法）
        
        Returns:
            [
                {
                    "triggered": bool,
                    "spell_id": str
                }
            ]
        """
        results = []
        opening_spells = self.equipped_spells.get(SpellData.SPELL_TYPE_OPENING, [])
        
        for spell_id in opening_spells:
            if spell_id not in self.player_spells:
                continue
            
            spell_info = self.player_spells[spell_id]
            if not spell_info.get("obtained", False) or spell_info.get("level", 0) <= 0:
                continue
            
            level_data = SpellData.get_spell_level_data(spell_id, spell_info["level"])
            effect = level_data.get("effect", {})
            effect_type = effect.get("effect_type", "")
            
            if effect_type == "undispellable_buff":
                results.append({
                    "triggered": True,
                    "spell_id": spell_id,
                })
        
        return results
    
    def trigger_active_spell(self) -> Dict[str, Any]:
        """
        触发主动术法
        
        Returns:
            {
                "triggered": bool,
                "spell_id": str
            }
        """
        active_spells = self.equipped_spells.get(SpellData.SPELL_TYPE_ACTIVE, [])
        if not active_spells:
            return {"triggered": False, "spell_id": ""}
        
        spell_chances = []
        total_chance = 0.0
        
        for spell_id in active_spells:
            if spell_id not in self.player_spells:
                continue
            
            spell_info = self.player_spells[spell_id]
            if not spell_info.get("obtained", False) or spell_info.get("level", 0) <= 0:
                continue
            
            level_data = SpellData.get_spell_level_data(spell_id, spell_info["level"])
            effect = level_data.get("effect", {})
            
            # 所有类型的术法只要有释放几率都参与计算
            chance = effect.get("trigger_chance", 0.0)
            if chance > 0:
                spell_chances.append({
                    "spell_id": spell_id,
                    "chance": chance
                })
                total_chance += chance
        
        if not spell_chances:
            return {"triggered": False, "spell_id": ""}
        
        if total_chance > self.MAX_TOTAL_TRIGGER_CHANCE:
            scale_factor = self.MAX_TOTAL_TRIGGER_CHANCE / total_chance
            total_chance = self.MAX_TOTAL_TRIGGER_CHANCE
            for spell_chance in spell_chances:
                spell_chance["chance"] *= scale_factor
        
        normal_attack_chance = max(0.2, 1.0 - total_chance)
        
        if random.random() < normal_attack_chance:
            return {"triggered": False, "spell_id": ""}
        
        selected = random.choice(spell_chances)
        
        return {
            "triggered": True,
            "spell_id": selected["spell_id"]
        }
    
    def use_spell(self, spell_id: str, self_attributes: dict, target_attributes: dict = None) -> Dict[str, Any]:
        """
        使用术法
        
        Args:
            spell_id: 术法ID
            self_attributes: 自身属性
            target_attributes: 目标属性
            
        属性结构:
        {
            "health": float,
            "max_health": float,
            "speed": float,
            "attack": float,
            "defense": float
        }
        
        Returns:
            {
                "used": bool,
                "effect_type": str,
                "log": dict  # 用于战斗日志的信息
            }
        """
        # 异常校验
        if spell_id not in self.player_spells:
            return {"used": False, "effect_type": "", "log": {}}
        spell_info = self.player_spells[spell_id]
        if not spell_info.get("obtained", False) or spell_info.get("level", 0) <= 0:
            return {"used": False, "effect_type": "", "log": {}}
        
        # 获取术法效果
        level_data = SpellData.get_spell_level_data(spell_id, spell_info["level"])
        effect = level_data.get("effect", {})
        effect_type = effect.get("effect_type", "")
        
        # 根据效果类型处理
        if effect_type == "instant_damage":
            return self._use_instant_damage_spell(spell_id, effect, self_attributes, target_attributes)
        elif effect_type == "undispellable_buff":
            return self._use_undispellable_buff_spell(spell_id, effect, self_attributes)
        # 可以在这里添加其他类型的效果处理
        
        return {"used": False, "effect_type": effect_type, "log": {}}
    
    def _use_instant_damage_spell(self, spell_id: str, effect: dict, self_attributes: dict, target_attributes: dict) -> Dict[str, Any]:
        """
        使用即时伤害术法
        """
        damage_percent = effect.get("damage_percent", 1.0)
        attack = self_attributes.get("attack", 0.0)
        defense = target_attributes.get("defense", 0.0)
        
        # 计算伤害
        damage = AttributeCalculator.calculate_damage(attack, defense, damage_percent)
        
        # 应用伤害
        target_attributes["health"] = max(0.0, target_attributes["health"] - damage)
        
        return {
            "used": True,
            "log": {
                "spell_id": spell_id,
                "effect_type": "instant_damage",
                "damage": round(damage, 2),
                "target_health_after": round(target_attributes["health"], 2)
            }
        }
    
    def _use_undispellable_buff_spell(self, spell_id: str, effect: dict, self_attributes: dict) -> Dict[str, Any]:
        """
        使用不可驱散的buff术法
        """
        log = {
            "spell_id": spell_id,
            "effect_type": "undispellable_buff",
            "log_effect": effect.get("log_effect", "")
        }
        buff_type = effect.get("buff_type", "")
        buff_percent = effect.get("buff_percent", 0.0)
        buff_value = effect.get("buff_value", 0.0)
        
        # 应用buff
        if buff_percent > 0:
            if buff_type == "defense":
                self_attributes["defense"] *= (1.0 + buff_percent)
            elif buff_type == "attack":
                self_attributes["attack"] *= (1.0 + buff_percent)
            elif buff_type == "health":
                # 提升气血和气血上限
                max_health_increase = self_attributes.get("max_health", 0.0) * buff_percent
                self_attributes["max_health"] += max_health_increase
                self_attributes["health"] += max_health_increase
                log["self_health_after"] = round(self_attributes["health"], 2)
                log["self_max_health_after"] = round(self_attributes["max_health"], 2)
        elif buff_value > 0:
            if buff_type == "speed":
                self_attributes["speed"] += buff_value
                log["speed_increase"] = round(buff_value, 2)
        else:
            return {
                "used": False,
                "log": log
            }
        
        return {
            "used": True,
            "log": log
        }
    
    def to_dict(self) -> dict:
        """转换为数据库存储格式"""
        return {
            "player_spells": self.player_spells,
            "equipped_spells": self.equipped_spells,
            "slot_limits": self.slot_limits
        }
    
    @classmethod
    def from_dict(cls, db_data: dict) -> 'SpellSystem':
        """从数据库数据创建"""
        instance = cls()
        instance.player_spells = db_data.get("player_spells", {})
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
