"""
术法数据系统

负责术法配置的加载和查询
提供静态函数进行术法相关的查询
"""

import json
import os
from typing import Dict, Any, List


class SpellData:
    """
    术法数据系统 - 负责术法配置的加载和查询
    
    直接加载 spells.json 配置，提供静态函数进行术法相关的查询
    """
    
    _SPELLS_CONFIG: Dict[str, Any] = {}
    _LOADED: bool = False
    
    # 装备槽位类型常量
    SLOT_BREATHING = 0  # 吐纳槽位
    SLOT_ACTIVE = 1      # 主动术法槽位
    SLOT_PASSIVE = 2     # 被动术法槽位
    
    # 装备槽位上限常量
    MAX_BREATHING_SPELLS = 1
    MAX_ACTIVE_SPELLS = 2
    MAX_PASSIVE_SPELLS = 2
    
    # 术法类型常量
    SPELL_TYPE_BREATHING = 0  # 吐纳型
    SPELL_TYPE_ACTIVE = 1      # 主动型
    SPELL_TYPE_PASSIVE = 2     # 被动型
    SPELL_TYPE_MISC = 3        # 杂学型
    
    # 槽位类型映射（槽位索引 -> 槽位名称）
    SLOT_TYPE_NAMES = {
        0: "breathing",
        1: "active",
        2: "passive"
    }
    
    # 槽位名称映射（槽位名称 -> 槽位索引）
    SLOT_NAME_TO_TYPE = {
        "breathing": 0,
        "active": 1,
        "passive": 2
    }
    
    @classmethod
    def _load_config(cls):
        """加载配置文件"""
        if cls._LOADED:
            return
        
        config_path = os.path.join(os.path.dirname(__file__), 'spells.json')
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
    def get_spell_type(cls, spell_id: str) -> int:
        """获取术法类型"""
        spell_info = cls.get_spell_info(spell_id)
        return spell_info.get("type", cls.SPELL_TYPE_MISC)
    
    @classmethod
    def get_spell_max_level(cls, spell_id: str) -> int:
        """获取术法最大等级"""
        spell_info = cls.get_spell_info(spell_id)
        return spell_info.get("max_level", 3)
    
    @classmethod
    def get_spell_level_data(cls, spell_id: str, level: int) -> dict:
        """获取术法等级数据"""
        spell_info = cls.get_spell_info(spell_id)
        levels = spell_info.get("levels", {})
        return levels.get(str(level), {})
    
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
    def get_spells_by_type(cls, spell_type: int) -> List[str]:
        """获取指定类型的所有术法ID"""
        cls._load_config()
        spells = cls._SPELLS_CONFIG.get("spells", {})
        result = []
        for spell_id, spell_info in spells.items():
            if spell_info.get("type", cls.SPELL_TYPE_MISC) == spell_type:
                result.append(spell_id)
        return result
    
    @classmethod
    def get_slot_limit(cls, slot_type: int) -> int:
        """获取槽位上限"""
        limits = {
            cls.SLOT_BREATHING: cls.MAX_BREATHING_SPELLS,
            cls.SLOT_ACTIVE: cls.MAX_ACTIVE_SPELLS,
            cls.SLOT_PASSIVE: cls.MAX_PASSIVE_SPELLS
        }
        return limits.get(slot_type, 0)
    
    @classmethod
    def get_slot_name(cls, slot_type: int) -> str:
        """获取槽位名称"""
        return cls.SLOT_TYPE_NAMES.get(slot_type, "")
    
    @classmethod
    def get_slot_type_from_name(cls, slot_name: str) -> int:
        """从槽位名称获取槽位类型"""
        return cls.SLOT_NAME_TO_TYPE.get(slot_name, -1)
    
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
