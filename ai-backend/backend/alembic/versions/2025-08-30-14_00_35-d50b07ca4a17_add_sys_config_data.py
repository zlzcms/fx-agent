"""add_sys_config_data

Revision ID: d50b07ca4a17
Revises: 3dd145ba5ca2
Create Date: 2025-08-30 14:00:35.047651

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "d50b07ca4a17"
down_revision = "3dd145ba5ca2"
branch_labels = None
depends_on = None


def upgrade():
    # 同步本地数据库的sys_config配置到线上
    from sqlalchemy import text

    # 本地数据库的实际配置数据
    configs = [
        ("状态", "EMAIL", "EMAIL_STATUS", "1", False, None),
        ("服务器地址", "EMAIL", "EMAIL_HOST", "smtp.qq.com", False, None),
        ("服务器端口", "EMAIL", "EMAIL_PORT", "465", False, None),
        ("邮箱账号", "EMAIL", "EMAIL_USERNAME", "fba@qq.com", False, None),
        ("邮箱密码", "EMAIL", "EMAIL_PASSWORD", "", False, None),
        ("SSL 加密", "EMAIL", "EMAIL_SSL", "1", False, None),
    ]

    # 批量插入，避免重复，增加错误处理
    for config in configs:
        name, config_type, key, value, is_frontend, remark = config
        try:
            op.execute(
                text("""
                    INSERT INTO sys_config (name, type, key, value, is_frontend, remark)
                    VALUES (:name, :type, :key, :value, :is_frontend, :remark)
                    ON CONFLICT (key) DO UPDATE SET
                        name = EXCLUDED.name,
                        type = EXCLUDED.type,
                        value = EXCLUDED.value,
                        is_frontend = EXCLUDED.is_frontend,
                        remark = EXCLUDED.remark,
                        updated_time = CURRENT_TIMESTAMP
                """),
                {
                    "name": name,
                    "type": config_type,
                    "key": key,
                    "value": value,
                    "is_frontend": is_frontend,
                    "remark": remark,
                },
            )
            print(f"✅ 配置项 {key} 同步成功")
        except Exception as e:
            print(f"⚠️ 配置项 {key} 同步失败: {e}")
            # 继续执行其他配置项，不中断整个迁移
            continue


def downgrade():
    # 删除本次迁移添加的配置项
    keys_to_remove = ["EMAIL_STATUS", "EMAIL_HOST", "EMAIL_PORT", "EMAIL_USERNAME", "EMAIL_PASSWORD", "EMAIL_SSL"]

    from sqlalchemy import text

    for key in keys_to_remove:
        op.execute(text("DELETE FROM sys_config WHERE key = :key"), {"key": key})
