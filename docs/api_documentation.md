# 修仙挂机游戏服务端 API 文档

## 文档说明

### 通用请求参数

**除注册接口外，所有接口都需要以下参数：**

#### 请求头参数

| 字段          | 类型   | 必选 | 说明                    |
| ------------- | ------ | ---- | ----------------------- |
| Authorization | string | 是   | Bearer {token}          |

#### 请求体通用参数

| 字段         | 类型   | 必选 | 说明                          |
| ------------ | ------ | ---- | ----------------------------- |
| operation_id | string | 是   | 客户端生成的UUID，用于追踪请求 |
| timestamp    | number | 是   | 客户端触发操作的时间戳（秒）   |

### 通用响应格式

#### 成功响应

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "...": "其他数据"
}
```

#### 失败响应

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "message": "错误信息"
}
```

#### 异常响应

```json
{
  "detail": "错误信息"
}
```

---

### 9.7 battle_timeline 结构

战斗时间线是一个数组，每个元素代表一个战斗行动：

#### 玩家行动（player_action）

```json
{
  "time": 2.0,
  "type": "player_action",
  "info": {
    "spell_id": "basic_boxing_techniques",
    "effect_type": "instant_damage",
    "damage": 6.6,
    "heal": 0,
    "target_health_after": 23.4
  }
}
```

**info 字段说明**：

| 字段               | 类型   | 说明                           |
| ------------------ | ------ | ------------------------------ |
| spell_id           | string | 术法ID（norm_attack为普通攻击）|
| effect_type        | string | 效果类型                       |
| damage             | number | 伤害值（保留两位小数）         |
| heal               | number | 治疗值（保留两位小数）         |
| target_health_after| number | 目标剩余生命值                 |

**effect_type 类型**：

- `instant_damage`：即时伤害
- `heal`：治疗
- `undispellable_buff`：不可驱散的增益效果

#### 敌人行动（enemy_action）

```json
{
  "time": 2.3,
  "type": "enemy_action",
  "info": {
    "enemy_name": "野猪",
    "spell_id": "norm_attack",
    "damage": 1.0,
    "target_health_after": 75.0
  }
}
```

**info 字段说明**：

| 字段               | 类型   | 说明                   |
| ------------------ | ------ | ---------------------- |
| enemy_name         | string | 敌人名称               |
| spell_id           | string | 术法ID（通常为norm_attack）|
| damage             | number | 伤害值（保留两位小数） |
| target_health_after| number | 目标剩余生命值         |

---

## 1. 认证系统 API

### 1.1 注册账号

- **接口地址**：`POST /api/auth/register`
- **功能**：注册新账号
- **认证**：无需认证

#### 请求参数

| 字段     | 类型   | 必选 | 说明           |
| -------- | ------ | ---- | -------------- |
| username | string | 是   | 用户名（20字符以内） |
| password | string | 是   | 密码           |

#### 成功响应

```json
{
  "success": true,
  "account_id": "uuid",
  "message": "注册成功"
}
```

#### 失败响应

```json
{
  "success": false,
  "message": "用户名已存在"
}
```

---

### 1.2 登录账号

- **接口地址**：`POST /api/auth/login`
- **功能**：登录账号并获取 JWT Token
- **认证**：无需认证

#### 请求参数

| 字段         | 类型   | 必选 | 说明                          |
| ------------ | ------ | ---- | ----------------------------- |
| username     | string | 是   | 用户名                        |
| password     | string | 是   | 密码                          |
| operation_id | string | 是   | 客户端生成的UUID              |
| timestamp    | number | 是   | 客户端触发操作的时间戳（秒）  |

#### 成功响应

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "token": "jwt_token",
  "expires_in": 604800,
  "account_info": {
    "id": "uuid",
    "username": "testuser",
    "server_id": "default"
  },
  "data": {
    "account_info": {
      "nickname": "修仙者123456",
      "avatar_id": "abstract",
      "title_id": "",
      "is_vip": false,
      "vip_expire_time": null,
      "suspicious_operations_count": 0
    },
    "player": {
      "realm": "炼气期",
      "realm_level": 1,
      "health": 50.0,
      "spirit_energy": 0.0,
      "is_cultivating": false,
      "last_cultivation_report_time": 0.0
    },
    "inventory": {
      "slots": {},
      "capacity": 50
    },
    "spell_system": {
      "slot_limits": {
        "active": 2,
        "opening": 2,
        "breathing": 1
      },
      "player_spells": {},
      "equipped_spells": {
        "active": [],
        "opening": [],
        "breathing": []
      }
    },
    "alchemy_system": {
      "learned_recipes": [],
      "equipped_furnace_id": ""
    },
    "lianli_system": {
      "daily_dungeon_data": {
        "foundation_herb_cave": {
          "max_count": 3,
          "remaining_count": 3
        }
      },
      "tower_highest_floor": 0
    }
  }
}
```

#### 失败响应

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "message": "用户名或密码错误"
}
```

