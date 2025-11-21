"""add_api_key_table

Revision ID: add_api_key_table
Revises: 8ee6e90ec006
Create Date: 2025-11-04 16:12:31.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "8ee6e90ec007"
down_revision = "8ee6e90ec006"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    """检查表是否存在"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    return table_name in inspector.get_table_names()


def upgrade():
    # 创建 sys_api_key 表
    if not _table_exists("sys_api_key"):
        op.create_table(
            "sys_api_key",
            sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False, comment="主键 ID"),
            sa.Column("key_name", sa.String(length=100), nullable=False, comment="API Key名称"),
            sa.Column("api_key", sa.String(length=255), nullable=False, comment="API Key值"),
            sa.Column("api_secret", sa.String(length=255), nullable=False, comment="API Secret（加密存储）"),
            sa.Column("description", sa.Text(), nullable=True, comment="描述"),
            sa.Column("status", sa.Integer(), nullable=False, server_default="1", comment="状态(0停用 1启用)"),
            sa.Column(
                "expires_at",
                sa.DateTime(timezone=True),
                nullable=True,
                comment="过期时间，NULL表示永不过期",
            ),
            sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True, comment="最后使用时间"),
            sa.Column("last_used_ip", sa.String(length=50), nullable=True, comment="最后使用IP"),
            sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0", comment="使用次数"),
            sa.Column("ip_whitelist", sa.Text(), nullable=True, comment="IP白名单，多个IP用逗号分隔"),
            sa.Column("permissions", sa.Text(), nullable=True, comment="权限列表，JSON格式存储"),
            sa.Column("user_id", sa.BigInteger(), nullable=True, comment="创建者用户ID"),
            sa.Column("created_time", sa.DateTime(timezone=True), nullable=False, comment="创建时间"),
            sa.Column("updated_time", sa.DateTime(timezone=True), nullable=True, comment="更新时间"),
            sa.Column(
                "deleted_at",
                sa.DateTime(timezone=True),
                nullable=True,
                comment="软删除时间，NULL表示未删除",
            ),
            sa.ForeignKeyConstraint(["user_id"], ["sys_user.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("api_key"),
            comment="API Key表",
        )
        op.create_index("ix_sys_api_key_key_name", "sys_api_key", ["key_name"])
        op.create_index("ix_sys_api_key_status", "sys_api_key", ["status"])
        op.create_index("ix_sys_api_key_deleted_at", "sys_api_key", ["deleted_at"])
        op.create_index("ix_sys_api_key_api_key", "sys_api_key", ["api_key"])


def downgrade():
    # 删除 sys_api_key 表
    if _table_exists("sys_api_key"):
        op.drop_index("ix_sys_api_key_api_key", table_name="sys_api_key")
        op.drop_index("ix_sys_api_key_deleted_at", table_name="sys_api_key")
        op.drop_index("ix_sys_api_key_status", table_name="sys_api_key")
        op.drop_index("ix_sys_api_key_key_name", table_name="sys_api_key")
        op.drop_table("sys_api_key")
