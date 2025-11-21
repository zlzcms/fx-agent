#!/bin/bash

# Jenkins Docker部署脚本
# 用于AI客户端前端项目的自动化部署

set -e  # 遇到错误立即退出

# =============================================================================
# 配置变量
# =============================================================================

# 项目信息
PROJECT_NAME="ai_client_front"
CONTAINER_NAME="ai_client"
IMAGE_NAME="ai_client"
IMAGE_TAG="${BUILD_NUMBER:-latest}"
FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"

# Docker配置
DOCKER_NETWORK="fba_network"
DOCKER_PORT="8080"
HOST_PORT="8080"

# 部署环境配置
DEPLOY_ENV="${DEPLOY_ENV:-production}"
HEALTH_CHECK_URL="http://localhost:${HOST_PORT}/health"
HEALTH_CHECK_TIMEOUT=60

# 日志配置
LOG_DIR="./logs"
BUILD_LOG="${LOG_DIR}/build-${BUILD_NUMBER:-$(date +%Y%m%d_%H%M%S)}.log"

# =============================================================================
# 工具函数
# =============================================================================

# 日志函数
log() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$message"
    
    # 确保日志目录存在
    if [[ -n "${BUILD_LOG}" ]]; then
        mkdir -p "$(dirname "${BUILD_LOG}")" 2>/dev/null || true
        echo "$message" >> "${BUILD_LOG}" 2>/dev/null || true
    fi
}

# 错误处理函数
error_exit() {
    log "错误: $1"
    cleanup_on_failure
    exit 1
}

# 失败时清理函数
cleanup_on_failure() {
    log "执行清理操作..."
    # 清理可能的失败容器
    docker container prune -f 2>/dev/null || true
}

# 健康检查函数
health_check() {
    local url=$1
    local timeout=$2
    local count=0
    
    log "开始健康检查: $url"
    
    while [ $count -lt $timeout ]; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            log "健康检查通过"
            return 0
        fi
        
        count=$((count + 1))
        log "健康检查失败，等待重试... ($count/$timeout)"
        sleep 1
    done
    
    log "健康检查超时失败"
    return 1
}

# =============================================================================
# 主要部署流程
# =============================================================================

# 初始化环境
init_deploy() {
    # 首先创建日志目录
    mkdir -p "${LOG_DIR}"
    
    log "=== 开始部署 AI客户端前端项目 ==="
    log "项目名称: ${PROJECT_NAME}"
    log "镜像名称: ${FULL_IMAGE_NAME}"
    log "部署环境: ${DEPLOY_ENV}"
    log "构建编号: ${BUILD_NUMBER:-N/A}"
    
    # 检查Docker是否运行
    if ! docker info > /dev/null 2>&1; then
        error_exit "Docker服务未运行"
    fi
    
    # 检查Docker网络
    if ! docker network ls | grep -q "${DOCKER_NETWORK}"; then
        log "创建Docker网络: ${DOCKER_NETWORK}"
        docker network create "${DOCKER_NETWORK}" || error_exit "创建Docker网络失败"
    fi
}

# 构建Docker镜像
build_image() {
    log "=== 构建Docker镜像 ==="
    
    # 检查必要文件
    if [[ ! -f "Dockerfile" ]]; then
        error_exit "Dockerfile文件不存在"
    fi
    
    if [[ ! -f "package.json" ]]; then
        error_exit "package.json文件不存在"
    fi
    
    # 构建镜像
    log "开始构建镜像: ${FULL_IMAGE_NAME}"
    
    # 使用临时文件记录构建结果
    BUILD_OUTPUT=$(mktemp)
    if docker build -t "${FULL_IMAGE_NAME}" . > "${BUILD_OUTPUT}" 2>&1; then
        cat "${BUILD_OUTPUT}" | tee -a "${BUILD_LOG}"
        log "Docker镜像构建成功"
    else
        cat "${BUILD_OUTPUT}" | tee -a "${BUILD_LOG}"
        rm -f "${BUILD_OUTPUT}"
        error_exit "Docker镜像构建失败"
    fi
    
    rm -f "${BUILD_OUTPUT}"
    
    # 镜像信息
    docker images | grep "${IMAGE_NAME}" | head -1 | tee -a "${BUILD_LOG}"
}

# 启动新容器 (使用Docker Compose自动替换)
start_new_container() {
    log "=== 启动新容器 (Docker Compose自动替换) ==="
    
    # 检测Docker Compose命令
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        error_exit "未找到docker-compose或docker compose命令"
    fi
    
    # 停止并删除旧容器
    log "停止并删除旧容器..."
    BUILD_NUMBER=${BUILD_NUMBER} ${COMPOSE_CMD} down || log "警告: 停止旧容器失败或容器不存在"
    
    # 删除可能存在的同名容器
    if docker ps -a --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        log "发现同名容器，强制删除: ${CONTAINER_NAME}"
        docker rm -f "${CONTAINER_NAME}" || log "警告: 删除容器失败"
    fi
    
    log "使用${COMPOSE_CMD}启动服务..."
    BUILD_NUMBER=${BUILD_NUMBER} ${COMPOSE_CMD} up -d || error_exit "启动容器失败"
    
    # 等待容器启动
    log "等待容器启动..."
    sleep 10
    
    # 健康检查
    if ! health_check "${HEALTH_CHECK_URL}" "${HEALTH_CHECK_TIMEOUT}"; then
        error_exit "新容器健康检查失败"
    fi
    
    log "新容器启动成功"
}

