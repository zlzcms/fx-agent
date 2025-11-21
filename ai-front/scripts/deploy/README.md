# 自动部署脚本

这个目录包含了自动部署到服务器的脚本。

## 文件说明

- `deploy.sh` - 主要的部署脚本
- `deploy-config.sh` - 部署配置文件
- `nginx.conf` - Nginx配置文件

## 使用方法

### 1. 构建并部署

```bash
# 构建antd应用并自动部署
pnpm run build:deploy
```

### 2. 仅部署（需要先构建）

```bash
# 仅执行部署
pnpm run deploy
```

### 3. 手动执行部署脚本

```bash
# 直接运行部署脚本
./scripts/deploy/deploy.sh
```

## 配置说明

### SSH密钥认证（推荐）

1. 生成SSH密钥对：
```bash
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
```

2. 将公钥复制到服务器：
```bash
ssh-copy-id root@47.239.101.153
```

3. 修改 `deploy-config.sh` 中的 `USE_PASSWORD=false`

### 密码认证

如果需要使用密码认证，需要安装 `sshpass`：

```bash
brew install sshpass
```

## 安全注意事项

1. **强烈建议使用SSH密钥认证**而不是密码认证
2. 如果必须使用密码，请确保 `deploy-config.sh` 文件的权限设置正确：
```bash
chmod 600 scripts/deploy/deploy-config.sh
```
3. 不要将包含密码的配置文件提交到版本控制系统

## 自定义配置

编辑 `deploy-config.sh` 文件来修改：
- 服务器地址和用户名
- 部署路径
- rsync选项
- 认证方式

## 故障排除

### 常见问题

1. **权限被拒绝**
   - 确保SSH密钥已正确配置
   - 检查服务器用户权限

2. **sshpass未找到**
   - 运行 `brew install sshpass` 安装
   - 或切换到SSH密钥认证

3. **dist目录不存在**
   - 先运行 `pnpm run build:antd` 构建项目

4. **连接超时**
   - 检查服务器地址和网络连接
   - 确认服务器SSH服务正在运行