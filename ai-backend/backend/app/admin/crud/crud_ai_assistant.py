# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-01-XX 10:00:00
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-20 18:45:00
from datetime import datetime
from typing import List, Optional, Sequence

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy_crud_plus import CRUDPlus

from backend.app.admin.crud.crud_ai_assistant_relations import (
    crud_ai_assistant_notification,
    crud_ai_assistant_personnel,
    crud_ai_assistant_template,
)
from backend.app.admin.model.ai_assistant import (
    AIAssistant,
    AIAssistantNotification,
    AIAssistantPermission,
    AIAssistantPersonnel,
    AIDataPermission,
    AINotificationMethod,
    AIPersonnel,
)
from backend.app.admin.schema.ai_assistant import (
    AIAssistantCreate,
    AIAssistantQueryParams,
    AIAssistantUpdate,
    AIDataPermissionCreate,
    AINotificationMethodCreate,
)
from backend.database.db import uuid4_str as get_uuid


def parse_datetime_string(datetime_str: str) -> datetime:
    """解析各种格式的时间字符串"""
    # 移除时区标识
    datetime_str = datetime_str.replace("Z", "+00:00")

    # 尝试多种格式
    formats_to_try = [
        "%Y-%m-%dT%H:%M:%S.%f%z",  # 完整格式带毫秒和时区
        "%Y-%m-%dT%H:%M:%S%z",  # 完整格式带时区
        "%Y-%m-%dT%H:%M:%S.%f",  # 完整格式带毫秒
        "%Y-%m-%dT%H:%M:%S",  # 完整格式
        "%Y-%m-%dT%H:%M",  # 缺少秒部分
    ]

    for fmt in formats_to_try:
        try:
            if "%z" in fmt:
                return datetime.fromisoformat(datetime_str)
            else:
                return datetime.strptime(datetime_str.split("+")[0].split("Z")[0], fmt)
        except ValueError:
            continue

    # 如果所有格式都失败，抛出异常
    raise ValueError(f"Unable to parse datetime string: {datetime_str}")


