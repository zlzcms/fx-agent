#!/bin/bash

# Alembic 数据库更新脚本
# 确保使用正确的环境变量

set -e

cd /home/user/www/ai-backend

echo "🔄 Alembic 数据库更新工具"
echo "=========================="
echo ""

# 激活虚拟环境
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "❌ 虚拟环境不存在"
    exit 1
fi

# 加载环境变量
ENV_FILE=""
if [ -f "backend/.env" ]; then
    ENV_FILE="backend/.env"
    echo "✅ 加载环境配置 (.env)..."
elif [ -f "backend/.env.local" ]; then
    ENV_FILE="backend/.env.local"
    echo "✅ 加载本地环境配置 (.env.local)..."
elif [ -f "backend/.env.production" ]; then
    ENV_FILE="backend/.env.production"
    echo "✅ 加载生产环境配置 (.env.production)..."
else
    echo "❌ 未找到环境配置文件"
    exit 1
fi

# 导出环境变量（处理带引号的值）
set -a
source "$ENV_FILE"
set +a

echo ""
echo "📊 查看当前数据库版本..."
alembic current || echo "⚠️  无法获取当前版本"

echo ""
echo "📋 可用的迁移版本..."
alembic heads

echo ""
read -p "是否继续执行数据库迁移? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🔄 开始执行数据库迁移..."
    alembic upgrade head

    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ 数据库迁移成功！"
        echo ""
        echo "📊 当前版本:"
        alembic current
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
