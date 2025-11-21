#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI助手报告服务
"""

import json

from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.model.ai_assistant_report_log import AiAssistantReportLog
from backend.common.pagination import PageData


class AssistantReportService:
    """AI助手报告服务"""

    def _report_to_dict(self, report: AiAssistantReportLog) -> dict:
        """将报告转换为字典"""
        result = {
            "id": report.id,
            "assistant_id": report.assistant_id,
            "model_id": report.model_id,
            "member_ids": report.member_ids,
            "subscription_id": report.subscription_id,
            "sql_data": report.sql_data,
            "prompt_data": report.prompt_data,
            "input_prompt": report.input_prompt,
            "report_score": report.report_score,
            "report_result": report.report_result,
            "report_table": report.report_table,
            "report_document": report.report_document,
            "report_status": report.report_status,
            "ai_response": report.ai_response,
            "created_time": report.created_time,
            "updated_time": report.updated_time,
        }

        # 安全解析JSON字段
        try:
            if result["sql_data"]:
                result["sql_data"] = json.loads(result["sql_data"])
            else:
                result["sql_data"] = {}
        except (json.JSONDecodeError, TypeError):
            result["sql_data"] = {}

        try:
            if result["prompt_data"]:
                result["prompt_data"] = json.loads(result["prompt_data"])
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
                result["ai_response"] = json.loads(result["ai_response"])
            else:
                result["ai_response"] = {}
        except (json.JSONDecodeError, TypeError):
            result["ai_response"] = {}

        return result

    async def get_paginated_list(
        self,
        db: AsyncSession,
        *,
        assistant_id: Optional[str] = None,
        assistant_name: Optional[str] = None,
        model_id: Optional[str] = None,
        member_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        page: int = 1,
        size: int = 10,
    ) -> PageData[dict]:
        """获取分页AI助手报告列表"""
        query = select(AiAssistantReportLog)
        count_query = select(func.count(AiAssistantReportLog.id))

        conditions = []
        if assistant_id:
            conditions.append(AiAssistantReportLog.assistant_id == assistant_id)
        if assistant_name:
            # 通过助手名称查询，需要关联AI助手表
            from backend.app.admin.model.ai_assistant import AIAssistant

            query = query.join(AIAssistant, AiAssistantReportLog.assistant_id == AIAssistant.id)
            count_query = count_query.join(AIAssistant, AiAssistantReportLog.assistant_id == AIAssistant.id)
            conditions.append(AIAssistant.name.ilike(f"%{assistant_name}%"))
        if model_id:
            conditions.append(AiAssistantReportLog.model_id == model_id)
        if member_id:
            # 由于member_ids是字符串列表，需要进行模糊查询
            conditions.append(AiAssistantReportLog.member_ids.ilike(f"%{member_id}%"))
        if start_time:
            from datetime import datetime

            start_datetime = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            conditions.append(AiAssistantReportLog.created_time >= start_datetime)
        if end_time:
            from datetime import datetime

            end_datetime = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
            conditions.append(AiAssistantReportLog.created_time <= end_datetime)

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # 获取总数
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # 分页查询
        query = query.order_by(AiAssistantReportLog.created_time.desc())
        query = query.offset((page - 1) * size).limit(size)
        result = await db.execute(query)

        # 转换为字典，移除 report_result 字段（其他字段保留）
        items = [self._report_to_dict(report) for report in result.scalars().all()]
        for item in items:
            item.pop("report_result", None)
        # 批量预取关联对象名称，避免 N+1 查询
        try:
            assistant_ids = {item["assistant_id"] for item in items if item.get("assistant_id")}
            model_ids = {item["model_id"] for item in items if item.get("model_id")}
            subscription_ids = {item["subscription_id"] for item in items if item.get("subscription_id")}

            # 预取助手信息
            assistant_map = {}
            if assistant_ids:
                from backend.app.admin.model.ai_assistant import AIAssistant

                res = await db.execute(
                    select(AIAssistant.id, AIAssistant.name).where(AIAssistant.id.in_(assistant_ids))
                )
                for a_id, a_name in res.all():
                    assistant_map[a_id] = {"id": a_id, "name": a_name}

            # 预取模型名称
            model_map = {}
            if model_ids:
                from backend.app.admin.model.ai_model import AIModel

                res = await db.execute(select(AIModel.id, AIModel.name).where(AIModel.id.in_(model_ids)))
                for m_id, m_name in res.all():
                    model_map[m_id] = m_name

            # 预取订阅名称
            subscription_map = {}
            if subscription_ids:
                from backend.app.admin.model.ai_subscription import AISubscription

                res = await db.execute(
                    select(AISubscription.id, AISubscription.name).where(AISubscription.id.in_(subscription_ids))
                )
                for s_id, s_name in res.all():
                    subscription_map[s_id] = s_name

            # 回填到 items
            for item in items:
                item["assistant"] = assistant_map.get(item["assistant_id"], None)
                item["model_name"] = model_map.get(item["model_id"], "")
                item["subscription_name"] = subscription_map.get(item["subscription_id"], None)
        except Exception:
            # 出错时保持兼容，不影响核心数据返回
            for item in items:
                item.setdefault("assistant", None)
                item.setdefault("model_name", "")
                item.setdefault("subscription_name", None)

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
        """获取AI助手报告详情"""
        result = await db.execute(select(AiAssistantReportLog).where(AiAssistantReportLog.id == report_id))
        report = result.scalars().first()
        if not report:
            return None
        return self._report_to_dict(report)

    async def json_loads(self, data: str) -> dict:
        """将字符串转换为字典"""
        return json.loads(data)


assistant_report_service = AssistantReportService()
