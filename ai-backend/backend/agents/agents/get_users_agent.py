# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-09-04 18:02:36
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-09-09 09:40:05
# !/usr/bin/env python3
# -*- coding: utf-8 -*-


import time
import uuid

from typing import Any, AsyncGenerator, Dict, List, Optional

from backend.agents.config.prompt.agent import ERROR_SYSTEM_PROMPT
from backend.agents.config.setting import settings
from backend.agents.schema.agent import AgentState, Base, ExecuteStatus, ResponseType, YieldResponse
from backend.agents.tools.data_to_markdown import users_to_markdown
from backend.agents.tools.mcp_client import mcp_client
from backend.common.log import logger


class GetUsersAgent(Base):
    """
    获取用户数据智能体，专门负责从MCP服务查询用户数据
    """

    def __init__(self, task_id: str = None, config: dict = {}):
        super().__init__("get_users", config)
        self.task_id = task_id if task_id else str(uuid.uuid4())
        self.max_user_count = settings.MAX_USER_COUNT
        self.max_data_count = settings.MAX_DATA_COUNT

    async def get_users(self, **kwargs) -> Dict[str, Any]:
        """获取用户数据主方法"""

        try:
            request = kwargs.get("data_sources", {})
            if not request:
                return {"success": False, "message": "请求数据为空", "data": []}
            # 注入 crm_user_id 到顶层请求，满足 MCP 服务授权校验
            crm_user_id = kwargs.get("crm_user_id")
            logger.info(f"GetUsersAgent 接收到的crm_user_id: {crm_user_id}")
            try:
                if crm_user_id is not None:
                    crm_str = str(crm_user_id).strip()
                    if crm_str.isdigit():
                        request["crm_user_id"] = int(crm_str)
                        logger.info(f"GetUsersAgent 设置request中的crm_user_id: {request['crm_user_id']}")
                    else:
                        logger.warning(f"GetUsersAgent crm_user_id不是有效数字: {crm_str}")
                else:
                    logger.warning("GetUsersAgent crm_user_id为None")
            except Exception as e:
                # 保持健壮性，不因转换问题中断流程
                logger.warning(f"GetUsersAgent 处理crm_user_id时出错: {e}")
                pass
            self.result["request"] = request
            logger.debug("GetUsersAgent request", request)
            self.result["assistant"] = kwargs.get("assistant", None)
            if self.result.get("assistant"):
                logger.debug("GetUsersAgent assistant", self.result.get("assistant").get("name"))
                assistant_request = self.request_assistant(request, self.result.get("assistant").get("query_types", []))
                if assistant_request:
                    request = assistant_request
            self.add_log("查询的请求", request)
            self.bebug.append(f"查询的请求: {request}")
            start_time = time.time()
            result = await mcp_client.query_data(request)
            end_time = time.time()
            self.bebug.append(f"查询耗时: {end_time - start_time} 秒")
            self.bebug.append("\n")
            # print("=========result===============", result)
            logger.debug("GetUsersAgent result", result)
            return result
        except Exception as e:
            error_msg = f"获取用户异常 <{str(e)}>"
            return {"success": False, "message": error_msg, "data": []}

    def request_assistant(self, request: Dict[str, Any], query_types: List[str]):
        copy_request = request.copy()
        user_data = copy_request.get("user_data", {})
        return_request = {}
        if not user_data:
            return return_request
        range_time = user_data.get("range_time", {})
        del copy_request["user_data"]
        check_request = []
        if copy_request:
            for query_type, value in copy_request.items():
                if query_type in query_types:
                    check_request.append(query_type)
        if len(check_request) == 0:
            check_request = query_types

        for check_request_type in check_request:
            if check_request_type != "user_data":
                request[check_request_type] = {"limit": self.max_data_count}
                if range_time:
                    request[check_request_type]["range_time"] = range_time

        return request

    async def execute(
        self, user_query: str, conversation_history: Optional[List] = None, **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """执行获取用户数据任务"""
        try:
            self.state = AgentState.RUNNING
            logger.debug("GetUsersAgent set to RUNNING")
            users_info = await self.get_users(**kwargs)
            if not users_info or not users_info["success"]:
                error_msg = users_info.get("message")
                self.add_log("执行失败", users_info)
                # self.log.append({"title": "失败系统提示词", "content": ERROR_SYSTEM_PROMPT})

                async for error_message in self.chat_stream(
                    user_query=user_query,
                    conversation_history=conversation_history,
                    system_prompt=ERROR_SYSTEM_PROMPT.format(error_message=error_msg, user_query=user_query),
                    status=ExecuteStatus.ERROR,
                ):
                    yield error_message

                self.state = AgentState.FAILED
                self.error = error_msg
                logger.error(f"GetUsersAgent execution failed: {error_msg}")
                # print("=========users_error===============", error_msg)
                return
            self.add_log("查询结果", users_info)

            # 转换为markdown

            users_markdown_data = None
            user_data = users_info.get("data", {})
            if users_info.get("success") and users_info.get("data"):
                users_markdown_data = users_to_markdown(users_info)
            self.result["data"] = user_data
            is_save_file = kwargs.get("is_save_file", True)
            if is_save_file and users_markdown_data and isinstance(users_markdown_data, list):
                files = []
                for index, users_markdown_data_item in enumerate(users_markdown_data):
                    file = self.data_export_tool.export_to_markdown(
                        users_markdown_data_item, self.task_id, f"users_info_{len(user_data)}_{index + 1}"
                    )
                    logger.debug(f"GetUsersAgent file :{file}")
                    files.append(file)
                    yield YieldResponse(
                        name=f"{self.name}_file",
                        type=ResponseType.FILE,
                        status=ExecuteStatus.RUNNING,
                        message=file.get("filename"),
                        file=file,
                    )
                self.result["files"] = files
                self.add_log("输出文件", files)
            self.result["output"] = users_markdown_data
            yield YieldResponse(
                name=f"{self.name}_completed",
                type=ResponseType.COMPLETED,
                status=ExecuteStatus.COMPLETED,
                output=users_markdown_data,
                message="获取数据完成",
            )
            self.state = AgentState.COMPLETED
            logger.info("GetUsersAgent execution completed successfully")
            # self.log.append({"title": "执行完成 输出数据", "content": users_markdown_data})
        except Exception as e:
            error_msg = f"execute error: {str(e)}"
            logger.error(f"GetUsersAgent execution failed: {error_msg}")
            self.error = error_msg
            self.state = AgentState.FAILED
            self.add_log("系统执行失败", self.error)
            yield YieldResponse(
                name=f"{self.name}_error",
                type=ResponseType.ERROR,
                status=ExecuteStatus.ERROR,
                message=error_msg,
            )
