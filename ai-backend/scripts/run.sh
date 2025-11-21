#!/usr/bin/env bash
# 统一脚本入口点
# 提供简化的脚本调用方式

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 显示帮助信息
show_help() {
    echo -e "${BLUE}📋 Max AI Backend 脚本管理工具${NC}"
    echo ""
    echo -e "${CYAN}用法:${NC}"
    echo "  $0 <命令> [参数]"
    echo ""
    echo -e "${CYAN}🚀 服务管理:${NC}"
    echo "  dev                    启动本地开发环境"
    echo "  server                 启动Docker FastAPI服务"
    echo "  celery                 启动Docker Celery服务"
    echo ""
    echo -e "${CYAN}🗄️ 数据库管理:${NC}"
    echo "  db:init                初始化数据库"
    echo "  db:migrate             执行数据库迁移"
    echo "  db:fix-sequences       修复PostgreSQL序列"
    echo ""
    echo -e "${CYAN}🛠️ 开发工具:${NC}"
    echo "  hooks:install          安装Git Hooks"
    echo "  hooks:check            检查Git Hooks状态"
    echo ""
    echo -e "${CYAN}🚀 部署监控:${NC}"
    echo "  health                 生产环境健康检查"
    echo ""
    echo -e "${CYAN}📖 帮助:${NC}"
    echo "  help, -h, --help       显示此帮助信息"
    echo ""
    echo -e "${YELLOW}示例:${NC}"
    echo "  $0 dev                 # 启动开发环境"

    echo "  $0 db:init             # 初始化数据库"
    echo "  $0 hooks:install       # 安装Git Hooks"
}

# 执行脚本
run_script() {
    local script_path="$1"
    shift

    if [ -f "$script_path" ]; then
        echo -e "${GREEN}🔧 执行: $script_path${NC}"
        bash "$script_path" "$@"
    else
        echo -e "${RED}❌ 脚本不存在: $script_path${NC}"
        exit 1
    fi
}

# 主函数
main() {
    local command="$1"
    shift || true

    case "$command" in
        # 服务管理
        "dev")
            run_script "$SCRIPT_DIR/dev/start.sh" "$@"
            ;;
        "server")
            run_script "$SCRIPT_DIR/deployment/start.sh" "$@"
            ;;
        "celery")
            run_script "$SCRIPT_DIR/deployment/celery.sh" "$@"
            ;;

        # 数据库管理
        "db:init")
            run_script "$SCRIPT_DIR/database/init-database.sh" "$@"
            ;;
        "db:migrate")
            run_script "$SCRIPT_DIR/database/run-migrations.sh" "$@"
            ;;
        "db:fix-sequences")
            run_script "$SCRIPT_DIR/database/fix-sequences.sh" "$@"
            ;;

        # 开发工具
        "hooks:install")
            run_script "$SCRIPT_DIR/dev/install-git-hooks.sh" "$@"
            ;;
        "hooks:check")
            run_script "$SCRIPT_DIR/dev/install-git-hooks.sh" "--check" "$@"
            ;;

        # 部署监控
        "health")
            run_script "$SCRIPT_DIR/deployment/health-check.sh" "$@"
            ;;

        # 帮助
        "help" | "-h" | "--help" | "")
            show_help
            ;;

        *)
            echo -e "${RED}❌ 未知命令: $command${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 如果脚本被直接执行
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi
