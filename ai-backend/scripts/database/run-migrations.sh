#!/bin/bash

# 数据库迁移脚本
# 用于在容器启动时执行Alembic迁移

set -e

echo "🔄 开始数据库迁移..."

# 设置工作目录
cd /fba

# 检查数据库连接
echo "🔍 检查数据库连接..."
python -c "
import asyncio
from sqlalchemy import text
from backend.database.db import async_engine

async def check_db():
    try:
        async with async_engine.begin() as conn:
            await conn.execute(text('SELECT 1'))
        print('✅ 数据库连接正常')
        return True
    except Exception as e:
        print(f'❌ 数据库连接失败: {e}')
        return False

result = asyncio.run(check_db())
exit(0 if result else 1)
"

if [ $? -ne 0 ]; then
    echo "❌ 数据库连接失败，退出"
    exit 1
fi

# 检查迁移历史
echo "🔍 检查迁移历史..."
python -c "
import asyncio, sys
from sqlalchemy import text
from backend.database.db import async_engine

async def check():
    try:
        async with async_engine.begin() as conn:
            result = await conn.execute(text('SELECT COUNT(*) FROM information_schema.tables WHERE table_name = \\'alembic_version\\''))
            exists = result.scalar() > 0
            if exists:
                result = await conn.execute(text('SELECT version_num FROM alembic_version'))
                version = result.scalar()
                print('✅ 发现迁移历史:', version if version else '空版本')
                sys.exit(0 if version else 1)
            else:
                print('📋 无迁移历史')
                sys.exit(2)
    except Exception as e:
        print('❌ 检查失败:', e)
        sys.exit(1)

asyncio.run(check())
"
MIGRATION_STATUS=$?

# 处理迁移
case $MIGRATION_STATUS in
    0) echo "📊 检查是否需要迁移..."
       # 检查当前版本是否已经是最新版本
       CURRENT_VERSION=$(alembic current 2>/dev/null | grep -v "INFO" | tail -1 | awk '{print $1}')
       HEAD_VERSION=$(alembic heads 2>/dev/null | grep -v "INFO" | tail -1 | awk '{print $1}')

       if [ "$CURRENT_VERSION" = "$HEAD_VERSION" ]; then
           echo "✅ 数据库已是最新版本: $CURRENT_VERSION"
       else
           echo "🔄 执行增量迁移: $CURRENT_VERSION -> $HEAD_VERSION"
           alembic upgrade head
       fi ;;
    1) echo "❌ 迁移历史异常，退出"
       exit 1 ;;
    2) echo "🆕 初次部署..."
       # TODO: 执行初始化SQL脚本
       # 预期执行：init_schema.sql + init_data.sql
       # 当前缺少init sql，暂时跳过
       echo "⚠️  初始化SQL脚本尚未准备，请手动初始化数据库"
       exit 1 ;;
    *) echo "❌ 未知错误，退出"
       exit 1 ;;
esac

# 修复序列
echo "🔧 修复数据库序列..."
bash /fba/scripts/database/fix-sequences.sh

echo "✅ 数据库迁移完成"
