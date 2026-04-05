# Idle Cultivation Server

修仙挂机游戏的服务端实现，基于 Python + FastAPI。

## 项目特性

- ✅ **完整的游戏系统**：修炼、术法、背包、炼丹、历练等多个游戏系统
- ✅ **JWT认证**：基于JWT的用户认证和授权机制
- ✅ **防作弊系统**：修炼上报时间验证、可疑操作记录
- ✅ **离线奖励**：根据离线时间计算离线奖励
- ✅ **模块化设计**：清晰的功能模块划分，便于维护和扩展
- ✅ **完整的API文档**：详细的API接口文档和参数说明
- ✅ **集成测试**：完整的集成测试覆盖所有核心功能

## 技术栈

- **服务端**：Python 3.12 + FastAPI
- **数据库**：PostgreSQL
- **ORM**：Tortoise-ORM
- **认证**：JWT Token
- **API 文档**：Swagger UI
- **日志**：自定义日志系统

## 项目结构

```
idle_cultivation_server/
├── main.py                     # 入口文件
├── app/
│   ├── main.py                 # FastAPI 应用实例
│   ├── api/                    # API 路由
│   │   ├── game_base.py        # 游戏基础功能API（含排行榜）
│   │   └── admin.py            # 管理后台相关
│   ├── modules/                # 功能模块
│   │   ├── account/            # 账号模块
│   │   │   ├── AccountApi.py   # 账号API（注册、登录、登出等）
│   │   │   └── AccountSystem.py # 账号系统逻辑
│   │   ├── cultivation/        # 修炼模块
│   │   │   ├── CultivationApi.py      # 修炼API
│   │   │   ├── CultivationSystem.py   # 修炼系统逻辑
│   │   │   └── RealmData.py           # 境界数据
│   │   ├── spell/              # 术法模块
│   │   │   ├── SpellApi.py     # 术法API
│   │   │   ├── SpellSystem.py  # 术法系统逻辑
│   │   │   └── SpellData.py    # 术法数据
│   │   ├── inventory/          # 背包模块
│   │   │   ├── InventoryApi.py # 背包API
│   │   │   ├── InventorySystem.py # 背包系统逻辑
│   │   │   └── ItemData.py     # 物品数据
│   │   ├── alchemy/            # 炼丹模块
│   │   │   ├── AlchemyApi.py   # 炼丹API
│   │   │   ├── AlchemySystem.py # 炼丹系统逻辑
│   │   │   ├── AlchemyWorkshop.py # 炼丹工坊逻辑
│   │   │   └── RecipeData.py   # 丹方数据
│   │   ├── lianli/             # 历练模块
│   │   │   ├── LianliApi.py    # 历练API
│   │   │   ├── LianliSystem.py # 历练系统逻辑
│   │   │   ├── AreasData.py    # 区域数据
│   │   │   └── EnemiesData.py  # 敌人数据
│   │   └── player/             # 玩家模块
│   │       ├── PlayerSystem.py # 玩家系统逻辑
│   │       └── AttributeCalculator.py # 属性计算器
│   ├── core/                   # 核心模块
│   │   ├── ServerConfig.py     # 配置管理
│   │   ├── Security.py         # 安全相关（JWT认证）
│   │   ├── Validator.py        # 数据验证工具
│   │   ├── AntiCheatSystem.py  # 防作弊系统
│   │   ├── Logger.py           # 日志管理
│   │   ├── InitPlayerInfo.py   # 玩家初始化信息
│   │   └── config_loader.py    # 配置文件加载
│   ├── db/                     # 数据库相关
│   │   ├── Database.py         # 数据库连接
│   │   └── Models.py           # 数据模型
│   └── schemas/                # 数据验证模型
│       ├── base.py             # 基础请求/响应模型
│       ├── auth.py             # 认证相关
│       └── game.py             # 游戏数据相关
├── config/                     # 配置文件软链接
│   ├── items.json
│   ├── realms.json
│   ├── recipes.json
│   └── spells.json
├── docs/                       # 文档
│   ├── api_documentation.md    # API详细文档
│   └── security_system.md      # 服务安全系统文档
├── unit_test/                  # 单元测试
│   └── integration_test.py     # 集成测试
├── sql/                        # SQL 脚本
│   └── init.sql                # 数据库初始化脚本
├── start.sh                    # 启动脚本
├── requirements.txt            # 依赖包
└── README.md                   # 项目说明
```

## 快速开始

### 1. 环境搭建

#### 安装依赖

```bash
# 创建虚拟环境
python3.12 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

#### 安装 PostgreSQL

- **Linux**：`sudo apt install postgresql postgresql-contrib`
- **Mac**：`brew install postgresql`
- **Windows**：从官网下载安装包

#### 创建数据库

```bash
# 创建数据库
createdb idle_cultivation_game

# 初始化表结构
psql -d idle_cultivation_game -f sql/init.sql
```

### 2. 运行服务

```bash
# 启动服务（后台运行）
bash start.sh

# 查看服务状态
ps aux | grep uvicorn

# 查看服务日志
tail -f server.log
```

服务将在 `http://127.0.0.1:8444` 运行。

### 3. 访问 API 文档

打开浏览器访问：`http://127.0.0.1:8444/api/docs`

