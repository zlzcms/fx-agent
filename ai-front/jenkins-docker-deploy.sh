#!/bin/bash

# Jenkins Docker 构建部署脚本
# 用于在同一服务器上构建Docker镜像并启动容器服务

set -e  # 遇到错误立即退出

echo "======================================"
echo "开始 Jenkins Docker 构建部署流程"
echo "======================================"

# 配置变量
PROJECT_NAME="fba_ui"
IMAGE_NAME="fba_ui"
IMAGE_TAG="${BUILD_NUMBER:-latest}"
FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"
CONTAINER_NAME="fba_ui"
COMPOSE_FILE="docker-compose.yml"

# 环境检查
echo "1. 检查环境..."
echo "当前工作目录: $(pwd)"
echo "Docker版本: $(docker --version)"
if command -v docker-compose &> /dev/null; then
    echo "Docker Compose版本: $(docker-compose --version)"
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    echo "Docker Compose版本: $(docker compose version)"
    COMPOSE_CMD="docker compose"
else
    echo "错误: 未找到docker-compose或docker compose命令"
    exit 1
fi

# 检查必要文件
if [ ! -f "Dockerfile" ]; then
    echo "错误: 未找到Dockerfile"
    exit 1
fi

if [ ! -f "$COMPOSE_FILE" ]; then
    echo "错误: 未找到docker-compose.yml"
    exit 1
fi

# 记录现有容器状态
echo "2. 检查现有fba_ui容器..."

# 查找所有名为fba_ui的容器
OLD_FBA_UI_CONTAINERS=$(docker ps -aq --filter name=^fba_ui$)

if [ -n "$OLD_FBA_UI_CONTAINERS" ]; then
    echo "发现现有fba_ui容器，Docker Compose将自动替换："
    docker ps -a --filter name=^fba_ui$ --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}"
    HAS_OLD_CONTAINER=true
else
    echo "未发现现有fba_ui容器"
    HAS_OLD_CONTAINER=false
fi

# 清理悬空资源（保留构建缓存）
echo "3. 清理悬空资源..."

# 只清理<none>标签的悬空镜像
echo "清理悬空镜像..."
docker image prune -f || true

# 构建新的Docker镜像（利用缓存）
echo "4. 构建Docker镜像（利用缓存）..."
echo "构建命令: docker build -t $FULL_IMAGE_NAME ."
docker build -t $FULL_IMAGE_NAME .

# 检查构建结果
if ! docker images -q $FULL_IMAGE_NAME | grep -q .; then
    echo "错误: Docker镜像构建失败"
    exit 1
fi

echo "Docker镜像构建成功: $FULL_IMAGE_NAME"
docker images | grep $IMAGE_NAME

# 检查并创建Docker网络
echo "5. 检查Docker网络..."
if ! docker network ls | grep -q fba_network; then
    echo "创建Docker网络: fba_network"
    docker network create fba_network || true
fi

# 检查并创建Docker卷
echo "6. 检查Docker卷..."
if ! docker volume ls | grep -q fba_static; then
    echo "创建Docker卷: fba_static"
    docker volume create fba_static || true
fi

if ! docker volume ls | grep -q fba_static_upload; then
    echo "创建Docker卷: fba_static_upload"
    docker volume create fba_static_upload || true
fi

# 启动容器（Docker Compose会自动处理容器替换）
echo "7. 启动新容器..."

echo "使用$COMPOSE_CMD启动服务..."
echo "注意：Docker Compose会自动停止并替换现有的同名容器"
$COMPOSE_CMD up -d $PROJECT_NAME

# 等待容器启动并进行健康检查
echo "8. 等待容器启动并验证健康状态..."
sleep 15

# 验证部署
echo "9. 验证容器部署..."
CURRENT_CONTAINER=$CONTAINER_NAME

if docker ps | grep -q $CURRENT_CONTAINER; then
    echo "✅ 容器启动成功: $CURRENT_CONTAINER"
    echo "容器状态:"
    docker ps | grep $CURRENT_CONTAINER
    
    # 检查容器日志
    echo "容器启动日志:"
    docker logs $CURRENT_CONTAINER --tail 20
    
    # 检查服务端口
    if docker ps | grep $CURRENT_CONTAINER | grep -q "8088:80\|8088->80"; then
        echo "✅ 端口映射正常: 8088:80"
        
        # 等待服务完全启动
        echo "等待服务完全启动..."
        sleep 10
        
        # 健康检查
        if curl -f -s http://localhost:8088 >/dev/null 2>&1; then
            echo "✅ 服务访问正常 (http://localhost:8088)"
            SERVICE_HEALTHY=true
        else
            echo "⚠️  警告: 服务健康检查失败，等待更长时间..."
            sleep 15
            if curl -f -s http://localhost:8088 >/dev/null 2>&1; then
                echo "✅ 服务访问正常 (延迟启动)"
                SERVICE_HEALTHY=true
            else
                echo "❌ 服务健康检查失败"
                SERVICE_HEALTHY=false
            fi
        fi
    else
        echo "⚠️  警告: 端口映射检查异常"
        SERVICE_HEALTHY=false
    fi
    
    # 验证部署结果
    if [ "$SERVICE_HEALTHY" = true ]; then
        if [ "$HAS_OLD_CONTAINER" = true ]; then
            echo "✅ 容器部署成功，Docker Compose已自动替换旧容器"
        else
            echo "✅ 容器部署成功"
        fi
    else
        echo "❌ 容器服务异常，请检查问题"
        exit 1
    fi
    
else
    echo "❌ 容器启动失败"
    echo "查看容器日志:"
    docker logs $CURRENT_CONTAINER || true
    exit 1
fi

# 清理停止的容器（保留构建缓存和镜像）
echo "10. 清理停止的容器..."
docker container prune -f || true

# 清理多余的fba_ui镜像版本（保留最新的3个版本）
echo "11. 清理多余的fba_ui镜像版本（保留最新3个）..."

# 获取所有fba_ui镜像，按创建时间排序，跳过前3个最新的
OLD_IMAGES=$(docker images $IMAGE_NAME --format "{{.Repository}}:{{.Tag}}" | grep -v "<none>" | grep -v "latest" | tail -n +4 || true)

if [ ! -z "$OLD_IMAGES" ]; then
    echo "发现需要清理的旧fba_ui镜像:"
    echo "$OLD_IMAGES" | while read -r old_image; do
        if [ ! -z "$old_image" ] && [ "$old_image" != "$FULL_IMAGE_NAME" ]; then
            echo "  删除: $old_image"
            docker rmi "$old_image" 2>/dev/null || echo "    ⚠️ 删除失败，可能被其他容器使用"
        fi
    done
else
    echo "  没有需要清理的旧fba_ui镜像"
fi

# 显示当前fba_ui镜像状态
echo "📊 当前fba_ui镜像状态:"
docker images $IMAGE_NAME --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" || true

# 显示最终状态
echo "======================================"
echo "Jenkins Docker 部署完成"
echo "======================================"
echo "部署时间: $(date)"
echo "镜像信息:"
docker images | grep $IMAGE_NAME | head -3
echo ""
echo "容器信息:"
docker ps | grep $CONTAINER_NAME
echo ""
echo "服务访问地址: http://localhost:8088"
echo "容器管理命令:"
echo "  查看日志: docker logs $CONTAINER_NAME"
echo "  重启服务: $COMPOSE_CMD restart $PROJECT_NAME"
echo "  停止服务: $COMPOSE_CMD stop $PROJECT_NAME"
echo "======================================"