---

### 1.3 Token 续期

- **接口地址**：`POST /api/auth/refresh`
- **功能**：刷新 JWT Token
- **认证**：需要认证

#### 请求参数

| 字段         | 类型   | 必选 | 说明                          |
| ------------ | ------ | ---- | ----------------------------- |
| operation_id | string | 是   | 客户端生成的UUID              |
| timestamp    | number | 是   | 客户端触发操作的时间戳（秒）  |

#### 成功响应

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "token": "new_jwt_token",
  "expires_in": 604800
}
```

#### 失败响应

```json
{
  "detail": "Invalid token"
}
```

---

### 1.4 登出

- **接口地址**：`POST /api/auth/logout`
- **功能**：登出账号
- **认证**：需要认证

#### 请求参数

| 字段         | 类型   | 必选 | 说明                          |
| ------------ | ------ | ---- | ----------------------------- |
| operation_id | string | 是   | 客户端生成的UUID              |
| timestamp    | number | 是   | 客户端触发操作的时间戳（秒）  |

#### 成功响应

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "message": "登出成功"
}
```

#### 失败响应

```json
{
  "detail": "Invalid token"
}
```

---

### 1.5 修改密码

- **接口地址**：`POST /api/auth/change_password`
- **功能**：修改账号密码
- **认证**：需要认证

#### 请求参数

| 字段         | 类型   | 必选 | 说明                          |
| ------------ | ------ | ---- | ----------------------------- |
| operation_id | string | 是   | 客户端生成的UUID              |
| timestamp    | number | 是   | 客户端触发操作的时间戳（秒）  |
| old_password | string | 是   | 旧密码（6-20位）             |
| new_password | string | 是   | 新密码（6-20位）             |

#### 成功响应

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "message": "密码修改成功"
}
```

#### 失败响应（旧密码错误）

```json
{
  "detail": "旧密码错误"
}
```

#### 失败响应（新密码与旧密码相同）

```json
{
  "detail": "新密码不能与旧密码相同"
}
```

#### 失败响应（新密码与用户名相同）

```json
{
  "detail": "新密码不能与用户名相同"
}
```

---

### 1.6 修改昵称

- **接口地址**：`POST /api/auth/change_nickname`
- **功能**：修改玩家昵称
- **认证**：需要认证

#### 请求参数

| 字段         | 类型   | 必选 | 说明                          |
| ------------ | ------ | ---- | ----------------------------- |
| operation_id | string | 是   | 客户端生成的UUID              |
| timestamp    | number | 是   | 客户端触发操作的时间戳（秒）  |
| nickname     | string | 是   | 新昵称（4-10位）             |

#### 成功响应

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "nickname": "新昵称",
  "message": "昵称修改成功"
}
```

#### 失败响应

```json
{
  "detail": "玩家数据不存在"
}
```

---

### 1.7 修改头像

- **接口地址**：`POST /api/auth/change_avatar`
- **功能**：修改玩家头像
- **认证**：需要认证

#### 请求参数

| 字段         | 类型   | 必选 | 说明                          |
| ------------ | ------ | ---- | ----------------------------- |
| operation_id | string | 是   | 客户端生成的UUID              |
| timestamp    | number | 是   | 客户端触发操作的时间戳（秒）  |
| avatar_id    | string | 是   | 头像ID                        |

