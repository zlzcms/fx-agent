"""drop_ai_assistant_data_sources_table

Revision ID: 9ccb88c3e652
Revises: 7b0a9242d431
Create Date: 2025-09-08 21:17:12.931102

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "9ccb88c3e652"
down_revision = "7b0a9242d431"
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
    # 删除ai_assistant_data_sources表（如果存在）
    if _table_exists("ai_assistant_data_sources"):
        # 先删除可能的索引
        if _index_exists("ai_assistant_data_sources", "ix_ai_assistant_data_sources_assistant_id"):
            op.drop_index("ix_ai_assistant_data_sources_assistant_id", table_name="ai_assistant_data_sources")
        if _index_exists("ai_assistant_data_sources", "ix_ai_assistant_data_sources_collection_id"):
            op.drop_index("ix_ai_assistant_data_sources_collection_id", table_name="ai_assistant_data_sources")

        # 删除表
        op.drop_table("ai_assistant_data_sources")


def downgrade():
    # 重新创建ai_assistant_data_sources表（用于回滚）
    if not _table_exists("ai_assistant_data_sources"):
        op.create_table(
            "ai_assistant_data_sources",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("assistant_id", sa.String(length=36), nullable=False),
            sa.Column("collection_id", sa.String(length=36), nullable=False),
            sa.Column("query_name", sa.String(length=255), nullable=True),
            sa.Column("tables", sa.JSON(), nullable=True),
            sa.Column("created_time", sa.DateTime(), nullable=True),
            sa.Column("updated_time", sa.DateTime(), nullable=True),
            sa.Column("deleted_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

        # 重新创建索引
        op.create_index(
            "ix_ai_assistant_data_sources_assistant_id", "ai_assistant_data_sources", ["assistant_id"], unique=False
        )
        op.create_index(
            "ix_ai_assistant_data_sources_collection_id", "ai_assistant_data_sources", ["collection_id"], unique=False
        )
