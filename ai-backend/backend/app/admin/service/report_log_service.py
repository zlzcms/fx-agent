#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import uuid

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.crud.crud_ai_assistant import crud_ai_assistant
from backend.app.admin.crud.crud_risk_assistant import crud_risk_assistant
from backend.app.admin.model.ai_assistant_report_log import AiAssistantReportLog
from backend.app.admin.model.risk_member_analysis import RiskMemberAnalysis
from backend.app.admin.model.risk_report_log import RiskReportLog


# 自定义JSON编码器，处理datetime和其他特殊类型
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, "dict") and callable(getattr(obj, "dict")):
            # Handle Pydantic models
            return obj.dict()
        elif hasattr(obj, "__dict__"):
            # Handle custom objects with __dict__
            return obj.__dict__
        return super().default(obj)


class ReportLogService:
    """报告日志服务类"""

    @staticmethod
    async def add_risk_report_log(db: AsyncSession, *, log_data: dict) -> RiskReportLog:
        """
        添加风控报告记录，并更新 RiskAssistant 的分析次数和最后分析时间
        :param db: 数据库会话
        :param log_data: 风控报告记录数据（dict）
        :return: RiskReportLog 实例
        """
        # 创建报告记录
        # Make sure id is None to let the database handle autoincrement
        if "id" not in log_data:
            log_data["id"] = None

        log_data["member_id"] = str(log_data.get("member_id", ""))
        # 对于 JSON 字段，直接传递原始对象，不需要序列化
        # 因为数据库字段类型已经是 JSON，SQLAlchemy 会自动处理序列化
        log_data["sql_data"] = log_data.get("sql_data", {})
        log_data["prompt_data"] = log_data.get("prompt_data", {})
        log_data["ai_response"] = log_data.get("ai_response", {})
        log_data["report_table"] = log_data.get("report_table", {})
        # report_document 是 Text 字段，需要字符串处理
        report_document = log_data.get("report_document", "")
        if isinstance(report_document, dict):
            log_data["report_document"] = ReportLogService.safe_json_dumps(report_document)
        else:
            log_data["report_document"] = str(report_document)
        # report_pdf_url 字段，如果不存在则设置为 None
        if "report_pdf_url" not in log_data:
            log_data["report_pdf_url"] = None

        report_log = RiskReportLog(**log_data)
        db.add(report_log)

        # 更新 RiskAssistant
        assistant_id = log_data.get("assistant_id")
        if assistant_id:
            risk_assistant = await crud_risk_assistant.get(db, id=assistant_id)
            if risk_assistant:
                risk_assistant.ai_analysis_count = (risk_assistant.ai_analysis_count or 0) + 1
                risk_assistant.last_analysis_time = datetime.now()
                db.add(risk_assistant)

        # 同时增加员工分析记录
        member_id = log_data.get("member_id")
        risk_type = log_data.get("risk_type")
        if member_id and risk_type:
            await ReportLogService.add_risk_member_analysis(
                db, member_id=member_id, risk_type=risk_type, remark=f"通过风控报告分析 ID: {report_log.id}"
            )

        await db.commit()
        await db.refresh(report_log)
        return report_log

    @staticmethod
    async def add_ai_assistant_report_log(db: AsyncSession, *, log_data: dict) -> AiAssistantReportLog:
        """
        添加 AI 助手报告记录，并更新 AIAssistant 的分析次数和最后分析时间
        :param db: 数据库会话
        :param log_data: AI 助手报告记录数据（dict）
        :return: AiAssistantReportLog 实例
        """
        if "id" not in log_data:
            log_data["id"] = None
        log_data["member_ids"] = ReportLogService.safe_json_dumps(log_data.get("member_ids", ""))
        log_data["ai_response"] = ReportLogService.safe_json_dumps(log_data.get("ai_response", ""))
        log_data["report_table"] = ReportLogService.safe_json_dumps(log_data.get("report_table", ""))
        log_data["report_document"] = ReportLogService.safe_json_dumps(log_data.get("report_document", ""))
        log_data["sql_data"] = ReportLogService.safe_json_dumps(log_data.get("sql_data", ""))
        log_data["prompt_data"] = ReportLogService.safe_json_dumps(log_data.get("prompt_data", ""))

        # 创建报告记录
        report_log = AiAssistantReportLog(**log_data)

        db.add(report_log)

        # 更新 AIAssistant
        assistant_id = log_data.get("assistant_id")
        if assistant_id:
            ai_assistant = await crud_ai_assistant.get(db, id=assistant_id)
            if ai_assistant:
                ai_assistant.ai_analysis_count = (ai_assistant.ai_analysis_count or 0) + 1
                ai_assistant.last_analysis_time = datetime.now()
                db.add(ai_assistant)

        await db.commit()
        await db.refresh(report_log)
        return report_log

    @staticmethod
    async def add_risk_member_analysis(
        db: AsyncSession, *, member_id: str, risk_type: str, remark: str = ""
    ) -> RiskMemberAnalysis:
        """
        添加或更新员工风险分析记录
        :param db: 数据库会话
        :param member_id: 员工ID
        :param risk_type: 风险类型
        :param remark: 备注
        :return: RiskMemberAnalysis 实例
        """
        # 查询是否已存在相同 member_id 和 risk_type 的记录
        from sqlalchemy import select

        stmt = select(RiskMemberAnalysis).where(
            RiskMemberAnalysis.member_id == member_id, RiskMemberAnalysis.risk_type == risk_type
        )
        result = await db.execute(stmt)
        existing_record = result.scalars().first()

        if existing_record:
            # 如果存在，更新分析时间和备注
            existing_record.analysis_time = datetime.now()
            existing_record.remark = f"{existing_record.remark}; {remark}" if existing_record.remark else remark
            db.add(existing_record)
            return existing_record
        else:
            # 如果不存在，创建新记录
            analysis_record = RiskMemberAnalysis(
                id=str(uuid.uuid4()),
                member_id=member_id,
                risk_type=risk_type,
                analysis_time=datetime.now(),
                remark=remark,
            )

            db.add(analysis_record)
            return analysis_record

    @staticmethod
    # 安全序列化函数
    def safe_json_dumps(obj):
        """安全地将对象序列化为JSON字符串，处理特殊类型如datetime"""
        try:
            if isinstance(obj, dict):
                return json.dumps(obj, cls=CustomJSONEncoder)
            else:
                return str(obj)
        except TypeError:
            return str(obj)


report_log_service = ReportLogService()
