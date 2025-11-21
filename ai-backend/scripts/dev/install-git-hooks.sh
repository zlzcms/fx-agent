#!/usr/bin/env bash
# Git Hooks 管理脚本
# 检查、安装和管理项目的 Git hooks

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查 Git hooks 状态函数
check_hooks_status() {
    local HOOKS_MISSING=false
    local REQUIRED_HOOKS=("pre-commit" "commit-msg" "pre-commit-alembic")

    echo -e "${BLUE}🔍 检查 Git Hooks 安装状态...${NC}"
    echo ""

    for hook in "${REQUIRED_HOOKS[@]}"; do
        if [ -f ".git/hooks/$hook" ] && [ -x ".git/hooks/$hook" ]; then
            echo -e "${GREEN}✅ $hook hook 已安装${NC}"
        else
            echo -e "${RED}❌ $hook hook 未安装${NC}"
            HOOKS_MISSING=true
        fi
    done

    echo ""
    if command -v pre-commit >/dev/null 2>&1; then
        echo -e "${GREEN}✅ pre-commit 工具已安装${NC}"
    else
        echo -e "${RED}❌ pre-commit 工具未安装${NC}"
        HOOKS_MISSING=true
    fi

    if [ -f ".pre-commit-config.yaml" ]; then
        echo -e "${GREEN}✅ pre-commit 配置文件存在${NC}"
    else
        echo -e "${RED}❌ pre-commit 配置文件不存在${NC}"
        HOOKS_MISSING=true
    fi

    echo ""

    if [ "$HOOKS_MISSING" = true ]; then
        return 1
    else
        echo -e "${GREEN}🎉 所有 Git Hooks 已正确安装！${NC}"
        return 0
    fi
}

# 如果传入 --check 参数，只检查状态
if [ "$1" = "--check" ]; then
    if check_hooks_status; then
        echo -e "${BLUE}💡 您的开发环境已准备就绪${NC}"
        exit 0
    else
        echo -e "${YELLOW}⚠️  检测到 Git Hooks 未完整安装！${NC}"
        echo ""
        echo -e "${BLUE}🚀 请运行以下命令安装 Git Hooks：${NC}"
        echo -e "${GREEN}   ./scripts/development/install-git-hooks.sh${NC}"
        exit 1
    fi
fi

# 检查当前状态，如果已安装则询问是否重新安装
if check_hooks_status; then
    read -p "Git Hooks 已安装，是否重新安装？[y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "跳过安装"
        exit 0
    fi
fi

echo -e "${BLUE}🔧 开始安装 Git Hooks...${NC}"

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

# 检查是否在Git仓库中
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ 当前目录不是Git仓库${NC}"
    exit 1
fi

# 安装pre-commit
echo -e "${BLUE}📦 检查pre-commit安装...${NC}"
if ! command -v pre-commit &> /dev/null; then
    echo -e "${YELLOW}正在安装pre-commit...${NC}"
    if command -v pip &> /dev/null; then
        pip install pre-commit
    elif command -v pip3 &> /dev/null; then
        pip3 install pre-commit
    else
        echo -e "${RED}❌ 未找到pip，请手动安装pre-commit${NC}"
        echo -e "${YELLOW}运行: pip install pre-commit${NC}"
        exit 1
    fi
fi

# 安装pre-commit hooks
echo -e "${BLUE}🔗 安装pre-commit hooks...${NC}"
pre-commit install

# 安装commit-msg hook
echo -e "${BLUE}📝 安装commit-msg hook...${NC}"
pre-commit install --hook-type commit-msg

# 创建自定义的pre-commit hook
echo -e "${BLUE}⚙️  创建自定义pre-commit hook...${NC}"
cat > .git/hooks/pre-commit-alembic << 'EOF'
#!/usr/bin/env bash
# 自定义Alembic检查hook

echo "🔍 运行Alembic迁移检查..."

# 运行数据库迁移检查脚本
if [ -f "scripts/development/pre-commit-db-migration.py" ]; then
    python3 scripts/development/pre-commit-db-migration.py
    if [ $? -ne 0 ]; then
        echo "❌ 数据库迁移检查失败"
        exit 1
    fi
fi

echo "✅ Alembic检查通过"
EOF

chmod +x .git/hooks/pre-commit-alembic

# 测试hooks
echo -e "${BLUE}🧪 测试pre-commit配置...${NC}"
pre-commit run --all-files --show-diff-on-failure || true

echo ""
echo -e "${GREEN}✅ Git Hooks安装完成！${NC}"
echo ""
echo -e "${BLUE}📋 已安装的检查项目：${NC}"
echo -e "${GREEN}  ✓ 代码格式检查 (ruff)${NC}"
echo -e "${GREEN}  ✓ YAML/TOML文件检查${NC}"
echo -e "${GREEN}  ✓ 提交信息格式检查 (commitizen)${NC}"
echo -e "${GREEN}  ✓ UV锁文件检查${NC}"
echo -e "${GREEN}  ✓ 数据库迁移状态检查${NC}"
echo ""
echo -e "${BLUE}🚀 使用说明：${NC}"
echo "  • 每次git commit时会自动运行检查"
echo "  • 如果检测到未生成的数据库迁移，提交会被阻止"
echo -e "${YELLOW}  • 手动运行检查: pre-commit run --all-files${NC}"
echo -e "${YELLOW}  • 只检查状态: ./scripts/development/install-git-hooks.sh --check${NC}"
echo ""
echo -e "${YELLOW}⚠️  注意事项：${NC}"
echo "  • 修改数据库模型后，请及时生成迁移文件"
echo "  • 确保数据库连接正常，否则检查可能失败"
echo "  • 团队成员都应该运行此安装脚本"