#### 成功响应

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "avatar_id": "new_avatar",
  "message": "头像修改成功"
}
```

#### 失败响应

```json
{
  "detail": "玩家数据不存在"
}
```

---

## 2. 游戏数据系统 API

### 2.1 加载游戏数据

- **接口地址**：`GET /api/game/data`
- **功能**：加载玩家游戏数据
- **认证**：需要认证

#### 请求参数

无（通过请求头传递token）

#### 成功响应

```json
{
  "success": true,
  "data": {
    "account_info": {
      "nickname": "修仙者123456",
      "avatar_id": "abstract",
      "title_id": "",
      "is_vip": false,
      "vip_expire_time": null,
      "suspicious_operations_count": 0
    },
    "player": {
      "realm": "炼气期",
      "realm_level": 1,
      "health": 50.0,
      "spirit_energy": 0.0,
      "is_cultivating": false,
      "last_cultivation_report_time": 0.0
    },
    "inventory": {
      "slots": {},
      "capacity": 50
    },
    "spell_system": {
      "slot_limits": {
        "active": 2,
        "opening": 2,
        "breathing": 1
      },
      "player_spells": {},
      "equipped_spells": {
        "active": [],
        "opening": [],
        "breathing": []
      }
    },
    "alchemy_system": {
      "learned_recipes": [],
      "equipped_furnace_id": ""
    },
    "lianli_system": {
      "daily_dungeon_data": {
        "foundation_herb_cave": {
          "max_count": 3,
          "remaining_count": 3
        }
      },
      "tower_highest_floor": 0
    }
  }
}
```

#### 失败响应

```json
{
  "detail": "玩家数据不存在"
}
```

---

### 2.2 保存游戏数据

- **接口地址**：`POST /api/game/save`
- **功能**：保存玩家游戏数据（字段级别更新）
- **认证**：需要认证

#### 请求参数

| 字段         | 类型   | 必选 | 说明                                      |
| ------------ | ------ | ---- | ----------------------------------------- |
| operation_id | string | 是   | 客户端生成的UUID                          |
| timestamp    | number | 是   | 客户端触发操作的时间戳（秒）              |
| data         | object | 是   | 游戏数据（支持部分更新）                  |

**允许更新的字段**：
- `account_info`：账号信息
- `player`：玩家数据
- `inventory`：背包数据
- `spell_system`：术法系统
- `alchemy_system`：炼丹系统
- `lianli_system`：历练系统（注意：`daily_dungeon_data`字段不会被更新）

#### 请求示例

```json
{
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "data": {
    "spell_system": {
      "player_spells": {"fire": 1},
      "equipped_spells": {
        "active": [],
        "opening": [],
        "breathing": []
      }
    }
  }
}
```

#### 成功响应

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "last_online_at": 1678900000
}
```

#### 失败响应

```json
{
  "detail": "无效的更新字段"
}
```

---

### 2.3 领取离线奖励

- **接口地址**：`POST /api/game/claim_offline_reward`
- **功能**：领取离线奖励（服务端自动计算离线时间）
- **认证**：需要认证

#### 请求参数

| 字段         | 类型   | 必选 | 说明                          |
| ------------ | ------ | ---- | ----------------------------- |
| operation_id | string | 是   | 客户端生成的UUID              |
| timestamp    | number | 是   | 客户端触发操作的时间戳（秒）  |

#### 成功响应（有奖励）

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "offline_reward": {
    "spirit_energy": 47.0,
    "spirit_stones": 1
  },
  "offline_seconds": 474,
  "last_online_at": 1774100000,
  "message": "领取成功"
}
```

#### 成功响应（无奖励）

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "offline_reward": null,
  "offline_seconds": 30,
  "last_online_at": 1774100000,
  "message": "离线时间不足，无法领取奖励"
}
```

#### 失败响应

```json
{
  "detail": "INVALID_OFFLINE_SECONDS"
}
```

---

### 2.4 获取排行榜

- **接口地址**：`GET /api/game/rank`
- **功能**：获取指定区服的玩家排行榜
- **认证**：不需要认证

#### 请求参数

| 字段     | 类型   | 必选 | 说明                           |
| -------- | ------ | ---- | ------------------------------ |
| server_id | string | 否   | 区服ID，默认为"default"        |

#### 成功响应

```json
{
  "success": true,
  "operation_id": "",
  "timestamp": 1234567890,
  "ranks": [
    {
      "rank": 1,
      "nickname": "修仙者123456",
      "title_id": "",
      "realm": "金丹期",
      "level": 5,
      "spirit_energy": 732.0
    },
    {
      "rank": 2,
      "nickname": "道人789012",
      "title_id": "master",
      "realm": "金丹期",
      "level": 3,
      "spirit_energy": 605.0
    },
    {
      "rank": 3,
      "nickname": "仙友345678",
      "title_id": "",
      "realm": "筑基期",
      "level": 10,
      "spirit_energy": 236.0
    }
  ]
}
```

#### 排序规则

排行榜按照以下规则排序（从高到低）：
1. 大境界（炼气期 < 筑基期 < 金丹期 < 元婴期 < 化神期 < 炼虚期 < 合体期 < 大乘期 < 渡劫期）
2. 小境界（从高到低）
3. 灵气值（从多到少）
4. 创建时间（从早到晚）

#### 说明

- 返回前100名玩家数据
- 不包含被封禁的账号
- 不需要认证即可访问

---

## 3. 修炼系统 API

### 3.1 开始修炼

- **接口地址**：`POST /api/game/player/cultivation/start`
- **功能**：开始修炼
- **认证**：需要认证

#### 请求参数

