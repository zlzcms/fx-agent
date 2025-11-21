#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import secrets

from datetime import datetime
from typing import List, Optional, Sequence

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_crud_plus import CRUDPlus

from backend.app.admin.model.api_key import ApiKey
from backend.app.admin.schema.api_key import CreateApiKeyParams, UpdateApiKeyParams


class CRUDApiKey(CRUDPlus[ApiKey]):
    """API Key CRUD操作"""

    @staticmethod
    def generate_api_key() -> tuple[str, str]:
        """
        生成API Key和Secret
        返回: (api_key, api_secret)
        """
        # 生成一个安全的随机字符串作为API Key
        api_key = f"ak_{secrets.token_urlsafe(32)}"
        # 生成Secret用于签名验证（可选）
        api_secret = secrets.token_urlsafe(32)
        return api_key, api_secret

    async def get(self, db: AsyncSession, *, id: int) -> Optional[ApiKey]:
        """根据ID获取API Key（排除已删除）"""
        result = await db.execute(select(self.model).where(and_(self.model.id == id, self.model.deleted_at.is_(None))))
        return result.scalars().first()

    async def get_by_api_key(self, db: AsyncSession, *, api_key: str) -> Optional[ApiKey]:
        """根据API Key值获取API Key（排除已删除和已停用的）"""
        result = await db.execute(
            select(self.model).where(
                and_(
                    self.model.api_key == api_key,
                    self.model.deleted_at.is_(None),
                    self.model.status == 1,  # 只返回启用状态的
                )
            )
        )
        return result.scalars().first()

    async def get_list(
        self,
        db: AsyncSession,
        *,
        key_name: Optional[str] = None,
        status: Optional[int] = None,
        user_id: Optional[int] = None,
        page: int = 1,
        size: int = 10,
    ) -> tuple[Sequence[ApiKey], int]:
        """获取API Key分页列表（排除已删除）"""
        query = select(self.model)

        conditions = [self.model.deleted_at.is_(None)]  # 基础条件：未删除
        if key_name:
            conditions.append(self.model.key_name.ilike(f"%{key_name}%"))
        if status is not None:
            conditions.append(self.model.status == status)
        if user_id is not None:
            conditions.append(self.model.user_id == user_id)

        if conditions:
            query = query.where(and_(*conditions))

        # 获取总数
        count_query = select(func.count(self.model.id)).where(and_(*conditions))
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 分页查询
        query = query.order_by(self.model.created_time.desc())
        query = query.offset((page - 1) * size).limit(size)
        result = await db.execute(query)
        keys = result.scalars().all()

        return keys, total

    async def create(self, db: AsyncSession, *, obj_in: CreateApiKeyParams, user_id: Optional[int] = None) -> ApiKey:
        """创建API Key"""
        api_key, api_secret = self.generate_api_key()

        db_obj = self.model(
            key_name=obj_in.key_name,
            api_key=api_key,
            api_secret=api_secret,
            description=obj_in.description,
            expires_at=obj_in.expires_at,
            ip_whitelist=obj_in.ip_whitelist,
            permissions=obj_in.permissions,
            user_id=user_id,
        )

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)

        return db_obj

    async def update(self, db: AsyncSession, *, db_obj: ApiKey, obj_in: UpdateApiKeyParams) -> ApiKey:
        """更新API Key"""
        update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        await db.commit()
        await db.refresh(db_obj)

        return db_obj

    async def delete(self, db: AsyncSession, *, id: int) -> bool:
        """软删除API Key"""
        result = await db.execute(select(self.model).where(and_(self.model.id == id, self.model.deleted_at.is_(None))))
        db_obj = result.scalars().first()
        if db_obj:
            db_obj.deleted_at = datetime.now()
            await db.commit()
            return True
        return False

    async def delete_batch(self, db: AsyncSession, *, ids: List[int]) -> int:
        """批量软删除API Key"""
        result = await db.execute(
            select(self.model).where(and_(self.model.id.in_(ids), self.model.deleted_at.is_(None)))
        )
        db_objs = result.scalars().all()

        deleted_count = 0
        current_time = datetime.now()
        for db_obj in db_objs:
            db_obj.deleted_at = current_time
            deleted_count += 1

        await db.commit()
        return deleted_count

    async def update_usage(self, db: AsyncSession, *, api_key_obj: ApiKey, ip: Optional[str] = None) -> None:
        """更新API Key使用信息"""
        api_key_obj.last_used_at = datetime.now()
        api_key_obj.last_used_ip = ip
        api_key_obj.usage_count += 1
        await db.commit()

    async def check_key_name_exists(self, db: AsyncSession, *, key_name: str, exclude_id: Optional[int] = None) -> bool:
        """检查API Key名称是否已存在（排除已删除）"""
        conditions = [self.model.key_name == key_name, self.model.deleted_at.is_(None)]
        if exclude_id:
            conditions.append(self.model.id != exclude_id)

        query = select(self.model).where(and_(*conditions))
        result = await db.execute(query)
        return result.scalars().first() is not None

    async def check_expired(self, *, api_key_obj: ApiKey) -> bool:
        """检查API Key是否已过期"""
        if api_key_obj.expires_at is None:
            return False
        return datetime.now() > api_key_obj.expires_at

    async def check_ip_allowed(self, *, api_key_obj: ApiKey, ip: str) -> bool:
        """检查IP是否在白名单中"""
        if not api_key_obj.ip_whitelist:
            return True  # 没有白名单，允许所有IP

        allowed_ips = [ip.strip() for ip in api_key_obj.ip_whitelist.split(",") if ip.strip()]
        return ip in allowed_ips


crud_api_key = CRUDApiKey(ApiKey)
