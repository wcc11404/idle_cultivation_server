"""
历练敌人数据系统

负责敌人模板配置的加载和查询
提供静态函数进行敌人相关的查询
"""

import json
import os
import math
import random
from typing import Dict, Any, List
from pathlib import Path


class EnemiesData:
    """
    历练敌人数据系统 - 负责敌人模板配置的加载和查询
    
    直接加载 enemies.json 配置
    """
    
    _ENEMIES_CONFIG: Dict[str, Any] = {}
    _LOADED: bool = False
    
    @classmethod
    def _load_config(cls):
        """加载配置文件"""
        if cls._LOADED:
            return
        
        config_path = Path(__file__).resolve().parents[2] / 'content' / 'lianli' / 'enemies.json'
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cls._ENEMIES_CONFIG = json.load(f)
            cls._LOADED = True
        except Exception as e:
            print(f"加载敌人配置失败: {e}")
    
    @classmethod
    def get_enemies_config(cls) -> Dict[str, Any]:
        """获取敌人配置"""
        cls._load_config()
        return cls._ENEMIES_CONFIG
    
    @classmethod
    def get_enemy_template(cls, template_id: str) -> dict:
        """获取敌人模板"""
        cls._load_config()
        if "templates" in cls._ENEMIES_CONFIG:
            return cls._ENEMIES_CONFIG["templates"].get(template_id, {}).copy()
        return cls._ENEMIES_CONFIG.get(template_id, {}).copy()
    
    @classmethod
    def get_template_name(cls, template_id: str) -> str:
        """获取敌人模板名称"""
        template = cls.get_enemy_template(template_id)
        return template.get("name", "未知敌人")
    
    @classmethod
    def get_all_template_ids(cls) -> List[str]:
        """获取所有敌人模板ID列表"""
        cls._load_config()
        if "templates" in cls._ENEMIES_CONFIG:
            return list(cls._ENEMIES_CONFIG["templates"].keys())
        return list(cls._ENEMIES_CONFIG.keys())
    
    @classmethod
    def can_appear_in_tower(cls, template_id: str) -> bool:
        """判断敌人是否可以在无尽塔中出现"""
        template = cls.get_enemy_template(template_id)
        return template.get("can_appear_in_tower", False)
    
    @classmethod
    def generate_enemy(cls, template_id: str, level: int) -> Dict[str, Any]:
        """
        根据模板生成敌人
        
        Args:
            template_id: 敌人模板ID
            level: 敌人等级
        
        Returns:
            敌人数据字典（与客户端对齐）
        """
        template = cls.get_enemy_template(template_id)
        if not template:
            return {}
        
        growth = template.get("growth", {})
        
        health_base = growth.get("health_base", 20)
        health_growth = growth.get("health_growth", 1.08)
        health = int(health_base * math.pow(health_growth, level - 1))
        
        attack_base = growth.get("attack_base", 4)
        attack_growth = growth.get("attack_growth", 1.06)
        attack = int(attack_base * math.pow(attack_growth, level - 1))
        
        defense_base = growth.get("defense_base", 2)
        defense_growth = growth.get("defense_growth", 1.04)
        defense = int(defense_base * math.pow(defense_growth, level - 1))
        
        speed_base = growth.get("speed_base", 5)
        speed_growth = growth.get("speed_growth", 0.01)
        speed = speed_base * (1 + speed_growth * (level - 1))
        
        name_variants = template.get("name_variants", [template.get("name", "敌人")])
        enemy_name = template.get("name", "敌人")
        if name_variants:
            enemy_name = random.choice(name_variants)
        
        enemy_data = {
            "template_id": template_id,
            "name": enemy_name,
            "level": level,
            "stats": {
                "health": health,
                "attack": attack,
                "defense": defense,
                "speed": speed
            }
        }
        
        return enemy_data
