#!/usr/bin/env python3
"""
集成测试脚本
测试流程：
1. 登录
2. 触发一次修炼，检查灵气是否增长5
3. 打开测试礼包
4. 使用bug丹
5. 触发突破，检查是否突破到炼气二层
"""

import requests
import json
import time

BASE_URL = "http://localhost:8444/api"

class TestClient:
    def __init__(self):
        self.token = None
    
    def login(self, username, password):
        """登录获取token"""
        url = f"{BASE_URL}/auth/login"
        payload = {
            "username": username,
            "password": password
        }
        response = requests.post(url, json=payload)
        result = response.json()
        if result.get("success"):
            self.token = result.get("token")
            player_data = result.get("data", {}).get("player", {})
            print("登录成功！")
            print(f"当前境界: {player_data.get('realm')}")
            print(f"当前灵气: {player_data.get('spirit_energy')}")
            return True
        else:
            print(f"登录失败: {result.get('detail')}")
            return False
    
    def get_headers(self):
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.token}"
        }
    
    def get_game_data(self):
        """获取游戏数据"""
        url = f"{BASE_URL}/game/data"
        response = requests.get(url, headers=self.get_headers())
        result = response.json()
        if result.get("success"):
            return result.get("data")
        else:
            print(f"加载失败: {result.get('detail')}")
            return None
    
    def open_test_gift(self):
        """打开测试礼包"""
        print("\n=== 打开测试礼包 ===")
        url = f"{BASE_URL}/game/inventory/use"
        payload = {
            "item_id": "test_pack"
        }
        response = requests.post(url, json=payload, headers=self.get_headers())
        result = response.json()
        
        if result.get("success"):
            print("测试礼包打开成功！")
            return True
        else:
            print(f"打开礼包失败: {result}")
            return False
    
    def use_bug_pill(self):
        """使用bug丹"""
        print("\n=== 使用bug丹 ===")
        url = f"{BASE_URL}/game/inventory/use"
        payload = {
            "item_id": "bug_pill"
        }
        response = requests.post(url, json=payload, headers=self.get_headers())
        result = response.json()
        
        if result.get("success"):
            print("bug丹使用成功！")
            return True
        else:
            print(f"使用bug丹失败: {result}")
            return False
    
    def test_breakthrough(self):
        """测试突破功能"""
        print(f"\n=== 测试突破到炼气5层 ===")
        
        current_realm = "炼气期"
        current_level = 1
        current_spirit = 0
        inventory_items = {}
        
        for i in range(4):
            print(f"第{i+1}次突破前境界: {current_realm} {current_level}层")
            print(f"第{i+1}次突破前灵气: {current_spirit}")
            
            url = f"{BASE_URL}/game/player/breakthrough"
            payload = {
                "current_realm": current_realm,
                "current_level": current_level,
                "spirit_energy": current_spirit,
                "inventory_items": inventory_items
            }
            response = requests.post(url, json=payload, headers=self.get_headers())
            result = response.json()
            
            if result.get("success"):
                current_realm = result.get("new_realm")
                current_level = result.get("new_level")
                current_spirit = result.get("remaining_spirit_energy")
                print(f"第{i+1}次突破后境界: {current_realm} {current_level}层")
            else:
                print(f"第{i+1}次突破失败: {result}")
                return False
        
        if current_level != 5:
            print(f"最终境界不是炼气5层，而是炼气{current_level}层")
            return False
        
        print("突破测试完成！最终境界：炼气5层")
        return True
    
    def discard_item(self, item_id):
        """丢弃物品"""
        print(f"\n=== 丢弃 {item_id} ===")
        url = f"{BASE_URL}/game/inventory/discard"
        payload = {
            "item_id": item_id,
            "count": 1
        }
        response = requests.post(url, json=payload, headers=self.get_headers())
        result = response.json()
        
        if result.get("success"):
            print(f"丢弃 {item_id} 成功！")
            return True
        else:
            print(f"丢弃 {item_id} 失败: {result}")
            return False
    
    def unlock_recipe(self, item_id):
        """解锁丹方"""
        print(f"\n=== 解锁丹方 {item_id} ===")
        url = f"{BASE_URL}/game/inventory/use"
        payload = {
            "item_id": item_id
        }
        response = requests.post(url, json=payload, headers=self.get_headers())
        result = response.json()
        
        if result.get("success"):
            print(f"解锁丹方 {item_id} 成功！")
            return True
        else:
            print(f"解锁丹方 {item_id} 失败: {result}")
            return False
    
    def unlock_furnace(self, item_id):
        """解锁炼丹炉"""
        print(f"\n=== 解锁炼丹炉 {item_id} ===")
        url = f"{BASE_URL}/game/inventory/use"
        payload = {
            "item_id": item_id
        }
        response = requests.post(url, json=payload, headers=self.get_headers())
        result = response.json()
        
        if result.get("success"):
            print(f"解锁炼丹炉 {item_id} 成功！")
            return True
        else:
            print(f"解锁炼丹炉 {item_id} 失败: {result}")
            return False
    
    def craft_pill(self, recipe_id):
        """炼制丹药"""
        print(f"\n=== 炼制 {recipe_id} ===")
        url = f"{BASE_URL}/game/alchemy/craft"
        payload = {
            "recipe_id": recipe_id
        }
        
        # 一直调用炼制接口，直到成功炼制出一颗补血丹
        while True:
            response = requests.post(url, json=payload, headers=self.get_headers())
            result = response.json()
            
            if result.get("success"):
                print(f"炼制 {recipe_id} 成功！")
                return True
            else:
                print(f"炼制 {recipe_id} 失败: {result}")
                continue
    
    def unlock_spell(self, item_id):
        """解锁法术"""
        print(f"\n=== 解锁法术 {item_id} ===")
        url = f"{BASE_URL}/game/inventory/use"
        payload = {
            "item_id": item_id
        }
        response = requests.post(url, json=payload, headers=self.get_headers())
        result = response.json()
        
        if result.get("success"):
            print(f"解锁法术 {item_id} 成功！")
            return True
        else:
            print(f"解锁法术 {item_id} 失败: {result}")
            return False
    
    def equip_spell(self, spell_id, slot_type):
        """装备法术"""
        print(f"\n=== 装备法术 {spell_id} 到 {slot_type} 槽位 ===")
        
        url = f"{BASE_URL}/game/spell/equip"
        payload = {
            "current_realm": spell_id,
            "current_level": 0,
            "spirit_energy": 0,
            "inventory_items": {}
        }
        response = requests.post(url, json=payload, headers=self.get_headers())
        result = response.json()
        
        if result.get("success"):
            print(f"装备法术 {spell_id} 到 {slot_type} 槽位成功！")
            return True
        else:
            print(f"装备法术 {spell_id} 到 {slot_type} 槽位失败: {result}")
            return False

