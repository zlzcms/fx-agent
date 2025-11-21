"""remove deleted_at from subscription relation tables

Revision ID: 9e0e7605c08a
Revises: 38300fa768e2
Create Date: 2025-09-08 18:55:10.600005

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "9e0e7605c08a"
down_revision = "38300fa768e2"
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
    # 安全删除两张非核心关系表的 deleted_at 列（如果存在）
    tables = [
        "ai_subscription_notification_methods",
        "ai_subscription_notifications",
    ]

    for table in tables:
        if _column_exists(table, "deleted_at"):
            with op.batch_alter_table(table, schema=None) as batch_op:
                batch_op.drop_column("deleted_at")


def downgrade():
    # 回滚时为两张关系表补回 deleted_at 列（若不存在）
    for table in [
        "ai_subscription_notification_methods",
        "ai_subscription_notifications",
    ]:
        if not _column_exists(table, "deleted_at"):
            with op.batch_alter_table(table, schema=None) as batch_op:
                batch_op.add_column(
                    sa.Column(
                        "deleted_at",
                        sa.DateTime(),
                        nullable=True,
                        comment="删除时间，NULL表示未删除",
                    )
                )