| 字段         | 类型   | 必选 | 说明                          |
| ------------ | ------ | ---- | ----------------------------- |
| operation_id | string | 是   | 客户端生成的UUID              |
| timestamp    | number | 是   | 客户端触发操作的时间戳（秒）  |

#### 成功响应

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "spirit_gained": 1.0,
  "health_gained": 0.5,
  "used_count_gained": 1,
  "message": "开始修炼"
}
```

#### 失败响应

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "spirit_gained": 0.0,
  "health_gained": 0.0,
  "used_count_gained": 0,
  "message": "已在修炼状态"
}
```

---

### 3.2 上报修炼

- **接口地址**：`POST /api/game/player/cultivation/report`
- **功能**：上报修炼进度
- **认证**：需要认证

#### 请求参数

| 字段         | 类型   | 必选 | 说明                          |
| ------------ | ------ | ---- | ----------------------------- |
| operation_id | string | 是   | 客户端生成的UUID              |
| timestamp    | number | 是   | 客户端触发操作的时间戳（秒）  |
| count        | number | 是   | 修炼次数（秒数）              |

#### 成功响应

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "spirit_gained": 5.0,
  "health_gained": 2.5,
  "used_count_gained": 5,
  "message": "修炼成功"
}
```

#### 失败响应（未在修炼状态）

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "spirit_gained": 0.0,
  "health_gained": 0.0,
  "used_count_gained": 0,
  "message": "当前未在修炼状态"
}
```

#### 失败响应（时间不合理）

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "spirit_gained": 0.0,
  "health_gained": 0.0,
  "used_count_gained": 0,
  "message": "修炼上报异常：上报次数异常：上报5次，实际间隔0.2秒，最大允许0.2次"
}
```

---

### 3.3 停止修炼

- **接口地址**：`POST /api/game/player/cultivation/stop`
- **功能**：停止修炼
- **认证**：需要认证

#### 请求参数

| 字段         | 类型   | 必选 | 说明                          |
| ------------ | ------ | ---- | ----------------------------- |
| operation_id | string | 是   | 客户端生成的UUID              |
| timestamp    | number | 是   | 客户端触发操作的时间戳（秒）  |

#### 成功响应

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "message": "停止修炼"
}
```

#### 失败响应

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "message": "当前未在修炼状态"
}
```

---

### 3.4 突破境界

- **接口地址**：`POST /api/game/player/breakthrough`
- **功能**：玩家突破境界
- **认证**：需要认证

#### 请求参数

| 字段         | 类型   | 必选 | 说明                          |
| ------------ | ------ | ---- | ----------------------------- |
| operation_id | string | 是   | 客户端生成的UUID              |
| timestamp    | number | 是   | 客户端触发操作的时间戳（秒）  |

#### 成功响应

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "new_realm": "炼气期",
  "new_level": 2,
  "remaining_spirit_energy": 99999990.0,
  "materials_used": {
    "foundation_pill": 1
  },
  "health": 55.0,
  "inventory": {
    "slots": {},
    "capacity": 50
  }
}
```

#### 失败响应

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "new_realm": "炼气期",
  "new_level": 1,
  "remaining_spirit_energy": 0.0,
  "materials_used": {},
  "health": 50.0,
  "inventory": {
    "slots": {},
    "capacity": 50
  }
}
```

---

## 4. 背包系统 API

### 4.1 使用物品

- **接口地址**：`POST /api/game/inventory/use`
- **功能**：使用物品
- **认证**：需要认证

#### 请求参数

| 字段         | 类型   | 必选 | 说明                          |
| ------------ | ------ | ---- | ----------------------------- |
| operation_id | string | 是   | 客户端生成的UUID              |
| timestamp    | number | 是   | 客户端触发操作的时间戳（秒）  |
| item_id      | string | 是   | 物品ID                        |

#### 成功响应

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "effect": {
    "health": 100,
    "spirit_energy": 50
  },
  "contents": {
    "spirit_stone": 100,
    "health_pill": 5
  }
}
```

#### 失败响应

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "effect": {},
  "contents": null
}
```

---

### 4.2 整理背包

- **接口地址**：`POST /api/game/inventory/organize`
- **功能**：整理背包，压缩空位
- **认证**：需要认证

#### 请求参数

| 字段         | 类型   | 必选 | 说明                          |
| ------------ | ------ | ---- | ----------------------------- |
| operation_id | string | 是   | 客户端生成的UUID              |
| timestamp    | number | 是   | 客户端触发操作的时间戳（秒）  |

#### 成功响应

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "inventory": {
    "slots": {
      "0": {"id": "health_pill", "count": 5},
      "1": {"id": "spirit_pill", "count": 3}
    },
    "capacity": 50
  }
}
```

