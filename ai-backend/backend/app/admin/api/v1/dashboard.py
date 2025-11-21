#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from typing import Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.model.ai_assistant_report_log import AiAssistantReportLog
from backend.app.admin.model.ai_training_log import AITrainingLog
from backend.app.admin.model.login_log import LoginLog
from backend.app.admin.model.opera_log import OperaLog
from backend.app.admin.model.risk_report_log import RiskReportLog
from backend.app.admin.model.user import User
from backend.app.home.model.ai_chat_message import AIChatMessage
from backend.common.response.response_schema import ResponseSchemaModel, response_base
from backend.common.security.jwt import DependsJwtAuth
from backend.database.db import get_db

router = APIRouter()


@router.get("/analytics/overview", summary="获取数据概览", dependencies=[DependsJwtAuth])
async def get_analytics_overview(db: AsyncSession = Depends(get_db)) -> ResponseSchemaModel[Dict]:
    """获取数据概览统计信息"""
    try:
        # 计算本周开始时间
        now = datetime.now()
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

        # 1. 用户数量统计
        # 本周登录用户数
        weekly_users_query = select(func.count(User.id)).where(
            User.last_login_time >= week_start, User.deleted_at.is_(None)
        )
        weekly_users_result = await db.execute(weekly_users_query)
        weekly_users_count = weekly_users_result.scalar() or 0

        # 总用户数
        total_users_query = select(func.count(User.id)).where(User.deleted_at.is_(None))
        total_users_result = await db.execute(total_users_query)
        total_users_count = total_users_result.scalar() or 0

        # 2. 对话数量统计
        # 本周对话消息数
        weekly_chat_query = select(func.count(AIChatMessage.id)).where(
            AIChatMessage.created_time >= week_start, AIChatMessage.deleted_at.is_(None)
        )
        weekly_chat_result = await db.execute(weekly_chat_query)
        weekly_chat_count = weekly_chat_result.scalar() or 0

        # 总对话消息数
        total_chat_query = select(func.count(AIChatMessage.id)).where(AIChatMessage.deleted_at.is_(None))
        total_chat_result = await db.execute(total_chat_query)
        total_chat_count = total_chat_result.scalar() or 0

        # 3. 报告数量统计
        # 本周AI助手报告数
        weekly_report_query = select(func.count(AiAssistantReportLog.id)).where(
            AiAssistantReportLog.created_time >= week_start
        )
        weekly_report_result = await db.execute(weekly_report_query)
        weekly_report_count = weekly_report_result.scalar() or 0

        # 总AI助手报告数
        total_report_query = select(func.count(AiAssistantReportLog.id))
        total_report_result = await db.execute(total_report_query)
        total_report_count = total_report_result.scalar() or 0

        # 4. 风控次数统计
        # 本周风控报告数
        weekly_risk_query = select(func.count(RiskReportLog.id)).where(RiskReportLog.created_time >= week_start)
        weekly_risk_result = await db.execute(weekly_risk_query)
        weekly_risk_count = weekly_risk_result.scalar() or 0

        # 总风控报告数
        total_risk_query = select(func.count(RiskReportLog.id))
        total_risk_result = await db.execute(total_risk_query)
        total_risk_count = total_risk_result.scalar() or 0

        return response_base.success(
            data={
                "userCount": {"value": weekly_users_count, "totalValue": total_users_count},
                "chatCount": {"value": weekly_chat_count, "totalValue": total_chat_count},
                "reportCount": {"value": weekly_report_count, "totalValue": total_report_count},
                "riskCount": {"value": weekly_risk_count, "totalValue": total_risk_count},
            }
        )
    except Exception:
        return response_base.success(
            data={
                "userCount": {"value": 0, "totalValue": 0},
                "chatCount": {"value": 0, "totalValue": 0},
                "reportCount": {"value": 0, "totalValue": 0},
                "riskCount": {"value": 0, "totalValue": 0},
            }
        )


