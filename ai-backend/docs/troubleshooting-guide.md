# 线上问题排查指南

这份指南涵盖了Max AI Backend项目中所有日志源，帮助你快速定位和解决线上问题。

## 🎯 日志架构概览

项目使用多层日志架构：
- **Docker容器日志**：容器级别的系统日志
- **Supervisord日志**：进程管理器日志
- **应用日志**：FastAPI/Celery应用程序日志
- **Web服务器日志**：Granian/Gunicorn访问和错误日志
- **数据库日志**：PostgreSQL/Redis日志
- **业务日志**：登录日志、操作日志等

## 📋 快速检查清单

遇到问题时按以下顺序检查：

1. **服务状态** → Docker容器是否正常运行
2. **进程状态** → Supervisord管理的进程是否正常
3. **应用日志** → 查看具体错误信息
4. **资源状态** → CPU、内存、磁盘使用情况
5. **依赖服务** → 数据库、Redis连接状态

## 🐳 Docker容器日志

### 查看容器状态
```bash
# 查看所有容器状态
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 查看容器资源使用
docker stats --no-stream
```

### 容器日志
```bash
# FastAPI服务日志
docker logs fba_server
docker logs -f fba_server --tail 100

# Celery服务日志
docker logs fba_celery
docker logs -f fba_celery --tail 100

# 数据库日志
docker logs fba_postgres
docker logs fba_redis

# 查看特定时间范围的日志
docker logs fba_server --since "2025-08-30T10:00:00" --until "2025-08-30T11:00:00"
```

## 🔧 Supervisord进程管理日志

### 查看进程状态
```bash
# FastAPI服务进程状态
docker exec fba_server supervisorctl status

# Celery服务进程状态
docker exec fba_celery supervisorctl status
```

### 进程日志
```bash
# 查看FastAPI服务日志
docker exec fba_server supervisorctl tail fastapi_server
docker exec fba_server supervisorctl tail -f fastapi_server

# 查看Celery各组件日志
docker exec fba_celery supervisorctl tail celery_worker
docker exec fba_celery supervisorctl tail celery_beat
docker exec fba_celery supervisorctl tail celery_flower
```

### 进程控制
```bash
# 重启服务
docker exec fba_server supervisorctl restart fastapi_server
docker exec fba_celery supervisorctl restart celery_worker

# 停止/启动服务
docker exec fba_server supervisorctl stop fastapi_server
docker exec fba_server supervisorctl start fastapi_server
```

## 📊 Supervisord日志文件位置

### FastAPI服务
- **进程日志**: `/var/log/fastapi_server/fba_server.log`
- **主配置**: `/etc/supervisor/supervisord.conf`
- **服务配置**: `/etc/supervisor/conf.d/fastapi_server.conf`

```bash
# 查看日志文件
docker exec fba_server cat /var/log/fastapi_server/fba_server.log
docker exec fba_server tail -f /var/log/fastapi_server/fba_server.log
```

### Celery服务
- **Worker日志**: `/var/log/celery/fba_celery_worker.log`
- **Beat日志**: `/var/log/celery/fba_celery_beat.log`
- **Flower日志**: `/var/log/celery/fba_celery_flower.log`

```bash
# 查看Celery各组件日志
docker exec fba_celery cat /var/log/celery/fba_celery_worker.log
docker exec fba_celery cat /var/log/celery/fba_celery_beat.log
docker exec fba_celery cat /var/log/celery/fba_celery_flower.log
```

## 📝 应用程序日志

### 应用日志配置
- **日志目录**: `backend/log/`
- **访问日志**: `fba_access.log` / `fba_access_YYYY-MM-DD.log`
- **错误日志**: `fba_error.log` / `fba_error_YYYY-MM-DD.log`

### 查看应用日志
```bash
# 在宿主机上查看
tail -f backend/log/fba_access.log
tail -f backend/log/fba_error.log

# 在容器内查看
docker exec fba_server tail -f /fba/backend/log/fba_access.log
docker exec fba_server tail -f /fba/backend/log/fba_error.log

# 查看历史日志
docker exec fba_server ls -la /fba/backend/log/
docker exec fba_server cat /fba/backend/log/fba_access_2025-08-30.log
```

