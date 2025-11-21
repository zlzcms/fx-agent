#!/bin/bash
# 数据库健康检查脚本
# 建议通过crontab定期执行，例如：
# */5 * * * * cd /home/user/www/mcp-service && ./db_health_check.sh >> /home/user/www/mcp-service/log/health_check.log 2>&1

echo "=========================================="
echo "开始数据库健康检查: $(date)"
echo "=========================================="

# 健康检查URL
HEALTH_CHECK_URL="http://localhost:8008/health"

# 检查服务是否运行
SERVICE_PID=$(ps aux | grep "[p]ython main.py" | awk '{print $2}')
if [ -z "$SERVICE_PID" ]; then
    echo "服务未运行，启动服务..."
    cd "$(dirname "$0")"
    source .venv/bin/activate
    nohup ./start.sh > /dev/null 2>&1 &
    echo "服务已启动"
    exit 0
fi

# 检查健康状态
echo "检查健康状态..."
HTTP_STATUS=$(curl -s -o /tmp/health_response.json -w "%{http_code}" $HEALTH_CHECK_URL)

if [ "$HTTP_STATUS" -eq 200 ]; then
    # 检查响应内容
    DB_STATUS=$(grep -o '"database":"[^"]*"' /tmp/health_response.json | cut -d'"' -f4)
    SERVICE_STATUS=$(grep -o '"status":"[^"]*"' /tmp/health_response.json | cut -d'"' -f4)

    echo "服务状态: $SERVICE_STATUS"
    echo "数据库状态: $DB_STATUS"

    if [ "$DB_STATUS" = "connected" ] && [ "$SERVICE_STATUS" = "healthy" ]; then
        echo "服务健康，无需操作"
    elif [ "$DB_STATUS" = "reconnected" ] && [ "$SERVICE_STATUS" = "recovered" ]; then
        echo "服务已恢复，无需操作"
    else
        echo "服务不健康，尝试重启..."
        kill $SERVICE_PID
        sleep 5

        # 确认服务已停止
        if ps -p $SERVICE_PID > /dev/null; then
            echo "服务未能正常停止，强制终止..."
            kill -9 $SERVICE_PID
            sleep 2
        fi

        # 启动服务
        cd "$(dirname "$0")"
        source .venv/bin/activate
        nohup ./start.sh > /dev/null 2>&1 &
        echo "服务已重启"
    fi
else
    echo "健康检查请求失败，HTTP状态码: $HTTP_STATUS"
    echo "尝试重启服务..."

    # 终止当前服务
    kill $SERVICE_PID
    sleep 5

    # 确认服务已停止
    if ps -p $SERVICE_PID > /dev/null; then
        echo "服务未能正常停止，强制终止..."
        kill -9 $SERVICE_PID
        sleep 2
    fi

    # 启动服务
    cd "$(dirname "$0")"
    source .venv/bin/activate
    nohup ./start.sh > /dev/null 2>&1 &
    echo "服务已重启"
fi

# 清理临时文件
rm -f /tmp/health_response.json

echo "健康检查完成: $(date)"
echo "=========================================="
