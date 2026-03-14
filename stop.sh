#!/bin/bash

# 停止服务端脚本
echo "停止 Idle Cultivation Server..."

# 停止 FastAPI 服务
echo "停止 FastAPI 服务..."
UVICORN_PID=$(ps aux | grep "uvicorn app.main:app" | grep -v grep | awk '{print $2}')

if [ -n "$UVICORN_PID" ]; then
    kill $UVICORN_PID
    if [ $? -eq 0 ]; then
        echo "FastAPI 服务停止成功"
    else
        echo "FastAPI 服务停止失败"
    fi
else
    echo "FastAPI 服务未运行"
fi

# 停止 PostgreSQL 服务
echo "停止 PostgreSQL 服务..."
PG_STATUS=$(sudo service postgresql status 2>&1 | grep -E 'active|inactive')

if echo "$PG_STATUS" | grep -q "active"; then
    sudo service postgresql stop
    if [ $? -eq 0 ]; then
        echo "PostgreSQL 服务停止成功"
    else
        echo "PostgreSQL 服务停止失败，请检查权限"
    fi
else
    echo "PostgreSQL 服务未运行"
fi

echo "服务停止完成"