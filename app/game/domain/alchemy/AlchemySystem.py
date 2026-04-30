"""
炼丹系统

负责管理玩家的炼丹功能，包括学习丹方、炼制丹药等
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
import random

from .RecipeData import RecipeData

if TYPE_CHECKING:
    from ..player.PlayerSystem import PlayerSystem
    from ..spell.SpellSystem import SpellSystem
    from ..inventory.InventorySystem import InventorySystem


class AlchemySystem:
    """炼丹系统"""
    
    FURNACE_CONFIGS = {
        "alchemy_furnace": {
            "name": "初级丹炉",
            "success_bonus": 10,
            "speed_rate": 0.1
        }
    }
    
    def __init__(self):
        """
        初始化炼丹系统
        """
        self.learned_recipes: List[str] = []
        self.equipped_furnace_id: str = ""
        self.is_alchemizing: bool = False
        self.last_alchemy_report_time: float = 0.0
    
    def learn_recipe(self, recipe_id: str) -> Dict[str, Any]:
        """
        学习丹方
        
        Args:
            recipe_id: 丹方ID
        
        Returns:
            {
                "success": bool,
                "reason_code": str,
                "reason_data": dict
            }
        """
        if not RecipeData.recipe_exists(recipe_id):
            return {
                "success": False,
                "reason_code": "ALCHEMY_LEARN_RECIPE_NOT_FOUND",
                "reason_data": {"recipe_id": recipe_id}
            }
        
        if recipe_id in self.learned_recipes:
            return {
                "success": False,
                "reason_code": "ALCHEMY_LEARN_RECIPE_ALREADY_LEARNED",
                "reason_data": {"recipe_id": recipe_id}
            }
        
        self.learned_recipes.append(recipe_id)
        
        return {
            "success": True,
            "reason_code": "ALCHEMY_LEARN_RECIPE_SUCCEEDED",
            "reason_data": {"recipe_id": recipe_id}
        }
    
    def has_learned_recipe(self, recipe_id: str) -> bool:
        """检查是否学会丹方"""
        return recipe_id in self.learned_recipes
    
    def has_recipe(self, recipe_id: str) -> bool:
        """检查是否学会丹方（别名）"""
        return self.has_learned_recipe(recipe_id)
    
    def get_learned_recipes(self) -> List[str]:
        """获取已学会的丹方列表"""
        return self.learned_recipes.copy()
    
    def has_furnace(self) -> bool:
        """检查是否拥有丹炉"""
        return self.equipped_furnace_id != "" and self.equipped_furnace_id in self.FURNACE_CONFIGS
    
    def equip_furnace(self, furnace_id: str) -> bool:
        """装备丹炉"""
        if furnace_id not in self.FURNACE_CONFIGS:
            return False
        self.equipped_furnace_id = furnace_id
        return True
    
    def get_equipped_furnace_id(self) -> str:
        """获取当前装备的丹炉ID"""
        return self.equipped_furnace_id
    
    def get_furnace_config(self, furnace_id: str) -> dict:
        """获取丹炉配置"""
        return self.FURNACE_CONFIGS.get(furnace_id, {})
    
    def get_alchemy_bonus(self, spell_system: 'SpellSystem' = None) -> Dict[str, Any]:
        """获取炼丹术加成"""
        bonus = {
            "success_bonus": 0,
            "speed_rate": 0.0,
            "level": 0,
            "obtained": False
        }
        
        if not spell_system:
            return bonus
        
        if "alchemy" not in spell_system.player_spells:
            return bonus
        
        spell_info = spell_system.player_spells["alchemy"]
        if not spell_info.get("obtained", False):
            return bonus
        
        bonus["obtained"] = True
        level = spell_info.get("level", 0)
        bonus["level"] = level
        
        if level > 0:
            from ..spell.SpellData import SpellData
            level_data = SpellData.get_spell_level_data("alchemy", level)
            effect = level_data.get("effect", {})
            bonus["success_bonus"] = effect.get("success_bonus", 0)
            bonus["speed_rate"] = effect.get("speed_rate", 0.0)
        
        return bonus
    
    def get_furnace_bonus(self) -> Dict[str, Any]:
        """获取丹炉加成"""
        bonus = {
            "success_bonus": 0,
            "speed_rate": 0.0,
            "has_furnace": False,
            "furnace_name": ""
        }
        
        if not self.has_furnace():
            return bonus
        
        config = self.FURNACE_CONFIGS.get(self.equipped_furnace_id, {})
        bonus["has_furnace"] = True
        bonus["success_bonus"] = config.get("success_bonus", 0)
        bonus["speed_rate"] = config.get("speed_rate", 0.0)
        bonus["furnace_name"] = config.get("name", "未知丹炉")
        
        return bonus
    
    def reset_alchemy_state(self):
        """重置炼丹状态"""
        self.is_alchemizing = False
        self.last_alchemy_report_time = 0.0
    
    def to_dict(self) -> dict:
        """转换为数据库存储格式"""
        return {
            "learned_recipes": self.learned_recipes,
            "equipped_furnace_id": self.equipped_furnace_id,
            "is_alchemizing": self.is_alchemizing,
            "last_alchemy_report_time": self.last_alchemy_report_time
        }
    
    @classmethod
    def from_dict(cls, db_data: dict) -> 'AlchemySystem':
        """从数据库数据创建"""
        instance = cls()
        instance.learned_recipes = db_data.get("learned_recipes", [])
        instance.equipped_furnace_id = db_data.get("equipped_furnace_id", "")
        instance.is_alchemizing = db_data.get("is_alchemizing", False)
        instance.last_alchemy_report_time = db_data.get("last_alchemy_report_time", 0.0)
        return instance
