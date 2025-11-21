#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Body, Depends, Path, Query

from backend.app.admin.schema.notice_log import (
    CreateNoticeLogParam,
    GetNoticeLogDetail,
    UpdateNoticeLogParam,
)
from backend.app.admin.service.notice_log_service import notice_log_service
from backend.common.pagination import DependsPagination, PageData, paging_data
from backend.common.response.response_schema import ResponseModel, ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.common.security.permission import RequestPermission
from backend.common.security.rbac import DependsRBAC
from backend.database.db import CurrentSession

router = APIRouter()


@router.get(
    "",
    summary="分页获取通知日志列表",
    dependencies=[
        DependsJwtAuth,
        DependsPagination,
    ],
)
async def get_notice_logs_paged(
    db: CurrentSession,
    description: Annotated[Optional[str], Query(description="通知描述关键字")] = None,
    notification_type: Annotated[Optional[str], Query(description="通知方式筛选")] = None,
    is_success: Annotated[Optional[bool], Query(description="成功状态筛选")] = None,
    start_time: Annotated[Optional[datetime], Query(description="开始时间")] = None,
    end_time: Annotated[Optional[datetime], Query(description="结束时间")] = None,
) -> ResponseSchemaModel[PageData[GetNoticeLogDetail]]:
    """分页获取通知日志列表"""
    notice_log_select = await notice_log_service.get_select(
        description=description,
        notification_type=notification_type,
        is_success=is_success,
        start_time=start_time,
        end_time=end_time,
    )
    page_data = await paging_data(db, notice_log_select)
    return response_base.success(data=page_data)


@router.get("/{pk}", summary="获取通知日志详情", dependencies=[DependsJwtAuth])
async def get_notice_log(
    pk: Annotated[int, Path(description="通知日志 ID")],
) -> ResponseSchemaModel[GetNoticeLogDetail]:
    """获取通知日志详情"""
    notice_log = await notice_log_service.get(pk=pk)
    return response_base.success(data=notice_log)


@router.get("/all", summary="获取所有通知日志", dependencies=[DependsJwtAuth])
async def get_all_notice_logs() -> ResponseSchemaModel[list[GetNoticeLogDetail]]:
    """获取所有通知日志"""
    notice_logs = await notice_log_service.get_all()
    return response_base.success(data=notice_logs)


@router.get("/failed", summary="获取失败的通知日志", dependencies=[DependsJwtAuth])
async def get_failed_notice_logs() -> ResponseSchemaModel[list[GetNoticeLogDetail]]:
    """获取失败的通知日志"""
    failed_logs = await notice_log_service.get_failed_logs()
    return response_base.success(data=failed_logs)


@router.get("/by-type/{notification_type}", summary="根据通知方式获取日志", dependencies=[DependsJwtAuth])
async def get_notice_logs_by_type(
    notification_type: Annotated[str, Path(description="通知方式")],
) -> ResponseSchemaModel[list[GetNoticeLogDetail]]:
    """根据通知方式获取日志"""
    notice_logs = await notice_log_service.get_by_notification_type(notification_type=notification_type)
    return response_base.success(data=notice_logs)


@router.post(
    "",
    summary="创建通知日志",
    dependencies=[
        Depends(RequestPermission("sys:notice-log:add")),
        DependsRBAC,
    ],
)
async def create_notice_log(obj: CreateNoticeLogParam) -> ResponseModel:
    """创建通知日志"""
    await notice_log_service.create(obj=obj)
    return response_base.success()


@router.put(
    "/{pk}",
    summary="更新通知日志",
    dependencies=[
        Depends(RequestPermission("sys:notice-log:edit")),
        DependsRBAC,
    ],
)
async def update_notice_log(
    pk: Annotated[int, Path(description="通知日志 ID")], obj: UpdateNoticeLogParam
) -> ResponseModel:
    """更新通知日志"""
    count = await notice_log_service.update(pk=pk, obj=obj)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.delete(
    "",
    summary="批量删除通知日志",
    dependencies=[
        Depends(RequestPermission("sys:notice-log:del")),
        DependsRBAC,
    ],
)
async def delete_notice_logs(pks: Annotated[list[int], Body(description="通知日志 ID 列表")]) -> ResponseModel:
    """批量删除通知日志"""
    count = await notice_log_service.delete(pks=pks)
    if count > 0:
        return response_base.success()
    return response_base.fail()
