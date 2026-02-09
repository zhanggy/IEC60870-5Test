#!/bin/bash
# IEC60870-5-104 Slave服务器启动脚本 (Linux/Mac)

echo "========================================"
echo "IEC60870-5-104 Slave测试服务器"
echo "========================================"
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python3"
    exit 1
fi

echo "启动服务器..."
echo ""
python3 slave_server.py
