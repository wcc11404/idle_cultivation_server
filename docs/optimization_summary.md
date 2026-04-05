# 服务端代码优化总结

## 优化概述

在不改变现有业务逻辑的前提下，对服务端代码进行了架构优化，主要目标是减少重复代码、提高代码可维护性和可读性。

## 主要优化点

### 1. 依赖注入优化

**问题：** 每个API都重复进行以下操作：
- Token解码和验证
- 玩家数据加载
- 各个游戏系统的初始化

**解决方案：** 创建统一的依赖注入函数

**新增文件：** `app/core/Dependencies.py`

**核心类：**
```python
@dataclass
class GameContext:
    """游戏上下文，包含所有游戏系统"""
    account: Account
    player_data: PlayerData
    db_data: Dict[str, Any]
    player: PlayerSystem
    spell_system: SpellSystem
    inventory_system: InventorySystem
    alchemy_system: AlchemySystem
    lianli_system: LianliSystem
    account_system: AccountSystem
```

**使用方式：**
```python
# 优化前
@router.post("/lianli/simulate")
async def simulate_battle(request: LianliBattleRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    
    player_data = await DBPlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        raise HTTPException(...)
    
    db_data = player_data.data
    player = PlayerSystem.from_dict(db_data.get("player", {}))
    spell_system = SpellSystem.from_dict(db_data.get("spell_system", {}))
    lianli_system = LianliSystem.from_dict(db_data.get("lianli_system", {}))
    alchemy_system = AlchemySystem.from_dict(db_data.get("alchemy_system", {}))
    # ... 业务逻辑

# 优化后
@router.post("/lianli/simulate")
async def simulate_battle(
    request: LianliBattleRequest,
    ctx: GameContext = Depends(get_game_context),
    token_info: dict = Depends(get_token_info)
):
    # 直接使用 ctx.player, ctx.spell_system 等
    # ... 业务逻辑
```

**优势：**
- 减少每个API约15-20行重复代码
- 统一的错误处理
- 更清晰的代码结构

### 2. 响应构建优化

**问题：** 构建API响应时存在大量重复字段赋值

**解决方案：** 创建响应构建辅助函数

**新增文件：** `app/core/ResponseBuilder.py`

**示例：**
```python
# 优化前
response_data = LianliBattleResponse(
    success=False,
    operation_id=request.operation_id,
    timestamp=request.timestamp,
    battle_timeline=[],
    total_time=0.0,
    player_health_before=0.0,
    player_health_after=0.0,
    enemy_health_after=0.0,
    enemy_data={},
    victory=False,
    loot=[],
    message="正在修炼中，无法开始战斗"
)

# 优化后
response_data = build_lianli_battle_failure_response(
    request.operation_id, request.timestamp, "正在修炼中，无法开始战斗"
)
```

**优势：**
- 减少响应构建代码量
- 统一响应格式
- 更容易维护和修改

### 3. 数据保存优化

**问题：** 多个API都有相似的数据保存逻辑

**解决方案：** 在GameContext中添加save()方法

```python
# 优化前
db_data["player"] = player.to_dict()
db_data["spell_system"] = spell_system.to_dict()
db_data["inventory"] = inventory_system.to_dict()
db_data["alchemy_system"] = alchemy_system.to_dict()
db_data["lianli_system"] = lianli_system.to_dict()
db_data["account_info"] = account_system.to_dict()

# 优化后
ctx.save()
```

## 代码对比示例

### LianliApi.py 优化对比

**优化前行数：** ~180行
**优化后行数：** ~70行
**代码减少：** 约60%

