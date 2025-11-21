#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import Select

from backend.app.admin.crud.crud_notice_log import notice_log_dao
from backend.app.admin.model.notice_log import NoticeLog
from backend.app.admin.schema.notice_log import CreateNoticeLogParam, UpdateNoticeLogParam
from backend.common.exception import errors
from backend.database.db import async_db_session


class NoticeLogService:
    """通知日志服务类"""

    @staticmethod
    async def get(*, pk: int) -> NoticeLog:
        """
        获取通知日志详情

        :param pk: 通知日志 ID
        :return:
        """
        async with async_db_session() as db:
            notice_log = await notice_log_dao.get(db, pk)
            if not notice_log:
                raise errors.NotFoundError(msg="通知日志不存在")
            return notice_log

    @staticmethod
    async def get_select(
        *,
        description: Optional[str] = None,
        notification_type: Optional[str] = None,
        is_success: Optional[bool] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Select:
        """
        获取通知日志查询对象

        :param description: 通知描述关键字
        :param notification_type: 通知方式筛选
        :param is_success: 成功状态筛选
        :param start_time: 开始时间
        :param end_time: 结束时间
        :return:
        """
        return await notice_log_dao.get_list(
            description=description,
            notification_type=notification_type,
            is_success=is_success,
            start_time=start_time,
            end_time=end_time,
        )

    @staticmethod
    async def get_all() -> Sequence[NoticeLog]:
        """获取所有通知日志"""
        async with async_db_session() as db:
            notice_logs = await notice_log_dao.get_all(db)
            return notice_logs

    @staticmethod
    async def create(*, obj: CreateNoticeLogParam) -> None:
        """
        创建通知日志

        :param obj: 创建通知日志参数
        :return:
        """
        async with async_db_session.begin() as db:
            await notice_log_dao.create(db, obj)

    @staticmethod
    async def update(*, pk: int, obj: UpdateNoticeLogParam) -> int:
        """
        更新通知日志

        :param pk: 通知日志 ID
        :param obj: 更新通知日志参数
        :return:
        """
        async with async_db_session.begin() as db:
            notice_log = await notice_log_dao.get(db, pk)
            if not notice_log:
                raise errors.NotFoundError(msg="通知日志不存在")
            count = await notice_log_dao.update(db, pk, obj)
            return count

    @staticmethod
    async def delete(*, pks: list[int]) -> int:
        """
        批量删除通知日志

        :param pks: 通知日志 ID 列表
        :return:
        """
        async with async_db_session.begin() as db:
            count = await notice_log_dao.delete(db, pks)
            return count

    @staticmethod
    async def get_by_notification_type(*, notification_type: str) -> Sequence[NoticeLog]:
        """
        根据通知方式获取日志

        :param notification_type: 通知方式
        :return:
        """
        async with async_db_session() as db:
            notice_logs = await notice_log_dao.get_by_notification_type(db, notification_type)
            return notice_logs

    @staticmethod
    async def get_failed_logs() -> Sequence[NoticeLog]:
        """
        获取失败的通知日志

        :return:
        """
        async with async_db_session() as db:
            failed_logs = await notice_log_dao.get_failed_logs(db)
            return failed_logs

    @staticmethod
    async def log_notification(
        *,
        description: str,
        notification_type: str,
        content: str,
        address: str,
        is_success: bool,
        failure_reason: Optional[str] = None,
    ) -> None:
        """
        记录通知日志的便捷方法

        :param description: 通知描述
        :param notification_type: 通知方式
        :param content: 通知内容
        :param address: 通知地址
        :param is_success: 是否成功
        :param failure_reason: 失败原因
        :return:
        """
        log_param = CreateNoticeLogParam(
            description=description,
            notification_type=notification_type,
            content=content,
            address=address,
            is_success=is_success,
            failure_reason=failure_reason,
        )
        await NoticeLogService.create(obj=log_param)


notice_log_service: NoticeLogService = NoticeLogService()
