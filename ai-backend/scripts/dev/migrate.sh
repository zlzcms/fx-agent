#!/bin/bash
# 本地数据库迁移脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo -e "${BLUE}🔄 开始数据库迁移...${NC}"

# 切换到项目根目录
cd "$PROJECT_ROOT"

# 设置PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# 检查虚拟环境
if [ -n "$VIRTUAL_ENV" ]; then
    echo -e "${GREEN}✅ 虚拟环境已激活: $VIRTUAL_ENV${NC}"
else
    echo -e "${YELLOW}⚠️  建议在虚拟环境中运行${NC}"
fi

# 检查alembic命令
if ! command -v alembic &> /dev/null; then
    echo -e "${RED}❌ 未找到alembic命令${NC}"
    exit 1
fi

# 检查当前迁移状态
echo -e "${BLUE}🔍 检查当前迁移状态...${NC}"
CURRENT_VERSION=$(alembic current 2>/dev/null | grep -v "INFO" | tail -1 | awk '{print $1}')
echo -e "${BLUE}当前版本: $CURRENT_VERSION${NC}"

# 检查最新版本
HEAD_VERSION=$(alembic heads 2>/dev/null | grep -v "INFO" | tail -1 | awk '{print $1}')
echo -e "${BLUE}最新版本: $HEAD_VERSION${NC}"

# 检查是否有多个head
HEAD_COUNT=$(alembic heads 2>/dev/null | grep -v "INFO" | wc -l | tr -d ' ')
if [ "$HEAD_COUNT" -gt 1 ]; then
    echo -e "${YELLOW}⚠️  发现多个head版本，这可能表示分支冲突${NC}"
    alembic heads
fi

# 执行迁移
if [ "$CURRENT_VERSION" = "$HEAD_VERSION" ]; then
    echo -e "${GREEN}✅ 数据库已是最新版本${NC}"
else
    echo -e "${BLUE}🔄 开始执行迁移...${NC}"

    # 尝试升级到最新版本
    if alembic upgrade head; then
        echo -e "${GREEN}✅ 数据库迁移完成${NC}"

        # 显示最终版本
        FINAL_VERSION=$(alembic current 2>/dev/null | grep -v "INFO" | tail -1 | awk '{print $1}')
        echo -e "${GREEN}🎯 最终版本: $FINAL_VERSION${NC}"
    else
        echo -e "${RED}❌ 数据库迁移失败${NC}"
        echo -e "${YELLOW}💡 这可能是因为迁移文件中的外键约束问题${NC}"
        echo -e "${YELLOW}💡 您可以手动检查数据库状态或运行 'alembic history' 查看详细信息${NC}"
        exit 1
    fi
fi
