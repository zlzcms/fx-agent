# 脚本目录说明

本目录包含了项目的各种管理和部署脚本，按功能分类组织。

## 目录结构

### 🚀 根目录脚本
- `run.sh` - 统一脚本入口点，提供简化的脚本调用方式

### 🛠️ dev/ - 开发环境脚本
- `start.sh` - 开发环境FastAPI服务启动脚本
- `install-git-hooks.sh` - Git Hooks安装管理脚本
- `pre-commit.sh` - Git提交前代码检查脚本
- `pre-commit-db-migration.py` - 数据库迁移检查脚本
- `pre-commit-fix-sequences.py` - 序列修复检查脚本

### 🚀 deployment/ - Docker生产环境脚本
- `start.sh` - Docker FastAPI服务启动脚本
- `celery.sh` - Docker Celery服务启动脚本
- `config/` - Docker部署配置文件目录
  - `gunicorn.conf.py` - Gunicorn配置
  - `supervisord.conf` - Supervisor进程管理配置
  - `nginx.conf` - Nginx配置
  - `celery.conf` - Celery Supervisor配置
  - `fastapi_server.conf` - FastAPI Server Supervisor配置
- `health-check.sh` - 生产环境健康检查脚本

### 🗄️ database/ - 数据库相关脚本
- `init-database.sh` - 数据库初始化脚本
- `run-migrations.sh` - Alembic数据库迁移脚本
- `fix-sequences.sh` - PostgreSQL序列修复脚本
- `sys_menu_sync.sql` - 系统菜单数据同步SQL

## 使用方法

### 🎯 推荐方式：统一入口点
```bash
# 使用统一脚本管理工具（推荐）
./scripts/run.sh <命令>

# 查看所有可用命令
./scripts/run.sh help

# 常用命令示例
./scripts/run.sh dev                # 启动开发环境
./scripts/run.sh db:init            # 初始化数据库
./scripts/run.sh hooks:install      # 安装Git Hooks
./scripts/run.sh health             # 健康检查
```

### 🚀 服务启动
```bash
# 启动开发环境
./scripts/run.sh dev
# 或直接调用: ./scripts/dev/start.sh

# 启动Docker FastAPI服务（生产环境）
./scripts/run.sh server
# 或直接调用: ./scripts/deployment/start.sh

# 启动Docker Celery服务（生产环境）
./scripts/run.sh celery
# 或直接调用: ./scripts/deployment/celery.sh
```

### 🗄️ 数据库管理
```bash
# 初始化数据库
./scripts/run.sh db:init
# 或直接调用: ./scripts/database/init-database.sh

# 执行数据库迁移
./scripts/run.sh db:migrate
# 或直接调用: ./scripts/database/run-migrations.sh

# 修复序列问题
./scripts/run.sh db:fix-sequences
# 或直接调用: ./scripts/database/fix-sequences.sh
```

### 🛠️ 开发工具
```bash
# 安装Git Hooks
./scripts/run.sh hooks:install
# 或直接调用: ./scripts/development/install-git-hooks.sh

# 检查Git Hooks状态
./scripts/run.sh hooks:check
# 或直接调用: ./scripts/development/install-git-hooks.sh --check


```

### 🚀 部署监控
```bash
# 生产环境健康检查
./scripts/run.sh health
# 或直接调用: ./scripts/deployment/health-check.sh
```

## 注意事项

1. **执行位置**：所有脚本都需要在项目根目录下执行
2. **执行权限**：确保脚本有执行权限：`chmod +x scripts/**/*.sh`
3. **环境依赖**：
   - 服务启动脚本需要Docker环境
   - 数据库脚本需要PostgreSQL容器运行
   - 开发脚本需要Python环境和相关依赖
4. **Git Hooks**：首次使用需要运行 `./scripts/development/install-git-hooks.sh` 安装
5. **数据库迁移**：修改数据模型后需要生成并执行迁移脚本
