#!/bin/bash

echo "🚀 启动开发环境..."

# 检查是否已经运行
if [ "$(docker ps -q -f name=xystock-dev)" ]; then
    echo "📦 容器已经在运行，直接进入..."
    docker exec -it xystock-dev bash
else
    echo "📦 启动新的开发容器..."
    docker-compose -f docker-compose.dev.yml up -d
    
    echo "⏳ 等待容器启动..."
    sleep 3
    
    echo "🔑 进入开发容器..."
    docker exec -it xystock-dev bash
fi
