"""add ai_subscription id sequence

Revision ID: eb51df590eca
Revises: 7b1a1c5e4a71
Create Date: 2025-09-05 17:48:03.053859

"""

import sqlalchemy as sa

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "eb51df590eca"
down_revision = "7b1a1c5e4a71"
branch_labels = None
depends_on = None


def _index_exists(table_name: str, index_name: str) -> bool:
    """检查索引是否存在"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    indexes = [idx["name"] for idx in inspector.get_indexes(table_name)]
    return index_name in indexes


def _constraint_exists(table_name: str, constraint_name: str) -> bool:
    """检查约束是否存在"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # 检查外键约束
    fks = [fk["name"] for fk in inspector.get_foreign_keys(table_name) if fk["name"]]
    if constraint_name in fks:
        return True

    # 检查唯一约束
    uqs = [uq["name"] for uq in inspector.get_unique_constraints(table_name) if uq["name"]]
    if constraint_name in uqs:
        return True

    # 检查检查约束
    checks = [ck["name"] for ck in inspector.get_check_constraints(table_name) if ck["name"]]
    return constraint_name in checks


def _table_exists(table_name: str) -> bool:
    """检查表是否存在"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    return table_name in inspector.get_table_names()


def _column_exists(table_name: str, column_name: str) -> bool:
    """检查列是否存在"""
    if not _table_exists(table_name):
        return False
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade():
    # 创建序列
    op.execute(text("CREATE SEQUENCE IF NOT EXISTS ai_subscription_id_seq"))

    # 设置序列的当前值为表中最大ID + 1
    op.execute(
        text("""
        SELECT setval('ai_subscription_id_seq',
                     COALESCE((SELECT MAX(id) FROM ai_subscription), 0) + 1,
                     false)
    """)
    )

    # 设置列的默认值为序列的下一个值
    op.execute(text("ALTER TABLE ai_subscription ALTER COLUMN id SET DEFAULT nextval('ai_subscription_id_seq')"))

    # 设置序列的拥有者为该列
    op.execute(text("ALTER SEQUENCE ai_subscription_id_seq OWNED BY ai_subscription.id"))


def downgrade():
    # 移除列的默认值
    op.execute(text("ALTER TABLE ai_subscription ALTER COLUMN id DROP DEFAULT"))

    # 删除序列
    op.execute(text("DROP SEQUENCE IF EXISTS ai_subscription_id_seq"))
