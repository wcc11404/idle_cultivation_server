"""
历练数据系统

负责历练区域和敌人配置的加载和查询
提供静态函数进行历练相关的查询
"""

import json
import os
from typing import Dict, Any, List


class LianliData:
    """
    历练数据系统 - 负责历练区域和敌人配置的加载和查询
    
    直接加载 areas.json 和 enemies.json 配置
    """
    
    _AREAS_CONFIG: Dict[str, Any] = {}
    _ENEMIES_CONFIG: Dict[str, Any] = {}
    _LOADED: bool = False
    
    @classmethod
    def _load_config(cls):
        """加载配置文件"""
        if cls._LOADED:
            return
        
        areas_path = os.path.join(os.path.dirname(__file__), 'areas.json')
        enemies_path = os.path.join(os.path.dirname(__file__), 'enemies.json')
        
        try:
            with open(areas_path, 'r', encoding='utf-8') as f:
                cls._AREAS_CONFIG = json.load(f)
            with open(enemies_path, 'r', encoding='utf-8') as f:
                cls._ENEMIES_CONFIG = json.load(f)
            cls._LOADED = True
        except Exception as e:
            print(f"加载历练配置失败: {e}")
    
    @classmethod
    def get_areas_config(cls) -> Dict[str, Any]:
        """获取区域配置"""
        cls._load_config()
        return cls._AREAS_CONFIG
    
    @classmethod
    def get_enemies_config(cls) -> Dict[str, Any]:
        """获取敌人配置"""
        cls._load_config()
        return cls._ENEMIES_CONFIG
    
    @classmethod
    def get_area_info(cls, area_id: str) -> dict:
        """获取区域信息"""
        cls._load_config()
        for area_type in ["normal_areas", "special_areas", "daily_dungeons"]:
            if area_id in cls._AREAS_CONFIG.get(area_type, {}):
                return cls._AREAS_CONFIG[area_type][area_id]
        return cls._AREAS_CONFIG.get(area_id, {})
    
    @classmethod
    def get_enemy_template(cls, template_id: str) -> dict:
        """获取敌人模板"""
        cls._load_config()
        if "templates" in cls._ENEMIES_CONFIG:
            return cls._ENEMIES_CONFIG["templates"].get(template_id, {})
        return cls._ENEMIES_CONFIG.get(template_id, {})
