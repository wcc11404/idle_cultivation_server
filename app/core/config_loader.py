"""
配置加载器

负责加载初始玩家数据
"""

import json
from pathlib import Path

CONFIG_DIR = Path(__file__).parent.parent.parent / "config"


def get_initial_player_data(account_id: str) -> dict:
    """
    获取初始玩家数据
    
    Args:
        account_id: 账号ID
    
    Returns:
        初始玩家数据字典
    """
    realms_path = CONFIG_DIR / "realms.json"
    
    with open(realms_path, "r", encoding="utf-8") as f:
        realms_data = json.load(f)
    
    first_realm = realms_data["realm_order"][0]
    level_data = realms_data["realms"][first_realm]["levels"]["1"]
    
    return {
        "account_info": {
            "nickname": f"修仙者{str(account_id)[:6]}",
            "avatar_id": "abstract",
            "title_id": "",
            "is_vip": False,
            "vip_expire_time": None
        },
        "player": {
            "realm": first_realm,
            "realm_level": 1,
            "health": level_data["health"],
            "spirit_energy": 0.0
        },
        "inventory": {
            "capacity": 50,
            "slots": {
                "0": {
                    "count": 1,
                    "id": "starter_pack"
                },
                "1": {
                    "count": 1,
                    "id": "test_pack"
                }
            }
        },
        "spell_system": {
            "player_spells": {},
            "equipped_spells": {
                "0": [],
                "1": [],
                "2": []
            }
        },
        "alchemy_system": {
            "equipped_furnace_id": "",
            "learned_recipes": []
        },
        "lianli_system": {
            "tower_highest_floor": 0,
            "daily_dungeon_data": {
                "foundation_herb_cave": {
                    "max_count": 3,
                    "remaining_count": 3
                }
            }
        },
        "version": "1.0"
    }
