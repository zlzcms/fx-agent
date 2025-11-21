# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-07 18:15:08
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-06-09 10:10:45
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.agent import Agent
from backend.app.admin.model import User
from backend.app.home.api.deps import get_current_home_user
from backend.app.home.schema.ai_chat import (
    AIChatCreate,
    AIChatMessageResponse,
    AIChatResponse,
    ChatRequest,
)
from backend.app.home.service.agent_service import agent_service
from backend.app.home.service.ai_chat_service import ai_chat_service
from backend.app.home.service.ai_model_service import ai_model_service
from backend.common.log import logger
from backend.common.pagination import PageData
from backend.database.db import get_db
from backend.utils.format_output import format_message

router = APIRouter()
interruption_status = {}
confirm_intent_message = {}


# 自定义JSON编码器，处理AIMessage对象和枚举类型
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (AIMessage, HumanMessage, SystemMessage, BaseMessage)):
            return {"type": obj.__class__.__name__, "content": obj.content}
        # 处理枚举类型
        if hasattr(obj, "value"):
            return obj.value
        # 处理Pydantic模型
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        return super().default(obj)


@router.post("/completion")
async def stream_chat_completion(
    request: ChatRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_home_user)
):
    """处理流式聊天完成请求"""

    # 验证chat_id
    if not request.chat_id:
        raise HTTPException(status_code=400, detail="chat_id is required")

    # 检查聊天会话权限
    chat = await ai_chat_service.get_chat(db, chat_id=request.chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    if chat.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this chat")
    if request.action and request.action in ["auto", "agent", "chat"]:
        action = request.action
    else:
        action = "auto"

    if request.channel:
        # 暂时记下日志， 后期再处理到数据表 TODO
        print(f"Channel: {request.channel}")

    if request.result_format and request.result_format in ["word", "html"]:
        result_format = request.result_format
    else:
        result_format = "word"

    # 创建用户消息
    await ai_chat_service.create_user_message(db, chat_id=request.chat_id, content=request.message)
    # 创建AI助手消息（初始为空内容）
    assistant_message = await ai_chat_service.create_assistant_message(
        db, chat_id=request.chat_id, content="", is_interrupted=False
    )
    # 生成唯一的任务ID
    interruption_status[request.chat_id] = False

    # 获取聊天历史消息
    history_messages = await agent_service.get_history_messages(db, chat)
    # print(history_messages)

    # 根据chat.model_id获取模型配置，如果没有则使用系统默认模型
    llm_config = {}
    # 暂时注释掉chat.model_id，直接使用系统配置的默认模型
    # model_id_to_use = chat.model_id

    # 直接使用系统默认模型
    model_id_to_use = None
    default_model_id = await ai_model_service.get_default_model_id(db)
    if default_model_id:
        model_id_to_use = default_model_id

    # 获取模型配置
    if model_id_to_use:
        model = await ai_model_service.get_model_by_id(db, model_id=model_id_to_use)
        if model and model.status:
            llm_config = {
                "id": model.id,  # 添加模型ID
                "api_key": model.api_key,
                "base_url": model.base_url,
                "name": model.name,
                "model_name": model.model,
                "temperature": model.temperature,
            }
    logger.info(f"llm_config: {llm_config}")
    # 创建agent实例，传入模型配置
    agent_config = {"llm": llm_config} if llm_config else {}
    chat_agent = Agent(config=agent_config)

    # 收集完整的AI响应内容
    full_content = []
    full_message = ""
    files = []
    file_message = ""
    chat_id = request.chat_id

    async def generate_stream():
        nonlocal full_content, full_message, files, file_message, action, assistant_message, chat_id, result_format
        from backend.agents.schema.agent import InterruptedException

        try:
            # 从当前用户获取 crm_user_id（字符串字段），确保为正整数
            crm_user_id = None
            try:
                crm_val = getattr(current_user, "crm_user_id", None)
                if crm_val is not None:
                    crm_str = str(crm_val).strip()
                    if crm_str.isdigit():
                        crm_user_id = int(crm_str)
            except Exception:
                # 保持健壮性，转换失败时不影响主流程
                crm_user_id = None

            # 创建中断检查器函数
            def check_interruption():
                return interruption_status.get(chat_id, False)

            async for message in chat_agent.auto_orchestrate(
                user_query=request.message,
                conversation_history=history_messages,
                action=action,
                last_confirm_intent_message=confirm_intent_message.get(chat_id),
                crm_user_id=crm_user_id,
                interruption_checker=check_interruption,  # 传递中断检查器
                result_format=result_format,
            ):
                message = format_message(message)

                # if message.get("type") == "confirm_intent_message":
                #     confirm_intent_message[chat_id] = message
                # print(message)
                full_content.append(message)
                # 将字典转换为JSON字符串
                if isinstance(message, dict):
                    if message.get("file"):
                        files.append(message.get("file"))
                        if message.get("message"):
                            file_message += f"{message.get('message')}\n"
                    else:
                        if (
                            message.get("message")
                            and message.get("type")
                            and message.get("type") in ["chat", "error", "md_info", "step"]
                        ):
                            full_message += message.get("message")
                    yield f"data: {json.dumps(message, ensure_ascii=False)}\n\n"
                else:
                    if isinstance(message, str):
                        full_message += message
                    yield f"data: {str(message)}\n\n"

            if file_message:
                full_message += f"\n以下是相关文件\n{file_message}"

            # 流式生成完成后，更新消息内容
            await ai_chat_service.update_message_content(
                db,
                message_id=assistant_message.id,
                content=full_message,
                response_data=json.dumps(full_content, ensure_ascii=False, cls=CustomJSONEncoder),
                is_interrupted=False,
            )

        except InterruptedException:
            # 处理用户主动中断
            if file_message:
                full_message += f"\n以下是相关文件\n{file_message}"
            interrupted_message = "\n用户中断"
            full_message += interrupted_message
            full_content.append({"type": "interrupted", "message": interrupted_message})
            # 更新消息内容并标记为已中断
            await ai_chat_service.update_message_content(
                db,
                message_id=assistant_message.id,
                content=full_message,
                response_data=json.dumps(full_content, ensure_ascii=False, cls=CustomJSONEncoder),
                is_interrupted=True,
            )
            yield f"data: {json.dumps({'type': 'interrupted', 'message': interrupted_message}, ensure_ascii=False)}\n\n"
        except Exception as e:
            # 发生错误时，更新消息内容并标记为已中断
            await ai_chat_service.update_message_content(
                db,
                message_id=assistant_message.id,
                response_data=json.dumps(full_content, ensure_ascii=False, cls=CustomJSONEncoder),
                content=full_message,
                is_interrupted=True,
            )
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n"

        finally:
            if chat_id in interruption_status:
                del interruption_status[chat_id]

    return StreamingResponse(generate_stream(), media_type="text/event-stream")


@router.post("/interrupt/{chat_id}")
async def interrupt_stream(
    chat_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_home_user),
):
    """中断指定的流式任务"""
    if chat_id in interruption_status:
        interruption_status[chat_id] = True
        return {"status": 1, "message": "Interruption signal sent"}
    else:
        raise HTTPException(status_code=404, detail="Task not found")


