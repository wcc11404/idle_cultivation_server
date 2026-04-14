# 修仙挂机游戏服务端 API 文档

## 文档说明

### 通用请求参数

**所有 `POST` 业务接口都需要以下请求体参数：**

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
  "...": "其他数据"
}
```

#### 业务响应补充说明

- 客户端使用的账号系统、游戏数据系统、修炼系统、背包系统、术法系统、炼丹系统、历练系统的业务接口统一返回 `reason_code` 与 `reason_data`
- `reason_code` 只表达业务语义，不直接承担中文提示展示
- `reason_data` 只携带客户端生成提示文案需要的动态字段
- 客户端必须根据 `reason_code + reason_data` 生成最终中文提示，不再直接使用接口中的 `message/reason`
- `auth/refresh` 这类纯鉴权接口的失败仍可能通过 `detail` 表达认证异常

#### 异常响应

```json
{
  "detail": "错误信息"
}
```

---

## 1. 认证系统 API

### 1.1 注册账号

- **接口地址**：`POST /api/auth/register`
- **功能**：注册新账号
- **认证**：无需认证

#### 请求参数

| 字段         | 类型   | 必选 | 说明                          |
| ------------ | ------ | ---- | ----------------------------- |
| username     | string | 是   | 用户名（4-20字符）           |
| password     | string | 是   | 密码（6-20字符）             |
| operation_id | string | 是   | 客户端生成的UUID              |
| timestamp    | number | 是   | 客户端触发操作的时间戳（秒）  |

#### 成功响应

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "token": "jwt_token",
  "reason_code": "ACCOUNT_REGISTER_SUCCEEDED",
  "reason_data": {
    "username": "testuser"
  }
}
```

#### 失败响应

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "reason_code": "ACCOUNT_REGISTER_USERNAME_EXISTS",
  "reason_data": {
    "username": "testuser"
  }
}
```

#### `reason_code` 枚举

- `ACCOUNT_REGISTER_SUCCEEDED`
- `ACCOUNT_REGISTER_USERNAME_EMPTY`
- `ACCOUNT_REGISTER_USERNAME_LENGTH_INVALID`
- `ACCOUNT_REGISTER_USERNAME_INVALID_CHARACTER`
- `ACCOUNT_REGISTER_PASSWORD_EMPTY`
- `ACCOUNT_REGISTER_PASSWORD_LENGTH_INVALID`
- `ACCOUNT_REGISTER_PASSWORD_INVALID_CHARACTER`
- `ACCOUNT_REGISTER_USERNAME_PASSWORD_SAME`
- `ACCOUNT_REGISTER_USERNAME_EXISTS`

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
  "reason_code": "ACCOUNT_LOGIN_SUCCEEDED",
  "reason_data": {
    "username": "testuser"
  },
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
  "reason_code": "ACCOUNT_LOGIN_PASSWORD_INCORRECT",
  "reason_data": {
    "username": "testuser"
  },
  "token": "",
  "expires_in": 0,
  "account_info": {
    "id": "00000000-0000-0000-0000-000000000000",
    "username": "",
    "server_id": ""
  },
  "data": {}
}
```

#### `reason_code` 枚举

- `ACCOUNT_LOGIN_SUCCEEDED`
- `ACCOUNT_LOGIN_USERNAME_NOT_FOUND`
- `ACCOUNT_LOGIN_PASSWORD_INCORRECT`
- `ACCOUNT_LOGIN_ACCOUNT_BANNED`

---

### 1.3 Token 续期

- **接口地址**：`POST /api/auth/refresh`
- **功能**：刷新 JWT Token
- **认证**：需要认证

#### 请求参数

无（通过请求头传递token）

#### 成功响应

```json
{
  "success": true,
  "reason_code": "ACCOUNT_REFRESH_SUCCEEDED",
  "reason_data": {},
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

无（通过请求头传递token）

#### 成功响应

```json
{
  "success": true,
  "reason_code": "ACCOUNT_LOGOUT_SUCCEEDED",
  "reason_data": {}
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
| username     | string | 是   | 用户名                        |
| old_password | string | 是   | 旧密码（6-20位）             |
| new_password | string | 是   | 新密码（6-20位）             |

#### 成功响应

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "reason_code": "ACCOUNT_PASSWORD_CHANGE_SUCCEEDED",
  "reason_data": {
    "username": "testuser"
  }
}
```

#### 失败响应

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "reason_code": "ACCOUNT_PASSWORD_CHANGE_OLD_PASSWORD_INCORRECT",
  "reason_data": {
    "username": "testuser"
  }
}
```

