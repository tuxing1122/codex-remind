#!/bin/bash

echo "========================================"
echo "  Claude Code 中继服务器"
echo "========================================"
echo

cd "$(dirname "$0")"

echo "[1/2] 检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到Python3"
    exit 1
fi
echo "[OK] Python3已安装"

echo
echo "[2/2] 检查依赖..."
if ! python3 -c "import websockets" &> /dev/null; then
    echo "[安装] 正在安装websockets..."
    pip3 install websockets
fi
echo "[OK] 依赖已就绪"

echo
echo "----------------------------------------"
echo "  监听地址: 0.0.0.0:8765"
echo "  按 Ctrl+C 停止服务"
echo "----------------------------------------"
echo

python3 relay_server.py