#### 失败响应

```json
{
  "detail": "玩家数据不存在"
}
```

---

### 4.3 丢弃物品

- **接口地址**：`POST /api/game/inventory/discard`
- **功能**：丢弃物品
- **认证**：需要认证

#### 请求参数

| 字段         | 类型   | 必选 | 说明                          |
| ------------ | ------ | ---- | ----------------------------- |
| operation_id | string | 是   | 客户端生成的UUID              |
| timestamp    | number | 是   | 客户端触发操作的时间戳（秒）  |
| item_id      | string | 是   | 物品ID                        |
| count        | number | 是   | 丢弃数量                      |

#### 成功响应

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "item_id": "health_pill",
  "discarded_count": 1
}
```

#### 失败响应

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "item_id": "health_pill",
  "discarded_count": 0
}
```

---

## 5. 术法系统 API

### 5.1 装备术法

- **接口地址**：`POST /api/game/spell/equip`
- **功能**：装备术法到指定槽位
- **认证**：需要认证

#### 请求参数

| 字段         | 类型   | 必选 | 说明                          |
| ------------ | ------ | ---- | ----------------------------- |
| operation_id | string | 是   | 客户端生成的UUID              |
| timestamp    | number | 是   | 客户端触发操作的时间戳（秒）  |
| spell_id     | string | 是   | 术法ID                        |
| slot_type    | string | 是   | 槽位类型：active/opening/breathing |

#### 成功响应

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "spell_id": "basic_boxing_techniques",
  "slot_type": "active",
  "equipped_spells": {
    "active": ["basic_boxing_techniques"],
    "opening": [],
    "breathing": []
  }
}
```

#### 失败响应

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "reason": "active槽位已达上限",
  "spell_id": "thunder_strike",
  "spell_type": "active"
}
```

---

### 5.2 卸下术法

- **接口地址**：`POST /api/game/spell/unequip`
- **功能**：从槽位卸下术法
- **认证**：需要认证

#### 请求参数

| 字段         | 类型   | 必选 | 说明                          |
| ------------ | ------ | ---- | ----------------------------- |
| operation_id | string | 是   | 客户端生成的UUID              |
| timestamp    | number | 是   | 客户端触发操作的时间戳（秒）  |
| spell_id     | string | 是   | 术法ID                        |
| slot_type    | string | 是   | 槽位类型：active/opening/breathing |

#### 成功响应

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "spell_id": "basic_boxing_techniques",
  "slot_type": "active",
  "equipped_spells": {
    "active": [],
    "opening": [],
    "breathing": []
  }
}
```

#### 失败响应

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "reason": "术法未装备在该槽位",
  "spell_id": "basic_boxing_techniques",
  "slot_type": "active"
}
```

---

### 5.3 升级术法

- **接口地址**：`POST /api/game/spell/upgrade`
- **功能**：升级术法等级
- **认证**：需要认证

#### 请求参数

| 字段         | 类型   | 必选 | 说明                          |
| ------------ | ------ | ---- | ----------------------------- |
| operation_id | string | 是   | 客户端生成的UUID              |
| timestamp    | number | 是   | 客户端触发操作的时间戳（秒）  |
| spell_id     | string | 是   | 术法ID                        |

#### 成功响应

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "spell_id": "basic_boxing_techniques",
  "old_level": 1,
  "new_level": 2,
  "cost": 100
}
```

#### 失败响应

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "reason": "灵气不足",
  "spell_id": "basic_boxing_techniques"
}
```

---

### 5.4 充灵气

- **接口地址**：`POST /api/game/spell/charge`
- **功能**：为术法充灵气
- **认证**：需要认证

#### 请求参数

| 字段         | 类型   | 必选 | 说明                          |
| ------------ | ------ | ---- | ----------------------------- |
| operation_id | string | 是   | 客户端生成的UUID              |
| timestamp    | number | 是   | 客户端触发操作的时间戳（秒）  |
| spell_id     | string | 是   | 术法ID                        |
| amount       | number | 是   | 充灵气数量                    |

#### 成功响应

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "spell_id": "basic_boxing_techniques",
  "charged_spirit": 100,
  "remaining_spirit_energy": 900
}
```

#### 失败响应

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "reason": "灵气不足",
  "spell_id": "basic_boxing_techniques"
}
```

---

### 5.5 获取术法列表

- **接口地址**：`GET /api/game/spell/list`
- **功能**：获取玩家所有术法
- **认证**：需要认证

#### 请求参数

无（通过请求头传递token）