#### `reason_code` 枚举

- `ACCOUNT_PASSWORD_CHANGE_SUCCEEDED`
- `ACCOUNT_PASSWORD_CHANGE_ACCOUNT_NOT_FOUND`
- `ACCOUNT_PASSWORD_CHANGE_OLD_PASSWORD_INCORRECT`
- `ACCOUNT_PASSWORD_CHANGE_SAME_AS_OLD`
- `ACCOUNT_PASSWORD_CHANGE_SAME_AS_USERNAME`

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
  "reason_code": "ACCOUNT_NICKNAME_CHANGE_SUCCEEDED",
  "reason_data": {
    "nickname": "新昵称"
  }
}
```

#### 失败响应

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "nickname": "新昵称",
  "reason_code": "ACCOUNT_NICKNAME_LENGTH_INVALID",
  "reason_data": {
    "nickname": "新昵称"
  }
}
```

#### `reason_code` 枚举

- `ACCOUNT_NICKNAME_CHANGE_SUCCEEDED`
- `ACCOUNT_NICKNAME_EMPTY`
- `ACCOUNT_NICKNAME_LENGTH_INVALID`
- `ACCOUNT_NICKNAME_CONTAINS_SPACE`
- `ACCOUNT_NICKNAME_INVALID_CHARACTER`
- `ACCOUNT_NICKNAME_ALL_DIGITS`
- `ACCOUNT_NICKNAME_SENSITIVE`
- `ACCOUNT_NICKNAME_PLAYER_NOT_FOUND`

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
  "reason_code": "ACCOUNT_AVATAR_CHANGE_SUCCEEDED",
  "reason_data": {
    "avatar_id": "new_avatar"
  }
}
```

#### 失败响应

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "avatar_id": "new_avatar",
  "reason_code": "ACCOUNT_AVATAR_PLAYER_NOT_FOUND",
  "reason_data": {
    "avatar_id": "new_avatar"
  }
}
```

#### `reason_code` 枚举

- `ACCOUNT_AVATAR_CHANGE_SUCCEEDED`
- `ACCOUNT_AVATAR_PLAYER_NOT_FOUND`

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
  "reason_code": "GAME_LOAD_SUCCEEDED",
  "reason_data": {},
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

#### `reason_code` 枚举

- `GAME_LOAD_SUCCEEDED`

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
  "reason_code": "GAME_SAVE_SUCCEEDED",
  "reason_data": {},
  "last_online_at": 1678900000
}
```

#### `reason_code` 枚举

- `GAME_SAVE_SUCCEEDED`

---

### 2.3 领取离线奖励

- **接口地址**：`POST /api/game/claim_offline_reward`
- **功能**：领取离线奖励（服务端自动计算离线时间，超过 4 小时按 4 小时封顶结算）
- **认证**：需要认证

#### 请求参数

| 字段         | 类型   | 必选 | 说明                          |
| ------------ | ------ | ---- | ----------------------------- |
| operation_id | string | 是   | 客户端生成的UUID              |
| timestamp    | number | 是   | 客户端触发操作的时间戳（秒）  |

- **说明**：
  - 离线时间小于等于 60 秒时，不发放奖励
  - 离线时间大于 4 小时时，按 14400 秒（4 小时）结算奖励

#### 成功响应（有奖励）

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "reason_code": "GAME_OFFLINE_REWARD_GRANTED",
  "reason_data": {},
  "offline_reward": {
    "spirit_energy": 47.0,
    "spirit_stones": 1
  },
  "offline_seconds": 474,
  "last_online_at": 1774100000
}
```

