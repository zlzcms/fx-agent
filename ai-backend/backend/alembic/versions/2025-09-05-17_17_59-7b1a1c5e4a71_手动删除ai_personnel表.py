"""手动删除ai_personnel表

Revision ID: 7b1a1c5e4a71
Revises: d8f1a1633bbc
Create Date: 2025-09-05 17:17:59.797612

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "7b1a1c5e4a71"
down_revision = "d8f1a1633bbc"
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
    # 删除 ai_personnel 表的索引和表
    if _table_exists("ai_personnel"):
        # 删除索引
        if _index_exists("ai_personnel", "ix_ai_personnel_id"):
            op.drop_index(op.f("ix_ai_personnel_id"), table_name="ai_personnel")

        # 删除表
        op.drop_table("ai_personnel")


def downgrade():
    # 重新创建 ai_personnel 表（如果需要回滚）
    op.create_table(
        "ai_personnel",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("position", sa.String(length=100), nullable=True),
        sa.Column("department", sa.String(length=100), nullable=True),
        sa.Column("email", sa.String(length=100), nullable=True),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("avatar", sa.String(length=255), nullable=True),
        sa.Column("status", sa.Integer(), nullable=True),
        sa.Column("create_datetime", sa.DateTime(), nullable=True),
        sa.Column("update_datetime", sa.DateTime(), nullable=True),
        sa.Column("create_user", sa.Integer(), nullable=True),
        sa.Column("update_user", sa.Integer(), nullable=True),
        sa.Column("remark", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_ai_personnel_id"), "ai_personnel", ["id"], unique=False)