#### 成功响应

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "spells": {
    "basic_boxing_techniques": {
      "level": 1,
      "obtained": true,
      "use_count": 0,
      "charged_spirit": 0
    },
    "thunder_strike": {
      "level": 1,
      "obtained": true,
      "use_count": 0,
      "charged_spirit": 0
    }
  },
  "equipped_spells": {
    "active": ["basic_boxing_techniques"],
    "opening": [],
    "breathing": []
  }
}
```

#### 失败响应

```json
{
  "detail": "玩家数据不存在"
}
```

---

## 6. 炼丹系统 API

### 6.1 开始炼丹

- **接口地址**：`POST /api/game/alchemy/start`
- **功能**：开始炼丹
- **认证**：需要认证

#### 请求参数

| 字段         | 类型   | 必选 | 说明                          |
| ------------ | ------ | ---- | ----------------------------- |
| operation_id | string | 是   | 客户端生成的UUID              |
| timestamp    | number | 是   | 客户端触发操作的时间戳（秒）  |

#### 成功响应

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "is_alchemizing": true,
  "message": "开始炼丹"
}
```

#### 失败响应

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "is_alchemizing": true,
  "message": "已在炼丹状态"
}
```

---

### 6.2 炼丹上报

- **接口地址**：`POST /api/game/alchemy/report`
- **功能**：上报炼丹进度
- **认证**：需要认证

#### 请求参数

| 字段         | 类型   | 必选 | 说明                          |
| ------------ | ------ | ---- | ----------------------------- |
| operation_id | string | 是   | 客户端生成的UUID              |
| timestamp    | number | 是   | 客户端触发操作的时间戳（秒）  |
| recipe_id    | string | 是   | 丹方ID                        |
| count        | number | 是   | 本次完成的数量                |

#### 成功响应

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "success_count": 1,
  "fail_count": 0,
  "products": {
    "health_pill": 1
  },
  "materials_consumed": {
    "mat_herb": 2,
    "spirit_energy": 1
  },
  "message": "炼丹完成：成功1颗，失败0颗"
}
```

#### 失败响应（未在炼丹状态）

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "success_count": 0,
  "fail_count": 0,
  "products": {},
  "materials_consumed": {},
  "message": "当前未在炼丹状态"
}
```

#### 失败响应（时间不合理）

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "success_count": 0,
  "fail_count": 0,
  "products": {},
  "materials_consumed": {},
  "message": "炼丹上报异常：上报1次，实际间隔2.0秒，最小允许2.7秒"
}
```

---

### 6.3 停止炼丹

- **接口地址**：`POST /api/game/alchemy/stop`
- **功能**：停止炼丹
- **认证**：需要认证

#### 请求参数

| 字段         | 类型   | 必选 | 说明                          |
| ------------ | ------ | ---- | ----------------------------- |
| operation_id | string | 是   | 客户端生成的UUID              |
| timestamp    | number | 是   | 客户端触发操作的时间戳（秒）  |

#### 成功响应

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "is_alchemizing": false,
  "message": "停止炼丹"
}
```

#### 失败响应

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "is_alchemizing": false,
  "message": "当前未在炼丹状态"
}
```

---

### 6.4 学习丹方

- **接口地址**：`POST /api/game/alchemy/learn_recipe`
- **功能**：学习新丹方
- **认证**：需要认证

#### 请求参数

| 字段         | 类型   | 必选 | 说明                          |
| ------------ | ------ | ---- | ----------------------------- |
| operation_id | string | 是   | 客户端生成的UUID              |
| timestamp    | number | 是   | 客户端触发操作的时间戳（秒）  |
| recipe_id    | string | 是   | 丹方ID                        |

#### 成功响应

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "recipe_id": "health_pill",
  "learned_recipes": ["health_pill", "spirit_pill"]
}
```

#### 失败响应

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "reason": "丹方已学习",
  "recipe_id": "health_pill"
}
```

---

### 6.5 获取丹方列表

- **接口地址**：`GET /api/game/alchemy/recipes`
- **功能**：获取已学习的丹方列表
- **认证**：需要认证

#### 请求参数

无（通过请求头传递token）

