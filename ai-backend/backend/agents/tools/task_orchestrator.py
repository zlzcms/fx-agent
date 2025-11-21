#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional

from backend.agents.agents.ai_data_analysis_agent import AIDataAnalysisAgent
from backend.agents.agents.ai_task_planner_agent import AITaskPlannerAgent
from backend.agents.agents.data_splitting_agent import DataSplittingAgent
from backend.agents.agents.general_chat_agent import GeneralChatAgent
from backend.agents.agents.mcp_data_agent import MCPDataAgent
from backend.agents.config.setting import settings
from backend.agents.schema.base_agent import AgentType
from backend.agents.tools.stream_task import ExecutionMode, StreamTaskManager


class TaskTemplate(Enum):
    """任务模板枚举"""

    SIMPLE_QUERY = "simple_query"  # 简单查询：意图识别 -> MCP查询 -> 输出
    ANALYSIS_REPORT = "analysis_report"  # 分析报告：意图识别 -> MCP查询 -> 数据拆分 -> AI分析 -> 报告生成


@dataclass
class TaskStep:
    """任务步骤定义"""

    step_name: str
    agent_type: AgentType
    dependencies: List[str] = None
    params_mapping: Dict[str, str] = None  # 参数映射规则
    step_description: str = ""
    step_index: int = 1
    kwargs: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.params_mapping is None:
            self.params_mapping = {}


# 在现有TaskOrchestrator类中添加AI驱动方法


