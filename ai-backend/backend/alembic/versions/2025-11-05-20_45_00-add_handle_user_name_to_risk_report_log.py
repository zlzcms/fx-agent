"""add handle_user_name to risk_report_log

Revision ID: 2025110500001
Revises: 712183087d1a
Create Date: 2025-11-05 20:45:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "2025110500001"
down_revision = "712183087d1a"
branch_labels = None
depends_on = None


def _column_exists(table_name: str, column_name: str) -> bool:
    """检查列是否存在"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if not inspector.has_table(table_name):
        return False
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade():
    """添加 handle_user_name 字段到 risk_report_log 表"""
    if not _column_exists("risk_report_log", "handle_user_name"):
        op.add_column(
            "risk_report_log",
            sa.Column("handle_user_name", sa.String(length=50), nullable=True, comment="处理人名称"),
        )


def downgrade():
    """回滚：删除 handle_user_name 字段"""
    if _column_exists("risk_report_log", "handle_user_name"):
        op.drop_column("risk_report_log", "handle_user_name")
