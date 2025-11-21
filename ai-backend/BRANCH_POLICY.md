# 分支策略说明

## ⚠️ 重要分支保护规则

### feature/king 分支

**禁止将 `feature/king` 分支合并到 `dev` 分支**

- **状态**: 此分支为实验性分支，不应合并到主开发分支
- **原因**: 该分支包含的实验性功能或代码不应进入主开发流程
- **最后更新**: 2025-10-29

#### 如何避免误合并

1. **手动合并前检查**
   - 在合并前确认目标分支和目标源分支
   - 使用 `git log dev..feature/king` 查看将要合并的提交

2. **使用 Pull Request/Merge Request**
   - 在代码审查平台上明确标注 `feature/king` 不应合并
   - 如果看到来自 `feature/king` 的合并请求，请拒绝或关闭

3. **Git 命令检查**
   ```bash
   # 检查是否有来自 feature/king 的未合并提交
   git log dev..feature/king

   # 查看合并历史中是否包含 feature/king
   git log --oneline --all --graph | grep "feature/king"
   ```

#### 历史记录

根据 Git 历史记录，`feature/king` 分支的内容在历史中曾被部分合并过（通过多次 `Merge branch 'feature/king' into dev` 提交），但当前策略是不再继续合并该分支。

---

## 其他分支说明

### dev 分支
- 主开发分支
- 所有功能分支应合并到此分支（除了明确禁止的，如 `feature/king`）

### master 分支
- 主分支
- 仅用于发布稳定版本
