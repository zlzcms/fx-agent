#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import uuid

from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.home.model.ai_chat_file import AIChatFile
from backend.app.home.schema.ai_chat_file import AIChatFileCreate, AIChatFileUpdate, ExportResultCreate


class CRUDAIChatFile:
    """AI聊天文件CRUD操作"""

    async def create(self, db: AsyncSession, *, obj_in: AIChatFileCreate) -> AIChatFile:
        """创建新的聊天文件记录

        参数:
            db: 数据库会话
            obj_in: 文件创建数据

        返回:
            创建的文件记录
        """
        # 生成文件ID
        file_id = obj_in.id or str(uuid.uuid4())

        try:
            # 创建对象
            db_obj = AIChatFile(
                id=file_id,
                chat_message_id=obj_in.chat_message_id,
                filename=obj_in.filename,
                file_path=obj_in.file_path,
                file_paths=obj_in.file_paths,
                export_directory=obj_in.export_directory,
                task_id=obj_in.task_id,
                data_source=obj_in.data_source,
                export_time=obj_in.export_time,
                url=obj_in.url,
                file_size=obj_in.file_size,
                error_message=obj_in.error_message,
                file_type=obj_in.file_type,
                status=obj_in.status,
            )

            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)

            return db_obj
        except Exception as e:
            await db.rollback()
            raise Exception(f"创建AIChatFile对象时出错: {str(e)}")

    async def create_from_export_result(self, db: AsyncSession, *, export_result: ExportResultCreate) -> AIChatFile:
        """从ExportResult创建文件记录

        参数:
            db: 数据库会话
            export_result: 导出结果数据

        返回:
            创建的文件记录
        """
        # 生成文件ID
        file_id = str(uuid.uuid4())

        try:
            # 创建对象
            db_obj = AIChatFile(
                id=file_id,
                chat_message_id=export_result.chat_message_id,
                filename=export_result.filename,
                file_path=export_result.file_path,
                file_paths=export_result.file_paths,
                export_directory=export_result.export_directory,
                task_id=export_result.task_id,
                data_source=export_result.data_source,
                export_time=export_result.export_time,
                url=export_result.url,
                file_size=export_result.file_size,
                error_message=export_result.error_message,
                file_type=export_result.file_type,
                status=export_result.success,  # 使用success作为status
            )

            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)

            return db_obj
        except Exception as e:
            await db.rollback()
            raise Exception(f"从ExportResult创建AIChatFile对象时出错: {str(e)}")

    async def get(self, db: AsyncSession, *, file_id: str) -> Optional[AIChatFile]:
        """获取文件记录

        参数:
            db: 数据库会话
            file_id: 文件ID

        返回:
            找到的文件记录，如果不存在则返回None
        """
        stmt = select(AIChatFile).where(AIChatFile.id == file_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_chat_message(self, db: AsyncSession, *, chat_message_id: str) -> List[AIChatFile]:
        """获取聊天消息的所有文件记录

        参数:
            db: 数据库会话
            chat_message_id: 聊天消息ID

        返回:
            文件记录列表
        """
        stmt = (
            select(AIChatFile)
            .where(and_(AIChatFile.chat_message_id == chat_message_id, AIChatFile.status))
            .order_by(desc(AIChatFile.created_time))
        )

        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_by_task_id(self, db: AsyncSession, *, task_id: str) -> List[AIChatFile]:
        """根据任务ID获取文件记录

        参数:
            db: 数据库会话
            task_id: 任务ID

        返回:
            文件记录列表
        """
        stmt = (
            select(AIChatFile)
            .where(and_(AIChatFile.task_id == task_id, AIChatFile.status))
            .order_by(desc(AIChatFile.created_time))
        )

        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_by_data_source(self, db: AsyncSession, *, data_source: str, limit: int = 100) -> List[AIChatFile]:
        """根据数据源获取文件记录

        参数:
            db: 数据库会话
            data_source: 数据源
            limit: 限制返回数量

        返回:
            文件记录列表
        """
        stmt = (
            select(AIChatFile)
            .where(and_(AIChatFile.data_source == data_source, AIChatFile.status))
            .order_by(desc(AIChatFile.created_time))
            .limit(limit)
        )

        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None
    ) -> List[AIChatFile]:
        """获取多个文件记录

        参数:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 限制返回数量
            filters: 过滤条件

        返回:
            文件记录列表
        """
        stmt = select(AIChatFile).where(AIChatFile.status)

        # 应用过滤条件
        if filters:
            for key, value in filters.items():
                if hasattr(AIChatFile, key) and value is not None:
                    if isinstance(value, str):
                        stmt = stmt.where(getattr(AIChatFile, key).ilike(f"%{value}%"))
                    else:
                        stmt = stmt.where(getattr(AIChatFile, key) == value)

        stmt = stmt.order_by(desc(AIChatFile.created_time)).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def update(self, db: AsyncSession, *, db_obj: AIChatFile, obj_in: AIChatFileUpdate) -> AIChatFile:
        """更新文件记录

        参数:
            db: 数据库会话
            db_obj: 数据库中的文件对象
            obj_in: 更新数据

        返回:
            更新后的文件记录
        """
        update_data = obj_in.dict(exclude_unset=True)

        try:
            for field, value in update_data.items():
                setattr(db_obj, field, value)

            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)

            return db_obj
        except Exception as e:
            await db.rollback()
            raise Exception(f"更新AIChatFile对象时出错: {str(e)}")

    async def update_by_id(self, db: AsyncSession, *, file_id: str, obj_in: AIChatFileUpdate) -> Optional[AIChatFile]:
        """根据ID更新文件记录

        参数:
            db: 数据库会话
            file_id: 文件ID
            obj_in: 更新数据

        返回:
            更新后的文件记录，如果不存在则返回None
        """
        db_obj = await self.get(db, file_id=file_id)
        if not db_obj:
            return None

        return await self.update(db, db_obj=db_obj, obj_in=obj_in)

    async def delete(self, db: AsyncSession, *, file_id: str) -> bool:
        """删除文件记录（软删除）

        参数:
            db: 数据库会话
            file_id: 文件ID

        返回:
            是否删除成功
        """
        try:
            stmt = update(AIChatFile).where(AIChatFile.id == file_id).values(status=False)
            result = await db.execute(stmt)
            await db.commit()

            return result.rowcount > 0
        except Exception as e:
            await db.rollback()
            raise Exception(f"删除AIChatFile对象时出错: {str(e)}")

    async def hard_delete(self, db: AsyncSession, *, file_id: str) -> bool:
        """硬删除文件记录

        参数:
            db: 数据库会话
            file_id: 文件ID

        返回:
            是否删除成功
        """
        try:
            db_obj = await self.get(db, file_id=file_id)
            if not db_obj:
                return False

            await db.delete(db_obj)
            await db.commit()

            return True
        except Exception as e:
            await db.rollback()
            raise Exception(f"硬删除AIChatFile对象时出错: {str(e)}")

    async def count(self, db: AsyncSession, *, filters: Optional[Dict[str, Any]] = None) -> int:
        """统计文件记录数量

        参数:
            db: 数据库会话
            filters: 过滤条件

        返回:
            记录数量
        """
        stmt = select(AIChatFile).where(AIChatFile.status)

        # 应用过滤条件
        if filters:
            for key, value in filters.items():
                if hasattr(AIChatFile, key) and value is not None:
                    if isinstance(value, str):
                        stmt = stmt.where(getattr(AIChatFile, key).ilike(f"%{value}%"))
                    else:
                        stmt = stmt.where(getattr(AIChatFile, key) == value)

        result = await db.execute(stmt)
        return len(result.scalars().all())

    async def search(self, db: AsyncSession, *, query: str, skip: int = 0, limit: int = 100) -> List[AIChatFile]:
        """搜索文件记录

        参数:
            db: 数据库会话
            query: 搜索查询
            skip: 跳过的记录数
            limit: 限制返回数量

        返回:
            匹配的文件记录列表
        """
        stmt = (
            select(AIChatFile)
            .where(
                and_(
                    AIChatFile.status,
                    or_(
                        AIChatFile.filename.ilike(f"%{query}%"),
                        AIChatFile.task_id.ilike(f"%{query}%"),
                        AIChatFile.data_source.ilike(f"%{query}%"),
                        AIChatFile.file_type.ilike(f"%{query}%"),
                    ),
                )
            )
            .order_by(desc(AIChatFile.created_time))
            .offset(skip)
            .limit(limit)
        )

        result = await db.execute(stmt)
        return result.scalars().all()


# 创建CRUD实例
ai_chat_file = CRUDAIChatFile()
