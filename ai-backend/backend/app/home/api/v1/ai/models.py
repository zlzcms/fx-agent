#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.model import User
from backend.app.home.api.deps import get_optional_home_user
from backend.app.home.schema.ai_model import AIModelResponse
from backend.app.home.service.ai_model_service import ai_model_service
from backend.database.db import get_db

router = APIRouter()


@router.get("", response_model=List[AIModelResponse])
async def get_models(
    request: Request, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_optional_home_user)
):
    """
    获取所有启用的AI模型列表

    此接口不需要认证，任何用户都可以访问
    如果用户已登录，会记录用户信息用于统计
    """
    try:
        # 获取模型列表，无论用户是否登录
        models = await ai_model_service.get_all_enabled_models(db)
        return models
    except Exception as e:
        print(f"获取模型列表时出错: {str(e)}")
        # 返回空列表而不是抛出异常
        return []


@router.get("/{model_id}", response_model=AIModelResponse)
async def get_model_detail(
    request: Request,
    model_id: str = Path(..., description="模型ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_optional_home_user),
):
    """
    获取AI模型详情

    此接口不需要认证，任何用户都可以访问
    如果用户已登录，会记录用户信息用于统计
    """
    try:
        model = await ai_model_service.get_model_by_id(db, model_id=model_id)
        if not model:
            raise HTTPException(status_code=404, detail="模型不存在")
        if not model.status:
            raise HTTPException(status_code=404, detail="模型已禁用")
        return model
    except HTTPException:
        raise
    except Exception as e:
        print(f"获取模型详情时出错: {str(e)}")
        raise HTTPException(status_code=500, detail="服务器内部错误")
