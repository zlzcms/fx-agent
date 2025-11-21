"""fix_risk_type_mapping

Revision ID: 2df4e45d5c20
Revises: f4b3d2ee10b1
Create Date: 2025-09-29 16:12:37.337113

"""

import sqlalchemy as sa

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "2df4e45d5c20"
down_revision = "f4b3d2ee10b1"
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
    """修正 risk_type 的映射"""
    if not _table_exists("risk_tag"):
        return

    conn = op.get_bind()

    # 根据标签名称和描述进行智能映射
    # 员工风控相关标签
    conn.execute(
        text("""
        UPDATE risk_tag
        SET risk_type = 'crm_user'
        WHERE name IN (
            '操作时段异常', '批量操作异常', '异常操作嫌疑', '客户关联异常'
        )
    """)
    )

    # 客户风控相关标签
    conn.execute(
        text("""
        UPDATE risk_tag
        SET risk_type = 'all_employee'
        WHERE name IN (
            '无实际入金交易', '同IP/设备多账户', '盈亏与返佣倒挂', '高频交易异常'
        )
    """)
    )

    # 代理商风控相关标签
    conn.execute(
        text("""
        UPDATE risk_tag
        SET risk_type = 'agent_user'
        WHERE name IN (
            '佣金异常波动', '代理刷单嫌疑', '客户质量异常'
        )
    """)
    )

    # 验证更新结果
    result = conn.execute(text("SELECT name, risk_type FROM risk_tag ORDER BY id"))
    print("更新后的 risk_type 映射:")
    for row in result:
        print(f"  {row[0]}: {row[1]}")


def downgrade():
    """回滚：将所有 risk_type 重置为 all_employee"""
    if not _table_exists("risk_tag"):
        return

    conn = op.get_bind()
    conn.execute(text("UPDATE risk_tag SET risk_type = 'all_employee'"))
