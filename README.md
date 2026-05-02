# Idle Cultivation Server

修仙挂机游戏服务端，基于 Python + FastAPI + PostgreSQL。

首次进入仓库时，先看 [docs/快速开发手册.md](/Users/hsams/Documents/idle_cultivation_project/idle_cultivation_server/docs/快速开发手册.md)。

## 快速开始

### Ubuntu / 腾讯云

```bash
cd idle_cultivation_server
bash setup_ubuntu.sh
bash restart.sh
```

### 本地开发

```bash
cd idle_cultivation_server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
bash restart.sh
```

服务默认运行在 `http://localhost:8444`，Swagger 文档地址为 `http://localhost:8444/api/docs`。

如果已经接入并构建运维前端，运维网页入口为 `http://localhost:8444/ops`。

## 常用命令

```bash
# 启动 / 重启服务
bash restart.sh

# 停止服务
bash stop.sh

# 查看日志
tail -f server.log

# 跑服务端测试
pytest unit_test

# 运行复杂 smoke 脚本
python -m unit_test.integration_test
```

## 文档入口

- 快速导览与开发约定：
  [docs/快速开发手册.md](/Users/hsams/Documents/idle_cultivation_project/idle_cultivation_server/docs/快速开发手册.md)
- 安装、部署、启动与排障：
  [docs/03-operations/安装与启动手册.md](/Users/hsams/Documents/idle_cultivation_project/idle_cultivation_server/docs/03-operations/安装与启动手册.md)
- API 真值手册：
  [docs/05-api/api_documentation.md](/Users/hsams/Documents/idle_cultivation_project/idle_cultivation_server/docs/05-api/api_documentation.md)
- 安全系统专项：
  [docs/04-security/security_system.md](/Users/hsams/Documents/idle_cultivation_project/idle_cultivation_server/docs/04-security/security_system.md)
- 运维系统安装与启动：
  [docs/03-operations/运维系统安装与启动手册.md](/Users/hsams/Documents/idle_cultivation_project/idle_cultivation_server/docs/03-operations/运维系统安装与启动手册.md)
- 数据库与表结构说明：
  [docs/03-operations/数据库与表结构说明.md](/Users/hsams/Documents/idle_cultivation_project/idle_cultivation_server/docs/03-operations/数据库与表结构说明.md)

## 当前结构

```text
idle_cultivation_server/
├── app/
│   ├── admin_support/      # 历史管理接口兼容层
│   ├── bootstrap/          # 顶层路由装配
│   ├── core/               # 配置、安全、数据库、日志、资源、写锁
│   ├── game/               # 游戏正式主线
│   ├── ops/                # 正式运维后台域
│   └── test_support/       # 测试支持接口与引导逻辑
├── docs/                   # 开发文档（API 手册单独保留）
├── ops_web/                # 运维前端（React + Vite）
├── sql/                    # 数据库初始化总入口与 schema 子系统分片
├── unit_test/              # pytest 与 smoke 支持
├── util/                   # 手工运维/调试脚本
├── setup_ubuntu.sh         # 一键安装
├── restart.sh              # 一键启动/重启
└── stop.sh                 # 一键停止
```
