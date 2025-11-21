#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
风控报告服务
"""

import json

from datetime import datetime
from typing import Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.crud.crud_user import user_dao
from backend.app.admin.model.risk_level import RiskLevel
from backend.app.admin.model.risk_report_log import RiskReportLog
from backend.app.admin.service.risk_level_service import risk_level_service
from backend.common.enums import RiskType
from backend.common.pagination import PageData


class RiskReportService:
    """风控报告服务"""

    async def _report_to_dict(self, db: AsyncSession, report: RiskReportLog) -> dict:
        """将报告转换为字典"""
        result = {
            "id": report.id,
            "assistant_id": report.assistant_id,
            "model_id": report.model_id,
            "risk_type": report.risk_type,
            "member_id": report.member_id,
            "report_score": report.report_score,
            "sql_data": report.sql_data,
            "prompt_data": report.prompt_data,
            "input_prompt": report.input_prompt,
            "score": report.score,
            "report_tags": report.report_tags,
            "report_result": report.report_result,
            "report_table": report.report_table,
            "report_document": report.report_document,
            "report_pdf_url": report.report_pdf_url,
            "description": report.description,
            "report_status": report.report_status,
            "is_processed": report.is_processed,
            "ai_response": report.ai_response,
            "created_time": report.created_time,
            "updated_time": report.updated_time,
            "handle_suggestion": report.handle_suggestion,
            "handle_result": report.handle_result,
            "handle_user": report.handle_user,
            "handle_time": report.handle_time,
            "member_name": report.member_name,
            # 新增增量分析字段
            "analysis_type": report.analysis_type,
            "trigger_sources": report.trigger_sources,
            "detection_window_info": report.detection_window_info,
        }

        # 优先使用数据库中存储的 handle_user_name，如果没有则从用户表查询
        handle_user_name: str | None = report.handle_user_name
        if not handle_user_name and report.handle_user:
            try:
                user_id_int = int(str(report.handle_user))
                user = await user_dao.get(db, user_id_int)
                if user:
                    handle_user_name = user.nickname or user.username
            except Exception:
                # 忽略转换或查询异常，保持名称为空
                handle_user_name = None
        result["handle_user_name"] = handle_user_name

        # 根据report_score获取风险等级信息
        risk_level_info = None
        if report.score is not None:
            risk_level_info = await risk_level_service.get_by_score(db, score=report.score)

        # 添加风险等级信息到结果中
        result["risk_level"] = {
            "name": risk_level_info["name"] if risk_level_info else None,
            "description": risk_level_info["description"] if risk_level_info else None,
        }

        # 安全解析JSON字段
        try:
            if result["sql_data"]:
                if isinstance(result["sql_data"], str):
                    result["sql_data"] = json.loads(result["sql_data"])
                # 如果已经是字典类型，保持不变
            else:
                result["sql_data"] = {}
        except (json.JSONDecodeError, TypeError):
            result["sql_data"] = {}

        try:
            if result["prompt_data"]:
                if isinstance(result["prompt_data"], str):
                    result["prompt_data"] = json.loads(result["prompt_data"])
                # 如果已经是字典类型，保持不变
            else:
                result["prompt_data"] = {}
        except (json.JSONDecodeError, TypeError):
            result["prompt_data"] = {}

        try:
            if result["report_table"]:
                result["report_table"] = json.loads(result["report_table"])
            else:
                result["report_table"] = {}
        except (json.JSONDecodeError, TypeError):
            result["report_table"] = {}

        try:
            if result["ai_response"]:
                if isinstance(result["ai_response"], str):
                    result["ai_response"] = json.loads(result["ai_response"])
                # 如果已经是字典类型，保持不变
            else:
                result["ai_response"] = {}
        except (json.JSONDecodeError, TypeError):
            result["ai_response"] = {}

        # 处理检测窗口信息JSON字段
        try:
            if result["detection_window_info"]:
                result["detection_window_info"] = (
                    json.loads(result["detection_window_info"])
                    if isinstance(result["detection_window_info"], str)
                    else result["detection_window_info"]
                )
            else:
                result["detection_window_info"] = {}
        except (json.JSONDecodeError, TypeError):
            result["detection_window_info"] = {}

        return result

    async def get_paginated_list(
        self,
        db: AsyncSession,
        *,
        assistant_id: Optional[str] = None,
        model_id: Optional[str] = None,
        risk_type: Optional[RiskType] = None,
        member_id: Optional[str] = None,
        member_name: Optional[str] = None,
        is_processed: Optional[bool] = None,
        risk_level_ids: Optional[list] = None,
        risk_tag_ids: Optional[list] = None,
        # 新增增量分析过滤参数
        analysis_type: Optional[str] = None,
        trigger_sources: Optional[str] = None,
        page: int = 1,
        size: int = 10,
    ) -> PageData[dict]:
        """获取分页风控报告列表"""
        query = select(RiskReportLog)
        count_query = select(RiskReportLog)

        conditions = []
        if assistant_id:
            conditions.append(RiskReportLog.assistant_id == assistant_id)
        if model_id:
            conditions.append(RiskReportLog.model_id == model_id)
        if risk_type:
            conditions.append(RiskReportLog.risk_type == risk_type.value)
        if member_id:
            conditions.append(RiskReportLog.member_id == member_id)
        if member_name:
            conditions.append(RiskReportLog.member_name.ilike(f"%{member_name}%"))
        if is_processed is not None:
            conditions.append(RiskReportLog.is_processed == is_processed)

        # 新增增量分析字段过滤
        if analysis_type:
            conditions.append(RiskReportLog.analysis_type == analysis_type)
        if trigger_sources:
            # 支持触发源的模糊匹配，因为trigger_sources可能包含多个值（逗号分隔）
            conditions.append(RiskReportLog.trigger_sources.ilike(f"%{trigger_sources}%"))

        # 处理风控等级筛选（基于分数范围）
        if risk_level_ids:
            # 查询选中的风控等级的分数范围
            risk_level_query = select(RiskLevel).where(
                and_(RiskLevel.id.in_(risk_level_ids), RiskLevel.deleted_at.is_(None))
            )
            risk_levels_result = await db.execute(risk_level_query)
            risk_levels = risk_levels_result.scalars().all()

            if risk_levels:
                level_conditions = []
                for level in risk_levels:
                    level_conditions.append(
                        and_(RiskReportLog.score >= level.start_score, RiskReportLog.score <= level.end_score)
                    )
                if level_conditions:
                    conditions.append(or_(*level_conditions))

        # 处理风险标签筛选（基于标签ID）
        if risk_tag_ids:
            try:
                # 使用 PostgreSQL JSONB 操作符查询数组中是否包含指定标签ID
                tag_conditions = []
                for tag_id in risk_tag_ids:
                    # 使用 JSONB @> 操作符检查数组是否包含指定元素
                    tag_conditions.append(RiskReportLog.report_tags.op("@>")([tag_id]))
                if tag_conditions:
                    conditions.append(or_(*tag_conditions))
            except Exception:
                # 标签筛选失败时记录错误但不影响其他筛选条件
                import traceback

                traceback.print_exc()
                pass

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # 获取总数
        # 使用 COUNT(*) 提升性能，避免加载全部记录导致超时
        count_stmt = select(func.count()).select_from(RiskReportLog)
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # 分页查询
        query = query.order_by(RiskReportLog.created_time.desc())
        query = query.offset((page - 1) * size).limit(size)
        result = await db.execute(query)

        # 转换为字典
        reports = result.scalars().all()
        items = []
        for report in reports:
            item = await self._report_to_dict(db, report)
            # 移除不必要的大字段，降低响应体大小
            if "report_result" in item:
                del item["report_result"]
            items.append(item)

        from math import ceil

        total_pages = ceil(total / size) if total > 0 else 1

        return PageData(
            items=items,
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

    async def get_detail(self, db: AsyncSession, *, report_id: int) -> Optional[dict]:
        """获取风控报告详情"""
        result = await db.execute(select(RiskReportLog).where(RiskReportLog.id == report_id))
        report = result.scalars().first()
        if not report:
            return None
        return await self._report_to_dict(db, report)

    async def process_report(
        self,
        db: AsyncSession,
        *,
        report_id: int,
        handle_result: str,
        handler: str,
        handler_name: Optional[str],
        handle_time: datetime,
    ) -> Optional[dict]:
        """处理风控报告"""
        result = await db.execute(select(RiskReportLog).where(RiskReportLog.id == report_id))
        report = result.scalar_one_or_none()
        if not report:
            return None

        # 更新处理状态和处理信息
        report.is_processed = True
        report.handle_result = handle_result
        report.handle_user = handler
        report.handle_user_name = handler_name
        report.handle_time = handle_time
        await db.commit()
        await db.refresh(report)

        return await self._report_to_dict(db, report)


risk_report_service = RiskReportService()
