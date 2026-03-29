"""
历练系统

负责管理玩家的历练功能，包括战斗、掉落、无尽塔等

区域类型：
1. 普通区域：无限制，持续战斗
2. 特殊区域：每日次数限制
3. 每日区域：每日重置次数

战斗细节：
- 服务器负责模拟战斗
- 记录战斗过程中的所有细节
- 返回给客户端用于播放动画
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
import random

from ..player.AttributeCalculator import AttributeCalculator
from .LianliData import LianliData

if TYPE_CHECKING:
    from ..player.PlayerData import PlayerData
    from ..spell.SpellSystem import SpellSystem
    from ..inventory.InventorySystem import InventorySystem


class LianliSystem:
    """
    历练系统
    
    区域类型：
    1. 普通区域：无限制，持续战斗
    2. 特殊区域：每日次数限制
    3. 每日区域：每日重置次数
    
    战斗细节：
    - 服务器负责模拟战斗
    - 记录战斗过程中的所有细节
    - 返回给客户端用于播放动画
    """
    
    ATB_MAX = 100.0
    TICK_INTERVAL = 0.1
    DEFAULT_ENEMY_ATTACK = 50.0
    PERCENTAGE_BASE = 100.0
    
    def __init__(self, spell_system: 'SpellSystem', inventory_system: 'InventorySystem'):
        """
        初始化历练系统
        
        Args:
            spell_system: 术法系统
            inventory_system: 背包系统
        """
        self.spell_system = spell_system
        self.inventory_system = inventory_system
        
        self.tower_highest_floor: int = 0
        self.daily_dungeon_data: Dict[str, Dict] = {}
    
    def _get_areas_config(self) -> dict:
        """获取区域配置"""
        return LianliData.get_areas_config()
    
    def _get_enemies_config(self) -> dict:
        """获取敌人配置"""
        return LianliData.get_enemies_config()
    
    def is_normal_area(self, area_id: str) -> bool:
        """判断是否为普通区域"""
        area_config = LianliData.get_area_info(area_id)
        return area_config.get("type", "normal") == "normal"
    
    def is_special_area(self, area_id: str) -> bool:
        """判断是否为特殊区域（每日限制）"""
        area_config = LianliData.get_area_info(area_id)
        return area_config.get("type", "normal") == "special"
    
    def is_daily_dungeon(self, area_id: str) -> bool:
        """判断是否为每日副本"""
        area_config = LianliData.get_area_info(area_id)
        return area_config.get("type", "normal") == "daily"
    
    def is_single_boss_area(self, area_id: str) -> bool:
        """判断是否为单BOSS区域"""
        area_config = LianliData.get_area_info(area_id)
        return area_config.get("is_single_boss", False)
    
    def get_daily_dungeon_count(self, area_id: str) -> int:
        """获取每日副本次数"""
        if area_id not in self.daily_dungeon_data:
            area_config = LianliData.get_area_info(area_id)
            max_count = area_config.get("daily_count", 3)
            self.daily_dungeon_data[area_id] = {
                "max_count": max_count,
                "remaining_count": max_count
            }
        return self.daily_dungeon_data[area_id].get("remaining_count", 3)
    
    def use_daily_dungeon_count(self, area_id: str):
        """使用每日副本次数"""
        if area_id not in self.daily_dungeon_data:
            area_config = LianliData.get_area_info(area_id)
            max_count = area_config.get("daily_count", 3)
            self.daily_dungeon_data[area_id] = {
                "max_count": max_count,
                "remaining_count": max_count
            }
        
        self.daily_dungeon_data[area_id]["remaining_count"] = max(
            0, 
            self.daily_dungeon_data[area_id]["remaining_count"] - 1
        )
    
    def reset_daily_dungeons(self):
        """重置每日副本次数"""
        areas_config = self._get_areas_config()
        for area_id in self.daily_dungeon_data:
            area_config = LianliData.get_area_info(area_id)
            max_count = area_config.get("daily_count", 3)
            self.daily_dungeon_data[area_id]["remaining_count"] = max_count
    
    def generate_enemy(self, area_id: str, floor: int = None) -> Dict[str, Any]:
        """
        生成敌人
        
        Args:
            area_id: 区域 ID
            floor: 无尽塔层数（可选）
        
        Returns:
            敌人数据
        """
        area_config = LianliData.get_area_info(area_id)
        
        if floor is not None:
            template_id = self._get_random_tower_template()
            enemy_level = floor
        else:
            enemies = area_config.get("enemies", [])
            if not enemies:
                return {}
            
            enemy_config = random.choice(enemies)
            template_id = enemy_config.get("template")
            min_level = enemy_config.get("min_level", 1)
            max_level = enemy_config.get("max_level", 1)
            enemy_level = random.randint(min_level, max_level)
        
        return self._generate_enemy_from_template(template_id, enemy_level)
    
    def _get_random_tower_template(self) -> str:
        """获取随机无尽塔敌人模板"""
        enemies_config = self._get_enemies_config()
        tower_enemies = [eid for eid, econfig in enemies_config.items() 
                        if econfig.get("can_appear_in_tower", False)]
        if tower_enemies:
            return random.choice(tower_enemies)
        return list(enemies_config.keys())[0] if enemies_config else ""
    
    def _generate_enemy_from_template(self, template_id: str, level: int) -> Dict[str, Any]:
        """从模板生成敌人"""
        template = LianliData.get_enemy_template(template_id)
        
        if not template:
            return {}
        
        level_multiplier = 1.0 + (level - 1) * 0.1
        
        enemy_data = {
            "id": template_id,
            "name": template.get("name", "未知敌人"),
            "level": level,
            "health": int(template.get("health", 100) * level_multiplier),
            "attack": template.get("attack", 10) * level_multiplier,
            "defense": template.get("defense", 5) * level_multiplier,
            "speed": template.get("speed", 7),
            "drops": template.get("drops", {}),
            "is_elite": template.get("is_elite", False)
        }
        
        return enemy_data
    
    def _get_player_combat_attributes(self, player_data: 'PlayerData', combat_buffs: dict = None) -> dict:
        """
        获取玩家战斗属性
        
        Args:
            player_data: 玩家数据（已加载境界属性）
            combat_buffs: 战斗临时buff
        
        Returns:
            战斗属性字典
        """
        spell_bonuses = self.spell_system.get_attribute_bonuses() if self.spell_system else {}
        
        max_health = int(player_data.max_health * spell_bonuses.get("health", 1.0))
        attack = player_data.attack * spell_bonuses.get("attack", 1.0)
        defense = player_data.defense * spell_bonuses.get("defense", 1.0)
        speed = player_data.speed + spell_bonuses.get("speed", 0.0)
        
        if combat_buffs:
            max_health = int(max_health * (1.0 + combat_buffs.get("health_percent", 0.0)))
            attack = attack * (1.0 + combat_buffs.get("attack_percent", 0.0))
            defense = defense * (1.0 + combat_buffs.get("defense_percent", 0.0))
            speed = speed + combat_buffs.get("speed_bonus", 0.0)
        
        return {
            "max_health": max_health,
            "attack": attack,
            "defense": defense,
            "speed": speed
        }
    
    def execute_battle(self, player_data: 'PlayerData', enemy_data: dict, 
                      combat_buffs: dict = None) -> Dict[str, Any]:
        """
        执行战斗（服务端权威）
        
        Args:
            player_data: 玩家数据（需先调用 load_attributes_from_realm）
            enemy_data: 敌人数据
            combat_buffs: 战斗临时buff
        
        Returns:
            {
                "victory": bool,
                "battle_timeline": [...],
                "total_time": 10.5,
                "loot": [...],
                "player_health_after": 50,
                "enemy_health_after": 0
            }
        """
        if combat_buffs is None:
            combat_buffs = {}
        
        if player_data.health <= 0:
            return {
                "victory": False,
                "reason": "气血不足，无法战斗",
                "battle_timeline": [],
                "total_time": 0.0,
                "loot": [],
                "player_health_after": player_data.health,
                "enemy_health_after": enemy_data.get("health", 0)
            }
        
        combat_attrs = self._get_player_combat_attributes(player_data, combat_buffs)
        
        player_atb = 0.0
        enemy_atb = 0.0
        player_health = float(player_data.health)
        player_max_health = float(combat_attrs["max_health"])
        enemy_health = float(enemy_data.get("health", 100))
        enemy_max_health = enemy_health
        
        battle_timeline = []
        current_time = 0.0
        
        while True:
            current_time += self.TICK_INTERVAL
            
            player_atb += combat_attrs["speed"] * self.TICK_INTERVAL
            enemy_atb += enemy_data.get("speed", 7) * self.TICK_INTERVAL
            
            player_ready = player_atb >= self.ATB_MAX
            enemy_ready = enemy_atb >= self.ATB_MAX
            
            if player_ready and enemy_ready:
                if combat_attrs["speed"] > enemy_data.get("speed", 7):
                    player_atb, enemy_health, battle_timeline = self._player_action(
                        current_time, player_atb, enemy_health,
                        combat_attrs, enemy_data, battle_timeline
                    )
                    if enemy_health <= 0:
                        break
                    
                    enemy_atb, player_health, battle_timeline = self._enemy_action(
                        current_time, enemy_atb, player_health,
                        enemy_data, combat_attrs, battle_timeline
                    )
                else:
                    enemy_atb, player_health, battle_timeline = self._enemy_action(
                        current_time, enemy_atb, player_health,
                        enemy_data, combat_attrs, battle_timeline
                    )
                    if player_health <= 0:
                        break
                    
                    player_atb, enemy_health, battle_timeline = self._player_action(
                        current_time, player_atb, enemy_health,
                        combat_attrs, enemy_data, battle_timeline
                    )
            elif player_ready:
                player_atb, enemy_health, battle_timeline = self._player_action(
                    current_time, player_atb, enemy_health,
                    combat_attrs, enemy_data, battle_timeline
                )
            elif enemy_ready:
                enemy_atb, player_health, battle_timeline = self._enemy_action(
                    current_time, enemy_atb, player_health,
                    enemy_data, combat_attrs, battle_timeline
                )
            
            if player_health <= 0 or enemy_health <= 0:
                break
        
        victory = enemy_health <= 0 and player_health > 0
        
        loot = []
        if victory:
            loot = self._calculate_loot(enemy_data)
            for loot_item in loot:
                self.inventory_system.add_item(loot_item["item_id"], loot_item["amount"])
        
        player_data.health = int(player_health)
        
        return {
            "victory": victory,
            "battle_timeline": battle_timeline,
            "total_time": round(current_time, 2),
            "loot": loot,
            "player_health_after": player_data.health,
            "enemy_health_after": max(0, int(enemy_health))
        }
    
    def _player_action(self, current_time: float, player_atb: float, enemy_health: float,
                       combat_attrs: dict, enemy_data: dict, battle_timeline: list) -> tuple:
        """玩家攻击行动"""
        attack = combat_attrs["attack"]
        defense = enemy_data.get("defense", 0)
        
        spell_result = self.spell_system.trigger_attack_spell() if self.spell_system else None
        skill_name = "普通攻击"
        damage_percent = 100.0
        
        if spell_result and spell_result.get("triggered", False):
            skill_name = spell_result.get("spell_name", "术法")
            damage_percent = spell_result.get("damage_percent", 100.0)
        
        damage = AttributeCalculator.calculate_damage(attack, defense, damage_percent)
        enemy_health = max(0.0, enemy_health - damage)
        
        battle_timeline.append({
            "time": round(current_time, 2),
            "type": "player_attack",
            "skill": skill_name,
            "damage": round(damage, 2),
            "enemy_health_after": round(enemy_health, 2)
        })
        
        return player_atb - self.ATB_MAX, enemy_health, battle_timeline
    
    def _enemy_action(self, current_time: float, enemy_atb: float, player_health: float,
                      enemy_data: dict, combat_attrs: dict, battle_timeline: list) -> tuple:
        """敌人攻击行动"""
        attack = enemy_data.get("attack", self.DEFAULT_ENEMY_ATTACK)
        defense = combat_attrs["defense"]
        
        damage = AttributeCalculator.calculate_damage(attack, defense)
        player_health = max(0.0, player_health - damage)
        
        battle_timeline.append({
            "time": round(current_time, 2),
            "type": "enemy_attack",
            "skill": "普通攻击",
            "damage": round(damage, 2),
            "player_health_after": round(player_health, 2)
        })
        
        return enemy_atb - self.ATB_MAX, player_health, battle_timeline
    
    def _calculate_loot(self, enemy_data: dict) -> List[Dict[str, Any]]:
        """计算掉落"""
        loot = []
        drops = enemy_data.get("drops", {})
        
        for item_id, drop_info in drops.items():
            chance = drop_info.get("chance", 1.0)
            if random.random() <= chance:
                min_amount = drop_info.get("min", 0)
                max_amount = drop_info.get("max", 0)
                amount = random.randint(min_amount, max_amount)
                if amount > 0:
                    loot.append({
                        "item_id": item_id,
                        "amount": amount
                    })
        
        return loot
    
    def finish_tower_battle(self, floor: int, victory: bool):
        """完成无尽塔战斗"""
        if victory and floor > self.tower_highest_floor:
            self.tower_highest_floor = floor
    
    def to_db_data(self) -> dict:
        """转换为数据库存储格式"""
        return {
            "tower_highest_floor": self.tower_highest_floor,
            "daily_dungeon_data": self.daily_dungeon_data
        }
    
    @classmethod
    def from_db_data(cls, db_data: dict, 
                     spell_system: 'SpellSystem', inventory_system: 'InventorySystem') -> 'LianliSystem':
        """从数据库数据创建"""
        instance = cls(spell_system, inventory_system)
        instance.tower_highest_floor = db_data.get("tower_highest_floor", 0)
        instance.daily_dungeon_data = db_data.get("daily_dungeon_data", {})
        return instance
