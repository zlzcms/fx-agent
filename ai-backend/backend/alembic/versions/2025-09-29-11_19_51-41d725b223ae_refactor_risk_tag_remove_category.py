"""refactor_risk_tag_remove_category

Revision ID: 41d725b223ae
Revises: 2025011500001
Create Date: 2025-09-29 11:19:51.883112

"""

import sqlalchemy as sa

from alembic import op
from sqlalchemy import text

from backend.common.enums import RiskType

# revision identifiers, used by Alembic.
revision = "41d725b223ae"
down_revision = "2025011500001"
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
    """升级：重构风控标签表，移除分类表"""

    # 1. 添加 risk_type 字段到 risk_tag 表
    if _table_exists("risk_tag") and not _column_exists("risk_tag", "risk_type"):
        op.add_column("risk_tag", sa.Column("risk_type", sa.String(50), nullable=True, comment="风控类型"))

        # 创建索引
        op.create_index("ix_risk_tag_risk_type", "risk_tag", ["risk_type"])

    # 2. 迁移现有数据：将 category_id 映射到 risk_type
    if _table_exists("risk_tag") and _table_exists("risk_tag_category"):
        # 定义映射关系
        category_mapping = {
            "客户风控": RiskType.ALL_EMPLOYEE.value,
            "员工风控": RiskType.CRM_USER.value,
            "代理商风控": RiskType.AGENT_USER.value,
            "出金风控": RiskType.PAYMENT.value,
        }

        # 更新现有记录的 risk_type 字段
        for category_name, risk_type in category_mapping.items():
            conn = op.get_bind()
            conn.execute(
                text("""
                UPDATE risk_tag
                SET risk_type = :risk_type
                WHERE category_id IN (
                    SELECT id FROM risk_tag_category
                    WHERE name = :category_name AND deleted_at IS NULL
                )
            """),
                {"risk_type": risk_type, "category_name": category_name},
            )

        # 处理可能遗漏的记录，根据标签名称进行智能映射
        conn = op.get_bind()

        # 如果标签名称包含特定关键词，进行智能映射
        conn.execute(
            text("""
            UPDATE risk_tag
            SET risk_type = 'agent_user'
            WHERE risk_type IS NULL
            AND (name LIKE '%代理%' OR name LIKE '%代理商%')
        """)
        )

        conn.execute(
            text("""
            UPDATE risk_tag
            SET risk_type = 'crm_user'
            WHERE risk_type IS NULL
            AND (name LIKE '%员工%' OR name LIKE '%内部%' OR name LIKE '%CRM%')
        """)
        )

        conn.execute(
            text("""
            UPDATE risk_tag
            SET risk_type = 'payment'
            WHERE risk_type IS NULL
            AND (name LIKE '%出金%' OR name LIKE '%支付%' OR name LIKE '%财务%')
        """)
        )

        # 最后，将所有剩余的 NULL 值设置为默认值
        conn.execute(
            text("""
            UPDATE risk_tag
            SET risk_type = 'all_employee'
            WHERE risk_type IS NULL
        """)
        )

    # 3. 将 risk_type 字段设置为 NOT NULL
    if _column_exists("risk_tag", "risk_type"):
        # 再次确保没有空值
        conn = op.get_bind()
        conn.execute(
            text("""
            UPDATE risk_tag
            SET risk_type = 'all_employee'
            WHERE risk_type IS NULL
        """)
        )

        # 验证是否还有空值
        result = conn.execute(text("SELECT COUNT(*) FROM risk_tag WHERE risk_type IS NULL"))
        null_count = result.scalar()
        if null_count > 0:
            raise Exception(f"仍有 {null_count} 条记录的 risk_type 为空，无法设置为 NOT NULL")

        op.alter_column("risk_tag", "risk_type", nullable=False)

    # 4. 删除外键约束
    if _constraint_exists("risk_tag", "risk_tag_category_id_fkey"):
        op.drop_constraint("risk_tag_category_id_fkey", "risk_tag", type_="foreignkey")

    # 5. 删除 category_id 字段
    if _column_exists("risk_tag", "category_id"):
        # 删除相关索引
        if _index_exists("risk_tag", "ix_risk_tag_category_id"):
            op.drop_index("ix_risk_tag_category_id", "risk_tag")

        op.drop_column("risk_tag", "category_id")

    # 6. 删除 risk_tag_category 表
    if _table_exists("risk_tag_category"):
        op.drop_table("risk_tag_category")


def downgrade():
    """降级：恢复原有的分类表结构"""

    # 1. 重新创建 risk_tag_category 表
    if not _table_exists("risk_tag_category"):
        op.create_table(
            "risk_tag_category",
            sa.Column("id", sa.String(36), primary_key=True, comment="标签分类ID，使用UUID"),
            sa.Column("name", sa.String(100), nullable=False, index=True, unique=True, comment="分类名称"),
            sa.Column("created_time", sa.DateTime, nullable=False, comment="创建时间"),
            sa.Column("updated_time", sa.DateTime, nullable=False, comment="更新时间"),
            sa.Column("deleted_at", sa.DateTime, nullable=True, index=True, comment="软删除时间，NULL表示未删除"),
        )

    # 2. 重新插入分类数据
    categories = [
        {"id": "cat_all_employee", "name": "客户风控"},
        {"id": "cat_crm_user", "name": "员工风控"},
        {"id": "cat_agent_user", "name": "代理商风控"},
        {"id": "cat_payment", "name": "出金风控"},
    ]

    for category in categories:
        op.execute(
            text("""
            INSERT INTO risk_tag_category (id, name, created_time, updated_time)
            VALUES (:id, :name, NOW(), NOW())
            ON CONFLICT (id) DO NOTHING
        """),
            category,
        )

    # 3. 添加 category_id 字段到 risk_tag 表
    if _table_exists("risk_tag") and not _column_exists("risk_tag", "category_id"):
        op.add_column("risk_tag", sa.Column("category_id", sa.String(36), nullable=True, comment="标签分类ID"))

        # 创建索引
        op.create_index("ix_risk_tag_category_id", "risk_tag", ["category_id"])

    # 4. 迁移数据：将 risk_type 映射回 category_id
    if _table_exists("risk_tag") and _column_exists("risk_tag", "risk_type"):
        risk_type_mapping = {
            RiskType.ALL_EMPLOYEE: "cat_all_employee",
            RiskType.CRM_USER: "cat_crm_user",
            RiskType.AGENT_USER: "cat_agent_user",
            RiskType.PAYMENT: "cat_payment",
        }

        for risk_type, category_id in risk_type_mapping.items():
            op.execute(
                text("""
                UPDATE risk_tag
                SET category_id = :category_id
                WHERE risk_type = :risk_type
            """),
                {"category_id": category_id, "risk_type": risk_type},
            )

    # 5. 将 category_id 设置为 NOT NULL
    if _column_exists("risk_tag", "category_id"):
        op.alter_column("risk_tag", "category_id", nullable=False)

    # 6. 添加外键约束
    if _table_exists("risk_tag") and _table_exists("risk_tag_category"):
        op.create_foreign_key("risk_tag_category_id_fkey", "risk_tag", "risk_tag_category", ["category_id"], ["id"])

    # 7. 删除 risk_type 字段
    if _column_exists("risk_tag", "risk_type"):
        # 删除相关索引
        if _index_exists("risk_tag", "ix_risk_tag_risk_type"):
            op.drop_index("ix_risk_tag_risk_type", "risk_tag")

        op.drop_column("risk_tag", "risk_type")
