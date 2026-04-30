"""
境界系统

负责境界相关的查询和数值计算
直接加载 realms.json 配置
"""

import json
import os
from typing import Dict, Any, List
from pathlib import Path


class RealmData:
    """
    境界系统
    
    直接加载 realms.json 配置，提供静态函数进行境界相关的查询和数值计算
    """
    
    _REALMS_CONFIG: Dict[str, Any] = {}
    _LOADED: bool = False
    
    @classmethod
    def _load_config(cls):
        """加载配置文件"""
        if cls._LOADED:
            return
        
        config_path = Path(__file__).resolve().parents[2] / 'content' / 'cultivation' / 'realms.json'
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cls._REALMS_CONFIG = json.load(f)
            cls._LOADED = True
        except Exception as e:
            print(f"加载境界配置失败: {e}")
            cls._REALMS_CONFIG = {}
    
    @classmethod
    def get_realm_info(cls, realm_name: str) -> dict:
        """获取境界信息"""
        cls._load_config()
        realms = cls._REALMS_CONFIG.get("realms", {})
        return realms.get(realm_name, {})
    
    @classmethod
    def get_level_info(cls, realm_name: str, level: int) -> dict:
        """获取境界层数信息"""
        realm_info = cls.get_realm_info(realm_name)
        levels = realm_info.get("levels", {})
        return levels.get(str(level), {})
    
    @classmethod
    def get_level_name(cls, realm_name: str, level: int) -> str:
        """获取境界层数名称"""
        realm_info = cls.get_realm_info(realm_name)
        names = realm_info.get("level_names", {})
        return names.get(str(level), f"{level}段")
    
    @classmethod
    def get_realm_attributes(cls, realm_name: str, level: int) -> dict:
        """
        获取境界属性（从配置加载）
        
        Returns:
            {
                "max_health": int,
                "attack": float,
                "defense": float,
                "speed": float,
                "max_spirit_energy": int,
                "health_regen_per_second": float,
                "spirit_gain_speed": float
            }
        """
        level_info = cls.get_level_info(realm_name, level)
        realm_info = cls.get_realm_info(realm_name)
        
        return {
            "max_health": level_info.get("health", 100),
            "attack": level_info.get("attack", 10),
            "defense": level_info.get("defense", 5),
            "speed": realm_info.get("speed", 7.0),
            "max_spirit_energy": level_info.get("max_spirit_energy", 100),
            "health_regen_per_second": level_info.get("health_regen", 1.0),
            "spirit_gain_speed": realm_info.get("spirit_gain_speed", 1.0)
        }
    
    @classmethod
    def get_breakthrough_info(cls, realm_name: str, level: int) -> dict:
        """
        获取突破所需信息
        
        Args:
            realm_name: 当前境界名称
            level: 当前境界层数
        
        Returns:
            {
                "can": bool,  # 是否可以突破
                "next_realm": str,  # 突破后的境界
                "next_level": int,  # 突破后的层数
                "spirit_energy_cost": int,      # 需要的灵气
                "spirit_stone_cost": int,       # 需要的灵石
                "materials": {"item_id": count, ...}  # 需要的物品
            }
        """
        cls._load_config()
        realm_info = cls.get_realm_info(realm_name)
        
        if not realm_info:
            return {
                "can": False,
                "next_realm": realm_name,
                "next_level": level,
                "spirit_energy_cost": 0,
                "spirit_stone_cost": 0,
                "materials": {}
            }
        
        max_level = realm_info.get("max_level", 10)
        current_level_info = cls.get_level_info(realm_name, level)
        
        spirit_energy_cost = current_level_info.get("spirit_energy_cost", 0)
        spirit_stone_cost = current_level_info.get("spirit_stone_cost", 0)
        
        if level >= max_level:
            next_realm = cls.get_next_realm(realm_name)
            if not next_realm:
                return {
                    "can": False,
                    "next_realm": realm_name,
                    "next_level": level,
                    "spirit_energy_cost": 0,
                    "spirit_stone_cost": 0,
                    "materials": {}
                }
            
            materials_config = cls._REALMS_CONFIG.get("breakthrough_materials", {})
            materials = materials_config.get(realm_name, {}).get(str(level), {})
            
            return {
                "can": True,
                "next_realm": next_realm,
                "next_level": 1,
                "spirit_energy_cost": spirit_energy_cost,
                "spirit_stone_cost": spirit_stone_cost,
                "materials": materials
            }
        else:
            materials_config = cls._REALMS_CONFIG.get("breakthrough_materials", {})
            materials = materials_config.get(realm_name, {}).get(str(level), {})
            
            return {
                "can": True,
                "next_realm": realm_name,
                "next_level": level + 1,
                "spirit_energy_cost": spirit_energy_cost,
                "spirit_stone_cost": spirit_stone_cost,
                "materials": materials
            }
    
    @classmethod
    def get_total_realm_level(cls, realm_name: str, level: int) -> int:
        """获取总境界等级"""
        cls._load_config()
        realm_order = cls._REALMS_CONFIG.get("realm_order", [])
        try:
            realm_index = realm_order.index(realm_name)
            return realm_index * 10 + level
        except ValueError:
            return 0
    
    @classmethod
    def get_next_realm(cls, current_realm: str) -> str:
        """获取下一大境界"""
        cls._load_config()
        realm_order = cls._REALMS_CONFIG.get("realm_order", [])
        try:
            current_index = realm_order.index(current_realm)
            if current_index + 1 < len(realm_order):
                return realm_order[current_index + 1]
        except ValueError:
            pass
        return ""
    
    @classmethod
    def get_realm_display_name(cls, realm_name: str, level: int) -> str:
        """获取境界显示名称"""
        level_name = cls.get_level_name(realm_name, level)
        return f"{realm_name} {level_name}"
    
    @classmethod
    def get_all_realms(cls) -> List[str]:
        """获取所有境界"""
        cls._load_config()
        realms = cls._REALMS_CONFIG.get("realms", {})
        return list(realms.keys())
    
    @classmethod
    def get_max_level(cls, realm_name: str) -> int:
        """获取境界最大层数"""
        realm_info = cls.get_realm_info(realm_name)
        return realm_info.get("max_level", 10)
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """获取完整配置（用于其他模块）"""
        cls._load_config()
        return cls._REALMS_CONFIG
    
    @classmethod
    def get_first_realm(cls) -> str:
        """获取第一个境界"""
        cls._load_config()
        realm_order = cls._REALMS_CONFIG.get("realm_order", [])
        return realm_order[0] if realm_order else "炼气期"
