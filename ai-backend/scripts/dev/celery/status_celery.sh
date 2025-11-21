#!/usr/bin/env bash
# 开发环境Celery服务状态检查脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs/celery"

# 检查服务状态
check_status() {
    echo -e "${BLUE}📊 Celery 服务状态检查${NC}"
    echo -e "${BLUE}================================${NC}"

    # 检查各个服务
    local services=("worker" "beat" "flower")
    local all_running=true

    for service in "${services[@]}"; do
        echo -e "\n${BLUE}🔍 检查 celery_${service}:${NC}"

        # 查找对应的进程
        local processes=$(ps aux | grep "celery.*${service}" | grep -v grep | grep -v "$(basename "$0")")

        if [[ -n "$processes" ]]; then
            echo -e "  ${GREEN}✅ 状态: 运行中${NC}"

            # 显示进程信息
            echo "$processes" | while IFS= read -r line; do
                local pid=$(echo "$line" | awk '{print $2}')
                local cpu=$(echo "$line" | awk '{print $3}')
                local mem=$(echo "$line" | awk '{print $4}')
                echo -e "  ${BLUE}📋 PID: $pid, CPU: ${cpu}%, MEM: ${mem}%${NC}"
            done

            # 显示日志文件大小
            local log_file="$LOG_DIR/${service}.log"
            if [[ -f "$log_file" ]]; then
                local log_size=$(du -h "$log_file" 2>/dev/null | cut -f1)
                echo -e "  ${BLUE}📝 日志大小: $log_size${NC}"
                echo -e "  ${BLUE}📄 日志文件: $log_file${NC}"
            fi
        else
            echo -e "  ${RED}❌ 状态: 未运行${NC}"
            all_running=false
        fi
    done

    # 总体状态
    echo -e "\n${BLUE}📈 总体状态:${NC}"
    if [ "$all_running" = true ]; then
        echo -e "  ${GREEN}✅ 所有服务正常运行${NC}"
    else
        echo -e "  ${RED}❌ 部分服务未运行${NC}"
    fi

    # 显示Flower访问信息
    local flower_processes=$(ps aux | grep "celery.*flower" | grep -v grep)
    if [[ -n "$flower_processes" ]]; then
        echo -e "\n${BLUE}🌸 Flower监控面板:${NC}"
        echo -e "  ${GREEN}🌐 访问地址: http://localhost:8555${NC}"
        echo -e "  ${GREEN}👤 用户名: admin${NC}"
        echo -e "  ${GREEN}🔑 密码: 123456${NC}"
    fi

    # 显示管理命令
    echo -e "\n${BLUE}🔧 管理命令:${NC}"
    echo -e "  启动服务: $SCRIPT_DIR/start_celery.sh"
    echo -e "  停止服务: $SCRIPT_DIR/stop_celery.sh"
    echo -e "  重启服务: $SCRIPT_DIR/restart_celery.sh"
    echo -e "  查看日志: tail -f $LOG_DIR/worker.log"
}

# 实时日志查看
show_logs() {
    local service="${1:-worker}"
    local log_file="$LOG_DIR/${service}.log"

    if [[ -f "$log_file" ]]; then
        echo -e "${BLUE}📝 实时查看 ${service} 日志 (Ctrl+C 退出):${NC}"
        tail -f "$log_file"
    else
        echo -e "${RED}❌ 日志文件不存在: $log_file${NC}"
        exit 1
    fi
}

# 主函数
main() {
    case "${1:-status}" in
        "status"|"")
            check_status
            ;;
        "logs")
            show_logs "${2:-worker}"
            ;;
        "worker-logs")
            show_logs "worker"
            ;;
        "beat-logs")
            show_logs "beat"
            ;;
        "flower-logs")
            show_logs "flower"
            ;;
        *)
            echo -e "${BLUE}用法: $0 [status|logs|worker-logs|beat-logs|flower-logs] [service_name]${NC}"
            echo -e "${BLUE}示例:${NC}"
            echo -e "  $0                # 显示状态"
            echo -e "  $0 status         # 显示状态"
            echo -e "  $0 logs worker    # 查看worker日志"
            echo -e "  $0 worker-logs    # 查看worker日志"
            echo -e "  $0 beat-logs      # 查看beat日志"
            echo -e "  $0 flower-logs    # 查看flower日志"
            exit 1
            ;;
    esac
}

# 如果直接运行此脚本
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
