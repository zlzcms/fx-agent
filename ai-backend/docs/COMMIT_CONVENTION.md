# Commit Message 规范

本项目使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范来标准化 commit message 格式。

## 格式

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

## Type 类型

- **feat**: 新功能
- **fix**: 修复 bug
- **docs**: 文档更新
- **style**: 代码格式化（不影响代码逻辑）
- **refactor**: 代码重构
- **perf**: 性能优化
- **test**: 测试相关
- **build**: 构建系统或外部依赖变更
- **ci**: CI 配置文件和脚本变更
- **chore**: 其他不修改源码或测试的变更
- **revert**: 回滚之前的 commit

## 示例

### 基本格式
```bash
git commit -m "feat: add user authentication"
git commit -m "fix: resolve login validation issue"
git commit -m "docs: update API documentation"
```

### 带作用域
```bash
git commit -m "feat(auth): add JWT token validation"
git commit -m "fix(api): handle null response in user service"
```

### 破坏性变更
```bash
git commit -m "feat!: remove deprecated API endpoints"
git commit -m "feat(api)!: change user schema structure"
```

## Pre-commit 检查

项目已配置 pre-commit hooks 来自动检查：
- Commit message 格式
- 代码格式化 (ruff)
- YAML/TOML 文件格式
- 依赖锁定文件更新

如果 commit message 不符合规范，提交将被拒绝并显示错误信息。

## 工具

可以使用 `commitizen` 工具来交互式创建符合规范的 commit message：

```bash
uv run cz commit
```

这将引导您选择类型、作用域和描述，自动生成符合规范的 commit message。
