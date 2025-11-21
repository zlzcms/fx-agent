#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Optional

from fastapi import APIRouter, Depends, Path, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.schema.api_key import (
    CreateApiKeyParams,
    DeleteApiKeyParams,
    DeleteApiKeyResponse,
    UpdateApiKeyParams,
)
from backend.app.admin.service.api_key_service import api_key_service
from backend.common.pagination import PageData
from backend.common.response.response_code import CustomResponse
from backend.common.response.response_schema import ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.common.security.rbac import DependsRBAC
from backend.database.db import get_db

router = APIRouter()


@router.get("", summary="获取API Key列表", dependencies=[DependsJwtAuth])
async def get_api_key_list(
    key_name: Optional[str] = Query(None, description="API Key名称（模糊搜索）"),
    status: Optional[int] = Query(None, description="状态(0停用 1启用)"),
    user_id: Optional[int] = Query(None, description="创建者用户ID"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, gt=0, le=200, description="每页数量"),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
) -> ResponseSchemaModel[PageData[dict]]:
    """获取API Key列表（不包含完整的API Key值，只显示前8和后8个字符）"""
    try:
        # 如果用户不是超级管理员，只能查看自己创建的API Key
        current_user_id = None if request.user.is_superuser else request.user.id
        data = await api_key_service.get_paginated_list(
            db,
            key_name=key_name,
            status=status,
            user_id=user_id or current_user_id,
            page=page,
            size=size,
            include_full_key=False,
        )
        return response_base.success(data=data)
    except Exception as e:
        return response_base.fail(
            res=CustomResponse(code=500, msg=f"获取API Key列表失败: {str(e)}"),
            data=PageData(items=[], total=0, page=page, size=size, total_pages=0, links={}),
        )


@router.get("/{api_key_id}", summary="获取API Key详情", dependencies=[DependsJwtAuth])
async def get_api_key_detail(
    api_key_id: int = Path(..., description="API Key ID"),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
) -> ResponseSchemaModel[dict]:
    """获取API Key详情（不包含完整的API Key值，只显示前8和后8个字符）"""
    try:
        data = await api_key_service.get_detail(db, api_key_id=api_key_id, include_full_key=False)
        if not data:
            return response_base.fail(res=CustomResponse(code=404, msg="API Key不存在"), data=None)

        # 如果用户不是超级管理员，只能查看自己创建的API Key
        if not request.user.is_superuser and data.get("user_id") != request.user.id:
            return response_base.fail(res=CustomResponse(code=403, msg="无权访问此API Key"), data=None)

        return response_base.success(data=data)
    except Exception as e:
        return response_base.fail(res=CustomResponse(code=500, msg=f"获取API Key详情失败: {str(e)}"), data=None)


@router.post("", summary="创建API Key", dependencies=[DependsJwtAuth])
async def create_api_key(
    obj_in: CreateApiKeyParams,
    db: AsyncSession = Depends(get_db),
    request: Request = None,
) -> ResponseSchemaModel[dict]:
    """创建API Key（仅在创建时返回完整的API Key值）"""
    try:
        data = await api_key_service.create(db, request=obj_in, user_id=request.user.id)
        return response_base.success(data=data)
    except ValueError as e:
        return response_base.fail(res=CustomResponse(code=400, msg=str(e)), data={})
    except Exception as e:
        return response_base.fail(res=CustomResponse(code=500, msg=f"创建API Key失败: {str(e)}"), data={})


@router.put("/{api_key_id}", summary="更新API Key", dependencies=[DependsJwtAuth])
async def update_api_key(
    api_key_id: int = Path(..., description="API Key ID"),
    obj_in: UpdateApiKeyParams = ...,
    db: AsyncSession = Depends(get_db),
    request: Request = None,
) -> ResponseSchemaModel[dict]:
    """更新API Key"""
    try:
        # 检查权限
        key_detail = await api_key_service.get_detail(db, api_key_id=api_key_id)
        if not key_detail:
            return response_base.fail(res=CustomResponse(code=404, msg="API Key不存在"), data=None)

        if not request.user.is_superuser and key_detail.get("user_id") != request.user.id:
            return response_base.fail(res=CustomResponse(code=403, msg="无权更新此API Key"), data=None)

        data = await api_key_service.update(db, api_key_id=api_key_id, request=obj_in)
        if not data:
            return response_base.fail(res=CustomResponse(code=404, msg="API Key不存在"), data=None)
        return response_base.success(data=data)
    except ValueError as e:
        return response_base.fail(res=CustomResponse(code=400, msg=str(e)), data=None)
    except Exception as e:
        return response_base.fail(res=CustomResponse(code=500, msg=f"更新API Key失败: {str(e)}"), data=None)


@router.delete("/{api_key_id}", summary="删除API Key", dependencies=[DependsJwtAuth])
async def delete_api_key(
    api_key_id: int = Path(..., description="API Key ID"),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
) -> ResponseSchemaModel[dict]:
    """删除API Key（软删除）"""
    try:
        key_detail = await api_key_service.get_detail(db, api_key_id=api_key_id)
        if not key_detail:
            return response_base.fail(res=CustomResponse(code=404, msg="API Key不存在"), data=None)

        if not request.user.is_superuser and key_detail.get("user_id") != request.user.id:
            return response_base.fail(res=CustomResponse(code=403, msg="无权删除此API Key"), data=None)

        success = await api_key_service.delete(db, api_key_id=api_key_id)
        if not success:
            return response_base.fail(res=CustomResponse(code=500, msg="删除API Key失败"), data=None)

        return response_base.success(data={"deleted": True})
    except Exception as e:
        return response_base.fail(res=CustomResponse(code=500, msg=f"删除API Key失败: {str(e)}"), data=None)


@router.delete("", summary="批量删除API Key", dependencies=[DependsJwtAuth, DependsRBAC])
async def delete_api_keys_batch(
    obj_in: DeleteApiKeyParams,
    db: AsyncSession = Depends(get_db),
    request: Request = None,
) -> ResponseSchemaModel[DeleteApiKeyResponse]:
    """批量删除API Key（软删除）"""
    try:
        if not request.user.is_superuser:
            # 检查所有要删除的API Key是否都属于当前用户
            keys_to_delete = []
            for key_id in obj_in.ids:
                key_detail = await api_key_service.get_detail(db, api_key_id=key_id)
                if key_detail and key_detail.get("user_id") == request.user.id:
                    keys_to_delete.append(key_id)
            data = await api_key_service.delete_batch(db, ids=keys_to_delete)
        else:
            data = await api_key_service.delete_batch(db, ids=obj_in.ids)

        return response_base.success(data=data)
    except Exception as e:
        return response_base.fail(
            res=CustomResponse(code=500, msg=f"批量删除API Key失败: {str(e)}"),
            data=DeleteApiKeyResponse(deleted_count=0),
        )