## API 接口

详细的API文档请查看：[API Documentation](docs/api_documentation.md)

### 认证系统

- `POST /api/auth/register` - 注册账号
- `POST /api/auth/login` - 登录账号
- `POST /api/auth/refresh` - Token 续期
- `POST /api/auth/logout` - 登出
- `POST /api/auth/change_password` - 修改密码
- `POST /api/auth/change_nickname` - 修改昵称
- `POST /api/auth/change_avatar` - 修改头像

### 修炼系统

- `POST /api/game/player/cultivation/start` - 开始修炼
- `POST /api/game/player/cultivation/report` - 上报修炼进度
- `POST /api/game/player/breakthrough` - 突破境界

### 术法系统

- `POST /api/game/spell/equip` - 装备术法
- `POST /api/game/spell/unequip` - 卸下术法
- `POST /api/game/spell/upgrade` - 升级术法
- `POST /api/game/spell/charge` - 充灵气
- `GET /api/game/spell/list` - 获取术法列表

### 背包系统

- `POST /api/game/inventory/use` - 使用物品
- `POST /api/game/inventory/organize` - 整理背包
- `POST /api/game/inventory/discard` - 丢弃物品

### 炼丹系统

- `POST /api/game/alchemy/start` - 开始炼丹
- `POST /api/game/alchemy/report` - 炼丹上报
- `POST /api/game/alchemy/stop` - 停止炼丹
- `POST /api/game/alchemy/learn_recipe` - 学习丹方
- `GET /api/game/alchemy/recipes` - 获取丹方列表

### 历练系统

- `POST /api/game/lianli/simulate` - 战斗模拟
- `POST /api/game/lianli/finish` - 战斗结算
- `GET /api/game/lianli/foundation_herb_cave` - 获取破镜草洞穴信息
- `GET /api/game/lianli/tower` - 获取无尽塔信息

### 游戏基础功能

- `GET /api/game/data` - 加载游戏数据
- `POST /api/game/save` - 保存游戏数据
- `POST /api/game/claim_offline_reward` - 领取离线奖励
- `GET /api/game/rank` - 获取排行榜

### 管理后台

- `POST /api/admin/login` - 管理员登录
- `GET /api/admin/players` - 获取玩家列表
- `GET /api/admin/player/{id}` - 获取玩家详情
- `POST /api/admin/player/{id}/ban` - 封号

## 测试账号

- **用户名**：test
- **密码**：test123
- **用途**：预置的测试用户账号，用于测试游戏功能
- **定义位置**：`sql/init.sql`（数据库初始化时自动创建）

## 管理员账号

- **用户名**：admin
- **密码**：admin123
- **用途**：管理员登录后台管理系统（查看玩家、封号等）
- **定义位置**：`app/api/admin.py`（硬编码在代码中）

⚠️ **安全警告**：这两个账号仅用于开发测试，生产环境请务必：
1. 删除或修改测试账号密码
2. 将管理员密码改为从环境变量读取
3. 使用强密码并定期更换

## 运行测试

项目包含完整的集成测试，覆盖所有核心功能：

```bash
# 运行集成测试
cd idle_cultivation_server
python3 -m unit_test.integration_test
```

测试覆盖的功能：
- ✅ 用户注册和登录
- ✅ 游戏数据加载和保存
- ✅ 修炼系统（开始修炼、上报修炼、突破境界）
- ✅ 术法系统（装备、卸下、升级、充灵气）
- ✅ 背包系统（使用物品、整理、丢弃）
- ✅ 炼丹系统（炼制丹药、学习丹方）
- ✅ 历练系统（战斗模拟、战斗结算、防作弊验证）
- ✅ 离线奖励领取
- ✅ 防作弊测试

## 开发说明

### 代码规范

- **文件命名**：核心文件使用PascalCase（如`ServerConfig.py`、`Database.py`、`Models.py`）
- **类命名**：使用PascalCase
- **函数命名**：使用snake_case
- **常量命名**：使用UPPER_SNAKE_CASE

### Schema设计

所有请求和响应模型都继承自基础模型：

- **BaseRequest**：包含`operation_id`（UUID）和`timestamp`（Unix时间戳）
- **BaseResponse**：包含`success`、`operation_id`、`timestamp`

**例外**：注册接口不需要`operation_id`和`timestamp`

### 浮点数精度

游戏中所有涉及浮点数的计算都保留两位小数：

- **静态属性计算**：攻击力、防御力、速度、最大气血、最大灵气等
- **伤害计算**：所有伤害值都保留两位小数
- **气血和灵气变化**：增加、扣除、治疗等操作都保留两位小数
- **战斗数据**：玩家和敌人的生命值变化都保留两位小数

**实现位置**：
- `AttributeCalculator.py`：所有静态属性计算方法
- `PlayerSystem.py`：气血和灵气的增减方法
- `LianliSystem.py`：战斗中的伤害和治疗计算

### 时间戳处理

- **数据库时间戳**：使用`datetime.now(timezone.utc)`，存储为UTC时区
- **客户端时间戳**：使用Unix时间戳（秒）
- **修炼系统时间戳**：使用`time.time()`返回UTC Unix时间戳

## 许可证

MIT License