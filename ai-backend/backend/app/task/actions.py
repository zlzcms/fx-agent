#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket 任务 Worker 状态事件处理
"""

from datetime import datetime

from backend.common.log import log
from backend.common.socketio.server import sio


async def check_worker_status():
    """检查celery worker的状态"""
    try:
        # 优先使用 Celery inspect 检查状态
        from backend.app.task.celery import celery_app

        inspect = celery_app.control.inspect()

        # 获取基础统计信息
        stats = inspect.stats()
        active_tasks = inspect.active()
        registered_tasks = inspect.registered()

        if stats and len(stats) > 0:
            # 解析第一个worker的详细信息
            worker_name = list(stats.keys())[0]
            worker_stats = stats[worker_name]
            worker_active = active_tasks.get(worker_name, []) if active_tasks else []
            worker_registered = registered_tasks.get(worker_name, []) if registered_tasks else []

            return {
                "status": "running",
                "worker_name": worker_name,
                "active_tasks": len(worker_active),
                "registered_tasks": len(worker_registered),
                "total_processed": worker_stats.get("total", {}),
                "pool_info": {
                    "pool": worker_stats.get("pool", {}).get("implementation", "unknown"),
                    "max_concurrency": worker_stats.get("pool", {}).get("max-concurrency", 0),
                    "processes": worker_stats.get("pool", {}).get("processes", []),
                },
                "broker_info": {
                    "transport": worker_stats.get("broker", {}).get("transport", "unknown"),
                    "hostname": worker_stats.get("broker", {}).get("hostname", "unknown"),
                },
                "rusage": worker_stats.get("rusage", {}),
                "clock": worker_stats.get("clock", 0),
                "timestamp": datetime.now().isoformat(),
            }

        return {"status": "stopped", "timestamp": datetime.now().isoformat()}

    except Exception as e:
        log.error(f"Error checking worker status: {str(e)}")
        return {"status": "error", "message": str(e), "timestamp": datetime.now().isoformat()}


@sio.event
async def task_worker_status(sid, data):
    """任务 Worker 状态事件"""
    try:
        worker_status = await check_worker_status()
        await sio.emit("task_worker_status", worker_status, room=sid)
    except Exception as e:
        log.error(f"Worker status error for {sid}: {str(e)}")
        await sio.emit("task_worker_status", {"status": "error", "message": str(e)}, room=sid)
