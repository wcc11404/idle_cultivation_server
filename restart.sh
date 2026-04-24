#!/bin/bash

# 启动服务端脚本
echo "启动 Idle Cultivation Server..."

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

VENV_PYTHON="$SCRIPT_DIR/venv/bin/python"
if [ ! -x "$VENV_PYTHON" ]; then
    echo "未找到可执行解释器: $VENV_PYTHON"
    echo "请先执行: bash setup_ubuntu.sh"
    exit 1
fi

# 检查并启动 PostgreSQL 服务
echo "检查 PostgreSQL 服务状态..."

# 检测系统类型
if [ "$(uname)" = "Darwin" ]; then
    # macOS 系统
    echo "检测到 macOS 系统"
    PG_STATUS=$(brew services list | grep postgresql)
    
    if echo "$PG_STATUS" | grep -q "started"; then
        echo "PostgreSQL 服务已运行"
    else
        echo "PostgreSQL 服务未运行，正在启动..."
        brew services start postgresql@16
        if [ $? -eq 0 ]; then
            echo "PostgreSQL 服务启动成功"
        else
            echo "PostgreSQL 服务启动失败，请检查权限"
            exit 1
        fi
    fi
else
    # Linux 系统
    echo "检测到 Linux 系统"
    PG_STATUS=$(sudo service postgresql status 2>&1 | grep -E 'active|inactive')
    
    if echo "$PG_STATUS" | grep -q "inactive"; then
        echo "PostgreSQL 服务未运行，正在启动..."
        sudo service postgresql start
        if [ $? -eq 0 ]; then
            echo "PostgreSQL 服务启动成功"
        else
            echo "PostgreSQL 服务启动失败，请检查权限"
            exit 1
        fi
    else
        echo "PostgreSQL 服务已运行"
    fi
fi

# 检查端口是否被占用，如果占用则杀死进程
PORT=8444
echo "检查端口 $PORT 是否被占用..."
PID=$(lsof -i:$PORT | grep -E 'uvicorn|python|Python|Google' | awk '{print $2}')
if [ -n "$PID" ]; then
    echo "端口 $PORT 被进程 $PID 占用，正在终止..."
    kill -9 $PID 2>/dev/null
    sleep 1
    echo "进程已终止"
fi

# 使用 venv 中的 Python 启动 uvicorn，避免 PATH/激活问题
echo "启动 FastAPI 服务..."
nohup "$VENV_PYTHON" -m uvicorn app.main:app --host 0.0.0.0 --port $PORT --reload > server.log 2>&1 &
echo "服务已后台启动，日志输出到 server.log"
echo "服务地址: http://0.0.0.0:$PORT"
echo "API 文档: http://0.0.0.0:$PORT/api/docs"
