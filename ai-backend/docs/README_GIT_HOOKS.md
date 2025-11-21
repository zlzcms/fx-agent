# Git提交时Alembic自动检测系统

## 🎯 功能概述

本系统为项目添加了Git提交时的Alembic数据库迁移自动检测功能，确保：
- ✅ 数据库模型变更时自动提醒生成迁移文件
- ✅ 防止忘记生成迁移文件导致的部署问题
- ✅ 团队协作中数据库结构的一致性
- ✅ 自动检测迁移文件冲突和Git状态

## 🚀 快速安装

```bash
# 在项目根目录运行一键安装脚本
./scripts/development/install-git-hooks.sh
```

## 📋 检查项目

### 自动检查（每次git commit时）
1. **模型变更检测** - 检测未生成的数据库模型变更
2. **迁移同步检查** - 确保本地数据库与迁移文件同步
3. **Git状态检查** - 检查未跟踪的迁移文件和冲突
4. **代码格式检查** - ruff代码格式化
5. **配置文件检查** - YAML/TOML格式验证
6. **提交信息检查** - commitizen格式规范

### 手动检查
```bash
# 运行所有检查
pre-commit run --all-files

# 只运行Alembic检查
pre-commit run check-alembic --all-files

# 直接运行检查脚本
python3 scripts/development/alembic-model-check.py
```

## 🔄 典型工作流程

### 1. 开发人员修改数据库模型
```python
# 修改模型文件，例如添加新字段
class User(MappedBase):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(100))  # 新增字段
```

### 2. 尝试提交代码
```bash
git add .
git commit -m "feat: 添加用户邮箱字段"
```

### 3. 系统自动检测并提示
```
❌ 检测到未生成的数据库模型变更！

变更详情：
  - add_column('user', sa.Column('email', sa.String(100), nullable=True))

请运行以下命令生成迁移文件：
  alembic revision --autogenerate -m "添加用户邮箱字段"
  alembic upgrade head
```

### 4. 生成迁移文件并重新提交
```bash
alembic revision --autogenerate -m "添加用户邮箱字段"
alembic upgrade head

# 重新提交，现在会通过检查
git add .
git commit -m "feat: 添加用户邮箱字段"
```

### 5. 其他开发人员同步
```bash
git pull origin main
alembic upgrade head
```

## 🛠️ 核心文件说明

| 文件 | 功能 |
|------|------|
| `.pre-commit-config.yaml` | Pre-commit配置，定义所有检查项目 |
| `scripts/development/alembic-model-check.py` | 智能Python检查脚本，检测模型变更 |
| `scripts/development/check-alembic.sh` | 简单Bash检查脚本，检查Git状态 |
| `scripts/development/install-git-hooks.sh` | 一键安装脚本 |
| `docs/ALEMBIC_GIT_HOOKS.md` | 详细使用文档 |

## ⚠️ 注意事项

1. **数据库连接**：检查需要数据库连接，确保数据库服务正在运行
2. **环境依赖**：确保安装了所有Python依赖
3. **团队协作**：所有团队成员都应该运行安装脚本
4. **紧急情况**：可以使用`git commit --no-verify`跳过检查

## 🔧 故障排除

### 数据库连接失败
```bash
# 检查数据库服务状态
psql -h localhost -U postgres -d fba -c "SELECT 1;"

# 检查环境配置
cat backend/.env
```

### 模块导入错误
如果遇到 `No module named 'backend'` 错误，可以使用提供的辅助脚本：

```bash
# 直接使用git commit
git commit -m "你的提交信息"

# 或者手动设置PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd):$(pwd)/backend
git commit -m "你的提交信息"
```

### 跳过检查（紧急情况）
```bash
# 跳过所有检查
git commit --no-verify -m "紧急修复"

# 跳过特定检查
SKIP=check-alembic git commit -m "跳过Alembic检查"
```

### 更新配置
```bash
# 重新安装hooks
pre-commit clean
pre-commit install
```

## 📚 更多信息

- 详细文档：[docs/ALEMBIC_GIT_HOOKS.md](docs/ALEMBIC_GIT_HOOKS.md)
- Alembic官方文档：https://alembic.sqlalchemy.org/
- Pre-commit官方文档：https://pre-commit.com/

---

通过这套系统，团队可以确保数据库迁移的一致性，避免因忘记生成迁移文件而导致的部署问题！🎉