#### 成功响应（无奖励）

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "reason_code": "GAME_OFFLINE_REWARD_SKIPPED_SHORT_OFFLINE",
  "reason_data": {},
  "offline_reward": null,
  "offline_seconds": 30,
  "last_online_at": 1774100000
}
```

#### `reason_code` 枚举

- `GAME_OFFLINE_REWARD_GRANTED`
- `GAME_OFFLINE_REWARD_SKIPPED_SHORT_OFFLINE`
- `GAME_OFFLINE_REWARD_INVALID_TIME`

#### 失败响应

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "reason_code": "GAME_OFFLINE_REWARD_INVALID_TIME",
  "reason_data": {
    "offline_seconds": -30
  },
  "offline_reward": null,
  "offline_seconds": -30,
  "last_online_at": 1774100000
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
  "reason_code": "GAME_RANK_SUCCEEDED",
  "reason_data": {},
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

#### `reason_code` 枚举

- `GAME_RANK_SUCCEEDED`

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
  "reason_code": "CULTIVATION_START_SUCCEEDED",
  "reason_data": {}
}
```

#### 说明

- `start` 只切换为修炼状态并记录开始时间，不立即结算修炼收益
- 真正的修炼收益只会在客户端后续调用 `report` 时结算

#### 失败响应

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "reason_code": "CULTIVATION_START_ALREADY_ACTIVE",
  "reason_data": {}
}
```

#### `reason_code` 枚举

- `CULTIVATION_START_SUCCEEDED`：开始修炼成功
- `CULTIVATION_START_ALREADY_ACTIVE`：当前已在修炼状态
- `CULTIVATION_START_BLOCKED_BY_BATTLE`：战斗中不可开始修炼
- `CULTIVATION_START_BLOCKED_BY_ALCHEMY`：炼丹中不可开始修炼

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
  "reason_code": "CULTIVATION_REPORT_SUCCEEDED",
  "reason_data": {},
  "spirit_gained": 5.0,
  "health_gained": 2.5,
  "used_count_gained": 5
}
```

#### 失败响应（未在修炼状态）

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "reason_code": "CULTIVATION_REPORT_NOT_ACTIVE",
  "reason_data": {},
  "spirit_gained": 0.0,
  "health_gained": 0.0,
  "used_count_gained": 0
}
```

#### 失败响应（时间不合理）

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "reason_code": "CULTIVATION_REPORT_TIME_INVALID",
  "reason_data": {
    "reported_count": 5,
    "actual_interval": 0.2,
    "max_acceptable_count": 0.22,
    "invalid_report_count": 3,
    "kicked_out": false,
    "kick_threshold": 10
  },
  "spirit_gained": 0.0,
  "health_gained": 0.0,
  "used_count_gained": 0
}
```

#### `reason_code` 枚举

- `CULTIVATION_REPORT_SUCCEEDED`：修炼上报成功
- `CULTIVATION_REPORT_NOT_ACTIVE`：当前未在修炼状态
- `CULTIVATION_REPORT_TIME_INVALID`：上报时间校验失败
- 当 `reason_data.kicked_out=true` 时，服务端已执行 `token_version + 1`，客户端下一次请求将收到鉴权失效并回到登录态

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
  "reason_code": "CULTIVATION_STOP_SUCCEEDED",
  "reason_data": {}
}
```

#### `reason_code` 枚举

- `CULTIVATION_STOP_SUCCEEDED`
- `CULTIVATION_STOP_NOT_ACTIVE`

#### 失败响应

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "reason_code": "CULTIVATION_STOP_NOT_ACTIVE",
  "reason_data": {}
}
```

#### `reason_code` 枚举

- `CULTIVATION_STOP_SUCCEEDED`：停止修炼成功
- `CULTIVATION_STOP_NOT_ACTIVE`：当前未在修炼状态

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
  "reason_code": "CULTIVATION_BREAKTHROUGH_SUCCEEDED",
  "reason_data": {
    "consumed_resources": {
      "spirit_energy": 100.0,
      "foundation_pill": 1
    },
    "missing_resources": {},
    "new_realm": "炼气期",
    "new_level": 2,
    "current_realm": "",
    "current_level": 0
  }
}
```

#### 失败响应

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "reason_code": "CULTIVATION_BREAKTHROUGH_INSUFFICIENT_RESOURCES",
  "reason_data": {
    "consumed_resources": {},
    "missing_resources": {
      "spirit_energy": 100.0,
      "spirit_stone": 2
    },
    "new_realm": "",
    "new_level": 0,
    "current_realm": "炼气期",
    "current_level": 1
  }
}
```

#### `reason_code` 枚举

