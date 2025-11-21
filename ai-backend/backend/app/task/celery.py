#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import os

import celery
import celery_aio_pool

from backend.app.task.model.result import OVERWRITE_CELERY_RESULT_GROUP_TABLE_NAME, OVERWRITE_CELERY_RESULT_TABLE_NAME
from backend.app.task.tasks.beat import LOCAL_BEAT_SCHEDULE
from backend.core.conf import settings
from backend.core.path_conf import BASE_PATH


def find_task_packages():
    packages = []
    task_dir = os.path.join(BASE_PATH, "app", "task", "tasks")
    for root, dirs, files in os.walk(task_dir):
        # 查找所有以tasks结尾的Python文件，包括tasks.py, payment_tasks.py等
        task_files = [f for f in files if f.endswith("tasks.py") and not f.startswith("__")]
        if task_files:
            # 获取包路径
            package_path = root.replace(str(BASE_PATH.parent) + os.path.sep, "").replace(os.path.sep, ".")
            # 为每个任务文件添加具体的模块路径
            for task_file in task_files:
                module_name = task_file[:-3]  # 去掉.py后缀
                full_module_path = f"{package_path}.{module_name}"
                packages.append(full_module_path)
    return packages


def init_celery() -> celery.Celery:
    """初始化 Celery 应用"""

    # TODO: Update this work if celery version >= 6.0.0
    # https://github.com/fastapi-practices/fastapi_best_architecture/issues/321
    # https://github.com/celery/celery/issues/7874
    celery.app.trace.build_tracer = celery_aio_pool.build_async_tracer
    celery.app.trace.reset_worker_optimizations()

    # 配置日志输出到文件
    import logging

    from backend.core.path_conf import BASE_PATH

    # 确保 logs 目录存在
    log_dir = os.path.join(BASE_PATH.parent, "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 配置 Celery 日志处理器
    celery_logger = logging.getLogger("celery")
    celery_logger.setLevel(logging.INFO)

    # 文件处理器 - 应用日志
    app_handler = logging.FileHandler(os.path.join(log_dir, "celery_app.log"))
    app_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    app_handler.setFormatter(formatter)
    celery_logger.addHandler(app_handler)

    # 配置 Worker 专用日志处理器
    worker_logger = logging.getLogger("celery.worker")
    worker_handler = logging.FileHandler(os.path.join(log_dir, "celery_worker.log"))
    worker_handler.setLevel(logging.INFO)
    worker_handler.setFormatter(formatter)
    worker_logger.addHandler(worker_handler)

    # 配置任务执行日志
    task_logger = logging.getLogger("celery.task")
    task_handler = logging.FileHandler(os.path.join(log_dir, "celery_task.log"))
    task_handler.setLevel(logging.INFO)
    task_handler.setFormatter(formatter)
    task_logger.addHandler(task_handler)

    # 构建Redis URL
    if settings.REDIS_PASSWORD:
        redis_url = f"redis://:{settings.REDIS_PASSWORD}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.CELERY_BROKER_REDIS_DATABASE}"
    else:
        redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.CELERY_BROKER_REDIS_DATABASE}"

    app = celery.Celery(
        "fba_celery",
        broker=redis_url,
        # if settings.CELERY_BROKER == "redis"
        # else f"amqp://{settings.CELERY_RABBITMQ_USERNAME}:{settings.CELERY_RABBITMQ_PASSWORD}@{settings.CELERY_RABBITMQ_HOST}:{settings.CELERY_RABBITMQ_PORT}",
        broker_connection_retry_on_startup=True,
        broker_transport_options={
            "visibility_timeout": 3600,  # 消息可见性超时时间
            "fanout_prefix": True,
            "fanout_patterns": True,
            "retry_on_timeout": True,
            "health_check_interval": 30,  # 健康检查间隔
            "socket_keepalive": True,  # 保持连接活跃
            "socket_keepalive_options": {},
            "socket_connect_timeout": 10,  # 增加连接超时时间
            "socket_timeout": 10,  # 增加Socket超时时间
        },
        backend=f"db+{settings.DATABASE_TYPE}+{'pymysql' if settings.DATABASE_TYPE == 'mysql' else 'psycopg2'}"
        f"://{settings.DATABASE_USER}:{settings.DATABASE_PASSWORD}@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.DATABASE_SCHEMA}",
        database_engine_options={"echo": settings.DATABASE_ECHO},
        database_table_names={
            "task": OVERWRITE_CELERY_RESULT_TABLE_NAME,
            "group": OVERWRITE_CELERY_RESULT_GROUP_TABLE_NAME,
        },
        result_extended=True,
        result_expires=None,  # 不自动清理任务结果，保留历史记录
        task_reject_on_worker_lost=True,  # 工作进程丢失时拒绝任务
        task_acks_late=True,  # 任务完成后才确认，确保任务不丢失
        worker_prefetch_multiplier=1,  # 降低预取倍数，避免任务堆积
        worker_max_tasks_per_child=1000,  # 每个worker子进程处理的最大任务数
        worker_disable_rate_limits=False,  # 启用速率限制
        task_compression="gzip",  # 任务压缩
        result_compression="gzip",  # 结果压缩
        worker_send_task_events=True,  # 启用任务事件
        task_send_sent_event=True,  # 启用任务发送事件
        worker_hijack_root_logger=False,  # 不劫持根日志记录器
        worker_log_color=False,  # 禁用日志颜色
        worker_pool="gevent",  # 使用gevent pool，与supervisor配置保持一致
        worker_concurrency=100,  # 设置并发数，与supervisor配置保持一致
        # beat_sync_every=1,  # 保存任务状态周期，默认 3 * 60 秒
        beat_schedule=LOCAL_BEAT_SCHEDULE,
        beat_scheduler="backend.app.task.utils.schedulers:DatabaseScheduler",
        task_cls="backend.app.task.tasks.base:TaskBase",
        task_track_started=True,
        enable_utc=False,
        timezone=settings.DATETIME_TIMEZONE,
    )

    return app


celery_app: celery.Celery = init_celery()


# 设置 Celery 专用的日志配置
def setup_celery_logging():
    """为 Celery 设置专用的日志配置"""
    import logging

    # 确保 Celery 使用自己的日志处理器，但允许部分传播用于调试
    logging.getLogger("celery").propagate = False
    logging.getLogger("celery.task").propagate = True  # 允许任务日志传播到worker日志
    logging.getLogger("celery.worker").propagate = True  # 允许worker日志传播

    # 设置其他相关日志记录器的传播
    for logger_name in ["amqp", "kombu", "vine", "redis"]:
        logging.getLogger(logger_name).propagate = False


# 设置日志
setup_celery_logging()

# 记录初始化信息
logger = logging.getLogger("celery")
logger.info("Celery application initialized successfully")
logger.info(f"Broker URL: {celery_app.conf.broker_url}")
logger.info(f"Result Backend: {celery_app.conf.result_backend}")

# 延迟自动发现任务，避免循环导入
packages = find_task_packages()
logger.info(f"Discovered task packages: {packages}")
celery_app.autodiscover_tasks(packages, force=True)
