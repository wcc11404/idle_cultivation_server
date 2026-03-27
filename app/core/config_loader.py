import json
from pathlib import Path

CONFIG_DIR = Path(__file__).parent.parent.parent / "config"

_realms_data = None
_spells_data = None
_recipes_data = None
_items_data = None


def load_realms():
    global _realms_data
    if _realms_data is None:
        with open(CONFIG_DIR / "realms.json", "r", encoding="utf-8") as f:
            _realms_data = json.load(f)
    return _realms_data


def load_spells():
    global _spells_data
    if _spells_data is None:
        with open(CONFIG_DIR / "spells.json", "r", encoding="utf-8") as f:
            _spells_data = json.load(f)
    return _spells_data


def load_recipes():
    global _recipes_data
    if _recipes_data is None:
        with open(CONFIG_DIR / "recipes.json", "r", encoding="utf-8") as f:
            _recipes_data = json.load(f)
    return _recipes_data


def load_items():
    global _items_data
    if _items_data is None:
        with open(CONFIG_DIR / "items.json", "r", encoding="utf-8") as f:
            _items_data = json.load(f)
    return _items_data


def get_initial_realm():
    realms = load_realms()
    first_realm = realms["realm_order"][0]
    return first_realm


def get_initial_level_data():
    realms = load_realms()
    first_realm = realms["realm_order"][0]
    level_1_data = realms["realms"][first_realm]["levels"]["1"]
    return level_1_data


def get_initial_player_data(account_id: str) -> dict:
    initial_realm = get_initial_realm()
    level_data = get_initial_level_data()
    
    return {
        "account_info": {
            "nickname": f"修仙者{str(account_id)[:6]}",
            "avatar_id": "abstract",
            "title_id": "",
            "is_vip": False,
            "vip_expire_time": None
        },
        "player": {
            "realm": initial_realm,
            "realm_level": 1,
            "health": level_data["health"],
            "spirit_energy": 0.0,
            # "max_spirit_energy": level_data["max_spirit_energy"]
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
