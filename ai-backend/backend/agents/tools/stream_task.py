# -*- coding: utf-8 -*-
# @Author: claude-3.7-sonnet
# @Date:   2023-11-18 10:28:13

import asyncio
import logging
import uuid

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional, Set

from backend.agents.agents.general_chat_agent import GeneralChatAgent
from backend.agents.config.prompt.general_chat import COMPLETION_PROMPT, COMPLETION_SYSTEM_PROMPT
from backend.agents.config.setting import settings
from backend.agents.schema.base_agent import AgentType, BaseAgent
from backend.agents.tools.workflow_info import ExecutionMode, WorkflowInfo, WorkflowStatus

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态枚举"""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    CANCELED = "canceled"
    COMPLETED = "completed"
    FAILED = "failed"
    DISCONNECTED = "disconnected"
    WAITING_DEPENDENCIES = "waiting_dependencies"


# ExecutionMode 现在从 workflow_info 模块导入
@dataclass
class TaskInfo:
    """任务信息数据类"""

    task_id: str
    name: str
    info: dict
    step_index: int
    step_name: str
    status: TaskStatus
    agent_type: AgentType = AgentType.CUSTOM
    agent_id: Optional[str] = None
    progress: float = 0.0
    total_steps: int = 0
    current_step: int = 0
    created_at: datetime = None
    started_at: datetime = None
    completed_at: datetime = None
    error_message: str = None
    metadata: Dict[str, Any] = None
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    workflow_id: Optional[str] = None
    priority: int = 0
    success: bool = False
    result: Any = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        data["status"] = self.status.value
        data["agent_type"] = self.agent_type.value
        data["success"] = self.success
        data["created_at"] = self.created_at.isoformat() if self.created_at else None
        data["started_at"] = self.started_at.isoformat() if self.started_at else None
        data["completed_at"] = self.completed_at.isoformat() if self.completed_at else None
        return data


# WorkflowInfo 现在从 workflow_info 模块导入


class StreamTaskManager:
    """多智能体流式任务执行管理器"""

    def __init__(self):
        self.active_tasks: Dict[str, TaskInfo] = {}
        self.task_generators: Dict[str, AsyncGenerator] = {}
        self.task_callbacks: Dict[str, Callable] = {}
        self.agents: Dict[str, BaseAgent] = {}
        self.workflows: Dict[str, WorkflowInfo] = {}
        self.task_dependencies: Dict[str, Set[str]] = {}  # task_id -> dependencies
        self.task_dependents: Dict[str, Set[str]] = {}  # task_id -> dependents
        self._lock = asyncio.Lock()
        self._workflow_lock = asyncio.Lock()

    # ==================== 智能体管理 ====================

    async def register_agent(self, agent: BaseAgent) -> bool:
        """注册智能体"""
        async with self._lock:
            if agent.agent_id in self.agents:
                return False
            self.agents[agent.agent_id] = agent
            return True

    async def unregister_agent(self, agent_id: str) -> bool:
        """注销智能体"""
        async with self._lock:
            if agent_id not in self.agents:
                return False
            agent = self.agents[agent_id]
            if agent.is_busy:
                return False
            del self.agents[agent_id]
            return True

    async def get_available_agents(self, agent_type: Optional[AgentType] = None) -> List[BaseAgent]:
        """获取可用的智能体"""
        available = []
        for agent in self.agents.values():
            if not agent.is_busy:
                if agent_type is None or agent.agent_type == agent_type:
                    available.append(agent)
        return available

    # ==================== 任务管理 ====================

    async def create_task(
        self,
        name: str,
        task_func: Optional[Callable] = None,
        agent_id: Optional[str] = None,
        agent_type: AgentType = AgentType.CUSTOM,
        total_steps: int = 100,
        dependencies: Optional[List[str]] = None,
        workflow_id: Optional[str] = None,
        priority: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
        step_index: int = 1,
        step_name: str = "",
    ) -> str:
        """创建新任务"""
        task_id = str(uuid.uuid4())
        dependencies = dependencies or []

        async with self._lock:
            task_info = TaskInfo(
                task_id=task_id,
                name=name,
                step_index=step_index,
                step_name=step_name,
                info=settings.available_agents.get(agent_type.value, {}),
                status=TaskStatus.PENDING,
                agent_type=agent_type,
                agent_id=agent_id,
                total_steps=total_steps,
                dependencies=dependencies,
                workflow_id=workflow_id,
                priority=priority,
                metadata=metadata or {},
            )

            # 检查依赖任务是否存在
            for dep_id in dependencies:
                if dep_id not in self.active_tasks:
                    raise ValueError(f"依赖任务 {dep_id} 不存在")
                # 添加到依赖关系图
                if dep_id not in self.task_dependents:
                    self.task_dependents[dep_id] = set()
                self.task_dependents[dep_id].add(task_id)

            if dependencies:
                self.task_dependencies[task_id] = set(dependencies)
                task_info.status = TaskStatus.WAITING_DEPENDENCIES

            self.active_tasks[task_id] = task_info
            if task_func:
                self.task_callbacks[task_id] = task_func

        await self.add_task_to_workflow(workflow_id, task_id)

        return task_id

    # ==================== 工作流管理 ====================

    async def create_workflow(
        self,
        name: str,
        execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """创建工作流"""
        workflow_id = str(uuid.uuid4())

        async with self._workflow_lock:
            workflow_info = WorkflowInfo(
                workflow_id=workflow_id, name=name, execution_mode=execution_mode, metadata=metadata or {}
            )
            self.workflows[workflow_id] = workflow_info

        return workflow_id

    async def add_task_to_workflow(self, workflow_id: str, task_id: str) -> bool:
        """将任务添加到工作流"""
        async with self._workflow_lock:
            if workflow_id not in self.workflows:
                return False
            if task_id not in self.active_tasks:
                return False

            workflow = self.workflows[workflow_id]
            if task_id not in workflow.task_ids:
                workflow.task_ids.append(task_id)
                self.active_tasks[task_id].workflow_id = workflow_id

            return True

    async def execute_workflow(self, workflow_id: str, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """执行工作流"""
        if workflow_id not in self.workflows:
            yield {"type": "error", "message": f"❌ 工作流 {workflow_id[:8]} 不存在"}
            return

        workflow = self.workflows[workflow_id]
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.now()

        try:
            if workflow.execution_mode == ExecutionMode.SEQUENTIAL:
                async for message in self._execute_sequential_workflow(workflow, **kwargs):
                    yield message
            elif workflow.execution_mode == ExecutionMode.PARALLEL:
                async for message in self._execute_parallel_workflow(workflow, **kwargs):
                    yield message
            elif workflow.execution_mode == ExecutionMode.PIPELINE:
                async for message in self._execute_pipeline_workflow(workflow, **kwargs):
                    yield message

            workflow.status = WorkflowStatus.COMPLETED
            workflow.completed_at = datetime.now()
            # yield {"type": "success", "message": f"✅ 工作流 {workflow_id[:8]} 执行完成"}

        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.completed_at = datetime.now()
            yield {"type": "error", "message": f"❌ 工作流 {workflow_id[:8]} 执行失败: {str(e)}"}

    async def _execute_sequential_workflow(
        self, workflow: WorkflowInfo, **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """顺序执行工作流"""
        # yield {"type": "info", "message": f"🔄 开始顺序执行工作流: {workflow.name}"}

        for task_id in workflow.task_ids:
            # yield {"type": "info", "message": f"📝 开始执行任务: {task_id[:8]}"}
            async for message in self.start_task_stream(task_id, **kwargs):
                yield message

            # 检查任务是否成功完成
            task_info = self.active_tasks.get(task_id)
            if task_info and task_info.status != TaskStatus.COMPLETED:
                yield {"type": "warning", "message": f"⚠️ 任务 {task_id[:8]} 未成功完成，停止工作流执行"}
                break

    async def _execute_parallel_workflow(
        self, workflow: WorkflowInfo, **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """并行执行工作流"""
        # yield {"type": "info", "message": f"🔄 开始并行执行工作流: {workflow.name}"}

        # 创建所有任务的协程
        tasks = []
        for task_id in workflow.task_ids:
            task_coro = self._collect_task_messages(task_id, **kwargs)
            tasks.append(asyncio.create_task(task_coro))

        # 等待所有任务完成并收集消息
        completed_tasks = 0
        while completed_tasks < len(tasks):
            for i, task in enumerate(tasks):
                if task.done() and not hasattr(task, "_processed"):
                    task._processed = True
                    completed_tasks += 1
                    try:
                        messages = await task
                        for message in messages:
                            yield message
                    except Exception as e:
                        yield {"type": "error", "message": f"❌ 任务执行失败: {str(e)}"}

            await asyncio.sleep(0.1)  # 避免忙等待

    async def _execute_pipeline_workflow(
        self, workflow: WorkflowInfo, **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """流水线执行工作流"""
        # yield {"type": "info", "message": f"🔄 开始流水线执行工作流: {workflow.name}"}

        # 流水线执行：前一个任务的输出作为后一个任务的输入
        pipeline_data = kwargs

        for task_id in workflow.task_ids:
            # yield {"type": "info", "message": f"📝 流水线执行任务: {task_id[:8]}"}

            async for message in self.start_task_stream(task_id, **pipeline_data):
                yield message

            # 获取任务结果作为下一个任务的输入
            task_info = self.active_tasks.get(task_id)
            if task_info and task_info.result:
                pipeline_data.update({"previous_result": task_info.result})

    async def _collect_task_messages(self, task_id: str, **kwargs) -> List[Dict[str, Any]]:
        """收集任务执行消息"""
        messages = []
        async for message in self.start_task_stream(task_id, **kwargs):
            messages.append(message)
        return messages

    # ==================== 依赖管理 ====================

    async def _check_dependencies_completed(self, task_id: str) -> bool:
        """检查任务依赖是否已完成"""
        if task_id not in self.task_dependencies:
            return True

        for dep_id in self.task_dependencies[task_id]:
            dep_task = self.active_tasks.get(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False

        return True

    async def _notify_dependents(self, completed_task_id: str):
        """通知依赖任务已完成"""
        if completed_task_id not in self.task_dependents:
            return

        for dependent_id in self.task_dependents[completed_task_id]:
            if dependent_id in self.active_tasks:
                dependent_task = self.active_tasks[dependent_id]
                if dependent_task.status == TaskStatus.WAITING_DEPENDENCIES:
                    if await self._check_dependencies_completed(dependent_id):
                        dependent_task.status = TaskStatus.PENDING

    async def _resolve_task_params(self, task_id: str, **base_kwargs) -> Dict[str, Any]:
        """解析任务参数，支持从前置任务结果中获取参数"""
        task_info = self.active_tasks[task_id]
        step_config = task_info.metadata.get("step_config")

        # 添加调试输出
        # print(f"[DEBUG] 解析任务参数 - 任务ID: {task_id}, 任务名: {task_info.name}")
        # print(f"[DEBUG] step_config: {step_config}")
        # print(f"[DEBUG] base_kwargs: {base_kwargs}")

        if not step_config or not step_config.params_mapping:
            # print(f"[DEBUG] 没有参数映射配置，返回原始参数")
            return base_kwargs

        resolved_params = base_kwargs.copy()

        for param_name, source_path in step_config.params_mapping.items():
            # print(f"[DEBUG] 处理参数映射: {param_name} <- {source_path}")
            if "." in source_path:
                # 从其他任务结果中获取参数
                source_task_name, result_path = source_path.split(".", 1)
                # print(f"[DEBUG] 查找源任务: {source_task_name}, 结果路径: {result_path}")

                # 修改：通过任务名称查找task_id
                source_task_id = self._find_task_id_by_name(source_task_name)
                # print(f"[DEBUG] 找到源任务ID: {source_task_id}")

                if source_task_id and source_task_id in self.active_tasks:
                    source_task_info = self.active_tasks[source_task_id]
                    # print(f"[DEBUG] 源任务结果: {source_task_info.result}")

                    if source_task_info.result:
                        value = self._extract_nested_value(source_task_info.result, result_path)
                        # print(f"[DEBUG] 提取的值: {value}")
                        if value is not None:
                            resolved_params[param_name] = value
                            # print(f"[DEBUG] 成功设置参数: {param_name} = {value}")
                    # else:
                    #     print(f"[DEBUG] 未找到源任务或任务结果为空")
            else:
                # 直接从base_kwargs获取
                if source_path in base_kwargs:
                    resolved_params[param_name] = base_kwargs[source_path]
                    # print(f"[DEBUG] 从base_kwargs获取参数: {param_name} = {base_kwargs[source_path]}")

        # print(f"[DEBUG] 最终解析的参数: {resolved_params}")
        return resolved_params

    def _find_task_id_by_name(self, task_name: str) -> Optional[str]:
        """通过任务名称查找task_id"""
        for task_id, task_info in self.active_tasks.items():
            if task_info.name == task_name:
                return task_id
        return None

    def _extract_nested_value(self, data: Any, path: str) -> Any:
        """从嵌套数据结构中提取值"""
        try:
            # 如果路径为空或为"result"，直接返回数据本身
            if not path or path == "result":
                return data

            keys = path.split(".")
            current = data
            for key in keys:
                if isinstance(current, dict):
                    current = current.get(key)
                elif hasattr(current, key):
                    current = getattr(current, key)
                else:
                    return None
            return current
        except (KeyError, TypeError, AttributeError):
            return None

    async def start_task_stream(self, task_id: str, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """启动任务流式执行"""
        if task_id not in self.active_tasks:
            yield {"type": "error", "message": f"❌ 任务 {task_id[:8]} 不存在"}
            return

        task_info = self.active_tasks[task_id]

        # 检查任务依赖
        if not await self._check_dependencies_completed(task_id):
            task_info.status = TaskStatus.WAITING_DEPENDENCIES
            return

        if task_info.status not in [TaskStatus.PENDING, TaskStatus.WAITING_DEPENDENCIES]:
            yield {"type": "warning", "message": f"⚠️ 任务 {task_id[:8]} 状态不正确: {task_info.status.value}"}
            return

        # 更新任务状态
        task_info.status = TaskStatus.RUNNING
        task_info.started_at = datetime.now()

        try:
            yield {"type": "step", "type_name": "title", "message": f"{task_info.step_index}.{task_info.step_name}"}

            # 如果指定了智能体，使用智能体执行
            if task_info.agent_id and task_info.agent_id in self.agents:
                agent = self.agents[task_info.agent_id]
                agent.is_busy = True
                yield {
                    "type": "step",
                    "type_name": "start",
                    "message": f"处理{task_info.info.get('description', task_info.agent_type.value)}",
                }

                try:
                    # 解析任务参数
                    resolved_kwargs = await self._resolve_task_params(task_id, **kwargs)

                    # 准备智能体
                    await agent.prepare(**resolved_kwargs)

                    # 执行智能体任务并保存结果
                    # 在智能体执行循环中添加结果保存逻辑
                    resolved_kwargs["task_id"] = task_id
                    async for result in agent.execute(**resolved_kwargs):
                        if result.get("type") == "result":
                            result["type_name"] = "result"
                            result["type"] = "step"
                        if result.get("type") == "execute":
                            result["type_name"] = "execute"
                            result["type"] = "step"
                        yield result

                        # 保存最终结果
                        if result.get("result") and result.get("status") == "completed":
                            task_info.result = result.get("result")
                            task_info.success = True
                            # 使用AI告诉用户该智能体已完成
                            # yield {"==============使用AI告诉用户该智能体已完成=========="}
                            async for completion_notification in self._send_ai_completion_notification(
                                task_info, result
                            ):
                                yield completion_notification

                    # 清理智能体
                    await agent.cleanup()
                finally:
                    agent.is_busy = False
            else:
                # 获取任务执行函数
                task_func = self.task_callbacks[task_id]

                # 创建任务生成器
                generator = self._execute_task_with_monitoring(task_id, task_func, **kwargs)
                self.task_generators[task_id] = generator

                # 流式输出任务执行结果
                async for message in generator:
                    # 检查任务是否被取消
                    if task_info.status == TaskStatus.CANCELED:
                        yield {
                            "type": "step",
                            "type_name": "warning",
                            "message": f"{task_info.info.get('description', task_info.agent_type.value)}任务已被取消",
                        }
                        break

                    # 检查客户端连接
                    if task_info.status == TaskStatus.DISCONNECTED:
                        yield {"type": "step", "type_name": "warning", "message": "客户端已断开连接"}
                        break

                    yield message

            # 任务完成
            if task_info.status == TaskStatus.RUNNING:
                task_info.status = TaskStatus.COMPLETED
                task_info.completed_at = datetime.now()
                task_info.progress = 100.0
                yield {
                    "type": "step",
                    "type_name": "success",
                    "message": f"{task_info.info.get('description', task_info.agent_type.value)}处理完成",
                }

        except asyncio.CancelledError:
            task_info.status = TaskStatus.CANCELED
            yield {
                "type": "error",
                "message": f"{task_info.info.get('description', task_info.agent_type.value)}任务被强制取消",
            }

        except Exception as e:
            task_info.status = TaskStatus.FAILED
            task_info.error_message = str(e)
            task_info.completed_at = datetime.now()
            yield {
                "type": "error",
                "message": f"{task_info.info.get('description', task_info.agent_type.value)}处理失败: {str(e)}",
            }

        finally:
            # 清理资源
            await self._cleanup_task(task_id)

            # 任务完成后通知依赖任务
            if task_info.status == TaskStatus.COMPLETED:
                await self._notify_dependents(task_id)

    async def _execute_task_with_monitoring(
        self, task_id: str, task_func: Callable, **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """执行任务并监控进度"""
        task_info = self.active_tasks[task_id]

        # 如果任务函数是异步生成器
        if asyncio.iscoroutinefunction(task_func):
            async for result in task_func(task_id, **kwargs):
                # 更新进度
                if isinstance(result, dict) and "progress" in result:
                    task_info.current_step = result.get("step", task_info.current_step)
                    task_info.progress = result.get("progress", task_info.progress)

                    # 格式化输出
                    message = f"📊 任务 {task_id[:8]}: {result.get('message', '')} "
                    message += f"[{task_info.current_step}/{task_info.total_steps}] "
                    message += f"({task_info.progress:.1f}%)"

                    yield {"type": "progress", "message": message}
                else:
                    # 简单字符串输出
                    yield {"type": "info", "message": f"📝 任务 {task_id[:8]}: {str(result)}"}
        else:
            # 同步函数，包装为异步
            try:
                result = task_func(task_id, **kwargs)
                if hasattr(result, "__iter__") and not isinstance(result, (str, bytes)):
                    for item in result:
                        yield {"type": "info", "message": f"📝 任务 {task_id[:8]}: {str(item)}"}
                        await asyncio.sleep(0.1)  # 避免阻塞
                else:
                    yield {"type": "info", "message": f"📝 任务 {task_id[:8]}: {str(result)}"}
            except Exception as e:
                yield {"type": "error", "message": f"❌ 任务执行错误: {str(e)}"}

    async def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """取消任务"""
        if task_id not in self.active_tasks:
            return {"status": "not_found", "message": "任务不存在"}

        task_info = self.active_tasks[task_id]

        if task_info.status in [TaskStatus.CANCELED, TaskStatus.COMPLETED, TaskStatus.FAILED]:
            return {"status": "already_stopped", "message": "任务已停止"}

        # 标记为取消状态
        task_info.status = TaskStatus.CANCELED
        task_info.completed_at = datetime.now()

        return {"status": "cancel_requested", "task_id": task_id, "message": "取消请求已发送"}

    async def pause_task(self, task_id: str) -> Dict[str, Any]:
        """暂停任务"""
        if task_id not in self.active_tasks:
            return {"status": "not_found", "message": "任务不存在"}

        task_info = self.active_tasks[task_id]

        if task_info.status != TaskStatus.RUNNING:
            return {"status": "invalid_status", "message": f"任务状态不正确: {task_info.status.value}"}

        task_info.status = TaskStatus.PAUSED
        return {"status": "paused", "task_id": task_id, "message": "任务已暂停"}

    async def resume_task(self, task_id: str) -> Dict[str, Any]:
        """恢复任务"""
        if task_id not in self.active_tasks:
            return {"status": "not_found", "message": "任务不存在"}

        task_info = self.active_tasks[task_id]

        if task_info.status != TaskStatus.PAUSED:
            return {"status": "invalid_status", "message": f"任务状态不正确: {task_info.status.value}"}

        task_info.status = TaskStatus.RUNNING
        return {"status": "resumed", "task_id": task_id, "message": "任务已恢复"}

    async def get_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息"""
        if task_id not in self.active_tasks:
            return None

        return self.active_tasks[task_id].to_dict()

    async def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """获取所有任务状态"""
        return {task_id: task_info.to_dict() for task_id, task_info in self.active_tasks.items()}

    async def _cleanup_task(self, task_id: str):
        """清理任务资源"""
        # 移除生成器引用
        if task_id in self.task_generators:
            del self.task_generators[task_id]

        # 可选择性保留任务信息用于历史查询
        # 或者在一定时间后清理
        pass

    async def cleanup_completed_tasks(self, max_age_hours: int = 24):
        """清理已完成的旧任务"""
        current_time = datetime.now()
        tasks_to_remove = []

        for task_id, task_info in self.active_tasks.items():
            if task_info.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELED]:
                if task_info.completed_at:
                    age = (current_time - task_info.completed_at).total_seconds() / 3600
                    if age > max_age_hours:
                        tasks_to_remove.append(task_id)

        for task_id in tasks_to_remove:
            del self.active_tasks[task_id]
            if task_id in self.task_callbacks:
                del self.task_callbacks[task_id]

    # ==================== 工作流查询 ====================

    async def get_workflow_info(self, workflow_id: str) -> Optional[WorkflowInfo]:
        """获取工作流信息"""
        return self.workflows.get(workflow_id)

    async def get_all_workflows(self) -> Dict[str, WorkflowInfo]:
        """获取所有工作流"""
        return self.workflows.copy()

    async def get_workflow_tasks(self, workflow_id: str) -> List[TaskInfo]:
        """获取工作流中的所有任务"""
        if workflow_id not in self.workflows:
            return []

        workflow = self.workflows[workflow_id]
        tasks = []
        for task_id in workflow.task_ids:
            if task_id in self.active_tasks:
                tasks.append(self.active_tasks[task_id])

        return tasks

    async def cancel_workflow(self, workflow_id: str) -> bool:
        """取消工作流"""
        if workflow_id not in self.workflows:
            return False

        workflow = self.workflows[workflow_id]
        workflow.status = WorkflowStatus.CANCELLED
        workflow.completed_at = datetime.now()

        # 取消工作流中的所有任务
        for task_id in workflow.task_ids:
            if task_id in self.active_tasks:
                await self.cancel_task(task_id)

        return True

    # ==================== 智能体状态管理 ====================

    async def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """获取智能体状态"""
        if agent_id not in self.agents:
            return None

        agent = self.agents[agent_id]
        return {
            "agent_id": agent_id,
            "agent_type": agent.agent_type.value if hasattr(agent, "agent_type") else "unknown",
            "is_busy": getattr(agent, "is_busy", False),
            "current_task": getattr(agent, "current_task_id", None),
        }

    async def get_all_agents_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有智能体状态"""
        status = {}
        for agent_id in self.agents:
            agent_status = await self.get_agent_status(agent_id)
            if agent_status:
                status[agent_id] = agent_status
        return status

    # ==================== 任务优先级管理 ====================

    async def set_task_priority(self, task_id: str, priority: int) -> bool:
        """设置任务优先级"""
        if task_id not in self.active_tasks:
            return False

        self.active_tasks[task_id].priority = priority
        return True

    async def get_tasks_by_priority(self) -> List[TaskInfo]:
        """按优先级获取任务列表"""
        tasks = list(self.active_tasks.values())
        return sorted(tasks, key=lambda x: x.priority, reverse=True)

    # ==================== 统计信息 ====================

    async def get_statistics(self) -> Dict[str, Any]:
        """获取任务管理器统计信息"""
        total_tasks = len(self.active_tasks)
        total_workflows = len(self.workflows)
        total_agents = len(self.agents)

        task_status_count = {}
        for status in TaskStatus:
            task_status_count[status.value] = sum(1 for task in self.active_tasks.values() if task.status == status)

        workflow_status_count = {}
        for status in WorkflowStatus:
            workflow_status_count[status.value] = sum(
                1 for workflow in self.workflows.values() if workflow.status == status
            )

        busy_agents = sum(1 for agent in self.agents.values() if getattr(agent, "is_busy", False))

        return {
            "total_tasks": total_tasks,
            "total_workflows": total_workflows,
            "total_agents": total_agents,
            "busy_agents": busy_agents,
            "task_status_distribution": task_status_count,
            "workflow_status_distribution": workflow_status_count,
            "dependency_count": len(self.task_dependencies),
            "timestamp": datetime.now().isoformat(),
        }

    async def _send_ai_completion_notification(
        self, task_info: TaskInfo, result: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        使用AI生成任务完成通知（流式输出）

        Args:
            task_info: 任务信息
            result: 任务执行结果

        Yields:
            Dict: 通知消息字典
        """
        try:
            # 先输出开始生成通知的消息
            # yield {
            #     "type": "step",
            #     "type_name": "info",
            #     "message": "正在生成任务完成通知..."
            # }

            # 创建通用对话智能体实例
            chat_agent = GeneralChatAgent(
                agent_id=f"completion_notifier_{task_info.task_id}",
                config={"system_prompt": COMPLETION_SYSTEM_PROMPT},
            )

            # 构造完成通知消息
            task_information = task_info.to_dict()
            # 截取result字段，避免数据过大
            if "result" in task_information and task_information["result"]:
                result_str = str(task_information["result"])
                if len(result_str) > 100:  # 限制为1000个字符
                    task_information["result"] = result_str[:100] + "...[截取]"

            completion_query = COMPLETION_PROMPT.substitute(task_info=task_information)
            # completion_query = COMPLETION_PROMPT.substitute(task_info=task_information)
            # print(completion_query)
            # 使用流式输出生成AI完成通知
            full_ai_response = ""
            async for chunk in chat_agent.analyze_intent_stream(completion_query):
                full_ai_response += chunk
                # 流式输出每个chunk
                yield {
                    "type": "step",
                    "type_name": "completion",
                    "message": chunk,
                }

            # # 输出完整的AI生成通知
            # if full_ai_response.strip():
            #     yield {
            #         "type": "step",
            #         "status": "success",
            #         "type_name": "completion",
            #         "message": full_ai_response.strip(),
            #     }
            # else:
            #     # 如果AI生成为空，使用默认消息
            #     yield {
            #         "type": "step",
            #         "type_name": "completion",
            #         "message": f"✅ {task_info.name} 任务已成功完成！"
            #     }

            # 清理临时智能体
            await chat_agent.cleanup()

        except Exception as e:
            logger.warning(f"AI完成通知生成失败: {e}，使用默认通知")
            # 如果AI通知失败，使用默认消息
            yield {"type": "step", "type_name": "completion", "message": f"✅ {task_info.name} 任务已成功完成！"}
