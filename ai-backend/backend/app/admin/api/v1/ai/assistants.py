from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.schema.ai_assistant import (
    AIAssistantCreate,
    AIAssistantQueryParams,
    AIAssistantUpdate,
    AIDataPermissionInDB,
    AINotificationMethodInDB,
    BatchDeleteRequest,
    CloneRequest,
    ToggleTemplateStatusRequest,
)
from backend.app.admin.schema.user import GetUserInfoDetail
from backend.app.admin.service.ai_assistant_service import AIAssistantService
from backend.app.admin.service.warehouse_user_service import warehouse_user_service
from backend.common.pagination import PageData
from backend.common.response.response_schema import ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.database.db import get_db

router = APIRouter()


@router.get(
    "", summary="获取AI助手列表", description="获取AI助手列表，支持分页和条件筛选", dependencies=[DependsJwtAuth]
)
async def get_ai_assistants(
    *,
    db: AsyncSession = Depends(get_db),
    name: Optional[str] = Query(None, description="助手名称"),
    assistant_type_id: Optional[str] = Query(None, description="助手类型"),
    ai_model_id: Optional[str] = Query(None, description="AI模型ID"),
    responsible_person: Optional[str] = Query(None, description="负责人员"),
    status: Optional[bool] = Query(None, description="状态"),
    is_template: Optional[bool] = Query(None, description="是否为模板"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
) -> ResponseSchemaModel[PageData[Dict[str, Any]]]:
    """
    获取AI助手列表

    查询参数说明：
    - **name**: 助手名称（模糊搜索）
    - **type**: 助手类型
    - **ai_model_id**: AI模型ID
    - **responsible_person**: 负责人员（模糊搜索）
    - **status**: 状态筛选
    - **is_template**: 是否为模板
    - **page**: 页码，从1开始
    - **size**: 每页数量，最大100
    """
    params = AIAssistantQueryParams(
        name=name,
        assistant_type_id=assistant_type_id,
        ai_model_id=ai_model_id,
        responsible_person=responsible_person,
        status=status,
        is_template=is_template,
    )

    data = await AIAssistantService.get_ai_assistant_list(
        db,
        params=params,
        page=page,
        size=size,
    )
    return response_base.success(data=data)


@router.get(
    "/all",
    summary="获取所有AI助手",
    description="获取所有AI助手（不分页），用于下拉选择等场景",
    dependencies=[DependsJwtAuth],
)
async def get_all_ai_assistants(
    db: AsyncSession = Depends(get_db), status: Optional[bool] = Query(None, description="状态筛选")
) -> ResponseSchemaModel[List[Dict[str, Any]]]:
    """
    获取所有AI助手（不分页）

    - **status**: 状态筛选（可选）
    """
    result = await AIAssistantService.get_all_ai_assistants(db, status=status)
    return response_base.success(data=result)


@router.get(
    "/get_members",
    summary="获取客户",
    description="获取客户",
    dependencies=[DependsJwtAuth],
)
async def get_members(
    dataSourceLimit: dict = Path(..., description="数据源限制配置"),
) -> ResponseSchemaModel[list]:
    """
    获取客户

    - **dataSourceLimit**: 数据源限制配置（路径参数）

    返回客户列表
    """
    member_ids = await warehouse_user_service.get_need_analyzed_user_ids(dataSourceLimit)
    return response_base.success(data=member_ids)


@router.get(
    "/options/types",
    summary="获取AI助手类型选项",
    description="获取可用的AI助手类型列表",
    dependencies=[DependsJwtAuth],
)
async def get_ai_assistant_types(
    db: AsyncSession = Depends(get_db),
) -> ResponseSchemaModel[List[Dict[str, str]]]:
    """
    获取AI助手类型选项

    返回可用的助手类型列表，用于下拉选择
    """
    result = await AIAssistantService.get_ai_assistant_types(db)
    return response_base.success(data=result)


@router.get("/personnel/all", summary="获取所有人员", description="获取所有可用人员列表", dependencies=[DependsJwtAuth])
async def get_all_personnel(
    db: AsyncSession = Depends(get_db), status: Optional[bool] = Query(None, description="状态筛选")
) -> ResponseSchemaModel[List[GetUserInfoDetail]]:
    """
    获取所有人员列表

    - **status**: 状态筛选（可选）

    返回所有可用人员信息，用于助手配置中的人员选择
    """
    from backend.app.admin.service.ai_assistant_service import get_all_personnel

    try:
        result = await get_all_personnel(db, status=status)
        return response_base.success(data=result)
    except Exception as e:
        print(f"获取人员列表失败: {e}")
        return response_base.success(data=[])


@router.get(
    "/notification-methods",
    name="assistants_get_notification_methods",
    summary="获取通知方式",
    description="获取所有可用的通知方式",
    dependencies=[DependsJwtAuth],
)
async def assistants_get_notification_methods(
    db: AsyncSession = Depends(get_db),
) -> ResponseSchemaModel[List[AINotificationMethodInDB]]:
    """
    获取通知方式列表

    返回所有可用的通知方式配置，用于助手配置中的通知方式选择
    """
    from backend.app.admin.service.ai_assistant_service import AINotificationMethodService

    try:
        result = await AINotificationMethodService.get_notification_methods(db)
        return response_base.success(data=result)
    except Exception as e:
        print(f"获取通知方式列表失败: {e}")
        return response_base.success(data=[])


@router.get(
    "/data-permissions", summary="获取数据权限", description="获取所有可用的数据权限配置", dependencies=[DependsJwtAuth]
)
async def get_data_permissions(
    db: AsyncSession = Depends(get_db),
) -> ResponseSchemaModel[List[AIDataPermissionInDB]]:
    """
    获取数据权限列表

    返回所有可用的数据权限配置
    """
    from backend.app.admin.service.ai_assistant_service import AIDataPermissionService

    try:
        result = await AIDataPermissionService.get_data_permissions(db)
        return response_base.success(data=result)
    except Exception as e:
        print(f"获取数据权限列表失败: {e}")
        return response_base.success(data=[])


# 模板管理相关接口 - 放在 /{id} 路由之前
@router.get(
    "/templates",
    summary="获取AI助手模板列表",
    description="获取所有AI助手模板列表，支持分页",
    dependencies=[DependsJwtAuth],
)
async def get_ai_assistant_template_list(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, description="页码", ge=1),
    size: int = Query(10, description="每页数量", ge=1, le=100),
) -> ResponseSchemaModel[PageData[Dict[str, Any]]]:
    """
    获取AI助手模板列表

    - **page**: 页码
    - **size**: 每页数量

    返回所有设置为模板的AI助手信息，包括：
    - 头像
    - 助手名称
    - 助手类型
    - 使用模型
    - 描述
    - 开启状态
    """
    result = await AIAssistantService.get_ai_assistant_template_list(db, page=page, size=size)
    return response_base.success(data=result)


