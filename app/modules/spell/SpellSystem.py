"""
术法系统

负责管理玩家的术法数据，包括装备、升级、充灵气等功能
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
import random

from .SpellData import SpellData

if TYPE_CHECKING:
    from ..player.PlayerData import PlayerData


class SpellSystem:
    """术法系统"""
    
    MAX_TOTAL_TRIGGER_CHANCE = 0.80
    
    def __init__(self):
        """初始化术法系统"""
        self.player_spells: Dict[str, Dict[str, Any]] = {}
        self.equipped_spells: Dict[int, List[str]] = {
            SpellData.SLOT_BREATHING: [],
            SpellData.SLOT_ACTIVE: [],
            SpellData.SLOT_PASSIVE: []
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
                "spell_type": int
            }
        """
        if not SpellData.spell_exists(spell_id):
            return {"success": False, "reason": "术法不存在", "spell_type": -1}
        
        if not self.has_spell(spell_id):
            return {"success": False, "reason": "未获取该术法", "spell_type": -1}
        
        if self.is_spell_equipped(spell_id):
            return {"success": False, "reason": "术法已装备", "spell_type": -1}
        
        spell_type = SpellData.get_spell_type(spell_id)
        
        if spell_type == SpellData.SPELL_TYPE_MISC:
            return {"success": False, "reason": "杂学术法无法装备", "spell_type": spell_type}
        
        limit = SpellData.get_slot_limit(spell_type)
        current_count = len(self.equipped_spells.get(spell_type, []))
        
        if limit >= 0 and current_count >= limit:
            return {
                "success": False,
                "reason": f"装备数量已达上限（{limit}个）",
                "spell_type": spell_type
            }
        
        if spell_type not in self.equipped_spells:
            self.equipped_spells[spell_type] = []
        
        self.equipped_spells[spell_type].append(spell_id)
        
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
                "spell_type": int
            }
        """
        if not SpellData.spell_exists(spell_id):
            return {"success": False, "reason": "术法不存在", "spell_type": -1}
        
        if not self.is_spell_equipped(spell_id):
            return {"success": False, "reason": "术法未装备", "spell_type": -1}
        
        spell_type = SpellData.get_spell_type(spell_id)
        
        if spell_type in self.equipped_spells and spell_id in self.equipped_spells[spell_type]:
            self.equipped_spells[spell_type].remove(spell_id)
        
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
    
    def upgrade_spell(self, spell_id: str, player_data: 'PlayerData') -> Dict[str, Any]:
        """
        升级术法
        
        Args:
            spell_id: 术法ID
            player_data: 玩家数据（用于扣除灵气）
        
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
    
    def charge_spell_spirit(self, spell_id: str, amount: int, player_data: 'PlayerData') -> Dict[str, Any]:
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
    
    def add_spell_use_count(self, spell_id: str):
        """增加术法使用次数"""
        if spell_id in self.player_spells:
            spell_info = self.player_spells[spell_id]
            if spell_info.get("obtained", False):
                max_level = SpellData.get_spell_max_level(spell_id)
                
                if spell_info["level"] < max_level:
                    current_level = spell_info["level"]
                    level_data = SpellData.get_spell_level_data(spell_id, current_level)
                    use_count_required = level_data.get("use_count_required", 0)
                    
                    if spell_info["use_count"] < use_count_required:
                        spell_info["use_count"] += 1
    
    def get_breathing_heal_bonus(self) -> float:
        """获取吐纳术法的气血恢复加成"""
        total_heal = 0.0
        
        for spell_id in self.equipped_spells.get(SpellData.SLOT_BREATHING, []):
            if spell_id not in self.player_spells:
                continue
            
            spell_info = self.player_spells[spell_id]
            if not spell_info.get("obtained", False) or spell_info.get("level", 0) <= 0:
                continue
            
            level_data = SpellData.get_spell_level_data(spell_id, spell_info["level"])
            effect = level_data.get("effect", {})
            
            if effect.get("type") == "passive_heal":
                heal_percent = effect.get("heal_percent", 0.0)
                total_heal += heal_percent
        
        return total_heal
    
    def trigger_attack_spell(self) -> Dict[str, Any]:
        """
        触发攻击术法
        
        Returns:
            {
                "triggered": bool,
                "spell_name": str,
                "damage_percent": float
            }
        """
        active_spells = self.equipped_spells.get(SpellData.SLOT_ACTIVE, [])
        if not active_spells:
            return {"triggered": False, "spell_name": "", "damage_percent": 100.0}
        
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
            
            if effect.get("type") == "active_damage":
                chance = effect.get("trigger_chance", 0.0)
                damage_percent = effect.get("damage_percent", 100.0)
                spell_chances.append({
                    "spell_id": spell_id,
                    "chance": chance,
                    "damage_percent": damage_percent
                })
                total_chance += chance
        
        if not spell_chances:
            return {"triggered": False, "spell_name": "", "damage_percent": 100.0}
        
        if total_chance > self.MAX_TOTAL_TRIGGER_CHANCE:
            scale_factor = self.MAX_TOTAL_TRIGGER_CHANCE / total_chance
            total_chance = self.MAX_TOTAL_TRIGGER_CHANCE
            for spell_chance in spell_chances:
                spell_chance["chance"] *= scale_factor
        
        normal_attack_chance = max(0.2, 1.0 - total_chance)
        
        if random.random() < normal_attack_chance:
            return {"triggered": False, "spell_name": "", "damage_percent": 100.0}
        
        selected = random.choice(spell_chances)
        spell_name = SpellData.get_spell_name(selected["spell_id"])
        
        self.add_spell_use_count(selected["spell_id"])
        
        return {
            "triggered": True,
            "spell_name": spell_name,
            "damage_percent": selected["damage_percent"]
        }
    
    def to_db_data(self) -> dict:
        """转换为数据库存储格式"""
        return {
            "player_spells": self.player_spells,
            "equipped_spells": self.equipped_spells
        }
    
    @classmethod
    def from_db_data(cls, db_data: dict) -> 'SpellSystem':
        """从数据库数据创建"""
        instance = cls()
        instance.player_spells = db_data.get("player_spells", {})
        instance.equipped_spells = db_data.get("equipped_spells", {
            SpellData.SLOT_BREATHING: [],
            SpellData.SLOT_ACTIVE: [],
            SpellData.SLOT_PASSIVE: []
        })
        instance.recalculate_bonuses()
        return instance
