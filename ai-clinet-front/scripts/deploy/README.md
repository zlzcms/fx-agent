# AI Client Front 部署说明

本目录包含 AI Client Front 项目的自动化部署脚本。

## 文件说明

- `deploy.sh` - 主部署脚本
- `deploy-config.sh` - 部署配置文件
- `README.md` - 本说明文档

## 使用方法

### 1. 构建项目

```bash
# 在项目根目录执行
npm run build
# 或
pnpm build
```

### 2. 配置部署参数

编辑 `deploy-config.sh` 文件，修改以下配置：

- `SERVER_HOST` - 服务器地址
- `SERVER_USER` - 服务器用户名
- `SERVER_PATH` - 服务器部署路径
- `SSH_PASSWORD` - SSH密码（如果使用密码认证）

### 3. 执行部署

```bash
# 在项目根目录执行
./scripts/deploy/deploy.sh
```

### 4. 快速部署命令

如果你想直接使用 rsync 命令部署（类似于你提到的命令），可以执行：

```bash
rsync -avz -e ssh ./dist/ root@47.239.101.153:/www/ai/ai-clinet-front/dist/
```

## 注意事项

1. **SSH认证方式**：
   - 推荐使用SSH密钥认证
   - 如果使用密码认证，需要安装 `sshpass`：`brew install sshpass`

2. **构建时间注入**：
   - 脚本会自动在页面中注入构建时间信息
   - 构建时间会显示在页面左下角

3. **文件同步**：
   - 使用 `--delete` 选项，会删除服务器上多余的文件
   - 确保服务器路径正确，避免误删重要文件

4. **权限设置**：
   - 确保部署脚本有执行权限：`chmod +x scripts/deploy/deploy.sh`

## 服务器配置

当前配置的服务器信息：

- 服务器：47.239.101.153
- 用户：root
- 部署路径：/www/ai/ai-clinet-front/dist/

## 故障排除

1. **权限问题**：确保有服务器访问权限
2. **路径问题**：检查本地dist目录和服务器路径是否正确
3. **网络问题**：确保网络连接正常
4. **SSH问题**：检查SSH配置和认证方式

## 自动化集成

可以将部署脚本集成到 CI/CD 流程中，或者添加到 package.json 的 scripts 中：

```json
{
  "scripts": {
    "deploy": "npm run build && ./scripts/deploy/deploy.sh"
  }
}
```
