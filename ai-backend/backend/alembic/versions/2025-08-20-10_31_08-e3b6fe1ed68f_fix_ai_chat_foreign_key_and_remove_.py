"""fix_ai_chat_foreign_key_and_remove_unused_tables

Revision ID: e3b6fe1ed68f
Revises: 4032fc0f911f
Create Date: 2025-08-20 10:31:08.288695

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "e3b6fe1ed68f"
down_revision = "4032fc0f911f"
branch_labels = None
depends_on = None


def upgrade():
    """执行升级操作"""

    # 使用SQL语句来执行变更，避免约束名称问题

    # 1. 删除ai_chat表上的外键约束
    op.execute("""
        DO $$
        BEGIN
            -- 尝试删除可能存在的约束
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = 'ai_chat_user_id_fkey'
                AND table_name = 'ai_chat'
            ) THEN
                ALTER TABLE ai_chat DROP CONSTRAINT ai_chat_user_id_fkey;
            END IF;

            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = 'fk_ai_chat_user_id_client_user'
                AND table_name = 'ai_chat'
            ) THEN
                ALTER TABLE ai_chat DROP CONSTRAINT fk_ai_chat_user_id_client_user;
            END IF;
        END $$;
    """)

    # 2. 重新添加外键约束，指向sys_user.id
    op.execute("""
        ALTER TABLE ai_chat
        ADD CONSTRAINT ai_chat_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES sys_user(id);
    """)

    # 3. 删除mcp_query表（如果存在）
    op.execute("""
        DROP TABLE IF EXISTS mcp_query CASCADE;
    """)

    # 4. 删除client_user表（如果存在）
    op.execute("""
        DROP TABLE IF EXISTS client_user CASCADE;
    """)


def downgrade():
    """执行回滚操作"""

    # 1. 重新创建client_user表
    op.create_table(
        "client_user",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("uuid", sa.String(50), nullable=False),
        sa.Column("username", sa.String(20), nullable=False),
        sa.Column("email", sa.String(50), nullable=False),
        sa.Column("password", sa.String(255), nullable=True),
        sa.Column("full_name", sa.String(50), nullable=True),
        sa.Column("phone", sa.String(11), nullable=True),
        sa.Column("avatar", sa.String(255), nullable=True),
        sa.Column("status", sa.Boolean(), nullable=False, default=True),
        sa.Column("created_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_time", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("email"),
    )

    # 2. 重新创建mcp_query表
    op.create_table(
        "mcp_query",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("chat_message_id", sa.String(36), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("status", sa.Boolean(), nullable=False, default=True),
        sa.Column("created_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_time", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["chat_message_id"],
            ["ai_chat_message.id"],
        ),
    )

    # 3. 恢复ai_chat表的外键约束到client_user.id
    op.execute("""
        ALTER TABLE ai_chat DROP CONSTRAINT IF EXISTS ai_chat_user_id_fkey;
        ALTER TABLE ai_chat
        ADD CONSTRAINT ai_chat_user_id_fkey
        FOREIGN KEY (user_id) REFERENCES client_user(id);
    """)
