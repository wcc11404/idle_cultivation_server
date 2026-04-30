"""
历练区域数据系统

负责历练区域配置的加载和查询
提供静态函数进行区域相关的查询
"""

import json
import os
import random
from typing import Dict, Any, List
from pathlib import Path


class AreasData:
    """
    历练区域数据系统 - 负责区域配置的加载和查询
    
    直接加载 areas.json 配置
    """
    
    _AREAS_CONFIG: Dict[str, Any] = {}
    _LOADED: bool = False
    
    @classmethod
    def _load_config(cls):
        """加载配置文件"""
        if cls._LOADED:
            return
        
        config_path = Path(__file__).resolve().parents[2] / 'content' / 'lianli' / 'areas.json'
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cls._AREAS_CONFIG = json.load(f)
            cls._LOADED = True
        except Exception as e:
            print(f"加载区域配置失败: {e}")
    
    @classmethod
    def get_areas_config(cls) -> Dict[str, Any]:
        """获取区域配置"""
        cls._load_config()
        return cls._AREAS_CONFIG
    
    @classmethod
    def get_normal_areas(cls) -> Dict[str, Any]:
        """获取普通区域"""
        cls._load_config()
        return cls._AREAS_CONFIG.get("normal_areas", {}).copy()
    
    @classmethod
    def get_daily_areas(cls) -> Dict[str, Any]:
        """获取每日区域"""
        cls._load_config()
        return cls._AREAS_CONFIG.get("daily_areas", {}).copy()
    
    @classmethod
    def get_all_areas(cls) -> Dict[str, Any]:
        """获取所有区域"""
        cls._load_config()
        all_areas = {}
        all_areas.update(cls._AREAS_CONFIG.get("normal_areas", {}))
        all_areas.update(cls._AREAS_CONFIG.get("daily_areas", {}))
        return all_areas
    
    @classmethod
    def get_normal_area_ids(cls) -> List[str]:
        """获取普通区域ID列表"""
        cls._load_config()
        return list(cls._AREAS_CONFIG.get("normal_areas", {}).keys())
    
    @classmethod
    def get_daily_area_ids(cls) -> List[str]:
        """获取每日区域ID列表"""
        cls._load_config()
        return list(cls._AREAS_CONFIG.get("daily_areas", {}).keys())
    
    @classmethod
    def get_all_area_ids(cls) -> List[str]:
        """获取所有区域ID列表"""
        cls._load_config()
        ids = []
        ids.extend(cls._AREAS_CONFIG.get("normal_areas", {}).keys())
        ids.extend(cls._AREAS_CONFIG.get("daily_areas", {}).keys())
        return ids
    
    @classmethod
    def get_area_info(cls, area_id: str) -> dict:
        """获取区域信息"""
        cls._load_config()
        for area_type in ["normal_areas", "daily_areas"]:
            if area_id in cls._AREAS_CONFIG.get(area_type, {}):
                return cls._AREAS_CONFIG[area_type][area_id].copy()
        return {}
    
    @classmethod
    def get_area_name(cls, area_id: str) -> str:
        """获取区域名称"""
        area_config = cls.get_area_info(area_id)
        return area_config.get("name", "未知区域")
    
    @classmethod
    def get_area_description(cls, area_id: str) -> str:
        """获取区域描述"""
        area_config = cls.get_area_info(area_id)
        return area_config.get("description", "")
    
    @classmethod
    def get_default_continuous(cls, area_id: str) -> bool:
        """获取区域是否默认连续战斗"""
        area_config = cls.get_area_info(area_id)
        return area_config.get("default_continuous", True)
    
    @classmethod
    def get_random_enemy_config(cls, area_id: str) -> Dict[str, Any]:
        """
        使用权重随机选择敌人配置
        
        Args:
            area_id: 区域 ID
        
        Returns:
            敌人配置字典，包含enemies列表、drops等
        """
        area = cls.get_area_info(area_id)
        if not area:
            return {}
        
        enemies_template = area.get("enemies_template", [])
        if not enemies_template:
            return {}
        
        total_weight = 0
        for template in enemies_template:
            total_weight += template.get("weight", 0)
        
        if total_weight <= 0:
            return enemies_template[0].copy()
        
        random_value = random.randint(0, total_weight - 1)
        current_weight = 0
        
        for template in enemies_template:
            current_weight += template.get("weight", 0)
            if random_value < current_weight:
                return template.copy()
        
        return enemies_template[0].copy()
    
    # ==================== 每日区域相关函数 ====================
    @classmethod
    def is_daily_area(cls, area_id: str) -> bool:
        """判断是否为每日区域"""
        cls._load_config()
        return area_id in cls._AREAS_CONFIG.get("daily_areas", {})
    
    # ==================== 无尽塔相关函数 ====================
    
    @classmethod
    def get_tower_config(cls) -> Dict[str, Any]:
        """获取无尽塔配置"""
        cls._load_config()
        return cls._AREAS_CONFIG.get("tower", {}).copy()
    
    @classmethod
    def get_tower_max_floor(cls) -> int:
        """获取无尽塔最高层数"""
        tower_config = cls.get_tower_config()
        return tower_config.get("max_floor", 51)
    
    @classmethod
    def get_tower_name(cls) -> str:
        """获取无尽塔名称"""
        tower_config = cls.get_tower_config()
        config = tower_config.get("config", {})
        return config.get("name", "无尽塔")
    
    @classmethod
    def get_tower_description(cls) -> str:
        """获取无尽塔描述"""
        tower_config = cls.get_tower_config()
        config = tower_config.get("config", {})
        return config.get("description", "")
    
    @classmethod
    def get_tower_area_id(cls) -> str:
        """获取无尽塔区域ID"""
        tower_config = cls.get_tower_config()
        return tower_config.get("id", "sourth_endless_tower")
    
    @classmethod
    def is_tower_area(cls, area_id: str) -> bool:
        """判断是否为无尽塔区域"""
        tower_config = cls.get_tower_config()
        return area_id == tower_config.get("id", "sourth_endless_tower")
    
    @classmethod
    def get_tower_reward_floors(cls) -> List[int]:
        """获取无尽塔奖励层列表"""
        tower_config = cls.get_tower_config()
        config = tower_config.get("config", {})
        return config.get("reward_floors", [])
    
    @classmethod
    def is_tower_reward_floor(cls, floor: int) -> bool:
        """判断是否是无尽塔奖励层"""
        reward_floors = cls.get_tower_reward_floors()
        return floor in reward_floors
    
    @classmethod
    def get_tower_reward_for_floor(cls, floor: int) -> Dict[str, int]:
        """获取无尽塔指定层的奖励"""
        tower_config = cls.get_tower_config()
        config = tower_config.get("config", {})
        rewards = config.get("rewards", {})
        if floor > 50:
            return rewards.get("50", {}).copy()
        return rewards.get(str(floor), {}).copy()
    
    @classmethod
    def get_tower_random_template(cls) -> str:
        """获取无尽塔随机敌人模板"""
        tower_config = cls.get_tower_config()
        config = tower_config.get("config", {})
        templates = config.get("templates", ["qingwen_fox"])
        return random.choice(templates)
    
    @classmethod
    def get_tower_next_reward_floor(cls, current_floor: int) -> int:
        """获取下一个无尽塔奖励层"""
        reward_floors = cls.get_tower_reward_floors()
        for floor in reward_floors:
            if floor > current_floor:
                return floor
        return -1
    
    @classmethod
    def get_tower_floors_to_next_reward(cls, current_floor: int) -> int:
        """获取到下一个无尽塔奖励层需要的层数"""
        next_reward = cls.get_tower_next_reward_floor(current_floor)
        if next_reward == -1:
            return 0
        return next_reward - current_floor
