#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Path, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.crud.crud_ai_assistant_report_user_read import ai_assistant_report_user_read_dao
from backend.app.home.api.deps import get_current_home_user
from backend.app.home.schema.report import ReportItem, ReportListResponse
from backend.app.home.service.report_service import HomeReportService
from backend.common.response.response_schema import ResponseSchemaModel, response_base
from backend.database.db import get_db

router = APIRouter()


@router.get("", response_model=ResponseSchemaModel[ReportListResponse])
async def list_my_reports(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_home_user),
    status: Literal["all", "read", "unread"] = Query("all", description="报告状态筛选"),
    assistant_id: str | None = Query(None, description="助手ID筛选"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
) -> ResponseSchemaModel:
    skip = (page - 1) * size
    items, total = await HomeReportService.list_reports_for_user(
        db, user_id=current_user.id, status=status, assistant_id=assistant_id, skip=skip, limit=size
    )
    from math import ceil

    total_pages = ceil(total / size) if total > 0 else 1

    data = ReportListResponse(
        items=[
            ReportItem(
                id=report.id,
                assistant_id=report.assistant_id,
                model_id=report.model_id,
                subscription_id=report.subscription_id,
                subscription_name=subscription_name,
                report_score=report.report_score,
                report_result=report.report_result,
                created_time=report.created_time,
                is_read=is_read,
            )
            for report, is_read, subscription_name in items
        ],
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
    return response_base.success(data=data)


@router.post("/{report_id}/read", response_model=ResponseSchemaModel[bool])
async def mark_my_report_as_read(
    request: Request,
    report_id: Annotated[int, Path(description="报告ID")],
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_home_user),
) -> ResponseSchemaModel:
    await ai_assistant_report_user_read_dao.mark_as_read(db, report_id, current_user.id)
    return response_base.success(data=True)
