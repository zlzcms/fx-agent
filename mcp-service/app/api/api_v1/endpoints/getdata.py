#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time

from fastapi import APIRouter, Depends

from app.api.deps import get_api_key
from app.common.response import ResponseFactory
from app.models.schema import (
    GetDataRequest,
    QueryDataResponse,
    QueryMetadata,
    QueryResponse,
)
from app.services.query_service import query_service
from core.log import logger
from core.query import QUERY_TYPES
from utils.data import compress_data

router = APIRouter()

DEFAULT_ERROR_MESSAGE = "未找到用户数据"
DEFAULT_COMPRESS = True


@router.post("/query", response_model=QueryResponse)
async def execute_query(request: GetDataRequest, api_key: str = Depends(get_api_key)):
    """执行单个查询"""
    try:
        query_type = request.query_type
        parameters = request.parameters
        is_compress_data = getattr(request, "is_compress_data", DEFAULT_COMPRESS)
        start_time = time.time()

        logger.info(f"Request content: {request.model_dump()}")

        # 授权参数校验：强制要求提供 crm_user_id
        crm_user_id = parameters.get("crm_user_id") if parameters else None
        if crm_user_id is None or not str(crm_user_id).strip():
            return ResponseFactory.error_response(
                message="缺少crm_user_id参数",
                parameters=parameters,
                error_code="MISSING_CRM_USER_ID",
            )
        try:
            crm_user_id_int = int(crm_user_id)
            if crm_user_id_int <= 0:
                return ResponseFactory.error_response(
                    message="crm_user_id参数无效",
                    parameters=parameters,
                    error_code="INVALID_CRM_USER_ID",
                )
        except Exception:
            return ResponseFactory.error_response(
                message="crm_user_id参数无效",
                parameters=parameters,
                error_code="INVALID_CRM_USER_ID",
            )

        result: QueryDataResponse = await query_service.execute_query(
            query_type, parameters
        )
        # logger.info(f"Query result: {result}")

        if not result.success:
            return ResponseFactory.error_response(
                message=result.message or DEFAULT_ERROR_MESSAGE, parameters=parameters
            )

        count = len(result.data) if isinstance(result.data, list) else 0
        data = (
            compress_data(result.data)
            if is_compress_data and query_type != "user_data"
            else result.data
        )
        query_time = time.time() - start_time
        metadata = QueryMetadata(
            query_time=f"{query_time:.2f}s", count=count, parameters=parameters
        )

        return ResponseFactory.success_response(
            data=data, message="查询成功", metadata=metadata
        )
    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        return ResponseFactory.error_response(
            message=f"查询失败: {str(e)}",
            parameters=getattr(request, "parameters", {}),
            error_code="QUERY_EXCEPTION",
        )


@router.post("/querys", response_model=QueryResponse)
async def execute_querys(request: GetDataRequest, api_key: str = Depends(get_api_key)):
    """执行批量查询"""
    try:
        query_types = request.query_types
        parameters = request.parameters
        is_compress_data = getattr(request, "is_compress_data", DEFAULT_COMPRESS)

        logger.info(f"Request content: {request.model_dump()}")

        if not query_types:
            return ResponseFactory.error_response(
                message="查询类型列表不能为空",
                parameters=parameters,
                error_code="EMPTY_QUERY_TYPES",
            )

        # 授权参数校验：强制要求提供 crm_user_id
        crm_user_id = parameters.get("crm_user_id") if parameters else None
        if crm_user_id is None or not str(crm_user_id).strip():
            return ResponseFactory.error_response(
                message="缺少crm_user_id参数",
                parameters=parameters,
                error_code="MISSING_CRM_USER_ID",
            )
        try:
            crm_user_id_int = int(crm_user_id)
            if crm_user_id_int <= 0:
                return ResponseFactory.error_response(
                    message="crm_user_id参数无效",
                    parameters=parameters,
                    error_code="INVALID_CRM_USER_ID",
                )
        except Exception:
            return ResponseFactory.error_response(
                message="crm_user_id参数无效",
                parameters=parameters,
                error_code="INVALID_CRM_USER_ID",
            )

        results = {}
        start_time = time.time()
        total_count = 0
        failed_queries = []
        successful_queries = []

        for query_type in query_types:
            result: QueryDataResponse = await query_service.execute_query(
                query_type, parameters
            )
            logger.info(f"Batch query result - {query_type}: {result}")

            if result.success:
                count = len(result.data) if isinstance(result.data, list) else 0
                data = compress_data(result.data) if is_compress_data else result.data
                total_count += count

                query_result = {
                    "success": True,
                    "data": data,
                    "message": result.message,
                    "metadata": {
                        "count": count,
                        "query_type_name": QUERY_TYPES.get(query_type, {}).get(
                            "name", ""
                        ),
                    },
                }

                successful_queries.append(query_type)
            else:
                query_result = {
                    "success": False,
                    "data": None,
                    "message": result.message or "查询失败",
                    "metadata": {
                        "count": 0,
                        "query_type_name": QUERY_TYPES.get(query_type, {}).get(
                            "name", ""
                        ),
                    },
                }
                failed_queries.append(query_type)

            results[query_type] = query_result

        query_time = time.time() - start_time

        # 确定整体查询状态和消息
        if not failed_queries:
            overall_success = True
            overall_message = "查询成功"
        elif not successful_queries:
            overall_success = False
            overall_message = "所有查询失败"
        else:
            overall_success = True
            overall_message = (
                f"部分查询成功 (成功: {len(successful_queries)}, 失败: {len(failed_queries)})"
            )

        batch_metadata = QueryMetadata(
            query_time=f"{query_time:.2f}s",
            count=total_count,
            parameters=request.parameters,
            failed_queries=failed_queries if failed_queries else None,
            successful_queries=successful_queries if successful_queries else None,
        )

        return (
            ResponseFactory.success_response(
                data=results, message=overall_message, metadata=batch_metadata
            )
            if overall_success
            else ResponseFactory.error_response(
                message=overall_message,
                parameters=request.parameters,
                metadata=batch_metadata.model_dump(),
            )
        )
    except Exception as e:
        logger.error(f"Batch query failed: {str(e)}")
        return ResponseFactory.error_response(
            message=f"查询失败: {str(e)}",
            parameters=getattr(request, "parameters", {}),
            error_code="BATCH_QUERY_EXCEPTION",
        )


