# 团队成员开发环境配置检查清单

## 🚀 新成员入职必做事项

### 1. 基础环境配置
- [ ] 克隆项目仓库
- [ ] 安装 Python 3.10+
- [ ] 安装 uv 包管理器
- [ ] 配置数据库连接

### 2. **🔥 Git Hooks 配置（必须完成）**
- [ ] **立即运行**: `./scripts/development/install-git-hooks.sh`
- [ ] 验证 pre-commit 工具已安装: `pre-commit --version`
- [ ] 验证 hooks 文件存在:
  - [ ] `.git/hooks/pre-commit`
  - [ ] `.git/hooks/commit-msg`
  - [ ] `.git/hooks/pre-commit-alembic`
- [ ] 测试提交一个小改动，确认 hooks 正常工作

### 3. 开发工具配置
- [ ] 配置 IDE/编辑器
- [ ] 安装项目依赖: `uv sync`
- [ ] 配置环境变量

### 4. 首次启动验证
- [ ] 使用 `./scripts/development/dev-start.sh` 启动项目
- [ ] 确认所有检查通过
- [ ] 访问 API 文档页面验证服务正常

## 🔄 现有成员补充配置

**如果您已经在开发但尚未安装 Git hooks，请立即执行以下步骤：**

### 立即行动清单
- [ ] **停止当前开发工作**
- [ ] **运行**: `./scripts/development/install-git-hooks.sh`
- [ ] **验证安装**: `./scripts/development/check-git-hooks-status.sh`
- [ ] **测试提交**: 提交一个小改动验证 hooks 工作正常
- [ ] **继续开发**: 使用 `./scripts/development/dev-start.sh` 启动项目

## 📋 日常开发检查

### 每次启动开发前
- [ ] 使用 `./scripts/development/dev-start.sh` 启动（自动检查 hooks）
- [ ] 或手动检查: `./scripts/development/check-git-hooks-status.sh`

### 提交代码前
- [ ] 确保所有 pre-commit 检查通过
- [ ] 确保提交信息符合规范
- [ ] 确保数据库迁移状态正确

## 🆘 常见问题解决

### Git Hooks 相关
- **问题**: 提交时出现 "No module named 'backend'" 错误
- **解决**: 设置 PYTHONPATH: `export PYTHONPATH=$PYTHONPATH:$(pwd):$(pwd)/backend`

- **问题**: pre-commit 检查失败
- **解决**: 运行 `pre-commit run --all-files` 修复格式问题

- **问题**: Alembic 迁移检查失败
- **解决**: 检查数据库连接，运行 `alembic upgrade head`

### 获取帮助
- 查看详细文档: `README_GIT_HOOKS.md`
- 联系团队技术负责人
- 在团队群组中提问

## ✅ 配置完成确认

**请在完成所有配置后，在团队群组中确认：**

```
✅ [您的姓名] Git hooks 配置完成
- 安装脚本执行成功
- 测试提交正常
- 开发环境启动正常
```

---

**记住：Git hooks 不仅是工具，更是团队代码质量的守护者！** 🛡️