class TaskOrchestrator:
    def __init__(self, stream_manager: StreamTaskManager):
        self.stream_manager = stream_manager
        # self.task_templates = self._init_task_templates()
        # self.intent_patterns = self._init_intent_patterns()
        self.ai_planner = None
        # 添加意图分析智能体
        self.intent_agent = None

    async def report_orchestrate_task(
        self, user_query: str, conversation_history: Optional[List] = None, **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """报告驱动的智能任务编排"""
        try:
            # 1. 创建动态工作流
            workflow_id = await self.stream_manager.create_workflow(
                name=f"Report_Generated_{datetime.now().strftime('%H%M%S')}", execution_mode=ExecutionMode.PIPELINE
            )

            # 2. 获取预定义的任务步骤
            task_steps = await self.report_task_step()

            # 3. 根据预定义步骤创建任务
            task_ids = {}
            step_index = 1
            for step in task_steps:
                # 创建智能体
                agent = await self._create_agent_from_plan(step)
                if agent:
                    await self.stream_manager.register_agent(agent)

                # 处理依赖关系
                dependencies = [task_ids[dep] for dep in step.dependencies if dep in task_ids]
                task_id = await self.stream_manager.create_task(
                    name=step.step_name,
                    agent_type=AgentType(step.agent_type),
                    agent_id=agent.agent_id if agent else None,
                    dependencies=dependencies,
                    workflow_id=workflow_id,
                    metadata={"step_config": step, "user_query": user_query, "report_generated": True},
                    step_index=step.step_index,
                    step_name=step.step_description,
                )
                task_ids[step.step_name] = task_id
                step_index += 1

            # 4. 执行报告生成工作流
            final_message = {}
            async for message in self.stream_manager.execute_workflow(workflow_id, user_query=user_query, **kwargs):
                if message.get("type_name") == "result" and message.get("file"):
                    final_message["message"] = f"关于'{user_query}' {message.get('message')}"
                    final_message["type"] = "final"
                    final_message["status"] = "success"
                    final_message["success_message"] = "报告生成已完成"
                    final_message["file"] = message.get("file")
                yield message
            yield final_message

        except Exception as e:
            yield {"type": "error", "message": f"❌ 报告驱动的智能任务编排失败: {str(e)}"}

    async def report_task_step(self, **kwargs) -> list:
        """报告驱动的智能任务编排"""
        return [
            TaskStep(
                step_name="mcp_query",
                agent_type=AgentType.MCP_DATA.value,
                dependencies=[],  # 第一个步骤没有依赖
                params_mapping={"intent_result": "intent_analysis.result"},
                step_index=1,
                step_description=settings.available_agents[AgentType.MCP_DATA.value].get(
                    "description", "通过MCP数据查询数据"
                )
                if settings.available_agents[AgentType.MCP_DATA.value]
                else "查询MCP数据",
                # kwargs={"parameters": kwargs.get("parameters", {}),"query_type": kwargs.get("query_type", [])}
            ),
            TaskStep(
                step_name="data_splitting",
                agent_type=AgentType.DATA_PROCESSING.value,
                dependencies=["mcp_query"],
                params_mapping={"data": "mcp_query.result.data"},
                step_index=2,
                step_description=settings.available_agents[AgentType.DATA_PROCESSING.value].get(
                    "description", "对数据进行按块划分"
                )
                if settings.available_agents[AgentType.DATA_PROCESSING.value]
                else "数据处理",
            ),
            TaskStep(
                step_name="ai_analysis",
                agent_type=AgentType.AI_ANALYSIS.value,
                dependencies=["data_splitting"],
                params_mapping={"chunks": "data_splitting.result.chunks"},
                step_index=3,
                step_description=settings.available_agents[AgentType.AI_ANALYSIS.value].get(
                    "description", "对每块数据进行分析，并给出分析结果"
                )
                if settings.available_agents[AgentType.AI_ANALYSIS.value]
                else "AI分析",
                # kwargs={'assistant': kwargs.get("assistant", {})}
            ),
            TaskStep(
                step_name="generate_report",
                agent_type=AgentType.CUSTOM.value,
                dependencies=["ai_analysis"],
                params_mapping={"analysis_result": "ai_analysis.result"},
                step_index=4,
                step_description="根据分析结果，生成报告",
                # kwargs=kwargs
            ),
        ]

    async def ai_orchestrate_task(
        self, user_query: str, conversation_history: Optional[List] = None, **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """AI驱动的智能任务编排"""
        try:
            # 1. 创建AI任务规划器
            if not self.ai_planner:
                self.ai_planner = AITaskPlannerAgent(
                    agent_id=f"ai_planner_{datetime.now().strftime('%H%M%S')}",
                    conversation_history=conversation_history,
                )
                await self.stream_manager.register_agent(self.ai_planner)
            # 2. 生成智能任务计划
            plan_result = None
            async for response in self.ai_planner.execute(user_query=user_query):
                yield response
                plan_result = response.get("result")
                # if plan_result:
                #     print('plan_result=============', plan_result)
                # data = plan_result.data
                # print('data=============', data)

            if not plan_result:
                yield {"type": "error", "message": "❌ AI任务规划失败"}
                return

            # 3. 解析并执行AI生成的计划
            plan_result.get("query_analysis", {})
            task_steps = plan_result.get("task_steps", [])

            # 4. 创建动态工作流
            workflow_id = await self.stream_manager.create_workflow(
                name=f"AI_Generated_{datetime.now().strftime('%H%M%S')}", execution_mode=ExecutionMode.PIPELINE
            )
            print("task_steps======================", task_steps)
            # 5. 根据AI计划创建任务
            task_ids = {}
            step_index = 1
            for step in task_steps:
                # 将字典转换为TaskStep对象
                task_step = TaskStep(
                    step_name=step["step_name"],
                    step_description=step["step_description"],
                    step_index=step_index,
                    agent_type=AgentType(step["agent_type"]),
                    dependencies=step.get("dependencies", []),
                    params_mapping=step.get("params_mapping", {}),
                )

                # 创建智能体
                agent = await self._create_agent_from_plan(step)
                if agent:
                    await self.stream_manager.register_agent(agent)

                # 修复：使用step_name作为依赖查找的键
                dependencies = [task_ids[dep] for dep in step.get("dependencies", []) if dep in task_ids]
                task_id = await self.stream_manager.create_task(
                    name=step["step_name"],  # 使用step_name作为任务名称
                    agent_type=AgentType(step["agent_type"]),
                    agent_id=agent.agent_id if agent else None,
                    dependencies=dependencies,
                    workflow_id=workflow_id,
                    metadata={"step_config": task_step, "user_query": user_query, "ai_generated": True},
                    step_index=step_index,
                    step_name=step["step_description"],
                )
                # 修复：使用step_name作为映射键，而不是step_name+index
                task_ids[step["step_name"]] = task_id
                step_index += 1
            # 6. 执行AI生成的工作流
            yield {"type": "info", "message": f"🚀 开始执行AI生成的工作流: {workflow_id[:8]}"}
            final_message = {}
            async for message in self.stream_manager.execute_workflow(workflow_id, user_query=user_query, **kwargs):
                if message.get("type_name") == "result" and message.get("file"):
                    final_message["message"] = f"关于'{user_query}' {message.get('message')}"
                    final_message["type"] = "final"
                    final_message["file"] = message.get("file")
                yield message
            yield final_message

        except Exception as e:
            yield {"type": "error", "message": f"❌ AI任务编排失败: {str(e)}"}

    async def _create_agent_from_plan(self, step_config):
        """根据AI计划创建智能体"""
        # 支持TaskStep对象和字典两种类型
        if hasattr(step_config, "agent_type"):
            # TaskStep对象
            agent_type = AgentType(step_config.agent_type)
            step_name = step_config.step_name
        elif isinstance(step_config, dict):
            # 字典类型
            agent_type = AgentType(step_config["agent_type"])
            step_name = step_config["step_name"]
        else:
            raise ValueError(f"Unsupported step_config type: {type(step_config)}")

        # 使用现有的_create_agent方法
        return await self._create_agent(agent_type, step_name)

    def _init_task_templates(self) -> Dict[TaskTemplate, List[TaskStep]]:
        """初始化任务模板"""
        return {
            TaskTemplate.SIMPLE_QUERY: [
                TaskStep(
                    step_name="mcp_query",
                    agent_type=AgentType.MCP_DATA.value,
                    dependencies=["user_query"],
                    params_mapping={"user_query": "user_query"},
                    step_index=1,
                    step_description=settings.available_agents[AgentType.MCP_DATA.value].get(
                        "description", "查询MCP数据"
                    )
                    if settings.available_agents[AgentType.MCP_DATA.value]
                    else "查询MCP数据",
                ),
                TaskStep(
                    step_name="output_result",
                    agent_type=AgentType.CUSTOM,
                    dependencies=["mcp_query"],
                    params_mapping={"data": "mcp_query.result"},
                    step_index=2,
                    step_description="输出结果",
                ),
            ],
            TaskTemplate.ANALYSIS_REPORT: [
                TaskStep(
                    step_name="mcp_query",
                    agent_type=AgentType.MCP_DATA.value,
                    dependencies=["intent_analysis"],
                    params_mapping={"intent_result": "intent_analysis.result"},
                    step_index=1,
                    step_description=settings.available_agents[AgentType.MCP_DATA.value].get(
                        "description", "查询MCP数据"
                    )
                    if settings.available_agents[AgentType.MCP_DATA.value]
                    else "查询MCP数据",
                ),
                TaskStep(
                    step_name="data_splitting",
                    agent_type=AgentType.DATA_PROCESSING.value,
                    dependencies=["mcp_query"],
                    params_mapping={"data": "mcp_query.result.data"},
                    step_index=2,
                    step_description=settings.available_agents[AgentType.DATA_PROCESSING.value].get(
                        "description", "数据处理"
                    )
                    if settings.available_agents[AgentType.DATA_PROCESSING.value]
                    else "数据处理",
                ),
                TaskStep(
                    step_name="ai_analysis",
                    agent_type=AgentType.AI_ANALYSIS.value,
                    dependencies=["data_splitting"],
                    params_mapping={"chunks": "data_splitting.result.chunks"},
                    step_index=3,
                    step_description=settings.available_agents[AgentType.AI_ANALYSIS.value].get("description", "AI分析")
                    if settings.available_agents[AgentType.AI_ANALYSIS.value]
                    else "AI分析",
                ),
                TaskStep(
                    step_name="generate_report",
                    agent_type=AgentType.CUSTOM.value,
                    dependencies=["ai_analysis"],
                    params_mapping={"analysis_result": "ai_analysis.result"},
                    step_index=4,
                    step_description="生成报告",
                ),
            ],
        }

    def _init_intent_patterns(self) -> Dict[str, TaskTemplate]:
        """初始化意图模式映射"""
        return {
            r"查询.*信息": TaskTemplate.SIMPLE_QUERY,
            r"生成.*报告": TaskTemplate.ANALYSIS_REPORT,
            r"分析.*数据": TaskTemplate.ANALYSIS_REPORT,
            r"获取.*详情": TaskTemplate.SIMPLE_QUERY,
        }

    def detect_task_template(self, user_query: str) -> Optional[TaskTemplate]:
        """检测用户查询对应的任务模板"""
        import re

        for pattern, template in self.intent_patterns.items():
            if re.search(pattern, user_query):
                return template
        return None

    async def orchestrate_task(self, user_query: str, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """编排并执行任务"""
        # 1. 检测任务模板
        template = self.detect_task_template(user_query)
        if not template:
            yield {"type": "error", "message": f"❌ 无法识别查询意图: {user_query}"}
            return

        yield {"type": "info", "message": f"🎯 检测到任务类型: {template.value}"}

        # 2. 创建工作流
        workflow_id = await self.stream_manager.create_workflow(
            name=f"Auto_{template.value}_{datetime.now().strftime('%H%M%S')}", execution_mode=ExecutionMode.SEQUENTIAL
        )

        # 3. 根据模板创建任务
        task_steps = self.task_templates[template]
        task_ids = {}

        for step in task_steps:
            # 创建智能体
            agent = await self._create_agent(step.agent_type, step.step_name)
            if agent:
                await self.stream_manager.register_agent(agent)

            # 创建任务
            dependencies = [task_ids[dep] for dep in step.dependencies if dep in task_ids]
            task_id = await self.stream_manager.create_task(
                name=step.step_name,
                agent_type=step.agent_type,
                agent_id=agent.agent_id if agent else None,
                dependencies=dependencies,
                workflow_id=workflow_id,
                metadata={"step_config": step, "user_query": user_query},
            )
            task_ids[step.step_name] = task_id

        # 4. 执行工作流
        yield {"type": "info", "message": f"🚀 开始执行工作流: {workflow_id[:8]}"}
        async for message in self.stream_manager.execute_workflow(workflow_id, user_query=user_query, **kwargs):
            yield message

    async def _create_agent(self, agent_type: AgentType, step_name: str):
        """根据类型创建智能体"""
        agent_id = f"{step_name}_{datetime.now().strftime('%H%M%S')}"

        if agent_type == AgentType.GENERAL_CHAT:
            return GeneralChatAgent(agent_id=agent_id)
        elif agent_type == AgentType.MCP_DATA:
            return MCPDataAgent(agent_id=agent_id)
        elif agent_type == AgentType.DATA_PROCESSING:
            return DataSplittingAgent(agent_id=agent_id)
        elif agent_type == AgentType.AI_ANALYSIS:
            return AIDataAnalysisAgent(agent_id=agent_id)
        elif agent_type == AgentType.CUSTOM:
            return self._create_custom_agent(agent_id, step_name)

        return None

    def _create_custom_agent(self, agent_id: str, step_name: str):
        """创建自定义智能体"""
        from backend.agents.schema.base_agent import BaseAgent

        class CustomOutputAgent(BaseAgent):
            def __init__(self, agent_id: str):
                super().__init__(agent_id, AgentType.CUSTOM, {})
                self.step_name = step_name

            async def execute(self, **kwargs):
                if self.step_name == "output_result":
                    data = kwargs.get("data", {})
                    yield {
                        "type": "result",
                        "status": "completed",
                        "message": f"查询结果: {data}",
                        "progress": 100,
                        "result": data,
                        "success": True,
                    }
                elif self.step_name == "generate_report":
                    analysis_result = kwargs.get("analysis_result", {})
                    report = self._generate_final_report(analysis_result)
                    yield {
                        "type": "result",
                        "status": "completed",
                        "message": "报告生成完成",
                        "progress": 100,
                        "result": report,
                        "success": True,
                    }

            def _generate_final_report(self, analysis_result):
                return f"""
                    # 数据分析报告

                    ## 分析概要
                    {analysis_result.get("insights", {}).get("analysis_summary", "暂无分析结果")}

                    ## 详细分析
                    {analysis_result.get("insights", {}).get("analytical_report", "暂无详细分析")}

                    ## 建议
                    {", ".join(analysis_result.get("recommendations", []))}

                    ## 置信度
                    {analysis_result.get("confidence", 0):.2f}

                    ---
                    报告生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                """

        return CustomOutputAgent(agent_id)
