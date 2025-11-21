#!/bin/bash

# Jenkins Docker 部署脚本 - Max AI Backend
# 简洁但完整的生产环境部署脚本

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}🚀 Max AI Backend - Jenkins 部署${NC}"
echo -e "${BLUE}======================================${NC}"

# 配置变量
PROJECT_NAME="max-ai-backend"
IMAGE_TAG="${BUILD_NUMBER:-latest}"
SERVICES=("fba_postgres" "fba_redis" "fba_celery" "fba_server")
HEALTH_CHECK_URL="http://localhost:8000/api/v1/health"

# 检测Docker Compose命令
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
else
    echo -e "${RED}❌ 错误: 未找到docker-compose或docker compose命令${NC}"
    exit 1
fi

# 通用检查函数
check_service() {
    local service_name="$1"
    local check_command="$2"
    local success_msg="$3"
    local error_msg="$4"

    if eval "$check_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ ${success_msg}${NC}"
        return 0
    else
        echo -e "${RED}❌ ${error_msg}${NC}"
        return 1
    fi
}

# 重试执行函数
retry_command() {
    local max_attempts="$1"
    local delay="$2"
    local description="$3"
    shift 3
    local command="$@"

    for i in $(seq 1 $max_attempts); do
        echo -e "${BLUE}🔍 ${description} ($i/$max_attempts)...${NC}"
        if eval "$command"; then
            echo -e "${GREEN}✅ ${description}成功${NC}"
            return 0
        elif [ $i -eq $max_attempts ]; then
            echo -e "${RED}❌ ${description}失败${NC}"
            return 1
        else
            echo -e "${YELLOW}⏳ 第${i}次尝试失败，等待${delay}秒后重试...${NC}"
            sleep $delay
        fi
    done
}

echo -e "${BLUE}📋 使用命令: $COMPOSE_CMD${NC}"
echo -e "${BLUE}📋 项目: $PROJECT_NAME${NC}"
echo -e "${BLUE}📋 服务数量: ${#SERVICES[@]}${NC}"

# 1. 环境检查
echo ""
echo -e "${BLUE}1️⃣ 环境检查...${NC}"
check_service "Dockerfile" "[ -f Dockerfile ]" "Dockerfile存在" "未找到Dockerfile" || exit 1
check_service "docker-compose.yml" "[ -f docker-compose.yml ]" "docker-compose.yml存在" "未找到docker-compose.yml" || exit 1
echo -e "${GREEN}✅ 环境检查通过${NC}"

# 2. 创建Docker资源
echo ""
echo -e "${BLUE}2️⃣ 创建Docker资源...${NC}"

# 创建网络和卷
NETWORK_NAME="fba_network"
VOLUMES=("fba_postgres" "fba_redis" "fba_static" "fba_static_upload")

if ! docker network ls | grep -q $NETWORK_NAME; then
    docker network create $NETWORK_NAME
    echo -e "${GREEN}✅ 创建网络: $NETWORK_NAME${NC}"
fi

for volume in "${VOLUMES[@]}"; do
    if ! docker volume ls | grep -q $volume; then
        docker volume create $volume
        echo -e "${GREEN}✅ 创建卷: $volume${NC}"
    fi
done

# 3. 构建和启动服务
echo ""
echo -e "${BLUE}3️⃣ 构建和启动服务...${NC}"

# 构建镜像
echo -e "${BLUE}🔨 构建镜像...${NC}"
BUILD_NUMBER=${BUILD_NUMBER} $COMPOSE_CMD build

# 启动服务
echo -e "${BLUE}🚀 启动服务...${NC}"
$COMPOSE_CMD up -d

# 等待服务启动
echo -e "${BLUE}⏳ 等待服务启动...${NC}"
sleep 15

# 4. 数据库迁移检查
echo ""
echo -e "${BLUE}4️⃣ 数据库迁移检查...${NC}"

# 检查迁移状态
MIGRATION_OUTPUT=$(docker exec fba_server bash -c "cd /fba && alembic current" 2>&1)
CURRENT_MIGRATION=$(echo "$MIGRATION_OUTPUT" | grep -E '^[a-f0-9]+' | head -1)

if [ ! -z "$CURRENT_MIGRATION" ]; then
    echo -e "${GREEN}✅ 当前数据库版本: $CURRENT_MIGRATION${NC}"
else
    echo -e "${RED}❌ 无法检查数据库迁移状态${NC}"
    docker logs fba_server --tail 20
    exit 1
fi

# 5. 健康检查
echo ""
echo -e "${BLUE}5️⃣ 健康检查...${NC}"

# 检查容器状态
FAILED_SERVICES=()
for service in "${SERVICES[@]}"; do
    if docker ps | grep -q $service; then
        echo -e "${GREEN}✅ $service: 运行中${NC}"
    else
        echo -e "${RED}❌ $service: 未运行${NC}"
        FAILED_SERVICES+=($service)
    fi
