"""add_ai_subscription_tables

Revision ID: 6b275f964adb
Revises: bd129e4cf3d8
Create Date: 2025-08-19 10:42:03.341682

"""

import sqlalchemy as sa

from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "6b275f964adb"
down_revision = "bd129e4cf3d8"
branch_labels = None
depends_on = None


def upgrade():
    # 创建 ai_subscription 表
    op.create_table(
        "ai_subscription",
        sa.Column("id", sa.String(50), nullable=False),
        sa.Column("name", sa.String(100), nullable=False, comment="订阅名称"),
        sa.Column("subscription_type", sa.String(50), nullable=False, comment="订阅类型"),
        sa.Column("subscription_type_id", sa.String(50), nullable=False, comment="订阅类型ID"),
        sa.Column("execution_frequency", sa.String(20), nullable=True, default="daily", comment="执行频率"),
        sa.Column("execution_time", sa.String(10), nullable=True, default="09:00", comment="执行时间"),
        sa.Column("execution_minutes", sa.Integer(), nullable=True, comment="分钟间隔"),
        sa.Column("execution_hours", sa.Integer(), nullable=True, comment="小时间隔"),
        sa.Column("execution_weekday", sa.String(10), nullable=True, comment="执行星期"),
        sa.Column("execution_weekly_time", sa.String(10), nullable=True, comment="每周执行时间"),
        sa.Column("execution_day", sa.String(10), nullable=True, comment="执行日期"),
        sa.Column("execution_monthly_time", sa.String(10), nullable=True, comment="每月执行时间"),
        sa.Column("is_view_myself", sa.Boolean(), nullable=True, default=False, comment="本人查看"),
        sa.Column("setting", postgresql.JSON(), nullable=True, comment="其他设置"),
        sa.Column("ai_analysis_count", sa.Integer(), nullable=True, default=0, comment="分析次数"),
        sa.Column("last_analysis_time", sa.DateTime(), nullable=True, comment="最后一次分析时间"),
        sa.Column("created_time", sa.DateTime(), nullable=True),
        sa.Column("updated_time", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ai_subscription_id"), "ai_subscription", ["id"], unique=False)

    # 创建 ai_subscription_notification_methods 表
    op.create_table(
        "ai_subscription_notification_methods",
        sa.Column("id", sa.String(50), nullable=False),
        sa.Column("name", sa.String(50), nullable=False, comment="通知方式名称"),
        sa.Column("type", sa.String(20), nullable=False, comment="通知类型"),
        sa.Column("config", postgresql.JSON(), nullable=True, comment="配置信息"),
        sa.Column("status", sa.Boolean(), nullable=True, default=True, comment="状态"),
        sa.Column("created_time", sa.DateTime(), nullable=True),
        sa.Column("updated_time", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_ai_subscription_notification_methods_id"), "ai_subscription_notification_methods", ["id"], unique=False
    )

    # 创建 ai_subscription_notifications 关联表
    op.create_table(
        "ai_subscription_notifications",
        sa.Column("id", sa.String(50), nullable=False),
        sa.Column("subscription_id", sa.String(50), nullable=False, comment="订阅ID"),
        sa.Column("notification_id", sa.String(50), nullable=False, comment="通知方式ID"),
        sa.Column("created_time", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["subscription_id"], ["ai_subscription.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["notification_id"], ["ai_subscription_notification_methods.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("subscription_id", "notification_id", name="uk_subscription_notification"),
    )
    op.create_index(op.f("ix_ai_subscription_notifications_id"), "ai_subscription_notifications", ["id"], unique=False)


def downgrade():
    # 删除表
    op.drop_table("ai_subscription_notifications")
    op.drop_table("ai_subscription_notification_methods")
    op.drop_table("ai_subscription")
