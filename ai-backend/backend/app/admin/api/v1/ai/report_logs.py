#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI助手报告和风控报告API
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Body, Depends, Path, Query, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.service.assistant_report_service import assistant_report_service
from backend.app.admin.service.risk_report_service import risk_report_service
from backend.common.enums import RiskType
from backend.common.pagination import PageData
from backend.common.response.response_code import CustomResponse
from backend.common.response.response_schema import ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.database.db import get_db

router = APIRouter()


class ProcessReportRequest(BaseModel):
    """处理风控报告请求模型"""

    handle_result: str
    handle_user: Optional[str] = None
    handle_user_name: Optional[str] = None


# =========================== AI助手报告日志 API ===========================


@router.get("/assistant", summary="获取AI助手报告日志列表", dependencies=[DependsJwtAuth])
async def get_assistant_report_logs(
    assistant_id: Optional[str] = Query(None, description="AI助手ID"),
    assistant_name: Optional[str] = Query(None, description="助理名称"),
    model_id: Optional[str] = Query(None, description="AI模型ID"),
    member_id: Optional[str] = Query(None, description="用户ID"),
    start_time: Optional[str] = Query(None, description="开始时间"),
    end_time: Optional[str] = Query(None, description="结束时间"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, gt=0, le=200, description="每页数量"),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchemaModel[PageData[dict]]:
    """获取AI助手报告日志列表"""
    try:
        data = await assistant_report_service.get_paginated_list(
            db,
            assistant_id=assistant_id,
            assistant_name=assistant_name,
            model_id=model_id,
            member_id=member_id,
            start_time=start_time,
            end_time=end_time,
            page=page,
            size=size,
        )
        return response_base.success(data=data)
    except Exception as e:
        return response_base.fail(
            res=CustomResponse(code=500, msg=f"获取AI助手报告列表失败: {str(e)}"),
            data=PageData(
                items=[],
                total=0,
                page=page,
                size=size,
                total_pages=0,
                links={
                    "first": f"?page=1&size={size}",
                    "last": f"?page=1&size={size}",
                    "self": f"?page={page}&size={size}",
                    "next": None,
                    "prev": None,
                },
            ),
        )


@router.get("/assistant/{report_id}", summary="获取AI助手报告详情", dependencies=[DependsJwtAuth])
async def get_assistant_report_detail(
    report_id: int = Path(..., description="报告ID"), db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[dict]:
    """获取AI助手报告详情"""
    try:
        data = await assistant_report_service.get_detail(db, report_id=report_id)
        if not data:
            return response_base.fail(res=CustomResponse(code=404, msg="AI助手报告不存在"), data={})
        return response_base.success(data=data)
    except Exception as e:
        return response_base.fail(res=CustomResponse(code=500, msg=f"获取AI助手报告详情失败: {str(e)}"), data={})


# =========================== 风控报告日志 API ===========================


@router.get("/risk", summary="获取风控报告日志列表", dependencies=[DependsJwtAuth])
async def get_risk_report_logs(
    assistant_id: Optional[str] = Query(None, description="风控助手ID"),
    model_id: Optional[str] = Query(None, description="AI模型ID"),
    risk_type: Optional[RiskType] = Query(None, description="风险类型"),
    member_id: Optional[str] = Query(None, description="用户ID"),
    member_name: Optional[str] = Query(None, description="用户名称"),
    is_processed: Optional[bool] = Query(None, description="处理状态"),
    risk_level_id: Optional[str] = Query(None, description="风控等级ID列表，逗号分隔"),
    risk_tags: Optional[str] = Query(None, description="风险标签ID列表，逗号分隔"),
    # 新增增量分析过滤参数
    analysis_type: Optional[str] = Query(None, description="分析类型：STOCK=存量，INCREMENTAL=增量，TRIGGERED=触发"),
    trigger_sources: Optional[str] = Query(None, description="触发源：可包含new_register,new_login,new_transfer等"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, gt=0, le=200, description="每页数量"),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchemaModel[PageData[dict]]:
    """获取风控报告日志列表"""
    try:
        # 处理筛选参数
        risk_level_ids = None
        if risk_level_id:
            risk_level_ids = [id.strip() for id in risk_level_id.split(",") if id.strip()]

        risk_tag_ids = None
        if risk_tags:
            risk_tag_ids = [id.strip() for id in risk_tags.split(",") if id.strip()]

        data = await risk_report_service.get_paginated_list(
            db,
            assistant_id=assistant_id,
            model_id=model_id,
            risk_type=risk_type,
            member_id=member_id,
            member_name=member_name,
            is_processed=is_processed,
            risk_level_ids=risk_level_ids,
            risk_tag_ids=risk_tag_ids,
            # 新增增量分析过滤参数
            analysis_type=analysis_type,
            trigger_sources=trigger_sources,
            page=page,
            size=size,
        )
        return response_base.success(data=data)
    except Exception as e:
        return response_base.fail(
            res=CustomResponse(code=500, msg=f"获取风控报告列表失败: {str(e)}"),
            data=PageData(
                items=[],
                total=0,
                page=page,
                size=size,
                total_pages=0,
                links={
                    "first": f"?page=1&size={size}",
                    "last": f"?page=1&size={size}",
                    "self": f"?page={page}&size={size}",
                    "next": None,
                    "prev": None,
                },
            ),
        )


@router.get("/risk/{report_id}", summary="获取风控报告详情", dependencies=[DependsJwtAuth])
async def get_risk_report_detail(
    report_id: int = Path(..., description="报告ID"), db: AsyncSession = Depends(get_db)
) -> ResponseSchemaModel[dict]:
    """获取风控报告详情"""
    try:
        data = await risk_report_service.get_detail(db, report_id=report_id)
        if not data:
            return response_base.fail(res=CustomResponse(code=404, msg="风控报告不存在"), data={})
        return response_base.success(data=data)
    except Exception as e:
        return response_base.fail(res=CustomResponse(code=500, msg=f"获取风控报告详情失败: {str(e)}"), data={})


@router.put("/risk/{report_id}/process", summary="处理风控报告", dependencies=[DependsJwtAuth])
async def process_risk_report(
    report_id: int = Path(..., description="报告ID"),
    request_body: ProcessReportRequest = Body(..., description="处理请求参数"),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
) -> ResponseSchemaModel[dict]:
    """处理风控报告，更新处理结果、处理人和处理时间"""
    try:
        # 如果传了 handle_user，使用传入的值；否则从登录态获取
        if request_body.handle_user:
            handler = request_body.handle_user
            # handle_user_name 如果传了就用传的值，没传就为空（允许为空）
            handler_name = request_body.handle_user_name
        else:
            # 从JWT token中获取当前用户ID和名称作为处理人
            handler = str(request.user.id)
            handler_name = request.user.nickname or request.user.username

        data = await risk_report_service.process_report(
            db,
            report_id=report_id,
            handle_result=request_body.handle_result,
            handler=handler,
            handler_name=handler_name,
            handle_time=datetime.now(),
        )
        if not data:
            return response_base.fail(res=CustomResponse(code=404, msg="风控报告不存在"), data={"processed": False})
        return response_base.success(data={"processed": True, "report": data})
    except Exception as e:
        return response_base.fail(
            res=CustomResponse(code=500, msg=f"处理风控报告失败: {str(e)}"), data={"processed": False}
        )
