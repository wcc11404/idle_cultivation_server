"""
炼丹数据系统

负责丹方配置的加载和查询
提供静态函数进行炼丹相关的查询
"""

import json
import os
from typing import Dict, Any, List


class RecipeData:
    """
    炼丹数据系统 - 负责丹方配置的加载和查询
    
    直接加载 recipes.json 配置
    """
    
    _RECIPES_CONFIG: Dict[str, Any] = {}
    _LOADED: bool = False
    
    @classmethod
    def _load_config(cls):
        """加载配置文件"""
        if cls._LOADED:
            return
        
        config_path = os.path.join(os.path.dirname(__file__), 'recipes.json')
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                cls._RECIPES_CONFIG = config.get('recipes', config)
            cls._LOADED = True
        except Exception as e:
            print(f"加载丹方配置失败: {e}")
    
    @classmethod
    def get_recipes_config(cls) -> Dict[str, Any]:
        """获取丹方配置"""
        cls._load_config()
        return cls._RECIPES_CONFIG
    
    @classmethod
    def get_recipe(cls, recipe_id: str) -> dict:
        """获取单个丹方"""
        cls._load_config()
        return cls._RECIPES_CONFIG.get(recipe_id, {})
    
    @classmethod
    def recipe_exists(cls, recipe_id: str) -> bool:
        """检查丹方是否存在"""
        cls._load_config()
        return recipe_id in cls._RECIPES_CONFIG
    
    @classmethod
    def get_recipe_name(cls, recipe_id: str) -> str:
        """获取丹方名称"""
        recipe = cls.get_recipe(recipe_id)
        return recipe.get("name", "未知丹方")
    
    @classmethod
    def get_recipe_success_value(cls, recipe_id: str) -> int:
        """获取丹方基础成功值"""
        recipe = cls.get_recipe(recipe_id)
        return recipe.get("success_value", 0)
    
    @classmethod
    def get_recipe_base_time(cls, recipe_id: str) -> float:
        """获取丹方基础耗时"""
        recipe = cls.get_recipe(recipe_id)
        return recipe.get("base_time", 0.0)
    
    @classmethod
    def get_recipe_materials(cls, recipe_id: str) -> Dict[str, int]:
        """获取丹方材料需求"""
        recipe = cls.get_recipe(recipe_id)
        return recipe.get("materials", {}).copy()
    
    @classmethod
    def get_recipe_product(cls, recipe_id: str) -> str:
        """获取丹方成品ID"""
        recipe = cls.get_recipe(recipe_id)
        return recipe.get("product", "")
    
    @classmethod
    def get_recipe_product_count(cls, recipe_id: str) -> int:
        """获取丹方成品数量"""
        recipe = cls.get_recipe(recipe_id)
        return recipe.get("product_count", 1)
    
    @classmethod
    def get_recipe_spirit_energy(cls, recipe_id: str) -> int:
        """获取丹方灵气消耗"""
        recipe = cls.get_recipe(recipe_id)
        return recipe.get("spirit_energy", 0)