- `CULTIVATION_BREAKTHROUGH_SUCCEEDED`：突破成功
- `CULTIVATION_BREAKTHROUGH_INSUFFICIENT_RESOURCES`：突破失败，资源不足
- `CULTIVATION_BREAKTHROUGH_NOT_AVAILABLE`：当前境界不可继续突破

#### `reason_data` 字段说明

- `consumed_resources`：成功时实际消耗资源，结构为 `{resource_id: amount}`
- `missing_resources`：失败时缺少资源，结构为 `{resource_id: amount}`
- `new_realm` / `new_level`：成功后新境界，放在 `reason_data` 中
- `current_realm` / `current_level`：失败时当前境界

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
  "reason_code": "INVENTORY_USE_CONSUMABLE_SUCCEEDED",
  "reason_data": {
    "item_id": "health_pill",
    "used_count": 1,
    "effect": {
      "type": "add_health",
      "health_added": 100
    },
    "contents": {}
  }
}
```

#### 失败响应

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "reason_code": "INVENTORY_USE_ITEM_NOT_ENOUGH",
  "reason_data": {
    "item_id": "health_pill",
    "used_count": 0,
    "effect": {},
    "contents": {}
  }
}
```

#### `reason_code` 枚举

- `INVENTORY_USE_CONSUMABLE_SUCCEEDED`
- `INVENTORY_USE_GIFT_SUCCEEDED`
- `INVENTORY_USE_UNLOCK_SPELL_SUCCEEDED`
- `INVENTORY_USE_UNLOCK_RECIPE_SUCCEEDED`
- `INVENTORY_USE_UNLOCK_FURNACE_SUCCEEDED`
- `INVENTORY_USE_ITEM_NOT_FOUND`
- `INVENTORY_USE_ITEM_NOT_ENOUGH`
- `INVENTORY_USE_ITEM_NOT_USABLE`
- `INVENTORY_USE_EFFECT_INVALID`
- `INVENTORY_USE_UNLOCK_SPELL_INVALID`
- `INVENTORY_USE_UNLOCK_RECIPE_INVALID`
- `INVENTORY_USE_ALREADY_USED`
- `INVENTORY_USE_SYSTEM_ERROR`

#### `reason_data` 字段说明

- `item_id`：本次操作的物品 ID
- `used_count`：本次实际消耗数量
- `effect`：结构化效果对象，客户端据此生成提示文案
- `contents`：礼包/开包奖励内容，结构为 `{item_id: count}`

#### 特殊失败语义

- `INVENTORY_USE_ALREADY_USED`：一次性解锁类物品已被消耗过，客户端应基于 `item_id` 输出统一提示，例如“xx已经使用过了，无法重复使用”
- `INVENTORY_USE_SYSTEM_ERROR`：服务端依赖缺失或物品配置异常导致的内部错误，客户端应输出通用失败提示，不应暴露服务端内部细节

#### `effect.type` 枚举

- `add_spirit_energy`
- `add_health`
- `add_spirit_and_health`
- `open_gift`
- `unlock_spell`
- `unlock_recipe`
- `unlock_furnace`

#### `effect` 数值说明

- `spirit_energy_added` 与 `health_added` 表示物品的理论恢复值，供客户端展示提示文案
- 实际结算时仍会受到玩家当前静态上限限制，服务端状态以最终裁切后的数值为准

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
  "reason_code": "INVENTORY_ORGANIZE_SUCCEEDED",
  "reason_data": {}
}
```

#### 失败响应

该接口当前无独立业务失败响应，失败通常表现为鉴权或网络异常。

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
  "reason_code": "INVENTORY_DISCARD_SUCCEEDED",
  "reason_data": {
    "item_id": "health_pill",
    "discarded_count": 1
  }
}
```

#### 失败响应

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "reason_code": "INVENTORY_DISCARD_ITEM_NOT_ENOUGH",
  "reason_data": {
    "item_id": "health_pill",
    "discarded_count": 0
  }
}
```

#### `reason_code` 枚举

- `INVENTORY_DISCARD_SUCCEEDED`
- `INVENTORY_DISCARD_ITEM_NOT_ENOUGH`

---

### 4.4 扩容背包

- **接口地址**：`POST /api/game/inventory/expand`
- **功能**：扩容背包容量
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
  "reason_code": "INVENTORY_EXPAND_SUCCEEDED",
  "reason_data": {
    "new_capacity": 60
  }
}
```

