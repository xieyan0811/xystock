#!/bin/bash

# 开发环境启动脚本

echo "启动开发环境容器..."
docker-compose -f docker-compose.dev.yml up -d

echo "等待容器启动..."
sleep 3

echo "进入开发容器..."
echo "在容器内，你可以运行以下命令启动应用："
echo "  python -m streamlit run ui/app.py --server.address=0.0.0.0 --server.port=8811"
echo ""
echo "或者运行其他 Python 脚本进行开发调试"
echo ""

# 进入容器的交互式终端
docker exec -it xystock-dev bash
