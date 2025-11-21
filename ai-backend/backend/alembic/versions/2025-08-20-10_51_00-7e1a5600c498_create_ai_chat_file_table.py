"""create_ai_chat_file_table

Revision ID: 7e1a5600c498
Revises: e3b6fe1ed68f
Create Date: 2025-08-20 10:51:00.508534

"""

import sqlalchemy as sa

from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "7e1a5600c498"
down_revision = "e3b6fe1ed68f"
branch_labels = None
depends_on = None


def upgrade():
    """创建ai_chat_file表"""

    # 创建ai_chat_file表
    op.create_table(
        "ai_chat_file",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("chat_message_id", sa.String(36), nullable=False),
        sa.Column("filename", sa.String(255), nullable=True),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("file_paths", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("export_directory", sa.Text(), nullable=True),
        sa.Column("task_id", sa.String(100), nullable=True),
        sa.Column("data_source", sa.String(100), nullable=True),
        sa.Column("export_time", sa.String(50), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("file_type", sa.String(50), nullable=True),
        sa.Column("status", sa.Boolean(), nullable=False, default=True),
        sa.Column("created_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_time", sa.DateTime(timezone=True), nullable=True),
        # 主键和外键约束
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["chat_message_id"], ["ai_chat_message.id"], ondelete="CASCADE"),
        comment="AI Chat File model for storing file information in chat messages",
    )

    # 创建索引
    op.create_index(op.f("ix_ai_chat_file_task_id"), "ai_chat_file", ["task_id"], unique=False)
    op.create_index(op.f("ix_ai_chat_file_data_source"), "ai_chat_file", ["data_source"], unique=False)


def downgrade():
    """删除ai_chat_file表"""

    # 删除索引
    op.drop_index(op.f("ix_ai_chat_file_data_source"), table_name="ai_chat_file")
    op.drop_index(op.f("ix_ai_chat_file_task_id"), table_name="ai_chat_file")

    # 删除表
    op.drop_table("ai_chat_file")
