# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-09-04 18:02:36
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-09-09 09:39:46
# !/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import time
import uuid

from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
import json
import pytz

from backend.agents.config.prompt.data_analyze import (
    ANALYSIS_PROMPT,
    DEFAULT_OUTPUT_ANALYTICAL_REPORT,
    DEFAULT_OUTPUT_PROPERTY_ANALYSIS,
    DEFAULT_PROMPT_TEMPLATE,
    DEFAULT_RISK_TAGS_TEMPLATE,
    PROPERTY_ANALYSIS_PROMPT,
)
from backend.agents.schema.agent import AgentState, Base, ExecuteStatus, ResponseType, YieldResponse
from backend.agents.schema.analyze import AnalyzeMessagesResult
from backend.agents.utils.data_reduce_strategy import DataReduceStrategy
from backend.agents.utils.format_output import convert_to_dict, get_current_weekday, response_to_json
from backend.common.log import logger


class DataAnalyzeAgent(Base):
    """
    数据分析智能体，专门负责分析数据
    """

    def __init__(self, task_id: str = None, config: dict = {}):
        if "llm" not in config:
            config["llm"] = {}
        config["llm"]["temperature"] = 0.2
        super().__init__("data_analyze", config)
        self.task_id = task_id if task_id else str(uuid.uuid4())

        # 初始化数据缩减策略
        self.data_reduce_strategy = DataReduceStrategy(self.llm)
        # self.is_should_reduce_data = False

    async def stream_analyze_data(
        self, user_query: str, conversation_history: Optional[List] = None, **kwargs
    ) -> AsyncGenerator:
        """流式分析数据"""
        try:
            analyze_message = await self._get_analyze_messages(user_query=user_query, **kwargs)
            if analyze_message.is_should_reduce_data:
                reduced_data = None
                async for event in self._analyze_large_data(analyze_message, **kwargs):
                    if event.get("type") == "__final__":
                        reduced_data = event.get("data")
                    else:
                        yield event
                all_chunk = reduced_data.content if reduced_data else ""
                if all_chunk:
                    yield YieldResponse(
                        name=f"{self.name}_chat",
                        type=ResponseType.CHAT,
                        status=ExecuteStatus.RUNNING,
                        message=all_chunk,
                    )
            else:
                all_chunk = ""
                chunk_count = 0
                async for chunk in self.stream(analyze_message.result, f"数据分析【{user_query}】"):
                    all_chunk += chunk.content
                    chunk_count += 1
                    yield YieldResponse(
                        name=f"{self.name}_chat",
                        type=ResponseType.CHAT,
                        status=ExecuteStatus.RUNNING,
                        message=chunk.content,
                    )

            self.result["data"] = all_chunk
            self.result["output"] = all_chunk

        except Exception as e:
            logger.error(f"DataAnalyzeAgent stream_analyze_data failed: {str(e)}")
            raise e

    async def invoke_analyze_data(self, user_query: str, conversation_history: Optional[List] = None, **kwargs) -> str:
        """调用分析数据"""
        try:
            analyze_message = await self._get_analyze_messages(user_query=user_query, **kwargs)
            if analyze_message.is_should_reduce_data:
                response = await self._collect_large_data_result(analyze_message, **kwargs)
            else:
                response = await self.ainvoke(analyze_message.result, f"数据分析【{user_query}】")
            self.result["response"] = convert_to_dict(response)
            self.result["data"] = response.content
            self.result["output"] = response.content
            return response.content
        except Exception as e:
            logger.error(f"DataAnalyzeAgent invoke_analyze_data failed: {str(e)}")
            raise e

    async def report_analyze_data(
        self, user_query: str, conversation_history: Optional[List] = None, **kwargs
    ) -> Tuple[bool, dict, str]:
        """报告分析数据"""
        try:
            analyze_message = await self._get_analyze_messages(user_query=user_query, **kwargs)
            is_property_analysis = kwargs.get("is_property_analysis", False)

            if analyze_message.is_should_reduce_data:
                response = await self._collect_large_data_result(analyze_message, **kwargs)
                if is_property_analysis:
                    property_prompt = analyze_message.property_prompt.replace("$analysis_data", response.content)
            else:
                response = await self.ainvoke(analyze_message.result, f"数据分析【{user_query}】")
                property_prompt = analyze_message.property_prompt

            success = True
            data = {}
            if is_property_analysis:
                success, data = await self._property_analysis(property_prompt, response.content)
            self.result["response"] = convert_to_dict(response)
            data_markdown = response.content
            data["analytical_report"] = data_markdown
            self.result["output"] = data_markdown
            self.result["data"] = data
            return success, data, data_markdown
        except Exception as e:
            logger.error(f"DataAnalyzeAgent report_analyze_data failed: {str(e)}")
            raise e

    async def _property_analysis(self, property_prompt: str, data: Any) -> Tuple[bool, dict]:
        try:
            response = await self.ainvoke(property_prompt, f"属性分析【{data}】")
            success, data = response_to_json(response.content)
            if not isinstance(data, dict):
                data = {}
            return success, data
        except Exception as e:
            logger.error(f"DataAnalyzeAgent property_analysis failed: {str(e)}")
            raise Exception(str(e))

    async def _collect_large_data_result(self, analyze_message: AnalyzeMessagesResult, **kwargs) -> AIMessage:
        """消费大数据量分析的流式结果，仅返回最终结果"""
        final_response = None
        async for event in self._analyze_large_data(analyze_message, **kwargs):
            if event.get("type") == "__final__":
                final_response = event.get("data")
        if final_response is None:
            return AIMessage(content="")
        return final_response

    async def _analyze_large_data(
        self, analyze_message: AnalyzeMessagesResult, **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        专门处理大数据量的分析方法
        使用LangChain的map_reduce策略进行分块分析
        使用异步生成器版本，直接使用 async for，避免队列轮询
        """
        try:
            self.bebug.append("大数据量的分析")
            start_time = time.time()

            # 直接使用异步生成器，无需队列轮询
            async for event in self.data_reduce_strategy.reduce_data_async_stream(
                analyze_message.data,
                analyze_message.result,
                analyze_message.result,
                **kwargs,
            ):
                if event.get("type") == "__final__":
                    duration = time.time() - start_time
                    self.bebug.append(f"耗时: {duration} 秒")
                    self.bebug.append("\n")
                    reduced_data = AIMessage(content=event.get("content", ""))
                    yield {"type": "__final__", "data": reduced_data}
                else:
                    chunk_index = event.get("chunk_index", 0)
                    total_chunks = event.get("total_chunks", 0)
                    chunk_message = event.get("result", "")
                    yield {
                        "type": "step",
                        "type_name": "execute",
                        "status": "running",
                        "chunk_index": chunk_index,
                        "chunk_total": total_chunks,
                        "message": f"已完成第{chunk_index}/{total_chunks}个数据分片分析",
                        "data": chunk_message,
                    }
        except Exception as e:
            logger.error(f"DataAnalyzeAgent analyze_large_data failed: {str(e)}")
            raise e

    async def _get_analyze_messages(self, user_query: str, **kwargs) -> AnalyzeMessagesResult:
        """分析数据"""
        analyze_data = kwargs.get("analyze_data")
        self.result["analyze_data"] = analyze_data
        self.add_log("输入数据", analyze_data)
        if isinstance(analyze_data, list) and len(analyze_data) > 1:
            kwargs["is_should_reduce_data"] = True
            prompt, property_prompt = await self.get_system_prompt(user_query=user_query, **kwargs)
            analysis_prompt = prompt.replace("{", "{{").replace("}", "}}").replace("$analysis_data", "{text}")
            self.result["prompt"] = prompt
            return AnalyzeMessagesResult(
                result=analysis_prompt, is_should_reduce_data=True, data=analyze_data, property_prompt=property_prompt
            )
        else:
            if isinstance(analyze_data, list):
                kwargs["analyze_data"] = analyze_data[0]
            prompt, property_prompt = await self.get_system_prompt(user_query=user_query, **kwargs)
            messages = self._get_history_messages(user_query=user_query, conversation_history=[], system_prompt=prompt)
            self.result["prompt"] = prompt
            return AnalyzeMessagesResult(
                result=messages, is_should_reduce_data=False, data=analyze_data, property_prompt=property_prompt
            )

    async def execute(
        self, user_query: str, conversation_history: Optional[List] = None, **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """执行数据分析任务"""
        try:
            # 设置中断检查器
            interruption_checker = kwargs.get("interruption_checker")
            if interruption_checker:
                self.set_interruption_checker(interruption_checker)
            self.state = AgentState.RUNNING
            analyze_data = kwargs.get("analyze_data")
            if not analyze_data:
                yield YieldResponse(
                    name=f"{self.name}_error",
                    type=ResponseType.ERROR,
                    status=ExecuteStatus.ERROR,
                    message="无数据分析数据",
                )
                return
            # 常规数据分析流程
            llm_response_type = kwargs.get("llm_response_type", "report")
            logger.info(f"llm_response_type: {llm_response_type}")
            intent_data = kwargs.get("intent_data", {})
            if llm_response_type == "invoke":
                message = await self.invoke_analyze_data(
                    user_query=user_query, conversation_history=conversation_history, **kwargs
                )
                yield YieldResponse(
                    name=f"{self.name}_chat",
                    type=ResponseType.CHAT,
                    status=ExecuteStatus.RUNNING,
                    message=message,
                )
            elif llm_response_type == "report":
                success, data, data_markdown = await self.report_analyze_data(
                    user_query=user_query, conversation_history=conversation_history, **kwargs
                )
                selected_service = intent_data.get("selected_service")
                if selected_service in ["report", "agent"]:
                    type = ResponseType.INFO
                else:
                    type = ResponseType.CHAT
                yield YieldResponse(
                    name=f"{self.name}_chat",
                    type=type,
                    status=ExecuteStatus.RUNNING,
                    message=data_markdown,
                )
            else:
                async for chunk in self.stream_analyze_data(
                    user_query=user_query, conversation_history=conversation_history, **kwargs
                ):
                    yield chunk

            is_save_file = kwargs.get("is_save_file", True)
            if is_save_file:
                self.result["file"] = self.data_export_tool.export_to_markdown(
                    self.result["output"], self.task_id, f"data_analyze_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                )
                ## 如果要求导出html，则将结果推给llm 生成一份html文件
                if kwargs.get("result_format", "word") == "html":
                    self.result["file"] = await self.convert_to_web_html( self.result["output"], self.task_id, f"data_analyze_{datetime.now().strftime('%Y%m%d%H%M%S')}")
                   
                logger.info(f"Analysis report exported to file: {self.result.get('file', {}).get('filename')}")
                self.add_log("文件", self.result["file"])
                yield YieldResponse(
                    name=f"{self.name}_file",
                    type=ResponseType.FILE,
                    status=ExecuteStatus.RUNNING,
                    message=self.result.get("file", {}).get("filename"),
                    file=self.result["file"],
                )

            self.state = AgentState.COMPLETED
            yield YieldResponse(
                name=f"{self.name}_completed",
                type=ResponseType.COMPLETED,
                status=ExecuteStatus.COMPLETED,
                output=self.result["output"],
                message="数据分析完成",
            )
            logger.info("DataAnalyzeAgent execution completed successfully")
        except Exception as e:
            error_msg = f"DataAnalyzeAgent execution failed: {str(e)}"
            logger.error(error_msg)
            self.error = error_msg
            self.state = AgentState.FAILED
            self.add_log("系统执行失败", self.error)
            yield YieldResponse(
                name=f"{self.name}_error",
                type=ResponseType.ERROR,
                status=ExecuteStatus.ERROR,
                message=error_msg,
            )
    async def convert_to_web_html(self, output: str | dict, task_id: str, filename: str) -> dict:
        """将输出转换为web html格式并导出"""
        try:
            if isinstance(output, (dict, list)):
                content_str = json.dumps(output, ensure_ascii=False, indent=2)
            else:
                content_str = str(output)

            system_prompt = (
                "You are an experienced front-end engineer and technical writer. "
                "The user will give you an analytical report in Markdown-like text. "
                "Your job is to READ and UNDERSTAND the content, then DESIGN a new, polished, responsive, self-contained HTML page. "
                "You MUST NOT simply dump the original Markdown into <pre> or otherwise show raw Markdown markers (#, *, ``` etc.). "
                "Use semantic HTML5 sections, inline CSS, good typography, clear hierarchy, and highlight key metrics, and avoid any scripts."
            )
            human_prompt = f"""
请将下面的“分析结果”（Markdown 或接近 Markdown 的文本）转化为一份**重新排版的、用户体验良好的 Web HTML 页面**，而不是把原始 Markdown 直接展示出来。

要求：
1. 页面结构：包含标题区、关键发现摘要、详尽内容、数据要点（使用表格或列表）以及结论/建议区域，可以根据内容合理拆分和重组版块。
2. 视觉风格：使用内联CSS，整体风格现代、响应式，对暗色背景设备也要有良好对比度（例如注意文字颜色与背景色对比）。
3. Markdown 处理：请解析 Markdown 语义（标题、列表、表格、代码块等），**不要**把整段原始 Markdown 文本丢进一个<pre>里；只有当内容本身是“代码片段或数据片段”时才用<pre><code>包裹该代码/数据块。
4. 请不要在最终页面中显示 Markdown 标记符号（例如 #, *, ``` 等），而是转换为合适的 HTML 结构和样式。
5. 页脚中添加生成时间（可以使用“当前生成时间”字样）和数据来源说明（例如“数据来源：系统分析结果”）。

分析结果（Markdown 文本）如下：
<analysis_content>
{content_str}
</analysis_content>
"""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt),
            ]

            response = await self.llm.ainvoke(messages)
            html_content = response.content.strip()
            logger.info(f"html_content: {html_content}")
            return self.data_export_tool.export_to_html(html_content, task_id, filename)

        except Exception as e:
            logger.error(f"convert_to_web_html failed: {str(e)}")
            fallback_html = f"""<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8" />
    <title>数据分析报告</title>
</head>
<body>
    <h1>数据分析报告</h1>
    <pre>{content_str if 'content_str' in locals() else output}</pre>
</body>
</html>"""
            return self.data_export_tool.export_to_html(fallback_html, task_id, filename)

    async def get_system_prompt(self, user_query: str, **kwargs):
        """获取系统提示词"""
        assistant = kwargs.get("assistant", None)
        analysis_prompt = kwargs.get("analysis_prompt", {})
        is_should_reduce_data = kwargs.get("is_should_reduce_data", False)
        analyze_data = kwargs.get("analyze_data") if not is_should_reduce_data else "$analysis_data"
        data_request = kwargs.get("data_request")
        is_tool = self.check_is_tool(data_request)
        if is_tool:
            role_prompt_template = "智能行情分析专家"
            current_time = datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S")
            week = "\n\n 注意：当前时间是utc时间 ，数据mt_date是MT时间，请不要混淆 "
        else:
            role_prompt_template = "CRM智能助理"
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            week = get_current_weekday()
        risk_tags_template = DEFAULT_RISK_TAGS_TEMPLATE
        if assistant:
            prompt_template = assistant.get("model_definition")
            output_analytical_report = assistant.get("output_format_document")
            output_property_analysis = self.format_output_property_analysis(assistant.get("output_format_table"))
        elif analysis_prompt:
            prompt_template = analysis_prompt.get("role_prompt_template", "你是专业的数据分析助手")
            output_analytical_report = analysis_prompt.get("analytical_report_format")
            output_property_analysis = analysis_prompt.get("property_analysis_format")
            risk_tags_template = analysis_prompt.get("risk_tags_template")
        else:
            prompt_template = DEFAULT_PROMPT_TEMPLATE.format(role_prompt_template=role_prompt_template)
            output_analytical_report = DEFAULT_OUTPUT_ANALYTICAL_REPORT
            output_property_analysis = DEFAULT_OUTPUT_PROPERTY_ANALYSIS

        self.add_log("系统提示词", ANALYSIS_PROMPT)
        prompt = ANALYSIS_PROMPT.format(
            prompt_template=prompt_template,
            user_query=user_query,
            data_request=data_request,
            analysis_data=analyze_data,
            output_analytical_report=output_analytical_report,
            current_time=current_time,
            week=week,
        )
        self.add_log("组装提示词", prompt)
        property_prompt = PROPERTY_ANALYSIS_PROMPT.format(
            prompt_template=prompt_template,
            data_request=data_request,
            analysis_data=analyze_data,
            output_property_analysis=output_property_analysis,
            current_time=current_time,
            week=week,
            risk_tags_template=risk_tags_template,
        )

        # 保存系统提示词供数据缩减策略使用
        self.current_system_prompt = prompt

        return prompt, property_prompt

    def format_output_property_analysis(self, output_property_analysis):
        result = ""
        output_property: list[dict] = []
        if isinstance(output_property_analysis, str):
            success, data = response_to_json(output_property_analysis)
            if success:
                output_property = data
        elif isinstance(output_property_analysis, list):
            output_property = output_property_analysis
        if output_property:
            result = "[\n"
            for item in output_property:
                if isinstance(item, dict) and item.get("fieldName") and item.get("fieldDesc"):
                    name = item.get("fieldName")
                    value = item.get("fieldDesc")
                    result += f'{{"name":"{name}","value":"" // {value} }},\n'
            result += "]"
        return result

    def check_is_tool(self, data_request):
        """检查是否是工具"""
        if isinstance(data_request, dict):
            for key, value in data_request.items():
                if key.startswith("tool_"):
                    return True
        return False
