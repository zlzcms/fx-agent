#!/bin/bash

# 自动部署脚本
# 构建完成后自动上传dist目录到服务器

set -e  # 遇到错误立即退出

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 加载配置文件
source "$SCRIPT_DIR/deploy-config.sh"

echo "开始部署到服务器 $SERVER_USER@$SERVER_HOST..."

# 检查dist目录是否存在
if [ ! -d "$LOCAL_DIST_PATH" ]; then
    echo "错误: dist目录不存在，请先运行构建命令"
    echo "路径: $LOCAL_DIST_PATH"
    exit 1
fi

# 在部署前注入构建时间信息到index.html
INDEX_HTML_PATH="$LOCAL_DIST_PATH/index.html"
if [ -f "$INDEX_HTML_PATH" ]; then
    echo "正在注入构建时间信息..."
    
    # 生成构建时间
    BUILD_TIME=$(date '+%Y/%m/%d %H:%M:%S')
    
    # 创建构建时间显示的HTML和JavaScript代码
    BUILD_TIME_HTML='<!-- 构建时间显示区域 -->\n    <div id="build-time-info" style="position: fixed; bottom: 40px; left: 10px; width: 200px; background: rgba(0,0,0,0.7); color: white; padding: 8px 12px; border-radius: 4px; font-size: 10px; z-index: 9999; font-family: monospace;">\n      <div>构建时间: <span id="build-time">'"$BUILD_TIME"'</span></div>\n    </div>\n    <script>\n      // 显示构建时间信息\n      (function() {\n        function updateBuildTimeInfo() {\n          const buildTimeEl = document.getElementById("build-time");\n          if (buildTimeEl) buildTimeEl.textContent = "'"$BUILD_TIME"'";\n        }\n        \n        // DOM加载完成后执行\n        if (document.readyState === "loading") {\n          document.addEventListener("DOMContentLoaded", updateBuildTimeInfo);\n        } else {\n          updateBuildTimeInfo();\n        }\n      })();\n    </script>'
    
    # 在</body>标签前插入构建时间信息
    sed -i.bak "s|</body>|$BUILD_TIME_HTML\n    </body>|g" "$INDEX_HTML_PATH"
    
    echo "构建时间信息已注入: $BUILD_TIME"
else
    echo "警告: 未找到index.html文件，跳过构建时间注入"
fi

# 检查是否安装了sshpass（如果使用密码认证）
if [ "$USE_PASSWORD" = true ]; then
    if ! command -v sshpass &> /dev/null; then
        echo "警告: 未安装sshpass，将尝试使用SSH密钥认证"
        echo "如需使用密码认证，请运行: brew install sshpass"
        USE_PASSWORD=false
    fi
fi

# 构建rsync命令
if [ "$USE_PASSWORD" = true ]; then
    echo "正在使用密码认证上传文件到服务器..."
    sshpass -p "$SSH_PASSWORD" rsync $RSYNC_OPTIONS -e ssh "$LOCAL_DIST_PATH" "$SERVER_USER@$SERVER_HOST:$SERVER_PATH"
else
    echo "正在使用SSH密钥认证上传文件到服务器..."
    rsync $RSYNC_OPTIONS -e ssh "$LOCAL_DIST_PATH" "$SERVER_USER@$SERVER_HOST:$SERVER_PATH"
fi

if [ $? -eq 0 ]; then
    echo "部署成功！"
    echo "文件已上传到: $SERVER_USER@$SERVER_HOST:$SERVER_PATH"
else
    echo "部署失败！"
    exit 1
fi
