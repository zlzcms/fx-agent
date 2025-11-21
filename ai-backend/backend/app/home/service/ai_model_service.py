#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# 确保admin模块的模型已正确导入
try:
    from backend.app.admin.model.ai_model import AIModel
except ImportError:
    # 如果导入失败，创建一个简单的模型类用于测试
    from sqlalchemy import Boolean, Float, String, Text
    from sqlalchemy.orm import Mapped, mapped_column

    from backend.common.model import Base

    class AIModel(Base):
        """AI模型配置表"""

        __tablename__ = "ai_models"

        id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
        name: Mapped[str] = mapped_column(String(100), index=True)
        api_key: Mapped[str] = mapped_column(Text)
        model_type: Mapped[str] = mapped_column(String(50), index=True)
        model: Mapped[str] = mapped_column(String(100))
        temperature: Mapped[float] = mapped_column(Float, default=0.75)
        base_url: Mapped[Optional[str]] = mapped_column(String(500), default=None)
        status: Mapped[bool] = mapped_column(Boolean, default=True, index=True)


class AIModelService:
    """AI模型服务"""

    async def get_all_enabled_models(self, db: AsyncSession) -> List[AIModel]:
        """
        获取所有启用的AI模型

        参数:
            db: 数据库会话

        返回:
            启用的AI模型列表
        """
        try:
            stmt = (
                select(AIModel)
                .where(AIModel.status == True, AIModel.deleted_at.is_(None))
                .order_by(AIModel.created_time.desc())
            )
            result = await db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            print(f"获取AI模型列表出错: {str(e)}")
            # 出错时返回空列表
            return []

    async def get_model_by_id(self, db: AsyncSession, model_id: str) -> Optional[AIModel]:
        """
        通过ID获取AI模型

        参数:
            db: 数据库会话
            model_id: 模型ID

        返回:
            AI模型，如果不存在则返回None
        """
        try:
            stmt = select(AIModel).where(AIModel.id == model_id, AIModel.deleted_at.is_(None))
            result = await db.execute(stmt)
            return result.scalars().first()
        except Exception as e:
            print(f"获取AI模型详情出错: {str(e)}")
            return None

    async def get_default_model_id(self, db: AsyncSession) -> Optional[str]:
        """
        获取系统默认AI模型ID

        参数:
            db: 数据库会话

        返回:
            默认模型ID，如果未设置则返回None
        """
        try:
            from backend.plugin.config.crud.crud_config import config_dao

            config = await config_dao.get_by_key(db, "ai_default_model_id")
            if config and config.value:
                return config.value
            return None
        except Exception as e:
            print(f"获取默认模型ID出错: {str(e)}")
            return None


# 创建服务实例
ai_model_service = AIModelService()
