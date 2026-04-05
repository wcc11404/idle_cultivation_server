#!/usr/bin/env python3
"""
集成测试脚本
测试流程：
1. 删除测试账号
2. 注册测试账号
3. 登录
4. 测试使用不存在的物品（应该失败）
5. 测试丢弃不存在的物品（应该失败）
6. 开始修炼，测试防作弊机制
7. 打开测试礼包
8. 使用bug丹
9. 等待5秒后上报修炼
10. 突破到筑基一层
11. 丢弃一个补气丹
12. 解锁所有丹方
13. 解锁炼丹炉
14. 测试互斥：开始炼丹（应该失败）
15. 停止修炼
16. 炼制补血丹
17. 解锁所有法术
18. 装备法术
19. 测试历练系统
20. 测试排行榜API
"""

import requests
import json
import time
import uuid

BASE_URL = "http://localhost:8444/api"

class TestClient:
    def __init__(self):
        self.token = None
    
    def _generate_request_params(self):
        """生成通用请求参数"""
        return {
            "operation_id": str(uuid.uuid4()),
            "timestamp": time.time()
        }
    
    def login(self, username, password):
        """登录获取token"""
        url = f"{BASE_URL}/auth/login"
        payload = {
            "username": username,
            "password": password,
            **self._generate_request_params()
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
            "item_id": "test_pack",
            **self._generate_request_params()
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
            "item_id": "bug_pill",
            **self._generate_request_params()
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
        print(f"\n=== 测试突破到筑基一层 ===")
        
        current_realm = "炼气期"
        current_level = 1
        current_spirit = 0
        inventory_items = {}
        
        for i in range(10):
            print(f"第{i+1}次突破前境界: {current_realm} {current_level}层")
            print(f"第{i+1}次突破前灵气: {current_spirit}")
            
            url = f"{BASE_URL}/game/player/breakthrough"
            payload = {
                "current_realm": current_realm,
                "current_level": current_level,
                "spirit_energy": current_spirit,
                "inventory_items": inventory_items,
                **self._generate_request_params()
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
        
        if current_level != 1 and current_realm != "筑基期":
            print(f"最终境界不是筑基一层，而是{current_realm} {current_level}层")
            return False
        
        print("突破测试完成！最终境界：筑基一层")
        return True
    
    def discard_item(self, item_id):
        """丢弃物品"""
        print(f"\n=== 丢弃 {item_id} ===")
        url = f"{BASE_URL}/game/inventory/discard"
        payload = {
            "item_id": item_id,
            "count": 1,
            **self._generate_request_params()
        }
        response = requests.post(url, json=payload, headers=self.get_headers())
        result = response.json()
        
        if result.get("success"):
            print(f"丢弃 {item_id} 成功！")
            return True
        else:
            print(f"丢弃 {item_id} 失败: {result}")
            return False
    
    def stop_alchemy(self):
        """停止炼丹"""
        print("\n=== 停止炼丹 ===")
        url = f"{BASE_URL}/game/alchemy/stop"
        payload = self._generate_request_params()
        response = requests.post(url, json=payload, headers=self.get_headers())
        result = response.json()
        
        if result.get("success"):
            print("停止炼丹成功！")
            return True
        else:
            print(f"停止炼丹失败: {result}")
            return False
    
    def unlock_recipe(self, item_id):
        """解锁丹方"""
        print(f"\n=== 解锁丹方 {item_id} ===")
        url = f"{BASE_URL}/game/inventory/use"
        payload = {
            "item_id": item_id,
            **self._generate_request_params()
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
            "item_id": item_id,
            **self._generate_request_params()
        }
        response = requests.post(url, json=payload, headers=self.get_headers())
        result = response.json()
        
        if result.get("success"):
            print(f"解锁炼丹炉 {item_id} 成功！")
            return True
        else:
            print(f"解锁炼丹炉 {item_id} 失败: {result}")
            return False
    
    def start_alchemy(self):
        """开始炼丹"""
        print("\n=== 开始炼丹 ===")
        url = f"{BASE_URL}/game/alchemy/start"
        payload = self._generate_request_params()
        response = requests.post(url, json=payload, headers=self.get_headers())
        result = response.json()
        
        if result.get("success"):
            print("开始炼丹成功！")
            return True
        else:
            print(f"开始炼丹失败: {result}")
            return False
    
    def craft_pill(self, recipe_id):
        """炼制丹药"""
        print(f"\n=== 炼制 {recipe_id} ===")
        
        url_start = f"{BASE_URL}/game/alchemy/start"
        payload_start = self._generate_request_params()
        response = requests.post(url_start, json=payload_start, headers=self.get_headers())
        result = response.json()
        
        if not result.get("success"):
            print(f"开始炼丹失败: {result}")
            return False
        
        print("开始炼丹成功，等待3秒...")
        time.sleep(3)
        
        url_report = f"{BASE_URL}/game/alchemy/report"
        payload_report = {
            "recipe_id": recipe_id,
            "count": 1,
            **self._generate_request_params()
        }
        response = requests.post(url_report, json=payload_report, headers=self.get_headers())
        result = response.json()
        
        if result.get("success"):
            success_count = result.get('success_count', 0)
            fail_count = result.get('fail_count', 0)
            print(f"炼制 {recipe_id} 完成！成功{success_count}颗，失败{fail_count}颗")
            print(f"获得丹药: {result.get('products', {})}")
            print(f"消耗材料: {result.get('materials_consumed', {})}")
            
            if not self.stop_alchemy():
                return False
            
            return True
        else:
            print(f"炼制 {recipe_id} 失败: {result}")
            return False
    
    def unlock_spell(self, item_id):
        """解锁法术"""
        print(f"\n=== 解锁法术 {item_id} ===")
        url = f"{BASE_URL}/game/inventory/use"
        payload = {
            "item_id": item_id,
            **self._generate_request_params()
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
            "spell_id": spell_id,
            **self._generate_request_params()
        }
        response = requests.post(url, json=payload, headers=self.get_headers())
        result = response.json()
        
        if result.get("success"):
            print(f"装备法术 {spell_id} 到 {slot_type} 槽位成功！")
            return True
        else:
            print(f"装备法术 {spell_id} 到 {slot_type} 槽位失败: {result}")
            return False
    
    def start_cultivation(self):
        """开始修炼"""
        print("\n=== 开始修炼 ===")
        url = f"{BASE_URL}/game/player/cultivation/start"
        payload = self._generate_request_params()
        response = requests.post(url, json=payload, headers=self.get_headers())
        result = response.json()
        
        if result.get("success"):
            print("开始修炼成功！")
            return True
        else:
            print(f"开始修炼失败: {result}")
            return False
    
    def report_cultivation(self, count):
        """上报修炼"""
        print(f"\n=== 上报修炼 (count={count}) ===")
        url = f"{BASE_URL}/game/player/cultivation/report"
        payload = {
            "count": count,
            **self._generate_request_params()
        }
        response = requests.post(url, json=payload, headers=self.get_headers())
        result = response.json()
        
        if result.get("success"):
            print(f"上报修炼成功！")
            print(f"灵气增加: {result.get('spirit_gained')}")
            print(f"气血增加: {result.get('health_gained')}")
            print(f"术法使用次数增加: {result.get('used_count_gained')}")
            print(f"消息: {result.get('message')}")
            return True
        else:
            print(f"上报修炼失败: {result}")
            return False
    
    def stop_cultivation(self):
        """停止修炼"""
        print("\n=== 停止修炼 ===")
        url = f"{BASE_URL}/game/player/cultivation/stop"
        payload = self._generate_request_params()
        response = requests.post(url, json=payload, headers=self.get_headers())
        result = response.json()
        
        if result.get("success"):
            print("停止修炼成功！")
            return True
        else:
            print(f"停止修炼失败: {result}")
            return False
    
    def simulate_battle(self, area_id):
        """模拟战斗"""
        print(f"\n=== 模拟战斗 (area_id={area_id}) ===")
        url = f"{BASE_URL}/game/lianli/simulate"
        payload = {
            "area_id": area_id,
            **self._generate_request_params()
        }
        response = requests.post(url, json=payload, headers=self.get_headers())
        result = response.json()
        
        if result.get("success"):
            print(f"战斗模拟成功！")
            print(f"战斗时长: {result.get('total_time'):.2f}秒")
            print(f"战斗回合数: {len(result.get('battle_timeline', []))}")
            print(f"是否胜利: {result.get('victory')}")
            print(f"掉落物品: {result.get('loot', [])}")
            return result
        else:
            print(f"战斗模拟失败: {result}")
            return None
    
    def finish_battle(self, speed=1.0, index=None):
        """结算战斗"""
        print(f"\n=== 结算战斗 (speed={speed}, index={index}) ===")
        url = f"{BASE_URL}/game/lianli/finish"
        payload = {
            "speed": speed,
            **self._generate_request_params()
        }
        if index is not None:
            payload["index"] = index
        
        response = requests.post(url, json=payload, headers=self.get_headers())
        result = response.json()
        
        if result.get("success"):
            print(f"战斗结算成功！")
            print(f"结算进度: {result.get('settled_index')}/{result.get('total_index')}")
            print(f"玩家血量: {result.get('player_health_after')}")
            print(f"获得掉落: {result.get('loot_gained', [])}")
            print(f"获得经验: {result.get('exp_gained')}")
            return True
        else:
            print(f"战斗结算失败: {result}")
            return False
    
    def get_rank(self, server_id="default"):
        """获取排行榜"""
        print(f"\n=== 获取排行榜 (server_id={server_id}) ===")
        url = f"{BASE_URL}/game/rank"
        params = {"server_id": server_id}
        
        response = requests.get(url, params=params)
        result = response.json()
        
        if result.get("success"):
            print(f"获取排行榜成功！")
            ranks = result.get("ranks", [])
            print(f"排行榜数量: {len(ranks)}")
            if ranks:
                print("\n前10名:")
                for rank_item in ranks[:10]:
                    print(f"  {rank_item.get('rank')}. {rank_item.get('nickname')} - {rank_item.get('realm')}{rank_item.get('level')}层 - 灵气: {rank_item.get('spirit_energy')}")
            return result
        else:
            print(f"获取排行榜失败: {result}")
            return None


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
    if not client.login("wcc_test", "wcc_test123456"):
        return False
    
    # 4. 测试使用不存在的物品（应该失败）
    print("\n=== 测试使用不存在的bug丹（应该失败） ===")
    result = client.use_bug_pill()
    if result:
        print("测试失败：使用不存在的bug丹应该失败")
        return False
    print("测试成功：使用不存在的bug丹被正确拒绝")
    
    # 5. 测试丢弃不存在的物品（应该失败）
    print("\n=== 测试丢弃不存在的补血丹（应该失败） ===")
    result = client.discard_item("health_pill")
    if result:
        print("测试失败：丢弃不存在的补血丹应该失败")
        return False
    print("测试成功：丢弃不存在的补血丹被正确拒绝")
    
    # 6. 开始修炼
    if not client.start_cultivation():
        return False
    
    # 7. 测试防作弊：立即上报5次（应该失败）
    print("\n=== 测试防作弊：立即上报5次（应该失败） ===")
    result = client.report_cultivation(count=5)
    if result:
        print("测试失败：立即上报应该被拒绝")
        return False
    print("测试成功：立即上报被正确拒绝")
    
    # 8. 等待5秒
    print("\n=== 等待5秒 ===")
    time.sleep(5)
    
    # 9. 上报5次（应该成功）
    if not client.report_cultivation(count=5):
        return False
    
    # 10. 打开测试礼包，获取bug丹
    if not client.open_test_gift():
        return False
    
    # 11. 使用bug丹（确保有足够的灵气进行突破）
    if not client.use_bug_pill():
        return False
    
    # 12. 突破到筑基一层
    if not client.test_breakthrough():
        return False
    
    # 13. 丢弃一个补气丹
    if not client.discard_item("spirit_pill"):
        return False
    
    # 14. 解锁所有丹方
    recipes_to_unlock = [
        "recipe_health_pill",
        "recipe_spirit_pill",
        "recipe_foundation_pill",
        "recipe_golden_core_pill"
    ]
    for recipe_item in recipes_to_unlock:
        if not client.unlock_recipe(recipe_item):
            return False
    
    # 15. 解锁炼丹炉
    if not client.unlock_furnace("alchemy_furnace"):
        return False
    
    # 16. 测试互斥：开始炼丹（应该失败，因为正在修炼）
    print("\n=== 测试互斥：开始炼丹（应该失败） ===")
    result = client.start_alchemy()
    if result:
        print("测试失败：修炼中应该无法开始炼丹")
        return False
    print("测试成功：修炼中无法开始炼丹")
    
    # 17. 停止修炼
    if not client.stop_cultivation():
        return False
    
    # 18. 炼制补血丹
    if not client.craft_pill("health_pill"):
        return False
    
    # 15. 解锁所有法术
    spells_to_unlock = [
        "spell_basic_breathing",
        "spell_basic_boxing_techniques",
        "spell_thunder_strike",
        "spell_basic_health",
        "spell_basic_defense",
        "spell_basic_steps",
        "spell_alchemy"
    ]
    for spell_item in spells_to_unlock:
        if not client.unlock_spell(spell_item):
            return False
    
    # 16. 装备法术
    spells_to_equip = [
        ("basic_boxing_techniques", "active"),  # 基础拳法
        ("thunder_strike", "active"),          # 雷击术
        ("basic_health", "opening"),           # 基础气血
        ("basic_defense", "opening"),          # 基础防御
        ("basic_breathing", "breathing"),      # 基础吐纳
        ("basic_steps", "breathing")           # 基础步法（应该失败）
    ]
    
    for i, (spell_id, slot_type) in enumerate(spells_to_equip):
        result = client.equip_spell(spell_id, slot_type)
        if i < 5:
            # 前5个法术必须装备成功
            if not result:
                print(f"装备法术 {spell_id} 失败，测试中断")
                return False
        else:
            # 最后一个基础步法必须装备失败
            if result:
                print(f"基础步法装备成功，测试中断")
                return False
    
    print("\n=== 装备法术结果 ===")
    print("装备测试成功！前5个法术装备成功，基础步法装备失败")
    
    # 19. 测试历练系统
    print("\n=== 测试历练系统 ===")
    
    # 19.1 模拟战斗
    battle_result = client.simulate_battle("foundation_herb_cave")
    if not battle_result:
        print("战斗模拟失败，测试中断")
        return False
    
    # 19.2 立即结算（应该失败）
    print("\n=== 立即结算战斗（应该失败） ===")
    result = client.finish_battle(speed=1.0)
    if result:
        print("测试失败：立即结算应该被拒绝")
        return False
    print("测试成功：立即结算被正确拒绝")
    
    # 19.3 根据 battle_timeline 播放战斗
    battle_timeline = battle_result.get("battle_timeline", [])
    total_time = battle_result.get("total_time", 0)
    
    print(f"\n=== 播放战斗回合 ===")
    print(f"总时长: {total_time:.2f}秒")
    print(f"总回合数: {len(battle_timeline)}")
    
    if battle_timeline:
        prev_time = 0
        for i, action in enumerate(battle_timeline):
            current_time = action.get("time", 0)
            wait_time = current_time - prev_time
            
            if wait_time > 0:
                time.sleep(wait_time)
            
            action_type = action.get("type", "unknown")
            info = action.get("info", {})
            
            if action_type == "player_action":
                spell_id = info.get("spell_id", "unknown")
                effect_type = info.get("effect_type", "unknown")
                damage = info.get("damage", 0)
                heal = info.get("heal", 0)
                print(f"[{current_time:.2f}s] 回合{i+1} - 玩家行动: {spell_id} -> {effect_type} (伤害:{damage}, 治疗:{heal})")
            elif action_type == "enemy_action":
                enemy_name = info.get("enemy_name", "unknown")
                damage = info.get("damage", 0)
                print(f"[{current_time:.2f}s] 回合{i+1} - 敌人行动: {enemy_name} 攻击 (伤害:{damage})")
            else:
                print(f"[{current_time:.2f}s] 回合{i+1} - {action_type}: {info}")
            
            prev_time = current_time
    
    # 19.4 结算战斗
    if not client.finish_battle(speed=1.0):
        print("战斗结算失败，测试中断")
        return False
    
    # 20. 测试排行榜API
    print("\n=== 测试排行榜API ===")
    rank_result = client.get_rank()
    if not rank_result:
        print("获取排行榜失败，测试中断")
        return False
    
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
