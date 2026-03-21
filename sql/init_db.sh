#!/bin/bash

# 初始化数据库脚本
echo "开始初始化数据库..."

# 检查 PostgreSQL 服务状态
if [ "$(uname)" = "Darwin" ]; then
    # macOS 系统
    echo "检测到 macOS 系统"
    PG_STATUS=$(brew services list | grep postgresql)
    
    if echo "$PG_STATUS" | grep -q "started"; then
        echo "PostgreSQL 服务已运行"
    else
        echo "PostgreSQL 服务未运行，正在启动..."
        brew services start postgresql@14
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

# 创建数据库
echo "创建数据库 idle_cultivation_game..."
createdb idle_cultivation_game
if [ $? -eq 0 ]; then
    echo "数据库创建成功"
else
    echo "数据库创建失败，可能已存在"
fi

# 初始化表结构
echo "初始化表结构..."
psql -d idle_cultivation_game -f "$(dirname "$0")/init.sql"
if [ $? -eq 0 ]; then
    echo "表结构初始化成功"
else
    echo "表结构初始化失败"
    exit 1
fi

# 验证数据库
echo "验证数据库..."
psql -d idle_cultivation_game -c "SELECT COUNT(*) FROM accounts;"
if [ $? -eq 0 ]; then
    echo "数据库验证成功"
else
    echo "数据库验证失败"
    exit 1
fi

echo "数据库初始化完成！"
echo "测试账号：test / test123"
echo "服务地址：http://127.0.0.1:8444"
echo "API 文档：http://127.0.0.1:8444/api/docs"