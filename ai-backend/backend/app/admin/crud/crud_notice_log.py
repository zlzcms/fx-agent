#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import Select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_crud_plus import CRUDPlus

from backend.app.admin.model.notice_log import NoticeLog
from backend.app.admin.schema.notice_log import CreateNoticeLogParam, UpdateNoticeLogParam


class CRUDNoticeLog(CRUDPlus[NoticeLog]):
    """通知日志CRUD操作类"""

    async def get(self, db: AsyncSession, pk: int) -> NoticeLog | None:
        """
        获取通知日志详情

        :param db: 数据库会话
        :param pk: 通知日志 ID
        :return:
        """
        return await self.select_model_by_column(db, id=pk)

    async def get_all(self, db: AsyncSession) -> Sequence[NoticeLog]:
        """
        获取所有通知日志

        :param db: 数据库会话
        :return:
        """
        return await self.select_models(db)

    async def get_list(
        self,
        *,
        description: Optional[str] = None,
        notification_type: Optional[str] = None,
        is_success: Optional[bool] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Select:
        """
        获取通知日志列表查询对象

        :param description: 通知描述关键字
        :param notification_type: 通知方式筛选
        :param is_success: 成功状态筛选
        :param start_time: 开始时间
        :param end_time: 结束时间
        :return:
        """
        filters = {}

        if description:
            filters["description__like"] = f"%{description}%"

        if notification_type:
            filters["notification_type"] = notification_type

        if is_success is not None:
            filters["is_success"] = is_success

        # 处理时间范围筛选
        conditions = []
        if start_time:
            conditions.append(self.model.created_time >= start_time)
        if end_time:
            conditions.append(self.model.created_time <= end_time)

        if conditions:
            # 需要自定义查询以处理时间范围
            query = self.select_model().where(and_(*conditions))

            # 添加其他筛选条件
            for key, value in filters.items():
                if "__like" in key:
                    field_name = key.replace("__like", "")
                    field = getattr(self.model, field_name)
                    query = query.where(field.like(value))
                else:
                    field = getattr(self.model, key)
                    query = query.where(field == value)

            return query.order_by(desc(self.model.created_time))
        else:
            # 使用基类的筛选方法
            return await self.select_order("created_time", "desc", **filters)

    async def create(self, db: AsyncSession, obj: CreateNoticeLogParam) -> None:
        """
        创建通知日志

        :param db: 数据库会话
        :param obj: 创建通知日志参数
        :return:
        """
        await self.create_model(db, obj)

    async def update(self, db: AsyncSession, pk: int, obj: UpdateNoticeLogParam) -> int:
        """
        更新通知日志

        :param db: 数据库会话
        :param pk: 通知日志 ID
        :param obj: 更新通知日志参数
        :return:
        """
        return await self.update_model(db, pk, obj)

    async def delete(self, db: AsyncSession, pks: list[int]) -> int:
        """
        批量删除通知日志

        :param db: 数据库会话
        :param pks: 通知日志 ID 列表
        :return:
        """
        return await self.delete_model_by_column(db, allow_multiple=True, id__in=pks)

    async def get_by_notification_type(self, db: AsyncSession, notification_type: str) -> Sequence[NoticeLog]:
        """
        根据通知方式获取日志

        :param db: 数据库会话
        :param notification_type: 通知方式
        :return:
        """
        return await self.select_models(db, notification_type=notification_type)

    async def get_failed_logs(self, db: AsyncSession) -> Sequence[NoticeLog]:
        """
        获取失败的通知日志

        :param db: 数据库会话
        :return:
        """
        return await self.select_models(db, is_success=False)


notice_log_dao: CRUDNoticeLog = CRUDNoticeLog(NoticeLog)
