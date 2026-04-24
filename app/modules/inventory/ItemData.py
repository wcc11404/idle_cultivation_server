"""
物品系统

负责物品配置的加载和查询
提供静态函数进行物品相关的查询
"""

import json
import os
from typing import Dict, Any, List


class ItemData:
    """
    物品系统 - 负责物品配置的加载和查询
    
    直接加载 items.json 配置，提供静态函数进行物品相关的查询
    """
    
    _ITEMS_CONFIG: Dict[str, Any] = {}
    _LOADED: bool = False
    
    # 物品类型常量（与客户端对齐）
    ITEM_TYPE_CURRENCY = 0          # 货币类型（灵石等）
    ITEM_TYPE_MATERIAL = 1          # 材料类型（炼丹材料等）
    ITEM_TYPE_CONSUMABLE = 2        # 消耗品类型（丹药等）
    ITEM_TYPE_GIFT = 3              # 宝箱/礼包类型
    ITEM_TYPE_UNLOCK_SPELL = 4      # 解锁术法类型（术法书等）
    ITEM_TYPE_UNLOCK_RECIPE = 5     # 解锁丹方类型（丹方等）
    ITEM_TYPE_UNLOCK_FURNACE = 6    # 解锁炼丹炉类型（丹炉等）
    
    @classmethod
    def _load_config(cls):
        """加载配置文件"""
        if cls._LOADED:
            return
        
        config_path = os.path.join(os.path.dirname(__file__), 'items.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            cls._ITEMS_CONFIG = config.get("items", {})
            cls._LOADED = True
        except Exception as e:
            print(f"加载物品配置失败: {e}")
            cls._ITEMS_CONFIG = {}
    
    @classmethod
    def get_item_info(cls, item_id: str) -> dict:
        """获取物品信息"""
        cls._load_config()
        return cls._ITEMS_CONFIG.get(item_id, {})
    
    @classmethod
    def get_item_name(cls, item_id: str) -> str:
        """获取物品名称"""
        item_info = cls.get_item_info(item_id)
        return item_info.get("name", "未知物品")
    
    @classmethod
    def get_item_type(cls, item_id: str) -> int:
        """获取物品类型"""
        item_info = cls.get_item_info(item_id)
        return item_info.get("type", cls.ITEM_TYPE_MATERIAL)
    
    @classmethod
    def get_max_stack(cls, item_id: str) -> int:
        """获取物品最大堆叠数量"""
        item_info = cls.get_item_info(item_id)
        return item_info.get("max_stack", 99)
    
    @classmethod
    def can_stack(cls, item_id: str) -> bool:
        """检查物品是否可以堆叠"""
        item_info = cls.get_item_info(item_id)
        return item_info.get("max_stack", 1) > 1
    
    @classmethod
    def get_item_effect(cls, item_id: str) -> dict:
        """获取物品效果"""
        item_info = cls.get_item_info(item_id)
        return item_info.get("effect", {})
    
    @classmethod
    def get_item_content(cls, item_id: str) -> dict:
        """获取物品内容（宝箱/礼包）"""
        item_info = cls.get_item_info(item_id)
        return item_info.get("content", {})

    @classmethod
    def get_item_requirement(cls, item_id: str) -> dict:
        """获取物品使用需求配置"""
        item_info = cls.get_item_info(item_id)
        requirement = item_info.get("requirement", {})
        return requirement if isinstance(requirement, dict) else {}
    
    @classmethod
    def get_item_icon(cls, item_id: str) -> str:
        """获取物品图标路径"""
        item_info = cls.get_item_info(item_id)
        return item_info.get("icon", "")
    
    @classmethod
    def get_item_description(cls, item_id: str) -> str:
        """获取物品描述"""
        item_info = cls.get_item_info(item_id)
        return item_info.get("description", "")
    
    @classmethod
    def get_item_quality(cls, item_id: str) -> int:
        """获取物品品质"""
        item_info = cls.get_item_info(item_id)
        return item_info.get("quality", 0)
    
    @classmethod
    def is_currency(cls, item_id: str) -> bool:
        """检查是否为货币"""
        return cls.get_item_type(item_id) == cls.ITEM_TYPE_CURRENCY
    
    @classmethod
    def is_material(cls, item_id: str) -> bool:
        """检查是否为材料"""
        return cls.get_item_type(item_id) == cls.ITEM_TYPE_MATERIAL
    
    @classmethod
    def is_consumable(cls, item_id: str) -> bool:
        """检查是否为消耗品"""
        return cls.get_item_type(item_id) == cls.ITEM_TYPE_CONSUMABLE
    
    @classmethod
    def is_gift(cls, item_id: str) -> bool:
        """检查是否为宝箱/礼包"""
        return cls.get_item_type(item_id) == cls.ITEM_TYPE_GIFT
    
    @classmethod
    def is_unlock_spell(cls, item_id: str) -> bool:
        """检查是否为解锁术法物品"""
        return cls.get_item_type(item_id) == cls.ITEM_TYPE_UNLOCK_SPELL
    
    @classmethod
    def is_unlock_recipe(cls, item_id: str) -> bool:
        """检查是否为解锁丹方物品"""
        return cls.get_item_type(item_id) == cls.ITEM_TYPE_UNLOCK_RECIPE
    
    @classmethod
    def is_unlock_furnace(cls, item_id: str) -> bool:
        """检查是否为解锁炼丹炉物品"""
        return cls.get_item_type(item_id) == cls.ITEM_TYPE_UNLOCK_FURNACE
    
    @classmethod
    def item_exists(cls, item_id: str) -> bool:
        """检查物品是否存在"""
        cls._load_config()
        return item_id in cls._ITEMS_CONFIG
    
    @classmethod
    def get_all_items(cls) -> List[str]:
        """获取所有物品ID列表"""
        cls._load_config()
        return list(cls._ITEMS_CONFIG.keys())
    
    @classmethod
    def get_items_by_type(cls, item_type: int) -> List[str]:
        """获取指定类型的所有物品ID"""
        cls._load_config()
        result = []
        for item_id, item_info in cls._ITEMS_CONFIG.items():
            if item_info.get("type", cls.ITEM_TYPE_MATERIAL) == item_type:
                result.append(item_id)
        return result
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """获取完整配置（用于其他模块）"""
        cls._load_config()
        return cls._ITEMS_CONFIG
