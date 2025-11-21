#!/bin/bash

echo "🗄️  初始化数据库..."

# 等待PostgreSQL启动
echo "⏳ 等待PostgreSQL启动..."
until docker exec fba_postgres pg_isready -U postgres -d fba; do
    echo "等待PostgreSQL启动..."
    sleep 2
done

echo "✅ PostgreSQL已启动"

# 创建数据库表结构
echo "🔨 创建数据库表结构..."
docker exec -i fba_postgres psql -U postgres -d fba < backend/sql/postgresql/init_v1.0_schema.sql

# 检查是否有初始数据
if [ -f "backend/sql/postgresql/init_v1.0_data.sql" ]; then
    echo "📊 插入初始数据..."
    docker exec -i fba_postgres psql -U postgres -d fba < backend/sql/postgresql/init_v1.0_data.sql
fi

echo "✅ 数据库初始化完成"
