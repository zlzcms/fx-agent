# -*- coding: utf-8 -*-
# MCP Service Services Package
from .query_service import query_service

__all__ = ["query_service"]

# 查询服务现在通过query_service动态加载，不再直接导入