@router.post("/data", response_model=QueryResponse)
async def execute_query(request: dict = None, api_key: str = Depends(get_api_key)):
    try:
        logger.info(f"query/data request: {request}")
        user_ids = []
        result = {}
        query_error = {}
        # 在组合查询中，优先从顶层或子请求获取crm_user_id，并向下传递
        crm_user_id = None
        if isinstance(request, dict):
            crm_user_id = request.get("crm_user_id")
            if not crm_user_id and "user_data" in request:
                crm_user_id = request["user_data"].get("crm_user_id")
        if crm_user_id is None or not str(crm_user_id).strip():
            return QueryResponse(
                success=False,
                message="缺少crm_user_id参数",
                metadata=QueryMetadata(parameters=request),
            )
        # 规范化为整型并做有效性校验
        try:
            crm_user_id_int = int(crm_user_id)
            if crm_user_id_int <= 0:
                return QueryResponse(
                    success=False,
                    message="crm_user_id参数无效",
                    metadata=QueryMetadata(parameters=request),
                )
            crm_user_id = crm_user_id_int
        except Exception:
            return QueryResponse(
                success=False,
                message="crm_user_id参数无效",
                metadata=QueryMetadata(parameters=request),
            )
        if "user_data" in request:
            # 确保子请求包含crm_user_id
            request["user_data"]["crm_user_id"] = crm_user_id
            user_result: QueryDataResponse = await query_service.execute_query(
                "user_data", request["user_data"]
            )
            if not user_result.success:
                logger.error(
                    f"query/data user_data query failed: {user_result.message}"
                )
                return QueryResponse(
                    success=False,
                    message=user_result.message or DEFAULT_ERROR_MESSAGE,
                    metadata=QueryMetadata(parameters=request["user_data"]),
                )
            if crm_user_id == 1:
                user_ids = []
            else:
                user_ids = (
                    [user.get("id") for user in user_result.data]
                    if user_result.data
                    else []
                )
            del request["user_data"]
            if user_result.data:
                result["user_data"] = compress_data(user_result.data)
            else:
                # 查询成功但没有数据，记录为查询结果而不是错误
                result["user_data"] = []

        for data_source, parameters in request.items():
            if QUERY_TYPES.get(data_source):
                if user_ids and not parameters.get("user_id"):
                    parameters["user_id"] = user_ids
                # 传递crm_user_id到每个子查询
                parameters["crm_user_id"] = crm_user_id
                logger.info(f"query/data {data_source} parameters: {parameters}")
                data_source_result: QueryDataResponse = (
                    await query_service.execute_query(data_source, parameters)
                )
                logger.info(
                    f"query/data {data_source} sql_info: {data_source_result.sql_info}"
                )
                if data_source_result.success:
                    if data_source_result.data:
                        result[data_source] = compress_data(data_source_result.data)
                    else:
                        # 查询成功但没有数据，记录为空结果
                        result[data_source] = []
                else:
                    query_error[data_source] = data_source_result.to_dict()

        # 如果有查询错误，返回失败；否则即使没有数据也返回成功
        if query_error:
            logger.error(f"query/data query failed: {DEFAULT_ERROR_MESSAGE}")
            return QueryResponse(
                success=False,
                message=DEFAULT_ERROR_MESSAGE,
                metadata=QueryMetadata(parameters=request, failed_queries=query_error),
            )
        logger.info(f"query/data query success")
        return QueryResponse(
            success=True,
            message="查询成功",
            data=result,
            metadata=QueryMetadata(parameters=request, failed_queries=query_error),
        )
    except Exception as e:
        logger.error(f"Query failed: {str(e)}")
        return QueryResponse(
            success=False,
            message=f"查询失败: {str(e)}",
            metadata=QueryMetadata(parameters=parameters),
        )
