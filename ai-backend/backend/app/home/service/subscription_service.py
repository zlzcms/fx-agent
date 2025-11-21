#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.home.crud.crud_subscription import home_subscription_dao
from backend.common.exception.errors import NotFoundError
from backend.common.pagination import PageData


class HomeSubscriptionService:
    """Home订阅服务"""

    @staticmethod
    async def get_user_subscriptions(
        db: AsyncSession,
        *,
        user_id: str,
        name: Optional[str] = None,
        subscription_type: Optional[str] = None,
        assistant_name: Optional[str] = None,
        status: Optional[bool] = None,
        page: int = 1,
        size: int = 10,
    ) -> PageData[Dict[str, Any]]:
        """
        获取用户的订阅列表

        Args:
            db: 数据库会话
            user_id: 用户ID
            name: 订阅名称过滤
            subscription_type: 订阅类型过滤
            assistant_name: 助手名称过滤
            status: 状态过滤
            page: 页码
            size: 每页数量

        Returns:
            分页的订阅列表
        """
        skip = (page - 1) * size

        # 获取订阅列表和总数
        items = await home_subscription_dao.get_user_subscriptions(
            db,
            user_id=user_id,
            name=name,
            subscription_type=subscription_type,
            assistant_name=assistant_name,
            status=status,
            skip=skip,
            limit=size,
        )

        total = await home_subscription_dao.get_user_subscriptions_count(
            db,
            user_id=user_id,
            name=name,
            subscription_type=subscription_type,
            assistant_name=assistant_name,
            status=status,
        )

        # 转换为响应格式
        records = []
        for item in items:
            record = await HomeSubscriptionService._convert_to_response_model(item, db, include_setting_str=True)
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
    async def get_user_subscription_detail(
        db: AsyncSession,
        *,
        subscription_id: int,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        获取用户的订阅详情

        Args:
            db: 数据库会话
            subscription_id: 订阅ID
            user_id: 用户ID

        Returns:
            订阅详情（仅启用状态的订阅）

        Raises:
            NotFoundError: 订阅不存在、已禁用或用户无权限访问
        """
        item = await home_subscription_dao.get_user_subscription_by_id(
            db,
            subscription_id=subscription_id,
            user_id=user_id,
            status=True,  # 只获取启用的订阅
        )

        if not item:
            raise NotFoundError(msg=f"订阅 {subscription_id} 不存在或您无权限访问")

        return await HomeSubscriptionService._convert_to_response_model(item)

    @staticmethod
    async def _convert_to_response_model(
        db_obj, db: AsyncSession = None, include_setting_str: bool = False
    ) -> Dict[str, Any]:
        """将数据库对象转换为响应模型"""
        if not db_obj:
            return None

        # 构建响应数据
        base_data = {k: v for k, v in db_obj.__dict__.items() if not k.startswith("_")}

        response_data = {
            **base_data,
            # 添加assistant_name字段（如果存在的话）
            "assistant_name": getattr(db_obj, "assistant_name", None),
        }

        # 只在需要时添加setting_str字段
        if include_setting_str and db:
            response_data["setting_str"] = await HomeSubscriptionService._convert_setting_to_string(db, db_obj.setting)

        return response_data

    @staticmethod
    async def _convert_setting_to_string(db: AsyncSession, setting: Optional[Dict[str, Any]]) -> str:
        """将setting字段转换为可读的字符串格式"""
        if not setting:
            return ""

        # 获取dataSourceLimit数据
        data_source_limit = setting.get("dataSourceLimit", {})
        if not data_source_limit:
            return ""

        result_parts = []

        # 处理客户限制
        if data_source_limit.get("customer"):
            customer_ids = data_source_limit["customer"]
            if isinstance(customer_ids, list) and customer_ids:
                customer_names = await HomeSubscriptionService._get_customer_names(db, customer_ids)
                if customer_names:
                    result_parts.append(f"客户：{', '.join(customer_names)}")

        # 处理用户限制
        if data_source_limit.get("user"):
            user_ids = data_source_limit["user"]
            if isinstance(user_ids, list) and user_ids:
                user_names = await HomeSubscriptionService._get_user_names(db, user_ids)
                if user_names:
                    result_parts.append(f"员工：{', '.join(user_names)}")

        # 处理代理限制
        if data_source_limit.get("agent"):
            agent_ids = data_source_limit["agent"]
            if isinstance(agent_ids, list) and agent_ids:
                agent_names = await HomeSubscriptionService._get_agent_names(db, agent_ids)
                if agent_names:
                    result_parts.append(f"代理：{', '.join(agent_names)}")

        # 处理国家限制
        if data_source_limit.get("country"):
            countries = data_source_limit["country"]
            if isinstance(countries, list) and countries:
                result_parts.append(f"国家：{', '.join(countries)}")

        # 处理标签限制
        if data_source_limit.get("user_tag") is not None:
            user_tag = data_source_limit["user_tag"]
            tag_map = {"0": "标准用户", "1": "白名单", "2": "黑名单"}
            tag_name = tag_map.get(str(user_tag), f"标签{user_tag}")
            result_parts.append(f"标签：{tag_name}")

        # 处理KYC限制
        if data_source_limit.get("kyc_status") is not None:
            kyc_status = data_source_limit["kyc_status"]
            kyc_map = {
                "0": "未KYC",
                "1": "问卷调查",
                "2": "基础信息",
                "3": "上传证件",
                "4": "签署合同",
                "5": "上传住址证明",
                "9": "KYC成功",
                "-1": "KYC失败",
            }
            kyc_name = kyc_map.get(str(kyc_status), f"KYC状态{kyc_status}")
            result_parts.append(f"KYC：{kyc_name}")

        # 处理注册时间限制
        if data_source_limit.get("register_time"):
            register_days = data_source_limit["register_time"]
            result_parts.append(f"注册时间：{register_days}天内")

        return "；".join(result_parts)

    @staticmethod
    async def _get_customer_names(db: AsyncSession, customer_ids: List[str]) -> List[str]:
        """根据客户ID获取客户名称"""
        if not customer_ids:
            return []

        # 为了性能考虑，暂时使用简化的名称格式
        # 避免对每个ID都进行数据库查询
        try:
            names = []
            for customer_id in customer_ids:
                names.append(f"客户{customer_id}")
            return names
        except Exception:
            return [f"客户{cid}" for cid in customer_ids]

    @staticmethod
    async def _get_user_names(db: AsyncSession, user_ids: List[str]) -> List[str]:
        """根据用户ID获取用户名称"""
        if not user_ids:
            return []

        # 为了性能考虑，暂时使用简化的名称格式
        # 避免对每个ID都进行数据库查询
        try:
            names = []
            for user_id in user_ids:
                names.append(f"用户{user_id}")
            return names
        except Exception:
            return [f"用户{uid}" for uid in user_ids]

    @staticmethod
    async def _get_agent_names(db: AsyncSession, agent_ids: List[str]) -> List[str]:
        """根据代理ID获取代理名称"""
        if not agent_ids:
            return []

        # 为了性能考虑，暂时使用简化的名称格式
        # 避免对每个ID都进行数据库查询
        try:
            names = []
            for agent_id in agent_ids:
                names.append(f"代理{agent_id}")
            return names
        except Exception:
            return [f"代理{aid}" for aid in agent_ids]