@router.get("/analytics/trends", summary="获取使用趋势", dependencies=[DependsJwtAuth])
async def get_analytics_trends(db: AsyncSession = Depends(get_db)) -> ResponseSchemaModel[Dict]:
    """获取使用趋势数据"""
    try:
        # 获取今天0:00到23:00的24小时数据
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        hours_data = []
        login_data = []
        operation_data = []

        for i in range(24):
            hour_start = today_start + timedelta(hours=i)
            hour_end = hour_start + timedelta(hours=1)

            # 登录日志统计
            login_query = select(func.count(LoginLog.id)).where(
                LoginLog.login_time >= hour_start, LoginLog.login_time < hour_end
            )
            login_result = await db.execute(login_query)
            login_count = login_result.scalar() or 0
            login_data.append(login_count)

            # 操作日志统计
            operation_query = select(func.count(OperaLog.id)).where(
                OperaLog.created_time >= hour_start, OperaLog.created_time < hour_end
            )
            operation_result = await db.execute(operation_query)
            operation_count = operation_result.scalar() or 0
            operation_data.append(operation_count)

            # 时间标签
            hours_data.append(f"{hour_start.hour:02d}:00")

        return response_base.success(
            data={"hours": hours_data, "loginData": login_data, "operationData": operation_data}
        )
    except Exception:
        return response_base.success(data={"hours": [], "loginData": [], "operationData": []})


@router.get("/analytics/monthly", summary="获取月使用量", dependencies=[DependsJwtAuth])
async def get_analytics_monthly(db: AsyncSession = Depends(get_db)) -> ResponseSchemaModel[Dict]:
    """获取月使用量数据"""
    try:
        # 获取当前年份1月到12月的数据
        now = datetime.now()
        current_year = now.year
        months_data = []

        for month in range(1, 13):  # 1月到12月
            month_start = datetime(current_year, month, 1)
            if month == 12:
                month_end = datetime(current_year + 1, 1, 1)
            else:
                month_end = datetime(current_year, month + 1, 1)

            # 登录日志统计
            login_query = select(func.count(LoginLog.id)).where(
                LoginLog.login_time >= month_start, LoginLog.login_time < month_end
            )
            login_result = await db.execute(login_query)
            login_count = login_result.scalar() or 0

            # 操作日志统计
            operation_query = select(func.count(OperaLog.id)).where(
                OperaLog.created_time >= month_start, OperaLog.created_time < month_end
            )
            operation_result = await db.execute(operation_query)
            operation_count = operation_result.scalar() or 0

            months_data.append(login_count + operation_count)

        return response_base.success(data={"months": months_data})
    except Exception:
        return response_base.success(data={"months": []})


@router.get("/analytics/countries", summary="获取国家统计", dependencies=[DependsJwtAuth])
async def get_analytics_countries(db: AsyncSession = Depends(get_db)) -> ResponseSchemaModel[List[Dict]]:
    """获取国家统计数据"""
    try:
        # 统计各国家的登录次数
        country_query = (
            select(LoginLog.country, func.count(LoginLog.id).label("count"))
            .where(LoginLog.country.isnot(None), LoginLog.country != "")
            .group_by(LoginLog.country)
            .order_by(func.count(LoginLog.id).desc())
        )

        country_result = await db.execute(country_query)
        countries = country_result.fetchall()

        return response_base.success(
            data=[{"name": country.country or "未知", "value": country.count} for country in countries]
        )
    except Exception:
        return response_base.success(data=[])


@router.get("/analytics/ai-stats", summary="获取AI统计", dependencies=[DependsJwtAuth])
async def get_analytics_ai_stats(db: AsyncSession = Depends(get_db)) -> ResponseSchemaModel[List[Dict]]:
    """获取AI统计数据"""
    try:
        # 助理报告数量统计
        assistant_report_query = select(func.count(AiAssistantReportLog.id))
        assistant_report_result = await db.execute(assistant_report_query)
        assistant_report_count = assistant_report_result.scalar() or 0

        # 风控报告数量统计
        risk_report_query = select(func.count(RiskReportLog.id))
        risk_report_result = await db.execute(risk_report_query)
        risk_report_count = risk_report_result.scalar() or 0

        # 训练日志数量统计
        training_log_query = select(func.count(AITrainingLog.id))
        training_log_result = await db.execute(training_log_query)
        training_log_count = training_log_result.scalar() or 0

        return response_base.success(
            data=[
                {"name": "助理报告", "value": assistant_report_count},
                {"name": "风控报告", "value": risk_report_count},
                {"name": "训练日志", "value": training_log_count},
            ]
        )
    except Exception:
        return response_base.success(data=[])
