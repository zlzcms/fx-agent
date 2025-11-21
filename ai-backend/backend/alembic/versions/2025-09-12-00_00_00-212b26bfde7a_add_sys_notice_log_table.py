"""add_sys_notice_log_table

Revision ID: 212b26bfde7a
Revises: 7d836b48dabb
Create Date: 2025-09-12 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql, postgresql

# revision identifiers, used by Alembic.
revision = "212b26bfde7a"
down_revision = "7d836b48dabb"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    """检查表是否存在"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    return table_name in inspector.get_table_names()


def _index_exists(table_name: str, index_name: str) -> bool:
    """检查索引是否存在"""
    if not _table_exists(table_name):
        return False
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    indexes = [idx["name"] for idx in inspector.get_indexes(table_name)]
    return index_name in indexes


def upgrade():
    """创建通知日志表"""
    # 创建 sys_notice_log 表
    if not _table_exists("sys_notice_log"):
        op.create_table(
            "sys_notice_log",
            sa.Column("id", sa.BigInteger(), nullable=False, comment="主键ID"),
            sa.Column("description", sa.String(length=500), nullable=False, comment="通知描述，例如：订阅报告通知，报告id:56"),
            sa.Column("notification_type", sa.String(length=50), nullable=False, comment="通知方式：email/lark_webhook"),
            sa.Column("content", sa.Text(), nullable=False, comment="通知发送时的主体内容"),
            sa.Column("address", sa.String(length=500), nullable=False, comment="通知地址：邮箱地址/webhook地址"),
            sa.Column("is_success", sa.Boolean(), nullable=False, default=False, comment="通知是否成功：True=成功，False=失败"),
            sa.Column("failure_reason", sa.Text(), nullable=True, comment="通知失败原因描述"),
            sa.Column("created_time", sa.DateTime(timezone=True), nullable=False, comment="创建时间"),
            sa.Column("updated_time", sa.DateTime(timezone=True), nullable=True, comment="更新时间"),
            sa.PrimaryKeyConstraint("id"),
            comment="通知日志记录表"
        )
        
        # 创建索引
        if not _index_exists("sys_notice_log", "ix_sys_notice_log_id"):
            op.create_index(op.f("ix_sys_notice_log_id"), "sys_notice_log", ["id"], unique=False)
        
        if not _index_exists("sys_notice_log", "ix_sys_notice_log_notification_type"):
            op.create_index(op.f("ix_sys_notice_log_notification_type"), "sys_notice_log", ["notification_type"], unique=False)
        
        if not _index_exists("sys_notice_log", "ix_sys_notice_log_is_success"):
            op.create_index(op.f("ix_sys_notice_log_is_success"), "sys_notice_log", ["is_success"], unique=False)
        
        if not _index_exists("sys_notice_log", "ix_sys_notice_log_created_time"):
            op.create_index(op.f("ix_sys_notice_log_created_time"), "sys_notice_log", ["created_time"], unique=False)


def downgrade():
    """删除通知日志表"""
    if _table_exists("sys_notice_log"):
        # 删除索引
        if _index_exists("sys_notice_log", "ix_sys_notice_log_created_time"):
            op.drop_index(op.f("ix_sys_notice_log_created_time"), table_name="sys_notice_log")
        
        if _index_exists("sys_notice_log", "ix_sys_notice_log_is_success"):
            op.drop_index(op.f("ix_sys_notice_log_is_success"), table_name="sys_notice_log")
        
        if _index_exists("sys_notice_log", "ix_sys_notice_log_notification_type"):
            op.drop_index(op.f("ix_sys_notice_log_notification_type"), table_name="sys_notice_log")
        
        if _index_exists("sys_notice_log", "ix_sys_notice_log_id"):
            op.drop_index(op.f("ix_sys_notice_log_id"), table_name="sys_notice_log")
        
        # 删除表
        op.drop_table("sys_notice_log")