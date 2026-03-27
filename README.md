# Idle Cultivation Server

修仙挂机游戏的服务端实现，基于 Python + FastAPI。

## 技术栈

- **服务端**：Python 3.12 + FastAPI
- **数据库**：PostgreSQL
- **ORM**：Tortoise-ORM
- **认证**：JWT Token
- **API 文档**：Swagger UI

## 项目结构

```
idle_cultivation_server/
├── main.py                     # 入口文件
├── app/
│   ├── main.py                 # FastAPI 应用实例
│   ├── api/                    # API 路由
│   │   ├── auth.py             # 认证相关
│   │   ├── game.py             # 游戏数据相关
│   │   └── admin.py            # 管理后台相关
│   ├── core/                   # 核心模块
│   │   ├── config.py           # 配置管理
│   │   ├── security.py         # 安全相关
│   │   └── config_loader.py    # 配置文件加载
│   ├── db/                     # 数据库相关
│   │   ├── database.py         # 数据库连接
│   │   └── models.py           # 数据模型
│   └── schemas/                # 数据验证模型
│       ├── auth.py             # 认证相关
│       └── game.py             # 游戏数据相关
├── config/                     # 配置文件软链接
│   ├── items.json
│   ├── realms.json
│   ├── recipes.json
│   └── spells.json
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

### 认证相关

- `POST /api/auth/register` - 注册账号
- `POST /api/auth/login` - 登录账号
- `POST /api/auth/refresh` - Token 续期
- `POST /api/auth/logout` - 登出

### 游戏数据相关

- `GET /api/game/data` - 加载游戏数据
- `POST /api/game/save` - 保存游戏数据
- `POST /api/game/player/breakthrough` - 突破境界
- `POST /api/game/inventory/use_item` - 使用物品
- `POST /api/game/battle/victory` - 战斗胜利
- `GET /api/game/dungeon/info` - 获取副本信息
- `POST /api/game/dungeon/finish` - 完成副本（扣减次数）
- `POST /api/game/claim_offline_reward` - 领取离线奖励
- `GET /api/game/rank` - 获取排行榜

### 管理后台相关

- `POST /api/admin/login` - 管理员登录
- `GET /api/admin/players` - 获取玩家列表
- `GET /api/admin/player/{id}` - 获取玩家详情
- `POST /api/admin/player/{id}/ban` - 封号

## 测试账号

- **用户名**：test
- **密码**：test123

## 管理员账号

- **用户名**：admin
- **密码**：admin123