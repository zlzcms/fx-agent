#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流信息管理类
提供完整的工作流生命周期管理功能
"""

import json
import uuid

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ExecutionMode(Enum):
    """执行模式枚举"""

    SEQUENTIAL = "sequential"  # 顺序执行
    PARALLEL = "parallel"  # 并行执行
    PIPELINE = "pipeline"  # 流水线执行
    CONDITIONAL = "conditional"  # 条件执行
    LOOP = "loop"  # 循环执行


class WorkflowStatus(Enum):
    """工作流状态枚举"""

    DRAFT = "draft"  # 草稿状态
    PENDING = "pending"  # 等待执行
    RUNNING = "running"  # 执行中
    PAUSED = "paused"  # 暂停
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 执行失败
    CANCELLED = "cancelled"  # 已取消
    TIMEOUT = "timeout"  # 超时


class TaskNode:
    """任务节点类"""

    def __init__(
        self,
        task_id: str,
        name: str = None,
        dependencies: List[str] = None,
        conditions: Dict[str, Any] = None,
        retry_count: int = 0,
        timeout: int = None,
    ):
        self.task_id = task_id
        self.name = name or task_id
        self.dependencies = dependencies or []
        self.conditions = conditions or {}
        self.retry_count = retry_count
        self.max_retries = 3
        self.timeout = timeout
        self.start_time = None
        self.end_time = None
        self.result = None
        self.error = None
        self.status = WorkflowStatus.PENDING

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "dependencies": self.dependencies,
            "conditions": self.conditions,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "result": self.result,
            "error": self.error,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskNode":
        """从字典创建任务节点"""
        node = cls(
            task_id=data["task_id"],
            name=data.get("name"),
            dependencies=data.get("dependencies", []),
            conditions=data.get("conditions", {}),
            retry_count=data.get("retry_count", 0),
            timeout=data.get("timeout"),
        )
        node.max_retries = data.get("max_retries", 3)
        node.result = data.get("result")
        node.error = data.get("error")
        node.status = WorkflowStatus(data.get("status", "pending"))

        if data.get("start_time"):
            node.start_time = datetime.fromisoformat(data["start_time"])
        if data.get("end_time"):
            node.end_time = datetime.fromisoformat(data["end_time"])

        return node


@dataclass
class WorkflowMetrics:
    """工作流执行指标"""

    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    cancelled_tasks: int = 0
    total_execution_time: float = 0.0
    average_task_time: float = 0.0
    success_rate: float = 0.0

    def calculate_metrics(self, tasks: List[TaskNode]):
        """计算工作流指标"""
        self.total_tasks = len(tasks)
        self.completed_tasks = sum(1 for t in tasks if t.status == WorkflowStatus.COMPLETED)
        self.failed_tasks = sum(1 for t in tasks if t.status == WorkflowStatus.FAILED)
        self.cancelled_tasks = sum(1 for t in tasks if t.status == WorkflowStatus.CANCELLED)

        if self.total_tasks > 0:
            self.success_rate = self.completed_tasks / self.total_tasks

        # 计算执行时间
        task_times = []
        for task in tasks:
            if task.start_time and task.end_time:
                duration = (task.end_time - task.start_time).total_seconds()
                task_times.append(duration)

        if task_times:
            self.total_execution_time = sum(task_times)
            self.average_task_time = self.total_execution_time / len(task_times)


class WorkflowInfo:
    """完善的工作流信息管理类"""

    def __init__(
        self,
        workflow_id: str = None,
        name: str = None,
        description: str = None,
        execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL,
        version: str = "1.0.0",
        tags: List[str] = None,
        metadata: Dict[str, Any] = None,
    ):
        self.workflow_id = workflow_id or str(uuid.uuid4())
        self.name = name or f"Workflow_{self.workflow_id[:8]}"
        self.description = description or ""
        self.execution_mode = execution_mode
        self.version = version
        self.tags = tags or []
        self.metadata = metadata or {}

        # 状态管理
        self.status = WorkflowStatus.DRAFT
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.updated_at = datetime.now()

        # 任务管理
        self.tasks: Dict[str, TaskNode] = {}
        self.task_order: List[str] = []
        self.task_ids: List[str] = []

        # 执行配置
        self.max_parallel_tasks = 5
        self.timeout = 3600  # 1小时默认超时
        self.retry_policy = {"max_retries": 3, "retry_delay": 1.0, "exponential_backoff": True}

        # 执行状态
        self.current_step = 0
        self.progress = 0.0
        self.error_message = None
        self.execution_log: List[Dict[str, Any]] = []

        # 指标
        self.metrics = WorkflowMetrics()

        # 事件回调
        self.event_handlers = {
            "on_start": [],
            "on_complete": [],
            "on_error": [],
            "on_task_complete": [],
            "on_task_error": [],
        }

    def add_task(
        self,
        task_id: str,
        name: str = None,
        dependencies: List[str] = None,
        conditions: Dict[str, Any] = None,
        timeout: int = None,
        position: int = None,
    ) -> TaskNode:
        """添加任务到工作流"""
        if task_id in self.tasks:
            raise ValueError(f"任务 {task_id} 已存在")

        # 验证依赖任务存在
        if dependencies:
            for dep_id in dependencies:
                if dep_id not in self.tasks:
                    raise ValueError(f"依赖任务 {dep_id} 不存在")

        task_node = TaskNode(
            task_id=task_id, name=name, dependencies=dependencies, conditions=conditions, timeout=timeout
        )

        self.tasks[task_id] = task_node

        # 添加到任务顺序列表
        if position is not None:
            self.task_order.insert(position, task_id)
        else:
            self.task_order.append(task_id)

        self._update_timestamp()
        self._log_event("task_added", {"task_id": task_id, "name": name})

        return task_node

    def remove_task(self, task_id: str) -> bool:
        """移除任务"""
        if task_id not in self.tasks:
            return False

        # 检查是否有其他任务依赖此任务
        dependents = self.get_task_dependents(task_id)
        if dependents:
            raise ValueError(f"无法删除任务 {task_id}，存在依赖任务: {dependents}")

        del self.tasks[task_id]
        if task_id in self.task_order:
            self.task_order.remove(task_id)

        self._update_timestamp()
        self._log_event("task_removed", {"task_id": task_id})

        return True

    def get_task(self, task_id: str) -> Optional[TaskNode]:
        """获取任务节点"""
        return self.tasks.get(task_id)

    def get_task_dependencies(self, task_id: str) -> List[str]:
        """获取任务依赖"""
        task = self.tasks.get(task_id)
        return task.dependencies if task else []

    def get_task_dependents(self, task_id: str) -> List[str]:
        """获取依赖此任务的任务列表"""
        dependents = []
        for tid, task in self.tasks.items():
            if task_id in task.dependencies:
                dependents.append(tid)
        return dependents

    def get_ready_tasks(self) -> List[str]:
        """获取可以执行的任务（依赖已满足）"""
        ready_tasks = []
        for task_id, task in self.tasks.items():
            if task.status == WorkflowStatus.PENDING:
                # 检查所有依赖是否已完成
                deps_completed = all(
                    self.tasks[dep_id].status == WorkflowStatus.COMPLETED for dep_id in task.dependencies
                )
                if deps_completed:
                    ready_tasks.append(task_id)
        return ready_tasks

    def validate_workflow(self) -> List[str]:
        """验证工作流配置"""
        errors = []

        # 检查循环依赖
        if self._has_circular_dependency():
            errors.append("存在循环依赖")

        # 检查孤立任务
        orphaned_tasks = self._find_orphaned_tasks()
        if orphaned_tasks:
            errors.append(f"存在孤立任务: {orphaned_tasks}")

        # 检查无效依赖
        for task_id, task in self.tasks.items():
            for dep_id in task.dependencies:
                if dep_id not in self.tasks:
                    errors.append(f"任务 {task_id} 依赖不存在的任务 {dep_id}")

        return errors

    def _has_circular_dependency(self) -> bool:
        """检查是否存在循环依赖"""
        visited = set()
        rec_stack = set()

        def dfs(task_id: str) -> bool:
            if task_id in rec_stack:
                return True
            if task_id in visited:
                return False

            visited.add(task_id)
            rec_stack.add(task_id)

            task = self.tasks.get(task_id)
            if task:
                for dep_id in task.dependencies:
                    if dfs(dep_id):
                        return True

            rec_stack.remove(task_id)
            return False

        for task_id in self.tasks:
            if task_id not in visited:
                if dfs(task_id):
                    return True

        return False

    def _find_orphaned_tasks(self) -> List[str]:
        """查找孤立任务（没有依赖也不被依赖）"""
        if len(self.tasks) <= 1:
            return []

        orphaned = []
        for task_id, task in self.tasks.items():
            has_dependencies = bool(task.dependencies)
            has_dependents = bool(self.get_task_dependents(task_id))

            if not has_dependencies and not has_dependents:
                orphaned.append(task_id)

        return orphaned

    def get_execution_plan(self) -> List[List[str]]:
        """获取执行计划（按层级分组）"""
        if self.execution_mode == ExecutionMode.SEQUENTIAL:
            return [[task_id] for task_id in self.task_order]

        # 拓扑排序生成执行层级
        levels = []
        remaining_tasks = set(self.tasks.keys())

        while remaining_tasks:
            current_level = []
            for task_id in list(remaining_tasks):
                task = self.tasks[task_id]
                # 检查依赖是否都已在前面的层级中
                deps_satisfied = all(dep_id not in remaining_tasks for dep_id in task.dependencies)
                if deps_satisfied:
                    current_level.append(task_id)

            if not current_level:
                # 可能存在循环依赖
                break

            levels.append(current_level)
            remaining_tasks -= set(current_level)

        return levels

    def update_progress(self):
        """更新工作流进度"""
        if not self.tasks:
            self.progress = 0.0
            return

        completed_count = sum(1 for task in self.tasks.values() if task.status == WorkflowStatus.COMPLETED)
        self.progress = completed_count / len(self.tasks) * 100
        self._update_timestamp()

    def start_execution(self):
        """开始执行工作流"""
        self.status = WorkflowStatus.RUNNING
        self.started_at = datetime.now()
        self.current_step = 0
        self._log_event("workflow_started", {"workflow_id": self.workflow_id})

        # 触发开始事件
        for handler in self.event_handlers["on_start"]:
            try:
                handler(self)
            except Exception as e:
                self._log_event("event_handler_error", {"error": str(e)})

    def complete_execution(self, success: bool = True):
        """完成工作流执行"""
        self.status = WorkflowStatus.COMPLETED if success else WorkflowStatus.FAILED
        self.completed_at = datetime.now()
        self.progress = 100.0 if success else self.progress

        # 计算指标
        self.metrics.calculate_metrics(list(self.tasks.values()))

        self._log_event(
            "workflow_completed", {"workflow_id": self.workflow_id, "success": success, "metrics": asdict(self.metrics)}
        )

        # 触发完成事件
        event_type = "on_complete" if success else "on_error"
        for handler in self.event_handlers[event_type]:
            try:
                handler(self)
            except Exception as e:
                self._log_event("event_handler_error", {"error": str(e)})

    def pause_execution(self):
        """暂停工作流执行"""
        self.status = WorkflowStatus.PAUSED
        self._log_event("workflow_paused", {"workflow_id": self.workflow_id})

    def resume_execution(self):
        """恢复工作流执行"""
        if self.status == WorkflowStatus.PAUSED:
            self.status = WorkflowStatus.RUNNING
            self._log_event("workflow_resumed", {"workflow_id": self.workflow_id})

    def cancel_execution(self):
        """取消工作流执行"""
        self.status = WorkflowStatus.CANCELLED
        self.completed_at = datetime.now()

        # 取消所有未完成的任务
        for task in self.tasks.values():
            if task.status in [WorkflowStatus.PENDING, WorkflowStatus.RUNNING]:
                task.status = WorkflowStatus.CANCELLED

        self._log_event("workflow_cancelled", {"workflow_id": self.workflow_id})

    def add_event_handler(self, event_type: str, handler):
        """添加事件处理器"""
        if event_type in self.event_handlers:
            self.event_handlers[event_type].append(handler)

    def _update_timestamp(self):
        """更新时间戳"""
        self.updated_at = datetime.now()

    def _log_event(self, event_type: str, data: Dict[str, Any]):
        """记录事件日志"""
        log_entry = {"timestamp": datetime.now().isoformat(), "event_type": event_type, "data": data}
        self.execution_log.append(log_entry)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "execution_mode": self.execution_mode.value,
            "version": self.version,
            "tags": self.tags,
            "metadata": self.metadata,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "updated_at": self.updated_at.isoformat(),
            "tasks": {tid: task.to_dict() for tid, task in self.tasks.items()},
            "task_order": self.task_order,
            "max_parallel_tasks": self.max_parallel_tasks,
            "timeout": self.timeout,
            "retry_policy": self.retry_policy,
            "current_step": self.current_step,
            "progress": self.progress,
            "error_message": self.error_message,
            "execution_log": self.execution_log,
            "metrics": asdict(self.metrics),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowInfo":
        """从字典创建工作流实例"""
        workflow = cls(
            workflow_id=data["workflow_id"],
            name=data["name"],
            description=data.get("description", ""),
            execution_mode=ExecutionMode(data["execution_mode"]),
            version=data.get("version", "1.0.0"),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )

        # 恢复状态
        workflow.status = WorkflowStatus(data["status"])
        workflow.created_at = datetime.fromisoformat(data["created_at"])
        workflow.updated_at = datetime.fromisoformat(data["updated_at"])

        if data.get("started_at"):
            workflow.started_at = datetime.fromisoformat(data["started_at"])
        if data.get("completed_at"):
            workflow.completed_at = datetime.fromisoformat(data["completed_at"])

        # 恢复任务
        workflow.tasks = {tid: TaskNode.from_dict(task_data) for tid, task_data in data.get("tasks", {}).items()}
        workflow.task_order = data.get("task_order", [])

        # 恢复配置
        workflow.max_parallel_tasks = data.get("max_parallel_tasks", 5)
        workflow.timeout = data.get("timeout", 3600)
        workflow.retry_policy = data.get(
            "retry_policy", {"max_retries": 3, "retry_delay": 1.0, "exponential_backoff": True}
        )

        # 恢复执行状态
        workflow.current_step = data.get("current_step", 0)
        workflow.progress = data.get("progress", 0.0)
        workflow.error_message = data.get("error_message")
        workflow.execution_log = data.get("execution_log", [])

        # 恢复指标
        metrics_data = data.get("metrics", {})
        workflow.metrics = WorkflowMetrics(**metrics_data)

        return workflow

    def save_to_file(self, file_path: str):
        """保存工作流到文件"""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load_from_file(cls, file_path: str) -> "WorkflowInfo":
        """从文件加载工作流"""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def clone(self, new_name: str = None) -> "WorkflowInfo":
        """克隆工作流"""
        data = self.to_dict()
        data["workflow_id"] = str(uuid.uuid4())
        data["name"] = new_name or f"{self.name}_copy"
        data["status"] = WorkflowStatus.DRAFT.value
        data["started_at"] = None
        data["completed_at"] = None
        data["execution_log"] = []
        data["current_step"] = 0
        data["progress"] = 0.0
        data["error_message"] = None

        # 重置任务状态
        for task_data in data["tasks"].values():
            task_data["status"] = WorkflowStatus.PENDING.value
            task_data["start_time"] = None
            task_data["end_time"] = None
            task_data["result"] = None
            task_data["error"] = None
            task_data["retry_count"] = 0

        return self.from_dict(data)

    def get_summary(self) -> Dict[str, Any]:
        """获取工作流摘要信息"""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "status": self.status.value,
            "execution_mode": self.execution_mode.value,
            "task_count": len(self.tasks),
            "progress": self.progress,
            "created_at": self.created_at.isoformat(),
            "duration": self._get_duration(),
            "metrics": asdict(self.metrics),
        }

    def _get_duration(self) -> Optional[float]:
        """获取执行时长（秒）"""
        if self.started_at:
            end_time = self.completed_at or datetime.now()
            return (end_time - self.started_at).total_seconds()
        return None

    def __str__(self) -> str:
        return f"WorkflowInfo(id={self.workflow_id[:8]}, name={self.name}, status={self.status.value})"

    def __repr__(self) -> str:
        return self.__str__()
