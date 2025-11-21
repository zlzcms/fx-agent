#!/bin/bash
# 设置定时任务脚本

# 获取当前目录的绝对路径
CURRENT_DIR=$(cd "$(dirname "$0")" && pwd)

# 创建临时crontab文件
TEMP_CRONTAB=$(mktemp)

# 导出当前用户的crontab
crontab -l > $TEMP_CRONTAB 2>/dev/null || echo "# 当前用户没有crontab" > $TEMP_CRONTAB

# 检查是否已经存在相同的任务
if ! grep -q "db_health_check.sh" $TEMP_CRONTAB; then
    # 添加健康检查任务，每5分钟执行一次
    echo "*/5 * * * * cd $CURRENT_DIR && $CURRENT_DIR/db_health_check.sh >> $CURRENT_DIR/log/health_check.log 2>&1" >> $TEMP_CRONTAB

    # 应用新的crontab
    crontab $TEMP_CRONTAB

    echo "已添加数据库健康检查定时任务（每5分钟执行一次）"
else
    echo "数据库健康检查定时任务已存在，无需添加"
fi

# 清理临时文件
rm -f $TEMP_CRONTAB

# 显示当前crontab
echo "当前crontab内容:"
crontab -l
