#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI助手报告用户阅读关系服务（Admin）
"""

from typing import List

from fastapi import Request

from backend.app.admin.crud.crud_ai_assistant_report_user_read import ai_assistant_report_user_read_dao
from backend.app.admin.model.ai_assistant_report_user_read import AiAssistantReportUserRead
from backend.app.admin.schema.ai_assistant_report_user_read import (
    CreateAiAssistantReportUserReadParam,
    GetReportReadUsersParam,
    GetUserUnreadReportsParam,
    MarkReportAsReadParam,
)
from backend.database.db import async_db_session


class AiAssistantReportUserReadService:
    """AI助手报告用户阅读关系服务"""

    @staticmethod
    async def create(*, request: Request, obj: CreateAiAssistantReportUserReadParam) -> AiAssistantReportUserRead:
        async with async_db_session.begin() as db:
            existing_record = await ai_assistant_report_user_read_dao.get_user_read_status(
                db, obj.report_id, obj.user_id
            )
            if existing_record:
                return existing_record

            new_record = AiAssistantReportUserRead(**obj.model_dump())
            db.add(new_record)
            await db.flush()
            return new_record

    @staticmethod
    async def mark_as_read(*, request: Request, obj: MarkReportAsReadParam) -> AiAssistantReportUserRead:
        async with async_db_session.begin() as db:
            return await ai_assistant_report_user_read_dao.mark_as_read(db, obj.report_id, obj.user_id)

    @staticmethod
    async def get_user_unread_reports(
        *, request: Request, obj: GetUserUnreadReportsParam
    ) -> List[AiAssistantReportUserRead]:
        async with async_db_session() as db:
            return await ai_assistant_report_user_read_dao.get_user_unread_reports(db, obj.user_id, obj.limit)

    @staticmethod
    async def get_report_read_users(
        *, request: Request, obj: GetReportReadUsersParam
    ) -> List[AiAssistantReportUserRead]:
        async with async_db_session() as db:
            return await ai_assistant_report_user_read_dao.get_report_read_users(db, obj.report_id)

    @staticmethod
    async def get_report_read_count(*, request: Request, report_id: int) -> int:
        async with async_db_session() as db:
            return await ai_assistant_report_user_read_dao.get_report_read_count(db, report_id)

    @staticmethod
    async def get_user_read_status(
        *, request: Request, report_id: int, user_id: int
    ) -> AiAssistantReportUserRead | None:
        async with async_db_session() as db:
            return await ai_assistant_report_user_read_dao.get_user_read_status(db, report_id, user_id)
