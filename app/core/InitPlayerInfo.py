"""
初始玩家信息生成器

负责生成账号创建时的初始玩家数据
"""

import json
from typing import Dict, Any
from pathlib import Path

from app.modules.spell.SpellSystem import SpellSystem
from app.modules.inventory.InventorySystem import InventorySystem
from app.modules.alchemy.AlchemySystem import AlchemySystem
from app.modules.lianli.LianliSystem import LianliSystem
from app.modules.player.PlayerSystem import PlayerSystem
from app.modules.cultivation.RealmData import RealmData
from app.modules.account.AccountSystem import AccountSystem


def get_initial_player_data(account_id: str) -> dict:
    """
    获取初始玩家数据
    
    Args:
        account_id: 账号ID
    
    Returns:
        初始玩家数据字典
    """
    # 创建各个系统实例
    spell_system = SpellSystem()
    inventory_system = InventorySystem()
    alchemy_system = AlchemySystem()
    lianli_system = LianliSystem()
    account_system = AccountSystem.create_with_nickname(f"修仙者{str(account_id)[:6]}")
    
    # 创建PlayerSystem实例
    first_realm = RealmData.get_first_realm()
    player_data = PlayerSystem(
        health=float(RealmData.get_realm_attributes(first_realm, 1).get("max_health", 100)),
        spirit_energy=0.0,
        realm=first_realm,
        realm_level=1,
        spell_system=spell_system
    )
    
    # 背包系统添加初始物品
    inventory_system.add_item("starter_pack", 1)
    inventory_system.add_item("test_pack", 1)
    
    return {
        "account_info": account_system.to_dict(),
        "player": player_data.to_dict(),
        "inventory": inventory_system.to_dict(),
        "spell_system": spell_system.to_dict(),
        "alchemy_system": alchemy_system.to_dict(),
        "lianli_system": lianli_system.to_dict(),
        "version": "1.0"
    }
