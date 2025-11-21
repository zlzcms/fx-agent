"""change_risk_tag_id_to_auto_increment

Revision ID: f4b3d2ee10b1
Revises: 41d725b223ae
Create Date: 2025-09-29 15:45:09.654259

"""

import sqlalchemy as sa

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = "f4b3d2ee10b1"
down_revision = "41d725b223ae"
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
    """将 risk_tag 表的 id 字段从 UUID 改为自增整数"""

    # 1. 创建临时表来保存现有数据
    op.execute(
        text("""
        CREATE TABLE risk_tag_temp AS
        SELECT * FROM risk_tag
    """)
    )

    # 2. 删除原表
    op.drop_table("risk_tag")

    # 3. 重新创建表，使用自增 ID
    op.create_table(
        "risk_tag",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False, comment="标签ID，自增主键"),
        sa.Column("risk_type", sa.String(length=50), nullable=False, comment="风控类型"),
        sa.Column("name", sa.String(length=100), nullable=False, comment="标签名称"),
        sa.Column("description", sa.Text(), nullable=True, comment="标签描述"),
        sa.Column("created_time", sa.DateTime(timezone=True), nullable=False, comment="创建时间"),
        sa.Column("updated_time", sa.DateTime(timezone=True), nullable=True, comment="更新时间"),
        sa.Column("deleted_at", sa.DateTime(), nullable=True, comment="软删除时间，NULL表示未删除"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 4. 创建索引
    op.create_index("ix_risk_tag_id", "risk_tag", ["id"])
    op.create_index("ix_risk_tag_risk_type", "risk_tag", ["risk_type"])
    op.create_index("ix_risk_tag_name", "risk_tag", ["name"])
    op.create_index("ix_risk_tag_deleted_at", "risk_tag", ["deleted_at"])

    # 5. 从临时表恢复数据（不包含 id，让数据库自动生成）
    op.execute(
        text("""
        INSERT INTO risk_tag (risk_type, name, description, created_time, updated_time, deleted_at)
        SELECT risk_type, name, description, created_time, updated_time, deleted_at
        FROM risk_tag_temp
    """)
    )

    # 6. 删除临时表
    op.drop_table("risk_tag_temp")


def downgrade():
    """回滚：将 risk_tag 表的 id 字段从自增整数改回 UUID"""

    # 1. 创建临时表来保存现有数据
    op.execute(
        text("""
        CREATE TABLE risk_tag_temp AS
        SELECT * FROM risk_tag
    """)
    )

    # 2. 删除原表
    op.drop_table("risk_tag")

    # 3. 重新创建表，使用 UUID
    op.create_table(
        "risk_tag",
        sa.Column("id", sa.String(length=36), nullable=False, comment="标签ID，使用UUID"),
        sa.Column("risk_type", sa.String(length=50), nullable=False, comment="风控类型"),
        sa.Column("name", sa.String(length=100), nullable=False, comment="标签名称"),
        sa.Column("description", sa.Text(), nullable=True, comment="标签描述"),
        sa.Column("created_time", sa.DateTime(timezone=True), nullable=False, comment="创建时间"),
        sa.Column("updated_time", sa.DateTime(timezone=True), nullable=True, comment="更新时间"),
        sa.Column("deleted_at", sa.DateTime(), nullable=True, comment="软删除时间，NULL表示未删除"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 4. 创建索引
    op.create_index("ix_risk_tag_id", "risk_tag", ["id"])
    op.create_index("ix_risk_tag_risk_type", "risk_tag", ["risk_type"])
    op.create_index("ix_risk_tag_name", "risk_tag", ["name"])
    op.create_index("ix_risk_tag_deleted_at", "risk_tag", ["deleted_at"])

    # 5. 从临时表恢复数据（生成新的 UUID）
    op.execute(
        text("""
        INSERT INTO risk_tag (id, risk_type, name, description, created_time, updated_time, deleted_at)
        SELECT gen_random_uuid()::text, risk_type, name, description, created_time, updated_time, deleted_at
        FROM risk_tag_temp
    """)
    )

    # 6. 删除临时表
    op.drop_table("risk_tag_temp")
