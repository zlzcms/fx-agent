#!/bin/bash

# Jenkins Docker Deploy Script for MCP Service
# 简洁版部署脚本

set -e  # 遇到错误立即退出

# 配置变量
SERVICE_NAME="mcp_service"
IMAGE_NAME="mcp_service"
IMAGE_TAG="${BUILD_NUMBER:-latest}"
FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"
CONTAINER_NAME="mcp_service"

echo "🚀 开始部署 MCP Service..."

# 验证必要文件是否存在
echo "🔍 验证配置文件..."
required_files=("Dockerfile" "docker-compose.yml" "supervisord.conf" ".env")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ 缺少必要文件: $file"
        exit 1
    fi
done
echo "✅ 配置文件验证通过"

# 清理未使用的镜像
echo "🧹 清理Docker资源..."
docker image prune -f || echo "⚠️ 镜像清理失败，继续执行"
docker container prune -f || echo "⚠️ 容器清理失败，继续执行"

# 清理悬空镜像
docker image prune --filter "dangling=true" -f || echo "⚠️ 悬空镜像清理失败，继续执行"

# 清理多余的mcp_service镜像版本（保留最新的3个版本）
echo "🧹 清理多余的mcp_service镜像版本（保留最新3个）..."

# 获取所有mcp_service镜像，按创建时间排序，跳过前3个最新的
OLD_IMAGES=$(docker images ${IMAGE_NAME} --format "{{.Repository}}:{{.Tag}}" | grep -v "<none>" | grep -v "latest" | tail -n +4 || true)

if [ ! -z "$OLD_IMAGES" ]; then
    echo "发现需要清理的旧mcp_service镜像:"
    echo "$OLD_IMAGES" | while read -r old_image; do
        if [ ! -z "$old_image" ] && [ "$old_image" != "${FULL_IMAGE_NAME}" ]; then
            echo "  删除: $old_image"
            docker rmi "$old_image" 2>/dev/null || echo "    ⚠️ 删除失败，可能被其他容器使用"
        fi
    done
else
    echo "  没有需要清理的旧mcp_service镜像"
fi

# 显示当前镜像状态
echo "📊 当前mcp_service镜像状态:"
docker images ${IMAGE_NAME} --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" || true

# 构建新镜像
echo "🔨 构建Docker镜像..."
echo "构建镜像: ${FULL_IMAGE_NAME}"
BUILD_NUMBER=${BUILD_NUMBER} docker compose build

# 构建完成，直接通过 compose 替换运行中的容器
echo "🧩 构建完成，准备通过 compose 自动替换..."

# 启动服务（使用刚构建的镜像，不触发构建）
echo "▶️ 启动服务..."
docker compose up -d --no-build --remove-orphans

# 等待服务启动
echo "🔍 等待服务启动..."
sleep 5

# 等待API服务就绪
echo "⏳ 等待API服务就绪..."
for i in {1..12}; do
    if curl -f http://localhost:8008/health > /dev/null 2>&1; then
        echo "✅ API服务已就绪 (${i}0秒)"
        break
    fi
    if [ $i -eq 12 ]; then
        echo "⏰ API服务启动超时，继续检查容器状态"
    fi
    sleep 5
done

# 检查容器状态
if docker ps | grep -q $CONTAINER_NAME; then
    echo "✅ 容器启动成功"
else
    echo "❌ 容器启动失败"
    docker logs $CONTAINER_NAME
    exit 1
fi

# 健康检查API
echo "🩺 健康检查..."

# 检查API服务 (8008)
if curl -f http://localhost:8008/health > /dev/null 2>&1; then
    echo "✅ API服务健康检查通过 (8008)"
    api_status="✅"
else
    echo "❌ API服务健康检查失败 (8008)"
    api_status="❌"
fi

# 检查MCP服务 (8009) - 仅检测免鉴权健康端点
mcp_code_health=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8009/health || echo 000)
if [ "$mcp_code_health" = "200" ] || [ "$mcp_code_health" = "204" ]; then
    echo "✅ MCP服务健康检查通过 (8009 /health ${mcp_code_health})"
    mcp_status="✅"
else
    echo "⚠️ MCP服务健康检查失败 (8009 /health ${mcp_code_health})"
    mcp_status="⚠️"
fi

# 汇总健康状态
if [[ "$api_status" == "✅" ]]; then
    echo "✅ 整体服务健康检查通过"
else
    echo "❌ 服务健康检查失败，检查容器日志"
    docker logs $CONTAINER_NAME --tail 20
fi

# 显示服务状态
echo "📊 服务状态:"
docker compose ps

echo "🎉 部署完成！"
echo "🌐 API服务: http://localhost:8008 $api_status"
echo "🔌 MCP服务: http://localhost:8009 $mcp_status"
echo "📖 API文档: http://localhost:8008/api/v1/docs"
