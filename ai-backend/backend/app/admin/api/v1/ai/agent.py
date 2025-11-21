# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-29 10:00:00
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-07-05 15:47:36
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import APIRouter, Body

from backend.app.admin.schema.agent import (
    ContentPolishRequest,
    ContentPolishResponse,
    SmartAssistantCreateRequest,
    SmartAssistantCreateResponse,
)
from backend.app.admin.service.agent_service import agent_service
from backend.common.response.response_schema import ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth

router = APIRouter()


@router.post("/smart-create-assistant", dependencies=[DependsJwtAuth])
async def smart_create_assistant(
    request: SmartAssistantCreateRequest = Body(...),
) -> ResponseSchemaModel[SmartAssistantCreateResponse]:
    """
    智能创建助手

    根据业务场景、数据源、分析需求等信息，智能生成助手配置和提示词模板
    """
    result = await agent_service.create_assistant(request=request)

    return response_base.success(data=result)


@router.post("/polish-content", dependencies=[DependsJwtAuth])
async def polish_content(request: ContentPolishRequest = Body(...)) -> ResponseSchemaModel[ContentPolishResponse]:
    """
    AI内容润色

    对输入的内容进行AI润色，支持多种润色类型和长度调整

    """
    result = await agent_service.polish_content(request=request)

    return response_base.success(data=result)
