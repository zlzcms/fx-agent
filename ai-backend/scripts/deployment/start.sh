#!/usr/bin/env bash
# Docker生产环境服务启动脚本
# 在Docker容器中启动FastAPI服务（使用supervisor管理）

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 等待服务启动函数
wait_for_service() {
    local service_name="$1"
    local host_port="$2"
    local timeout="${3:-30}"

    echo -e "${YELLOW}⏳ 等待 ${service_name} 服务...${NC}"

    if command -v python >/dev/null 2>&1; then
        python -m wait_for_it -s "$host_port" -t "$timeout"
    else
        local count=0
        while [ $count -lt $timeout ]; do
            if nc -z ${host_port/:/ } 2>/dev/null; then
                echo -e "${GREEN}✅ ${service_name} 服务已就绪${NC}"
                return 0
            fi
            sleep 1
            count=$((count + 1))
        done
        echo -e "${RED}❌ ${service_name} 服务启动超时${NC}"
        exit 1
    fi
}

# 等待核心服务
wait_for_core_services() {
    echo -e "${BLUE}🔍 检查核心服务...${NC}"
    wait_for_service "PostgreSQL" "fba_postgres:5432" 30
    wait_for_service "Redis" "fba_redis:6379" 30
}

# 执行数据库迁移
run_migrations() {
    echo -e "${BLUE}🔄 执行数据库迁移...${NC}"
    cd /fba

    if command -v alembic &> /dev/null; then
        # 获取当前数据库版本
        CURRENT_VERSION=$(alembic current 2>/dev/null | grep -E '^[a-f0-9]+' | head -1)
        if [ -z "$CURRENT_VERSION" ]; then
            CURRENT_VERSION="(empty database)"
        fi
        echo -e "${BLUE}📊 当前数据库版本: ${CURRENT_VERSION}${NC}"

        # 获取目标版本
        TARGET_VERSION=$(alembic heads 2>/dev/null | grep -E '^[a-f0-9]+' | head -1)
        if [ -z "$TARGET_VERSION" ]; then
            TARGET_VERSION="(no migrations)"
        fi
        echo -e "${BLUE}🎯 目标数据库版本: ${TARGET_VERSION}${NC}"

        # 执行迁移
        if [ "$CURRENT_VERSION" = "$TARGET_VERSION" ]; then
            echo -e "${GREEN}✅ 数据库已是最新版本，无需迁移${NC}"
        else
            echo -e "${BLUE}🔄 开始执行数据库迁移: ${CURRENT_VERSION} → ${TARGET_VERSION}${NC}"
            if alembic upgrade head; then
                echo -e "${GREEN}✅ 数据库迁移成功完成${NC}"
            else
                echo -e "${RED}❌ 数据库迁移失败${NC}"
                exit 1
            fi
        fi
    else
        echo -e "${YELLOW}⚠️  未找到alembic，跳过数据库迁移${NC}"
    fi
}

# 启动服务
start_service() {
    echo -e "${GREEN}🚀 启动FastAPI服务...${NC}"

    # 等待核心服务
    wait_for_core_services

    # 执行数据库迁移
    run_migrations

    # 启动supervisor
    exec supervisord -c /fba/scripts/deployment/config/supervisord.conf -n
}

# 主流程
echo -e "${BLUE}🌟 启动生产环境服务...${NC}"

# 启动服务
start_service
