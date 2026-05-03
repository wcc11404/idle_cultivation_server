#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_TAR="$SCRIPT_DIR/idle_cultivation_server.tar"

echo "开始打包服务端目录..."
echo "输出文件: $OUTPUT_TAR"
echo "排除目录: venv, .git, __pycache__, .pytest_cache, ops_web/node_modules, ops_web/.npm-cache"
echo "排除文件: server.log, test_server.log, idle_cultivation_server.tar"

rm -f "$OUTPUT_TAR"

cd "$SCRIPT_DIR"
tar \
  --exclude='./venv' \
  --exclude='./.git' \
  --exclude='./.pytest_cache' \
  --exclude='./__pycache__' \
  --exclude='*/__pycache__' \
  --exclude='./ops_web/node_modules' \
  --exclude='./ops_web/.npm-cache' \
  --exclude='./server.log' \
  --exclude='./test_server.log' \
  --exclude='./idle_cultivation_server.tar' \
  -cf "$OUTPUT_TAR" \
  .

echo "打包完成: $OUTPUT_TAR"
