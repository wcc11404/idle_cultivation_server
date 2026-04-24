"""
初始玩家信息生成器

负责生成账号创建时的初始玩家数据
"""

from datetime import datetime
from typing import Optional

from app.db.Models import Account, PlayerData
from app.modules.spell.SpellSystem import SpellSystem
from app.modules.inventory.InventorySystem import InventorySystem
from app.modules.alchemy.AlchemySystem import AlchemySystem
from app.modules.lianli.LianliSystem import LianliSystem
from app.modules.herb.HerbGatherSystem import HerbGatherSystem
from app.modules.player.PlayerSystem import PlayerSystem
from app.modules.cultivation.RealmData import RealmData
from app.modules.account.AccountSystem import AccountSystem
from unit_test.support.TestSupportConfig import (
    TEST_PACK_ITEM_ID,
)


def should_grant_test_pack(username: str) -> bool:
    return True


def get_initial_player_data(account_id: str, username: str = "", include_test_pack: Optional[bool] = None) -> dict:
    """
    获取初始玩家数据
    
    Args:
        account_id: 账号ID
        username: 用户名
        include_test_pack: 是否包含测试礼包，默认按用户名判断
    
    Returns:
        初始玩家数据字典
    """
    if include_test_pack is None:
        include_test_pack = should_grant_test_pack(username)

    # 创建各个系统实例
    spell_system = SpellSystem()
    inventory_system = InventorySystem()
    alchemy_system = AlchemySystem()
    lianli_system = LianliSystem()
    herb_system = HerbGatherSystem()
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
    if include_test_pack:
        inventory_system.add_item(TEST_PACK_ITEM_ID, 1)
    return {
        "account_info": account_system.to_dict(),
        "player": player_data.to_dict(),
        "inventory": inventory_system.to_dict(),
        "spell_system": spell_system.to_dict(),
        "alchemy_system": alchemy_system.to_dict(),
        "lianli_system": lianli_system.to_dict(),
        "herb_system": herb_system.to_dict(),
        "version": "1.0"
    }


async def create_initial_player_data_record(
    account: Account,
    last_online_at: datetime,
    include_test_pack: Optional[bool] = None
) -> PlayerData:
    initial_data = get_initial_player_data(str(account.id), account.username, include_test_pack=include_test_pack)
    return await PlayerData.create(
        account_id=account.id,
        data=initial_data,
        last_online_at=last_online_at
    )


async def reset_player_data_record(
    account: Account,
    player_data: PlayerData,
    last_online_at: datetime,
    include_test_pack: Optional[bool] = None
) -> PlayerData:
    player_data.data = get_initial_player_data(str(account.id), account.username, include_test_pack=include_test_pack)
    player_data.last_online_at = last_online_at
    await player_data.save()
    return player_data