done

if [ ${#FAILED_SERVICES[@]} -gt 0 ]; then
    echo -e "${RED}❌ 以下服务启动失败: ${FAILED_SERVICES[*]}${NC}"
    for service in "${FAILED_SERVICES[@]}"; do
        echo -e "${BLUE}🔍 $service 日志:${NC}"
        docker logs $service --tail 20 || true
    done
    exit 1
fi

# FastAPI健康检查
if ! retry_command 5 5 "FastAPI健康检查" "curl -f -s $HEALTH_CHECK_URL > /dev/null 2>&1"; then
    echo -e "${BLUE}🔍 fba_server 日志:${NC}"
    docker logs fba_server --tail 30
    exit 1
fi

# Celery服务检查
echo -e "${BLUE}🩺 Celery服务检查...${NC}"

# 清理Redis Celery数据
docker exec fba_redis redis-cli -n ${CELERY_BROKER_REDIS_DATABASE:-1} FLUSHDB > /dev/null 2>&1 || true
echo -e "${GREEN}✅ Redis Celery数据清理完成${NC}"

# 等待Celery Worker启动
echo -e "${BLUE}⏳ 等待Celery Worker启动...${NC}"
sleep 15

# 检查supervisor服务状态
echo -e "${BLUE}📊 检查Supervisor服务状态...${NC}"
docker exec fba_celery supervisorctl status

# 检查Celery Worker进程状态（主要检查）
echo -e "${BLUE}🔍 检查Celery Worker进程状态...${NC}"
if ! retry_command 3 5 "Celery Worker进程检查" "docker exec fba_celery supervisorctl status celery_worker | grep -q RUNNING"; then
    echo -e "${BLUE}🔍 Celery诊断信息:${NC}"

    # 检查supervisor状态
    echo -e "${BLUE}📊 Supervisor状态:${NC}"
    docker exec fba_celery supervisorctl status || true

    # 检查进程信息
    echo -e "${BLUE}🔍 Celery进程信息:${NC}"
    docker exec fba_celery pgrep -fl celery || echo "未找到Celery进程"

    # 检查应用日志
    echo -e "${BLUE}📋 应用日志:${NC}"
    if docker exec fba_celery test -f /fba/logs/celery_app.log; then
        docker exec fba_celery tail -20 /fba/logs/celery_app.log
    else
        echo "celery_app.log 不存在"
    fi
        docker exec fba_celery ls -la /var/log/supervisor/ 2>/dev/null || true
    fi

# 6. 清理和完成
echo ""
echo -e "${BLUE}6️⃣ 清理和完成...${NC}"

# 清理Docker资源
echo -e "${BLUE}🧹 清理Docker资源...${NC}"

# 清理旧的项目镜像（保留最近3个版本）
echo -e "${BLUE}🗑️ 清理旧的项目镜像...${NC}"
OLD_IMAGES=$(docker images --filter "reference=${PROJECT_NAME}*" --format "table {{.Repository}}:{{.Tag}}\t{{.CreatedAt}}" | tail -n +2 | sort -k2 -r | tail -n +4 | awk '{print $1}' | tr '\n' ' ')
if [ ! -z "$OLD_IMAGES" ]; then
    echo -e "${YELLOW}删除旧镜像: $OLD_IMAGES${NC}"
    echo "$OLD_IMAGES" | xargs -r docker rmi -f > /dev/null 2>&1 || true
    echo -e "${GREEN}✅ 旧镜像清理完成${NC}"
else
    echo -e "${GREEN}✅ 没有需要清理的旧镜像${NC}"
fi

# 清理悬空镜像和容器
docker image prune -f > /dev/null 2>&1 || true
docker container prune -f > /dev/null 2>&1 || true
docker builder prune -f --filter until=48h > /dev/null 2>&1 || true

# 显示部署结果
echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}🎉 部署完成！${NC}"
echo -e "${GREEN}======================================${NC}"
echo -e "${BLUE}📅 部署时间: $(date)${NC}"
echo -e "${BLUE}🏷️ 项目: $PROJECT_NAME${NC}"
echo ""
echo -e "${BLUE}📊 服务状态:${NC}"
$COMPOSE_CMD ps
echo ""
echo -e "${BLUE}🌐 服务地址:${NC}"
echo "  API服务: http://localhost:8000"
echo "  API文档: http://localhost:8000/docs"
echo "  健康检查: $HEALTH_CHECK_URL"
echo "  Celery监控: http://localhost:8555/flower/"
echo ""
echo -e "${BLUE}🔧 管理命令:${NC}"
echo "  查看日志: $COMPOSE_CMD logs -f"
echo "  健康检查: ./scripts/deployment/health-check.sh"
echo "  停止服务: $COMPOSE_CMD down"
echo -e "${GREEN}======================================${NC}"

exit 0
