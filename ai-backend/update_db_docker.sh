#!/bin/bash

# 使用 Docker 执行 Alembic 数据库更新

set -e

echo "🔄 Alembic 数据库更新工具 (Docker 版本)"
echo "=========================================="
echo ""

cd /home/user/www/ai-backend

# 检查容器是否运行
if ! docker ps | grep -q fba_server; then
    echo "❌ fba_server 容器未运行"
    echo "请先启动服务: docker-compose up -d"
    exit 1
fi

echo "✅ 检测到 fba_server 容器正在运行"
echo ""

# 在容器内执行迁移
echo "📊 查看当前数据库版本..."
docker exec fba_server alembic current || echo "⚠️  无法获取当前版本"

echo ""
echo "📋 可用的迁移版本..."
docker exec fba_server alembic heads

echo ""
read -p "是否继续执行数据库迁移? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🔄 开始执行数据库迁移..."
    docker exec fba_server alembic upgrade head

    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ 数据库迁移成功！"
        echo ""
        echo "📊 当前版本:"
        docker exec fba_server alembic current
    else
        echo ""
        echo "❌ 数据库迁移失败"
        exit 1
    fi
else
    echo "操作已取消"
fi

echo ""
echo "✅ 完成"
