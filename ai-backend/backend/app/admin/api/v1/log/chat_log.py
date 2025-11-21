#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from datetime import datetime
from math import ceil
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, Request
from pydantic import Field
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.model.user import User
from backend.app.home.model.ai_chat import AIChat
from backend.app.home.model.ai_chat_message import AIChatMessage
from backend.common.pagination import PageData
from backend.common.response.response_schema import ResponseSchemaModel, response_base
from backend.common.schema import SchemaBase
from backend.database.db import get_db

router = APIRouter()


class ChatMessageItem(SchemaBase):
    id: str = Field(..., description="ID")
    chat_id: str = Field(..., description="会话ID")
    role: str = Field(..., description="角色")
    content: Optional[str] = Field(None, description="内容")
    response_data: Optional[Any] = Field(None, description="响应数据(任意JSON)")
    is_interrupted: Optional[bool] = Field(None, description="是否中断")
    created_time: Optional[datetime] = Field(None, description="创建时间")
    updated_time: Optional[datetime] = Field(None, description="更新时间")
    user_id: Optional[int] = Field(None, description="用户ID")
    username: Optional[str] = Field(None, description="用户名")
    nickname: Optional[str] = Field(None, description="昵称")


class ChatMessagePage(PageData[ChatMessageItem]):
    pass


@router.get("", response_model=ResponseSchemaModel[ChatMessagePage])
async def list_chat_messages(
    request: Request,
    db: AsyncSession = Depends(get_db),
    chat_id: Optional[str] = Query(None, description="按会话ID过滤"),
    user_id: Optional[int] = Query(None, description="按用户ID过滤"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
) -> ResponseSchemaModel:
    conditions = []

    if chat_id:
        conditions.append(AIChatMessage.chat_id == chat_id)
    if user_id is not None:
        conditions.append(AIChat.user_id == user_id)

    base_stmt = select(AIChatMessage).join(AIChat, AIChat.id == AIChatMessage.chat_id, isouter=(user_id is None))
    if conditions:
        base_stmt = base_stmt.where(and_(*conditions))

    total = len((await db.execute(base_stmt.with_only_columns(AIChatMessage.id))).scalars().all())

    data_stmt = (
        select(
            AIChatMessage,
            AIChat.user_id,
            User.username,
            User.nickname,
        )
        .join(AIChat, AIChat.id == AIChatMessage.chat_id)
        .join(User, User.id == AIChat.user_id, isouter=True)
    )
    if conditions:
        data_stmt = data_stmt.where(and_(*conditions))

    data_stmt = data_stmt.order_by(AIChatMessage.created_time.desc()).offset((page - 1) * size).limit(size)

    result = await db.execute(data_stmt)
    rows = result.all()

    items = [
        {
            "id": m.id,
            "chat_id": m.chat_id,
            "role": m.role,
            "content": m.content,
            "response_data": m.response_data,
            "is_interrupted": m.is_interrupted,
            "created_time": m.created_time,
            "updated_time": m.updated_time,
            "user_id": uid,
            "username": uname,
            "nickname": nname,
        }
        for (m, uid, uname, nname) in rows
    ]

    total_pages = ceil(total / size) if size else 0

    base_path = str(request.url.replace(query=None))

    def build_url(p: int) -> str:
        return f"{base_path}?page={p}&size={size}"

    links = {
        "first": build_url(1),
        "last": build_url(total_pages if total_pages > 0 else 1),
        "self": build_url(page),
        "next": build_url(page + 1) if (page + 1) <= total_pages else None,
        "prev": build_url(page - 1) if (page - 1) >= 1 else None,
    }

    data = {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "total_pages": total_pages,
        "links": links,
    }
    return response_base.success(data=data)


@router.get("/paginated", response_model=ResponseSchemaModel[ChatMessagePage])
async def list_chat_messages_paginated(
    request: Request,
    db: AsyncSession = Depends(get_db),
    chat_id: str = Query(..., description="会话ID"),
    start_message_id: Optional[str] = Query(None, description="起始消息ID（将根据其 created_time 进行过滤）"),
    size: int = Query(6, ge=1, le=100, description="获取条数，默认6条"),
    filter_symbol: str = Query(">=", description="过滤符号：>=, <=, >, <"),
) -> ResponseSchemaModel:
    """
    获取分页的会话信息列表

    Args:
        chat_id: 会话ID
        start_message_id: 起始消息ID（用其 created_time 做时间参考）
        size: 获取条数（默认6条）
        filter_symbol: 过滤符号，可选值：">="，"<="，">"，"<"
    """
    # 验证过滤符号
    valid_filters = [">=", "<=", ">", "<"]
    if filter_symbol not in valid_filters:
        return response_base.fail(message=f"无效的过滤符号，支持的值：{', '.join(valid_filters)}")

    conditions = [AIChatMessage.chat_id == chat_id, AIChatMessage.deleted_at.is_(None)]

    # 如果提供了 start_message_id，则先查出该消息的 created_time，并据此进行时间过滤
    if start_message_id is not None:
        anchor_msg = await db.get(AIChatMessage, start_message_id)
        if anchor_msg is None:
            return response_base.fail(message="起始消息ID不存在")

        anchor_time = anchor_msg.created_time
        if anchor_time is not None:
            if filter_symbol == ">=":
                conditions.append(AIChatMessage.created_time >= anchor_time)
            elif filter_symbol == "<=":
                conditions.append(AIChatMessage.created_time <= anchor_time)
            elif filter_symbol == ">":
                conditions.append(AIChatMessage.created_time > anchor_time)
            elif filter_symbol == "<":
                conditions.append(AIChatMessage.created_time < anchor_time)

    # 构建基础查询语句
    base_stmt = select(AIChatMessage).where(and_(*conditions))

    # 获取总数
    total = len((await db.execute(base_stmt.with_only_columns(AIChatMessage.id))).scalars().all())

    # 构建数据查询语句（仅返回消息本身数据，不关联用户信息）
    data_stmt = select(AIChatMessage).where(and_(*conditions)).order_by(AIChatMessage.created_time.desc()).limit(size)
    print(str(data_stmt))  # SQL 模板（含 :param 占位符）
    print(data_stmt.compile().params)  # 绑定参数
    result = await db.execute(data_stmt)
    rows = result.scalars().all()

    items = [
        {
            "id": m.id,
            "chat_id": m.chat_id,
            "role": m.role,
            "content": m.content,
            "response_data": m.response_data,
            "is_interrupted": m.is_interrupted,
            "created_time": m.created_time,
            "updated_time": m.updated_time,
        }
        for m in reversed(rows)
    ]

    # 计算分页信息
    total_pages = ceil(total / size) if size else 0
    current_page = 1  # 由于是按时间过滤，这里固定为第1页

    base_path = str(request.url.replace(query=None))

    def build_url(p: int) -> str:
        return f"{base_path}?page={p}&size={size}"

    links = {
        "first": build_url(1),
        "last": build_url(total_pages if total_pages > 0 else 1),
        "self": build_url(current_page),
        "next": build_url(current_page + 1) if (current_page + 1) <= total_pages else None,
        "prev": build_url(current_page - 1) if (current_page - 1) >= 1 else None,
    }

    data = {
        "items": items,
        "total": total,
        "page": current_page,
        "size": size,
        "total_pages": total_pages,
        "links": links,
    }
    return response_base.success(data=data)
