#!/usr/bin/env bash
set -euo pipefail

# Ubuntu 一键环境安装脚本（腾讯云可直接使用）
# 用途：
# 1) 安装系统依赖（Python/PostgreSQL/构建工具）
# 2) 创建并安装 Python venv 依赖
# 3) 初始化数据库（首次）
# 4) 可选启动服务
#
# 用法：
#   bash setup_ubuntu.sh
#   bash setup_ubuntu.sh --start
#   bash setup_ubuntu.sh --skip-apt
#   bash setup_ubuntu.sh --recreate-venv   # 可选：强制重建
#   bash setup_ubuntu.sh --with-ops-web    # 安装 Node/npm 并构建 ops_web
#   bash setup_ubuntu.sh --init-ops-db     # 初始化运维相关表与引导账号

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

DB_NAME="idle_cultivation_game"
DB_USER="postgres"
DB_PASS="postgres"

SKIP_APT=0
START_AFTER_SETUP=0
RECREATE_VENV=0
WITH_OPS_WEB=0
INIT_OPS_DB=0
SKIP_OPS_WEB_BUILD=0

for arg in "$@"; do
  case "$arg" in
    --skip-apt)
      SKIP_APT=1
      ;;
    --start)
      START_AFTER_SETUP=1
      ;;
    --recreate-venv)
      RECREATE_VENV=1
      ;;
    --with-ops-web)
      WITH_OPS_WEB=1
      ;;
    --init-ops-db)
      INIT_OPS_DB=1
      ;;
    --skip-ops-web-build)
      SKIP_OPS_WEB_BUILD=1
      ;;
    *)
      echo "未知参数: $arg"
      echo "支持参数: --skip-apt --start --recreate-venv --with-ops-web --init-ops-db --skip-ops-web-build"
      exit 1
      ;;
  esac
done

log() {
  echo "[setup] $1"
}

run_as_postgres() {
  sudo -u postgres psql -v ON_ERROR_STOP=1 "$@"
}

is_venv_healthy() {
  if [[ ! -d "venv" ]]; then
    return 1
  fi
  if [[ ! -e "venv/bin/python" ]]; then
    return 1
  fi
  if ! venv/bin/python -V >/dev/null 2>&1; then
    return 1
  fi
  if ! venv/bin/python -m pip -V >/dev/null 2>&1; then
    return 1
  fi
  return 0
}

if [[ ! -f "requirements.txt" ]]; then
  echo "未在服务端根目录运行（缺少 requirements.txt）"
  exit 1
fi

if [[ "$SKIP_APT" -eq 0 ]]; then
  log "安装系统依赖（apt）..."
  sudo apt-get update
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3 \
    python3-venv \
    python3-pip \
    postgresql \
    postgresql-contrib \
    build-essential \
    lsof \
    curl
  if [[ "$WITH_OPS_WEB" -eq 1 ]]; then
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y nodejs npm
  fi
else
  log "跳过 apt 安装（--skip-apt）"
fi

log "启动并设置 PostgreSQL 开机自启..."
sudo systemctl enable postgresql >/dev/null 2>&1 || true
sudo systemctl start postgresql

log "设置 PostgreSQL 用户密码..."
run_as_postgres -d postgres -c "ALTER USER ${DB_USER} WITH PASSWORD '${DB_PASS}';"

log "确保数据库 ${DB_NAME} 存在..."
DB_EXISTS="$(run_as_postgres -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | tr -d '[:space:]')"
if [[ "$DB_EXISTS" != "1" ]]; then
  run_as_postgres -d postgres -c "CREATE DATABASE ${DB_NAME};"
  log "数据库 ${DB_NAME} 创建完成"
else
  log "数据库 ${DB_NAME} 已存在"
fi

log "确保 pgcrypto 扩展存在..."
run_as_postgres -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"

log "检查是否需要初始化表结构..."
TABLE_EXISTS="$(run_as_postgres -d "$DB_NAME" -tAc "SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name='accounts'" | tr -d '[:space:]')"
if [[ "$TABLE_EXISTS" != "1" ]]; then
  log "首次初始化数据库（执行 sql/init.sql）..."
  run_as_postgres -d "$DB_NAME" -f "sql/init.sql"
  log "数据库初始化完成"
else
  log "检测到 accounts 表已存在，跳过 init.sql（避免重复建表失败）"
fi

log "准备 Python 虚拟环境..."
if [[ "$RECREATE_VENV" -eq 1 ]]; then
  if [[ -d "venv" ]]; then
    log "按参数要求重建 venv（--recreate-venv）..."
    rm -rf venv
  fi
fi

if ! is_venv_healthy; then
  if [[ -d "venv" ]]; then
    log "检测到现有 venv 不可用（常见于从其他机器拷贝），自动重建..."
    rm -rf venv
  fi
  python3 -m venv venv
fi

log "安装 Python 依赖..."
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

if [[ "$INIT_OPS_DB" -eq 1 || "$WITH_OPS_WEB" -eq 1 ]]; then
  log "初始化运维表与引导账号..."
  python - <<'PY'
import asyncio
from app.core.db.Database import close_db, init_db
from app.ops.auth.Service import OpsAuthService

async def main():
    await init_db()
    await OpsAuthService.ensure_bootstrap_data()
    await close_db()

asyncio.run(main())
PY
fi

if [[ "$WITH_OPS_WEB" -eq 1 ]]; then
  if [[ -d "ops_web" ]]; then
    log "安装 ops_web 前端依赖..."
    (
      cd ops_web
      npm install
      if [[ "$SKIP_OPS_WEB_BUILD" -eq 0 ]]; then
        log "构建 ops_web..."
        npm run build
      else
        log "跳过 ops_web 构建（--skip-ops-web-build）"
      fi
    )
  else
    log "未找到 ops_web 目录，跳过运维前端安装"
  fi
fi

log "环境安装完成"
echo ""
echo "下一步："
echo "1) 启动服务: bash restart.sh"
echo "2) 查看日志: tail -f server.log"
echo "3) 访问文档: http://<你的服务器IP>:8444/api/docs"
if [[ "$WITH_OPS_WEB" -eq 1 ]]; then
  echo "4) 访问运维页: http://<你的服务器IP>:8444/ops"
fi
echo ""

if [[ "$START_AFTER_SETUP" -eq 1 ]]; then
  log "执行启动脚本..."
  bash restart.sh
fi
