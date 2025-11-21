#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Annotated

from fastapi import APIRouter, Path, Query, Request

from backend.app.admin.schema.recommended_question import (
    CreateRecommendedQuestionParam,
    DeleteRecommendedQuestionParam,
    GetRecommendedQuestionDetail,
    GetRecommendedQuestionsByRoleResult,
    UpdateRecommendedQuestionParam,
)
from backend.app.admin.service.recommended_question_service import recommended_question_service
from backend.app.admin.service.user_service import user_service
from backend.common.pagination import DependsPagination, PageData, paging_data
from backend.common.response.response_schema import ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.common.security.rbac import DependsRBAC
from backend.database.db import CurrentSession

router = APIRouter()


@router.get("/by-roles", summary="根据用户角色获取推荐问法", dependencies=[DependsJwtAuth])
async def get_questions_by_roles(
    db: CurrentSession,
    role_ids: Annotated[str, Query(description="角色ID列表，逗号分隔")],
    limit: Annotated[int, Query(description="返回数量限制", ge=1, le=10)] = 3,
) -> ResponseSchemaModel[list[GetRecommendedQuestionsByRoleResult]]:
    """根据用户角色获取推荐问法"""
    role_id_list = [int(rid.strip()) for rid in role_ids.split(",") if rid.strip()]
    data = await recommended_question_service.get_questions_by_roles(db, role_id_list, limit)
    return response_base.success(data=data)


@router.get("/for-current-user", summary="获取当前用户对应的推荐问法", dependencies=[DependsJwtAuth])
async def get_questions_for_current_user(
    request: Request,
    db: CurrentSession,
    limit: Annotated[int, Query(description="返回数量限制", ge=1, le=10)] = 3,
) -> ResponseSchemaModel[list[GetRecommendedQuestionsByRoleResult]]:
    """根据当前用户角色获取推荐问法"""
    user_id = request.user.id
    roles = await user_service.get_roles(pk=user_id)
    role_id_list = [role.id for role in roles] if roles else []
    data = await recommended_question_service.get_questions_by_roles(db, role_id_list, limit)
    return response_base.success(data=data)


@router.get("/{pk}", summary="获取推荐问法详情", dependencies=[DependsJwtAuth])
async def get_recommended_question(
    db: CurrentSession,
    pk: Annotated[int, Path(description="推荐问法 ID")],
) -> ResponseSchemaModel[GetRecommendedQuestionDetail]:
    """获取推荐问法详情"""
    data = await recommended_question_service.get_recommended_question(db, pk=pk)
    return response_base.success(data=data)


@router.get("", summary="获取推荐问法列表", dependencies=[DependsJwtAuth, DependsPagination])
async def get_recommended_questions(
    db: CurrentSession,
    title: Annotated[str | None, Query(description="标题")] = None,
    status: Annotated[int | None, Query(description="状态")] = None,
    is_default: Annotated[bool | None, Query(description="是否默认")] = None,
) -> ResponseSchemaModel[PageData[GetRecommendedQuestionDetail]]:
    """获取推荐问法列表"""
    config_select = recommended_question_service.get_select(title=title, status=status, is_default=is_default)
    page_data = await paging_data(db, config_select)
    return response_base.success(data=page_data)


@router.post("", summary="创建推荐问法", dependencies=[DependsJwtAuth, DependsRBAC])
async def create_recommended_question(
    db: CurrentSession,
    data: CreateRecommendedQuestionParam,
) -> ResponseSchemaModel[GetRecommendedQuestionDetail]:
    """创建推荐问法"""
    obj = await recommended_question_service.create_recommended_question(db, obj_in=data)
    return response_base.success(data=obj)


@router.put("/{pk}", summary="更新推荐问法", dependencies=[DependsJwtAuth, DependsRBAC])
async def update_recommended_question(
    db: CurrentSession,
    pk: Annotated[int, Path(description="推荐问法 ID")],
    data: UpdateRecommendedQuestionParam,
) -> ResponseSchemaModel[GetRecommendedQuestionDetail]:
    """更新推荐问法"""
    obj = await recommended_question_service.update_recommended_question(db, pk=pk, obj_in=data)
    return response_base.success(data=obj)


@router.delete("/{pk}", summary="删除推荐问法", dependencies=[DependsJwtAuth, DependsRBAC])
async def delete_recommended_question(
    db: CurrentSession,
    pk: Annotated[int, Path(description="推荐问法 ID")],
) -> ResponseSchemaModel[None]:
    """删除推荐问法"""
    await recommended_question_service.delete_recommended_question(db, pk=pk)
    return response_base.success()


@router.delete("", summary="批量删除推荐问法", dependencies=[DependsJwtAuth, DependsRBAC])
async def delete_recommended_questions(
    db: CurrentSession,
    data: DeleteRecommendedQuestionParam,
) -> ResponseSchemaModel[None]:
    """批量删除推荐问法"""
    await recommended_question_service.delete_recommended_questions(db, pks=data.pks)
    return response_base.success()
