#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Request

from backend.app.task.schema.scheduler import CreateTaskSchedulerParam, GetTaskSchedulerDetail, UpdateTaskSchedulerParam
from backend.app.task.service.scheduler_service import task_scheduler_service
from backend.common.pagination import DependsPagination, PageData, paging_data
from backend.common.response.response_schema import ResponseModel, ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.common.security.permission import RequestPermission
from backend.common.security.rbac import DependsRBAC
from backend.database.db import CurrentSession

router = APIRouter()


@router.get("/all", summary="获取所有任务调度", dependencies=[DependsJwtAuth])
async def get_all_task_schedulers() -> ResponseSchemaModel[list[GetTaskSchedulerDetail]]:
    schedulers = await task_scheduler_service.get_all()
    return response_base.success(data=schedulers)


@router.get("/{pk}", summary="获取任务调度详情", dependencies=[DependsJwtAuth])
async def get_task_scheduler(
    pk: Annotated[int, Path(description="任务调度 ID")],
) -> ResponseSchemaModel[GetTaskSchedulerDetail]:
    task_scheduler = await task_scheduler_service.get(pk=pk)
    return response_base.success(data=task_scheduler)


@router.get(
    "",
    summary="分页获取所有任务调度",
    dependencies=[
        DependsJwtAuth,
        DependsPagination,
    ],
)
async def get_task_scheduler_paged(
    db: CurrentSession,
    name: Annotated[int, Path(description="任务调度名称")] = None,
    type: Annotated[int | None, Query(description="任务调度类型")] = None,
) -> ResponseSchemaModel[PageData[GetTaskSchedulerDetail]]:
    task_scheduler_select = await task_scheduler_service.get_select(name=name, type=type)
    page_data = await paging_data(db, task_scheduler_select)
    return response_base.success(data=page_data)


@router.post(
    "",
    summary="创建任务调度",
    dependencies=[
        Depends(RequestPermission("sys:task:add")),
        DependsRBAC,
    ],
)
async def create_task_scheduler(request: Request, obj: CreateTaskSchedulerParam) -> ResponseModel:
    # 自动记录当前登录的后台用户ID
    try:
        obj.user_id = request.user.id
    except Exception:
        # 若取不到用户（理论上不会发生，除非禁用鉴权），保持原样
        pass
    await task_scheduler_service.create(obj=obj)
    return response_base.success()


@router.put(
    "/{pk}",
    summary="更新任务调度",
    dependencies=[
        Depends(RequestPermission("sys:task:edit")),
        DependsRBAC,
    ],
)
async def update_task_scheduler(
    pk: Annotated[int, Path(description="任务调度 ID")], obj: UpdateTaskSchedulerParam
) -> ResponseModel:
    count = await task_scheduler_service.update(pk=pk, obj=obj)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.put(
    "/{pk}/status",
    summary="更新任务调度状态",
    dependencies=[
        Depends(RequestPermission("sys:task:edit")),
        DependsRBAC,
    ],
)
async def update_task_scheduler_status(pk: Annotated[int, Path(description="任务调度 ID")]) -> ResponseModel:
    count = await task_scheduler_service.update_status(pk=pk)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.delete(
    "/{pk}",
    summary="删除任务调度",
    dependencies=[
        Depends(RequestPermission("sys:task:del")),
        DependsRBAC,
    ],
)
async def delete_task_scheduler(pk: Annotated[int, Path(description="任务调度 ID")]) -> ResponseModel:
    count = await task_scheduler_service.delete(pk=pk)
    if count > 0:
        return response_base.success()
    return response_base.fail()


@router.post(
    "/{pk}/executions",
    summary="手动执行任务",
    dependencies=[
        Depends(RequestPermission("sys:task:exec")),
        DependsRBAC,
    ],
)
async def execute_task(
    request: Request,
    pk: Annotated[int, Path(description="任务调度 ID")],
    user_id: Annotated[int | None, Query(description="执行用户ID")] = None,
    subscription_id: Annotated[int | None, Query(description="订阅ID")] = None,
) -> ResponseModel:
    # 未显式传入时，默认使用当前登录用户
    if user_id is None:
        try:
            user_id = request.user.id
        except Exception as e:
            from backend.common.exception import errors

            raise errors.AuthorizationError(msg=f"无法获取当前用户ID，请确保已登录: {str(e)}")

    result = await task_scheduler_service.execute(pk=pk, user_id=user_id, subscription_id=subscription_id)
    return response_base.success(data=result)
