"""
修炼系统

提供修炼相关的基础功能：
1. 修炼tick处理
2. 离线修炼处理
3. 突破检查
4. 突破执行
"""

from typing import Dict, Any, TYPE_CHECKING

from ..inventory.ItemData import ItemData
from ..player.AttributeCalculator import AttributeCalculator
from .RealmData import RealmData
from ..spell.SpellData import SpellData

if TYPE_CHECKING:
    from ..player.PlayerSystem import PlayerSystem
    from ..spell.SpellSystem import SpellSystem
    from ..inventory.InventorySystem import InventorySystem


class CultivationSystem:
    """
    修炼系统 - 提供修炼相关的基础功能
    
    所有方法都是静态方法，无需实例化
    """
    
    @staticmethod
    def calculate_health_regen_per_second(player: 'PlayerSystem', spell_system: 'SpellSystem' = None) -> float:
        """
        计算每秒气血恢复速度，玩家静态气血恢复速度 + 已装备的吐纳术法加成
        
        修炼时自动恢复气血，这个功能是修炼系统特有的
        
        Args:
            player: 玩家数据
            spell_system: 术法系统（可选，用于获取吐纳术法加成）
        
        Returns:
            每秒气血恢复量
        """
        base_regen = float(player.static_health_regen_per_second)
        
        if spell_system:
            breathing_bonus = spell_system.get_breathing_heal_bonus()
            if breathing_bonus > 0:
                base_regen += float(player.static_max_health) * breathing_bonus
        
        return base_regen
    
    @staticmethod
    def process_cultivation_tick(player: 'PlayerSystem', delta_seconds: float, 
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
        # 计算修炼tick内获得的气血和灵力
        spirit_gained = player.static_spirit_gain_speed * delta_seconds
        health_gained = CultivationSystem.calculate_health_regen_per_second(player, spell_system) * delta_seconds
        
        actual_spirit = player.add_spirit_energy(spirit_gained)
        actual_health = player.add_health(health_gained)
        
        used_count_gained = 0
        # 已装备的第一个吐纳术法，熟练度增加
        if len(spell_system.equipped_spells[SpellData.SPELL_TYPE_BREATHING]) > 0:
            spell_id = spell_system.equipped_spells[SpellData.SPELL_TYPE_BREATHING][0]
            used_count_gained = spell_system.add_spell_use_count(spell_id, round(delta_seconds, 0))
        
        return {
            "spirit_gained": actual_spirit,
            "health_gained": actual_health,
            "used_count_gained": used_count_gained
        }
    
    @staticmethod
    def process_offline_cultivation(player: 'PlayerSystem', offline_seconds: int,
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
        spirit_theoretical = player.static_spirit_gain_speed * offline_seconds
        actual_spirit = player.add_spirit_energy(spirit_theoretical)
        
        spirit_stones = int(offline_seconds / 60)
        if spirit_stones > 0:
            inventory_system.add_item("spirit_stone", spirit_stones)
        
        return {
            "spirit_theoretical": spirit_theoretical,
            "spirit_actual": actual_spirit,
            "spirit_stones_gained": spirit_stones
        }

    @staticmethod
    def _build_breakthrough_missing_reason(missing: Dict[str, Any]) -> str:
        """按旧客户端优先级构造突破失败原因。"""
        material_ids = [item_id for item_id in missing.keys() if item_id not in ("spirit_energy", "spirit_stone")]
        if material_ids:
            return f"{ItemData.get_item_name(str(material_ids[0]))}不足"

        if "spirit_energy" in missing:
            return "灵气不足"

        if "spirit_stone" in missing:
            return "灵石不足"

        return "资源不足"
    
    @staticmethod
    def _can_breakthrough(player: 'PlayerSystem', inventory_system: 'InventorySystem') -> Dict[str, Any]:
        """
        检查是否可以突破
        
        Args:
            player: 玩家数据
            inventory_system: 储纳系统（用于检查材料）
        
        Returns:
            {
                "can": bool,
                "reason_code": str,
                "breakthrough_info": dict,
                "missing": dict
            }
        """
        breakthrough_info = RealmData.get_breakthrough_info(player.realm, player.realm_level)
        
        if not breakthrough_info["can"]:
            return {
                "can": False,
                "reason_code": "CULTIVATION_BREAKTHROUGH_NOT_AVAILABLE",
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
                "reason_code": "CULTIVATION_BREAKTHROUGH_INSUFFICIENT_RESOURCES",
                "breakthrough_info": breakthrough_info,
                "missing": missing
            }
        
        return {
            "can": True,
            "reason_code": "CULTIVATION_BREAKTHROUGH_AVAILABLE",
            "breakthrough_info": breakthrough_info,
            "missing": {}
        }
    
    @staticmethod
    def execute_breakthrough(player: 'PlayerSystem', inventory_system: 'InventorySystem') -> Dict[str, Any]:
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
                "reason_code": str,
                "missing_resources": dict,
                "costs": dict
            }
        """
        check_result = CultivationSystem._can_breakthrough(player, inventory_system)
        
        if not check_result["can"]:
            return {
                "success": False,
                "new_realm": player.realm,
                "new_level": player.realm_level,
                "reason_code": check_result["reason_code"],
                "missing_resources": check_result.get("missing", {}),
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
        
        # 突破后生命恢复满值
        player.health = player.static_max_health
        
        return {
            "success": True,
            "new_realm": player.realm,
            "new_level": player.realm_level,
            "reason_code": "CULTIVATION_BREAKTHROUGH_SUCCEEDED",
            "missing_resources": {},
            "costs": costs
        }
