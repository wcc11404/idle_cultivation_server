"""
属性计算器

负责计算玩家的各种属性

属性分层：
1. 基础属性：境界带来的基础属性（PlayerSystem 中已加载）
2. 静态最终属性：基础属性 + 术法等永久加成
3. 动态最终属性：静态最终属性 + 战斗临时buff
"""

from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..spell.SpellSystem import SpellSystem
    from .PlayerSystem import PlayerSystem


class AttributeCalculator:
    """
    属性计算器 - 负责计算玩家的各种属性
    
    属性分层：
    1. 基础属性：境界带来的基础属性（PlayerSystem 中已加载）
    2. 静态最终属性：基础属性 + 术法等永久加成
    3. 动态最终属性：静态最终属性 + 战斗临时buff
    """
    
    @staticmethod
    def calculate_static_max_health(player: 'PlayerSystem', spell_system: 'SpellSystem' = None) -> float:
        """计算静态最终最大气血"""
        base = float(player.max_health)
        if spell_system:
            bonus = spell_system.get_attribute_bonuses().get("health", 1.0)
            base = base * bonus
        return round(base, 2)
    
    @staticmethod
    def calculate_static_attack(player: 'PlayerSystem', spell_system: 'SpellSystem' = None) -> float:
        """计算静态最终攻击力"""
        base = player.attack
        if spell_system:
            bonus = spell_system.get_attribute_bonuses().get("attack", 1.0)
            return round(base * bonus, 2)
        return round(base, 2)
    
    @staticmethod
    def calculate_static_defense(player: 'PlayerSystem', spell_system: 'SpellSystem' = None) -> float:
        """计算静态最终防御力"""
        base = player.defense
        if spell_system:
            bonus = spell_system.get_attribute_bonuses().get("defense", 1.0)
            return round(base * bonus, 2)
        return round(base, 2)
    
    @staticmethod
    def calculate_static_speed(player: 'PlayerSystem', spell_system: 'SpellSystem' = None) -> float:
        """计算静态最终速度"""
        base = player.speed
        if spell_system:
            bonus = spell_system.get_attribute_bonuses().get("speed", 0.0)
            return round(base + bonus, 2)
        return round(base, 2)
    
    @staticmethod
    def calculate_static_max_spirit_energy(player: 'PlayerSystem', spell_system: 'SpellSystem' = None) -> float:
        """计算静态最终最大灵气"""
        base = float(player.max_spirit_energy)
        if spell_system:
            bonus = spell_system.get_attribute_bonuses().get("max_spirit", 1.0)
            base = base * bonus
        return round(base, 2)
    
    @staticmethod
    def calculate_static_spirit_gain_speed(player: 'PlayerSystem', spell_system: 'SpellSystem' = None) -> float:
        """计算静态最终每秒灵气获取速度"""
        base_speed = player.spirit_gain_speed
        if spell_system:
            spell_bonus = spell_system.get_attribute_bonuses().get("spirit_gain", 1.0)
            return round(base_speed * spell_bonus, 2)
        return round(base_speed, 2)
    
    @staticmethod
    def calculate_static_attributes(player: 'PlayerSystem', spell_system: 'SpellSystem' = None) -> dict:
        """
        计算静态最终属性（汇总）
        
        Args:
            player: 玩家数据
            spell_system: 术法系统（可选）
        
        Returns:
            {
                "max_health": int,
                "attack": float,
                "defense": float,
                "speed": float,
                "max_spirit_energy": int,
                "spirit_gain_speed": float
            }
        """
        return {
            "max_health": AttributeCalculator.calculate_static_max_health(player, spell_system),
            "attack": AttributeCalculator.calculate_static_attack(player, spell_system),
            "defense": AttributeCalculator.calculate_static_defense(player, spell_system),
            "speed": AttributeCalculator.calculate_static_speed(player, spell_system),
            "max_spirit_energy": AttributeCalculator.calculate_static_max_spirit_energy(player, spell_system),
            "spirit_gain_speed": AttributeCalculator.calculate_static_spirit_gain_speed(player, spell_system)
        }
    
    @staticmethod
    def calculate_dynamic_attributes(static_attributes: dict, combat_buffs: dict = None) -> dict:
        """
        计算动态最终属性（战斗中）
        
        Args:
            static_attributes: 静态最终属性
            combat_buffs: 战斗临时buff
        
        Returns:
            {
                "health": float,
                "max_health": float,
                "attack": float,
                "defense": float,
                "speed": float
            }
        """
        if not combat_buffs:
            return static_attributes.copy()
        
        health_bonus = combat_buffs.get("health_bonus", 0.0)
        
        return {
            "health": static_attributes.get("health", static_attributes["max_health"]) + health_bonus,
            "max_health": static_attributes["max_health"] + health_bonus,
            "attack": static_attributes["attack"] * (1.0 + combat_buffs.get("attack_percent", 0.0)),
            "defense": static_attributes["defense"] * (1.0 + combat_buffs.get("defense_percent", 0.0)),
            "speed": static_attributes["speed"] + combat_buffs.get("speed_bonus", 0.0)
        }
    
    @staticmethod
    def calculate_damage(attack: float, defense: float, damage_percent: float = 1.0) -> float:
        """
        计算伤害
        
        Args:
            attack: 攻击力
            defense: 防御力
            damage_percent: 伤害百分比（默认1.0即100%）
        
        Returns:
            最终伤害值
        """
        k_value = 100.0
        penetration = 0.0
        effective_defense = max(defense - penetration, 0.0)
        defense_ratio = effective_defense / max(effective_defense + k_value, k_value)
        base_damage = attack * (1.0 - defense_ratio)
        final_damage = max(base_damage, 1.0) * damage_percent
        return round(final_damage, 2)
    
    @staticmethod
    def format_default(value: float) -> str:
        """默认格式化：保留两位小数，去除尾0"""
        result = f"{value:.2f}"
        while '.' in result and result.endswith('0'):
            result = result[:-1]
        if result.endswith('.'):
            result = result[:-1]
        return result
    
    @staticmethod
    def format_percent(value: float) -> str:
        """百分比格式化：乘100，保留两位小数，去除尾0，加%"""
        percent = value * 100.0
        result = f"{percent:.2f}"
        while '.' in result and result.endswith('0'):
            result = result[:-1]
        if result.endswith('.'):
            result = result[:-1]
        return result + "%"
    
    @staticmethod
    def format_integer(value: float) -> str:
        """保留整数"""
        return str(int(round(value)))
    
    @staticmethod
    def format_damage(value: float) -> str:
        """伤害值格式化：≤1000保留一位小数，>1000保留整数"""
        if value <= 1000.0:
            result = f"{value:.1f}"
            if result.endswith('.0'):
                result = result[:-2]
            return result
        else:
            return str(int(round(value)))
