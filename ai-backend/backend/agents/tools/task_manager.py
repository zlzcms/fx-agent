# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-09-06 14:01:26
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-09-08 20:42:11
import asyncio
import importlib
import re
import uuid

from datetime import datetime
from os import path
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

from backend.agents.agents.general_chat_agent import GeneralChatAgent
from backend.agents.config.prompt.agent import PLAN_PROMPT, SUMMARIZE_PROMPT
from backend.agents.schema.agent import Base, YieldResponse
from backend.common.log import logger


class Task:
    """表示单个任务的类"""

    def __init__(
        self,
        task_id: str,
        name: str,
        description: str,
        executor_type: str,
        executor: Base | Callable | str,  # 执行者（智能体实例、工具函数或智能体名称字符串）
        executor_link_param: list[tuple[str, str]] = [],
        parameters: Dict[str, Any] = None,
        status: str = "pending",
    ):
        self.task_id = task_id
        self.name = name
        self.description = description
        self.executor_type = executor_type
        self.executor = executor
        self.executor_link_param = executor_link_param or []
        self.parameters = parameters or {}
        self.status = status
        self.result = {}
        self.error = None
        self.created_at = datetime.now()
        self.completed_at = None
        logger.debug(f"Task created: {name} (ID: {task_id}, Type: {executor_type})")

    def to_dict(self) -> Dict[str, Any]:
        """将任务转换为字典"""
        logger.debug(f"Converting task to dict: {self.task_id}")
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "executor": str(self.executor),
            "executor_type": self.executor_type,
            "executor_link_param": self.executor_link_param,
            "parameters": self.parameters,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    def to_prompt(self) -> str:
        """将任务转换为提示"""
        logger.debug(f"Converting task to prompt: {self.task_id}")
        return {"name": self.name, "description": self.description, "executor_type": self.executor_type}


