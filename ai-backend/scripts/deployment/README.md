# 部署脚本使用说明

本目录包含了用于生产环境的Docker部署脚本。

> **注意**: 现在统一使用根目录下的 `jenkins-docker-deploy.sh` 进行部署，该脚本功能更完整，包含健康检查、错误处理等功能。

## 📁 脚本文件说明

### 🔍 监控脚本
- **`health-check.sh`** - 生产环境健康检查

## 🎯 推荐使用方式

### 生产环境部署
```bash
# 使用Jenkins部署脚本（推荐）
./jenkins-docker-deploy.sh

# 独立健康检查
./scripts/deployment/health-check.sh
```

## 🔧 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- 确保在项目根目录运行脚本

## ⚠️ 注意事项

1. **健康检查脚本**：
   - 检查所有核心服务状态
   - 验证数据库和Redis连接
   - 监控资源使用情况

2. **数据安全**：
   - 停止服务不会删除数据卷
   - 生产环境数据删除前请务必备份
   - 如需清理数据，请手动操作

## 🚨 故障排除

### 健康检查失败处理
1. **FastAPI服务异常**：检查容器日志和端口占用
2. **数据库连接失败**：验证PostgreSQL容器状态
3. **Redis连接失败**：检查Redis服务和网络配置

### 日志查看
```bash
# 查看健康检查详细输出
./scripts/deployment/health-check.sh

# 查看特定服务日志
docker logs fba_server
docker logs fba_postgres
docker logs fba_redis
```

## 📞 技术支持

如遇到问题，请检查：
1. 使用 `jenkins-docker-deploy.sh` 进行完整部署
2. Docker服务状态和资源使用
3. 网络和卷配置
4. 服务日志输出
