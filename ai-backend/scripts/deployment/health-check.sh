#!/bin/bash

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# 检查函数
check_service() {
    local service_name="$1"
    local check_command="$2"
    local success_msg="$3"
    local error_msg="$4"

    echo -e "${BLUE}🔍 检查${service_name}...${NC}"
    if eval "$check_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ ${success_msg}${NC}"
        return 0
    else
        echo -e "${RED}❌ ${error_msg}${NC}"
        return 1
    fi
}

echo -e "${BLUE}🔍 开始生产环境健康检查...${NC}"

# 检查Docker服务状态
echo -e "${BLUE}📊 检查Docker服务状态...${NC}"
docker-compose -f docker-compose.yml ps

# 定义检查项
CHECKS=(
    "PostgreSQL连接|docker exec fba_postgres pg_isready -U postgres -d fba|PostgreSQL连接正常|PostgreSQL连接失败"
    "Redis连接|docker exec fba_redis redis-cli ping|Redis连接正常|Redis连接失败"
    "FastAPI服务|curl -f http://localhost:8000/api/v1/health|FastAPI服务正常|FastAPI服务异常"
    "Celery监控|curl -f -u admin:123456 http://localhost:8555/flower/|Celery监控正常|Celery监控异常"
    "Celery Supervisor|docker exec fba_celery supervisorctl status celery_worker | grep -q RUNNING|Celery Worker进程正常|Celery Worker进程异常"
)

# 执行检查
failed_checks=0
for check in "${CHECKS[@]}"; do
    IFS='|' read -r name command success_msg error_msg <<< "$check"
    if ! check_service "$name" "$command" "$success_msg" "$error_msg"; then
        failed_checks=$((failed_checks + 1))

        # 特殊处理：Celery Supervisor失败时显示详细信息
        if [[ "$name" == "Celery Supervisor" ]]; then
            echo -e "${BLUE}🔍 Supervisor状态详情:${NC}"
            docker exec fba_celery supervisorctl status || true

            echo -e "${BLUE}🔍 Celery进程信息:${NC}"
            docker exec fba_celery pgrep -fl celery || echo "未找到Celery进程"

            echo -e "${BLUE}🔍 Celery应用日志:${NC}"
            if docker exec fba_celery test -f /fba/logs/celery_app.log; then
                docker exec fba_celery tail -10 /fba/logs/celery_app.log
            else
                echo "celery_app.log 不存在"
            fi
        fi
    fi
done

# 显示容器资源使用情况
echo -e "${BLUE}📊 检查容器资源使用情况...${NC}"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# 结果汇总
echo ""
if [ $failed_checks -eq 0 ]; then
    echo -e "${GREEN}🎉 健康检查完成！所有服务运行正常${NC}"
    echo ""
    echo -e "${BLUE}📋 查看详细日志：${NC}"
    echo "   docker-compose -f docker-compose.yml logs -f"
    echo ""
    echo -e "${BLUE}📊 查看资源使用：${NC}"
    echo "   docker stats"
    exit 0
else
    echo -e "${RED}❌ 健康检查失败！${failed_checks} 个服务异常${NC}"
    exit 1
fi
