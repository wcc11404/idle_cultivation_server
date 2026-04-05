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
import time

from ..player.AttributeCalculator import AttributeCalculator
from .AreasData import AreasData
from .EnemiesData import EnemiesData

if TYPE_CHECKING:
    from ..player.PlayerSystem import PlayerSystem
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
    PERCENTAGE_BASE = 100.0
    
    def __init__(self):
        """
        初始化历练系统
        """
        self.tower_highest_floor: int = 0
        self.daily_dungeon_data: Dict[str, Dict] = {}
        
        self.is_battling: bool = False
        self.battle_start_time: Optional[float] = None
        self.current_battle_data: Optional[Dict[str, Any]] = None
        
        daily_area_ids = AreasData.get_daily_area_ids()
        for area_id in daily_area_ids:
            area_config = AreasData.get_area_info(area_id)
            max_count = area_config.get("daily_count", 3)
            self.daily_dungeon_data[area_id] = {
                "max_count": max_count,
                "remaining_count": max_count
            }
    
    def get_daily_dungeon_count(self, area_id: str) -> int:
        """获取每日副本次数"""
        if area_id not in self.daily_dungeon_data:
            area_config = AreasData.get_area_info(area_id)
            max_count = area_config.get("daily_count", 3)
            self.daily_dungeon_data[area_id] = {
                "max_count": max_count,
                "remaining_count": max_count
            }
        return self.daily_dungeon_data[area_id].get("remaining_count", 3)
    
    def use_daily_dungeon_count(self, area_id: str):
        """使用每日副本次数"""
        if area_id not in self.daily_dungeon_data:
            area_config = AreasData.get_area_info(area_id)
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
        for area_id in self.daily_dungeon_data:
            area_config = AreasData.get_area_info(area_id)
            max_count = area_config.get("daily_count", 3)
            self.daily_dungeon_data[area_id]["remaining_count"] = max_count
    
    def generate_enemy(self, area_id: str) -> Dict[str, Any]:
        """
        生成敌人
        
        Args:
            area_id: 区域 ID
        
        Returns:
            敌人数据
        """
        is_tower = AreasData.is_tower_area(area_id)
        
        if is_tower:
            template_id = AreasData.get_tower_random_template()
            enemy_level = self.tower_highest_floor + 1
            drops = {}
        else:
            enemy_config = AreasData.get_random_enemy_config(area_id)
            if not enemy_config:
                return {}
            
            enemies = enemy_config.get("enemies", [])
            if not enemies:
                return {}
            
            enemy = enemies[0]
            template_id = enemy.get("template", "")
            min_level = enemy.get("min_level", 1)
            max_level = enemy.get("max_level", 1)
            enemy_level = random.randint(min_level, max_level)
            drops = enemy_config.get("drops", {})
        
        generated_enemy = EnemiesData.generate_enemy(template_id, enemy_level)
        if not generated_enemy:
            return {}
        
        stats = generated_enemy.get("stats", {})
        
        enemy_data = {
            "template_id": template_id,
            "name": generated_enemy.get("name", "敌人"),
            "level": enemy_level,
            "health": stats.get("health", 1000),
            "attack": stats.get("attack", 50.0),
            "defense": stats.get("defense", 0),
            "speed": stats.get("speed", 9),
            "drops": drops
        }
        
        return enemy_data
    
    def calculate_loot(self, enemy_data: Dict[str, Any], area_id: str = None) -> List[Dict[str, Any]]:
        """
        计算掉落（外层函数）
        
        Args:
            enemy_data: 敌人数据
            area_id: 区域 ID
        
        Returns:
            掉落列表
        """
        loot = []
        
        # 标准区域的掉落配置都是在 enemys 的drop字段下
        drops_config = enemy_data.get("drops", {})
        for item_id in drops_config.keys():
            drop_info = drops_config[item_id]
            chance = drop_info.get("chance", 1.0)
            if random.random() <= chance:
                min_amount = drop_info.get("min", 0)
                max_amount = drop_info.get("max", 0)
                amount = random.randint(min_amount, max_amount)
                if amount > 0:
                    loot.append({"item_id": item_id, "amount": amount})
        
        # 无尽塔的奖励需要通过特定逻辑计算
        if area_id and AreasData.is_tower_area(area_id):
            current_floor = self.tower_highest_floor + 1
            if AreasData.is_tower_reward_floor(current_floor):
                tower_rewards = AreasData.get_tower_reward_for_floor(current_floor)
                for item_id in tower_rewards.keys():
                    amount = tower_rewards[item_id]
                    loot.append({"item_id": item_id, "amount": amount})
        
        return loot

    def finish_battle(self, speed: float, index: Optional[int], 
                      player_data: 'PlayerSystem',
                      spell_system: Optional['SpellSystem'] = None,
                      inventory_system: Optional['InventorySystem'] = None) -> Dict[str, Any]:
        """
        结算战斗（更新数据库）
        
        Args:
            speed: 播放倍速
            index: 战斗进度索引（None表示完整结算）
            player_data: 玩家数据
            spell_system: 术法系统
            inventory_system: 背包系统
        
        Returns:
            结算结果
        """
        if not self.is_battling or not self.current_battle_data:
            return {
                "success": False,
                "reason": "当前未在战斗状态",
                "settled_index": 0,
                "total_index": 0,
                "player_health_after": player_data.health,
                "loot_gained": [],
                "exp_gained": 0
            }
        
        current_time = time.time()
        
        battle_data = self.current_battle_data
        battle_timeline = battle_data["battle_timeline"]
        total_index = len(battle_timeline)
        
        if index is None or index >= total_index:
            index = total_index - 1
        
        if index < 0:
            index = 0
        
        battle_time_at_index = battle_timeline[index]["time"] if index < total_index else battle_data["total_time"]
        expected_time = battle_time_at_index / speed
        actual_time = current_time - self.battle_start_time
        
        if actual_time < expected_time * 0.9:
            return {
                "success": False,
                "reason": f"战斗结算异常：时间验证失败，实际用时{actual_time:.1f}秒，最小需要{expected_time * 0.9:.1f}秒",
                "settled_index": 0,
                "total_index": total_index,
                "player_health_after": player_data.health,
                "loot_gained": [],
                "exp_gained": 0
            }
        
        player_health_after = battle_data["player_health_before"]
        spells_used = []
        
        for i in range(min(index + 1, total_index)):
            action = battle_timeline[i]
            if action["type"] == "player_action":
                info = action.get("info", {})
                spell_id = info.get("spell_id", "")
                if spell_id and spell_id != "norm_attack":
                    spells_used.append(spell_id)
                
                if info.get("effect_type") == "instant_damage":
                    pass
                elif info.get("effect_type") == "heal":
                    # TODO: 实现治疗逻辑
                    # heal_amount = info.get("heal", 0)
                    # player_health_after = round(min(player_data.static_max_health, player_health_after + heal_amount), 2)
                    pass
        
        for i in range(min(index + 1, total_index)):
            action = battle_timeline[i]
            if action["type"] == "enemy_action":
                info = action.get("info", {})
                damage = info.get("damage", 0)
                player_health_after = round(max(0, player_health_after - damage), 2)
        
        player_data.set_health(player_health_after)
        
        if spell_system:
            for spell_id in spells_used:
                spell_system.add_spell_use_count(spell_id)
        
        loot_gained = []
        is_full_settlement = (index >= total_index - 1)
        
        if is_full_settlement and battle_data["victory"]:
            loot_gained = battle_data["loot"]
            if inventory_system:
                for loot_item in loot_gained:
                    inventory_system.add_item(loot_item["item_id"], loot_item["amount"])
            
            area_id = battle_data["area_id"]
            if AreasData.is_daily_area(area_id):
                self.use_daily_dungeon_count(area_id)
            
            if AreasData.is_tower_area(area_id):
                current_floor = self.tower_highest_floor + 1
                self.finish_tower_battle(current_floor, battle_data["victory"])
        
        self.is_battling = False
        self.battle_start_time = None
        self.current_battle_data = None
        
        return {
            "success": True,
            "reason": "",
            "settled_index": index + 1,
            "total_index": total_index,
            "player_health_after": player_health_after,
            "loot_gained": loot_gained,
            "exp_gained": 0,
            "message": "战斗结算成功" if is_full_settlement else "战斗部分结算成功"
        }
    
    def can_start_battle(self, area_id: str, player_data: 'PlayerSystem') -> Dict[str, Any]:
        """
        判断是否可以开始战斗
        
        Args:
            area_id: 区域 ID
            player_data: 玩家数据
        
        Returns:
            {
                "can_start": bool,
                "reason": str
            }
        """
        if player_data.health <= 0:
            return {
                "can_start": False,
                "reason": "气血不足，无法战斗"
            }
        
        if area_id == AreasData.get_tower_area_id():
            max_floor = AreasData.get_tower_max_floor()
            if self.tower_highest_floor >= max_floor:
                return {
                    "can_start": False,
                    "reason": "已达无尽塔最高层"
                }
        
        if AreasData.is_daily_area(area_id):
            count = self.get_daily_dungeon_count(area_id)
            if count <= 0:
                return {
                    "can_start": False,
                    "reason": "今日副本次数已用完"
                }
        
        return {
            "can_start": True,
            "reason": ""
        }
    
    def start_battle_simulation(self, area_id: str,
                                 player_data: 'PlayerSystem',
                                 spell_system: Optional['SpellSystem'] = None) -> Dict[str, Any]:
        """
        开始战斗模拟（不更新数据库）
        
        Args:
            area_id: 区域 ID
            player_data: 玩家数据
            spell_system: 术法系统
        
        Returns:
            完整的战斗模拟结果
        """
        check_result = self.can_start_battle(area_id, player_data)
        if not check_result["can_start"]:
            return {
                "success": False,
                "reason": check_result["reason"],
                "battle_timeline": [],
                "total_time": 0.0,
                "loot": [],
                "player_health_before": player_data.health,
                "player_health_after": player_data.health,
                "enemy_health_after": 0
            }
        
        enemy_data = self.generate_enemy(area_id)
        
        battle_result = self.execute_battle(
            player_data, enemy_data, spell_system
        )
        
        loot = []
        if battle_result["victory"]:
            loot = self.calculate_loot(enemy_data, area_id)
        
        current_time = time.time()
        
        self.is_battling = True
        self.battle_start_time = current_time
        self.current_battle_data = {
            "area_id": area_id,
            "enemy_data": enemy_data,
            "battle_timeline": battle_result["battle_timeline"],
            "total_time": battle_result["total_time"],
            "player_health_before": player_data.health,
            "player_health_after": battle_result["player_health_after"],
            "enemy_health_after": battle_result["enemy_health_after"],
            "victory": battle_result["victory"],
            "loot": loot
        }
        
        return {
            "success": True,
            "battle_timeline": battle_result["battle_timeline"],
            "total_time": battle_result["total_time"],
            "player_health_before": player_data.health,
            "player_health_after": battle_result["player_health_after"],
            "enemy_health_after": battle_result["enemy_health_after"],
            "enemy_data": enemy_data,
            "victory": battle_result["victory"],
            "loot": loot,
            "reason": ""
        }
    
    def execute_battle(self, player_data: 'PlayerSystem', enemy_data: dict, 
                      spell_system: Optional['SpellSystem']) -> Dict[str, Any]:
        """
        执行战斗（只处理战斗部分）
        
        Args:
            player_data: 玩家数据
            enemy_data: 敌人数据
            spell_system: 术法系统
        
        Returns:
            {
                "victory": bool,
                "battle_timeline": [...],
                "total_time": 10.5,
                "player_health_after": 50,
                "enemy_health_after": 0
            }
        """
        # 初始化战斗属性
        player_atb = 0.0
        player_attributes = player_data.get_battle_attributes()
        # combat_buffs = {
        #     "attack_percent": 0.0,
        #     "defense_percent": 0.0,
        #     "speed_bonus": 0.0,
        #     "health_bonus": 0.0
        # }
        
        enemy_atb = 0.0
        enemy_attributes = {
            "health": float(enemy_data.get("health", 100)),
            "max_health": float(enemy_data.get("max_health", enemy_data.get("health", 100))),
            "speed": enemy_data.get("speed", 7),
            "attack": enemy_data.get("attack", 10),
            "defense": enemy_data.get("defense", 5)
        }
        enemy_name = enemy_data.get("name", "敌人")
     
        battle_timeline = []
        current_time = 0.0
        
        # 触发开局术法
        if spell_system:
            battle_timeline = self._opening_action(
                spell_system, player_attributes, battle_timeline
            )
        # 计算动态属性
        # player_attributes = AttributeCalculator.calculate_dynamic_attributes(player_attributes, combat_buffs)
        
        # 战斗循环
        while True:
            # 推进时间和atb行动值
            current_time += self.TICK_INTERVAL
            
            player_atb += player_attributes["speed"]
            enemy_atb += enemy_attributes["speed"]
            
            player_ready = player_atb >= self.ATB_MAX
            enemy_ready = enemy_atb >= self.ATB_MAX
            
            # 判断玩家和敌人是否准备就绪
            # 如果都准备就绪，根据速度判断行动顺序
            if player_ready and enemy_ready:
                if player_attributes["speed"] > enemy_attributes["speed"]:
                    player_atb, battle_timeline = self._player_action(
                        current_time, player_atb, player_attributes, enemy_attributes, 
                        battle_timeline, spell_system
                    )
                    if enemy_attributes["health"] <= 0:
                        break
                    
                    enemy_atb, battle_timeline = self._enemy_action(
                        current_time, enemy_atb, player_attributes, enemy_attributes, battle_timeline, enemy_name
                    )
                else:
                    enemy_atb, battle_timeline = self._enemy_action(
                        current_time, enemy_atb, player_attributes, enemy_attributes, battle_timeline, enemy_name
                    )
                    if player_attributes["health"] <= 0:
                        break
                    
                    player_atb, battle_timeline = self._player_action(
                        current_time, player_atb, player_attributes, enemy_attributes, 
                        battle_timeline, spell_system
                    )
            elif player_ready:
                player_atb, battle_timeline = self._player_action(
                    current_time, player_atb, player_attributes, enemy_attributes, 
                    battle_timeline, spell_system
                )
            elif enemy_ready:
                enemy_atb, battle_timeline = self._enemy_action(
                    current_time, enemy_atb, player_attributes, enemy_attributes, battle_timeline, enemy_name
                )
            
            # 检查战斗是否结束
            # 如果玩家或敌人气血为0，战斗结束
            if player_attributes["health"] <= 0 or enemy_attributes["health"] <= 0:
                break
        
        # 检查战斗结果
        victory = enemy_attributes["health"] <= 0 and player_attributes["health"] > 0
        
        # 单独处理气血buff导致的玩家气血变化可能超过静态最大气血的情况
        # if combat_buffs.get("health_bonus", 0.0) > 0:
            # player_attributes["health"] = min(player_data.static_max_health, player_attributes["health"])
        
        return {
            "victory": victory,
            "battle_timeline": battle_timeline,
            "total_time": round(current_time, 2),
            "player_health_after": player_attributes["health"],
            "enemy_health_after": enemy_attributes["health"]
        }
    
    def _opening_action(self, spell_system: 'SpellSystem', 
                              player_attributes: dict, battle_timeline: List) -> List[Dict[str, Any]]:
        """
        触发战斗开始时的被动术法
        
        Args:
            player_data: 玩家数据
            spell_system: 术法系统
            combat_buffs: 战斗buff
            static_max_health: 玩家静态最大气血
        
        Returns:
            战斗时间线事件列表
        """
        if not spell_system:
            return battle_timeline
        
        opening_spells = spell_system.trigger_opening_spell()
        
        for spell in opening_spells:
            spell_use_result = spell_system.use_spell(spell["spell_id"], player_attributes)
            
            battle_timeline.append({
                "time": 0.0,
                "type": "player_action",
                "info": spell_use_result["log"]
            })
        
        return battle_timeline
    
    def _player_action(self, current_time: float, player_atb: float, 
                       player_attributes: dict, enemy_attributes: dict, 
                       battle_timeline: list,
                       spell_system: Optional['SpellSystem'] = None) -> tuple:
        """玩家攻击行动"""
        spell_id = ""
        
        if spell_system:
            # 触发主动术法
            active_spell_result = spell_system.trigger_active_spell()
            if active_spell_result.get("triggered", False):
                spell_id = active_spell_result.get("spell_id", "")
                # 使用术法
                spell_use_result = spell_system.use_spell(spell_id, player_attributes, enemy_attributes)
                if spell_use_result.get("used", False):
                    battle_timeline.append({
                        "time": round(current_time, 2),
                        "type": "player_action",
                        "info": spell_use_result["log"]
                    })
                else:
                    # 术法使用失败，使用普通攻击
                    spell_id = ""
        
        if not spell_id:
            # 普通攻击
            damage = AttributeCalculator.calculate_damage(
                player_attributes["attack"], enemy_attributes["defense"]
            )
            enemy_attributes["health"] = round(max(0.0, enemy_attributes["health"] - damage), 2)
            battle_timeline.append({
                "time": round(current_time, 2),
                "type": "player_action",
                "info": {
                    "spell_id": "norm_attack",
                    "effect_type": "instant_damage",
                    "damage": round(damage, 2),
                    "target_health_after": round(enemy_attributes["health"], 2)
                }
            })
        
        return player_atb - self.ATB_MAX, battle_timeline
    
    def _enemy_action(self, current_time: float, enemy_atb: float,
                      player_attributes: dict, enemy_attributes: dict, 
                      battle_timeline: list, enemy_name: str = "敌人") -> tuple:
        """敌人攻击行动"""
        attack = enemy_attributes["attack"]
        defense = player_attributes["defense"]
        
        damage = AttributeCalculator.calculate_damage(attack, defense)
        player_attributes["health"] = round(max(0.0, player_attributes["health"] - damage), 2)
        
        battle_timeline.append({
            "time": round(current_time, 2),
            "type": "enemy_action",
            "info": {
                "enemy_name": enemy_name,
                "spell_id": "norm_attack",
                "damage": round(damage, 2),
                "target_health_after": round(player_attributes["health"], 2)
            }
        })
        
        return enemy_atb - self.ATB_MAX, battle_timeline
    
    def finish_tower_battle(self, floor: int, victory: bool):
        """完成无尽塔战斗"""
        if victory and floor > self.tower_highest_floor:
            self.tower_highest_floor = floor
    
    def reset_battle_state(self):
        """重置战斗状态"""
        self.is_battling = False
        self.battle_start_time = None
        self.current_battle_data = None
    
    def to_dict(self) -> dict:
        """转换为数据库存储格式"""
        return {
            "tower_highest_floor": self.tower_highest_floor,
            "daily_dungeon_data": self.daily_dungeon_data,
            "is_battling": self.is_battling,
            "battle_start_time": self.battle_start_time,
            "current_battle_data": self.current_battle_data
        }
    
    @classmethod
    def from_dict(cls, db_data: dict) -> 'LianliSystem':
        """从数据库数据创建"""
        instance = cls()
        instance.tower_highest_floor = db_data.get("tower_highest_floor", 0)
        instance.daily_dungeon_data = db_data.get("daily_dungeon_data", {})
        instance.is_battling = db_data.get("is_battling", False)
        instance.battle_start_time = db_data.get("battle_start_time", None)
        instance.current_battle_data = db_data.get("current_battle_data", None)
        return instance


