"""add subscription_id to ai_assistant_report_log

Revision ID: add_subscription_id_to_ai_assistant_report_log
Revises: 2025-09-15-14_33_47-5172e3e7211d_check
Create Date: 2025-01-15 10:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "2025011500001"
down_revision = "5172e3e7211d"
branch_labels = None
depends_on = None


def upgrade():
    """添加 subscription_id 字段到 ai_assistant_report_log 表"""
    # 添加 subscription_id 字段
    op.add_column(
        "ai_assistant_report_log", sa.Column("subscription_id", sa.BigInteger(), nullable=True, comment="订阅ID")
    )

    # 添加索引以提高查询性能
    op.create_index("ix_ai_assistant_report_log_subscription_id", "ai_assistant_report_log", ["subscription_id"])


def downgrade():
    """回滚：删除 subscription_id 字段"""
    # 删除索引
    op.drop_index("ix_ai_assistant_report_log_subscription_id", table_name="ai_assistant_report_log")

    # 删除字段
    op.drop_column("ai_assistant_report_log", "subscription_id")