#### 失败响应

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "reason_code": "INVENTORY_EXPAND_CAPACITY_MAX",
  "reason_data": {
    "new_capacity": 200
  }
}
```

**说明**：
- 每次扩容增加10格容量
- 最大容量为200格
- 达到最大容量时返回失败

#### `reason_code` 枚举

- `INVENTORY_EXPAND_SUCCEEDED`
- `INVENTORY_EXPAND_CAPACITY_MAX`

---

### 4.5 获取背包列表

- **接口地址**：`GET /api/game/inventory/list`
- **功能**：获取背包数据
- **认证**：需要认证

#### 成功响应

```json
{
  "success": true,
  "operation_id": "",
  "timestamp": 1234567890,
  "reason_code": "INVENTORY_LIST_SUCCEEDED",
  "reason_data": {},
  "inventory": {
    "slots": {
      "0": {"id": "health_pill", "count": 5},
      "1": {"id": "spirit_pill", "count": 3}
    },
    "capacity": 50
  }
}
```

#### `reason_code` 枚举

- `INVENTORY_LIST_SUCCEEDED`

#### 失败响应

该接口当前无独立业务失败响应，失败通常表现为鉴权或网络异常。

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

#### 成功响应

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "reason_code": "SPELL_EQUIP_SUCCEEDED",
  "reason_data": {
    "spell_id": "basic_boxing_techniques",
    "slot_type": "active",
    "spell_type": "active",
    "action": ""
  }
}
```

#### 失败响应

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "reason_code": "SPELL_SLOT_LIMIT_REACHED",
  "reason_data": {
    "spell_id": "thunder_strike",
    "slot_type": "active",
    "spell_type": "active",
    "limit": 2,
    "current_count": 2,
    "action": ""
  }
}
```

#### `reason_code` 枚举

- `SPELL_EQUIP_SUCCEEDED`
- `SPELL_EQUIP_NOT_FOUND`
- `SPELL_EQUIP_NOT_OWNED`
- `SPELL_EQUIP_ALREADY_EQUIPPED`
- `SPELL_EQUIP_PRODUCTION_FORBIDDEN`
- `SPELL_SLOT_LIMIT_REACHED`
- `SPELL_ACTION_BATTLE_LOCKED`

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

#### 成功响应

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "reason_code": "SPELL_UNEQUIP_SUCCEEDED",
  "reason_data": {
    "spell_id": "basic_boxing_techniques",
    "slot_type": "active",
    "spell_type": "active",
    "action": ""
  }
}
```

#### 失败响应

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "reason_code": "SPELL_UNEQUIP_NOT_EQUIPPED",
  "reason_data": {
    "spell_id": "basic_boxing_techniques",
    "slot_type": "",
    "spell_type": "",
    "action": ""
  }
}
```

#### `reason_code` 枚举

- `SPELL_UNEQUIP_SUCCEEDED`
- `SPELL_UNEQUIP_NOT_FOUND`
- `SPELL_UNEQUIP_NOT_EQUIPPED`
- `SPELL_ACTION_BATTLE_LOCKED`

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
  "reason_code": "SPELL_UPGRADE_SUCCEEDED",
  "reason_data": {
    "spell_id": "basic_boxing_techniques",
    "new_level": 2,
    "action": ""
  }
}
```

#### 失败响应

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "reason_code": "SPELL_UPGRADE_CHARGED_SPIRIT_INSUFFICIENT",
  "reason_data": {
    "spell_id": "basic_boxing_techniques",
    "current_level": 1,
    "current_charged_spirit": 20,
    "required_charged_spirit": 100,
    "action": ""
  }
}
```

#### `reason_code` 枚举

- `SPELL_UPGRADE_SUCCEEDED`
- `SPELL_UPGRADE_NOT_OWNED`
- `SPELL_UPGRADE_AT_MAX_LEVEL`
- `SPELL_UPGRADE_USE_COUNT_INSUFFICIENT`
- `SPELL_UPGRADE_CHARGED_SPIRIT_INSUFFICIENT`
- `SPELL_ACTION_BATTLE_LOCKED`

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
| amount       | integer | 是   | 充灵气数量                    |

#### 成功响应

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "reason_code": "SPELL_CHARGE_SUCCEEDED",
  "reason_data": {
    "spell_id": "basic_boxing_techniques",
    "charged_amount": 100,
    "action": ""
  }
}
```