if __name__ == "__main__":
    from ..spell.SpellSystem import SpellSystem
    from ..player.PlayerSystem import PlayerSystem
    
    print("=" * 60)
    print("历练系统测试")
    print("=" * 60)
    
    spell_system = SpellSystem()
    # 解锁并装备术法
    spell_system.unlock_spell("basic_boxing_techniques")
    spell_system.equip_spell("basic_boxing_techniques")
    
    spell_system.unlock_spell("basic_health")
    spell_system.equip_spell("basic_health")
    
    spell_system.unlock_spell("basic_defense")
    spell_system.equip_spell("basic_defense")
    
    print(f"已解锁并装备基础拳法、基础气血、基础防御")
    print(f"装备的主动术法: {spell_system.equipped_spells.get('active', [])}")
    print(f"装备的开场术法: {spell_system.equipped_spells.get('opening', [])}")
    
    player_data = PlayerSystem(
        health=76.0,
        spirit_energy=20.0,
        realm="炼气期",
        realm_level=5,
        spell_system=spell_system
    )
    print(f"\n玩家信息:")
    print(f"  境界: {player_data.realm}{player_data.realm_level}层")
    print(f"  气血: {player_data.health}/{player_data.static_max_health}")
    print(f"  攻击: {player_data.static_attack}")
    print(f"  防御: {player_data.static_defense}")
    print(f"  速度: {player_data.static_speed}")
    
    lianli_system = LianliSystem()
    
    print(f"\n开始挑战区域: qi_refining_outer")
    print("-" * 60)
    
    result = lianli_system.start_battle_simulation(
        area_id="qi_refining_outer",
        player_data=player_data,
        spell_system=spell_system
    )
    
    print(f"\n战斗结果:")
    print(f"  胜利: {result['victory']}")
    print(f"  总时间: {result['total_time']}秒")
    print(f"  战斗后气血: {result['player_health_after']}")
    print(f"  敌人剩余气血: {result['enemy_health_after']}")
    print(f"  掉落: {result.get('loot', [])}")
    
    print(f"\n战斗时间线 (共{len(result['battle_timeline'])}个事件):")
    print("-" * 60)
    for i, event in enumerate(result['battle_timeline'], 1):
        event_type = event.get('type', 'unknown')
        time = event.get('time', 0)
        
        if event_type == 'opening_spell':
            print(f"[{i:2d}] {time:6.2f}s | 开场术法: {event.get('spell_id', 'unknown')} - {event.get('log_effect', '效果触发')}")
        elif event_type == 'player_attack':
            print(f"[{i:2d}] {time:6.2f}s | 玩家攻击: {event.get('spell_id', 'unknown')} -> 伤害 {event.get('damage'):.2f}, 敌人剩余气血 {event.get('enemy_health_after'):.2f}")
        elif event_type == 'enemy_attack':
            print(f"[{i:2d}] {time:6.2f}s | 敌人攻击: {event.get('spell_id', 'unknown')} -> 伤害 {event.get('damage'):.2f}, 玩家剩余气血 {event.get('player_health_after'):.2f}")
        else:
            print(f"[{i:2d}] {time:6.2f}s | {event_type}: {event}")
    
    print("=" * 60)
    print("测试完成")
