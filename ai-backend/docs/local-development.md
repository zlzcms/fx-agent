# 本地开发环境搭建指南

本指南帮助新开发人员在本地不使用Docker的情况下搭建开发环境。

## 📋 前置要求

- Python 3.10+
- PostgreSQL 16
- Redis
- [uv](https://docs.astral.sh/uv/) (Python包管理工具)

## 🚀 快速开始

### 1. 准备依赖服务

你有两种选择来运行PostgreSQL和Redis：

#### 选择1：本地安装（推荐用于长期开发）
```bash
# macOS (使用Homebrew)
brew install postgresql@16 redis
brew services start postgresql@16
brew services start redis

# Ubuntu/Debian
sudo apt install postgresql-16 redis-server
sudo systemctl start postgresql
sudo systemctl start redis-server
```

#### 选择2：使用Docker只启动数据库服务
```bash
# 启动PostgreSQL
docker run -d --name fba_postgres \
  -p 5432:5432 \
  -e POSTGRES_DB=fba \
  -e POSTGRES_PASSWORD=123456 \
  -e TZ=Asia/Shanghai \
  postgres:16

# 启动Redis
docker run -d --name fba_redis \
  -p 6379:6379 \
  -e TZ=Asia/Shanghai \
  redis:latest
```

### 2. 配置Python环境

```bash
# 安装依赖
uv sync

# 激活虚拟环境
source .venv/bin/activate
```

### 3. 配置环境变量

确保 `backend/.env.local` 文件存在且配置正确：
```bash
# 检查配置文件
cat backend/.env.local
```

关键配置项：
- `DATABASE_HOST='127.0.0.1'`
- `DATABASE_PORT=5432`
- `REDIS_HOST='127.0.0.1'`
- `REDIS_PORT=6379`

### 4. 初始化数据库

```bash
# 执行数据库迁移
bash scripts/database/run-migrations.sh
```

### 5. 启动服务

#### 方式1：使用run.py启动（推荐）
```bash
# 在项目根目录执行
cd backend
python run.py
```

#### 方式2：使用uvicorn直接启动
```bash
# 在项目根目录执行
PYTHONPATH=. uv run uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### 6. 启动Celery任务队列（可选）

如果需要异步任务功能，在新终端中启动Celery：

```bash
# 方式1：使用现有脚本
cd backend
bash scripts/celery-start.sh

# 方式2：手动启动各组件
# Worker进程
celery -A backend.task.celery worker -l info -P gevent -c 100

# Beat调度器（新终端）
celery -A backend.task.celery beat -l info

# Flower监控（新终端）
celery -A backend.task.celery flower --port=8555 --basic-auth=admin:123456
```

## 🌐 服务访问地址

启动成功后，可以访问以下地址：

- **FastAPI服务**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **Celery监控**: http://localhost:8555 (用户名/密码: admin/123456)

## 🔧 开发工具

### 代码检查和格式化
```bash
# 运行pre-commit检查
pre-commit run --all-files

# 或使用开发脚本
bash scripts/development/pre-commit.sh
```

### 数据库操作
```bash
# 查看当前迁移状态
alembic current

# 创建新迁移
alembic revision --autogenerate -m "描述"

# 应用迁移
alembic upgrade head
```

## 🚨 常见问题

### 1. 端口冲突
如果8000端口被占用，修改run.py中的端口：
```python
uvicorn.run(
    app="backend.main:app",
    host="127.0.0.1",
    port=8001,  # 修改为其他端口
    reload=True,
)
```

### 2. 数据库连接失败
检查PostgreSQL是否启动：
```bash
# 检查PostgreSQL状态
pg_isready -h 127.0.0.1 -p 5432

# 或者测试连接
psql -h 127.0.0.1 -p 5432 -U postgres -d fba
```

### 3. Redis连接失败
检查Redis是否启动：
```bash
# 检查Redis状态
redis-cli ping
```

### 4. 依赖安装问题
```bash
# 重新安装依赖
uv sync --reinstall

# 检查Python版本
python --version  # 需要 3.10+
```

## 🔄 开发流程

1. **启动服务**：按照上述步骤启动FastAPI和Celery
2. **代码修改**：修改代码后自动重载（--reload模式）
3. **测试API**：访问 http://localhost:8000/docs 测试接口
4. **查看日志**：直接在终端查看实时日志
5. **提交代码**：使用pre-commit确保代码质量

## 📞 获取帮助

如遇到问题：
1. 检查所有服务是否正常启动
2. 查看终端错误日志
3. 验证环境变量配置
4. 确认数据库和Redis连接状态

---

> **提示**: 如果你更倾向于使用Docker开发，可以直接使用根目录的 `jenkins-docker-deploy.sh` 脚本，它会自动处理所有服务的启动和配置。