**优化前：**
```python
@router.post("/lianli/simulate", response_model=LianliBattleResponse)
async def simulate_battle(request: LianliBattleRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """历练战斗模拟"""
    start_time = time.time()
    token = credentials.credentials
    payload = decode_token(token)
    account_id = payload.get("account_id")
    token_version = payload.get("version")
    current_user = await get_current_user(credentials)
    logger.info(f"[IN] POST /game/lianli/battle - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token} - account_id: {account_id} - token_version: {token_version}")
    
    player_data = await DBPlayerData.get_or_none(account_id=current_user.id)
    if not player_data:
        logger.warning(f"[GAME] 玩家数据不存在 - account_id: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="玩家数据不存在"
        )
    
    db_data = player_data.data
    
    player = PlayerSystem.from_dict(db_data.get("player", {}))
    spell_system = SpellSystem.from_dict(db_data.get("spell_system", {}))
    lianli_system = LianliSystem.from_dict(db_data.get("lianli_system", {}))
    alchemy_system = AlchemySystem.from_dict(db_data.get("alchemy_system", {}))
    
    if player.is_cultivating:
        response_data = LianliBattleResponse(
            success=False,
            operation_id=request.operation_id,
            timestamp=request.timestamp,
            battle_timeline=[],
            total_time=0.0,
            player_health_before=0.0,
            player_health_after=0.0,
            enemy_health_after=0.0,
            enemy_data={},
            victory=False,
            loot=[],
            message="正在修炼中，无法开始战斗"
        )
        logger.info(f"[OUT] POST /game/lianli/battle - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    # ... 更多重复代码
```

**优化后：**
```python
@router.post("/lianli/simulate", response_model=LianliBattleResponse)
async def simulate_battle(
    request: LianliBattleRequest,
    ctx: GameContext = Depends(get_game_context),
    token_info: dict = Depends(get_token_info)
):
    """历练战斗模拟（优化版）"""
    start_time = time.time()
    logger.info(f"[IN] POST /game/lianli/battle - {json.dumps(request.dict(), ensure_ascii=False)} - token: {token_info['token']} - account_id: {token_info['account_id']} - token_version: {token_info['token_version']}")
    
    if ctx.player.is_cultivating:
        response_data = build_lianli_battle_failure_response(
            request.operation_id, request.timestamp, "正在修炼中，无法开始战斗"
        )
        logger.info(f"[OUT] POST /game/lianli/battle - {json.dumps(response_data.dict(), ensure_ascii=False)} - 耗时：{time.time() - start_time:.4f}s")
        return response_data
    
    # ... 业务逻辑更清晰
```

## 其他优化建议

### 1. 日志记录优化

**建议：** 创建日志装饰器，自动记录API的进入和退出

```python
def log_api_call(api_name: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            logger.info(f"[IN] {api_name}")
            result = await func(*args, **kwargs)
            logger.info(f"[OUT] {api_name} - 耗时：{time.time() - start_time:.4f}s")
            return result
        return wrapper
    return decorator

# 使用
@router.post("/lianli/simulate")
@log_api_call("POST /game/lianli/battle")
async def simulate_battle(...):
    # 业务逻辑
```

### 2. 异常处理优化

**建议：** 创建统一的异常处理器

```python
from fastapi import Request
from fastapi.responses import JSONResponse

class GameException(Exception):
    def __init__(self, message: str, error_code: int = 400):
        self.message = message
        self.error_code = error_code

@app.exception_handler(GameException)
async def game_exception_handler(request: Request, exc: GameException):
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "message": exc.message,
            "error_code": exc.error_code
        }
    )
```

### 3. 配置管理优化

**建议：** 将硬编码的配置值提取到配置文件

```python
# 当前
if actual_time < expected_time * 0.9:

# 建议
BATTLE_TIME_TOLERANCE = 0.9  # 在配置文件中
if actual_time < expected_time * BATTLE_TIME_TOLERANCE:
```

## 实施建议

### 渐进式迁移

1. **第一阶段：** 保留现有API文件，创建优化版本（如LianliApi_optimized.py）
2. **第二阶段：** 在测试环境验证优化版本
3. **第三阶段：** 逐步替换原API文件
4. **第四阶段：** 删除优化版本文件，保留最终版本

### 测试策略

1. **单元测试：** 为新增的依赖注入函数和响应构建函数编写单元测试
2. **集成测试：** 使用现有的integration_test.py验证优化后的API
3. **性能测试：** 对比优化前后的响应时间

## 总结

通过这次优化，主要改进了：

1. **代码复用性：** 通过依赖注入和辅助函数，大幅减少重复代码
2. **可维护性：** 统一的代码结构，更容易理解和修改
3. **可测试性：** 依赖注入使得单元测试更容易编写
4. **可扩展性：** 新增功能时可以复用现有的基础设施

**估算收益：**
- 代码量减少约40-50%
- 新API开发时间减少约30%
- Bug修复时间减少约20%（因为需要检查的代码更少）

**注意事项：**
- 保持向后兼容，不改变API接口
- 充分测试，确保业务逻辑不变
- 渐进式迁移，降低风险
