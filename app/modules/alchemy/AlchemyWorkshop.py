"""
炼丹工坊

提供炼丹相关的静态功能，包括计算成功率、炼制时间、检查材料等
"""

from typing import Dict, Any, List, TYPE_CHECKING
import random

from .RecipeData import RecipeData

if TYPE_CHECKING:
    from ..player.PlayerData import PlayerData
    from ..spell.SpellSystem import SpellSystem
    from ..inventory.InventorySystem import InventorySystem
    from .AlchemySystem import AlchemySystem


class AlchemyWorkshop:
    """炼丹工坊 - 提供炼丹相关的静态功能"""
    
    @staticmethod
    def calculate_success_rate(alchemy_system: 'AlchemySystem', recipe_id: str, spell_system: 'SpellSystem' = None) -> int:
        """
        计算成功率（百分比）
        
        Args:
            alchemy_system: 炼丹系统实例
            recipe_id: 丹方ID
            spell_system: 术法系统实例
        
        Returns:
            成功率（1-100）
        """
        recipe_config = RecipeData.get_recipe(recipe_id)
        if not recipe_config:
            return 0
        
        base_value = recipe_config.get("success_value", 50)
        
        alchemy_bonus = alchemy_system.get_alchemy_bonus(spell_system)
        furnace_bonus = alchemy_system.get_furnace_bonus()
        
        final_value = base_value + alchemy_bonus["success_bonus"] + furnace_bonus["success_bonus"]
        
        return max(1, min(100, final_value))
    
    @staticmethod
    def calculate_craft_time(alchemy_system: 'AlchemySystem', recipe_id: str, spell_system: 'SpellSystem' = None) -> float:
        """
        计算炼制耗时（秒/颗）
        
        Args:
            alchemy_system: 炼丹系统实例
            recipe_id: 丹方ID
            spell_system: 术法系统实例
        
        Returns:
            每颗丹药的炼制时间
        """
        recipe_config = RecipeData.get_recipe(recipe_id)
        if not recipe_config:
            return 0.0
        
        base_time = recipe_config.get("base_time", 10.0)
        
        alchemy_bonus = alchemy_system.get_alchemy_bonus(spell_system)
        furnace_bonus = alchemy_system.get_furnace_bonus()
        
        final_speed = 1.0 + alchemy_bonus["speed_rate"] + furnace_bonus["speed_rate"]
        
        return base_time / final_speed
    
    @staticmethod
    def check_materials(recipe_id: str, count: int, inventory_system: 'InventorySystem') -> Dict[str, Any]:
        """
        检查材料是否足够
        
        Args:
            recipe_id: 丹方ID
            count: 炼制数量
            inventory_system: 背包系统实例
        
        Returns:
            {
                "enough": bool,
                "materials": dict,
                "missing": list
            }
        """
        result = {
            "enough": False,
            "materials": {},
            "missing": []
        }
        
        recipe_config = RecipeData.get_recipe(recipe_id)
        if not recipe_config:
            return result
        
        materials = recipe_config.get("materials", {})
        
        for material_id, material_count in materials.items():
            required = material_count * count
            has = inventory_system.get_item_count(material_id)
            result["materials"][material_id] = {
                "required": required,
                "has": has,
                "enough": has >= required
            }
            
            if has < required:
                result["missing"].append(material_id)
        
        result["enough"] = len(result["missing"]) == 0
        return result
    
    @staticmethod
    def check_spirit_energy(recipe_id: str, count: int, player_data: 'PlayerData') -> Dict[str, Any]:
        """
        检查灵气是否足够
        
        Args:
            recipe_id: 丹方ID
            count: 炼制数量
            player_data: 玩家数据
        
        Returns:
            {
                "enough": bool,
                "required": int,
                "has": int
            }
        """
        result = {
            "enough": True,
            "required": 0,
            "has": 0
        }
        
        recipe_config = RecipeData.get_recipe(recipe_id)
        if not recipe_config:
            return result
        
        spirit_per_pill = recipe_config.get("spirit_energy", 0)
        
        result["required"] = spirit_per_pill * count
        result["has"] = int(player_data.spirit_energy)
        result["enough"] = result["has"] >= result["required"]
        
        return result
    
    @staticmethod
    def craft_pills(alchemy_system: 'AlchemySystem', recipe_id: str, count: int, player_data: 'PlayerData', 
                   spell_system: 'SpellSystem' = None, inventory_system: 'InventorySystem' = None) -> Dict[str, Any]:
        """
        炼制丹药（批量，服务端直接完成）
        
        Args:
            alchemy_system: 炼丹系统实例
            recipe_id: 丹方ID
            count: 炼制数量
            player_data: 玩家数据
            spell_system: 术法系统实例
            inventory_system: 背包系统实例
        
        Returns:
            {
                "success": bool,
                "reason": str,
                "success_count": int,
                "fail_count": int,
                "products": dict
            }
        """
        if not alchemy_system.has_learned_recipe(recipe_id):
            return {
                "success": False,
                "reason": "未学会该丹方",
                "success_count": 0,
                "fail_count": 0,
                "products": {}
            }
        
        if not inventory_system:
            return {
                "success": False,
                "reason": "背包系统未初始化",
                "success_count": 0,
                "fail_count": 0,
                "products": {}
            }
        
        material_check = AlchemyWorkshop.check_materials(recipe_id, count, inventory_system)
        if not material_check["enough"]:
            return {
                "success": False,
                "reason": "材料不足",
                "success_count": 0,
                "fail_count": 0,
                "products": {}
            }
        
        spirit_check = AlchemyWorkshop.check_spirit_energy(recipe_id, count, player_data)
        if not spirit_check["enough"]:
            return {
                "success": False,
                "reason": "灵气不足",
                "success_count": 0,
                "fail_count": 0,
                "products": {}
            }
        
        recipe_config = RecipeData.get_recipe(recipe_id)
        materials = recipe_config.get("materials", {})
        spirit_per_pill = recipe_config.get("spirit_energy", 0)
        product_id = recipe_config.get("product", "")
        product_count_per_pill = recipe_config.get("product_count", 1)
        
        for material_id, material_count in materials.items():
            inventory_system.remove_item(material_id, material_count * count)
        
        player_data.reduce_spirit_energy(float(spirit_per_pill * count))
        
        success_rate = AlchemyWorkshop.calculate_success_rate(alchemy_system, recipe_id, spell_system)
        success_count = 0
        fail_count = 0
        products = {}
        
        for i in range(count):
            roll = random.random() * 100.0
            
            if spell_system:
                spell_system.add_spell_use_count("alchemy")
            
            if roll <= success_rate:
                success_count += 1
                if product_id:
                    if product_id in products:
                        products[product_id] += product_count_per_pill
                    else:
                        products[product_id] = product_count_per_pill
            else:
                fail_count += 1
                AlchemyWorkshop._return_half_materials(materials, 1, inventory_system)
        
        for prod_id, prod_count in products.items():
            inventory_system.add_item(prod_id, prod_count)
        
        return {
            "success": True,
            "reason": "炼制完成",
            "success_count": success_count,
            "fail_count": fail_count,
            "products": products
        }
    
    @staticmethod
    def _return_half_materials(materials: Dict[str, int], fail_count: int, inventory_system: 'InventorySystem'):
        """返还一半材料（失败时）"""
        for material_id, material_count in materials.items():
            return_amount = int(material_count * fail_count / 2.0)
            if return_amount > 0:
                inventory_system.add_item(material_id, return_amount)