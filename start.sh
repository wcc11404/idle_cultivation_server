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

# 检查端口是否被占用，如果占用则杀死进程
PORT=8444
echo "检查端口 $PORT 是否被占用..."
PID=$(lsof -i:$PORT | grep uvicorn | awk '{print $2}')
if [ -n "$PID" ]; then
    echo "端口 $PORT 被进程 $PID 占用，正在终止..."
    kill -9 $PID 2>/dev/null
    sleep 1
    echo "进程已终止"
fi

# 直接使用 uvicorn 命令启动，指定主机地址
echo "启动 FastAPI 服务..."
nohup uvicorn app.main:app --host 127.0.0.1 --port $PORT --reload > server.log 2>&1 &
echo "服务已后台启动，日志输出到 server.log"
echo "服务地址: http://127.0.0.1:$PORT"
echo "API 文档: http://127.0.0.1:$PORT/api/docs"