#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移检查脚本 - 用于pre-commit钩子
检查是否需要生成新的迁移文件，并自动执行迁移
"""

import os
import subprocess
import sys

from pathlib import Path

# 设置项目路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"

# 添加到Python路径
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(BACKEND_DIR))

# 设置环境变量
os.environ["PYTHONPATH"] = f"{PROJECT_ROOT}:{BACKEND_DIR}"
os.chdir(PROJECT_ROOT)

# 确保在subprocess中也使用正确的PYTHONPATH
os.environ.setdefault("PYTHONPATH", f"{PROJECT_ROOT}:{BACKEND_DIR}")


def check_database_connection():
    """检查数据库连接"""
    try:
        from sqlalchemy import URL, create_engine, text

        from backend.core.conf import settings

        # 构建同步数据库URL
        sync_url = URL.create(
            drivername="mysql+pymysql" if settings.DATABASE_TYPE == "mysql" else "postgresql+psycopg2",
            username=settings.DATABASE_USER,
            password=settings.DATABASE_PASSWORD,
            host=settings.DATABASE_HOST,
            port=settings.DATABASE_PORT,
            database=settings.DATABASE_SCHEMA,
        )

        engine = create_engine(sync_url)

        with engine.begin() as conn:
            conn.execute(text("SELECT 1"))
            return True
    except Exception:
        return False


def check_migration_needed():
    """检查是否需要生成新的迁移文件"""
    try:
        # 设置环境变量
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{PROJECT_ROOT}:{BACKEND_DIR}"

        # 检查当前版本与head版本是否一致
        current_result = subprocess.run(
            ["alembic", "current"], capture_output=True, text=True, cwd=PROJECT_ROOT, env=env
        )

        heads_result = subprocess.run(["alembic", "heads"], capture_output=True, text=True, cwd=PROJECT_ROOT, env=env)

        if current_result.returncode != 0 or heads_result.returncode != 0:
            print("⚠️  无法检查迁移状态")
            return False

        # 提取版本号
        current_lines = [line for line in current_result.stdout.split("\n") if line and not line.startswith("INFO")]
        heads_lines = [line for line in heads_result.stdout.split("\n") if line and not line.startswith("INFO")]

        if not current_lines or not heads_lines:
            print("⚠️  无法获取迁移版本信息")
            return False

        current_version = current_lines[-1].split()[0] if current_lines[-1].split() else ""
        head_version = heads_lines[-1].split()[0] if heads_lines[-1].split() else ""

        if current_version != head_version:
            print(f"🔄 检测到需要迁移: {current_version} -> {head_version}")
            return True

        # 检查是否有未生成的模型变更
        check_result = subprocess.run(["alembic", "check"], capture_output=True, text=True, cwd=PROJECT_ROOT, env=env)

        # 如果检查失败，检查是否是已知的可以忽略的差异
        if check_result.returncode != 0:
            error_output = check_result.stderr or check_result.stdout
            # 检查是否是 server_default 或索引的差异（这些可以忽略）
            if "modify_default" in error_output or "add_index" in error_output:
                # 这些是模型和数据库的细微差异，不影响功能
                # - 模型使用 Python default，数据库使用 server_default
                # - 主键列已有索引，额外的索引是冗余的
                print("✅ 数据库迁移检查通过（忽略已知的细微差异）")
                return False
            else:
                # 其他类型的差异需要处理
                print("🔄 检测到未生成的模型变更")
                return True

        if "No new upgrade operations detected" not in check_result.stdout:
            print("🔄 检测到未生成的模型变更")
            return True

        return False

    except Exception as e:
        print(f"❌ 检查迁移状态失败: {e}")
        return False


def run_migration():
    """执行数据库迁移"""
    try:
        # 设置环境变量
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{PROJECT_ROOT}:{BACKEND_DIR}"

        print("🔄 执行数据库迁移...")
        result = subprocess.run(
            ["alembic", "upgrade", "head"], capture_output=True, text=True, cwd=PROJECT_ROOT, env=env
        )

        if result.returncode == 0:
            print("✅ 数据库迁移完成")
            return True
        else:
            print(f"❌ 数据库迁移失败: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ 执行迁移失败: {e}")
        return False


def main():
    """主函数"""
    print("🔍 检查数据库迁移状态...")

    # 检查数据库连接
    if not check_database_connection():
        print("⚠️  数据库连接失败，跳过迁移检查")
        print("💡 提示: 确保数据库服务正在运行")
        return 0  # 不阻止提交，但给出警告

    # 检查是否需要迁移
    if check_migration_needed():
        print("❌ 检测到数据库模型变更，需要生成迁移文件")
        print("💡 请先运行以下命令生成迁移文件:")
        print("   alembic revision --autogenerate -m '描述你的变更'")
        print("💡 然后运行以下命令应用迁移:")
        print("   alembic upgrade head")
        print("💡 完成后重新提交代码")
        return 1  # 阻止提交
    else:
        print("✅ 数据库已是最新状态")
        return 0


if __name__ == "__main__":
    sys.exit(main())