#### 失败响应

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "reason_code": "SPELL_CHARGE_PLAYER_SPIRIT_INSUFFICIENT",
  "reason_data": {
    "spell_id": "basic_boxing_techniques",
    "current_spirit": 0,
    "action": ""
  }
}
```

#### `reason_code` 枚举

- `SPELL_CHARGE_SUCCEEDED`
- `SPELL_CHARGE_NOT_OWNED`
- `SPELL_CHARGE_AT_MAX_LEVEL`
- `SPELL_CHARGE_ALREADY_FULL`
- `SPELL_CHARGE_PLAYER_SPIRIT_INSUFFICIENT`
- `SPELL_ACTION_BATTLE_LOCKED`

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
  "operation_id": "",
  "timestamp": 1234567890,
  "reason_code": "SPELL_LIST_SUCCEEDED",
  "reason_data": {},
  "player_spells": {
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

#### `reason_code` 枚举

- `SPELL_LIST_SUCCEEDED`

#### 失败响应

该接口当前无独立业务失败响应，失败通常表现为鉴权或网络异常。

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
  "reason_code": "ALCHEMY_START_SUCCEEDED",
  "reason_data": {}
}
```

#### 失败响应

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "reason_code": "ALCHEMY_START_ALREADY_ACTIVE",
  "reason_data": {}
}
```

#### `reason_code` 枚举

- `ALCHEMY_START_SUCCEEDED`
- `ALCHEMY_START_ALREADY_ACTIVE`
- `ALCHEMY_START_BLOCKED_BY_CULTIVATION`
- `ALCHEMY_START_BLOCKED_BY_BATTLE`

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
  "reason_code": "ALCHEMY_REPORT_SUCCEEDED",
  "reason_data": {
    "recipe_id": "health_pill"
  },
  "success_count": 1,
  "fail_count": 0,
  "products": {
    "health_pill": 1
  },
  "returned_materials": {}
}
```

#### 失败响应（未在炼丹状态）

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "reason_code": "ALCHEMY_REPORT_NOT_ACTIVE",
  "reason_data": {},
  "success_count": 0,
  "fail_count": 0,
  "products": {},
  "returned_materials": {}
}
```

#### 失败响应（时间不合理）

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "reason_code": "ALCHEMY_REPORT_TIME_INVALID",
  "reason_data": {
    "recipe_id": "health_pill",
    "reported_count": 1,
    "actual_interval": 2.0,
    "min_allowed_interval": 2.7,
    "invalid_report_count": 4,
    "kicked_out": false,
    "kick_threshold": 10
  },
  "success_count": 0,
  "fail_count": 0,
  "products": {},
  "returned_materials": {}
}
```

#### `reason_code` 枚举

- `ALCHEMY_REPORT_SUCCEEDED`
- `ALCHEMY_REPORT_NOT_ACTIVE`
- `ALCHEMY_REPORT_RECIPE_NOT_FOUND`
- `ALCHEMY_REPORT_RECIPE_NOT_LEARNED`
- `ALCHEMY_REPORT_TIME_INVALID`
- `ALCHEMY_REPORT_INVENTORY_UNAVAILABLE`
- `ALCHEMY_REPORT_MATERIALS_INSUFFICIENT`
- `ALCHEMY_REPORT_SPIRIT_INSUFFICIENT`

#### `reason_data` 字段说明

- `recipe_id`：丹方 ID
- `missing_materials`：材料不足时缺少的材料，结构为 `{item_id: count}`
- `required_spirit` / `current_spirit` / `missing_spirit`：灵气不足时的结构化字段
- `invalid_report_count` / `kicked_out` / `kick_threshold`：上报时间非法计数与阈值状态（`kicked_out=true` 表示服务端已执行强制下线）

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
  "reason_code": "ALCHEMY_STOP_SUCCEEDED",
  "reason_data": {}
}
```

#### 失败响应

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "reason_code": "ALCHEMY_STOP_NOT_ACTIVE",
  "reason_data": {}
}
```

#### `reason_code` 枚举

- `ALCHEMY_STOP_SUCCEEDED`
- `ALCHEMY_STOP_NOT_ACTIVE`

