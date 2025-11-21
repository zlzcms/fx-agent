# 代码规范和提交规范

本项目已配置了代码提交前的规范检查，包括代码格式化和commit提交规范。

## 代码规范

### ESLint 规则

- 使用单引号
- 使用分号
- 缩进2个空格
- 不允许未使用的变量
- 生产环境警告console和debugger

### Prettier 格式化

- 单引号
- 分号结尾
- 2个空格缩进
- 行宽80字符
- 不使用尾随逗号

## 提交规范

### Commit 消息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式化，不影响代码逻辑
- `refactor`: 重构代码
- `perf`: 性能优化
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动
- `revert`: 回滚
- `build`: 构建系统或外部依赖项的更改

### 示例

```bash
feat(auth): 添加用户登录功能

fix(chat): 修复消息发送失败的问题

docs: 更新API文档

style: 格式化代码
```

## 使用方法

### 手动运行检查

```bash
# 代码检查和修复
npm run lint

# 代码格式化
npm run format
```

### 自动检查

- **提交前检查**: 每次`git commit`时会自动运行ESLint和Prettier检查暂存的文件
- **提交信息检查**: 每次`git commit`时会自动检查commit信息格式

### 绕过检查（不推荐）

```bash
# 跳过pre-commit检查
git commit --no-verify -m "commit message"
```

## 注意事项

1. 首次提交前请确保所有文件都符合代码规范
2. 如果pre-commit检查失败，请修复问题后重新提交
3. commit信息必须符合约定式提交规范，否则提交会被拒绝
4. 建议在IDE中安装ESLint和Prettier插件以获得实时提示
