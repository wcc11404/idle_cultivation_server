# 修仙挂机游戏服务端 API 文档

## 1. 认证相关接口

### 1.1 注册账号
- **接口地址**：`POST /api/auth/register`
- **功能**：注册新账号
- **请求参数**：
  | 字段 | 类型 | 必选 | 说明 |
  |------|------|------|------|
  | username | string | 是 | 用户名（20字符以内） |
  | password | string | 是 | 密码 |
- **响应格式**：
  ```json
  {
    "success": true,
    "account_id": "uuid",
    "message": "注册成功"
  }
  ```

### 1.2 登录账号
- **接口地址**：`POST /api/auth/login`
- **功能**：登录账号并获取 JWT Token
- **请求参数**：
  | 字段 | 类型 | 必选 | 说明 |
  |------|------|------|------|
  | username | string | 是 | 用户名 |
  | password | string | 是 | 密码 |
- **响应格式**：
  ```json
  {
    "success": true,
    "token": "jwt_token",
    "expires_in": 604800,
    "account_info": {
      "id": "uuid",
      "username": "testuser",
      "server_id": "default"
    },
    "data": {
      "player": { ... },
      "inventory": { ... },
      "spell_system": { ... },
      "alchemy_system": { ... },
      "lianli_system": { ... }
    }
  }
  ```

### 1.3 Token 续期
- **接口地址**：`POST /api/auth/refresh`
- **功能**：刷新 JWT Token
- **请求头**：
  | 字段 | 类型 | 必选 | 说明 |
  |------|------|------|------|
  | Authorization | string | 是 | Bearer {token} |
- **响应格式**：
  ```json
  {
    "success": true,
    "token": "new_jwt_token",
    "expires_in": 604800
  }
  ```

### 1.4 登出
- **接口地址**：`POST /api/auth/logout`
- **功能**：登出账号
- **请求头**：
  | 字段 | 类型 | 必选 | 说明 |
  |------|------|------|------|
  | Authorization | string | 是 | Bearer {token} |
- **响应格式**：
  ```json
  {
    "success": true,
    "message": "登出成功"
  }
  ```

### 2.6 领取离线奖励
- **接口地址**：`POST /api/game/claim_offline_reward`
- **功能**：验证并发放离线奖励（计算逻辑由客户端处理）
- **请求头**：
  | 字段 | 类型 | 必选 | 说明 |
  |------|------|------|------|
  | Authorization | string | 是 | Bearer {token} |
- **请求参数**：
  | 字段 | 类型 | 必选 | 说明 |
  |------|------|------|------|
  | offline_seconds | number | 是 | 离线时间（秒），最大14400（4小时） |
- **响应格式**：
  
  **成功且有奖励**：
  ```json
  {
    "success": true,
    "offline_reward": {
      "spirit_energy": 47,
      "spirit_stones": 1
    },
    "offline_seconds": 474,
    "message": "领取成功"
  }
  ```
  
  **成功但无奖励**：
  ```json
  {
    "success": true,
    "offline_reward": null,
    "offline_seconds": 30,
    "message": "离线时间不足，无法领取奖励"
  }
  ```
  
  **获取失败**：
  ```json
  {
    "detail": "INVALID_OFFLINE_SECONDS"
  }
  ```

## 2. 游戏相关接口

### 2.1 加载游戏数据
- **接口地址**：`GET /api/game/data`
- **功能**：加载玩家游戏数据
- **请求头**：
  | 字段 | 类型 | 必选 | 说明 |
  |------|------|------|------|
  | Authorization | string | 是 | Bearer {token} |
- **响应格式**：
  ```json
  {
    "success": true,
    "data": {
      "player": { ... },
      "inventory": { ... },
      "spell_system": { ... },
      "alchemy_system": { ... },
      "lianli_system": { ... }
    }
  }
  ```

### 2.2 保存游戏数据
- **接口地址**：`POST /api/game/save`
- **功能**：保存玩家游戏数据
- **请求头**：
  | 字段 | 类型 | 必选 | 说明 |
  |------|------|------|------|
  | Authorization | string | 是 | Bearer {token} |
- **请求参数**：
  | 字段 | 类型 | 必选 | 说明 |
  |------|------|------|------|
  | data | object | 是 | 完整的游戏数据 |
- **响应格式**：
  ```json
  {
    "success": true,
    "last_online_at": 1678900000
  }
  ```