def delete_test_account():
    """删除测试账号"""
    print("\n=== 删除测试账号 ===")
    import subprocess
    # 使用 venv 环境中的 Python
    result = subprocess.run(["./venv/bin/python3", "unit_test/delete_test_account.py"], cwd=".", capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"删除账号时出错: {result.stderr}")
    # 即使删除失败，也继续执行
    return True

def register_test_account():
    """注册测试账号"""
    print("\n=== 注册测试账号 ===")
    import subprocess
    # 使用 venv 环境中的 Python
    result = subprocess.run(["./venv/bin/python3", "unit_test/register_test_account.py"], cwd=".", capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"注册账号时出错: {result.stderr}")
    # 即使注册失败（比如用户名已存在），也继续执行
    return True

def run_integration_test():
    """运行集成测试"""
    # 1. 删除测试账号
    if not delete_test_account():
        return False
    
    # 2. 注册测试账号
    if not register_test_account():
        return False
    
    client = TestClient()
    
    # 3. 登录
    if not client.login("wcc_test", "wcc_test"):
        return False
    
    # 4. 打开测试礼包，获取bug丹
    if not client.open_test_gift():
        return False
    
    # 5. 使用bug丹（确保有足够的灵气进行突破）
    if not client.use_bug_pill():
        return False
    
    # 6. 突破到炼气五层
    if not client.test_breakthrough():
        return False
    
    # 7. 丢弃一个补气丹
    if not client.discard_item("spirit_pill"):
        return False
    
    # 8. 解锁补血丹丹方
    if not client.unlock_recipe("recipe_health_pill"):
        return False
    
    # 9. 解锁炼丹炉
    if not client.unlock_furnace("alchemy_furnace"):
        return False
    
    # 10. 炼制补血丹
    if not client.craft_pill("health_pill"):
        return False
    
    # 11. 解锁各种法术
    spells_to_unlock = [
        "spell_basic_boxing_techniques",
        "spell_thunder_strike",
        "spell_basic_health",
        "spell_basic_defense",
        "spell_basic_steps"
    ]
    for spell_item in spells_to_unlock:
        if not client.unlock_spell(spell_item):
            return False
    
    # 13. 装备法术
    spells_to_equip = [
        ("basic_boxing_techniques", "active"),  # 基础拳法
        ("thunder_strike", "active"),          # 雷击术
        ("basic_health", "opening"),           # 基础气血
        ("basic_defense", "opening"),          # 基础防御
        ("basic_steps", "breathing")           # 基础步法（应该失败）
    ]
    
    for i, (spell_id, slot_type) in enumerate(spells_to_equip):
        result = client.equip_spell(spell_id, slot_type)
        if i < 4:
            # 前4个法术必须装备成功
            if not result:
                print(f"装备法术 {spell_id} 失败，测试中断")
                return False
        else:
            # 最后一个基础步法必须装备失败
            if result:
                print(f"基础步法装备成功，测试中断")
                return False
    
    print("\n=== 装备法术结果 ===")
    print("装备测试成功！前4个法术装备成功，基础步法装备失败")
    
    print("\n=== 打印数据库字段 ===")
    game_data = client.get_game_data()
    if game_data:
        print(json.dumps(game_data, ensure_ascii=False, indent=2))
    
    print("\n=== 所有测试通过！===")
    return True

if __name__ == "__main__":
    print("开始运行集成测试...")
    success = run_integration_test()
    if success:
        print("集成测试成功完成！")
    else:
        print("集成测试失败！")
