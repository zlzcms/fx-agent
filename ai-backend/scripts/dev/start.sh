#!/usr/bin/env bash
# 本地开发环境启动脚本
# 在本地开发环境中启动FastAPI服务

set -e

# 初始化变量
SKIP_MIGRATION=false

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 未找到Python3环境${NC}"
    exit 1
fi

# 检查虚拟环境
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  建议在虚拟环境中运行${NC}"
fi

# 激活虚拟环境（如果存在）
if [ -f "$PROJECT_ROOT/.venv/bin/activate" ]; then
    echo -e "${BLUE}🔧 激活虚拟环境...${NC}"
    source "$PROJECT_ROOT/.venv/bin/activate"
fi

# 安装依赖
echo -e "${BLUE}📦 检查并安装依赖...${NC}"
cd "$PROJECT_ROOT"
if command -v uv &> /dev/null; then
    uv sync
else
    pip install -e .
fi

# 加载环境变量
if [ -f "$PROJECT_ROOT/backend/.env" ]; then
    echo -e "${BLUE}📝 加载环境变量...${NC}"
    # 使用更安全的方式加载环境变量
    while IFS='=' read -r key value; do
        # 跳过注释和空行
        [[ $key =~ ^[[:space:]]*# ]] && continue
        [[ -z $key ]] && continue

        # 移除键值两端的空格
        key=$(echo "$key" | xargs)
        value=$(echo "$value" | xargs)

        # 导出环境变量
        export "$key=$value"
    done < "$PROJECT_ROOT/backend/.env"
else
    echo -e "${YELLOW}⚠️  未找到.env文件，将使用默认配置${NC}"
fi

# 等待服务启动函数
wait_for_service() {
    local service_name="$1"
    local host_port="$2"
    local timeout="${3:-30}"

    echo -e "${YELLOW}⏳ 等待 ${service_name} 服务...${NC}"

    # 使用Python内置的socket模块检查服务
    python3 -c "
import socket
import sys
import time

host, port = '$host_port'.split(':')
timeout = int('$timeout')

start_time = time.time()
while time.time() - start_time < timeout:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            s.connect((host, int(port)))
        print('✅ $service_name 服务已就绪')
        sys.exit(0)
    except (ConnectionRefusedError, socket.timeout, socket.gaierror):
        time.sleep(1)
        continue

print('❌ $service_name 服务启动超时')
sys.exit(1)
" || {
        echo -e "${RED}❌ ${service_name} 服务启动超时${NC}"
        return 1
    }
}

# 等待核心服务
wait_for_core_services() {
    echo -e "${BLUE}🔍 检查核心服务...${NC}"

    # 检查PostgreSQL
    if [ -n "$DATABASE_HOST" ] && [ -n "$DATABASE_PORT" ]; then
        wait_for_service "PostgreSQL" "$DATABASE_HOST:$DATABASE_PORT" 30 || {
            echo -e "${YELLOW}⚠️  PostgreSQL服务不可用，将跳过数据库迁移${NC}"
            SKIP_MIGRATION=true
        }
    else
        echo -e "${YELLOW}⚠️  未配置PostgreSQL，跳过检查${NC}"
        SKIP_MIGRATION=true
    fi

    # 检查Redis
    if [ -n "$REDIS_HOST" ] && [ -n "$REDIS_PORT" ]; then
        wait_for_service "Redis" "$REDIS_HOST:$REDIS_PORT" 30 || {
            echo -e "${YELLOW}⚠️  Redis服务不可用，但可以继续启动服务${NC}"
        }
    else
        echo -e "${YELLOW}⚠️  未配置Redis，跳过检查${NC}"
    fi
}

# 执行数据库迁移
run_migrations() {
    if [ "$SKIP_MIGRATION" = "true" ]; then
        echo -e "${YELLOW}⚠️  跳过数据库迁移${NC}"
        return 0
    fi

    echo -e "${BLUE}🔄 执行数据库迁移...${NC}"
    cd "$PROJECT_ROOT"

    # 设置PYTHONPATH以包含项目根目录
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

    if command -v alembic &> /dev/null; then
        if alembic upgrade heads; then
            echo -e "${GREEN}✅ 数据库迁移完成${NC}"
        else
            echo -e "${YELLOW}⚠️  数据库迁移失败，但可以继续启动服务${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  未找到alembic，跳过数据库迁移${NC}"
    fi
}

# 启动FastAPI服务
start_fastapi() {
    echo -e "${GREEN}🚀 启动FastAPI服务...${NC}"
    cd "$PROJECT_ROOT/backend"

    # 设置PYTHONPATH以包含项目根目录
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

    # 使用uvicorn启动服务
    if command -v uvicorn &> /dev/null; then
        exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    else
        echo -e "${RED}❌ 未找到uvicorn${NC}"
        exit 1
    fi
}

# 主流程
echo -e "${BLUE}🌟 启动本地开发服务...${NC}"

# 等待核心服务
wait_for_core_services

# 执行数据库迁移
run_migrations

# 启动服务
start_fastapi
