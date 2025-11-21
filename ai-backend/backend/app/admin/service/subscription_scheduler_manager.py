# -*- coding: utf-8 -*-
"""
订阅调度管理器
负责管理订阅与任务调度的集成
"""

import json

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.crud.crud_ai_subscription import crud_ai_subscription
from backend.app.admin.model.ai_subscription import AISubscription
from backend.app.task.crud.crud_execution import task_scheduler_execution_dao
from backend.app.task.crud.crud_scheduler import task_scheduler_dao
from backend.app.task.enums import TaskSchedulerType
from backend.app.task.model.scheduler import TaskScheduler
from backend.app.task.schema.scheduler import CreateTaskSchedulerParam
from backend.common.log import logger


class SubscriptionSchedulerManager:
    """订阅调度管理器"""

    @staticmethod
    async def validate_scheduler_relation(db: AsyncSession, subscription_id: int, scheduler_id: Optional[int]) -> bool:
        """应用层验证订阅和调度任务的关联关系"""
        if not scheduler_id:
            return True  # 允许为空

        try:
            # 检查调度任务是否存在
            scheduler = await task_scheduler_dao.get(db, scheduler_id)
            if not scheduler:
                logger.warning(f"调度任务 {scheduler_id} 不存在，订阅 {subscription_id} 的关联无效")
                return False

            # 检查调度任务是否已被其他订阅使用（通过task_scheduler表的subscription_id）
            from sqlalchemy import select

            from backend.app.task.model.scheduler import TaskScheduler

            stmt = select(TaskScheduler.subscription_id).where(TaskScheduler.id == scheduler_id)
            result = await db.execute(stmt)
            linked_subscription_id = result.scalar_one_or_none()

            if linked_subscription_id and linked_subscription_id != subscription_id:
                logger.warning(f"调度任务 {scheduler_id} 已被订阅 {linked_subscription_id} 使用")
                return False

            return True
        except Exception as e:
            logger.error(f"验证调度关系失败: {str(e)}")
            return False

    @staticmethod
    async def cleanup_orphaned_schedulers(db: AsyncSession) -> Dict[str, Any]:
        """清理孤立的调度任务（subscription_id不为空但对应订阅不存在的调度任务）"""
        try:
            from sqlalchemy import and_, select

            # 查找subscription_id不为空但对应订阅不存在的调度任务
            # 注意：subscription_id为空的调度任务是合法的（独立调度任务）
            stmt = select(TaskScheduler).where(
                and_(
                    TaskScheduler.subscription_id.isnot(None),
                    ~TaskScheduler.subscription_id.in_(select(AISubscription.id)),
                )
            )
            result = await db.execute(stmt)
            orphaned_schedulers = result.scalars().all()

            cleaned_count = 0
            for scheduler in orphaned_schedulers:
                logger.info(
                    f"删除孤立的调度任务: {scheduler.name} (ID: {scheduler.id}, subscription_id: {scheduler.subscription_id})"
                )
                await task_scheduler_dao.delete(db, scheduler.id)
                cleaned_count += 1

            return {
                "status": True,
                "message": f"清理了 {cleaned_count} 个孤立的调度任务（有subscription_id但订阅不存在）",
                "cleaned_count": cleaned_count,
            }
        except Exception as e:
            logger.error(f"清理孤立调度任务失败: {str(e)}")
            return {"status": False, "message": str(e), "cleaned_count": 0}

    @staticmethod
    async def frequency_to_crontab(subscription: AISubscription) -> str:
        """将订阅执行频率转换为crontab表达式"""
        if subscription.execution_frequency == "minutes":
            # 每隔X分钟执行一次
            minutes = subscription.execution_minutes or 30
            if minutes < 1:
                minutes = 1
            return f"*/{minutes} * * * *"

        elif subscription.execution_frequency == "hours":
            # 每隔X小时执行一次
            hours = subscription.execution_hours or 2
            if hours < 1:
                hours = 1
            return f"0 */{hours} * * *"

        elif subscription.execution_frequency == "daily":
            # 每天在指定时间执行
            exec_time = subscription.execution_time or "09:00"
            hour, minute = exec_time.split(":")
            return f"{minute} {hour} * * *"

        elif subscription.execution_frequency == "weekly":
            # 每周在指定的星期几和时间执行
            weekday = subscription.execution_weekday or "1"
            exec_time = subscription.execution_weekly_time or "19:00"
            hour, minute = exec_time.split(":")
            # 调整星期格式：周日为0，周一到周六为1-6
            if weekday == "0":
                weekday = "0"  # 周日
            else:
                weekday = str(int(weekday) - 1)  # 其他天减1
            return f"{minute} {hour} * * {weekday}"

        elif subscription.execution_frequency == "monthly":
            # 每月在指定的日期和时间执行
            day = subscription.execution_day or "1"
            exec_time = subscription.execution_monthly_time or "19:00"
            hour, minute = exec_time.split(":")
            return f"{minute} {hour} {day} * *"

        else:
            # 默认每天早上9点
            return "0 9 * * *"

    @staticmethod
    async def frequency_to_interval(subscription: AISubscription) -> Dict[str, Any]:
        """将订阅执行频率转换为interval配置"""
        if subscription.execution_frequency == "minutes":
            minutes = subscription.execution_minutes or 30
            return {
                "type": TaskSchedulerType.INTERVAL.value,
                "interval_every": max(minutes, 1),
                "interval_period": "minutes",
                "crontab": None,  # 明确设置crontab为None
            }
        elif subscription.execution_frequency == "hours":
            hours = subscription.execution_hours or 2
            return {
                "type": TaskSchedulerType.INTERVAL.value,
                "interval_every": max(hours, 1),
                "interval_period": "hours",  # PeriodType.HOURS.value
                "crontab": None,  # 明确设置crontab为None
            }
        else:
            # 其他频率使用crontab
            return {
                "type": TaskSchedulerType.CRONTAB.value,
                "crontab": await SubscriptionSchedulerManager.frequency_to_crontab(subscription),
            }

    @staticmethod
    async def create_scheduler_for_subscription(
        db: AsyncSession, subscription: AISubscription
    ) -> Optional[TaskScheduler]:
        """为订阅创建调度任务"""
        try:
            # 检查是否已存在调度任务（通过subscription_id查找）
            existing = await task_scheduler_dao.get_by_subscription_id(db, subscription.id)
            if existing:
                # 更新现有调度任务
                return await SubscriptionSchedulerManager.update_scheduler_for_subscription(db, subscription)

            # 获取AI助手信息用于构建任务名称（使用简单查询避免事务冲突）
            from sqlalchemy import select

            from backend.app.admin.model.ai_assistant import AIAssistant

            # 直接查询AI助手名称，避免复杂的关联查询
            logger.info(f"正在查询AI助手: {subscription.assistant_id}")
            result = await db.execute(select(AIAssistant.name).where(AIAssistant.id == subscription.assistant_id))
            assistant_name = result.scalar_one_or_none()
            if not assistant_name:
                logger.error(f"未找到ID为 {subscription.assistant_id} 的AI助手")
                return None
            logger.info(f"找到AI助手: {assistant_name}")

            # 构建调度任务配置
            logger.info(f"正在构建调度任务配置，频率: {subscription.execution_frequency}")
            scheduler_config = await SubscriptionSchedulerManager.frequency_to_interval(subscription)
            logger.info(f"调度配置生成完成: {scheduler_config}")

            # 创建调度任务
            task_name = f"Subscription_{subscription.id}_{assistant_name}"
            logger.info(f"准备创建调度任务: {task_name}")
            scheduler_data = CreateTaskSchedulerParam(
                name=task_name,
                task="scheduled_ai_analysis",
                args=json.dumps([subscription.assistant_id]),
                kwargs=json.dumps({"subscription_id": str(subscription.id), "setting": subscription.setting or {}}),
                remark=f"订阅：{subscription.name} - AI助手：{assistant_name}",
                enabled=subscription.status,
                one_off=False,
                expire_seconds=None,  # 明确设置为None
                expire_time=None,  # 明确设置为None
                user_id=subscription.user_id,  # 设置用户ID
                subscription_id=subscription.id,  # 设置订阅ID关联
                **scheduler_config,
            )
            logger.info(f"调度任务参数准备完成: {scheduler_data.model_dump()}")

            # 检查是否已存在同名任务
            existing_task = await task_scheduler_dao.get_by_name(db, scheduler_data.name)
            if existing_task:
                logger.warning(f"调度任务已存在: {scheduler_data.name}，将使用现有任务")
                scheduler = existing_task
            else:
                # 验证crontab格式（从TaskSchedulerService复制的验证逻辑）
                if scheduler_data.type == TaskSchedulerType.CRONTAB:
                    from backend.app.task.utils.tzcrontab import crontab_verify

                    try:
                        crontab_verify(scheduler_data.crontab)
                    except Exception as cron_error:
                        logger.error(f"crontab格式验证失败: {str(cron_error)}")
                        return None

                # 直接使用DAO创建调度任务
                logger.info("开始调用DAO创建调度任务")
                try:
                    logger.info(f"即将插入的调度任务数据: {scheduler_data.model_dump()}")
                    await task_scheduler_dao.create(db, scheduler_data)
                    logger.info(f"调度任务创建成功: {scheduler_data.name}")
                except Exception as dao_error:
                    logger.error(f"DAO创建调度任务失败: {dao_error}", exc_info=True)
                    raise dao_error

                # 查找创建的调度任务
                logger.info(f"正在查找创建的调度任务: {scheduler_data.name}")
                scheduler = await task_scheduler_dao.get_by_name(db, scheduler_data.name)
                if not scheduler:
                    logger.error(f"创建调度任务后无法找到任务: {scheduler_data.name}")
                    return None
                logger.info(f"成功找到调度任务, ID: {scheduler.id}")

            # 应用层验证关联关系
            if not await SubscriptionSchedulerManager.validate_scheduler_relation(db, subscription.id, scheduler.id):
                logger.error(f"调度任务 {scheduler.id} 关联验证失败")
                return None

            # 不再需要更新订阅的scheduler_id，因为已删除该字段
            # 通过task_scheduler.subscription_id来维护关联关系

            logger.info(f"为订阅 {subscription.name} 创建调度任务成功，ID: {scheduler.id}")
            return scheduler

        except Exception as e:
            logger.error(f"创建订阅调度任务失败: {str(e)}", exc_info=True)
            logger.error(
                f"订阅详情: id={subscription.id}, name={subscription.name}, assistant_id={subscription.assistant_id}"
            )
            logger.error(f"调度配置: {scheduler_config if 'scheduler_config' in locals() else 'Not created'}")
            return None

    @staticmethod
    async def update_scheduler_for_subscription(
        db: AsyncSession, subscription: AISubscription
    ) -> Optional[TaskScheduler]:
        """更新订阅的调度任务"""
        try:
            # 使用subscription_id查找对应的scheduler，而不是使用已删除的scheduler_id字段
            scheduler = await task_scheduler_dao.get_by_subscription_id(db, subscription.id)
            if not scheduler:
                logger.warning(f"订阅 {subscription.id} 没有关联的调度任务，将创建新的")
                return await SubscriptionSchedulerManager.create_scheduler_for_subscription(db, subscription)

            # 更新调度配置
            scheduler_config = await SubscriptionSchedulerManager.frequency_to_interval(subscription)

            # 更新任务参数
            import json

            update_data = {
                "name": scheduler.name,  # 保持原有名称
                "task": scheduler.task,  # 保持原有任务名
                "enabled": subscription.status,
                "args": json.dumps([subscription.assistant_id]),
                "kwargs": json.dumps({"subscription_id": str(subscription.id), "setting": subscription.setting or {}}),
                "user_id": subscription.user_id,  # 确保设置用户ID
                "subscription_id": subscription.id,  # 确保设置订阅ID
                **scheduler_config,
            }

            # 创建UpdateTaskSchedulerParam对象
            from backend.app.task.schema.scheduler import UpdateTaskSchedulerParam

            update_param = UpdateTaskSchedulerParam(**update_data)
            await task_scheduler_dao.update(db, scheduler.id, update_param)

            # 重新获取更新后的scheduler
            scheduler = await task_scheduler_dao.get(db, scheduler.id)

            logger.info(f"更新订阅 {subscription.name} 的调度任务成功")
            return scheduler

        except Exception as e:
            logger.error(f"更新订阅调度任务失败: {str(e)}")
            return None

    @staticmethod
    async def delete_scheduler_for_subscription(db: AsyncSession, subscription_id: int) -> bool:
        """删除订阅的调度任务"""
        try:
            subscription = await crud_ai_subscription.get(db, id=subscription_id)
            if not subscription:
                return True

            # 查找关联的调度任务
            scheduler = await task_scheduler_dao.get_by_subscription_id(db, subscription_id)
            if not scheduler:
                return True

            # 删除调度任务
            await task_scheduler_dao.delete(db, scheduler.id)

            # 不需要清理订阅的scheduler_id，因为该字段已被删除

            logger.info(f"删除订阅 {subscription.name} 的调度任务成功")
            return True

        except Exception as e:
            logger.error(f"删除订阅调度任务失败: {str(e)}")
            return False

    @staticmethod
    async def sync_subscription_scheduler(db: AsyncSession, subscription_id: int) -> bool:
        """同步订阅的调度任务状态"""
        try:
            subscription = await crud_ai_subscription.get(db, id=subscription_id)
            if not subscription:
                return False

            # 查找关联的调度任务
            scheduler = await task_scheduler_dao.get_by_subscription_id(db, subscription.id)
            if scheduler:
                if subscription.status and not scheduler.enabled:
                    # 启用订阅，确保调度任务也启用
                    await task_scheduler_dao.set_status(db, scheduler.id, True)
                elif not subscription.status and scheduler.enabled:
                    # 禁用订阅，同时禁用调度任务
                    await task_scheduler_dao.set_status(db, scheduler.id, False)

            return True

        except Exception as e:
            logger.error(f"同步订阅调度状态失败: {str(e)}")
            return False

    @staticmethod
    async def get_subscription_execution_history(
        db: AsyncSession, subscription_id: int, limit: int = 50
    ) -> list[Dict[str, Any]]:
        """获取订阅执行历史"""
        try:
            executions = await task_scheduler_execution_dao.get_by_subscription_id(
                db, subscription_id=subscription_id, limit=limit
            )

            history = []
            for exec in executions:
                history.append(
                    {
                        "id": exec.id,
                        "execution_time": exec.execution_time,
                        "start_time": exec.start_time,
                        "end_time": exec.end_time,
                        "status": exec.status,
                        "report_id": exec.report_id,
                        "error_message": exec.error_message,
                        "celery_task_id": exec.celery_task_id,
                        "duration": (
                            (exec.end_time - exec.start_time).total_seconds()
                            if exec.start_time and exec.end_time
                            else None
                        ),
                    }
                )

            return history

        except Exception as e:
            logger.error(f"获取订阅执行历史失败: {str(e)}")
            return []

    @staticmethod
    async def execute_subscription_now(
        db: AsyncSession, subscription_id: int, user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """立即执行订阅"""
        try:
            subscription = await crud_ai_subscription.get(db, id=subscription_id)
            if not subscription:
                return {"status": False, "message": "订阅不存在"}

            if not subscription.status:
                return {"status": False, "message": "订阅已禁用"}

            # 获取关联的调度任务
            scheduler = None
            # 查找关联的调度任务
            scheduler = await task_scheduler_dao.get_by_subscription_id(db, subscription_id)

            if scheduler:
                # 使用现有的调度任务执行
                from backend.app.task.service.scheduler_service import task_scheduler_service

                result = await task_scheduler_service.execute(
                    pk=scheduler.id, user_id=user_id, subscription_id=subscription_id
                )
                return {"status": True, "message": "执行成功", "celery_task_id": result.get("celery_task_id")}
            else:
                # 创建临时调度任务并执行
                from backend.app.task.celery import celery_app

                kwargs = {"subscription_id": str(subscription.id), "setting": subscription.setting or {}}
                if user_id:
                    kwargs["task_creator_id"] = user_id

                result = celery_app.send_task(
                    "scheduled_ai_analysis",
                    args=[subscription.assistant_id],
                    kwargs=kwargs,
                )

                # 创建执行记录
                execution_data = {
                    "scheduler_id": None,
                    "celery_task_id": result.id,
                    "execution_time": datetime.now(),
                    "user_id": user_id,
                    "subscription_id": subscription_id,
                    "status": "running",
                }
                await task_scheduler_execution_dao.create(db, execution_data)

                return {"status": True, "message": "执行成功", "celery_task_id": result.id}

        except Exception as e:
            logger.error(f"立即执行订阅失败: {str(e)}")
            return {"status": False, "message": str(e)}


# 全局实例
subscription_scheduler_manager = SubscriptionSchedulerManager()
