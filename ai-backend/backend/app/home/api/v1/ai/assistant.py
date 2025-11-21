# -*- coding: utf-8 -*-

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.service.ai_assistant_service import AIAssistantService
from backend.common.response.response_schema import ResponseSchemaModel, response_base
from backend.database.db import get_db

router = APIRouter()


@router.get(
    "/all",
    summary="获取所有AI助手",
    description="获取所有AI助手（不分页），用于下拉选择等场景",
)
async def get_ai_assistants_for_client(
    db: AsyncSession = Depends(get_db), status: Optional[bool] = Query(None, description="状态筛选")
) -> ResponseSchemaModel[List[Dict[str, Any]]]:
    """
    获取所有AI助手（不分页）

    - **status**: 状态筛选（可选）
    """
    result = await AIAssistantService.get_all_ai_assistants(db, status=status)
    return response_base.success(data=result)
