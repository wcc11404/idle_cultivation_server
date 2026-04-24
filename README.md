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

## 当前结构

```text
idle_cultivation_server/
├── app/
│   ├── api/                # 基础路由与测试支持路由
│   ├── core/               # 配置、安全、依赖、日志、初始化
│   ├── db/                 # 数据库连接与模型
│   ├── modules/            # 业务模块
│   └── schemas/            # 请求/响应 schema
├── docs/                   # 开发文档（API 手册单独保留）
├── sql/                    # 数据库初始化脚本
├── unit_test/              # pytest 与 smoke 支持
├── util/                   # 手工运维/调试脚本
├── setup_ubuntu.sh         # 一键安装
├── restart.sh              # 一键启动/重启
└── stop.sh                 # 一键停止
```
