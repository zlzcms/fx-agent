#!/usr/bin/env bash
# Docker生产环境Celery服务启动脚本
# 在Docker容器中启动Celery服务（使用supervisor管理）

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

# 启动服务
start_service() {
    echo -e "${GREEN}🚀 启动Celery服务...${NC}"

    # 等待核心服务
    wait_for_core_services

    # 启动supervisor
    exec supervisord -c /fba/scripts/deployment/config/supervisord.conf -n
}

# 主流程
echo -e "${BLUE}🌟 启动生产环境Celery服务...${NC}"

# 启动服务
start_service
