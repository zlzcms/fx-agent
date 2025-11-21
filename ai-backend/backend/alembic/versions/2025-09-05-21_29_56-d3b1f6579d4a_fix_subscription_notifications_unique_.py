"""fix_subscription_notifications_unique_constraint

Revision ID: d3b1f6579d4a
Revises: 8ff9b1f5f820
Create Date: 2025-09-05 21:29:56.609152

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "d3b1f6579d4a"
down_revision = "8ff9b1f5f820"
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
    # 修复 ai_subscription_notifications 表的 subscription_id 索引
    # 将错误的唯一索引改为非唯一索引，因为一个订阅可以关联多个通知方式

    # 检查并删除错误的唯一索引
    if _index_exists("ai_subscription_notifications", "ix_ai_subscription_notifications_subscription_id"):
        with op.batch_alter_table("ai_subscription_notifications", schema=None) as batch_op:
            batch_op.drop_index("ix_ai_subscription_notifications_subscription_id")

    # 重新创建非唯一索引
    with op.batch_alter_table("ai_subscription_notifications", schema=None) as batch_op:
        batch_op.create_index("ix_ai_subscription_notifications_subscription_id", ["subscription_id"], unique=False)


def downgrade():
    # 回滚：将非唯一索引改回唯一索引（虽然这是错误的设计）

    # 删除非唯一索引
    if _index_exists("ai_subscription_notifications", "ix_ai_subscription_notifications_subscription_id"):
        with op.batch_alter_table("ai_subscription_notifications", schema=None) as batch_op:
            batch_op.drop_index("ix_ai_subscription_notifications_subscription_id")

    # 重新创建唯一索引（错误的设计，但为了回滚一致性）
    with op.batch_alter_table("ai_subscription_notifications", schema=None) as batch_op:
        batch_op.create_index("ix_ai_subscription_notifications_subscription_id", ["subscription_id"], unique=True)
