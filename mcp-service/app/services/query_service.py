#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import importlib
import logging
from datetime import datetime
from typing import Any, Dict

from app.models.schema import QueryDataResponse
from core.log import logger
from core.query import QUERY_TYPES


class QueryService:
    """查询服务，处理各种类型的数据查询"""

    def __init__(self):
        # 服务缓存
        self.service_cache = {}

    def get_service(self, service_name: str):
        """根据服务名称动态获取服务实例

        参数:
            service_name: 服务名称

        返回:
            服务实例
        """
        # 如果服务已在缓存中，则直接返回
        if service_name in self.service_cache:
            return self.service_cache[service_name]

        try:
            # 尝试从 app.services.query 包导入
            module_path = f"app.services.query.{service_name}"
            service_module = importlib.import_module(module_path)

            # 约定服务模块应该导出与模块名相同的实例
            service_instance = getattr(service_module, service_name)

            # 缓存服务实例
            self.service_cache[service_name] = service_instance
            return service_instance
        except (ImportError, AttributeError) as e:
            logger.error(f"加载服务 {service_name} 失败: {str(e)}")
            return None

    async def execute_query(
        self, query_type: str, parameters: Dict[str, Any]
    ) -> QueryDataResponse:
        """执行指定类型的查询

        参数:
            query_type: 查询类型
            parameters: 查询参数
            context: 查询上下文

        返回:
            查询结果

        异常:
            KeyError: 查询类型不存在时抛出
            ValueError: 参数验证失败时抛出
        """
        try:
            # 检查查询类型是否存在
            if query_type not in QUERY_TYPES:
                raise KeyError(f"未知的查询类型: {query_type}")

            query_config = QUERY_TYPES[query_type]

            print(f"query_config: {query_config}")

            # 验证必需参数
            # for param in query_config.get("required_params", []):
            #     if param not in parameters:
            #         raise ValueError(f"缺少必需参数: {param}")

            # 使用服务方法而不是SQL查询
            service_method_name = query_config.get("service_method")
            query_service_name = query_config.get("query_service")

            if service_method_name and query_service_name:
                # 动态加载服务
                service = self.get_service(query_service_name)

                if service:
                    method = getattr(service, service_method_name)
                    return await method(parameters)

            return QueryDataResponse(
                success=False,
                message="未找到数据",
                data=None,
                parameters=parameters,
                sql_info=None,
                query_metadata={
                    "query_type": query_type,
                    "timestamp": datetime.now().isoformat(),
                },
            )

        except Exception as e:
            logger.error(f"执行查询 {query_type} 错误: {str(e)}")
            return QueryDataResponse(
                success=False,
                message=str(e),
                data=None,
                parameters=parameters,
                sql_info=None,
                query_metadata={
                    "query_type": query_type,
                    "timestamp": datetime.now().isoformat(),
                },
            )


# 创建单例实例
query_service = QueryService()
