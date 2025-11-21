#!/bin/bash
# MCP服务启动脚本

# 检查Python环境
# if ! command -v python3 &> /dev/null; then
#     echo "错误: 未找到Python3，请先安装Python3"
#     exit 1
# fi

# # 检查是否安装了依赖
# if ! command -v pip3 &> /dev/null; then
#     echo "错误: 未找到pip3，请先安装pip"
#     exit 1
# fi

# # 检查并创建虚拟环境
# if [ ! -d "venv" ]; then
#     echo "创建虚拟环境..."
#     python3 -m venv venv
# fi

# # 激活虚拟环境
# echo "激活虚拟环境..."
# source venv/bin/activate

# # 安装依赖
# echo "安装依赖..."
# pip install -r requirements.txt

# # 检查环境配置文件
# if [ ! -f ".env" ]; then
#     echo "警告: 未找到.env文件，将使用默认配置"
#     cp env.example .env
#     echo "已创建默认配置文件.env，请根据需要修改"
# fi

# 设置健康检查函数
health_check() {
    echo "执行健康检查..."
    HEALTH_CHECK_URL="http://localhost:8008/health"
    HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_CHECK_URL)

    if [ "$HEALTH_STATUS" -eq 200 ]; then
        HEALTH_RESPONSE=$(curl -s $HEALTH_CHECK_URL)
        if [[ $HEALTH_RESPONSE == *"unhealthy"* ]]; then
            echo "健康检查失败: 服务不健康"
            return 1
        else
            echo "健康检查成功: 服务正常运行"
            return 0
        fi
    else
        echo "健康检查失败: 无法连接到服务 (HTTP状态码: $HEALTH_STATUS)"
        return 1
    fi
}

# 启动服务函数
start_service() {
    echo "启动MCP服务..."
    python main.py &
    PID=$!
    echo "MCP服务已启动，PID: $PID"

    # 等待服务启动
    sleep 5

    # 定期健康检查
    while true; do
        if ! health_check; then
            echo "检测到服务异常，尝试重启..."
            kill $PID
            wait $PID 2>/dev/null
            echo "启动MCP服务..."
            python main.py &
            PID=$!
            echo "MCP服务已重启，新PID: $PID"
        fi
        sleep 60  # 每60秒检查一次
    done
}

# 捕获CTRL+C信号
trap 'echo "接收到中断信号，停止服务..."; kill $PID 2>/dev/null; exit 0' INT

# 启动服务
start_service
