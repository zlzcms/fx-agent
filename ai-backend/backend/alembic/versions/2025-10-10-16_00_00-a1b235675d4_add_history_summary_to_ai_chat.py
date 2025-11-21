"""Add history_summary and summary_time fields to ai_chat

Revision ID: a1b235675d4
Revises: 2df4e45d5c20
Create Date: 2025-10-10 16:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b235675d4"
down_revision = "2df4e45d5c20"
branch_labels = None
depends_on = None


def upgrade():
    """添加历史对话总结字段"""
    # 添加 history_summary 字段 - 用于存储历史对话的压缩摘要
    op.add_column(
        "ai_chat",
        sa.Column(
            "history_summary",
            sa.Text(),
            nullable=True,
            comment="历史对话压缩摘要，用于减少token消耗",
        ),
    )

    # 添加 summary_time 字段 - 用于记录摘要生成时间
    op.add_column(
        "ai_chat",
        sa.Column(
            "summary_time",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="摘要生成时间",
        ),
    )

    # 为 summary_time 添加索引，方便查询最新摘要
    op.create_index(op.f("ix_ai_chat_summary_time"), "ai_chat", ["summary_time"], unique=False)


def downgrade():
    """回滚：删除历史对话总结字段"""
    # 删除索引
    op.drop_index(op.f("ix_ai_chat_summary_time"), table_name="ai_chat")

    # 删除字段
    op.drop_column("ai_chat", "summary_time")
    op.drop_column("ai_chat", "history_summary")
