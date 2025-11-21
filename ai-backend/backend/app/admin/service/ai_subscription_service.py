# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-01-XX 10:00:00
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-26 22:00:00
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.crud.crud_ai_subscription import (
    crud_ai_subscription,
    crud_ai_subscription_notification_method,
)
from backend.app.admin.schema.ai_subscription import (
    AISubscriptionCreate,
    AISubscriptionQueryParams,
    AISubscriptionUpdate,
)
from backend.app.admin.service.subscription_scheduler_manager import subscription_scheduler_manager
from backend.common.enums import SubscriptionType
from backend.common.exception.errors import ForbiddenError, NotFoundError
from backend.common.log import logger
from backend.common.pagination import PageData


class AISubscriptionService:
    """AI订阅服务"""

    @staticmethod
    async def _convert_to_response_model(db: AsyncSession, db_obj) -> Dict[str, Any]:
        """将数据库对象转换为响应模型"""
        if not db_obj:
            return None

        # 调试：检查对象状态
        logger.info(f"Converting object to response model: id={getattr(db_obj, 'id', 'N/A')}, type={type(db_obj)}")

        # 获取通知方式的详细信息
        notification_methods = []
        try:
            if hasattr(db_obj, "notification_relations") and db_obj.notification_relations:
                # 直接访问已加载的关联对象，避免异步调用
                for rel in db_obj.notification_relations:
                    if hasattr(rel, "notification_method") and rel.notification_method:
                        method = rel.notification_method
                        notification_methods.append(
                            {
                                "id": method.id,
                                "name": method.name,
                                "type": method.type,
                            }
                        )
            logger.info(f"获取到 {len(notification_methods)} 个通知方式")
        except Exception as e:
            logger.warning(f"获取通知方式失败: {e}")
            notification_methods = []

        # 构建响应数据
        base_data = {
            k: v
            for k, v in db_obj.__dict__.items()
            if not k.startswith("_")
            and k
            not in [
                "responsible_persons",
                "notification_methods",
            ]
        }
        logger.info(f"Base data created successfully for subscription: {base_data.get('name', 'Unknown')}")

        response_data = {
            **base_data,
            # 覆盖需要特殊处理的字段
            "notification_methods": notification_methods,
            # 添加responsible_persons字段
            "responsible_persons": db_obj.responsible_persons or [],
            # 添加assistant_name字段（如果存在的话）
            "assistant_name": getattr(db_obj, "assistant_name", None),
        }

        return response_data

    @staticmethod
    async def get_ai_subscription_list(
        db: AsyncSession, *, params: Optional[AISubscriptionQueryParams] = None, page: int = 1, size: int = 10
    ) -> PageData[Dict[str, Any]]:
        """获取AI订阅列表"""
        skip = (page - 1) * size

        # 获取列表和总数
        items = await crud_ai_subscription.get_list(db, params=params, skip=skip, limit=size)
        total = await crud_ai_subscription.get_count(db, params=params)

        # 转换为响应格式
        records = []
        for item in items:
            record = await AISubscriptionService._convert_to_response_model(db, item)
            records.append(record)

        # 计算分页信息
        from math import ceil

        total_pages = ceil(total / size) if total > 0 else 1

        # 返回PageData格式
        result = PageData(
            items=records,
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

        return result

    @staticmethod
    async def get_all_ai_subscriptions(db: AsyncSession) -> List[Dict[str, Any]]:
        """获取所有AI订阅（不分页）"""
        items = await crud_ai_subscription.get_list_with_assistant_name(db, skip=0, limit=1000)

        records = []
        for item in items:
            record = await AISubscriptionService._convert_to_response_model(db, item)
            records.append(record)
        return records

    @staticmethod
    async def get_ai_subscription(db: AsyncSession, *, id: int) -> Dict[str, Any]:
        """获取AI订阅详情"""
        db_obj = await crud_ai_subscription.get(db, id=id)
        if not db_obj:
            raise NotFoundError(msg=f"AI订阅 {id} 不存在")

        return await AISubscriptionService._convert_to_response_model(db, db_obj)

    @staticmethod
    async def get_ai_subscription_by_name(db: AsyncSession, *, name: str) -> Dict[str, Any]:
        """通过名称获取AI订阅详情"""
        db_obj = await crud_ai_subscription.get_by_name(db, name=name)
        if not db_obj:
            raise NotFoundError(msg=f"AI订阅 '{name}' 不存在")

        return await AISubscriptionService._convert_to_response_model(db, db_obj)

    @staticmethod
    async def create_ai_subscription(db: AsyncSession, *, obj_in: AISubscriptionCreate, user_id: int) -> Dict[str, Any]:
        """创建AI订阅"""
        try:
            # 检查名称是否已存在
            existing = await crud_ai_subscription.get_by_name(db, name=obj_in.name)
            if existing:
                raise ForbiddenError(msg=f"订阅名称 '{obj_in.name}' 已存在")

            # 创建订阅，设置user_id
            db_obj = await crud_ai_subscription.create(db, obj_in=obj_in, user_id=user_id)

            # 创建调度任务（如果失败，整个订阅创建都会失败）
            scheduler = await subscription_scheduler_manager.create_scheduler_for_subscription(db, db_obj)
            if not scheduler:
                raise Exception(f"为订阅 '{db_obj.name}' 创建调度任务失败 - 检查日志获取详细信息")

            # 提交事务
            await db.commit()

            # 重新获取包含关联关系的订阅对象
            db_obj_with_relations = await crud_ai_subscription.get(db, id=db_obj.id)

            return await AISubscriptionService._convert_to_response_model(db, db_obj_with_relations)
        except Exception as e:
            # 发生异常时回滚事务
            await db.rollback()
            raise e

    @staticmethod
    async def update_ai_subscription(db: AsyncSession, *, id: int, obj_in: AISubscriptionUpdate) -> Dict[str, Any]:
        """更新AI订阅"""
        try:
            db_obj = await crud_ai_subscription.get(db, id=id)
            if not db_obj:
                raise NotFoundError(msg=f"AI订阅 {id} 不存在")

            # 如果更新名称，检查是否已存在
            if obj_in.name and obj_in.name != db_obj.name:
                existing = await crud_ai_subscription.get_by_name(db, name=obj_in.name)
                if existing:
                    raise ForbiddenError(msg=f"订阅名称 '{obj_in.name}' 已存在")

            # 如果更新scheduler_id，进行应用层验证
            # 注释掉scheduler_id验证，因为该字段已被删除
            # if hasattr(obj_in, "scheduler_id") and obj_in.scheduler_id is not None:
            #     from backend.app.admin.service.subscription_scheduler_manager import SubscriptionSchedulerManager
            #     if not await SubscriptionSchedulerManager.validate_scheduler_relation(db, id, obj_in.scheduler_id):
            #         raise ForbiddenError(msg=f"调度任务 {obj_in.scheduler_id} 关联验证失败")

            updated_obj = await crud_ai_subscription.update(db, db_obj=db_obj, obj_in=obj_in)

            # 更新调度任务
            await subscription_scheduler_manager.update_scheduler_for_subscription(db, updated_obj)

            # 提交事务
            await db.commit()
            await db.refresh(updated_obj)

            return await AISubscriptionService._convert_to_response_model(db, updated_obj)
        except Exception as e:
            await db.rollback()
            raise e

    @staticmethod
    async def delete_ai_subscription(db: AsyncSession, *, ids: List[int]) -> Dict[str, Any]:
        """删除AI订阅"""
        try:
            # 先删除关联的调度任务
            for subscription_id in ids:
                await subscription_scheduler_manager.delete_scheduler_for_subscription(db, subscription_id)

            deleted_count = await crud_ai_subscription.delete_batch(db, ids=ids)

            # 提交事务
            await db.commit()

            return {"deleted_count": deleted_count, "message": f"成功删除 {deleted_count} 个AI订阅"}
        except Exception as e:
            await db.rollback()
            raise e

    @staticmethod
    async def clone_ai_subscription(db: AsyncSession, *, id: int, new_name: str) -> Dict[str, Any]:
        """克隆AI订阅"""
        try:
            cloned_obj = await crud_ai_subscription.clone(db, id=id, new_name=new_name)
            if not cloned_obj:
                raise NotFoundError(msg=f"AI订阅 {id} 不存在")

            return await AISubscriptionService._convert_to_response_model(db, cloned_obj)
        except ValueError as e:
            raise ForbiddenError(msg=str(e))

    @staticmethod
    async def toggle_subscription_status(db: AsyncSession, *, id: int) -> Dict[str, Any]:
        """切换订阅状态"""
        db_obj = await crud_ai_subscription.get(db, id=id)
        if not db_obj:
            raise NotFoundError(msg=f"AI订阅 {id} 不存在")

        # 切换状态
        new_status = not db_obj.status
        updated_obj = await crud_ai_subscription.update(db, db_obj=db_obj, obj_in={"status": new_status})

        # 同步调度任务状态
        await subscription_scheduler_manager.sync_subscription_scheduler(db, id)

        status_text = "启用" if new_status else "禁用"
        return {
            **await AISubscriptionService._convert_to_response_model(db, updated_obj),
            "message": f"订阅已{status_text}",
        }

    @staticmethod
    async def execute_subscription_now(db: AsyncSession, *, id: int, user_id: Optional[int] = None) -> Dict[str, Any]:
        """立即执行订阅"""
        return await subscription_scheduler_manager.execute_subscription_now(db, id, user_id)

    @staticmethod
    async def get_subscription_execution_history(db: AsyncSession, *, id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """获取订阅执行历史"""
        return await subscription_scheduler_manager.get_subscription_execution_history(db, id, limit)

    @staticmethod
    async def get_subscription_types(db: AsyncSession) -> List[Dict[str, str]]:
        """获取AI订阅类型列表"""
        # 使用枚举类获取订阅类型
        return SubscriptionType.get_all_types()

    @staticmethod
    async def get_notification_methods(db: AsyncSession) -> List[Dict[str, Any]]:
        """获取通知方式列表"""
        try:
            items = await crud_ai_subscription_notification_method.get_list(db, status=True, skip=0, limit=100)
            result = []
            for item in items:
                result.append(
                    {
                        "id": item.id,
                        "name": item.name,
                        "type": item.type,
                        "config": item.config,
                        "status": item.status,
                        "created_time": item.created_time.isoformat() if item.created_time else None,
                        "updated_time": item.updated_time.isoformat() if item.updated_time else None,
                    }
                )
            return result
        except Exception:
            # 如果表不存在或没有数据，返回空列表
            return []

    @staticmethod
    async def update_analysis_status(db: AsyncSession, *, id: int) -> Dict[str, Any]:
        """更新分析状态"""
        try:
            db_obj = await crud_ai_subscription.get(db, id=id)
            if not db_obj:
                raise NotFoundError(msg=f"AI订阅 {id} 不存在")

            # 更新分析次数和最后分析时间
            db_obj.ai_analysis_count += 1
            db_obj.last_analysis_time = datetime.now()

            await db.commit()
            await db.refresh(db_obj)

            return await AISubscriptionService._convert_to_response_model(db, db_obj)
        except Exception as e:
            await db.rollback()
            raise e
