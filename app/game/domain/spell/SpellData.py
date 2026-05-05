"""
术法数据系统

负责术法配置的加载和查询
提供静态函数进行术法相关的查询
"""

import json
import os
from typing import Dict, Any, List
from pathlib import Path


class SpellData:
    """
    术法数据系统 - 负责术法配置的加载和查询
    
    直接加载 spells.json 配置，提供静态函数进行术法相关的查询
    """
    
    _SPELLS_CONFIG: Dict[str, Any] = {}
    _LOADED: bool = False
    
    # 术法类型常量
    SPELL_TYPE_BREATHING = "breathing"  # 吐纳型
    SPELL_TYPE_ACTIVE = "active"      # 主动型
    SPELL_TYPE_OPENING = "opening"     # 开场型
    SPELL_TYPE_PRODUCTION = "production"        # 生产型

    RARITY_TO_QUALITY = {
        "fan": 0,
        "huang": 1,
        "xuan": 2,
        "di": 3,
        "tian": 4,
    }
    
    @classmethod
    def _load_config(cls):
        """加载配置文件"""
        if cls._LOADED:
            return
        
        config_path = Path(__file__).resolve().parents[2] / 'content' / 'spell' / 'spells.json'
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cls._SPELLS_CONFIG = json.load(f)
            cls._LOADED = True
        except Exception as e:
            print(f"加载术法配置失败: {e}")
            cls._SPELLS_CONFIG = {}
    
    @classmethod
    def get_spell_info(cls, spell_id: str) -> dict:
        """获取术法信息"""
        cls._load_config()
        spells = cls._SPELLS_CONFIG.get("spells", {})
        return spells.get(spell_id, {})
    
    @classmethod
    def get_spell_name(cls, spell_id: str) -> str:
        """获取术法名称"""
        spell_info = cls.get_spell_info(spell_id)
        return spell_info.get("name", "未知术法")
    
    @classmethod
    def get_spell_type(cls, spell_id: str) -> str:
        """获取术法类型"""
        spell_info = cls.get_spell_info(spell_id)
        return spell_info.get("type", cls.SPELL_TYPE_PRODUCTION)
    
    @classmethod
    def get_spell_max_level(cls, spell_id: str) -> int:
        """获取术法最大等级"""
        spell_info = cls.get_spell_info(spell_id)
        return spell_info.get("max_level", 3)

    @classmethod
    def get_spell_max_star(cls, spell_id: str) -> int:
        """获取术法最大星级"""
        spell_info = cls.get_spell_info(spell_id)
        return int(spell_info.get("max_star", 0))

    @classmethod
    def get_spell_rarity(cls, spell_id: str) -> str:
        """获取术法稀有度"""
        spell_info = cls.get_spell_info(spell_id)
        return str(spell_info.get("rarity", "fan"))

    @classmethod
    def get_spell_quality(cls, spell_id: str) -> int:
        """获取术法对应的品质序号，直接复用物品稀有度映射。"""
        rarity = cls.get_spell_rarity(spell_id)
        return int(cls.RARITY_TO_QUALITY.get(rarity, 0))

    @classmethod
    def get_spell_element(cls, spell_id: str) -> str:
        """获取术法五行属性"""
        spell_info = cls.get_spell_info(spell_id)
        return str(spell_info.get("element", "none"))

    @classmethod
    def get_spell_unlock_item_id(cls, spell_id: str) -> str:
        """获取术法对应解锁道具 ID"""
        spell_info = cls.get_spell_info(spell_id)
        return str(spell_info.get("unlock_item_id", f"spell_{spell_id}"))
    
    @classmethod
    def get_spell_level_data(cls, spell_id: str, level: int) -> dict:
        """获取术法等级数据"""
        spell_info = cls.get_spell_info(spell_id)
        levels = spell_info.get("levels", {})
        return levels.get(str(level), {})

    @classmethod
    def get_spell_effects(cls, spell_id: str, level: int) -> List[Dict[str, Any]]:
        """获取指定等级的术法效果列表，兼容旧结构。"""
        level_data = cls.get_spell_level_data(spell_id, level)
        effect = level_data.get("effect", [])
        if isinstance(effect, list):
            return effect
        if isinstance(effect, dict) and effect:
            return [effect]
        return []

    @classmethod
    def get_spell_star_data(cls, spell_id: str, star: int) -> Dict[str, Any]:
        """获取星级数据。0-4 表示升星条件，5 表示五星最终属性。"""
        spell_info = cls.get_spell_info(spell_id)
        stars = spell_info.get("stars", {})
        return stars.get(str(star), {})
    
    @classmethod
    def get_spell_description(cls, spell_id: str) -> str:
        """获取术法描述"""
        spell_info = cls.get_spell_info(spell_id)
        return spell_info.get("description", "")
    
    @classmethod
    def spell_exists(cls, spell_id: str) -> bool:
        """检查术法是否存在"""
        cls._load_config()
        spells = cls._SPELLS_CONFIG.get("spells", {})
        return spell_id in spells
    
    @classmethod
    def get_all_spells(cls) -> List[str]:
        """获取所有术法ID列表"""
        cls._load_config()
        spells = cls._SPELLS_CONFIG.get("spells", {})
        return list(spells.keys())
    
    @classmethod
    def get_spells_by_type(cls, spell_type: str) -> List[str]:
        """获取指定类型的所有术法ID"""
        cls._load_config()
        spells = cls._SPELLS_CONFIG.get("spells", {})
        result = []
        for spell_id, spell_info in spells.items():
            if spell_info.get("type", cls.SPELL_TYPE_PRODUCTION) == spell_type:
                result.append(spell_id)
        return result
    
    @classmethod
    def get_slot_name(cls, slot_type: str) -> str:
        """获取槽位名称"""
        return slot_type
    
    @classmethod
    def get_slot_type_from_name(cls, slot_name: str) -> str:
        """从槽位名称获取槽位类型"""
        return slot_name
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """获取完整配置（用于其他模块）"""
        cls._load_config()
        return cls._SPELLS_CONFIG
    
    @classmethod
    def get_spells_config(cls) -> Dict[str, Any]:
        """获取术法配置（仅 spells 部分）"""
        cls._load_config()
        return cls._SPELLS_CONFIG.get("spells", {})
