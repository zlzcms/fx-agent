#!/usr/bin/env python3
"""
数据库序列修复脚本 - 用于 pre-commit hook
修复 PostgreSQL 序列同步问题
"""

import os
import re
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def check_database_connection():
    """检查数据库连接"""
    try:
        from sqlalchemy import URL, create_engine, text

        from backend.core.conf import settings

        # 构建同步数据库URL
        sync_url = URL.create(
            drivername="mysql+pymysql" if settings.DATABASE_TYPE == "mysql" else "postgresql+psycopg2",
            username=settings.DATABASE_USER,
            password=settings.DATABASE_PASSWORD,
            host=settings.DATABASE_HOST,
            port=settings.DATABASE_PORT,
            database=settings.DATABASE_SCHEMA,
        )

        engine = create_engine(sync_url)

        with engine.begin() as conn:
            conn.execute(text("SELECT 1"))
            return True
    except Exception:
        return False


def fix_sequences():
    """修复数据库序列"""
    try:
        from sqlalchemy import URL, create_engine, text

        from backend.core.conf import settings

        # 构建同步数据库URL
        sync_url = URL.create(
            drivername="mysql+pymysql" if settings.DATABASE_TYPE == "mysql" else "postgresql+psycopg2",
            username=settings.DATABASE_USER,
            password=settings.DATABASE_PASSWORD,
            host=settings.DATABASE_HOST,
            port=settings.DATABASE_PORT,
            database=settings.DATABASE_SCHEMA,
        )

        engine = create_engine(sync_url)

        with engine.begin() as conn:
            # 获取所有表及其主键列
            result = conn.execute(
                text("""
                SELECT t.table_name, c.column_name, c.column_default
                FROM information_schema.tables t
                JOIN information_schema.columns c ON t.table_name = c.table_name
                WHERE t.table_schema = 'public'
                AND c.column_default LIKE '%nextval%'
                AND t.table_type = 'BASE TABLE'
            """)
            )

            tables = result.fetchall()
            fixed_count = 0
            error_count = 0

            for table_name, column_name, column_default in tables:
                # 提取序列名
                match = re.search(r"nextval\(\'([^\']+)\'", column_default)
                if match:
                    sequence_name = match.group(1)
                    try:
                        # 重置序列到最大值+1
                        conn.execute(
                            text(f"""
                            SELECT setval('{sequence_name}',
                            COALESCE((SELECT MAX({column_name}) FROM {table_name}), 0) + 1, false)
                        """)
                        )
                        fixed_count += 1
                    except Exception as e:
                        print(f"❌ 修复序列 {sequence_name} 失败: {str(e)}")
                        error_count += 1
                else:
                    print(f"⚠️  无法解析序列: {table_name}.{column_name}")
                    error_count += 1

            return fixed_count, error_count

    except Exception as e:
        print(f"❌ 数据库操作失败: {str(e)}")
        return 0, 1


def main():
    """主函数"""
    print("🔧 检查数据库序列状态...")

    # 检查数据库连接
    if not check_database_connection():
        print("⚠️  数据库连接失败，跳过序列修复")
        print("💡 提示: 确保数据库服务正在运行")
        return 0  # 不阻止提交，但给出警告

    # 修复序列
    fixed_count, error_count = fix_sequences()

    if fixed_count > 0:
        print(f"✅ 成功修复 {fixed_count} 个序列")

    if error_count > 0:
        print(f"⚠️  {error_count} 个序列修复失败")
        # 序列修复失败不阻止提交，只是警告
        return 0

    if fixed_count == 0 and error_count == 0:
        print("✅ 所有序列状态正常")

    return 0


if __name__ == "__main__":
    sys.exit(main())