---

### 6.4 获取丹方列表

- **接口地址**：`GET /api/game/alchemy/recipes`
- **功能**：获取已学习的丹方列表
- **认证**：需要认证

#### 请求参数

无（通过请求头传递token）

#### 成功响应

```json
{
  "success": true,
  "operation_id": "",
  "timestamp": 1234567890,
  "reason_code": "ALCHEMY_RECIPES_SUCCEEDED",
  "reason_data": {},
  "learned_recipes": [
    "health_pill",
    "spirit_pill",
    "foundation_pill"
  ],
  "recipes_config": {
    "health_pill": {
      "name": "补血丹"
    }
  }
}
```

#### `reason_code` 枚举

- `ALCHEMY_RECIPES_SUCCEEDED`

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
  "reason_code": "LIANLI_SIMULATE_SUCCEEDED",
  "reason_data": {
    "area_id": "qi_refining_outer",
    "victory": true
  },
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
  ]
}
```

#### 失败响应（气血不足）

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "reason_code": "LIANLI_SIMULATE_HEALTH_INSUFFICIENT",
  "reason_data": {
    "area_id": "qi_refining_outer",
    "current_health": 0.0
  },
  "battle_timeline": [],
  "total_time": 0.0,
  "player_health_before": 0.0,
  "player_health_after": 0.0,
  "enemy_health_after": 0.0,
  "enemy_data": {},
  "victory": false,
  "loot": []
}
```

#### `reason_code` 枚举

- `LIANLI_SIMULATE_SUCCEEDED`
- `LIANLI_SIMULATE_BLOCKED_BY_CULTIVATION`
- `LIANLI_SIMULATE_BLOCKED_BY_ALCHEMY`
- `LIANLI_SIMULATE_HEALTH_INSUFFICIENT`
- `LIANLI_SIMULATE_TOWER_CLEARED`
- `LIANLI_SIMULATE_DAILY_LIMIT_REACHED`

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
  "reason_code": "LIANLI_FINISH_FULLY_SETTLED",
  "reason_data": {
    "is_full_settlement": true,
    "victory": true,
    "area_id": "qi_refining_outer"
  },
  "settled_index": 11,
  "total_index": 11,
  "player_health_after": 72.0,
  "loot_gained": [
    {"item_id": "spirit_stone", "amount": 1}
  ],
  "exp_gained": 0
}
```

#### 成功响应（部分结算）

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "reason_code": "LIANLI_FINISH_PARTIALLY_SETTLED",
  "reason_data": {
    "is_full_settlement": false,
    "victory": true,
    "area_id": "qi_refining_outer"
  },
  "settled_index": 5,
  "total_index": 11,
  "player_health_after": 75.0,
  "loot_gained": [],
  "exp_gained": 0
}
```