#### 成功响应

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "recipes": [
    "health_pill",
    "spirit_pill",
    "foundation_pill"
  ],
  "equipped_furnace_id": "alchemy_furnace"
}
```

#### 失败响应

```json
{
  "detail": "玩家数据不存在"
}
```

---

## 7. 历练系统 API

### 7.1 战斗模拟

- **接口地址**：`POST /api/game/lianli/simulate`
- **功能**：模拟战斗（不更新数据库）
- **认证**：需要认证

#### 请求参数

| 字段         | 类型   | 必选 | 说明                          |
| ------------ | ------ | ---- | ----------------------------- |
| operation_id | string | 是   | 客户端生成的UUID              |
| timestamp    | number | 是   | 客户端触发操作的时间戳（秒）  |
| area_id      | string | 是   | 历练区域ID                    |

#### 成功响应

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "battle_timeline": [
    {
      "time": 0.0,
      "type": "player_action",
      "info": {
        "spell_id": "basic_health",
        "effect_type": "undispellable_buff",
        "damage": 0,
        "heal": 0
      }
    },
    {
      "time": 2.0,
      "type": "player_action",
      "info": {
        "spell_id": "basic_boxing_techniques",
        "effect_type": "instant_damage",
        "damage": 6.6,
        "target_health_after": 23.4
      }
    },
    {
      "time": 2.3,
      "type": "enemy_action",
      "info": {
        "enemy_name": "野猪",
        "spell_id": "norm_attack",
        "damage": 1.0,
        "target_health_after": 75.0
      }
    }
  ],
  "total_time": 10.0,
  "player_health_before": 76.0,
  "player_health_after": 72.0,
  "enemy_health_after": 0.0,
  "enemy_data": {
    "name": "野猪",
    "health": 30.0,
    "attack": 3.0,
    "defense": 1.0,
    "speed": 1.0
  },
  "victory": true,
  "loot": [
    {"item_id": "spirit_stone", "amount": 1}
  ],
  "message": "战斗模拟完成"
}
```

#### 失败响应

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "battle_timeline": [],
  "total_time": 0.0,
  "player_health_before": 0.0,
  "player_health_after": 0.0,
  "enemy_health_after": 0.0,
  "enemy_data": {},
  "victory": false,
  "loot": [],
  "message": "当前已在战斗状态"
}
```

---

### 7.2 战斗结算

- **接口地址**：`POST /api/game/lianli/finish`
- **功能**：结算战斗（更新数据库）
- **认证**：需要认证

#### 请求参数

| 字段         | 类型   | 必选 | 说明                                      |
| ------------ | ------ | ---- | ----------------------------------------- |
| operation_id | string | 是   | 客户端生成的UUID                          |
| timestamp    | number | 是   | 客户端触发操作的时间戳（秒）              |
| speed        | number | 是   | 播放倍速（1.0/2.0等）                    |
| index        | number | 否   | 战斗进度索引（不传则完整结算）            |

#### 成功响应（完整结算）

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "settled_index": 11,
  "total_index": 11,
  "player_health_after": 72.0,
  "loot_gained": [
    {"item_id": "spirit_stone", "amount": 1}
  ],
  "exp_gained": 0,
  "message": "战斗结算成功"
}
```

#### 成功响应（部分结算）

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "settled_index": 5,
  "total_index": 11,
  "player_health_after": 75.0,
  "loot_gained": [],
  "exp_gained": 0,
  "message": "战斗部分结算成功"
}
```

#### 失败响应（时间验证失败）

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "settled_index": 0,
  "total_index": 11,
  "player_health_after": 76.0,
  "loot_gained": [],
  "exp_gained": 0,
  "message": "战斗结算异常：时间验证失败，实际用时0.0秒，最小需要9.0秒"
}
```

#### 失败响应（未在战斗状态）

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "settled_index": 0,
  "total_index": 0,
  "player_health_after": 76.0,
  "loot_gained": [],
  "exp_gained": 0,
  "message": "当前未在战斗状态"
}
```

---

### 7.3 获取破镜草洞穴信息

- **接口地址**：`GET /api/game/lianli/foundation_herb_cave`
- **功能**：获取破镜草洞穴剩余次数和总次数
- **认证**：需要认证

#### 请求参数

无（通过请求头传递token）

#### 成功响应

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "remaining_count": 2,
  "max_count": 3
}
```

#### 失败响应

```json
{
  "detail": "玩家数据不存在"
}
```

---

### 7.4 获取无尽塔信息

- **接口地址**：`GET /api/game/lianli/tower`
- **功能**：获取无尽塔最高层数
- **认证**：需要认证

#### 请求参数

无（通过请求头传递token）