### 应用日志级别配置

在 `backend/core/conf.py` 中配置：
```python
LOG_STD_LEVEL: str = "INFO"           # 标准输出日志级别
LOG_FILE_ACCESS_LEVEL: str = "INFO"   # 访问日志级别
LOG_FILE_ERROR_LEVEL: str = "ERROR"   # 错误日志级别
```

## 🌐 Web服务器日志

### Granian服务器（当前使用）
配置文件：`deploy/backend/fastapi_server.conf`
```bash
# Granian进程日志已重定向到supervisord日志
docker exec fba_server supervisorctl tail fastapi_server
```

### Gunicorn配置（备用）
配置文件：`deploy/backend/gunicorn.conf.py`
- 访问日志：输出到标准输出 (`accesslog = '-'`)
- 错误日志：输出到标准输出 (`errorlog = '-'`)

## 🗄️ 数据库日志

### PostgreSQL日志
```bash
# 查看PostgreSQL日志
docker logs fba_postgres

# 检查数据库连接
docker exec fba_postgres pg_isready -U postgres -d fba

# 连接数据库查询
docker exec -it fba_postgres psql -U postgres -d fba
```

### Redis日志
```bash
# 查看Redis日志
docker logs fba_redis

# 检查Redis连接
docker exec fba_redis redis-cli ping

# 连接Redis查询
docker exec -it fba_redis redis-cli
```

## 📊 业务日志

### 操作日志
- **表名**: `sys_opera_log`
- **API**: `/api/v1/admin/log/opera`
- **服务**: `backend/app/admin/service/opera_log_service.py`

```bash
# 查看最近的操作日志
docker exec -it fba_postgres psql -U postgres -d fba -c "SELECT * FROM sys_opera_log ORDER BY created_time DESC LIMIT 10;"
```

### 登录日志
- **表名**: `sys_login_log`
- **API**: `/api/v1/admin/log/login`
- **服务**: `backend/app/admin/service/login_log_service.py`

```bash
# 查看最近的登录日志
docker exec -it fba_postgres psql -U postgres -d fba -c "SELECT * FROM sys_login_log ORDER BY created_time DESC LIMIT 10;"
```

### 分析报告日志
- **静态文件**: `backend/agents/static/analysis/`
- **报告日志表**: `ai_assistant_report_log`

```bash
# 查看分析报告文件
docker exec fba_server find /fba/backend/agents/static/analysis/ -name "*.md" | head -10
```

## 🚨 常见问题排查

### 1. 服务启动失败

**症状**：容器状态为Exited或Restarting
```bash
# 检查容器状态
docker ps -a | grep fba

# 查看启动日志
docker logs fba_server
docker logs fba_celery
```

**常见原因**：
- 端口占用：8000, 5432, 6379
- 环境变量配置错误
- 依赖服务未启动

### 2. API请求超时/失败

**检查步骤**：
```bash
# 1. 检查FastAPI服务状态
docker exec fba_server supervisorctl status fastapi_server

# 2. 查看API访问日志
docker exec fba_server tail -f /fba/backend/log/fba_access.log

# 3. 查看错误日志
docker exec fba_server tail -f /fba/backend/log/fba_error.log

# 4. 测试API健康检查
curl http://localhost:8000/api/v1/health
```

### 3. 数据库连接问题

**检查步骤**：
```bash
# 1. 检查PostgreSQL状态
docker exec fba_postgres pg_isready -U postgres -d fba

# 2. 检查数据库日志
docker logs fba_postgres --tail 50

# 3. 测试数据库连接
docker exec -it fba_postgres psql -U postgres -d fba -c "SELECT 1;"
```

### 4. Celery任务处理异常

**检查步骤**：
```bash
# 1. 检查Celery各组件状态
docker exec fba_celery supervisorctl status

# 2. 查看Worker日志
docker exec fba_celery tail -f /var/log/celery/fba_celery_worker.log

# 3. 查看Beat调度器日志
docker exec fba_celery tail -f /var/log/celery/fba_celery_beat.log

# 4. 访问Flower监控
curl http://localhost:8555/flower  # 用户名/密码: admin/123456
```