class TaskManager:
    """任务管理器，负责注册和执行智能体与工具"""

    def __init__(self, export_base_path: str = ""):
        self.tasks = []  # 任务列表
        self.results = {}  # 任务结果
        self.last_result = {}
        self.export_base_path = export_base_path
        self.log = []
        self.is_plan = False
        self.plan_steps = []
        self.bebug = []
        self.chat_agent = GeneralChatAgent(task_id=f"task_{str(uuid.uuid4())}")

    def create_task(
        self,
        name: str,
        description: str,
        executor_type: str,
        executor: Callable | str,
        parameters: Dict[str, Any] = {},
        executor_link_param: list[tuple[str, str]] = [],
    ) -> str:
        """创建任务"""
        logger.info(f"Creating task: {name} (Type: {executor_type})")
        # 生成任务ID
        task_id = str(uuid.uuid4())

        # 确定执行器类型
        if executor_type == "agent":
            # 字符串类型的executor被视为agent名称
            if isinstance(executor, str):
                task_id = f"{executor}_{task_id}"
                logger.debug(f"Agent task ID generated: {task_id}")
                try:
                    if parameters is None:
                        parameters = {}
                    config = parameters.get("config", {})
                    config["export_base_path"] = self.export_base_path
                    logger.debug(f"Loading agent: {executor} with config: {config}")
                    executor = self.load_agent(executor, task_id=task_id, config=config)
                    logger.info(f"Agent loaded successfully: {executor}")
                except Exception as e:
                    error_msg = f"Failed to load agent {executor}: {str(e)}"
                    logger.error(error_msg)
                    self.log.append({"title": "系统异常", "content": error_msg})
                    raise ValueError(error_msg)
        elif executor_type == "tool":
            if not callable(executor):
                error_msg = "executor must be a callable"
                logger.error(error_msg)
                self.log.append({"title": "系统异常", "content": error_msg})
                raise ValueError(error_msg)
            task_id = f"{executor.__name__}_{task_id}"
            logger.debug(f"Tool task ID generated: {task_id}")
        if not task_id:
            error_msg = "task_id is required"
            logger.error(error_msg)
            self.log.append({"title": "系统异常", "content": error_msg})
            raise ValueError(error_msg)
        # 创建任务
        task = Task(
            task_id=task_id,
            name=name,
            description=description,
            executor_type=executor_type,
            executor=executor,
            executor_link_param=executor_link_param,
            parameters=parameters or {},
        )
        # print(f"Task instance: {task}")
        # 添加到任务列表
        self.tasks.append(task)
        logger.info(f"已创建任务: {name} (ID: {task_id})")

        return task_id

    async def execute_task(
        self, task: Task, user_query: str, conversation_history: Optional[List] = None, **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """执行单个任务，以异步生成器方式返回结果"""
        logger.info(f"Starting task execution: {task.name} (ID: {task.task_id})")
        # 添加一个微小的延迟，确保上面的消息被处理
        await asyncio.sleep(0)

        try:
            if task.status == "failed":
                logger.warning(f"Task already failed: {task.name} (ID: {task.task_id})")
                yield {"type": "task_error", "task_id": task.task_id, "status": "failed", "error": task.error}
                return

            task.status = "running"
            logger.info(f"开始执行任务: {task.name} (ID: {task.task_id})")

            # 发送任务开始消息
            start_message = {
                "type": "task",
                "task_id": task.task_id,
                "message": f"开始执行任务: {task.name} (ID: {task.task_id})",
            }
            yield start_message

            # 增加延迟确保消息被处理
            await asyncio.sleep(0.1)

            # 合并参数
            parameters = {**task.parameters, **kwargs}
            log = []
            if isinstance(task.executor, Base) and hasattr(task.executor, "execute"):
                async for chunk in task.executor.execute(user_query, conversation_history, **parameters):
                    if isinstance(chunk, YieldResponse):
                        yield chunk.to_dict()
                    else:
                        logger.info(f"Yield Task result: {chunk}")
                        yield chunk
                task.result = task.executor.result
                task.status = task.executor.state.value
                task.error = task.executor.error
                self.bebug = self.bebug + task.executor.bebug
                log = task.executor.log
            elif callable(task.executor):
                if asyncio.iscoroutinefunction(task.executor):
                    # 如果工具是异步函数
                    if hasattr(task.executor, "__aiter__") or hasattr(task.executor, "__anext__"):
                        result = {}
                        async for chunk in task.executor(**parameters):
                            if chunk.get("result"):
                                result = chunk.get("result")
                            yield chunk
                    else:
                        result = await task.executor(**parameters)
                else:
                    result = task.executor(**parameters)

                task.result = result  # 保存完整的结果，包括file等字段
                task.error = result.get("error", None)
                task.status = result.get("status", "completed")
                log = result.get("log", [])
                self.bebug = self.bebug + result.get("bebug", [])
            # 保存结果
            self.last_result = task.result
            task.completed_at = datetime.now()
            self.results[task.task_id] = task.result
            yield {"type": "log", "title": task.name, "content": log}
            # 检查任务是否失败
            if task.status == "failed":
                error_message = task.error if task.error else "未知错误"
                logger.error(f"Task execution failed: {task.name} (ID: {task.task_id}), Error: {error_message}")
                yield {"type": "task_error", "task_id": task.task_id, "status": "failed", "error": error_message}
                return
            task.status = "completed"
            logger.info(f"任务执行完成: {task.name} (ID: {task.task_id})")

        except Exception as e:
            error_message = str(e) if e else "未知异常"
            logger.error(f"任务执行失败: {task.name} (ID: {task.task_id}), 错误: {error_message}")
            task.status = "failed"
            task.error = error_message
            yield {"type": "task_error", "task_id": task.task_id, "status": "failed", "error": error_message}

    async def execute_tasks(
        self, user_query: str, conversation_history: Optional[List] = None, **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """按顺序执行所有任务"""
        logger.info(f"Starting execution of {len(self.tasks)} tasks")
        self.bebug = []
        if self.is_plan:
            logger.info("Generating task plan")
            async for plan_chunk in self.get_task_plan(user_query):
                yield plan_chunk
            # 确保计划消息被处理
            await asyncio.sleep(0.1)

        previous_task: Task = None
        for i, task in enumerate(self.tasks):
            # 如果需要传递上一个任务的结果，并且有上一个任务的结果
            if previous_task is not None and i > 0:
                if previous_task.executor_link_param:
                    for link_param in previous_task.executor_link_param:
                        task.parameters[link_param[1]] = previous_task.result.get(link_param[0])
                else:
                    task.parameters["previous_result"] = previous_task.result

            # 先发送任务标题，并确保它被处理
            if self.is_plan:
                if self.plan_steps and i < len(self.plan_steps) and self.plan_steps[i]:
                    step_message = self.plan_steps[i].strip()
                else:
                    step_message = f"{task.name}, 开始{task.description}"
                title_message = {
                    "type": "step",
                    "type_name": "title",
                    "message": step_message,
                }
                yield title_message

                # 确保标题消息被处理后再执行任务
                await asyncio.sleep(0.1)

            # 执行当前任务
            async for result_chunk in self.execute_task(task, user_query, conversation_history, **kwargs):
                yield result_chunk
            if task.status == "failed":
                logger.error(f"Task failed, stopping execution: {task.name}")
                error_message = task.error if task.error else "未知错误"
                yield {
                    "type": "error",
                    "status": "failed",
                    "message": f" {task.name} 任务失败:{error_message}",
                    "failed_task": task.name,
                    "error": error_message,
                }
                break
            elif task.status == "completed":
                previous_task = task
                if self.is_plan:
                    data = task.result.get("output", task.result.get("data", ""))
                    if data:
                        logger.debug(f"Summarizing task result: {task.name}")
                        async for summarize_chunk in self.chat_summarize(user_query, data):
                            yield summarize_chunk
        logger.info("All tasks execution completed")

    async def get_task_plan(self, user_query: str) -> AsyncGenerator[Dict[str, Any], None]:
        """获取任务计划"""
        logger.info("Generating task plan")
        try:
            task_info = []
            for task in self.tasks:
                task_info.append(task.to_prompt())
            logger.debug(f"Task info for planning: {task_info}")

            all_chunk = ""
            async for result_chunk in self.chat_agent.chat_stream(
                user_query=user_query,
                conversation_history=[],
                system_prompt=PLAN_PROMPT.format(task_info=task_info, user_query=user_query),
            ):
                result_chunk["type"] = "plan"
                all_chunk += result_chunk["message"]
                yield result_chunk
                # 确保计划消息被立即处理
                await asyncio.sleep(0.1)
            # 提取步骤
            self.plan_steps = self.extract_steps_from_plan(all_chunk)
            logger.info("Task plan generated successfully")
        except Exception as e:
            logger.error(f"Failed to generate task plan: {str(e)}")
            yield {"type": "plan", "message": f"获取任务计划失败: {str(e)}"}

    async def chat_summarize(self, user_query: str, data: Any) -> AsyncGenerator[Dict[str, Any], None]:
        """获取总结结果"""
        logger.info("Starting task result summarization")
        try:
            # 将数据转换为字符串并截取前1000个字符
            data_str = str(data) if not isinstance(data, str) else data
            if len(data_str) > 5000:
                data_str = data_str[:5000] + "\n\n..."
                logger.info(f"Data truncated to 1000 characters (original: {len(str(data))} chars)")

            print("=========data_str===============", user_query)
            async for result_chunk in self.chat_agent.chat_stream(
                user_query=user_query,
                conversation_history=[],
                system_prompt=SUMMARIZE_PROMPT.format(data_summary=data_str, user_query=user_query),
            ):
                result_chunk["type"] = "summarize"
                result_chunk["status"] = "running"
                yield result_chunk
                # 确保总结消息被立即处理
                await asyncio.sleep(0.1)
            yield {"type": "summarize", "status": "completed", "message": ""}
            logger.info("Task result summarization completed")
        except Exception as e:
            logger.error(f"Failed to summarize task result: {str(e)}")
            yield {"type": "summarize", "message": f"总结失败: {str(e)}"}

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取指定ID的任务"""
        logger.debug(f"Looking for task: {task_id}")
        for task in self.tasks:
            if task.task_id == task_id:
                logger.debug(f"Task found: {task.name}")
                return task
        logger.warning(f"Task not found: {task_id}")
        return None

    def get_task_result(self, task_id: str) -> Optional[Any]:
        """获取指定任务的结果"""
        logger.debug(f"Getting result for task: {task_id}")
        result = self.results.get(task_id)
        if result:
            logger.debug(f"Result found for task: {task_id}")
        else:
            logger.warning(f"No result found for task: {task_id}")
        return result

    def clear_tasks(self) -> None:
        """清除所有任务"""
        logger.info(f"Clearing {len(self.tasks)} tasks")
        self.tasks = []
        self.results = {}
        logger.info("已清除所有任务")

    def get_task_status(self) -> List[Dict[str, Any]]:
        """获取所有任务的状态"""
        status_list = [task.to_dict() for task in self.tasks]
        return status_list

    def load_agent(self, agent_name: str, task_id: Optional[str] = None, config: Dict[str, Any] = {}) -> Base:
        """
        Dynamically load an agent by its name.

        Args:
            agent_name: The name of the agent class to load (e.g., "DataAnalyzeAgent")
            task_id: Optional task ID to pass to the agent constructor
            config: Configuration dictionary to pass to the agent constructor

        Returns:
            An instance of the requested agent

        Raises:
            ImportError: If the agent module cannot be imported
            AttributeError: If the agent class cannot be found in the module
            Exception: For any other errors during agent instantiation
        """
        logger.info(f"Loading agent: {agent_name} (task_id: {task_id})")
        try:
            # Try to import the agent module
            module_name = agent_name.lower()
            current_dir = path.dirname(path.abspath(__file__))
            agents_dir = path.join(current_dir, "..", "agents")
            module_file = path.join(agents_dir, f"{module_name}.py")

            if not path.exists(module_file):
                raise ImportError(f"Agent module file not found: {module_file}")

            # print(f"Found agent module file=================: {module_file}")
            agent_class_name_split = agent_name.split("_")
            agent_class_name = "".join(part.capitalize() for part in agent_class_name_split)
            module_path = f"backend.agents.agents.{module_name}"
            module = importlib.import_module(module_path)
            # print(f"Module imported successfully: {module}")
            # print(f"Module attributes: {[name for name in dir(module) if not name.startswith('_')]}")
            # Check if the agent class exists in the module
            if not hasattr(module, agent_class_name):
                available_classes = [name for name in dir(module) if not name.startswith("_")]
                raise AttributeError(
                    f"Agent class '{agent_class_name}' not found in module '{module_path}'. Available classes: {available_classes}"
                )
            # Get the agent class
            agent_class = getattr(module, agent_class_name)
            # print(f"Agent class type: {type(agent_class)}")
            # print(f"Agent class repr: {repr(agent_class)}")
            # print(f"Is agent_class callable: {callable(agent_class)}")
            # Check if it's a tuple
            if isinstance(agent_class, tuple):
                logger.warning(f"Agent class is a tuple with {len(agent_class)} items")
                # print(f"Agent class is a tuple with {len(agent_class)} items:")
                for i, item in enumerate(agent_class):
                    print(f"  Item {i}: {item} (type: {type(item)})")
                # Try to get the first item if it's a tuple
                if len(agent_class) > 0:
                    # agent_class = agent_class[0]
                    print(f"Using first item as agent class: {agent_class}")

            # Instantiate the agent
            if task_id:
                agent_instance = agent_class(task_id=task_id, config=config)
            else:
                agent_instance = agent_class(config=config)
            logger.info(f"Agent loaded successfully: {agent_name} -> {agent_instance}")

            return agent_instance

        except ImportError as e:
            logger.error(f"Failed to import agent module for {agent_name}: {str(e)}")
            raise ImportError(f"Agent module not found: {agent_name}_agent")

        except AttributeError as e:
            logger.error(f"Failed to find agent class {agent_class_name} in module: {str(e)}")
            raise AttributeError(f"Agent class not found: {agent_class_name}")

        except Exception as e:
            logger.error(f"Failed to instantiate agent {agent_name}: {str(e)}")
            raise Exception(f"Failed to instantiate agent {agent_name}: {str(e)}")

    def extract_steps_from_plan(self, plan_text: str) -> List[str]:
        """
        从计划文本中提取步骤
        提取格式为 "数字. 标题: 描述" 的步骤

        Args:
            plan_text: 计划文本

        Returns:
            提取的步骤列表
        """
        try:
            steps = []
            # 按行分割
            lines = plan_text.split("\n")

            # 第一种模式：匹配 "数字. 标题: 描述"
            pattern_with_colon = r"^\s*(\d+)\.\s*([^:]+):\s*(.+)$"
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                match = re.match(pattern_with_colon, line)
                if match:
                    step_number = match.group(1)
                    step_title = match.group(2).strip()
                    step_description = match.group(3).strip()
                    step_text = f"{step_number}. {step_title}: {step_description}"
                    steps.append(step_text)

            # 如果上面的方法没有匹配到，尝试更简单的模式：匹配 "数字. 文本"
            if not steps:
                pattern_simple = r"^\s*(\d+)\.\s*(.+)$"
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    match = re.match(pattern_simple, line)
                    if match:
                        step_number = match.group(1)
                        step_text = match.group(2).strip()
                        # 过滤太短的行（少于10个字符），避免匹配到不相关的内容
                        if len(step_text) > 10:
                            steps.append(step_text)

            # 去重并保持顺序
            seen = set()
            unique_steps = []
            for step in steps:
                if step not in seen:
                    seen.add(step)
                    unique_steps.append(step)

            return unique_steps
        except Exception as e:
            logger.error(f"Failed to extract steps from plan: {str(e)}")
            return []
