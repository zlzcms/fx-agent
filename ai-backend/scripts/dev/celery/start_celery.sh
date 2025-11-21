#!/usr/bin/env bash
# 开发环境Celery服务启动脚本
# 本地开发时启动Celery Worker、Beat和Flower服务

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

# 选择Python解释器（优先项目虚拟环境）
if [[ -n "$VIRTUAL_ENV" && -x "$VIRTUAL_ENV/bin/python" ]]; then
  PYTHON_BIN="$VIRTUAL_ENV/bin/python"
elif [[ -x "$PROJECT_ROOT/.venv/bin/python" ]]; then
  PYTHON_BIN="$PROJECT_ROOT/.venv/bin/python"
else
  PYTHON_BIN="$(command -v python)"
fi

echo -e "${BLUE}🧪 使用Python: $PYTHON_BIN${NC}"

# 日志目录
LOG_DIR="$PROJECT_ROOT/logs/celery"
mkdir -p "$LOG_DIR"

# 检查Python环境
check_python_env() {
    if [[ -n "$VIRTUAL_ENV" ]]; then
        echo -e "${GREEN}✅ 虚拟环境: $VIRTUAL_ENV${NC}"
    else
        echo -e "${BLUE}ℹ️  使用系统Python环境${NC}"
    fi
}

# 检查依赖
check_dependencies() {
    echo -e "${BLUE}🔍 检查依赖...${NC}"

    # 验证选择的Python是否可用
    if [[ -z "$PYTHON_BIN" ]] || ! "$PYTHON_BIN" -V >/dev/null 2>&1; then
        echo -e "${RED}❌ Python 不可用或未安装${NC}"
        exit 1
    fi

    if ! "$PYTHON_BIN" -c "import celery" 2>/dev/null; then
        echo -e "${RED}❌ Celery 未安装，请运行: $PYTHON_BIN -m pip install celery${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ 依赖检查通过${NC}"
}

# 停止现有的celery进程
stop_existing_celery() {
    echo -e "${YELLOW}🛑 停止现有的Celery进程...${NC}"

    # 停止所有celery进程
    pkill -f "celery.*worker" 2>/dev/null || true
    pkill -f "celery.*beat" 2>/dev/null || true
    pkill -f "celery.*flower" 2>/dev/null || true

    # 等待进程停止
    sleep 2

    echo -e "${GREEN}✅ 现有进程已停止${NC}"
}

# 启动Celery Worker
start_worker() {
    echo -e "${BLUE}🚀 启动Celery Worker...${NC}"

    cd "$PROJECT_ROOT"

    nohup "$PYTHON_BIN" -m celery -A backend.app.task.celery worker \
        --loglevel=info \
        --pool=threads \
        > "$LOG_DIR/worker.log" 2>&1 &

    WORKER_PID=$!

    echo -e "${GREEN}✅ Celery Worker 已启动 (PID: $WORKER_PID)${NC}"
    echo -e "${BLUE}   日志文件: $LOG_DIR/worker.log${NC}"
}

# 启动Celery Beat
start_beat() {
    echo -e "${BLUE}🚀 启动Celery Beat...${NC}"

    cd "$PROJECT_ROOT"

    nohup "$PYTHON_BIN" -m celery -A backend.app.task.celery beat \
        --loglevel=info \
        > "$LOG_DIR/beat.log" 2>&1 &

    BEAT_PID=$!

    echo -e "${GREEN}✅ Celery Beat 已启动 (PID: $BEAT_PID)${NC}"
    echo -e "${BLUE}   日志文件: $LOG_DIR/beat.log${NC}"
}

# 启动Celery Flower
start_flower() {
    echo -e "${BLUE}🚀 启动Celery Flower...${NC}"

    cd "$PROJECT_ROOT"

    nohup "$PYTHON_BIN" -m celery -A backend.app.task.celery flower \
        --port=8555 \
        --basic-auth=admin:123456 \
        > "$LOG_DIR/flower.log" 2>&1 &

    FLOWER_PID=$!

    echo -e "${GREEN}✅ Celery Flower 已启动 (PID: $FLOWER_PID)${NC}"
    echo -e "${BLUE}   访问地址: http://localhost:8555${NC}"
    echo -e "${BLUE}   用户名/密码: admin/123456${NC}"
    echo -e "${BLUE}   日志文件: $LOG_DIR/flower.log${NC}"
}

# 显示状态
show_status() {
    echo -e "\n${BLUE}📊 Celery 服务状态:${NC}"

    # 检查各个服务
    local worker_count=$(ps aux | grep -c "celery.*worker" | grep -v grep || echo "0")
    local beat_count=$(ps aux | grep -c "celery.*beat" | grep -v grep || echo "0")
    local flower_count=$(ps aux | grep -c "celery.*flower" | grep -v grep || echo "0")

    if [[ $worker_count -gt 0 ]]; then
        echo -e "${GREEN}  ✅ celery_worker: 运行中${NC}"
    else
        echo -e "${RED}  ❌ celery_worker: 未运行${NC}"
    fi

    if [[ $beat_count -gt 0 ]]; then
        echo -e "${GREEN}  ✅ celery_beat: 运行中${NC}"
    else
        echo -e "${RED}  ❌ celery_beat: 未运行${NC}"
    fi

    if [[ $flower_count -gt 0 ]]; then
        echo -e "${GREEN}  ✅ celery_flower: 运行中${NC}"
    else
        echo -e "${RED}  ❌ celery_flower: 未运行${NC}"
    fi

    echo -e "\n${BLUE}📝 日志文件:${NC}"
    echo -e "  Worker: $LOG_DIR/worker.log"
    echo -e "  Beat: $LOG_DIR/beat.log"
    echo -e "  Flower: $LOG_DIR/flower.log"

    echo -e "\n${BLUE}🔧 管理命令:${NC}"
    echo -e "  查看日志: tail -f $LOG_DIR/worker.log"
    echo -e "  停止服务: $SCRIPT_DIR/stop_celery.sh"
    echo -e "  重启服务: $SCRIPT_DIR/restart_celery.sh"
    echo -e "  查看状态: $SCRIPT_DIR/status_celery.sh"
}

# 主函数
main() {
    echo -e "${BLUE}🌟 启动开发环境Celery服务...${NC}"

    # 检查Python环境
    check_python_env

    # 检查依赖
    check_dependencies

    # 停止现有进程
    stop_existing_celery

    # 启动服务
    start_worker
    sleep 2
    start_beat
    sleep 2
    start_flower

    # 显示状态
    show_status

    echo -e "\n${GREEN}🎉 Celery 服务启动完成！${NC}"
}

# 如果直接运行此脚本
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
