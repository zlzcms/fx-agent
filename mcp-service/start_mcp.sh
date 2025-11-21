#!/bin/bash
# MCP服务器启动脚本

# cd "$(dirname "$0")"

# # 激活虚拟环境（如果存在）
# if [ -d ".venv" ]; then
#     source .venv/bin/activate
# fi

# # 设置环境变量
# export PYTHONPATH="$(pwd):$PYTHONPATH"

# # 启动MCP服务器
# python mcp_server.py

# 启动MCP HTTP服务器
python mcp_server.py
