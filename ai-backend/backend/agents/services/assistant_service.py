# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-09-07 17:09:31
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-09-08 15:38:38
# !/usr/bin/env python3
# -*- coding: utf-8 -*-


from sqlalchemy import select

from backend.agents.config.mcp import get_intent_names
from backend.agents.utils.cache import check_cache, set_cache
from backend.app.admin.model.ai_assistant import AIAssistant
from backend.app.admin.service.data_analysis_service import DataAnalysisService
from backend.database.db import get_db
from backend.utils.format_output import extract_json

data_analysis_service = DataAnalysisService()


class AssistantService:
    async def get_agent_assistant(self):
        try:
            cached_key = "AssistantService_get_agent_assistant"
            cached_result = await check_cache(cached_key)
            if cached_result:
                return cached_result
            # 创建异步数据库会话
            async for db in get_db():
                # 查询所有启用状态的AI助手
                query = select(AIAssistant).where(AIAssistant.status)
                result = await db.execute(query)
                assistants = result.scalars().all()
                assistants_prompt = []
                for assistant in assistants:
                    item = {"name": assistant.name, "value": assistant.id, "description": assistant.description}
                    # data_sources = assistant.settings.get("data_sources", [])
                    # query_types = [data_source.get("query_name") for data_source in data_sources]
                    # for query_type in query_types:
                    #     if query_type in INTENT_PATTERNS:
                    #         item["child_args"][query_type] = INTENT_PATTERNS[query_type]["name"]
                    assistants_prompt.append(item)
                # print(assistants_prompt)
                await set_cache(cached_key, assistants_prompt)
                return assistants_prompt
        except Exception as e:
            raise e

    async def get_assistant_by_name(self, assistant_name: str = None):
        """根据名称获取助手信息"""
        if not assistant_name:
            return False

        try:
            cached_key = f"AssistantService_get_assistant_by_name_{assistant_name}"
            cached_result = await check_cache(cached_key)
            if cached_result:
                return cached_result
            async for db in get_db():
                clean_name = assistant_name.rstrip("助手").strip()

                from sqlalchemy import or_

                query = select(AIAssistant).where(
                    or_(
                        AIAssistant.name.ilike(f"%{clean_name}%"),
                        AIAssistant.name.ilike(f"{clean_name}%"),
                        AIAssistant.name.ilike(f"%{clean_name}"),
                    )
                )
                result = await db.execute(query)
                assistant = result.scalars().first()

                if not assistant:
                    return False

                data_sources = assistant.settings.get("data_sources", [])
                query_types = [data_source.get("query_name") for data_source in data_sources]
                output_data = extract_json(assistant.output_data)
                model = await data_analysis_service._get_model(db, assistant.ai_model_id)

                data = {
                    "assistant_id": assistant.id,
                    "name": assistant.name,
                    "description": assistant.description,
                    "model": model,
                    "output_format": "both",
                    "output_format_table": output_data.get("table", []),
                    "output_format_document": output_data.get("document", ""),
                    "model_definition": assistant.model_definition,
                    "query_types": query_types,
                    "query_types_name": get_intent_names(query_types),
                }
                await set_cache(cached_key, data)
                return data

        except Exception:
            return False

    async def get_assistant_by_id(self, assistant_id: str = None):
        """根据ID获取助手信息"""
        if not assistant_id:
            return False

        try:
            cached_key = f"AssistantService_get_assistant_by_id_{assistant_id}"
            cached_result = await check_cache(cached_key)
            if cached_result:
                return cached_result
            async for db in get_db():
                query = select(AIAssistant).where(AIAssistant.id == assistant_id)
                result = await db.execute(query)
                assistant = result.scalars().first()

                if not assistant:
                    return False

                data_sources = assistant.settings.get("data_sources", [])
                query_types = [data_source.get("query_name") for data_source in data_sources]
                output_data = extract_json(assistant.output_data)
                model = await data_analysis_service._get_model(db, assistant.ai_model_id)

                data = {
                    "assistant_id": assistant.id,
                    "name": assistant.name,
                    "description": assistant.description,
                    "model": model,
                    "output_format": "both",
                    "output_format_table": output_data.get("table", []),
                    "output_format_document": output_data.get("document", ""),
                    "model_definition": assistant.model_definition,
                    "query_types": query_types,
                }
                await set_cache(cached_key, data)
                return data
        except Exception:
            return False


assistant_service = AssistantService()