@router.patch("/{id}/status", summary="切换AI助手状态", description="启用或禁用AI助手", dependencies=[DependsJwtAuth])
async def toggle_ai_assistant_status(
    *,
    id: str = Path(..., description="AI助手ID"),
    db: AsyncSession = Depends(get_db),
    status: bool = Query(..., description="目标状态"),
) -> ResponseSchemaModel[Dict[str, Any]]:
    """
    切换AI助手状态

    - **id**: AI助手ID
    - **status**: 目标状态
    """
    result = await AIAssistantService.toggle_ai_assistant_status(db, id=id, status=status)
    return response_base.success(data=result)


@router.post(
    "/{id}/clone", summary="克隆AI助手", description="克隆现有AI助手创建新的助手", dependencies=[DependsJwtAuth]
)
async def clone_ai_assistant(
    *, id: str = Path(..., description="要克隆的AI助手ID"), db: AsyncSession = Depends(get_db), request: CloneRequest
) -> ResponseSchemaModel[Dict[str, Any]]:
    """
    克隆AI助手

    - **id**: 要克隆的AI助手ID
    - **name**: 新助手名称
    """
    result = await AIAssistantService.clone_ai_assistant(db, id=id, new_name=request.name)
    return response_base.success(data=result)


@router.put(
    "/{id}/template/status",
    summary="切换AI助手模板开启状态",
    description="切换指定AI助手模板的开启状态",
    dependencies=[DependsJwtAuth],
)
async def toggle_ai_assistant_template_status(
    *,
    id: str = Path(..., description="AI助手ID"),
    db: AsyncSession = Depends(get_db),
    request: ToggleTemplateStatusRequest,
) -> ResponseSchemaModel[Dict[str, Any]]:
    """
    切换AI助手模板开启状态

    - **id**: AI助手ID
    - **is_open**: 模板开启状态
    """
    result = await AIAssistantService.toggle_ai_assistant_template_status(db, id=id, is_open=request.is_open)
    return response_base.success(data=result)


