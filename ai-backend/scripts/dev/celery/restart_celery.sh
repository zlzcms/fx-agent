#!/usr/bin/env bash
# 开发环境Celery服务重启脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 主函数
main() {
    echo -e "${BLUE}🔄 重启开发环境Celery服务...${NC}"

    # 停止服务
    echo -e "${YELLOW}第一步: 停止现有服务${NC}"
    "$SCRIPT_DIR/stop_celery.sh"

    # 等待一下确保进程完全停止
    echo -e "${YELLOW}等待进程完全停止...${NC}"
    sleep 3

    # 清理Redis中的Celery相关缓存
    echo -e "${YELLOW}第二步: 清理Redis缓存${NC}"
    echo -e "清理Celery队列和任务状态..."

    # 检查Redis容器是否运行
    if docker ps --format "table {{.Names}}" | grep -q "fba_redis"; then
        # 使用Docker exec执行Redis清理
        if docker exec fba_redis redis-cli -n ${CELERY_BROKER_REDIS_DATABASE:-1} FLUSHDB > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Redis缓存清理完成${NC}"
        else
            echo -e "${RED}❌ Redis缓存清理失败${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Redis容器未运行，跳过缓存清理${NC}"
    fi

    # 启动服务
    echo -e "\n${YELLOW}第三步: 启动服务${NC}"
    "$SCRIPT_DIR/start_celery.sh"

    echo -e "\n${GREEN}🎉 Celery服务重启完成！${NC}"
}

# 如果直接运行此脚本
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
