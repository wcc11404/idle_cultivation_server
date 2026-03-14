#!/bin/bash

# 启动服务端脚本
echo "启动 Idle Cultivation Server..."

# 激活虚拟环境
source venv/bin/activate

# 检查并启动 PostgreSQL 服务
echo "检查 PostgreSQL 服务状态..."
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

# 直接使用 uvicorn 命令启动，指定主机地址
echo "启动 FastAPI 服务..."
uvicorn app.main:app --host 172.25.6.6 --port 8444 --reload