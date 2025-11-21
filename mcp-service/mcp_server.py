#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP服务器 - 将现有的HTTP API服务包装为标准MCP协议
"""

# 标准库导入
import logging
import os
from typing import Any, Dict

import uvicorn

# 第三方库导入
from fastmcp import FastMCP
from starlette.responses import JSONResponse

# 本地模块导入
from app.models.schema import QueryDataResponse
from app.services.query_service import query_service
from core.config import settings
from core.query import QUERY_TYPES
from utils.data import compress_data

# 参数示例（用于生成清晰的示例文档）
PARAM_EXAMPLES: Dict[str, Any] = {
    "user_id": "12345 or [12345, 67890]",  # 用户ID，支持单个数字或数组
    "username": "alice",  # 模糊搜索用户名，仅支持单个字符串
    "user_name": ["alice", "bob"],  # 精确匹配用户名，仅支持数组格式
    "email": "user@example.com",
    "country": ["US", "CN"],
    "kyc": 1,
    "register_time": {"start": "2024-01-01", "end": "2024-12-31"},
    "start_time": "2024-01-01 00:00:00",
    "end_time": "2024-12-31 23:59:59",
    "range_time": {"data_start_date": "2024-01-01", "data_end_date": "2024-12-31"},
    "page": 1,
    "size": 50,
    "limit": 100,
    "statistics_name": ["deposit_amount", "withdrawal_amount"],
}

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/tmp/mcp_server.log"),
    ],
)
logger = logging.getLogger(__name__)

host = os.getenv("MCP_HOST", "0.0.0.0")
port = int(os.getenv("MCP_SERVER_PORT", "8009"))

if settings.API_KEY:
    from fastmcp.server.auth.providers.jwt import StaticTokenVerifier

    # 配置静态令牌验证器，用于开发环境
    verifier = StaticTokenVerifier(
        tokens={
            settings.API_KEY: {
                "client_id": "mcp-client",
                "scopes": ["read:data", "write:data", "query:warehouse"],
            }
        },
        required_scopes=["read:data"],
    )

    mcp = FastMCP("Data Warehouse Query Service", auth=verifier)
    logger.info(f"已配置静态令牌认证，API密钥: {settings.API_KEY[:20]}...")
else:
    mcp = FastMCP("Data Warehouse Query Service")
    logger.warning("未配置MCP_API_KEY，跳过认证")


class QueryError(Exception):
    """查询相关异常"""

    pass


def handle_query_error(query_type: str, error: Exception) -> str:
    """统一处理查询错误"""
    error_msg = str(error)
    logger.error(f"查询{query_type}时发生错误: {error_msg}")

    if isinstance(error, QueryError):
        return f"查询失败：{error_msg}"
    else:
        return f"查询错误：{error_msg}"


def create_query_tools() -> None:
    """为每个查询类型创建MCP工具"""

    def _validate_crm_user_id(parameters: Dict[str, Any]) -> int:
        """校验并返回有效的 crm_user_id。

        - 必须存在于 parameters 中且为正整数
        - 失败时抛出 QueryError
        """
        crm_user_id = parameters.get("crm_user_id") if parameters else None
        if crm_user_id is None or not str(crm_user_id).strip():
            raise QueryError("缺少crm_user_id参数")
        try:
            crm_user_id_int = int(str(crm_user_id).strip())
            if crm_user_id_int <= 0:
                raise QueryError("crm_user_id参数无效")
            return crm_user_id_int
        except Exception:
            raise QueryError("crm_user_id参数无效")

    def create_query_handler(query_type: str, config: Dict[str, Any]) -> Any:
        """创建查询处理器"""

        async def query_handler(parameters: Dict[str, Any]) -> str:
            try:
                # 授权参数校验：强制要求提供 crm_user_id
                _validate_crm_user_id(parameters)
                result: QueryDataResponse = await query_service.execute_query(
                    query_type, parameters
                )

                if result.success:
                    if result.data is not None:
                        compressed_data = compress_data(result.data)
                        return f"查询成功：{compressed_data}"
                    else:
                        return "查询成功：无数据返回"
                else:
                    raise QueryError(result.message or "未知错误")

            except Exception as e:
                return handle_query_error(query_type, e)

        return query_handler

    def build_tool_description(query_type: str, config: Dict[str, Any]) -> str:
        """构建工具描述（包含必填/其一/可选参数与示例）"""
        description = config.get("description", f"{query_type}查询")
        required_params = config.get("required_params", [])
        one_of_params = config.get("one_of_params", [])
        optional_params = config.get("optional_params", [])

        if required_params:
            required_doc = "\n".join(
                [
                    f"        - {p}: 必填，例如 {PARAM_EXAMPLES.get(p, '...')}"
                    for p in required_params
                ]
            )
        else:
            required_doc = "        - 无必填参数（按需提供筛选条件）"

        one_of_doc = (
            "\n".join(
                [
                    f"        - {p}: 其一，例如 {PARAM_EXAMPLES.get(p, '...')}"
                    for p in one_of_params
                ]
            )
            if one_of_params
            else ""
        )

        optional_doc = (
            "\n".join(
                [
                    f"        - {p}: 可选，例如 {PARAM_EXAMPLES.get(p, '...')}"
                    for p in optional_params
                ]
            )
            if optional_params
            else ""
        )

        doc = (
            f"此工具用于查询{description}相关数据。\n"
            f"授权校验：必须提供 crm_user_id（正整数）。\n"
            f"参数说明：\n"
            f"    - username: 模糊搜索用户名，支持单个字符串或数组，使用LIKE匹配\n"
            f"    - user_name: 精确匹配用户名，仅支持数组格式，使用IN匹配\n"
            f"Args:\n"
            f"{required_doc}\n"
        )
        if one_of_doc:
            doc += f"至少其一:\n{one_of_doc}\n"
        if optional_doc:
            doc += f"可选参数:\n{optional_doc}\n"
        doc += (
            f"Returns:\n"
            f"    查询结果的JSON字符串（成功以'查询成功：'开头，失败以'查询失败：/查询错误：'开头）\n"
            f"Example:\n"
            f"    成功: '查询成功：{{"
            "data"
            ": [...], "
            "total"
            ": 10}}'\n"
            f"    失败: '查询失败：参数错误'\n"
        )
        return doc

    # 为每个查询类型创建工具
    for query_id, query_config in QUERY_TYPES.items():
        tool_name = f"query_{query_id}"
        tool_description = build_tool_description(query_id, query_config)

        # 使用闭包保持query_id和query_config的引用
        def make_tool(
            q_id: str = query_id, q_config: Dict[str, Any] = query_config
        ) -> Any:
            @mcp.tool(
                name=f"query_{q_id}", description=build_tool_description(q_id, q_config)
            )
            async def query_tool(parameters: Dict[str, Any]) -> str:
                return await create_query_handler(q_id, q_config)(parameters)

            return query_tool

        make_tool()


create_query_tools()


@mcp.tool()
async def execute_query(query_type: str, parameters: Dict[str, Any]) -> str:
    """执行指定类型的数据查询

    Args:
        query_type: 查询类型，可选值包括: user_data, user_amount_log, user_login_log等
        parameters: 查询参数字典

    Returns:
        查询结果的JSON字符串
    """
    try:
        if query_type not in QUERY_TYPES:
            available_types = ", ".join(QUERY_TYPES.keys())
            raise QueryError(f"不支持的查询类型: {query_type}。可用类型: {available_types}")

        # 授权参数校验：强制要求提供 crm_user_id
        def _validate_crm_user_id(parameters: Dict[str, Any]) -> int:
            crm_user_id = parameters.get("crm_user_id") if parameters else None
            if crm_user_id is None or not str(crm_user_id).strip():
                raise QueryError("缺少crm_user_id参数")
            try:
                crm_user_id_int = int(str(crm_user_id).strip())
                if crm_user_id_int <= 0:
                    raise QueryError("crm_user_id参数无效")
                return crm_user_id_int
            except Exception:
                raise QueryError("crm_user_id参数无效")

        _validate_crm_user_id(parameters)

        result: QueryDataResponse = await query_service.execute_query(
            query_type, parameters
        )

        if result.success:
            if result.data is not None:
                compressed_data = compress_data(result.data)
                return f"查询成功：{compressed_data}"
            else:
                return "查询成功：无数据返回"
        else:
            raise QueryError(result.message or "未知错误")

    except Exception as e:
        return handle_query_error(query_type, e)


@mcp.tool()
async def list_query_types() -> str:
    """获取所有可用的查询类型及其描述

    Returns:
        可用查询类型的列表
    """
    query_list = []
    for query_id, config in QUERY_TYPES.items():
        query_info = {
            "type": query_id,
            "name": config.get("name", ""),
            "description": config.get("description", ""),
            "service": config.get("query_service", ""),
            "method": config.get("service_method", ""),
            "required_params": config.get("required_params", []),
            "one_of_params": config.get("one_of_params", []),
            "optional_params": config.get("optional_params", []),
        }
        query_list.append(query_info)

    return f"查询成功：{query_list}"


@mcp.resource("query-types://config")
async def get_query_config() -> str:
    """获取查询类型配置信息"""
    return str(QUERY_TYPES)


if __name__ == "__main__":
    logger.info("启动MCP数据仓库查询服务器...")

    try:
        mcp_app = mcp.http_app(path="/mcp")
        uvicorn.run(mcp_app, host=host, port=port)

    except Exception as e:
        logger.error(f"启动MCP服务器失败: {e}")
        raise
