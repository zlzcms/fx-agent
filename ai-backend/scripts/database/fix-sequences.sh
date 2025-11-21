#!/bin/bash

# 修复PostgreSQL序列的脚本
# 解决主键ID序列与实际数据不同步的问题

set -e

echo "🔧 修复数据库序列..."

# 设置工作目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

# 修复所有表的序列
python -c "
import asyncio
import re
import logging

# 禁用SQLAlchemy详细日志（必须在导入数据库模块之前设置）
logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy.pool').setLevel(logging.ERROR)
logging.getLogger('sqlalchemy').setLevel(logging.ERROR)

from sqlalchemy import text
# 临时覆盖数据库echo设置
import os
os.environ['DATABASE_ECHO'] = 'False'
from backend.database.db import async_engine

async def fix_sequences():
    try:
        async with async_engine.begin() as conn:
            # 获取所有表及其主键列
            result = await conn.execute(text('''
                SELECT t.table_name, c.column_name, c.column_default
                FROM information_schema.tables t
                JOIN information_schema.columns c ON t.table_name = c.table_name
                WHERE t.table_schema = 'public'
                AND c.column_default LIKE '%nextval%'
                AND t.table_type = 'BASE TABLE'
            '''))

            tables = result.fetchall()
            fixed_count = 0
            error_count = 0

            for table_name, column_name, column_default in tables:
                # 提取序列名
                match = re.search(r'nextval\(\'([^\']+)\'', column_default)
                if match:
                    sequence_name = match.group(1)
                    try:
                        # 重置序列到最大值+1
                        await conn.execute(text(f'''
                            SELECT setval('{sequence_name}',
                            COALESCE((SELECT MAX({column_name}) FROM {table_name}), 0) + 1, false)
                        '''))
                        fixed_count += 1
                    except Exception as e:
                        print(f'❌ 修复序列 {sequence_name} 失败: {str(e)}')
                        error_count += 1
                else:
                    print(f'⚠️  无法解析序列: {table_name}.{column_name}')
                    error_count += 1

            if fixed_count > 0:
                print(f'✅ 成功修复 {fixed_count} 个序列')
            if error_count > 0:
                print(f'⚠️  {error_count} 个序列修复失败')

    except Exception as e:
        print(f'❌ 数据库连接失败: {str(e)}')
        exit(1)

asyncio.run(fix_sequences())
"

echo "✅ 序列修复完成"