#### 成功响应

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "highest_floor": 5
}
```

#### 失败响应

```json
{
  "detail": "玩家数据不存在"
}
```

---

## 8. 管理后台 API

### 8.1 管理员登录

- **接口地址**：`POST /api/admin/login`
- **功能**：管理员登录
- **认证**：无需认证

#### 请求参数

| 字段     | 类型   | 必选 | 说明     |
| -------- | ------ | ---- | -------- |
| username | string | 是   | 管理员用户名 |
| password | string | 是   | 管理员密码  |

#### 成功响应

```json
{
  "success": true,
  "token": "admin_jwt_token",
  "expires_in": 604800
}
```

#### 失败响应

```json
{
  "detail": "用户名或密码错误"
}
```

---

### 8.2 获取玩家列表

- **接口地址**：`GET /api/admin/players`
- **功能**：获取所有玩家列表
- **认证**：需要管理员认证

#### 请求参数

无（通过请求头传递token）

#### 成功响应

```json
{
  "success": true,
  "players": [
    {
      "id": "uuid",
      "username": "testuser",
      "server_id": "default",
      "created_at": "2024-01-01T00:00:00Z",
      "is_banned": false
    }
  ]
}
```

#### 失败响应

```json
{
  "detail": "Unauthorized"
}
```

---

### 8.3 获取玩家详情

- **接口地址**：`GET /api/admin/player/{id}`
- **功能**：获取指定玩家详情
- **认证**：需要管理员认证

#### 路径参数

| 字段 | 类型   | 必选 | 说明     |
| ---- | ------ | ---- | -------- |
| id   | string | 是   | 玩家账号ID |

#### 成功响应

```json
{
  "success": true,
  "player": {
    "id": "uuid",
    "username": "testuser",
    "server_id": "default",
    "created_at": "2024-01-01T00:00:00Z",
    "is_banned": false,
    "game_data": {
      "account_info": {},
      "player": {},
      "inventory": {}
    }
  }
}
```

#### 失败响应

```json
{
  "detail": "Player not found"
}
```

---

### 8.4 封号

- **接口地址**：`POST /api/admin/player/{id}/ban`
- **功能**：封禁玩家账号
- **认证**：需要管理员认证

#### 路径参数

| 字段 | 类型   | 必选 | 说明     |
| ---- | ------ | ---- | -------- |
| id   | string | 是   | 玩家账号ID |

#### 成功响应

```json
{
  "success": true,
  "message": "封号成功"
}
```

#### 失败响应

```json
{
  "detail": "Player not found"
}
```

---

## 9. 数据结构说明

### 9.1 account_info 字段

| 字段                      | 类型          | 说明          |
| ------------------------- | ------------- | ------------- |
| nickname                  | string        | 玩家昵称      |
| avatar_id                 | string        | 头像ID        |
| title_id                  | string        | 称号ID        |
| is_vip                    | boolean       | 是否VIP       |
| vip_expire_time           | number/null   | VIP过期时间戳 |
| suspicious_operations_count | number       | 异常操作次数  |

### 9.2 player 字段

| 字段                         | 类型    | 说明               |
| ---------------------------- | ------- | ------------------ |
| realm                        | string  | 当前境界           |
| realm_level                  | number  | 当前境界层数       |
| health                       | number  | 生命值             |
| spirit_energy                | number  | 灵气值             |
| is_cultivating               | boolean | 是否在修炼状态     |
| last_cultivation_report_time | number  | 上次上报修炼时间戳 |

### 9.3 inventory 字段

| 字段     | 类型   | 说明     |
| -------- | ------ | -------- |
| slots    | object | 物品槽位 |
| capacity | number | 背包容量 |

### 9.4 spell_system 字段

| 字段            | 类型   | 说明         |
| --------------- | ------ | ------------ |
| slot_limits     | object | 槽位上限     |
| player_spells   | object | 玩家术法     |
| equipped_spells | object | 已装备术法   |

### 9.5 alchemy_system 字段

| 字段                | 类型     | 说明         |
| ------------------- | -------- | ------------ |
| learned_recipes     | string[] | 已学习丹方   |
| equipped_furnace_id | string   | 已装备炼丹炉 |

### 9.6 lianli_system 字段

| 字段                  | 类型    | 说明                     |
| --------------------- | ------- | ------------------------ |
| is_battling           | boolean | 是否在战斗状态           |
| battle_start_time     | number  | 战斗开始时间戳（秒）     |
| daily_dungeon_data    | object  | 每日副本数据             |
| current_battle_data   | object  | 当前战斗数据（战斗中）   |
| tower_highest_floor   | number  | 塔防最高层               |

#### daily_dungeon_data 结构

```json
{
  "foundation_herb_cave": {
    "max_count": 3,
    "remaining_count": 3
  }
}
```

#### current_battle_data 结构（战斗中）

```json
{
  "battle_timeline": [...],
  "total_time": 10.0,
  "player_health_before": 76.0,
  "enemy_data": {...},
  "victory": true,
  "loot": [...]
}
```

---

## 10. 测试账号

- **测试账号**：wcc_test / wcc_test
- **管理员账号**：admin / admin123

---

## 11. 服务信息

- **服务地址**：http://127.0.0.1:8444
- **API 文档**：http://127.0.0.1:8444/api/docs
- **版本**：v1.0.0
