"""
玩家数据类

负责管理玩家的核心属性：气血和灵气
"""

from typing import TYPE_CHECKING

from .AttributeCalculator import AttributeCalculator

if TYPE_CHECKING:
    from ..spell.SpellSystem import SpellSystem


class PlayerData:
    """
    玩家数据类 - 负责管理玩家的核心属性
    
    存储：
    - 动态数据（存入数据库）：health, spirit_energy, realm, realm_level
    - 计算属性（从境界配置加载，不存数据库）：max_health, max_spirit_energy, speed, 
      health_regen_per_second, spirit_gain_speed, attack, defense
    """
    
    def __init__(self, health: int, spirit_energy: float, realm: str, realm_level: int):
        self.health = health
        self.spirit_energy = spirit_energy
        self.realm = realm
        self.realm_level = realm_level
        
        self.max_health: int = 0
        self.max_spirit_energy: int = 0
        self.speed: float = 0.0
        self.attack: float = 0.0
        self.defense: float = 0.0
        self.health_regen_per_second: float = 0.0
        self.spirit_gain_speed: float = 0.0
        
        self._load_attributes_from_realm()
    
    def _load_attributes_from_realm(self):
        """从境界系统加载属性（内部方法）"""
        from ..cultivation.RealmData import RealmData
        
        attrs = RealmData.get_realm_attributes(self.realm, self.realm_level)
        self.max_health = attrs.get("max_health", 100)
        self.max_spirit_energy = attrs.get("max_spirit_energy", 100)
        self.speed = attrs.get("speed", 7.0)
        self.attack = attrs.get("attack", 10.0)
        self.defense = attrs.get("defense", 5.0)
        self.health_regen_per_second = attrs.get("health_regen_per_second", 1.0)
        self.spirit_gain_speed = attrs.get("spirit_gain_speed", 1.0)
    
    def reload_attributes(self):
        """重新加载属性（境界变化后调用）"""
        self._load_attributes_from_realm()
    
    def add_health(self, amount: int, spell_system: 'SpellSystem' = None) -> int:
        max_hp = AttributeCalculator.calculate_static_max_health(self, spell_system)
        old_health = self.health
        self.health = min(self.health + amount, max_hp)
        return self.health - old_health
    
    def reduce_health(self, amount: int) -> int:
        old_health = self.health
        self.health = max(0, self.health - amount)
        return old_health - self.health
    
    def add_spirit_energy(self, amount: float, spell_system: 'SpellSystem' = None) -> float:
        final_max_spirit = float(AttributeCalculator.calculate_static_max_spirit_energy(self, spell_system))
        
        if self.spirit_energy >= final_max_spirit:
            return 0.0
        
        old_spirit = self.spirit_energy
        self.spirit_energy = min(self.spirit_energy + amount, final_max_spirit)
        return self.spirit_energy - old_spirit
    
    def add_spirit_energy_breakthrough(self, amount: float) -> float:
        old_spirit = self.spirit_energy
        self.spirit_energy = self.spirit_energy + amount
        return self.spirit_energy - old_spirit
    
    def reduce_spirit_energy(self, amount: float) -> float:
        old_spirit = self.spirit_energy
        self.spirit_energy = max(0.0, self.spirit_energy - amount)
        return old_spirit - self.spirit_energy
    
    def to_dict(self) -> dict:
        return {
            "health": self.health,
            "spirit_energy": self.spirit_energy,
            "realm": self.realm,
            "realm_level": self.realm_level
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PlayerData':
        return cls(
            health=data.get("health", 100),
            spirit_energy=float(data.get("spirit_energy", 0.0)),
            realm=data.get("realm", "炼气期"),
            realm_level=data.get("realm_level", 1)
        )
