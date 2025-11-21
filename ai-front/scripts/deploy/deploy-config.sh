#!/bin/bash

# 部署配置文件
# 请根据实际情况修改以下配置

# 服务器配置
SERVER_HOST="47.239.101.153"
SERVER_USER="root"
SERVER_PATH="/www/ai/ai-front/apps/web-antd/dist/"

# 本地构建目录
LOCAL_DIST_PATH="./apps/web-antd/dist/"

# SSH配置
# 建议使用SSH密钥认证而不是密码
# 如果需要使用密码，请安装sshpass: brew install sshpass
USE_PASSWORD=true
SSH_PASSWORD="(14lZxhEuXnU"

# rsync选项
RSYNC_OPTIONS="-avz --delete"