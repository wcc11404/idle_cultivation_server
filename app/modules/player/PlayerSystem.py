"""
玩家数据类

负责管理玩家的核心属性：气血和灵气
"""

from typing import TYPE_CHECKING

from .AttributeCalculator import AttributeCalculator
from ..cultivation.RealmData import RealmData

if TYPE_CHECKING:
    from ..spell.SpellSystem import SpellSystem


class PlayerSystem:
    """
    玩家数据类 - 负责管理玩家的核心属性
    
    存储：
    - 动态数据（存入数据库）：health, spirit_energy, realm, realm_level
    - 计算属性（从境界配置加载，不存数据库）：max_health, max_spirit_energy, speed, 
      health_regen_per_second, spirit_gain_speed, attack, defense
    """
    
    def __init__(self, health: float, spirit_energy: float, realm: str, realm_level: int, spell_system: 'SpellSystem' = None):
        # 动态数据，会存入数据库
        self.health = health
        self.spirit_energy = spirit_energy
        self.realm = realm
        self.realm_level = realm_level
        self.spell_system = spell_system
        
        # 修炼状态，会存入数据库
        self.is_cultivating: bool = False
        self.last_cultivation_report_time: float = 0.0
        
        # 基础属性，只随境界变化而变化，不存数据库，每次境界变化都会重新计算
        self._load_attributes_from_realm()
        
        # 静态最终属性，根据基础属性和术法等附属系统计算得到，不存数据库，每次境界变化和附属系统变化都会重新计算
        self._load_static_attributes()
    
    def _load_attributes_from_realm(self):
        """从境界系统加载属性（内部方法）"""
        attrs = RealmData.get_realm_attributes(self.realm, self.realm_level)
        self.max_health = attrs.get("max_health", 100)
        self.max_spirit_energy = attrs.get("max_spirit_energy", 100)
        self.speed = attrs.get("speed", 7.0)
        self.attack = attrs.get("attack", 10.0)
        self.defense = attrs.get("defense", 5.0)
        self.health_regen_per_second = attrs.get("health_regen_per_second", 1.0)
        self.spirit_gain_speed = attrs.get("spirit_gain_speed", 1.0)
        
    def _load_static_attributes(self):
        """根据所有附属系统带来的增益，计算最终静态属性（内部方法）"""
        self.static_max_health = AttributeCalculator.calculate_static_max_health(self, self.spell_system)
        self.static_max_spirit_energy = AttributeCalculator.calculate_static_max_spirit_energy(self, self.spell_system)
        self.static_speed = AttributeCalculator.calculate_static_speed(self, self.spell_system)
        self.static_attack = AttributeCalculator.calculate_static_attack(self, self.spell_system)
        self.static_defense = AttributeCalculator.calculate_static_defense(self, self.spell_system)
        self.static_health_regen_per_second = self.health_regen_per_second
        self.static_spirit_gain_speed = AttributeCalculator.calculate_static_spirit_gain_speed(self, self.spell_system)
    
    def get_battle_attributes(self):
        """获取一个战斗属性字典，包含当前气血、最大气血、速度、攻击、防御"""
        return {
            "health": self.health,
            "max_health": self.static_max_health,
            "speed": self.static_speed,
            "attack": self.static_attack,
            "defense": self.static_defense
        }
        
    def reload_attributes(self):
        """重新加载属性（境界变化后或者附属系统增益有变化后调用）"""
        # 基础属性，只随境界变化而变化，不存数据库，每次境界变化都会重新计算
        self._load_attributes_from_realm()
        # 静态最终属性，根据基础属性和术法等附属系统计算得到，不存数据库，每次境界变化和附属系统变化都会重新计算
        self._load_static_attributes()
    
    def add_health(self, amount: float) -> float:
        """添加气血"""
        old_health = self.health
        self.health = round(min(self.health + amount, self.static_max_health), 2)
        return round(self.health - old_health, 2)
    
    def reduce_health(self, amount: float) -> float:
        """减少气血"""
        old_health = self.health
        self.health = round(max(0.0, self.health - amount), 2)
        return round(old_health - self.health, 2)
    
    def add_spirit_energy(self, amount: float) -> float:
        """添加灵气（不可突破最大灵气上限）"""
        if self.spirit_energy >= self.static_max_spirit_energy:
            return 0.0
        old_spirit = self.spirit_energy
        self.spirit_energy = round(min(self.spirit_energy + amount, self.static_max_spirit_energy), 2)
        return round(self.spirit_energy - old_spirit, 2)
    
    def add_spirit_energy_breakthrough(self, amount: float) -> float:
        """添加灵气（可突破最大灵气上限）"""
        old_spirit = self.spirit_energy
        self.spirit_energy = round(self.spirit_energy + amount, 2)
        return round(self.spirit_energy - old_spirit, 2)
    
    def reduce_spirit_energy(self, amount: float) -> float:
        """减少灵气"""
        old_spirit = self.spirit_energy
        self.spirit_energy = round(max(0.0, self.spirit_energy - amount), 2)
        return round(old_spirit - self.spirit_energy, 2)
    
    def set_health(self, health: float):
        """设置气血（不超过静态生命最大上限）"""
        self.health = round(min(health, self.static_max_health), 2)
    
    def reset_cultivation_state(self):
        """重置修炼状态"""
        self.is_cultivating = False
        self.last_cultivation_report_time = 0.0
    
    def to_dict(self) -> dict:
        return {
            "health": self.health,
            "spirit_energy": self.spirit_energy,
            "realm": self.realm,
            "realm_level": self.realm_level,
            "is_cultivating": self.is_cultivating,
            "last_cultivation_report_time": self.last_cultivation_report_time
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PlayerSystem':
        instance = cls(
            health=float(data.get("health", 100.0)),
            spirit_energy=float(data.get("spirit_energy", 0.0)),
            realm=data.get("realm", "炼气期"),
            realm_level=data.get("realm_level", 1)
        )
        instance.is_cultivating = data.get("is_cultivating", False)
        instance.last_cultivation_report_time = data.get("last_cultivation_report_time", 0.0)
        return instance