### 5. 内存/CPU使用过高

**检查步骤**：
```bash
# 查看容器资源使用
docker stats

# 查看系统资源
docker exec fba_server top
docker exec fba_server free -h
docker exec fba_server df -h

# 查看Python进程
docker exec fba_server ps aux | grep python
```

## 🔍 日志分析技巧

### 1. 过滤关键信息
```bash
# 查找错误信息
docker logs fba_server 2>&1 | grep -i error
docker exec fba_server grep -i "error\|exception" /fba/backend/log/fba_error.log

# 查找特定时间段日志
docker exec fba_server grep "2025-08-30 14:" /fba/backend/log/fba_access.log

# 查找特定用户操作
docker exec -it fba_postgres psql -U postgres -d fba -c "SELECT * FROM sys_opera_log WHERE username = 'admin' ORDER BY created_time DESC LIMIT 5;"
```

### 2. 实时监控
```bash
# 同时监控多个日志文件
docker exec fba_server tail -f /fba/backend/log/fba_access.log /fba/backend/log/fba_error.log

# 监控Celery任务处理
docker exec fba_celery supervisorctl tail -f celery_worker
```

### 3. 日志轮转清理
```bash
# 查看日志文件大小
docker exec fba_server du -sh /fba/backend/log/*
docker exec fba_server ls -lah /var/log/fastapi_server/
docker exec fba_celery ls -lah /var/log/celery/

# 清理旧日志（谨慎操作）
docker exec fba_server find /fba/backend/log/ -name "*.log" -mtime +7 -delete
```

## 🔧 健康检查脚本

使用项目内置的健康检查脚本：
```bash
# 运行完整健康检查
./scripts/deployment/health-check.sh

# 或直接调用API健康检查
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/health/detailed
```

## 📞 紧急处理流程

### 服务完全不可用
1. 检查Docker服务：`systemctl status docker`
2. 重启整个服务栈：`./jenkins-docker-deploy.sh`
3. 查看部署日志确认问题

### 部分功能异常
1. 查看具体错误日志定位问题
2. 重启对应的supervisord进程
3. 必要时重启单个容器：`docker restart fba_server`

### 数据一致性问题
1. 检查数据库连接和数据完整性
2. 查看相关操作日志追踪问题根源
3. 必要时进行数据恢复操作

---

## 📋 日志位置速查表

| 日志类型 | 位置 | 查看命令 |
|---------|------|---------|
| Docker容器日志 | Docker系统 | `docker logs <container_name>` |
| FastAPI进程日志 | `/var/log/fastapi_server/fba_server.log` | `docker exec fba_server tail -f /var/log/fastapi_server/fba_server.log` |
| Celery Worker日志 | `/var/log/celery/fba_celery_worker.log` | `docker exec fba_celery tail -f /var/log/celery/fba_celery_worker.log` |
| Celery Beat日志 | `/var/log/celery/fba_celery_beat.log` | `docker exec fba_celery tail -f /var/log/celery/fba_celery_beat.log` |
| Celery Flower日志 | `/var/log/celery/fba_celery_flower.log` | `docker exec fba_celery tail -f /var/log/celery/fba_celery_flower.log` |
| 应用访问日志 | `/fba/backend/log/fba_access.log` | `docker exec fba_server tail -f /fba/backend/log/fba_access.log` |
| 应用错误日志 | `/fba/backend/log/fba_error.log` | `docker exec fba_server tail -f /fba/backend/log/fba_error.log` |
| PostgreSQL日志 | Docker日志 | `docker logs fba_postgres` |
| Redis日志 | Docker日志 | `docker logs fba_redis` |
| 分析报告文件 | `/fba/backend/agents/static/analysis/` | `docker exec fba_server find /fba/backend/agents/static/analysis/ -name "*.md"` |

---

> **提示**：建议定期检查日志文件大小，避免磁盘空间不足。可以设置日志轮转策略或定期清理旧日志文件。