#### 失败响应（时间验证失败）

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "reason_code": "LIANLI_FINISH_TIME_INVALID",
  "reason_data": {
    "actual_time": 0.0,
    "min_allowed_time": 9.0,
    "battle_speed": 1.0,
    "settle_index": 10,
    "invalid_report_count": 2,
    "kicked_out": false,
    "kick_threshold": 10
  },
  "settled_index": 0,
  "total_index": 11,
  "player_health_after": 76.0,
  "loot_gained": [],
  "exp_gained": 0
}
```

#### `reason_code` 枚举

- `LIANLI_FINISH_FULLY_SETTLED`
- `LIANLI_FINISH_PARTIALLY_SETTLED`
- `LIANLI_FINISH_NOT_ACTIVE`
- `LIANLI_FINISH_TIME_INVALID`

#### 失败响应（未在战斗状态）

```json
{
  "success": false,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "reason_code": "LIANLI_FINISH_NOT_ACTIVE",
  "reason_data": {},
  "settled_index": 0,
  "total_index": 0,
  "player_health_after": 76.0,
  "loot_gained": [],
  "exp_gained": 0
}
```

---

### 7.3 获取破镜草洞穴信息

- **接口地址**：`GET /api/game/dungeon/foundation_herb_cave`
- **功能**：获取破镜草洞穴剩余次数和总次数
- **认证**：需要认证

#### 请求参数

无（通过请求头传递token）

#### 成功响应

```json
{
  "success": true,
  "operation_id": "",
  "timestamp": 1234567890,
  "reason_code": "LIANLI_DUNGEON_INFO_SUCCEEDED",
  "reason_data": {
    "dungeon_id": "foundation_herb_cave"
  },
  "remaining_count": 2,
  "max_count": 3
}
```

#### 失败响应

```json
{
  "success": false,
  "operation_id": "",
  "timestamp": 1234567890,
  "reason_code": "LIANLI_DUNGEON_INFO_PLAYER_NOT_FOUND",
  "reason_data": {
    "dungeon_id": "foundation_herb_cave"
  },
  "remaining_count": 0,
  "max_count": 0
}
```

#### `reason_code` 枚举

- `LIANLI_DUNGEON_INFO_SUCCEEDED`
- `LIANLI_DUNGEON_INFO_PLAYER_NOT_FOUND`

---

### 7.4 获取无尽塔信息

- **接口地址**：`GET /api/game/tower/highest_floor`
- **功能**：获取无尽塔最高层数
- **认证**：需要认证

#### 请求参数

无（通过请求头传递token）

#### 成功响应

```json
{
  "success": true,
  "operation_id": "",
  "timestamp": 1234567890,
  "reason_code": "LIANLI_TOWER_INFO_SUCCEEDED",
  "reason_data": {},
  "highest_floor": 5
}
```

#### 失败响应

```json
{
  "success": false,
  "operation_id": "",
  "timestamp": 1234567890,
  "reason_code": "LIANLI_TOWER_INFO_PLAYER_NOT_FOUND",
  "reason_data": {},
  "highest_floor": 0
}
```

#### `reason_code` 枚举

- `LIANLI_TOWER_INFO_SUCCEEDED`
- `LIANLI_TOWER_INFO_PLAYER_NOT_FOUND`

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

## 10. 测试支持 API

### 10.1 使用规则

- **接口前缀**：`/api/test/*`
- **认证方式**：使用普通玩家 token
- **调用限制**：仅测试账号 `test / test123` 可以调用，非测试账号会直接返回 `403`
- **用途**：为服务端伪流程测试和后续客户端自动化测试快速构造精确状态

### 10.2 测试接口列表

- `POST /api/test/reset_account`
  - 重置测试账号到统一初始化状态，并补发 1 个测试礼包
- `POST /api/test/set_player_state`
  - 设置 `realm / realm_level / spirit_energy / health`
- `POST /api/test/set_inventory_items`
  - 以 `{item_id: count}` 精确设置背包
- `POST /api/test/unlock_content`
  - 解锁术法、丹方、丹炉
- `POST /api/test/set_equipped_spells`
  - 精确设置 `breathing / active / opening` 三类槽位
- `POST /api/test/set_progress_state`
  - 设置无尽塔层数和每日副本剩余次数
- `POST /api/test/set_runtime_state`
  - 设置修炼/炼丹/历练相关轻量运行态
- `POST /api/test/apply_preset`
  - 一键应用预设场景
- `POST /api/test/grant_test_pack`
  - 给测试账号补发测试礼包
- `GET /api/test/state_summary`
  - 获取当前测试账号状态摘要

### 10.3 统一响应格式

```json
{
  "success": true,
  "operation_id": "uuid",
  "timestamp": 1234567890,
  "reason_code": "TEST_RESET_ACCOUNT_SUCCEEDED",
  "reason_data": {},
  "state_summary": {
    "player": {
      "realm": "炼气期",
      "realm_level": 1,
      "health": 402.0,
      "spirit_energy": 0.0
    }
  }
}
```

### 10.4 `apply_preset` 支持的预设

- `breakthrough_ready`
- `alchemy_ready`
- `spell_ready`
- `lianli_ready`
- `tower_ready`
- `full_unlock`

### 10.5 测试礼包规则

- `test_pack` 只对测试账号发放
- 普通账号初始化不再自动获得测试礼包
- 测试账号首次初始化、`reset_account`、`grant_test_pack` 时会获得测试礼包
- 测试礼包主要用于人工验收，不作为自动化测试的基础前置

---

## 11. 测试账号

- **测试账号**：test / test123
- **管理员账号**：admin / admin123

---

## 12. 服务信息

- **服务地址**：http://127.0.0.1:8444
- **API 文档**：http://127.0.0.1:8444/api/docs
- **版本**：v1.0.0
