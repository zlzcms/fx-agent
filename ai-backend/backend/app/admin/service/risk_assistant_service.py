#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.crud.crud_risk_assistant import crud_risk_assistant
from backend.app.admin.schema.risk_assistant import (
    CreateRiskAssistantParams,
    DeleteResponse,
    UpdateRiskAssistantParams,
)
from backend.common.pagination import PageData


class RiskAssistantService:
    """风控助手服务"""

    def _assistant_to_dict(self, risk_assistant: any) -> dict:
        """将风控助手转换为字典"""
        return {
            "id": risk_assistant.id,
            "name": risk_assistant.name,
            "ai_model_id": risk_assistant.ai_model_id,
            "role": risk_assistant.role,
            "background": risk_assistant.background,
            "task_prompt": risk_assistant.task_prompt,
            "variable_config": risk_assistant.variable_config,
            "report_config": risk_assistant.report_config,
            "status": risk_assistant.status,
            "setting": risk_assistant.setting,
            "risk_type": risk_assistant.risk_type,
            "created_time": risk_assistant.created_time,
            "updated_time": risk_assistant.updated_time,
        }

    async def get_paginated_list(
        self,
        db: AsyncSession,
        *,
        name: Optional[str] = None,
        ai_model_id: Optional[str] = None,
        status: Optional[bool] = None,
        page: int = 1,
        size: int = 10,
    ) -> PageData[dict]:
        """获取分页风控助手列表"""
        risk_assistants, total = await crud_risk_assistant.get_list(
            db, name=name, ai_model_id=ai_model_id, status=status, page=page, size=size
        )

        # 转换为字典
        items = [self._assistant_to_dict(assistant) for assistant in risk_assistants]

        from math import ceil

        total_pages = ceil(total / size) if total > 0 else 1

        return PageData(
            items=items,
            total=total,
            page=page,
            size=size,
            total_pages=total_pages,
            links={
                "first": f"?page=1&size={size}",
                "last": f"?page={total_pages}&size={size}",
                "self": f"?page={page}&size={size}",
                "next": f"?page={page + 1}&size={size}" if page < total_pages else None,
                "prev": f"?page={page - 1}&size={size}" if page > 1 else None,
            },
        )

    async def get_all(self, db: AsyncSession) -> List[dict]:
        """获取所有风控助手"""
        risk_assistants = await crud_risk_assistant.get_all(db)
        return [self._assistant_to_dict(assistant) for assistant in risk_assistants]

    async def get_detail(self, db: AsyncSession, *, assistant_id: str) -> Optional[dict]:
        """获取风控助手详情"""
        risk_assistant = await crud_risk_assistant.get(db, id=assistant_id)
        if not risk_assistant:
            return None
        return self._assistant_to_dict(risk_assistant)

    async def create(self, db: AsyncSession, *, request: CreateRiskAssistantParams) -> dict:
        """创建风控助手"""
        # 检查风控助手名称是否已存在
        if await crud_risk_assistant.check_name_exists(db, name=request.name):
            raise ValueError(f"风控助手名称 '{request.name}' 已存在")

        # 创建风控助手
        risk_assistant = await crud_risk_assistant.create(db, obj_in=request)
        return self._assistant_to_dict(risk_assistant)

    async def update(
        self, db: AsyncSession, *, assistant_id: str, request: UpdateRiskAssistantParams
    ) -> Optional[dict]:
        """更新风控助手"""
        # 检查风控助手是否存在
        risk_assistant = await crud_risk_assistant.get(db, id=assistant_id)
        if not risk_assistant:
            return None

        # 如果更新名称，检查是否重复
        if request.name and request.name != risk_assistant.name:
            if await crud_risk_assistant.check_name_exists(db, name=request.name, exclude_id=assistant_id):
                raise ValueError(f"风控助手名称 '{request.name}' 已存在")

        # 更新风控助手
        updated_assistant = await crud_risk_assistant.update(db, db_obj=risk_assistant, obj_in=request)
        return self._assistant_to_dict(updated_assistant)

    async def delete_batch(self, db: AsyncSession, *, ids: List[str]) -> DeleteResponse:
        """批量删除风控助手"""
        # 检查风控助手是否存在
        for assistant_id in ids:
            risk_assistant = await crud_risk_assistant.get(db, id=assistant_id)
            if not risk_assistant:
                raise ValueError(f"风控助手 ID '{assistant_id}' 不存在")

        # 批量删除
        deleted_count = await crud_risk_assistant.delete_batch(db, ids=ids)
        return DeleteResponse(deleted_count=deleted_count)

    async def update_status(self, db: AsyncSession, *, assistant_id: str, status: bool) -> Optional[dict]:
        """更新风控助手状态"""
        risk_assistant = await crud_risk_assistant.update_status(db, id=assistant_id, status=status)
        if not risk_assistant:
            return None
        return self._assistant_to_dict(risk_assistant)

    async def get_by_ai_model(self, db: AsyncSession, *, ai_model_id: str) -> List[dict]:
        """根据AI模型ID获取风控助手列表"""
        risk_assistants = await crud_risk_assistant.get_by_ai_model(db, ai_model_id=ai_model_id)
        return [self._assistant_to_dict(assistant) for assistant in risk_assistants]


risk_assistant_service = RiskAssistantService()
