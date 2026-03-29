"""
修炼系统

提供修炼相关的基础功能：
1. 修炼tick处理
2. 离线修炼处理
3. 突破检查
4. 突破执行
"""

from typing import Dict, Any, TYPE_CHECKING

from ..player.AttributeCalculator import AttributeCalculator
from .RealmData import RealmData

if TYPE_CHECKING:
    from ..player.PlayerData import PlayerData
    from ..spell.SpellSystem import SpellSystem
    from ..inventory.InventorySystem import InventorySystem


class CultivationSystem:
    """
    修炼系统 - 提供修炼相关的基础功能
    
    所有方法都是静态方法，无需实例化
    """
    
    @staticmethod
    def calculate_health_regen_per_second(player: 'PlayerData', spell_system: 'SpellSystem' = None) -> float:
        """
        计算每秒气血恢复速度
        
        修炼时自动恢复气血，这个功能是修炼系统特有的
        
        Args:
            player: 玩家数据
            spell_system: 术法系统（可选，用于获取吐纳术法加成）
        
        Returns:
            每秒气血恢复量
        """
        base_regen = float(player.health_regen_per_second)
        
        if spell_system:
            breathing_bonus = spell_system.get_breathing_heal_bonus()
            if breathing_bonus > 0:
                static_max_health = AttributeCalculator.calculate_static_max_health(player, spell_system)
                base_regen += float(static_max_health) * breathing_bonus
        
        return base_regen
    
    @staticmethod
    def process_cultivation_tick(player: 'PlayerData', delta_seconds: float, 
                                  spell_system: 'SpellSystem' = None) -> Dict[str, Any]:
        """
        处理修炼tick（每次修炼循环调用）
        
        Args:
            player: 玩家数据
            delta_seconds: 时间间隔（秒）
            spell_system: 术法系统（可选）
        
        Returns:
            {
                "spirit_gained": float,
                "health_gained": float
            }
        """
        spirit_speed = AttributeCalculator.calculate_spirit_gain_speed(player, spell_system)
        spirit_gained = spirit_speed * delta_seconds
        
        health_speed = CultivationSystem.calculate_health_regen_per_second(player, spell_system)
        health_gained = health_speed * delta_seconds
        
        actual_spirit = player.add_spirit_energy(spirit_gained, spell_system)
        actual_health = player.add_health(int(health_gained), spell_system)
        
        return {
            "spirit_gained": actual_spirit,
            "health_gained": float(actual_health)
        }
    
    @staticmethod
    def process_offline_cultivation(player: 'PlayerData', offline_seconds: int,
                                     inventory_system: 'InventorySystem',
                                     spell_system: 'SpellSystem' = None) -> Dict[str, Any]:
        """
        处理离线修炼
        
        Args:
            player: 玩家数据
            offline_seconds: 离线秒数
            inventory_system: 储纳系统（用于添加灵石）
            spell_system: 术法系统（可选）
        
        Returns:
            {
                "spirit_theoretical": float,
                "spirit_actual": float,
                "spirit_stones_gained": int
            }
        """
        spirit_speed = AttributeCalculator.calculate_spirit_gain_speed(player, spell_system)
        spirit_theoretical = spirit_speed * offline_seconds
        
        actual_spirit = player.add_spirit_energy(spirit_theoretical, spell_system)
        
        spirit_stones = int(offline_seconds / 60)
        if spirit_stones > 0:
            inventory_system.add_item("spirit_stone", spirit_stones)
        
        return {
            "spirit_theoretical": spirit_theoretical,
            "spirit_actual": actual_spirit,
            "spirit_stones_gained": spirit_stones
        }
    
    @staticmethod
    def can_breakthrough(player: 'PlayerData', inventory_system: 'InventorySystem') -> Dict[str, Any]:
        """
        检查是否可以突破
        
        Args:
            player: 玩家数据
            inventory_system: 储纳系统（用于检查材料）
        
        Returns:
            {
                "can": bool,
                "reason": str,
                "breakthrough_info": dict,
                "missing": dict
            }
        """
        breakthrough_info = RealmData.get_breakthrough_info(player.realm, player.realm_level)
        
        if not breakthrough_info["can"]:
            return {
                "can": False,
                "reason": "已达到最高境界或境界信息错误",
                "breakthrough_info": breakthrough_info,
                "missing": {}
            }
        
        missing = {}
        
        if player.spirit_energy < breakthrough_info["spirit_energy_cost"]:
            missing["spirit_energy"] = breakthrough_info["spirit_energy_cost"] - player.spirit_energy
        
        spirit_stone_count = inventory_system.get_item_count("spirit_stone")
        if spirit_stone_count < breakthrough_info["spirit_stone_cost"]:
            missing["spirit_stone"] = breakthrough_info["spirit_stone_cost"] - spirit_stone_count
        
        for item_id, count in breakthrough_info["materials"].items():
            current_count = inventory_system.get_item_count(item_id)
            if current_count < count:
                missing[item_id] = count - current_count
        
        if missing:
            return {
                "can": False,
                "reason": "资源不足",
                "breakthrough_info": breakthrough_info,
                "missing": missing
            }
        
        return {
            "can": True,
            "reason": "可以突破",
            "breakthrough_info": breakthrough_info,
            "missing": {}
        }
    
    @staticmethod
    def execute_breakthrough(player: 'PlayerData', inventory_system: 'InventorySystem') -> Dict[str, Any]:
        """
        执行突破
        
        Args:
            player: 玩家数据
            inventory_system: 储纳系统（用于扣除材料）
        
        Returns:
            {
                "success": bool,
                "new_realm": str,
                "new_level": int,
                "reason": str,
                "costs": dict
            }
        """
        check_result = CultivationSystem.can_breakthrough(player, inventory_system)
        
        if not check_result["can"]:
            return {
                "success": False,
                "new_realm": player.realm,
                "new_level": player.realm_level,
                "reason": check_result["reason"],
                "costs": {}
            }
        
        breakthrough_info = check_result["breakthrough_info"]
        costs = {}
        
        if breakthrough_info["spirit_energy_cost"] > 0:
            actual_cost = player.reduce_spirit_energy(breakthrough_info["spirit_energy_cost"])
            costs["spirit_energy"] = actual_cost
        
        if breakthrough_info["spirit_stone_cost"] > 0:
            removed = inventory_system.remove_item("spirit_stone", breakthrough_info["spirit_stone_cost"])
            if removed > 0:
                costs["spirit_stone"] = removed
        
        for item_id, count in breakthrough_info["materials"].items():
            removed = inventory_system.remove_item(item_id, count)
            if removed > 0:
                costs[item_id] = removed
        
        player.realm = breakthrough_info["next_realm"]
        player.realm_level = breakthrough_info["next_level"]
        player.reload_attributes()
        
        return {
            "success": True,
            "new_realm": player.realm,
            "new_level": player.realm_level,
            "reason": "突破成功",
            "costs": costs
        }
