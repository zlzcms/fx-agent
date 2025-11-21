#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI助手报告用户阅读关系CRUD操作
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_crud_plus import CRUDPlus

from backend.app.admin.model.ai_assistant_report_user_read import AiAssistantReportUserRead
from backend.utils.timezone import timezone


class CRUDAiAssistantReportUserRead(CRUDPlus[AiAssistantReportUserRead]):
    """AI助手报告用户阅读关系数据库操作类"""

    async def get_user_read_status(
        self, db: AsyncSession, report_id: int, user_id: int
    ) -> AiAssistantReportUserRead | None:
        """
        获取用户对特定报告的阅读状态

        :param db: 数据库会话
        :param report_id: 报告ID
        :param user_id: 用户ID
        :return: 阅读状态记录，如果不存在则返回None
        """
        stmt = select(self.model).where(self.model.report_id == report_id, self.model.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_as_read(self, db: AsyncSession, report_id: int, user_id: int) -> AiAssistantReportUserRead:
        """
        标记用户已读报告

        :param db: 数据库会话
        :param report_id: 报告ID
        :param user_id: 用户ID
        :return: 更新后的阅读记录
        """
        # 查找现有记录
        read_record = await self.get_user_read_status(db, report_id, user_id)

        if read_record:
            # 如果记录存在，更新为已读
            read_record.is_read = True
            read_record.read_time = timezone.now()
            await db.flush()
            await db.commit()
            return read_record
        else:
            # 如果记录不存在，创建新记录
            new_record = self.model(report_id=report_id, user_id=user_id, is_read=True, read_time=timezone.now())
            db.add(new_record)
            await db.flush()
            await db.commit()
            return new_record

    async def get_user_unread_reports(
        self, db: AsyncSession, user_id: int, limit: int = 50
    ) -> list[AiAssistantReportUserRead]:
        """
        获取用户未读的报告列表

        :param db: 数据库会话
        :param user_id: 用户ID
        :param limit: 限制数量
        :return: 未读报告列表
        """
        stmt = (
            select(self.model)
            .where(self.model.user_id == user_id, self.model.is_read == False)
            .order_by(self.model.created_time.desc())
            .limit(limit)
        )

        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_report_read_users(self, db: AsyncSession, report_id: int) -> list[AiAssistantReportUserRead]:
        """
        获取已读特定报告的用户列表

        :param db: 数据库会话
        :param report_id: 报告ID
        :return: 已读用户列表
        """
        stmt = (
            select(self.model)
            .where(self.model.report_id == report_id, self.model.is_read == True)
            .order_by(self.model.read_time.desc())
        )

        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_report_read_count(self, db: AsyncSession, report_id: int) -> int:
        """
        获取特定报告的已读用户数量

        :param db: 数据库会话
        :param report_id: 报告ID
        :return: 已读用户数量
        """
        stmt = select(self.model).where(self.model.report_id == report_id, self.model.is_read == True)
        result = await db.execute(stmt)
        return len(result.scalars().all())


# 创建全局实例
ai_assistant_report_user_read_dao = CRUDAiAssistantReportUserRead(AiAssistantReportUserRead)
