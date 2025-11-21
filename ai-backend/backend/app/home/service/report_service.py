#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Literal

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.model.ai_assistant_report_log import AiAssistantReportLog
from backend.app.admin.model.ai_assistant_report_user_read import AiAssistantReportUserRead
from backend.app.admin.model.ai_subscription import AISubscription


class HomeReportService:
    @staticmethod
    async def list_reports_for_user(
        db: AsyncSession,
        *,
        user_id: int,
        status: Literal["all", "read", "unread"] = "all",
        assistant_id: str | None = None,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[list[tuple[AiAssistantReportLog, bool, str]], int]:
        conditions = [AiAssistantReportUserRead.user_id == user_id]
        if status == "read":
            conditions.append(AiAssistantReportUserRead.is_read.is_(True))
        elif status == "unread":
            conditions.append(AiAssistantReportUserRead.is_read.is_(False))

        if assistant_id is not None:
            conditions.append(AiAssistantReportLog.assistant_id == assistant_id)

        # 统计总数
        count_stmt = (
            select(AiAssistantReportLog.id)
            .join(AiAssistantReportUserRead, AiAssistantReportUserRead.report_id == AiAssistantReportLog.id)
            .outerjoin(AISubscription, AISubscription.id == AiAssistantReportLog.subscription_id)
            .where(and_(*conditions))
        )
        total = len((await db.execute(count_stmt)).scalars().all())

        # 分页查询，同时获取报告、阅读状态和订阅名称
        stmt = (
            select(AiAssistantReportLog, AiAssistantReportUserRead.is_read, AISubscription.name)
            .join(AiAssistantReportUserRead, AiAssistantReportUserRead.report_id == AiAssistantReportLog.id)
            .outerjoin(AISubscription, AISubscription.id == AiAssistantReportLog.subscription_id)
            .where(and_(*conditions))
            .order_by(AiAssistantReportLog.created_time.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        items = result.all()  # 返回 (report, is_read, subscription_name) 的元组列表
        return items, total