# @router.put("update/{chat_id}/chat", response_model=AIChatResponse)
# async def update_chat(
#     chat_id: str,
#     data: AIChatUpdate,
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_home_user),
# ):
#     """更新聊天会话"""
#     chat = await ai_chat_service.get_chat(db, chat_id=chat_id)
#     if not chat:
#         raise HTTPException(status_code=404, detail="Chat not found")
#     if chat.user_id != current_user.id:
#         raise HTTPException(status_code=403, detail="Not authorized to update this chat")

#     updated_chat = await ai_chat_service.update_chat(db, chat_id=chat_id, data=data)

#     # 将SQLAlchemy对象转换为Pydantic模型，避免在会话外访问关系属性
#     return AIChatResponse(
#         id=updated_chat.id,
#         user_id=updated_chat.user_id,
#         title=updated_chat.title,
#         model_id=updated_chat.model_id,
#         status=updated_chat.status,
#         created_time=updated_chat.created_time,
#         updated_time=updated_chat.updated_time,
#     )


@router.delete("/delete/{chat_id}")
async def delete_chat(
    chat_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_home_user)
):
    """删除聊天会话"""
    chat = await ai_chat_service.get_chat(db, chat_id=chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    if chat.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this chat")

    success = await ai_chat_service.delete_chat(db, chat_id=chat_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete chat")
    return {"status": 1, "message": "Chat deleted successfully"}


@router.get("/get/{chat_id}/messages", response_model=PageData[AIChatMessageResponse])
async def get_chat_messages(
    chat_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_home_user),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, gt=0, le=200, description="每页数量"),
):
    """获取聊天会话的消息（支持分页）"""
    chat = await ai_chat_service.get_chat(db, chat_id=chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    if chat.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this chat")

    page_data = await ai_chat_service.get_chat_messages_paginated(db, chat_id=chat_id, page=page, size=size)

    # 将SQLAlchemy对象转换为Pydantic模型，避免在会话外访问关系属性
    # 反转消息顺序，使旧的在前，新的在后（与原来的行为一致）
    items = [
        AIChatMessageResponse(
            id=msg.id,
            chat_id=msg.chat_id,
            role=msg.role,
            content=msg.content,
            response_data=json.loads(msg.response_data) if msg.response_data else None,
            created_time=msg.created_time,
            updated_time=msg.updated_time,
        )
        for msg in reversed(page_data.items)
    ]

    return PageData(
        items=items,
        total=page_data.total,
        page=page_data.page,
        size=page_data.size,
        total_pages=page_data.total_pages,
        links=page_data.links,
    )


@router.get("/get/{chat_id}", response_model=AIChatResponse)
async def get_chat(
    chat_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_home_user)
):
    """通过ID获取聊天会话"""
    chat = await ai_chat_service.get_chat(db, chat_id=chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    if chat.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this chat")

    # 将SQLAlchemy对象转换为Pydantic模型，避免在会话外访问关系属性
    return AIChatResponse(
        id=chat.id,
        user_id=chat.user_id,
        title=chat.title,
        model_id=chat.model_id,
        status=chat.status,
        channel=chat.channel,
        created_time=chat.created_time,
        updated_time=chat.updated_time,
    )


@router.post("/create", response_model=AIChatResponse)
async def create_chat(
    data: AIChatCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_home_user)
):
    """创建新的聊天会话"""
    # 详细记录用户信息和ID

    # 强制设置user_id为当前用户ID
    user_id = current_user.id
    if user_id is None:
        raise HTTPException(status_code=400, detail="无法获取有效的用户ID")

    # 生成或使用提供的聊天ID
    chat_id = data.id or str(uuid.uuid4())

    # 如果没有指定model_id，使用系统默认模型
    model_id = data.model_id
    if not model_id:
        default_model_id = await ai_model_service.get_default_model_id(db)
        if default_model_id:
            model_id = default_model_id

    # 创建新的AIChatCreate对象，确保user_id是整数
    chat_data = AIChatCreate(user_id=user_id, title=data.title, model_id=model_id, id=chat_id, channel=data.channel)

    try:
        chat = await ai_chat_service.create_chat(db, data=chat_data)
        return chat
    except ValueError as e:
        # 捕获并记录任何值错误
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        # 捕获并记录其他错误
        raise HTTPException(status_code=500, detail="创建聊天时发生错误")


@router.get("/gets", response_model=PageData[AIChatResponse])
async def list_chats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_home_user),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, gt=0, le=200, description="每页数量"),
):
    """列出当前用户的所有聊天会话（分页）"""
    page_data = await ai_chat_service.list_chats_paginated(db, user_id=current_user.id, page=page, size=size)

    # 将SQLAlchemy对象转换为Pydantic模型，避免在会话外访问关系属性
    items = [
        AIChatResponse(
            id=chat.id,
            user_id=chat.user_id,
            title=chat.title,
            model_id=chat.model_id,
            status=chat.status,
            channel=chat.channel,
            created_time=chat.created_time,
            updated_time=chat.updated_time,
        )
        for chat in page_data.items
    ]

    return PageData(
        items=items,
        total=page_data.total,
        page=page_data.page,
        size=page_data.size,
        total_pages=page_data.total_pages,
        links=page_data.links,
    )