# 清理旧的ai_client镜像
cleanup_old_images() {
    log "=== 清理旧的ai_client镜像 ==="
    
    # 清理多余的ai_client镜像版本（保留最新的3个版本）
    log "查找需要删除的旧ai_client镜像（保留最新3个版本）..."
    
    # 获取所有ai_client镜像，按创建时间排序，跳过前3个最新的
    OLD_IMAGES=$(docker images ai_client --format "{{.Repository}}:{{.Tag}}" | grep -v "<none>" | grep -v "latest" | tail -n +4 || true)
    
    if [[ -n "${OLD_IMAGES}" ]]; then
        log "找到需要清理的旧ai_client镜像:"
        echo "${OLD_IMAGES}" | while read -r image; do
            if [[ -n "${image}" ]] && [[ "${image}" != "ai_client:${IMAGE_TAG}" ]]; then
                log "删除镜像: ${image}"
                docker rmi "${image}" 2>/dev/null || log "警告: 删除镜像失败，可能被其他容器使用: ${image}"
            fi
        done
    else
        log "没有需要清理的旧ai_client镜像"
    fi
    
    # 清理悬空镜像
    log "清理悬空镜像..."
    docker image prune -f 2>/dev/null || log "警告: 悬空镜像清理失败"
    
    # 显示当前ai_client镜像状态
    log "当前ai_client镜像状态:"
    docker images ai_client --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" || true
    
    log "ai_client镜像清理完成"
}

# 验证部署结果
verify_deployment() {
    log "=== 验证部署结果 ==="
    
    # 检查容器状态
    if ! docker ps | grep -q "${CONTAINER_NAME}"; then
        error_exit "容器未正常运行"
    fi
    
    # 最终健康检查
    if ! health_check "${HEALTH_CHECK_URL}" 10; then
        error_exit "部署后健康检查失败"
    fi
    
    # 显示容器信息
    log "容器运行状态:"
    docker ps | grep "${CONTAINER_NAME}" | tee -a "${BUILD_LOG}"
    
    # 测试主要功能
    log "测试主页访问"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${HOST_PORT}/")
    if [[ "${HTTP_CODE}" != "200" ]]; then
        error_exit "主页访问失败，HTTP状态码: ${HTTP_CODE}"
    fi
    
    log "=== 部署验证通过 ==="
}

# 生成部署报告
generate_report() {
    log "=== 生成部署报告 ==="
    
    REPORT_FILE="${LOG_DIR}/deploy-report-${BUILD_NUMBER:-$(date +%Y%m%d_%H%M%S)}.md"
    
    cat > "${REPORT_FILE}" << EOF
# AI客户端前端部署报告

## 部署信息
- **部署时间**: $(date '+%Y-%m-%d %H:%M:%S')
- **构建编号**: ${BUILD_NUMBER:-N/A}
- **镜像版本**: ${FULL_IMAGE_NAME}
- **部署环境**: ${DEPLOY_ENV}
- **容器名称**: ${CONTAINER_NAME}

## 服务信息
- **访问地址**: http://localhost:${HOST_PORT}
- **健康检查**: ${HEALTH_CHECK_URL}
- **Docker网络**: ${DOCKER_NETWORK}

## 部署状态
✅ Docker镜像构建成功
✅ 容器启动成功  
✅ 健康检查通过
✅ 功能验证通过
✅ 旧镜像清理完成

## 容器信息
\`\`\`
$(docker ps | grep "${CONTAINER_NAME}")
\`\`\`

## 当前镜像信息
\`\`\`
$(docker images | grep "${IMAGE_NAME}")
\`\`\`

---
*报告生成时间: $(date '+%Y-%m-%d %H:%M:%S')*
EOF
    
    log "部署报告已生成: ${REPORT_FILE}"
}

# =============================================================================
# 主函数
# =============================================================================

main() {
    # 执行部署流程
    init_deploy
    build_image
    start_new_container
    cleanup_old_images
    verify_deployment
    generate_report
    
    log "=== 部署完成 ==="
    log "服务访问地址: http://localhost:${HOST_PORT}"
    log "健康检查地址: ${HEALTH_CHECK_URL}"
    log "构建日志: ${BUILD_LOG}"
}

# =============================================================================
# 脚本入口
# =============================================================================

# 检查参数
case "${1:-}" in
    "help"|"-h"|"--help")
        echo "用法: $0 [选项]"
        echo ""
        echo "环境变量:"
        echo "  BUILD_NUMBER    - Jenkins构建编号"
        echo "  DEPLOY_ENV      - 部署环境 (默认: production)"
        echo ""
        echo "示例:"
        echo "  $0                          # 使用默认配置部署"
        echo "  BUILD_NUMBER=123 $0         # 指定构建编号"
        echo "  DEPLOY_ENV=staging $0       # 指定部署环境"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac