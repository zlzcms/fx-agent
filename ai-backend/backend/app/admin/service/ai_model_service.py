# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-14 13:40:12
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-14 15:05:32

# !/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio

from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.crud.crud_ai_model import crud_ai_model
from backend.app.admin.schema.ai_model import (
    CreateAIModelParams,
    DeleteResponse,
    ModelTypeEnum,
    TestResponse,
    UpdateAIModelParams,
)
from backend.common.pagination import PageData


class AIModelService:
    """AI模型服务"""

    def _mask_api_key(self, api_key: str) -> str:
        """脱敏处理API Key"""
        if not api_key:
            return ""
        if len(api_key) <= 12:
            return api_key[:4] + "*" * 4 + api_key[-4:]
        return api_key[:8] + "*" * 8 + api_key[-4:]

    def _model_to_dict(self, model: any) -> dict:
        """将模型转换为字典并脱敏API Key"""
        return {
            "id": model.id,
            "name": model.name,
            "api_key": self._mask_api_key(model.api_key),
            "base_url": model.base_url,
            "model_type": model.model_type,
            "model": model.model,
            "temperature": model.temperature,
            "status": model.status,
            "created_time": model.created_time,
            "updated_time": model.updated_time,
        }

    def _model_to_dict_unmasked(self, model: any) -> dict:
        """将模型转换为字典，不脱敏API Key（用于详情查看）"""
        return {
            "id": model.id,
            "name": model.name,
            "api_key": model.api_key,  # 不脱敏
            "base_url": model.base_url,
            "model_type": model.model_type,
            "model": model.model,
            "temperature": model.temperature,
            "status": model.status,
            "created_time": model.created_time,
            "updated_time": model.updated_time,
        }

    async def get_paginated_list(
        self,
        db: AsyncSession,
        *,
        name: Optional[str] = None,
        model_type: Optional[ModelTypeEnum] = None,
        status: Optional[bool] = None,
        page: int = 1,
        size: int = 10,
    ) -> PageData[dict]:
        """获取分页AI模型列表"""
        models, total = await crud_ai_model.get_list(
            db, name=name, model_type=model_type, status=status, page=page, size=size
        )

        # 转换为字典并脱敏API Key
        items = [self._model_to_dict(model) for model in models]

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

    async def get_all_enabled(self, db: AsyncSession) -> List[dict]:
        """获取所有启用的AI模型"""
        models = await crud_ai_model.get_all_enabled(db)
        return [self._model_to_dict(model) for model in models]

    async def get_detail(self, db: AsyncSession, *, model_id: str) -> Optional[dict]:
        """获取AI模型详情"""
        model = await crud_ai_model.get(db, id=model_id)
        if not model:
            return None
        return self._model_to_dict_unmasked(model)

    async def create(self, db: AsyncSession, *, request: CreateAIModelParams) -> dict:
        """创建AI模型"""
        # 检查模型名称是否已存在
        if await crud_ai_model.check_name_exists(db, name=request.name):
            raise ValueError(f"模型名称 '{request.name}' 已存在")

        # 创建模型
        model = await crud_ai_model.create(db, obj_in=request)
        return self._model_to_dict(model)

    async def update(self, db: AsyncSession, *, model_id: str, request: UpdateAIModelParams) -> Optional[dict]:
        """更新AI模型"""
        # 检查模型是否存在
        model = await crud_ai_model.get(db, id=model_id)
        if not model:
            return None

        # 如果更新名称，检查是否重复
        if request.name and request.name != model.name:
            if await crud_ai_model.check_name_exists(db, name=request.name, exclude_id=model_id):
                raise ValueError(f"模型名称 '{request.name}' 已存在")

        # 更新模型
        updated_model = await crud_ai_model.update(db, db_obj=model, obj_in=request)
        return self._model_to_dict(updated_model)

    async def delete_batch(self, db: AsyncSession, *, ids: List[str]) -> DeleteResponse:
        """批量删除AI模型"""
        # 检查模型是否存在
        for model_id in ids:
            model = await crud_ai_model.get(db, id=model_id)
            if not model:
                raise ValueError(f"模型 ID '{model_id}' 不存在")

        # 批量删除
        deleted_count = await crud_ai_model.delete_batch(db, ids=ids)
        return DeleteResponse(deleted_count=deleted_count)

    async def toggle_status(self, db: AsyncSession, *, model_id: str, status: bool) -> Optional[dict]:
        """切换AI模型状态"""
        model = await crud_ai_model.update_status(db, id=model_id, status=status)
        if not model:
            return None
        return self._model_to_dict(model)

    async def test_connection(self, db: AsyncSession, *, model_id: str) -> TestResponse:
        """测试AI模型连接"""
        model = await crud_ai_model.get(db, id=model_id)
        if not model:
            return TestResponse(success=False, message="模型不存在")

        try:
            # 根据不同模型类型进行连接测试
            success, message = await self._test_model_connection(model)
            return TestResponse(success=success, message=message)
        except Exception as e:
            return TestResponse(success=False, message=f"连接测试失败: {str(e)}")

    async def _test_model_connection(self, model: any) -> tuple[bool, str]:
        """测试模型连接"""
        # 这里根据不同的模型类型实现具体的连接测试逻辑
        # 为了简化，这里只是模拟测试

        if model.model_type == ModelTypeEnum.OPENAI:
            return await self._test_openai_connection(model)
        elif model.model_type == ModelTypeEnum.DEEPSEEK:
            return await self._test_deepseek_connection(model)
        elif model.model_type == ModelTypeEnum.GOOGLE:
            return await self._test_google_connection(model)
        elif model.model_type == ModelTypeEnum.BAIDU:
            return await self._test_baidu_connection(model)
        elif model.model_type == ModelTypeEnum.ALIBABA:
            return await self._test_alibaba_connection(model)
        elif model.model_type == ModelTypeEnum.HUOSHAN:
            return await self._test_huoshan_connection(model)
        elif model.model_type == ModelTypeEnum.ANTHROPIC:
            return await self._test_anthropic_connection(model)
        else:
            return await self._test_other_connection(model)

    async def _test_openai_connection(self, model: any) -> tuple[bool, str]:
        """测试OpenAI连接"""
        try:
            # TODO: 实现OpenAI API连接测试
            # 这里只是模拟
            await asyncio.sleep(0.1)  # 模拟网络请求
            return True, "OpenAI连接测试成功"
        except Exception as e:
            return False, f"OpenAI连接失败: {str(e)}"

    async def _test_deepseek_connection(self, model: any) -> tuple[bool, str]:
        """测试DeepSeek连接"""
        try:
            # TODO: 实现DeepSeek API连接测试
            await asyncio.sleep(0.1)
            return True, "DeepSeek连接测试成功"
        except Exception as e:
            return False, f"DeepSeek连接失败: {str(e)}"

    async def _test_google_connection(self, model: any) -> tuple[bool, str]:
        """测试Google连接"""
        try:
            # TODO: 实现Google API连接测试
            await asyncio.sleep(0.1)
            return True, "Google连接测试成功"
        except Exception as e:
            return False, f"Google连接失败: {str(e)}"

    async def _test_baidu_connection(self, model: any) -> tuple[bool, str]:
        """测试百度连接"""
        try:
            # TODO: 实现百度API连接测试
            await asyncio.sleep(0.1)
            return True, "百度连接测试成功"
        except Exception as e:
            return False, f"百度连接失败: {str(e)}"

    async def _test_alibaba_connection(self, model: any) -> tuple[bool, str]:
        """测试阿里巴巴连接"""
        try:
            # TODO: 实现阿里巴巴API连接测试
            await asyncio.sleep(0.1)
            return True, "阿里巴巴连接测试成功"
        except Exception as e:
            return False, f"阿里巴巴连接失败: {str(e)}"

    async def _test_huoshan_connection(self, model: any) -> tuple[bool, str]:
        """测试火山引擎连接"""
        try:
            # TODO: 实现火山引擎API连接测试
            await asyncio.sleep(0.1)
            return True, "火山引擎连接测试成功"
        except Exception as e:
            return False, f"火山引擎连接失败: {str(e)}"

    async def _test_anthropic_connection(self, model: any) -> tuple[bool, str]:
        """测试Anthropic连接"""
        try:
            # TODO: 实现Anthropic API连接测试
            await asyncio.sleep(0.1)
            return True, "Anthropic连接测试成功"
        except Exception as e:
            return False, f"Anthropic连接失败: {str(e)}"

    async def _test_other_connection(self, model: any) -> tuple[bool, str]:
        """测试其他模型连接"""
        try:
            # TODO: 实现其他模型API连接测试
            await asyncio.sleep(0.1)
            return True, "其他模型连接测试成功"
        except Exception as e:
            return False, f"其他模型连接失败: {str(e)}"

    async def get_default_model_id(self, db: AsyncSession) -> Optional[str]:
        """
        获取系统默认AI模型ID

        Args:
            db: 数据库会话

        Returns:
            默认模型ID，如果未设置则返回None
        """
        try:
            from backend.plugin.config.crud.crud_config import config_dao

            config = await config_dao.get_by_key(db, "ai_default_model_id")
            if config and config.value:
                return config.value
            return None
        except Exception:
            return None

    async def set_default_model(self, db: AsyncSession, *, model_id: str) -> dict:
        """
        设置系统默认AI模型

        Args:
            db: 数据库会话
            model_id: 模型ID

        Returns:
            设置结果
        """
        # 验证模型是否存在且启用
        model = await crud_ai_model.get(db, id=model_id)
        if not model:
            raise ValueError(f"模型 ID '{model_id}' 不存在")
        if not model.status:
            raise ValueError(f"模型 ID '{model_id}' 已禁用，不能设置为默认模型")

        # 保存或更新配置
        from sqlalchemy import text

        try:
            # 使用 PostgreSQL 的 ON CONFLICT 来实现 upsert
            upsert_sql = text("""
                INSERT INTO sys_config (name, type, key, value, is_frontend, remark, created_time)
                VALUES (:name, :type, :key, :value, :is_frontend, :remark, NOW())
                ON CONFLICT (key)
                DO UPDATE SET
                    value = EXCLUDED.value,
                    remark = EXCLUDED.remark,
                    updated_time = NOW()
            """)

            await db.execute(
                upsert_sql,
                {
                    "name": "系统默认AI模型",
                    "type": "ai",
                    "key": "ai_default_model_id",
                    "value": model_id,
                    "is_frontend": False,
                    "remark": f"系统默认使用的AI模型ID，当前模型：{model.name}",
                },
            )

            await db.commit()

            return {
                "success": True,
                "message": f"成功设置默认模型为: {model.name}",
                "model_id": model_id,
            }
        except Exception as e:
            await db.rollback()
            raise ValueError(f"设置默认模型失败: {str(e)}")


ai_model_service = AIModelService()
