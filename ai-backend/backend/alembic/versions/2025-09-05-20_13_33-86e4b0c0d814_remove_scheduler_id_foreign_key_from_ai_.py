"""remove_scheduler_id_foreign_key_from_ai_subscription

Revision ID: 86e4b0c0d814
Revises: f39e90efcb20
Create Date: 2025-09-05 20:13:33.034387

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "86e4b0c0d814"
down_revision = "f39e90efcb20"
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
    # 移除ai_subscription表中scheduler_id字段的外键约束
    if _table_exists("ai_subscription") and _column_exists("ai_subscription", "scheduler_id"):
        # 检查并删除外键约束
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        fks = inspector.get_foreign_keys("ai_subscription")

        for fk in fks:
            if "scheduler_id" in fk["constrained_columns"]:
                constraint_name = fk["name"]
                if constraint_name:
                    print(f"Dropping foreign key constraint: {constraint_name}")
                    op.drop_constraint(constraint_name, "ai_subscription", type_="foreignkey")
                    break

        # scheduler_id字段保留，只是移除外键约束
        # 这样应用层可以继续使用这个字段来维护关联关系
        print("Foreign key constraint on scheduler_id has been removed")


def downgrade():
    # 恢复ai_subscription表中scheduler_id字段的外键约束
    if _table_exists("ai_subscription") and _column_exists("ai_subscription", "scheduler_id"):
        if _table_exists("task_scheduler"):
            print("Restoring foreign key constraint on scheduler_id")
            op.create_foreign_key(
                "fk_ai_subscription_scheduler_id",
                "ai_subscription",
                "task_scheduler",
                ["scheduler_id"],
                ["id"],
                ondelete="SET NULL",
            )
            print("Foreign key constraint on scheduler_id has been restored")
