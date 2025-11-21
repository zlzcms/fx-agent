#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Query

from backend.app.task.schema.execution import (
    DeleteTaskSchedulerExecutionParam,
    UpdateTaskSchedulerExecutionParam,
)
from backend.app.task.service.execution_service import task_scheduler_execution_service
from backend.common.pagination import DependsPagination, paging_data
from backend.common.response.response_schema import ResponseModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.database.db import CurrentSession

router = APIRouter()


@router.get("/{pk}", summary="获取任务调度执行记录详情", dependencies=[DependsJwtAuth])
async def get_task_scheduler_execution(pk: int) -> ResponseModel:
    execution = await task_scheduler_execution_service.get(pk=pk)
    return response_base.success(data=execution)


@router.get("/{pk}/real-time", summary="获取任务调度执行记录详情（包含实时状态）", dependencies=[DependsJwtAuth])
async def get_task_scheduler_execution_with_real_time_status(pk: int) -> ResponseModel:
    """获取执行记录详情，包含Celery任务的实时状态信息"""
    execution = await task_scheduler_execution_service.get_with_real_time_status(pk=pk)
    return response_base.success(data=execution)


@router.get("", summary="获取任务调度执行记录列表", dependencies=[DependsPagination])
async def get_task_scheduler_executions(
    db: CurrentSession,
    scheduler_id: Annotated[int | None, Query(description="任务调度ID")] = None,
    user_id: Annotated[int | None, Query(description="用户ID")] = None,
    status: Annotated[str | None, Query(description="执行状态")] = None,
    start_time: Annotated[datetime | None, Query(description="开始时间")] = None,
    end_time: Annotated[datetime | None, Query(description="结束时间")] = None,
    real_time: Annotated[bool, Query(description="是否获取实时状态")] = False,
) -> ResponseModel:
    if real_time:
        # 获取实时状态（暂时不支持分页和过滤，直接返回所有记录）
        executions = await task_scheduler_execution_service.get_all_with_real_time_status()
        # 简单的过滤逻辑
        if scheduler_id:
            executions = [e for e in executions if e["scheduler_id"] == scheduler_id]
        if user_id:
            executions = [e for e in executions if e["user_id"] == user_id]
        if status:
            executions = [e for e in executions if e["status"] == status]

        return response_base.success(
            data={"items": executions, "total": len(executions), "page": 1, "size": len(executions), "pages": 1}
        )
    else:
        # 原有的分页查询逻辑
        select = task_scheduler_execution_service.get_select(
            scheduler_id=scheduler_id,
            user_id=user_id,
            status=status,
            start_time=start_time,
            end_time=end_time,
        )
        page_data = await paging_data(db, select)
        return response_base.success(data=page_data)


@router.post("/sync/{celery_task_id}", summary="同步任务调度执行记录状态", dependencies=[DependsJwtAuth])
async def sync_task_scheduler_execution_status(celery_task_id: str) -> ResponseModel:
    """同步数据库状态与Celery任务状态"""
    success = await task_scheduler_execution_service.sync_status_with_celery(celery_task_id=celery_task_id)
    if success:
        return response_base.success(msg="状态同步成功")
    else:
        return response_base.fail(msg="状态同步失败")


@router.put("/{celery_task_id}", summary="更新任务调度执行记录状态", dependencies=[DependsJwtAuth])
async def update_task_scheduler_execution_status(
    celery_task_id: str, obj: UpdateTaskSchedulerExecutionParam
) -> ResponseModel:
    count = await task_scheduler_execution_service.update_status(
        celery_task_id=celery_task_id,
        status=obj.status,
        result=obj.result,
        error_message=obj.error_message,
        worker_name=obj.worker_name,
        retries=obj.retries,
    )
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.delete("/{pk}", summary="删除任务调度执行记录", dependencies=[DependsJwtAuth])
async def delete_task_scheduler_execution(pk: int) -> ResponseModel:
    count = await task_scheduler_execution_service.delete(pk=pk)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.delete("", summary="批量删除任务调度执行记录", dependencies=[DependsJwtAuth])
async def delete_task_scheduler_executions(obj: DeleteTaskSchedulerExecutionParam) -> ResponseModel:
    count = await task_scheduler_execution_service.delete_batch(pks=obj.pks)
    if count > 0:
        return response_base.success()
    return response_base.fail()