@router.get(
    "/{id}/training-logs",
    summary="获取AI助手训练日志",
    description="获取指定AI助手的训练日志记录",
    dependencies=[DependsJwtAuth],
)
async def get_ai_assistant_training_logs(
    *,
    id: str = Path(..., description="AI助手ID"),
    db: AsyncSession = Depends(get_db),
    log_type: Optional[str] = Query(None, description="日志类型"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
) -> ResponseSchemaModel[Dict[str, Any]]:
    """
    获取AI助手训练日志

    - **id**: AI助手ID
    - **page**: 页码，从1开始
    - **size**: 每页数量，最大100

    返回该助手的模拟训练记录
    """

    result = await AIAssistantService.get_assistant_training_logs(
        db, assistant_id=id, page=page, size=size, log_type=log_type
    )
    return response_base.success(data=result)


# 现在将 /{id} 路由放在具体路径之后
@router.get("/{id}", summary="获取AI助手详情", description="根据ID获取AI助手详情信息", dependencies=[DependsJwtAuth])
async def get_ai_assistant(
    id: str = Path(..., description="AI助手ID"),
    db: AsyncSession = Depends(get_db),
) -> ResponseSchemaModel[Dict[str, Any]]:
    """
    获取AI助手详情

    - **id**: AI助手ID
    """
    result = await AIAssistantService.get_ai_assistant(db, id=id)
    return response_base.success(data=result)


@router.post("", summary="创建AI助手", description="创建新的AI助手", dependencies=[DependsJwtAuth])
async def create_ai_assistant(
    *, db: AsyncSession = Depends(get_db), obj_in: AIAssistantCreate
) -> ResponseSchemaModel[Dict[str, Any]]:
    """
    创建AI助手
    """
    result = await AIAssistantService.create_ai_assistant(db, obj_in=obj_in)
    return response_base.success(data=result)


@router.put("/{id}", summary="更新AI助手", description="更新AI助手信息", dependencies=[DependsJwtAuth])
async def update_ai_assistant(
    *, id: str = Path(..., description="AI助手ID"), db: AsyncSession = Depends(get_db), obj_in: AIAssistantUpdate
) -> ResponseSchemaModel[Dict[str, Any]]:
    """
    更新AI助手

    - **id**: AI助手ID
    """
    result = await AIAssistantService.update_ai_assistant(db, id=id, obj_in=obj_in)
    return response_base.success(data=result)


@router.delete("", summary="批量删除AI助手", description="批量删除AI助手", dependencies=[DependsJwtAuth])
async def delete_ai_assistants(
    *, db: AsyncSession = Depends(get_db), request: BatchDeleteRequest
) -> ResponseSchemaModel[Dict[str, Any]]:
    """
    批量删除AI助手
    """
    result = await AIAssistantService.delete_ai_assistant(db, ids=request.ids)
    return response_base.success(data=result)