class CRUDAIAssistant(CRUDPlus[AIAssistant]):
    """AI助手CRUD操作"""

    async def get(
        self, db: AsyncSession, *, id: str, params: Optional[AIAssistantQueryParams] = None
    ) -> Optional[AIAssistant]:
        """获取AI助手详情，包含关联数据"""
        stmt = (
            select(self.model)
            .where(and_(self.model.id == id, self.model.deleted_at.is_(None)))
            .options(
                selectinload(self.model.personnel_relations),
                selectinload(self.model.notification_relations).selectinload(
                    AIAssistantNotification.notification_method
                ),
                # selectinload(self.model.permission_relations).selectinload(AIAssistantPermission.permission),
            )
        )
        if params:
            conditions = []
            if params.status is not None:
                conditions.append(self.model.status == params.status)
            if conditions:
                stmt = stmt.where(and_(*conditions))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, db: AsyncSession, *, name: str) -> Optional[AIAssistant]:
        """根据名称获取AI助手"""
        stmt = select(self.model).where(and_(self.model.name == name, self.model.deleted_at.is_(None)))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_list(
        self, db: AsyncSession, *, params: Optional[AIAssistantQueryParams] = None, skip: int = 0, limit: int = 100
    ) -> Sequence[AIAssistant]:
        """获取AI助手列表"""
        stmt = select(self.model).where(self.model.deleted_at.is_(None))

        if params:
            conditions = []
            if params.name:
                conditions.append(self.model.name.ilike(f"%{params.name}%"))
            if params.assistant_type_id:
                conditions.append(self.model.assistant_type_id == params.assistant_type_id)
            if params.ai_model_id:
                conditions.append(self.model.ai_model_id == params.ai_model_id)
            if params.responsible_person:
                # 这里需要查询关联表，暂时简化处理
                pass
            if params.status is not None:
                conditions.append(self.model.status == params.status)
            if params.is_template is not None:
                conditions.append(self.model.is_template == params.is_template)

            if conditions:
                stmt = stmt.where(and_(*conditions))

        stmt = stmt.offset(skip).limit(limit).order_by(self.model.created_time.desc())
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_count(self, db: AsyncSession, *, params: Optional[AIAssistantQueryParams] = None) -> int:
        """获取AI助手总数"""
        stmt = select(func.count(self.model.id)).where(self.model.deleted_at.is_(None))

        if params:
            conditions = []
            if params.name:
                conditions.append(self.model.name.ilike(f"%{params.name}%"))
            if params.assistant_type_id:
                conditions.append(self.model.assistant_type_id == params.assistant_type_id)
            if params.ai_model_id:
                conditions.append(self.model.ai_model_id == params.ai_model_id)
            if params.responsible_person:
                # 这里需要查询关联表，暂时简化处理
                pass
            if params.status is not None:
                conditions.append(self.model.status == params.status)
            if params.is_template is not None:
                conditions.append(self.model.is_template == params.is_template)

            if conditions:
                stmt = stmt.where(and_(*conditions))

        result = await db.execute(stmt)
        return result.scalar()

    async def create(self, db: AsyncSession, *, obj_in: AIAssistantCreate) -> AIAssistant:
        """创建AI助手"""
        # 生成UUID
        assistant_id = get_uuid()

        # 构建创建数据，排除init=False的字段
        db_data = {
            **obj_in.model_dump(
                exclude_unset=True,
                exclude={
                    "responsible_persons",
                    "notification_methods",
                    "data_sources",
                    "data_permissions",
                },
            ),
        }

        # 创建模型对象
        db_obj = self.model(**db_data)

        # 设置init=False的字段
        db_obj.id = assistant_id
        db_obj.created_time = datetime.now()

        db.add(db_obj)
        await db.flush()

        # 创建关联关系
        await self._create_relations(db, assistant_id=assistant_id, obj_in=obj_in)

        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, *, db_obj: AIAssistant, obj_in: AIAssistantUpdate) -> AIAssistant:
        """更新AI助手，包含关联关系"""
        # 更新基础字段
        update_data = obj_in.model_dump(exclude_unset=True, exclude_none=True)

        # 更新基础字段
        for field, value in update_data.items():
            if hasattr(db_obj, field) and field not in [
                "responsible_persons",
                "notification_methods",
                "data_sources",
                "data_permissions",
            ]:
                setattr(db_obj, field, value)

        # 更新data_sources到settings字段
        if obj_in.data_sources is not None:
            if not db_obj.settings:
                db_obj.settings = {}
            db_obj.settings["data_sources"] = obj_in.data_sources

        db_obj.updated_time = datetime.now()

        # 先更新关联关系（在同一个事务中）
        await self._update_relations(db, assistant_id=db_obj.id, obj_in=obj_in)

        # 统一提交事务
        await db.commit()
        await db.refresh(db_obj)

        # 重新获取包含关联数据的完整记录
        return await self.get(db, id=db_obj.id)

    async def delete(self, db: AsyncSession, *, id: str) -> bool:
        """软删除AI助手"""
        db_obj = await self.get(db, id=id)
        if db_obj:
            db_obj.deleted_at = datetime.now()
            await db.commit()
            return True
        return False

    async def delete_batch(self, db: AsyncSession, *, ids: List[str]) -> int:
        """批量软删除AI助手"""
        count = 0
        for assistant_id in ids:
            if await self.delete(db, id=assistant_id):
                count += 1
        return count

    async def toggle_status(self, db: AsyncSession, *, id: str, status: bool) -> Optional[AIAssistant]:
        """切换AI助手状态"""
        db_obj = await self.get(db, id=id)
        if db_obj:
            db_obj.status = status
            db_obj.updated_time = datetime.now()
            await db.commit()
            await db.refresh(db_obj)
        return db_obj

    async def clone(self, db: AsyncSession, *, id: str, new_name: str) -> Optional[AIAssistant]:
        """克隆AI助手"""
        # 获取原始数据
        original = await self.get(db, id=id)
        if not original:
            return None

        # 生成新ID
        new_id = get_uuid()

        # 复制数据，不包含init=False的字段
        obj_data = {
            "name": new_name,
            "type": original.type,
            "assistant_type_id": original.assistant_type_id,
            "ai_model_id": original.ai_model_id,
            "avatar": original.avatar,
            "description": original.description,
            "model_definition": original.model_definition,
            "execution_frequency": original.execution_frequency,
            "execution_time": original.execution_time,
            "status": original.status,
            "is_template": False,  # 克隆的助手默认不是模板
            "is_view_myself": original.is_view_myself,
            "data_limit": original.data_limit,
            "output_format": original.output_format,
            "output_data": original.output_data,
            "include_charts": original.include_charts,
            "auto_export": original.auto_export,
            "settings": original.settings,
            "ai_analysis_count": original.ai_analysis_count,
            "last_analysis_time": original.last_analysis_time,
        }

        new_obj = self.model(**obj_data)

        # 设置init=False的字段
        new_obj.id = new_id
        new_obj.created_time = datetime.now()

        db.add(new_obj)
        await db.flush()

        # 复制关联关系
        # ... 复制人员关联
        for relation in original.personnel_relations:
            personnel_relation = AIAssistantPersonnel()
            personnel_relation.id = get_uuid()
            personnel_relation.assistant_id = new_id
            personnel_relation.personnel_id = relation.personnel_id
            personnel_relation.created_time = datetime.now()
            db.add(personnel_relation)

        # ... 复制通知方式关联
        for relation in original.notification_relations:
            notification_relation = AIAssistantNotification()
            notification_relation.id = get_uuid()
            notification_relation.assistant_id = new_id
            notification_relation.notification_id = relation.notification_id
            notification_relation.created_time = datetime.now()
            db.add(notification_relation)

        # ... 复制权限关联
        for relation in original.permission_relations:
            permission_relation = AIAssistantPermission()
            permission_relation.id = get_uuid()
            permission_relation.assistant_id = new_id
            permission_relation.permission_id = relation.permission_id
            permission_relation.created_time = datetime.now()
            db.add(permission_relation)

        await db.commit()
        await db.refresh(new_obj)
        return new_obj

    async def _create_relations(self, db: AsyncSession, *, assistant_id: str, obj_in: AIAssistantCreate) -> None:
        """创建关联关系"""
        # 创建人员关联 - 修改为接收完整人员数据
        if obj_in.responsible_persons:
            await crud_ai_assistant_personnel.create_relations(
                db, assistant_id=assistant_id, personnel_data=obj_in.responsible_persons
            )

        # 创建通知方式关联
        if obj_in.notification_methods:
            await crud_ai_assistant_notification.create_relations(
                db, assistant_id=assistant_id, notification_ids=obj_in.notification_methods
            )

        # 创建模板记录（如果设为模板）
        if obj_in.is_template:
            await crud_ai_assistant_template.create_template(
                db,
                assistant_id=assistant_id,
                is_open=True,  # 默认开启模板
            )

    async def _update_relations(self, db: AsyncSession, *, assistant_id: str, obj_in: AIAssistantUpdate) -> None:
        """更新关联关系"""
        # 更新人员关联 - 修改为接收完整人员数据
        if obj_in.responsible_persons is not None:
            await crud_ai_assistant_personnel.update_relations(
                db, assistant_id=assistant_id, personnel_data=obj_in.responsible_persons
            )

        # 更新通知方式关联
        if obj_in.notification_methods is not None:
            await crud_ai_assistant_notification.update_relations(
                db, assistant_id=assistant_id, notification_ids=obj_in.notification_methods
            )

        # 更新模板状态
        if obj_in.is_template is not None:
            # 检查当前是否存在模板记录
            existing_template = await crud_ai_assistant_template.get_by_assistant_id(db, assistant_id=assistant_id)

            if obj_in.is_template:
                # 如果设为模板但不存在模板记录，则创建
                if not existing_template:
                    await crud_ai_assistant_template.create_template(
                        db,
                        assistant_id=assistant_id,
                        is_open=True,  # 默认开启模板
                    )
            else:
                # 如果取消模板且存在模板记录，则删除
                if existing_template:
                    await crud_ai_assistant_template.delete_by_assistant_id(db, assistant_id=assistant_id)


