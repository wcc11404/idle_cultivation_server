"""
背包系统

负责管理玩家的物品存储，包括添加、移除、使用、整理等功能
"""

from typing import Dict, Any, List, TYPE_CHECKING

from .ItemData import ItemData

if TYPE_CHECKING:
    from .player_data import PlayerSystem
    from .spell_system import SpellSystem
    from .alchemy_system import AlchemySystem


class InventorySystem:
    """背包系统"""
    
    DEFAULT_SIZE = 50
    MAX_SIZE = 200
    EXPAND_STEP = 10
    
    def __init__(self):
        """初始化背包系统"""
        self.slots: List[Dict[str, Any]] = []
        self.capacity: int = self.DEFAULT_SIZE
        self._init_slots()
    
    def _init_slots(self):
        """初始化槽位"""
        self.slots.clear()
        for i in range(self.MAX_SIZE):
            self.slots.append({"empty": True, "id": "", "count": 0})
    
    def get_used_slots(self) -> int:
        """获取已使用的槽位数量"""
        used = 0
        for i in range(self.capacity):
            if not self.slots[i]["empty"]:
                used += 1
        return used
    
    def get_capacity(self) -> int:
        """获取背包容量"""
        return self.capacity
    
    def can_expand(self) -> bool:
        """检查是否可以扩容"""
        return self.capacity < self.MAX_SIZE
    
    def expand_capacity(self) -> Dict[str, Any]:
        """
        扩容背包
        
        Returns:
            {
                "success": bool,
                "reason": str,
                "new_capacity": int
            }
        """
        if not self.can_expand():
            return {
                "success": False,
                "reason": "已达到最大容量",
                "new_capacity": self.capacity
            }
        
        self.capacity = min(self.capacity + self.EXPAND_STEP, self.MAX_SIZE)
        
        return {
            "success": True,
            "reason": "扩容成功",
            "new_capacity": self.capacity
        }
    
    def add_item(self, item_id: str, count: int = 1) -> int:
        """
        添加物品
        
        Args:
            item_id: 物品ID
            count: 数量
        
        Returns:
            实际添加的数量
        """
        if count <= 0:
            return 0
        
        if not ItemData.item_exists(item_id):
            return 0
        
        max_stack = ItemData.get_max_stack(item_id)
        can_stack = ItemData.can_stack(item_id)
        
        remaining_count = count
        
        if can_stack:
            for i in range(self.capacity):
                if remaining_count <= 0:
                    break
                if not self.slots[i]["empty"] and self.slots[i]["id"] == item_id:
                    current_count = self.slots[i]["count"]
                    can_add = min(remaining_count, max_stack - current_count)
                    if can_add > 0:
                        self.slots[i]["count"] = current_count + can_add
                        remaining_count -= can_add
        
        if remaining_count > 0:
            for i in range(self.capacity):
                if remaining_count <= 0:
                    break
                if self.slots[i]["empty"]:
                    add_count = min(remaining_count, max_stack)
                    self.slots[i] = {"empty": False, "id": item_id, "count": add_count}
                    remaining_count -= add_count
        
        return count - remaining_count
    
    def remove_item(self, item_id: str, count: int = 1) -> int:
        """
        移除物品
        
        Args:
            item_id: 物品ID
            count: 数量
        
        Returns:
            实际移除的数量
        """
        remaining_count = count
        
        for i in range(self.capacity):
            if remaining_count <= 0:
                break
            if not self.slots[i]["empty"] and self.slots[i]["id"] == item_id:
                current_count = self.slots[i]["count"]
                remove_count = min(remaining_count, current_count)
                
                if remove_count > 0:
                    self.slots[i]["count"] = current_count - remove_count
                    remaining_count -= remove_count
                    
                    if self.slots[i]["count"] <= 0:
                        self.slots[i] = {"empty": True, "id": "", "count": 0}
        
        return count - remaining_count
    
    def remove_items(self, items: Dict[str, int]) -> bool:
        """
        批量移除物品
        
        Args:
            items: {item_id: count, ...}
        
        Returns:
            是否全部移除成功
        """
        for item_id, count in items.items():
            if not self.has_item(item_id, count):
                return False
        
        for item_id, count in items.items():
            self.remove_item(item_id, count)
        
        return True
    
    def has_item(self, item_id: str, count: int = 1) -> bool:
        """检查是否有足够的物品"""
        total = self.get_item_count(item_id)
        return total >= count
    
    def get_item_count(self, item_id: str) -> int:
        """获取物品数量"""
        total = 0
        for i in range(self.capacity):
            if not self.slots[i]["empty"] and self.slots[i]["id"] == item_id:
                total += self.slots[i]["count"]
        return total
    
    def get_item_list(self) -> List[Dict[str, Any]]:
        """获取物品列表"""
        result = []
        for i in range(self.capacity):
            result.append({
                "index": i,
                "empty": self.slots[i]["empty"],
                "id": self.slots[i]["id"],
                "count": self.slots[i]["count"]
            })
        return result
    
    def organize_inventory(self) -> Dict[str, Any]:
        """
        整理背包
        
        Returns:
            {
                "success": bool,
                "reason": str
            }
        """
        items = []
        for i in range(self.capacity):
            if not self.slots[i]["empty"]:
                items.append({
                    "id": self.slots[i]["id"],
                    "count": self.slots[i]["count"]
                })
        
        items.sort(key=lambda x: x["id"])
        
        self._init_slots()
        
        for item in items:
            self.add_item(item["id"], item["count"])
        
        return {
            "success": True,
            "reason": "整理完成"
        }
    
    def discard_item(self, item_id: str, count: int) -> Dict[str, Any]:
        """
        丢弃物品
        
        Args:
            item_id: 物品ID
            count: 数量
        
        Returns:
            {
                "success": bool,
                "reason": str,
                "discarded_count": int
            }
        """
        removed = self.remove_item(item_id, count)
        
        if removed > 0:
            return {
                "success": True,
                "reason": "丢弃成功",
                "discarded_count": removed
            }
        else:
            return {
                "success": False,
                "reason": "物品不足",
                "discarded_count": 0
            }
    
    def use_item(self, item_id: str, player_data: 'PlayerSystem', 
                 spell_system: 'SpellSystem' = None,
                 alchemy_system: 'AlchemySystem' = None) -> Dict[str, Any]:
        """
        使用物品
        
        Args:
            item_id: 物品ID
            player_data: 玩家数据
            spell_system: 术法系统（可选）
            alchemy_system: 炼丹系统（可选）
        
        Returns:
            {
                "success": bool,
                "reason": str,
                "effect": dict
            }
        """
        if not self.has_item(item_id, 1):
            return {"success": False, "reason": "物品不足", "effect": {}}
        
        if not ItemData.item_exists(item_id):
            return {"success": False, "reason": "物品不存在", "effect": {}}
        
        item_type = ItemData.get_item_type(item_id)
        
        # 消耗品类型（丹药等）
        if item_type == ItemData.ITEM_TYPE_CONSUMABLE:
            return self._use_consumable(item_id, player_data)
        
        # 宝箱/礼包类型
        elif item_type == ItemData.ITEM_TYPE_GIFT:
            return self._use_gift(item_id)
        
        # 解锁术法类型
        elif item_type == ItemData.ITEM_TYPE_UNLOCK_SPELL:
            return self._use_unlock_spell(item_id, spell_system)
        
        # 解锁丹方类型
        elif item_type == ItemData.ITEM_TYPE_UNLOCK_RECIPE:
            return self._use_unlock_recipe(item_id, alchemy_system)
        
        # 解锁炼丹炉类型
        elif item_type == ItemData.ITEM_TYPE_UNLOCK_FURNACE:
            return self._use_unlock_furnace(item_id, alchemy_system)
        
        else:
            return {"success": False, "reason": "该物品无法使用", "effect": {}}
    
    def _use_consumable(self, item_id: str, player_data: 'PlayerSystem') -> Dict[str, Any]:
        """使用消耗品"""
        effect = ItemData.get_item_effect(item_id)
        actual_effect = {}
        
        effect_type = effect.get("type", "")
        
        if effect_type == "add_spirit_energy_unlimited":
            amount = int(effect.get("amount", 0))
            player_data.add_spirit_energy_breakthrough(float(amount))
            actual_effect["spirit_energy_added"] = amount
        
        elif effect_type == "add_spirit_energy":
            amount = int(effect.get("amount", 0))
            actual_added = player_data.add_spirit_energy(float(amount))
            actual_effect["spirit_energy_added"] = actual_added
        
        elif effect_type == "add_health":
            amount = int(effect.get("amount", 0))
            actual_added = player_data.add_health(amount)
            actual_effect["health_added"] = actual_added
        
        elif effect_type == "add_spirit_and_health":
            spirit_amount = int(effect.get("spirit_amount", 0))
            health_amount = int(effect.get("health_amount", 0))
            unlimited = effect.get("unlimited", False)
            
            if unlimited:
                player_data.add_spirit_energy_breakthrough(float(spirit_amount))
            else:
                player_data.add_spirit_energy(float(spirit_amount))
            player_data.add_health(health_amount)
            
            actual_effect["spirit_energy_added"] = spirit_amount
            actual_effect["health_added"] = health_amount
        
        else:
            return {"success": False, "reason": f"未知效果类型: {effect_type}", "effect": {}}
        
        self.remove_item(item_id, 1)
        
        return {
            "success": True,
            "reason": "使用成功",
            "effect": actual_effect
        }
    
    def _use_gift(self, item_id: str) -> Dict[str, Any]:
        """打开宝箱/礼包"""
        content = ItemData.get_item_content(item_id)
        
        if not content:
            return {"success": False, "reason": "礼包内容为空", "effect": {}}
        
        self.remove_item(item_id, 1)
        
        actual_contents = {}
        for content_item_id, count in content.items():
            added = self.add_item(content_item_id, count)
            if added > 0:
                actual_contents[content_item_id] = added
        
        return {
            "success": True,
            "reason": "打开成功",
            "effect": {"contents": actual_contents}
        }
    
    def _use_unlock_spell(self, item_id: str, spell_system: 'SpellSystem') -> Dict[str, Any]:
        """使用解锁术法物品"""
        if not spell_system:
            return {"success": False, "reason": "术法系统未初始化", "effect": {}}
        
        effect = ItemData.get_item_effect(item_id)
        spell_id = effect.get("spell_id", "")
        
        if not spell_id:
            return {"success": False, "reason": "术法书无效", "effect": {}}
        
        if spell_system.has_spell(spell_id):
            return {"success": False, "reason": "已学会该术法", "effect": {}}
        
        spell_system.unlock_spell(spell_id)
        self.remove_item(item_id, 1)
        
        return {
            "success": True,
            "reason": "学会新术法",
            "effect": {"unlocked_spell": spell_id}
        }
    
    def _use_unlock_recipe(self, item_id: str, alchemy_system: 'AlchemySystem') -> Dict[str, Any]:
        """使用解锁丹方物品"""
        if not alchemy_system:
            return {"success": False, "reason": "炼丹系统未初始化", "effect": {}}
        
        effect = ItemData.get_item_effect(item_id)
        recipe_id = effect.get("recipe_id", "")
        
        if not recipe_id:
            recipe_id = item_id.replace("recipe_", "")
        
        if alchemy_system.has_recipe(recipe_id):
            return {"success": False, "reason": "已学会该丹方", "effect": {}}
        
        result = alchemy_system.learn_recipe(recipe_id)
        
        if not result["success"]:
            return {"success": False, "reason": result.get("reason", "学习失败"), "effect": {}}
        
        self.remove_item(item_id, 1)
        
        return {
            "success": True,
            "reason": "学会新丹方",
            "effect": {"learned_recipe": recipe_id}
        }
    
    def _use_unlock_furnace(self, item_id: str, alchemy_system: 'AlchemySystem') -> Dict[str, Any]:
        """使用解锁炼丹炉物品"""
        if not alchemy_system:
            return {"success": False, "reason": "炼丹系统未初始化", "effect": {}}
        
        if alchemy_system.has_furnace():
            return {"success": False, "reason": "已拥有丹炉", "effect": {}}
        
        alchemy_system.equip_furnace(item_id)
        self.remove_item(item_id, 1)
        
        return {
            "success": True,
            "reason": "获得丹炉",
            "effect": {"unlocked_furnace": item_id}
        }
    
    def check_items_enough(self, items: Dict[str, int]) -> bool:
        """
        检查物品是否足够
        
        Args:
            items: {item_id: count, ...}
        
        Returns:
            是否全部足够
        """
        for item_id, count in items.items():
            if not self.has_item(item_id, count):
                return False
        return True
    
    def to_dict(self) -> dict:
        """转换为数据库存储格式（稀疏格式，只存储非空槽位）"""
        sparse_slots = {}
        for i in range(self.capacity):
            if not self.slots[i]["empty"]:
                sparse_slots[str(i)] = {
                    "id": self.slots[i]["id"],
                    "count": self.slots[i]["count"]
                }
        
        return {
            "capacity": self.capacity,
            "slots": sparse_slots
        }
    
    @classmethod
    def from_dict(cls, db_data: dict) -> 'InventorySystem':
        """从数据库数据创建（支持稀疏格式和数组格式）"""
        instance = cls()
        instance.capacity = db_data.get("capacity", cls.DEFAULT_SIZE)
        
        slots_data = db_data.get("slots", [])
        
        if isinstance(slots_data, list):
            instance._init_slots()
            for i in range(min(len(slots_data), cls.MAX_SIZE)):
                slot = slots_data[i]
                if isinstance(slot, dict) and not slot.get("empty", True):
                    instance.slots[i] = {
                        "empty": False,
                        "id": slot.get("id", ""),
                        "count": int(slot.get("count", 0))
                    }
        elif isinstance(slots_data, dict):
            instance._init_slots()
            for key, slot in slots_data.items():
                index = int(key)
                if 0 <= index < cls.MAX_SIZE:
                    if isinstance(slot, dict):
                        instance.slots[index] = {
                            "empty": False,
                            "id": slot.get("id", ""),
                            "count": int(slot.get("count", 0))
                        }
        else:
            instance._init_slots()
        
        if not instance.slots:
            instance._init_slots()
        
        return instance
