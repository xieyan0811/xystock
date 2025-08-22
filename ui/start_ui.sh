#!/bin/bash

# XY Stock Streamlit UI 启动脚本
# 在8811端口启动Streamlit应用

echo "正在启动 XY Stock Streamlit UI..."
echo "访问地址: http://localhost:8811"
echo "按 Ctrl+C 停止服务"
echo ""

# 切换到项目根目录
cd "$(dirname "$0")/.."

# 启动streamlit应用
streamlit run ui/app.py --server.port 8811 --server.address 0.0.0.0 --server.headless true
