#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI助手任务
定期执行AI助手数据分析任务
"""

import json

from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.crud.crud_ai_assistant_report_user_read import ai_assistant_report_user_read_dao
from backend.app.admin.model.ai_assistant_report_user_read import AiAssistantReportUserRead
from backend.app.admin.service.ai_assistant_service import AIAssistantService
from backend.app.admin.service.ai_subscription_service import AISubscriptionService
from backend.app.admin.service.data_analysis_service import DataAnalysisService
from backend.app.admin.service.notice_log_service import notice_log_service
from backend.app.admin.service.report_log_service import report_log_service
from backend.app.admin.service.warehouse_user_service import warehouse_user_service
from backend.app.email.utils.send import send_email
from backend.app.task.celery import celery_app
from backend.app.task.crud.crud_execution import task_scheduler_execution_dao
from backend.common.enums import AnalysisType, TrainingLogType
from backend.common.log import logger
from backend.database.db import get_db
from backend.plugin.config.crud.crud_config import config_dao

data_analysis_service = DataAnalysisService()


@celery_app.task(
    name="scheduled_ai_analysis",
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError, OSError),  # 只对网络和系统异常重试
    retry_kwargs={"max_retries": 2, "countdown": 30},  # 减少重试次数和间隔
)
async def scheduled_ai_analysis(self, assistant_id: str, setting: Dict[str, Any] = {}, **kwargs) -> Dict[str, Any]:
    """执行AI助手分析任务"""

    subscription_id = kwargs.get("subscription_id")
    celery_task_id = self.request.id
    user_id = None
    task_creator_id = kwargs.get("task_creator_id")
    logger.info(f"开始执行订阅任务: {subscription_id}, 任务ID: {celery_task_id}, 创建者ID: {task_creator_id}")

    # 添加幂等性检查，避免重复执行
    if subscription_id:
        logger.info(f"检查任务幂等性: subscription_id={subscription_id}, assistant_id={assistant_id}")

    try:
        db_gen = get_db()
        db = await anext(db_gen)

        try:
            # 获取用户ID - task_creator_id本身就是MCP需要的crm_user_id
            user_id = None

            if task_creator_id:
                user_id = task_creator_id
            elif subscription_id:
                # 订阅场景的降级方案：从订阅信息获取user_id
                try:
                    subscription = await AISubscriptionService.get_ai_subscription(db, id=int(subscription_id))
                    if subscription:
                        user_id = subscription.get("user_id")
                        if not user_id:
                            logger.warning(f"订阅 {subscription_id} 没有user_id")
                    else:
                        logger.warning(f"订阅ID {subscription_id} 对应的订阅信息为空")
                except Exception as e:
                    logger.warning(f"获取订阅用户ID失败: {e}")

            # 如果仍然没有获取到user_id（比如通过Flower调用），使用系统默认用户
            if not user_id:
                try:
                    from backend.core.conf import settings

                    user_id = settings.SYSTEM_DEFAULT_USER_ID
                    logger.warning(f"使用系统默认用户ID: {user_id}")
                except Exception as e:
                    logger.error(f"获取系统默认用户ID失败: {e}")

            # 更新执行记录状态为运行中
            if subscription_id:
                await _update_execution_status(
                    celery_task_id,
                    "running",
                    user_id=user_id,
                    subscription_id=int(subscription_id) if subscription_id else None,
                )

            assistant = await AIAssistantService.get_ai_assistant(db, id=assistant_id)
            if not assistant:
                error_msg = f"未找到ID为 {assistant_id} 的AI助手"
                logger.warning(error_msg)
                if subscription_id:
                    await _update_execution_status(
                        celery_task_id,
                        "failed",
                        error_msg,
                        user_id=user_id,
                        subscription_id=int(subscription_id) if subscription_id else None,
                    )
                return {"status": False, "message": error_msg, "task_id": celery_task_id}

            # 如果是订阅触发，使用订阅配置
            if subscription_id:
                try:
                    subscription = await AISubscriptionService.get_ai_subscription(db, id=int(subscription_id))
                    if subscription and subscription.get("setting"):
                        # 合并订阅配置，订阅配置优先级更高
                        merged_setting = {**setting, **subscription["setting"]}
                        setting = merged_setting
                except Exception as e:
                    logger.warning(f"获取订阅配置失败: {e}")
                    # 继续使用原有setting，不中断执行

            # 为process_ai_assistant创建新的数据库会话
            process_db_gen = get_db()
            process_db = await anext(process_db_gen)
            try:
                result = await process_ai_assistant(process_db, assistant, setting, subscription_id, user_id)
            finally:
                await process_db.close()

            # 更新订阅的分析次数和时间
            if subscription_id and result.get("status"):
                try:
                    await AISubscriptionService.update_analysis_status(db, id=int(subscription_id))
                except Exception as e:
                    logger.warning(f"更新订阅分析状态失败: {e}")

            # 更新执行记录状态和报告ID
            if subscription_id:
                status = "completed" if result.get("status") else "failed"
                report_id = result.get("data", {}).get("report_id")
                await _update_execution_status(
                    celery_task_id,
                    status,
                    error_message=result.get("message") if not result.get("status") else None,
                    report_id=report_id,
                    user_id=user_id,
                    subscription_id=int(subscription_id) if subscription_id else None,
                )
                # 根据订阅记录的通知对象 在ai_assistant_report_user_read 插入对应用户的阅读记录

                # 发送通知（仅在报告生成成功时）:  邮件 + lark webhook
                if result.get("status") and report_id:
                    # 发送邮件通知
                    try:
                        (
                            email_success,
                            email_address,
                            email_content,
                            email_failure_reason,
                        ) = await _send_subscription_notification(db, subscription, assistant, report_id)

                        # 记录邮件通知日志
                        await notice_log_service.log_notification(
                            description=f"订阅报告通知，报告id:{report_id}",
                            notification_type="email",
                            content=email_content,  # 使用渲染后的内容
                            address=email_address,
                            is_success=email_success,
                            failure_reason=email_failure_reason if not email_success else None,
                        )

                        if email_success:
                            logger.info(f"邮件通知发送成功: {email_address}")
                        else:
                            logger.warning(f"发送订阅邮件通知失败: {email_failure_reason}")

                    except Exception as e:
                        # 记录异常到日志
                        await notice_log_service.log_notification(
                            description=f"订阅报告通知，报告id:{report_id}",
                            notification_type="email",
                            content=f"AI助手报告生成通知 - {subscription.get('name', '未知订阅')} (系统异常)",
                            address="未知",
                            is_success=False,
                            failure_reason=f"系统异常: {str(e)}",
                        )
                        logger.warning(f"发送订阅邮件通知失败: {e}")

                    # 发送Lark webhook通知
                    try:
                        # 获取报告评分
                        report_score = 0.0
                        result_data = result.get("data", {})
                        if "report_score" in result_data:
                            report_score = float(result_data["report_score"])

                        (
                            webhook_success,
                            webhook_url,
                            webhook_content,
                            webhook_failure_reason,
                        ) = await _send_lark_webhook_notification(
                            db=db,
                            report_id=report_id,
                            assistant_name=assistant.get("name", "Unknown Assistant"),
                            report_score=report_score,
                            generated_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        )

                        # 记录Lark webhook通知日志
                        await notice_log_service.log_notification(
                            description=f"订阅报告通知，报告id:{report_id}",
                            notification_type="lark_webhook",
                            content=webhook_content,  # 使用实际的message_content
                            address=webhook_url,
                            is_success=webhook_success,
                            failure_reason=webhook_failure_reason if not webhook_success else None,
                        )

                        if webhook_success:
                            logger.info(f"Lark webhook通知发送成功: {webhook_url}")
                        else:
                            logger.warning(f"发送Lark webhook通知失败: {webhook_failure_reason}")

                    except Exception as e:
                        # 记录异常到日志
                        await notice_log_service.log_notification(
                            description=f"订阅报告通知，报告id:{report_id}",
                            notification_type="lark_webhook",
                            content=f"AI assistant 订阅报告通知 - 助理: {assistant.get('name', 'Unknown')} (系统异常)",
                            address="未知",
                            is_success=False,
                            failure_reason=f"系统异常: {str(e)}",
                        )
                        logger.warning(f"发送Lark webhook通知失败: {e}")
                else:
                    logger.info("报告未生成，不发送邮件通知")
            # 只返回可序列化的assistant基本信息，避免SQLAlchemy对象序列化错误
            serializable_assistant = {
                "id": assistant.get("id"),
                "name": assistant.get("name"),
                "type": assistant.get("type"),
                "description": assistant.get("description"),
                "status": assistant.get("status"),
            }
            result["assistant"] = serializable_assistant
            result["task_id"] = celery_task_id
            if subscription_id:
                result["subscription_id"] = subscription_id

            return result

        except Exception as e:
            error_msg = f"AI助手分析出现异常: {str(e)}"
            logger.exception(f"{error_msg}, task_id: {celery_task_id}")

            if subscription_id:
                await _update_execution_status(
                    celery_task_id,
                    "failed",
                    error_msg,
                    user_id=user_id,
                    subscription_id=int(subscription_id) if subscription_id else None,
                )

            return {"status": False, "message": error_msg, "task_id": celery_task_id, "data": {}, "report_id": None}

        finally:
            try:
                await db.close()
            except Exception as close_error:
                logger.warning(f"关闭数据库连接失败: {close_error}")

    except Exception as e:
        error_msg = f"AI助手分析启动失败: {str(e)}"
        logger.exception(f"{error_msg}, task_id: {celery_task_id}")
        raise


async def _update_execution_status(
    celery_task_id: str,
    status: str,
    error_message: Optional[str] = None,
    report_id: Optional[str] = None,
    user_id: Optional[int] = None,
    subscription_id: Optional[int] = None,
):
    """更新或创建执行记录状态 - 使用独立的数据库会话"""
    try:
        # 使用独立的数据库会话，避免事务冲突
        db_gen = get_db()
        status_db = await anext(db_gen)

        try:
            execution = await task_scheduler_execution_dao.get_by_celery_task_id(status_db, celery_task_id)
            if execution:
                # 更新现有记录
                update_data = {
                    "status": status,
                    "end_time": datetime.now() if status in ["completed", "failed"] else None,
                }
                if error_message:
                    update_data["error_message"] = error_message
                if report_id:
                    update_data["report_id"] = report_id
                if user_id:
                    update_data["user_id"] = user_id
                if subscription_id:
                    update_data["subscription_id"] = subscription_id

                await task_scheduler_execution_dao.update(status_db, execution.id, update_data)
            else:
                # 创建新记录 - 需要先查找scheduler_id
                scheduler_id = None
                if subscription_id:
                    from backend.app.task.crud.crud_scheduler import task_scheduler_dao

                    scheduler = await task_scheduler_dao.get_by_subscription_id(status_db, subscription_id)
                    if scheduler:
                        scheduler_id = scheduler.id

                if scheduler_id:
                    create_data = {
                        "scheduler_id": scheduler_id,
                        "celery_task_id": celery_task_id,
                        "status": status,
                        "execution_time": datetime.now(),
                        "start_time": datetime.now() if status == "running" else None,
                        "end_time": datetime.now() if status in ["completed", "failed"] else None,
                    }
                    if error_message:
                        create_data["error_message"] = error_message
                    if report_id:
                        create_data["report_id"] = report_id
                    if user_id:
                        create_data["user_id"] = user_id
                    if subscription_id:
                        create_data["subscription_id"] = subscription_id

                    await task_scheduler_execution_dao.create(status_db, create_data)
                else:
                    logger.warning(f"无法找到subscription_id {subscription_id}对应的scheduler，跳过创建执行记录")

            await status_db.commit()  # 确保提交更新或创建
        finally:
            await status_db.close()

    except Exception as e:
        logger.error(f"更新执行记录状态失败: {str(e)}")
        # 状态更新失败不影响主要流程


async def process_ai_assistant(
    db: AsyncSession,
    assistant: Dict[str, Any],
    setting: Dict[str, Any] = {},
    subscription_id: Optional[int] = None,
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """处理单个AI助手的分析逻辑"""
    try:
        # 验证assistant参数类型
        if not isinstance(assistant, dict):
            error_msg = f"assistant参数类型错误，期望dict，实际: {type(assistant)}"
            logger.error(error_msg)
            return {"status": False, "message": error_msg, "data": {}, "report_id": None}

        logger.info(f"Processing assistant: {assistant.get('name')}, setting: {setting}")

        # 在任务开始时固定时间范围，避免重复计算时时间变化
        from datetime import datetime

        fixed_end_time = datetime.now()
        logger.info(f"Fixed end time for analysis: {fixed_end_time}")

        # 获取crm_user_id - user_id本身就是MCP需要的crm_user_id
        if user_id:
            crm_user_id = int(user_id)
        else:
            error_msg = "未提供user_id，MCP服务需要此参数进行权限验证"
            logger.error(error_msg)
            return {"status": False, "message": error_msg, "data": {}, "report_id": None}

        # 验证和准备数据
        # settings = assistant.get("settings", {})

        # 处理setting参数（订阅功能需要）
        # 从setting中提取用户筛选条件，兼容订阅功能的dataSourceLimit格式
        condition = {}
        if setting:
            # 处理订阅功能的dataSourceLimit结构
            data_source_limit = setting.get("dataSourceLimit", {})
            if data_source_limit:
                # 直接提取dataSourceLimit中的字段，前端已统一字段名
                for field in ["customer", "agent", "country", "user_tag", "kyc_status", "register_time", "user"]:
                    if field in data_source_limit and data_source_limit[field] is not None:
                        condition[field] = data_source_limit[field]

            # 兼容其他调用场景：直接从setting根级别提取
            if not condition:
                for key in ["customer", "agent", "country", "user_tag", "kyc_status", "create_time"]:
                    if key in setting and setting[key] is not None:
                        condition[key] = setting[key]

        # 如果没有设置时间限制且没有明确指定用户ID，添加默认的30天限制以减少数据量
        has_explicit_users = any(key in condition for key in ["user", "customer"])
        if not any(key in condition for key in ["register_time", "create_time"]) and not has_explicit_users:
            from datetime import datetime, timedelta

            thirty_days_ago = datetime.now() - timedelta(days=30)
            condition["register_time"] = thirty_days_ago.strftime("%Y-%m-%d")
            logger.info(f"添加默认30天时间限制: {condition['register_time']}")
        elif has_explicit_users:
            logger.info(f"检测到明确指定的用户ID，跳过时间限制: {condition}")

        data_permission_values = await warehouse_user_service.get_need_analyzed_user_ids(condition)
        if not data_permission_values:
            error_msg = f"AI助手 {assistant.get('name', 'Unknown')} 没有需要分析的用户"
            logger.error(error_msg)
            return {"status": False, "message": "没有需要分析的用户", "data": {}, "report_id": None}

        assistant["avatar"] = None

        # 获取数据源信息，从助手的data_sources字段获取
        datasource_list = assistant.get("data_sources", []) or []
        query_types = []
        for datasource in datasource_list:
            if datasource.get("query_name"):
                query_types.append(datasource.get("query_name"))
        if len(query_types) == 0:
            error_msg = f"AI助手 {assistant.get('name', 'Unknown')} 没有数据源"
            logger.error(error_msg)
            return {"status": False, "message": "没有数据源", "data": {}, "report_id": None}

        condition = {
            "data_time_range_type": setting.get(
                "data_time_range_type", assistant.get("data_time_range_type", "quarter")
            ),
            "data_time_value": setting.get("data_time_value", assistant.get("data_time_value", 1)),
            "fixed_end_time": fixed_end_time,  # 添加固定结束时间
        }

        # 过滤掉不能JSON序列化的字段，特别是关联对象
        serializable_fields = {
            k: v
            for k, v in assistant.items()
            if k
            not in [
                "id",
                "ai_model_id",
                "name",
                "description",
                "background",
                "model_definition",
                "output_data",
                "personnel",
                "assistant_personnel",
            ]
            and not hasattr(v, "__table__")  # 排除SQLAlchemy模型对象
        }

        basic_info = await data_analysis_service.build_basic_info(
            db=db,
            assistant_id=assistant.get("id"),
            ai_model_id=assistant.get("ai_model_id"),
            name=assistant.get("name", ""),
            description=assistant.get("description", ""),
            background=assistant.get("background", ""),
            model_definition=assistant.get("model_definition", ""),
            output_format_table=assistant.get("output_data", {}).get("table", []),
            output_format_document=assistant.get("output_data", {}).get("document", ""),
            analysis_type=AnalysisType.general,
            training_type=TrainingLogType.ai_assistant,
            **serializable_fields,
        )

        analysis_service_result = await data_analysis_service.analyze_user_data(
            db=db,
            query_types=query_types,
            data_permission_values=data_permission_values,
            condition=condition,
            basicInfo=basic_info,
            is_save_file=False,
            crm_user_id=crm_user_id,
        )

        if not analysis_service_result.get("data"):
            error_msg = f"数据分析服务调用失败: {analysis_service_result.get('message')}"
            logger.error(error_msg)
            return {"status": False, "message": error_msg}

        result = await _process_analysis_result(
            db,
            analysis_service_result.get("data"),
            assistant.get("id"),
            data_permission_values,
            basic_info,
            subscription_id,
        )
        return result

    except Exception as e:
        error_msg = f"处理AI助手 {assistant.get('name')} 失败: {str(e)}"
        logger.exception(error_msg)
        return {"status": False, "message": error_msg, "data": {}, "report_id": None}


async def _process_analysis_result(
    db: AsyncSession,
    analysis_service_result: Dict[str, Any],
    assistant_id: str,
    member_ids: List[Any],
    basic_info: Dict[str, Any],
    subscription_id: Optional[int] = None,
) -> Dict[str, Any]:
    """处理AI助手分析结果并保存到数据库"""
    try:
        # 检查analysis_service_result的类型，如果不是字典则处理为错误情况
        if not isinstance(analysis_service_result, dict):
            error_msg = f"分析结果格式错误，期望字典类型，实际: {type(analysis_service_result)}"
            logger.error(error_msg)
            return {
                "status": False,
                "message": f"处理结果失败: {error_msg}",
                "data": {},
                "report_id": None,
            }

        data = analysis_service_result.get("data", {})

        # 确保model_id不为None，如果为None则使用默认值或跳过保存
        model_id = basic_info.get("ai_model_id")
        if not model_id:
            logger.warning(f"AI助手 {assistant_id} 的model_id为空，无法保存报告日志")
            return {
                "status": True,
                "message": "AI助手分析任务完成，但model_id为空，未保存报告日志",
                "data": {"report_id": None},
            }

        report_log = {
            "assistant_id": assistant_id,
            "model_id": model_id,
            "member_ids": member_ids,
            "subscription_id": int(subscription_id) if subscription_id else None,
            "sql_data": "",
            "prompt_data": basic_info,
            "input_prompt": analysis_service_result.get("prompt", ""),
            "report_status": True,
            "report_score": data.get("confidence", 0),
            "report_result": json.dumps(analysis_service_result),
            "report_table": json.dumps(data.get("property_analysis", {})),
            "report_document": data.get("analytical_report", ""),
            "ai_response": analysis_service_result.get("response", {}),
            "id": None,
        }

        # 保存报告日志并获取返回的SQLAlchemy对象
        saved_report_log = None
        try:
            saved_report_log = await report_log_service.add_ai_assistant_report_log(db=db, log_data=report_log)
        except Exception as report_error:
            logger.error(f"保存报告日志失败: {str(report_error)}")

        # 如果是订阅任务且报告保存成功，为订阅的responsible_persons创建通知记录
        if subscription_id and saved_report_log and saved_report_log.id:
            try:
                logger.info(f"获取订阅信息0: {subscription_id}")
                subscription = await AISubscriptionService.get_ai_subscription(db, id=int(subscription_id))
                logger.info(f"获取订阅信息1: {subscription}")
                if subscription and subscription.get("responsible_persons"):
                    responsible_persons = subscription["responsible_persons"]
                    logger.info(f"获取订阅信息2: {responsible_persons}")
                    for person in responsible_persons:
                        # 从responsible_persons中获取用户信息
                        logger.info(f"创建报告读取记录: {person}")
                        personnel_id = person.get("personnel_id")
                        if personnel_id:
                            try:
                                # 确保personnel_id是整数类型
                                personnel_id = int(personnel_id)
                            except (ValueError, TypeError):
                                logger.warning(f"无效的personnel_id: {personnel_id}，跳过创建通知记录")
                                continue

                            # 创建通知记录
                            try:
                                # 检查是否已存在记录
                                existing_record = await ai_assistant_report_user_read_dao.get_user_read_status(
                                    db, saved_report_log.id, personnel_id
                                )
                                if not existing_record:
                                    new_record = AiAssistantReportUserRead(
                                        report_id=saved_report_log.id, user_id=personnel_id, is_read=False
                                    )
                                    db.add(new_record)
                                    logger.info(f"为用户 {personnel_id} 创建报告 {saved_report_log.id} 的通知记录")
                            except Exception as notification_error:
                                logger.warning(f"为用户 {personnel_id} 创建通知记录失败: {str(notification_error)}")

                    # 提交通知记录
                    try:
                        await db.commit()
                    except Exception as commit_error:
                        logger.warning(f"提交通知记录失败: {str(commit_error)}")
                        await db.rollback()
            except Exception as subscription_error:
                logger.warning(f"处理订阅通知记录失败111: {str(subscription_error)}")

        return {
            "status": True,
            "message": "AI助手分析任务完成",
            "data": data,
            "report_id": saved_report_log.id if saved_report_log else None,
        }

    except Exception as e:
        error_msg = f"处理结果失败: {str(e)}"
        logger.exception(error_msg)

        return {"status": False, "message": error_msg}


async def _send_lark_webhook_notification(
    db: AsyncSession,
    report_id: int,
    assistant_name: str,
    report_score: float,
    generated_time: str,
    report_url: str = "https://admin.ai1center.com/ai/reports",
) -> tuple[bool, str, str, str]:
    """
    发送Lark webhook通知

    Args:
        db: 数据库会话
        assistant_name: AI助手名称
        report_score: 报告评分
        generated_time: 生成时间
        report_url: 报告链接地址

    Returns:
        tuple[bool, str, str, str]: (is_success, webhook_url, message_content_json, failure_reason)
    """
    webhook_url = ""
    message_content_json = ""
    failure_reason = ""

    try:
        # 获取Lark webhook配置
        webhook_configs = await config_dao.get_all(db, "HOOK")
        if not webhook_configs:
            failure_reason = "未找到Lark webhook配置"
            logger.info(f"{failure_reason}，跳过webhook通知")
            return False, webhook_url, message_content_json, failure_reason

        # 解析webhook配置
        configs = {config.key: config.value for config in webhook_configs}

        # 查找webhook URL和状态
        webhook_url = configs.get("HOOK_ADDR", "")
        webhook_status = configs.get("HOOK_STATUS", "1")  # 默认启用

        if not webhook_url:
            failure_reason = "未找到有效的Lark webhook URL配置"
            logger.warning(failure_reason)
            return False, webhook_url, message_content_json, failure_reason

        # 检查webhook状态（'1'表示启用，'0'表示禁用）
        if webhook_status != "1":
            failure_reason = "Lark webhook已禁用"
            logger.info(f"{failure_reason}，跳过webhook通知")
            return False, webhook_url, message_content_json, failure_reason

        # 构建Lark消息内容
        message_content = {
            "msg_type": "interactive",
            "card": {
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "content": f"**助理名称：** {assistant_name}\n**报告ID：**{report_id}\n**报告评分：** {report_score:.2f}\n**生成时间：** {generated_time}",
                            "tag": "lark_md",
                        },
                    },
                    {
                        "actions": [
                            {
                                "tag": "button",
                                "text": {"content": "查看报告", "tag": "lark_md"},
                                "url": report_url,
                                "type": "default",
                                "value": {},
                            }
                        ],
                        "tag": "action",
                    },
                ],
                "header": {"title": {"content": "AI assistant 订阅报告生成通知", "tag": "plain_text"}},
            },
        }

        # 将消息内容转为JSON字符串用于日志记录
        import json

        message_content_json = json.dumps(message_content, ensure_ascii=False, indent=2)

        # 发送webhook请求
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                webhook_url, json=message_content, headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    logger.info(f"Lark webhook通知发送成功: {assistant_name}")
                    return True, webhook_url, message_content_json, ""
                else:
                    response_text = await response.text()
                    failure_reason = f"状态码: {response.status}, 响应: {response_text}"
                    logger.warning(f"Lark webhook通知发送失败，{failure_reason}")
                    return False, webhook_url, message_content_json, failure_reason

    except Exception as e:
        failure_reason = str(e)
        logger.error(f"发送Lark webhook通知失败: {failure_reason}")
        return False, webhook_url, message_content_json, failure_reason


async def _send_subscription_notification(
    db: AsyncSession, subscription: Dict[str, Any], assistant: Dict[str, Any], report_id: str
) -> tuple[bool, str, str, str]:
    """
    发送订阅报告生成通知邮件

    Args:
        db: 数据库会话
        subscription: 订阅信息
        assistant: AI助手信息
        report_id: 报告ID

    Returns:
        tuple[bool, str, str, str]: (is_success, email_addresses, rendered_content, failure_reason)
    """
    email_addresses = ""
    rendered_content = ""
    failure_reason = ""

    try:
        # 获取通知对象列表
        responsible_persons = subscription.get("responsible_persons", [])
        if not responsible_persons:
            failure_reason = f"订阅 {subscription.get('name')} 没有配置通知对象"
            logger.info(f"{failure_reason}，跳过邮件通知")
            return False, email_addresses, rendered_content, failure_reason

        # 收集邮箱地址
        recipients = []
        for person in responsible_persons:
            if isinstance(person, dict):
                email = person.get("email")
                if email:
                    recipients.append(email)
            elif isinstance(person, str):
                # 如果是字符串，可能是邮箱地址
                if "@" in person:
                    recipients.append(person)

        if not recipients:
            failure_reason = f"订阅 {subscription.get('name')} 的通知对象中没有找到有效的邮箱地址"
            logger.warning(failure_reason)
            return False, email_addresses, rendered_content, failure_reason

        email_addresses = ", ".join(recipients)

        # 构建邮件内容
        subscription_name = subscription.get("name", "未知订阅")
        assistant_name = assistant.get("name", "未知助手")
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        subject = f"AI助手报告生成通知 - {subscription_name}"

        content = {
            "subscription_name": subscription_name,
            "assistant_name": assistant_name,
            "report_id": report_id,
            "generated_time": current_time,
            "recipients": ", ".join(recipients),
        }

        # 发送邮件并获取渲染后的内容
        email_success, rendered_content, email_failure_reason = await send_email(
            db=db,
            recipients=recipients,
            subject=subject,
            content=content,
            template="subscription_report_notification.html",  # 可以创建专门的模板
        )

        if email_success:
            logger.info(f"订阅 {subscription_name} 的报告生成通知邮件已发送给: {', '.join(recipients)}")
            return True, email_addresses, rendered_content, ""
        else:
            failure_reason = email_failure_reason
            return False, email_addresses, rendered_content, failure_reason

    except Exception as e:
        failure_reason = str(e)
        logger.error(f"发送订阅通知邮件失败: {failure_reason}")
        return False, email_addresses, rendered_content, failure_reason
