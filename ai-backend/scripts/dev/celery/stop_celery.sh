#!/usr/bin/env bash
# 开发环境Celery服务停止脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 停止celery服务
stop_celery() {
    echo -e "${BLUE}🛑 停止Celery服务...${NC}"

    local stopped_any=false

    # 停止worker进程
    if pkill -f "celery.*worker" 2>/dev/null; then
        echo -e "${YELLOW}  停止 celery_worker${NC}"
        stopped_any=true
    fi

    # 停止beat进程
    if pkill -f "celery.*beat" 2>/dev/null; then
        echo -e "${YELLOW}  停止 celery_beat${NC}"
        stopped_any=true
    fi

    # 停止flower进程
    if pkill -f "celery.*flower" 2>/dev/null; then
        echo -e "${YELLOW}  停止 celery_flower${NC}"
        stopped_any=true
    fi

    # 等待进程停止
    if [ "$stopped_any" = true ]; then
        echo -e "${YELLOW}  等待进程停止...${NC}"
        sleep 3

        # 检查是否还有进程在运行，如果有则强制停止
        if pgrep -f "celery.*(worker|beat|flower)" >/dev/null 2>&1; then
            echo -e "${YELLOW}  强制停止剩余进程${NC}"
            pkill -9 -f "celery.*worker" 2>/dev/null || true
            pkill -9 -f "celery.*beat" 2>/dev/null || true
            pkill -9 -f "celery.*flower" 2>/dev/null || true
        fi

        echo -e "${GREEN}✅ Celery服务已停止${NC}"
    else
        echo -e "${BLUE}ℹ️  没有运行中的Celery服务${NC}"
    fi
}

# 显示状态
show_status() {
    echo -e "\n${BLUE}📊 检查Celery进程状态:${NC}"

    local running_processes=$(ps aux | grep -E "celery.*(worker|beat|flower)" | grep -v grep | wc -l)

    if [ "$running_processes" -eq 0 ]; then
        echo -e "${GREEN}  ✅ 没有运行中的Celery进程${NC}"
    else
        echo -e "${YELLOW}  ⚠️  仍有 $running_processes 个Celery进程在运行:${NC}"
        ps aux | grep -E "celery.*(worker|beat|flower)" | grep -v grep | while read line; do
            echo -e "${YELLOW}    $line${NC}"
        done
        echo -e "\n${YELLOW}  如需强制停止所有进程，请运行:${NC}"
        echo -e "${YELLOW}    pkill -9 -f celery${NC}"
    fi
}

# 主函数
main() {
    echo -e "${BLUE}🌟 停止开发环境Celery服务...${NC}"

    # 停止服务
    stop_celery

    # 显示状态
    show_status

    echo -e "\n${GREEN}🎉 操作完成！${NC}"
}

# 如果直接运行此脚本
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
