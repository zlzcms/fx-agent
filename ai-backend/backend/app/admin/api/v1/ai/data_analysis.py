#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.schema.data_analysis import (
    DataAnalysisResponse,
    MultiUserDataAnalysisRequest,
)
from backend.app.admin.service.data_analysis_service import DataAnalysisService
from backend.common.response.response_schema import ResponseSchemaModel
from backend.common.security.jwt import DependsJwtAuth
from backend.database.db import get_db

data_analysis_service = DataAnalysisService()
router = APIRouter()


@router.post("/analyze-multi-user", summary="开始多用户数据分析", dependencies=[DependsJwtAuth])
async def analyze_multi_user_data(
    request: MultiUserDataAnalysisRequest, db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[DataAnalysisResponse]:
    """
    开始多用户数据分析流程：
    1. 查询每个用户的数据
    2. 对每个用户的数据进行智能拆分
    3. 分析每个用户的数据并生成报告
    4. 聚合所有用户报告生成总结报告

    Args:
        request: 多用户数据分析请求
        db: 数据库会话

    Returns:
        数据分析响应
    """
    # 构建条件字典
    condition = request.condition or {}
    if request.data_time_range_type:
        condition["data_time_range_type"] = request.data_time_range_type.value
    if request.data_time_value:
        condition["data_time_value"] = request.data_time_value

    try:
        # 从JWT token中获取当前用户的crm_user_id
        from backend.common.security.jwt import get_current_user_id

        current_user_id = get_current_user_id()
        crm_user_id = None
        if current_user_id:
            try:
                from backend.app.admin.crud.crud_user import user_dao

                user = await user_dao.get(db, current_user_id)
                if user and user.crm_user_id:
                    crm_user_id = int(user.crm_user_id)
            except Exception as e:
                print(f"获取crm_user_id失败: {e}")

        result = await data_analysis_service.analyze_user_data(
            db=db,
            query_types=request.query_types,
            data_permission_values=request.data_permission_values,
            condition=condition,
            basicInfo=request.basicInfo,
            crm_user_id=crm_user_id,
        )

        # 直接返回完整结果
        response_data = DataAnalysisResponse(
            task_id=None, status="completed", message="数据获取成功", success=True, data=result
        )
        return ResponseSchemaModel[DataAnalysisResponse](data=response_data)

    except Exception as e:
        response_data = DataAnalysisResponse(task_id=None, status="failed", message=str(e), success=False, data=None)
        return ResponseSchemaModel[DataAnalysisResponse](data=response_data)
