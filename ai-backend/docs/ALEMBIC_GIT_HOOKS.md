# Alembic Git Hooks 使用指南

本文档介绍如何使用Git提交时的Alembic自动检测功能，确保团队协作中数据库迁移的一致性。

## 🚀 快速开始

### 1. 安装Git Hooks

```bash
# 在项目根目录运行
./scripts/development/install-git-hooks.sh
```

这个脚本会自动：
- 安装pre-commit工具
- 配置所有的Git hooks
- 设置Alembic检查

### 2. 验证安装

```bash
# 手动运行所有检查
pre-commit run --all-files
```

## 🔍 检查项目

### Alembic相关检查

1. **模型变更检测**
   - 自动检测未生成的数据库模型变更
   - 比较当前模型与数据库结构
   - 如果有变更但未生成迁移文件，会阻止提交

2. **迁移同步检查**
   - 确保本地数据库与迁移文件同步
   - 检查当前数据库版本是否为最新

3. **Git状态检查**
   - 检查未跟踪的迁移文件
   - 检测迁移文件中的Git冲突标记

### 其他检查

- 代码格式检查 (ruff)
- YAML/TOML文件格式检查
- 提交信息格式检查 (commitizen)
- UV锁文件检查

## 📋 工作流程

### 开发人员修改数据库模型

1. **修改模型文件**
   ```python
   # 例如：在backend/app/admin/model/user.py中添加字段
   class User(MappedBase):
       __tablename__ = "user"

       id: Mapped[int] = mapped_column(primary_key=True)
       username: Mapped[str] = mapped_column(String(50))
       email: Mapped[str] = mapped_column(String(100))  # 新增字段
   ```

2. **尝试提交代码**
   ```bash
   git add .
   git commit -m "feat: 添加用户邮箱字段"
   ```

3. **检查会自动运行**
   ```
   🔍 检查Alembic迁移状态...
   ❌ 检测到未生成的数据库模型变更！

   变更详情：
     - add_column('user', sa.Column('email', sa.String(100), nullable=True))

   请运行以下命令生成迁移文件：
     alembic revision --autogenerate -m "添加用户邮箱字段"
     alembic upgrade head
   ```

4. **生成迁移文件**
   ```bash
   alembic revision --autogenerate -m "添加用户邮箱字段"
   alembic upgrade head
   ```

5. **重新提交**
   ```bash
   git add .
   git commit -m "feat: 添加用户邮箱字段"
   # 现在检查会通过
   ```

### 其他开发人员同步代码

1. **拉取最新代码**
   ```bash
   git pull origin main
   ```

2. **应用数据库迁移**
   ```bash
   alembic upgrade head
   ```

3. **验证同步状态**
   ```bash
   # 运行检查确保一切正常
   pre-commit run check-alembic --all-files
   ```

## 🛠️ 高级用法

### 手动运行特定检查

```bash
# 只运行Alembic检查
pre-commit run check-alembic --all-files

# 运行简单的Alembic检查
pre-commit run check-alembic-simple --all-files

# 直接运行Python检查脚本
python3 scripts/development/alembic-model-check.py

# 直接运行bash检查脚本
./scripts/development/check-alembic.sh
```

### 跳过检查（紧急情况）

```bash
# 跳过所有pre-commit检查
git commit --no-verify -m "紧急修复"

# 或者设置环境变量跳过特定检查
SKIP=check-alembic git commit -m "跳过Alembic检查"
```

### 更新hooks配置

```bash
# 更新pre-commit配置后重新安装
pre-commit clean
pre-commit install
```

## 🔧 故障排除

### 常见问题

1. **数据库连接失败**
   ```
   ❌ 检查过程中出现错误: (psycopg2.OperationalError) connection failed
   ```

   **解决方案：**
   - 确保数据库服务正在运行
   - 检查`.env`文件中的数据库配置
   - 确保数据库用户有足够权限

2. **模块导入错误**
   ```
   ❌ 检查过程中出现错误: No module named 'app.admin.model'
   ```

   **解决方案：**
   - 确保在backend目录下运行
   - 检查Python路径配置
   - 安装所有依赖：`pip install -r requirements.txt`

3. **迁移文件冲突**
   ```
   ❌ 发现迁移文件中的Git冲突标记！
   ```

   **解决方案：**
   - 手动解决迁移文件中的冲突
   - 或者使用`alembic merge`命令合并冲突的迁移

### 禁用特定检查

如果某个检查在特定环境下不适用，可以在`.pre-commit-config.yaml`中禁用：

```yaml
- repo: local
  hooks:
    - id: check-alembic
      name: 检查Alembic迁移状态
      entry: python3 scripts/development/alembic-model-check.py
      language: system
      pass_filenames: false
      files: '^(backend/.*\.py|backend/alembic/.*)$'
      stages: [pre-commit]
      # 添加这行来禁用
      # exclude: '.*'
```

## 📚 相关文档

- [Alembic官方文档](https://alembic.sqlalchemy.org/)
- [Pre-commit官方文档](https://pre-commit.com/)
- [项目数据库迁移指南](./DATABASE_MIGRATION.md)

## 🤝 团队协作建议

1. **统一环境**：确保所有开发人员使用相同的数据库版本和配置
2. **及时同步**：每天开始工作前先拉取最新代码并应用迁移
3. **描述清晰**：迁移文件要有清晰的描述信息
4. **小步迭代**：避免一次性进行大量数据库结构变更
5. **备份重要**：生产环境迁移前务必备份数据库

## 🔄 CI/CD集成

这些检查也可以集成到CI/CD流水线中：

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'

    - name: Install dependencies
      run: |
        pip install -r backend/requirements.txt
        pip install pre-commit

    - name: Run pre-commit
      run: pre-commit run --all-files

    - name: Run Alembic checks
      run: python3 scripts/development/alembic-model-check.py
```

通过这套完整的Git hooks系统，团队可以确保数据库迁移的一致性，避免因为忘记生成迁移文件而导致的部署问题。
