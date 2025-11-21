#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
出金风控API接口
提供出金风控分析相关的API接口
"""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.tools.data_export_tool import DataExportTool
from backend.app.admin.crud.crud_risk_tasks import crud_risk_tasks
from backend.app.admin.model.risk_report_log import RiskReportLog
from backend.app.admin.model.risk_tasks import TaskStatus as DBTaskStatus
from backend.app.admin.schema.payment_risk import (
    PaymentRiskAnalysisRequest,
    PaymentRiskAnalysisResponse,
    PaymentRiskTaskResponse,
    PaymentRiskTaskStatusResponse,
    TaskStatus,
)
from backend.app.task.celery import celery_app
from backend.common.log import logger
from backend.common.response.response_code import CustomResponse
from backend.common.response.response_schema import ResponseSchemaModel, response_base
from backend.database.db import get_db

router = APIRouter()


# ==================== 异步出金风控接口 ====================


@router.post(
    "/analyze-async",
    summary="创建出金风控分析任务",
    description="创建异步出金风控分析任务，返回任务ID用于后续查询",
    response_model=ResponseSchemaModel[PaymentRiskTaskResponse],
)
async def create_payment_risk_analysis_task(
    request: PaymentRiskAnalysisRequest,
    db: AsyncSession = Depends(get_db),
) -> ResponseSchemaModel[PaymentRiskTaskResponse]:
    """
    创建出金风控分析任务

    Args:
        request: 出金风控分析请求
        db: 数据库会话

    Returns:
        任务创建响应，包含任务ID
    """
    try:
        # 生成任务ID
        task_id = str(uuid.uuid4())

        # 先在数据库中创建任务记录
        await crud_risk_tasks.create_task(
            db,
            task_id=task_id,
            member_id=request.member_id,
            request_data={"member_id": request.member_id},
            message="出金风控分析任务已创建",
        )

        # 启动异步任务，传入我们生成的task_id
        celery_app.send_task(name="payment_risk_analysis", args=[request.member_id], kwargs={"db_task_id": task_id})

        # 构建响应数据
        response_data = PaymentRiskTaskResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            message="出金风控分析任务已创建",
            member_id=request.member_id,
        )

        return response_base.success(res=CustomResponse(code=200, msg="任务创建成功"), data=response_data)

    except Exception as e:
        # 记录错误日志
        import logging

        logger = logging.getLogger("payment_risk_api")
        logger.exception(f"创建出金风控分析任务异常: {str(e)}")

        # 返回错误响应
        error_response = PaymentRiskTaskResponse(
            task_id="",
            status=TaskStatus.FAILED,
            message=f"任务创建失败: {str(e)}",
            member_id=request.member_id,
        )

        return response_base.fail(
            res=CustomResponse(code=500, msg=f"任务创建失败: {str(e)}"),
            data=error_response,
        )


@router.get(
    "/task/{task_id}/status",
    summary="查询出金风控分析任务状态",
    description="根据任务ID查询出金风控分析任务的当前状态和进度",
    response_model=ResponseSchemaModel[PaymentRiskTaskStatusResponse],
)
async def get_payment_risk_task_status(
    task_id: str,
    db: AsyncSession = Depends(get_db),
) -> ResponseSchemaModel[PaymentRiskTaskStatusResponse]:
    """
    查询出金风控分析任务状态

    Args:
        task_id: 任务ID
        db: 数据库会话

    Returns:
        任务状态响应
    """
    try:
        # 从数据库获取任务信息
        db_task = await crud_risk_tasks.get_by_task_id(db, task_id=task_id)

        if not db_task:
            response_data = PaymentRiskTaskStatusResponse(
                task_id=task_id,
                status=TaskStatus.FAILED,
                progress=0,
                message="任务不存在",
                member_id=0,
            )
            return response_base.fail(res=CustomResponse(code=404, msg="任务不存在"), data=response_data)

        # 映射数据库状态到响应状态
        status_mapping = {
            DBTaskStatus.PENDING: TaskStatus.PENDING,
            DBTaskStatus.PROCESSING: TaskStatus.PROCESSING,
            DBTaskStatus.COMPLETED: TaskStatus.COMPLETED,
            DBTaskStatus.FAILED: TaskStatus.FAILED,
        }

        response_data = PaymentRiskTaskStatusResponse(
            task_id=task_id,
            status=status_mapping.get(db_task.status, TaskStatus.PENDING),
            progress=db_task.progress or 0,
            message=db_task.message or "任务处理中",
            member_id=db_task.member_id,
            created_at=db_task.created_at.isoformat() if db_task.created_at else None,
            updated_at=db_task.updated_at.isoformat() if db_task.updated_at else None,
        )

        return response_base.success(res=CustomResponse(code=200, msg="状态查询成功"), data=response_data)

    except Exception as e:
        # 记录错误日志
        import logging

        logger = logging.getLogger("payment_risk_api")
        logger.exception(f"查询任务状态异常: {str(e)}")

        # 返回错误响应
        error_response = PaymentRiskTaskStatusResponse(
            task_id=task_id,
            status=TaskStatus.FAILED,
            progress=0,
            message=f"状态查询失败: {str(e)}",
            member_id=0,
        )

        return response_base.fail(
            res=CustomResponse(code=500, msg=f"状态查询失败: {str(e)}"),
            data=error_response,
        )


@router.get(
    "/task/{task_id}/result",
    summary="获取出金风控分析任务结果",
    description="根据任务ID获取出金风控分析的完整结果报告",
    response_model=ResponseSchemaModel[PaymentRiskAnalysisResponse],
)
async def get_payment_risk_task_result(
    task_id: str,
    db: AsyncSession = Depends(get_db),
) -> ResponseSchemaModel[PaymentRiskAnalysisResponse]:
    """
    获取出金风控分析任务结果

    Args:
        task_id: 任务ID
        db: 数据库会话

    Returns:
        分析结果响应
    """
    try:
        # 从数据库获取任务信息
        db_task = await crud_risk_tasks.get_by_task_id(db, task_id=task_id)

        if not db_task:
            response_data = PaymentRiskAnalysisResponse(
                task_id=task_id,
                status=TaskStatus.FAILED,
                member_id=0,
                data={},
                report_id=None,
                report_pdf_url=None,
            )
            return response_base.fail(res=CustomResponse(code=404, msg="任务不存在"), data=response_data)

        # 映射数据库状态到响应状态
        status_mapping = {
            DBTaskStatus.PENDING: TaskStatus.PENDING,
            DBTaskStatus.PROCESSING: TaskStatus.PROCESSING,
            DBTaskStatus.COMPLETED: TaskStatus.COMPLETED,
            DBTaskStatus.FAILED: TaskStatus.FAILED,
        }

        if db_task.status == DBTaskStatus.COMPLETED:
            # 任务成功完成，返回结果
            report_pdf_url = None

            # 如果存在 report_id，尝试生成 PDF
            if db_task.report_id:
                try:
                    # 从 risk_report_log 获取 report_document
                    result = await db.execute(select(RiskReportLog).where(RiskReportLog.id == db_task.report_id))
                    risk_report = result.scalar_one_or_none()

                    if risk_report and risk_report.report_document:
                        # 使用 DataExportTool 生成 PDF（统一管理）
                        export_tool = DataExportTool(data_source="payment_risk", base_path="admin")

                        # 使用 report_id 作为 task_id 和文件名
                        result = export_tool.export_markdown_to_pdf(
                            markdown_content=risk_report.report_document,
                            task_id=str(db_task.report_id),
                            filename=f"payment_risk_report_{db_task.report_id}",
                        )

                        if result["success"]:
                            # 使用 DataExportTool 生成的 URL
                            report_pdf_url = result["url"]
                            logger.info(f"PDF生成成功: {report_pdf_url} (大小: {result['file_size']} bytes)")
                        else:
                            logger.warning(
                                f"PDF生成失败，report_id: {db_task.report_id}, 错误: {result.get('error_message')}"
                            )
                    else:
                        logger.warning(f"未找到报告文档，report_id: {db_task.report_id}")

                except Exception as e:
                    logger.exception(f"生成PDF时发生异常: {str(e)}")
                    # PDF 生成失败不影响主流程，继续返回其他数据

            response_data = PaymentRiskAnalysisResponse(
                task_id=task_id,
                status=TaskStatus.COMPLETED,
                member_id=db_task.member_id,
                data=db_task.analysis_result or {},
                report_id=db_task.report_id,
                report_pdf_url=report_pdf_url,
                created_at=db_task.created_at.isoformat() if db_task.created_at else None,
                completed_at=db_task.completed_at.isoformat() if db_task.completed_at else None,
            )

            return response_base.success(res=CustomResponse(code=200, msg="获取结果成功"), data=response_data)

        elif db_task.status == DBTaskStatus.FAILED:
            # 任务失败
            error_msg = db_task.error_message or "任务执行失败"

            response_data = PaymentRiskAnalysisResponse(
                task_id=task_id,
                status=TaskStatus.FAILED,
                member_id=db_task.member_id,
                data={},
                report_id=None,
                report_pdf_url=None,
            )

            return response_base.fail(
                res=CustomResponse(code=500, msg=error_msg),
                data=response_data,
            )

        else:
            # 任务尚未完成
            response_data = PaymentRiskAnalysisResponse(
                task_id=task_id,
                status=status_mapping.get(db_task.status, TaskStatus.PENDING),
                member_id=db_task.member_id,
                data={},
                report_id=None,
                report_pdf_url=None,
            )

            return response_base.fail(
                res=CustomResponse(code=400, msg="任务尚未完成，请稍后再试"),
                data=response_data,
            )

    except Exception as e:
        # 记录错误日志
        logger.exception(f"获取任务结果异常: {str(e)}")

        # 返回错误响应
        error_response = PaymentRiskAnalysisResponse(
            task_id=task_id,
            status=TaskStatus.FAILED,
            member_id=0,
            data={},
            report_id=None,
            report_pdf_url=None,
        )

        return response_base.fail(
            res=CustomResponse(code=500, msg=f"获取结果失败: {str(e)}"),
            data=error_response,
        )
