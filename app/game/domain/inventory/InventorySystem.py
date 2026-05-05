"""
背包系统

负责管理玩家的物品存储，包括添加、移除、使用、整理等功能
"""

from typing import Dict, Any, List, TYPE_CHECKING

from .ItemData import ItemData
from ..cultivation.RealmData import RealmData

if TYPE_CHECKING:
    from .player_data import PlayerSystem
    from .spell_system import SpellSystem
    from .alchemy_system import AlchemySystem


class InventorySystem:
    """背包系统"""
    
    DEFAULT_SIZE = 60
    MAX_SIZE = 60
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
                "reason_code": str,
                "reason_data": dict
            }
        """
        if not self.can_expand():
            return self._build_result(False, "INVENTORY_EXPAND_CAPACITY_MAX", {
                "new_capacity": self.capacity
            })
        
        self.capacity = min(self.capacity + self.EXPAND_STEP, self.MAX_SIZE)
        
        return self._build_result(True, "INVENTORY_EXPAND_SUCCEEDED", {
            "new_capacity": self.capacity
        })
    
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

    @staticmethod
    def _build_result(success: bool, reason_code: str, reason_data: Dict[str, Any] = None) -> Dict[str, Any]:
        return {
            "success": success,
            "reason_code": reason_code,
            "reason_data": reason_data or {}
        }

    @classmethod
    def _build_use_item_result(
        cls,
        success: bool,
        reason_code: str,
        item_id: str,
        used_count: int = 0,
        effect: Dict[str, Any] = None,
        contents: Dict[str, int] = None
    ) -> Dict[str, Any]:
        return cls._build_result(success, reason_code, {
            "item_id": item_id,
            "used_count": used_count,
            "effect": effect or {},
            "contents": contents or {}
        })
    
    def organize_inventory(self) -> Dict[str, Any]:
        """
        整理背包
        
        Returns:
            {
                "success": bool,
                "reason_code": str,
                "reason_data": dict
            }
        """
        items = []
        for i in range(self.capacity):
            if not self.slots[i]["empty"]:
                items.append({
                    "id": self.slots[i]["id"],
                    "count": self.slots[i]["count"]
                })

        items.sort(key=lambda x: (
            ItemData.get_item_type(x["id"]),
            -int(ItemData.get_item_quality(x["id"])),
            x["id"],
        ))
        
        self._init_slots()
        
        for item in items:
            self.add_item(item["id"], item["count"])
        
        return self._build_result(True, "INVENTORY_ORGANIZE_SUCCEEDED", {})
    
    def discard_item(self, item_id: str, count: int) -> Dict[str, Any]:
        """
        丢弃物品
        
        Args:
            item_id: 物品ID
            count: 数量
        
        Returns:
            {
                "success": bool,
                "reason_code": str,
                "reason_data": dict
            }
        """
        removed = self.remove_item(item_id, count)
        
        if removed > 0:
            return self._build_result(True, "INVENTORY_DISCARD_SUCCEEDED", {
                "item_id": item_id,
                "discarded_count": removed
            })
        else:
            return self._build_result(False, "INVENTORY_DISCARD_ITEM_NOT_ENOUGH", {
                "item_id": item_id,
                "discarded_count": 0
            })
    
    def use_item(self, item_id: str, player_data: 'PlayerSystem',
                 spell_system: 'SpellSystem' = None,
                 alchemy_system: 'AlchemySystem' = None,
                 count: int = 1) -> Dict[str, Any]:
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
                "reason_code": str,
                "reason_data": dict
            }
        """
        use_count = max(1, int(count))

        if not ItemData.item_exists(item_id):
            return self._build_use_item_result(False, "INVENTORY_USE_ITEM_NOT_FOUND", item_id)

        if not self.has_item(item_id, 1):
            return self._build_use_item_result(False, "INVENTORY_USE_ITEM_NOT_ENOUGH", item_id)

        success_count = 0
        merged_contents: Dict[str, int] = {}
        merged_effect: Dict[str, Any] = {}
        total_health_added = 0
        total_spirit_added = 0
        first_success_reason_code = ""
        last_error_result: Dict[str, Any] = {}

        for _ in range(use_count):
            if not self.has_item(item_id, 1):
                last_error_result = self._build_use_item_result(
                    False,
                    "INVENTORY_USE_ITEM_NOT_ENOUGH",
                    item_id
                )
                break
            single_result = self._use_item_single(item_id, player_data, spell_system, alchemy_system)
            if not single_result.get("success", False):
                last_error_result = single_result
                break

            success_count += int(single_result.get("reason_data", {}).get("used_count", 1))
            if not first_success_reason_code:
                first_success_reason_code = str(single_result.get("reason_code", "INVENTORY_USE_SUCCEEDED"))

            single_effect = single_result.get("reason_data", {}).get("effect", {})
            if isinstance(single_effect, dict) and single_effect:
                merged_effect["type"] = str(single_effect.get("type", merged_effect.get("type", "")))
                total_health_added += int(single_effect.get("health_added", 0))
                total_spirit_added += int(single_effect.get("spirit_energy_added", 0))

            single_contents = single_result.get("reason_data", {}).get("contents", {})
            if isinstance(single_contents, dict):
                for content_item_id, content_count in single_contents.items():
                    merged_contents[content_item_id] = int(merged_contents.get(content_item_id, 0)) + int(content_count)

        if success_count <= 0:
            return last_error_result if last_error_result else self._build_use_item_result(
                False, "INVENTORY_USE_SYSTEM_ERROR", item_id
            )

        if merged_effect:
            if total_health_added > 0:
                merged_effect["health_added"] = total_health_added
            if total_spirit_added > 0:
                merged_effect["spirit_energy_added"] = total_spirit_added

        reason_data = {
            "item_id": item_id,
            "used_count": success_count,
            "effect": merged_effect,
            "contents": merged_contents,
            "requested_count": use_count,
            "completed_count": success_count,
            "is_partial": success_count < use_count,
        }
        if last_error_result:
            reason_data["partial_stop_reason_code"] = str(last_error_result.get("reason_code", ""))
            reason_data["partial_stop_reason_data"] = last_error_result.get("reason_data", {})

        if success_count == use_count:
            return self._build_result(True, first_success_reason_code, reason_data)
        return self._build_result(True, "INVENTORY_USE_PARTIAL_SUCCEEDED", reason_data)

    def _use_item_single(self, item_id: str, player_data: 'PlayerSystem',
                         spell_system: 'SpellSystem' = None,
                         alchemy_system: 'AlchemySystem' = None) -> Dict[str, Any]:
        item_type = ItemData.get_item_type(item_id)

        # 消耗品类型（丹药等）
        if item_type == ItemData.ITEM_TYPE_CONSUMABLE:
            return self._use_consumable(item_id, player_data)

        # 宝箱/礼包类型
        elif item_type == ItemData.ITEM_TYPE_GIFT:
            requirement_check = self._check_item_requirement(item_id, player_data)
            if not requirement_check.get("ok", True):
                return self._build_use_item_result(
                    False,
                    "INVENTORY_USE_REQUIREMENT_NOT_MET",
                    item_id,
                    0,
                    {
                        "type": "requirement_not_met",
                        "requirement": requirement_check.get("requirement", {}),
                        "current_realm": str(player_data.realm),
                        "current_level": int(player_data.realm_level),
                    },
                )
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
            return self._build_use_item_result(False, "INVENTORY_USE_ITEM_NOT_USABLE", item_id)
    
    def _use_consumable(self, item_id: str, player_data: 'PlayerSystem') -> Dict[str, Any]:
        """使用消耗品"""
        effect = ItemData.get_item_effect(item_id)
        actual_effect = {"type": ""}
        
        effect_type = effect.get("type", "")
        
        if effect_type == "add_spirit_energy_unlimited":
            amount = int(effect.get("amount", 0))
            player_data.add_spirit_energy_breakthrough(float(amount))
            actual_effect["type"] = "add_spirit_energy"
            actual_effect["spirit_energy_added"] = amount
        
        elif effect_type == "add_spirit_energy":
            amount = int(effect.get("amount", 0))
            player_data.add_spirit_energy(float(amount))
            actual_effect["type"] = "add_spirit_energy"
            actual_effect["spirit_energy_added"] = amount

        elif effect_type == "add_health":
            amount = int(effect.get("amount", 0))
            player_data.add_health(float(amount))
            actual_effect["type"] = "add_health"
            actual_effect["health_added"] = amount
        
        elif effect_type == "add_spirit_and_health":
            spirit_amount = int(effect.get("spirit_amount", 0))
            health_amount = int(effect.get("health_amount", 0))
            unlimited = effect.get("unlimited", False)
            
            if unlimited:
                player_data.add_spirit_energy_breakthrough(float(spirit_amount))
            else:
                player_data.add_spirit_energy(float(spirit_amount))
            player_data.add_health(health_amount)
            
            actual_effect["type"] = "add_spirit_and_health"
            actual_effect["spirit_energy_added"] = spirit_amount
            actual_effect["health_added"] = health_amount
        
        else:
            return self._build_use_item_result(False, "INVENTORY_USE_EFFECT_INVALID", item_id, 0, {
                "type": effect_type
            })
        
        self.remove_item(item_id, 1)
        
        return self._build_use_item_result(True, "INVENTORY_USE_CONSUMABLE_SUCCEEDED", item_id, 1, actual_effect)
    
    def _use_gift(self, item_id: str) -> Dict[str, Any]:
        """打开宝箱/礼包"""
        content = ItemData.get_item_content(item_id)
        
        if not content:
            return self._build_use_item_result(False, "INVENTORY_USE_SYSTEM_ERROR", item_id, 0, {
                "type": "open_gift"
            })
        
        self.remove_item(item_id, 1)
        
        actual_contents = {}
        for content_item_id, count in content.items():
            added = self.add_item(content_item_id, count)
            if added > 0:
                actual_contents[content_item_id] = added
        
        return self._build_use_item_result(
            True,
            "INVENTORY_USE_GIFT_SUCCEEDED",
            item_id,
            1,
            {"type": "open_gift"},
            actual_contents
        )
    
    def _use_unlock_spell(self, item_id: str, spell_system: 'SpellSystem') -> Dict[str, Any]:
        """使用解锁术法物品"""
        if not spell_system:
            return self._build_use_item_result(False, "INVENTORY_USE_SYSTEM_ERROR", item_id)
        
        effect = ItemData.get_item_effect(item_id)
        spell_id = effect.get("spell_id", "")
        
        if not spell_id:
            return self._build_use_item_result(False, "INVENTORY_USE_UNLOCK_SPELL_INVALID", item_id)
        
        if spell_system.has_spell(spell_id):
            return self._build_use_item_result(False, "INVENTORY_USE_ALREADY_USED", item_id, 0, {
                "type": "unlock_spell",
                "spell_id": spell_id
            })
        
        spell_system.unlock_spell(spell_id)
        self.remove_item(item_id, 1)
        
        return self._build_use_item_result(True, "INVENTORY_USE_UNLOCK_SPELL_SUCCEEDED", item_id, 1, {
            "type": "unlock_spell",
            "spell_id": spell_id
        })
    
    def _use_unlock_recipe(self, item_id: str, alchemy_system: 'AlchemySystem') -> Dict[str, Any]:
        """使用解锁丹方物品"""
        if not alchemy_system:
            return self._build_use_item_result(False, "INVENTORY_USE_SYSTEM_ERROR", item_id)
        
        effect = ItemData.get_item_effect(item_id)
        recipe_id = effect.get("recipe_id", "")
        
        if not recipe_id:
            recipe_id = item_id.replace("recipe_", "")
        
        if alchemy_system.has_recipe(recipe_id):
            return self._build_use_item_result(False, "INVENTORY_USE_ALREADY_USED", item_id, 0, {
                "type": "unlock_recipe",
                "recipe_id": recipe_id
            })
        
        result = alchemy_system.learn_recipe(recipe_id)
        
        if not result["success"]:
            return self._build_use_item_result(False, "INVENTORY_USE_UNLOCK_RECIPE_INVALID", item_id, 0, {
                "type": "unlock_recipe",
                "recipe_id": recipe_id
            })
        
        self.remove_item(item_id, 1)
        
        return self._build_use_item_result(True, "INVENTORY_USE_UNLOCK_RECIPE_SUCCEEDED", item_id, 1, {
            "type": "unlock_recipe",
            "recipe_id": recipe_id
        })
    
    def _use_unlock_furnace(self, item_id: str, alchemy_system: 'AlchemySystem') -> Dict[str, Any]:
        """使用解锁炼丹炉物品"""
        if not alchemy_system:
            return self._build_use_item_result(False, "INVENTORY_USE_SYSTEM_ERROR", item_id)
        
        if alchemy_system.has_furnace():
            return self._build_use_item_result(False, "INVENTORY_USE_ALREADY_USED", item_id, 0, {
                "type": "unlock_furnace",
                "furnace_id": item_id
            })
        
        alchemy_system.equip_furnace(item_id)
        self.remove_item(item_id, 1)
        
        return self._build_use_item_result(True, "INVENTORY_USE_UNLOCK_FURNACE_SUCCEEDED", item_id, 1, {
            "type": "unlock_furnace",
            "furnace_id": item_id
        })

    def _check_item_requirement(self, item_id: str, player_data: 'PlayerSystem') -> Dict[str, Any]:
        requirement = ItemData.get_item_requirement(item_id)
        if not requirement:
            return {"ok": True, "requirement": {}}

        realm_min = int(requirement.get("realm_min", 0))
        if realm_min > 0:
            total_realm_level = RealmData.get_total_realm_level(str(player_data.realm), int(player_data.realm_level))
            if total_realm_level < realm_min:
                return {"ok": False, "requirement": requirement}

        return {"ok": True, "requirement": requirement}
    
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
