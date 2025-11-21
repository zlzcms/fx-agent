import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "4b6a903f1975"
down_revision = "4b6a903f1974"  # 基于最新的迁移脚本
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    """检查表是否存在"""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _column_exists(table_name: str, column_name: str) -> bool:
    """检查列是否存在"""
    if not _table_exists(table_name):
        return False
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade():
    """添加 channel 字段到 ai_chat 表"""
    # 检查表是否存在
    if not _table_exists("ai_chat"):
        print("⚠ ai_chat 表不存在，跳过迁移")
        return

    # 检查字段是否已存在（用于支持重复运行迁移）
    if not _column_exists("ai_chat", "channel"):
        try:
            op.add_column(
                "ai_chat",
                sa.Column(
                    "channel",
                    sa.String(100),
                    nullable=True,
                    comment="渠道标识，用于追踪来源",
                ),
            )
            print("✓ 成功添加 channel 字段到 ai_chat 表")
        except Exception as e:
            print(f"⚠ 添加 channel 字段时出错: {e}")
            raise
    else:
        print("⚠ channel 字段已存在，跳过添加")


def downgrade():
    """回滚：删除 channel 字段"""
    # 检查表是否存在
    if not _table_exists("ai_chat"):
        print("⚠ ai_chat 表不存在，跳过回滚")
        return

    # 检查字段是否存在
    if _column_exists("ai_chat", "channel"):
        try:
            op.drop_column("ai_chat", "channel")
            print("✓ 成功删除 channel 字段")
        except Exception as e:
            print(f"⚠ 删除 channel 字段时出错: {e}")
            raise
    else:
        print("⚠ channel 字段不存在，跳过删除")