### 2.3 突破境界
- **接口地址**：`POST /api/game/player/breakthrough`
- **功能**：玩家突破境界
- **请求头**：
  | 字段 | 类型 | 必选 | 说明 |
  |------|------|------|------|
  | Authorization | string | 是 | Bearer {token} |
- **请求参数**：
  | 字段 | 类型 | 必选 | 说明 |
  |------|------|------|------|
  | current_realm | string | 是 | 当前境界 |
  | current_level | number | 是 | 当前等级 |
- **响应格式**：
  ```json
  {
    "success": true,
    "new_realm": "筑基期",
    "new_level": 1,
    "remaining_spirit_energy": 0.0,
    "materials_used": { "spirit_stone": 100 }
  }
  ```

### 2.4 使用物品
- **接口地址**：`POST /api/game/inventory/use_item`
- **功能**：使用物品
- **请求头**：
  | 字段 | 类型 | 必选 | 说明 |
  |------|------|------|------|
  | Authorization | string | 是 | Bearer {token} |
- **请求参数**：
  | 字段 | 类型 | 必选 | 说明 |
  |------|------|------|------|
  | item_id | string | 是 | 物品ID |
- **响应格式**：
  ```json
  {
    "success": true,
    "effect": { "health": 100 },
    "contents": { "spirit_stone": 100, "health_pill": 5 }
  }
  ```

### 2.5 战斗胜利
- **接口地址**：`POST /api/game/battle/victory`
- **功能**：战斗胜利结算
- **请求头**：
  | 字段 | 类型 | 必选 | 说明 |
  |------|------|------|------|
  | Authorization | string | 是 | Bearer {token} |
- **请求参数**：
  | 字段 | 类型 | 必选 | 说明 |
  |------|------|------|------|
  | is_tower | boolean | 是 | 是否是塔防 |
  | tower_floor | number | 否 | 塔防楼层（is_tower为true时必填） |
- **响应格式**：
  ```json
  {
    "success": true,
    "loot": [
      { "item_id": "spirit_stone", "amount": 20 },
      { "item_id": "health_pill", "amount": 2 }
    ],
    "new_highest_floor": 5
  }
  ```

## 3. 管理后台接口

### 3.1 管理员登录
- **接口地址**：`POST /api/admin/login`
- **功能**：管理员登录
- **请求参数**：
  | 字段 | 类型 | 必选 | 说明 |
  |------|------|------|------|
  | username | string | 是 | 管理员用户名 |
  | password | string | 是 | 管理员密码 |
- **响应格式**：
  ```json
  {
    "success": true,
    "token": "admin_jwt_token",
    "expires_in": 604800
  }
  ```

### 3.2 获取玩家列表
- **接口地址**：`GET /api/admin/players`
- **功能**：获取所有玩家列表
- **请求头**：
  | 字段 | 类型 | 必选 | 说明 |
  |------|------|------|------|
  | Authorization | string | 是 | Bearer {token} |
- **响应格式**：
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

### 3.3 获取玩家详情
- **接口地址**：`GET /api/admin/player/{id}`
- **功能**：获取指定玩家详情
- **请求头**：
  | 字段 | 类型 | 必选 | 说明 |
  |------|------|------|------|
  | Authorization | string | 是 | Bearer {token} |
- **路径参数**：
  | 字段 | 类型 | 必选 | 说明 |
  |------|------|------|------|
  | id | string | 是 | 玩家账号ID |
- **响应格式**：
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
        "player": { ... },
        "inventory": { ... }
      }
    }
  }
  ```

### 3.4 封号
- **接口地址**：`POST /api/admin/player/{id}/ban`
- **功能**：封禁玩家账号
- **请求头**：
  | 字段 | 类型 | 必选 | 说明 |
  |------|------|------|------|
  | Authorization | string | 是 | Bearer {token} |
- **路径参数**：
  | 字段 | 类型 | 必选 | 说明 |
  |------|------|------|------|
  | id | string | 是 | 玩家账号ID |
- **响应格式**：
  ```json
  {
    "success": true,
    "message": "封号成功"
  }
  ```

## 4. 通用响应格式

### 4.1 成功响应
```json
{
  "success": true,
  "...": "其他数据"
}
```

### 4.2 错误响应
```json
{
  "detail": "错误信息"
}
```

## 5. 测试账号

- **测试账号**：test / test123
- **管理员账号**：admin / admin123

## 6. 服务信息

- **服务地址**：http://127.0.0.1:8444
- **API 文档**：http://127.0.0.1:8444/api/docs
- **版本**：v1.0.0