class CRUDAIPersonnel(CRUDPlus[AIPersonnel]):
    """AI人员CRUD操作"""

    async def get(self, db: AsyncSession, *, id: str) -> Optional[AIPersonnel]:
        """根据ID获取人员"""
        stmt = select(self.model).where(self.model.id == id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[AIPersonnel]:
        """根据邮箱获取人员"""
        stmt = select(self.model).where(self.model.email == email)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_list(
        self,
        db: AsyncSession,
        *,
        name: Optional[str] = None,
        department: Optional[str] = None,
        status: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[AIPersonnel]:
        """获取人员列表"""
        stmt = select(self.model)

        if name:
            stmt = stmt.where(self.model.name.ilike(f"%{name}%"))
        if department:
            stmt = stmt.where(self.model.department.ilike(f"%{department}%"))
        if status is not None:
            stmt = stmt.where(self.model.status == status)

        stmt = stmt.order_by(self.model.created_time.desc()).offset(skip).limit(limit)

        result = await db.execute(stmt)
        return result.scalars().all()


# AIPersonnel 相关方法已删除，改为使用 sys_user 表


class CRUDAINotificationMethod(CRUDPlus[AINotificationMethod]):
    """AI通知方式CRUD操作"""

    async def get(self, db: AsyncSession, *, id: str) -> Optional[AINotificationMethod]:
        """根据ID获取通知方式"""
        stmt = select(self.model).where(self.model.id == id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_list(
        self,
        db: AsyncSession,
        *,
        type: Optional[str] = None,
        status: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[AINotificationMethod]:
        """获取通知方式列表"""
        stmt = select(self.model)

        if type:
            stmt = stmt.where(self.model.type == type)
        if status is not None:
            stmt = stmt.where(self.model.status == status)

        stmt = stmt.order_by(self.model.created_time.desc()).offset(skip).limit(limit)

        result = await db.execute(stmt)
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: AINotificationMethodCreate) -> AINotificationMethod:
        """创建通知方式"""
        obj_data = obj_in.model_dump()

        # 创建对象（不包含init=False的字段）
        db_obj = self.model(**obj_data)

        # 设置init=False的字段
        db_obj.id = get_uuid()
        db_obj.created_time = datetime.now()

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


class CRUDAIDataPermission(CRUDPlus[AIDataPermission]):
    """AI数据权限CRUD操作"""

    async def get(self, db: AsyncSession, *, id: str) -> Optional[AIDataPermission]:
        """根据ID获取数据权限"""
        stmt = select(self.model).where(self.model.id == id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_list(
        self,
        db: AsyncSession,
        *,
        permission_type: Optional[str] = None,
        status: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[AIDataPermission]:
        """获取数据权限列表"""
        stmt = select(self.model)

        if permission_type:
            stmt = stmt.where(self.model.permission_type == permission_type)
        if status is not None:
            stmt = stmt.where(self.model.status == status)

        stmt = stmt.order_by(self.model.created_time.desc()).offset(skip).limit(limit)

        result = await db.execute(stmt)
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: AIDataPermissionCreate) -> AIDataPermission:
        """创建数据权限"""
        obj_data = obj_in.model_dump()

        # 创建对象（不包含init=False的字段）
        db_obj = self.model(**obj_data)

        # 设置init=False的字段
        db_obj.id = get_uuid()
        db_obj.created_time = datetime.now()

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


# 创建CRUD实例
crud_ai_assistant = CRUDAIAssistant(AIAssistant)
crud_ai_personnel = CRUDAIPersonnel(AIPersonnel)
crud_ai_notification_method = CRUDAINotificationMethod(AINotificationMethod)
crud_ai_data_permission = CRUDAIDataPermission(AIDataPermission)
