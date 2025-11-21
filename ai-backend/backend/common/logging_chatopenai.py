#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChatOpenAI包装类，用于拦截和记录所有AI服务调用
支持 LangSmith 追踪
"""

import time

from typing import Any, Dict, List, Optional, Union

from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI

from backend.common.ai_logger import (
    ai_service_logger,
    extract_request_info,
    extract_response_info,
    get_ai_request_id,
)


class LoggingChatOpenAI(ChatOpenAI):
    """
    带日志记录的ChatOpenAI包装类
    支持 LangSmith 追踪和监控
    """

    def __init__(self, *args, **kwargs):
        from backend.common.log import logger

        # 提取 LangSmith 相关参数（必须在 super().__init__ 之前设置）
        langsmith_tags = kwargs.pop("langsmith_tags", [])
        langsmith_metadata = kwargs.pop("langsmith_metadata", {})

        # 提取模型ID（在 super().__init__ 之前先保存，因为 Pydantic 会清除未定义的属性）
        model_id = kwargs.pop("model_id", None)
        intent_name = kwargs.pop("intent_name", None)
        model_alias_name = kwargs.pop("model_alias_name", None)
        # 打印完整的 kwargs 配置信息
        logger.info(
            f"[模型信息：LoggingChatOpenAI.__init__] kwargs:intent_name={intent_name}, model_name={model_alias_name}, model={kwargs.get('model')}, model_id={model_id}, base_url={kwargs.get('base_url')}, temperature={kwargs.get('temperature')}"
        )

        super().__init__(*args, **kwargs)

        # 在 super().__init__() 之后设置自定义属性（使用 object.__setattr__ 绕过 Pydantic 的限制）
        object.__setattr__(self, "_langsmith_tags", langsmith_tags)
        object.__setattr__(self, "_langsmith_metadata", langsmith_metadata)
        object.__setattr__(self, "_service_name", "ChatOpenAI")
        object.__setattr__(self, "_model_id", model_id)
        object.__setattr__(self, "_config_info", self._extract_config_info())

    def _extract_config_info(self):
        """提取配置信息"""
        # ChatOpenAI 使用 model_name 属性而不是 model
        model_name = getattr(self, "model_name", None) or getattr(self, "model", "unknown")
        base_url = getattr(self, "openai_api_base", None) or getattr(self, "base_url", "unknown")

        return {
            "model": model_name,
            "base_url": base_url,
            "temperature": getattr(self, "temperature", 0.7),
            "max_tokens": getattr(self, "max_tokens", None),
            "timeout": getattr(self, "request_timeout", 60),
            "max_retries": getattr(self, "max_retries", 2),
        }

    def _prepare_langsmith_config(
        self,
        config: Optional[Dict[str, Any]] = None,
        run_name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        准备 LangSmith 配置

        Args:
            config: 原始配置
            run_name: 运行名称
            tags: 标签列表
            metadata: 元数据

        Returns:
            合并后的配置
        """
        # 创建或更新配置
        if config is None:
            config = {}

        # 安全地获取属性
        langsmith_tags = getattr(self, "_langsmith_tags", [])
        langsmith_metadata = getattr(self, "_langsmith_metadata", {})
        service_name = getattr(self, "_service_name", "ChatOpenAI")
        config_info = getattr(self, "_config_info", {})

        # 合并标签
        all_tags = list(langsmith_tags)
        if tags:
            all_tags.extend(tags)
        if all_tags:
            config["tags"] = all_tags

        # 合并元数据
        all_metadata = dict(langsmith_metadata)
        if metadata:
            all_metadata.update(metadata)
        # 添加模型信息到元数据
        all_metadata.update(
            {
                "model": config_info.get("model", "unknown"),
                "temperature": config_info.get("temperature", 0.7),
                "service": service_name,
            }
        )
        if all_metadata:
            config["metadata"] = all_metadata

        # 设置运行名称
        if run_name:
            config["run_name"] = run_name

        return config

    def invoke(
        self,
        messages: Union[str, List[BaseMessage], List[Dict[str, str]]],
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """
        同步调用AI服务
        支持 LangSmith 追踪
        """
        request_id = get_ai_request_id()
        start_time = time.time()

        # 标准化消息格式
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        # 提取请求信息
        request_info = extract_request_info(messages)

        # 准备 LangSmith 配置
        service_name = getattr(self, "_service_name", "ChatOpenAI")
        run_name = kwargs.pop("run_name", None) or f"{service_name}_invoke"
        tags = kwargs.pop("tags", None)
        metadata = kwargs.pop("metadata", None)
        config = self._prepare_langsmith_config(config, run_name, tags, metadata)

        # 记录请求
        # 准备额外的配置信息，排除已显式传递的参数
        config_info = getattr(self, "_config_info", {})
        extra_config = {k: v for k, v in config_info.items() if k not in ["model", "base_url"]}

        ai_service_logger.log_ai_request(
            request_id=request_id,
            service_name=service_name,
            model_name=config_info.get("model", "unknown"),
            base_url=config_info.get("base_url", "unknown"),
            request_data={
                "messages": request_info["messages"],
                "total_tokens": request_info["total_tokens"],
                "config": config,
                **kwargs,
            },
            **extra_config,
        )

        try:
            # 调用原始方法（会自动使用 LangSmith 追踪）
            response = super().invoke(messages, config, **kwargs)

            # 计算响应时间
            response_time = time.time() - start_time

            # 提取响应信息
            response_info = extract_response_info(response)

            # 记录响应
            ai_service_logger.log_ai_response(
                request_id=request_id,
                response_data=response_info,
                status_code=200,
                response_time=response_time,
            )

            return response

        except Exception as e:
            # 计算响应时间
            response_time = time.time() - start_time

            # 记录错误
            ai_service_logger.log_ai_error(
                request_id=request_id,
                error_message=str(e),
                error_type=type(e).__name__,
            )

            # 记录错误响应
            ai_service_logger.log_ai_response(
                request_id=request_id,
                response_data={"error": str(e)},
                status_code=500,
                response_time=response_time,
                error_message=str(e),
            )

            raise

    async def ainvoke(
        self,
        messages: Union[str, List[BaseMessage], List[Dict[str, str]]],
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Any:
        """
        异步调用AI服务
        支持 LangSmith 追踪
        """
        request_id = get_ai_request_id()
        start_time = time.time()

        # 标准化消息格式
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        # 提取请求信息
        request_info = extract_request_info(messages)

        # 准备 LangSmith 配置
        service_name = getattr(self, "_service_name", "ChatOpenAI")
        run_name = kwargs.pop("run_name", None) or f"{service_name}_ainvoke"
        tags = kwargs.pop("tags", None)
        metadata = kwargs.pop("metadata", None)
        config = self._prepare_langsmith_config(config, run_name, tags, metadata)

        # 记录请求
        # 准备额外的配置信息，排除已显式传递的参数
        config_info = getattr(self, "_config_info", {})
        extra_config = {k: v for k, v in config_info.items() if k not in ["model", "base_url"]}

        ai_service_logger.log_ai_request(
            request_id=request_id,
            service_name=service_name,
            model_name=config_info.get("model", "unknown"),
            base_url=config_info.get("base_url", "unknown"),
            request_data={
                "messages": request_info["messages"],
                "total_tokens": request_info["total_tokens"],
                "config": config,
                **kwargs,
            },
            **extra_config,
        )

        try:
            # 调用原始方法（会自动使用 LangSmith 追踪）
            response = await super().ainvoke(messages, config, **kwargs)

            # 计算响应时间
            response_time = time.time() - start_time

            # 提取响应信息
            response_info = extract_response_info(response)

            # 记录响应
            ai_service_logger.log_ai_response(
                request_id=request_id,
                response_data=response_info,
                status_code=200,
                response_time=response_time,
            )

            return response

        except Exception as e:
            # 计算响应时间
            response_time = time.time() - start_time

            # 记录错误
            ai_service_logger.log_ai_error(
                request_id=request_id,
                error_message=str(e),
                error_type=type(e).__name__,
            )

            # 记录错误响应
            ai_service_logger.log_ai_response(
                request_id=request_id,
                response_data={"error": str(e)},
                status_code=500,
                response_time=response_time,
                error_message=str(e),
            )

            raise

    def stream(
        self,
        messages: Union[str, List[BaseMessage], List[Dict[str, str]]],
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ):
        """
        流式调用AI服务
        支持 LangSmith 追踪
        """
        request_id = get_ai_request_id()
        start_time = time.time()

        # 标准化消息格式
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        # 提取请求信息
        request_info = extract_request_info(messages)

        # 准备 LangSmith 配置
        service_name = getattr(self, "_service_name", "ChatOpenAI")
        run_name = kwargs.pop("run_name", None) or f"{service_name}_stream"
        tags = kwargs.pop("tags", None)
        metadata = kwargs.pop("metadata", None)
        config = self._prepare_langsmith_config(config, run_name, tags, metadata)

        # 记录请求
        # 准备额外的配置信息，排除已显式传递的参数
        config_info = getattr(self, "_config_info", {})
        extra_config = {k: v for k, v in config_info.items() if k not in ["model", "base_url"]}

        ai_service_logger.log_ai_request(
            request_id=request_id,
            service_name=service_name,
            model_name=config_info.get("model", "unknown"),
            base_url=config_info.get("base_url", "unknown"),
            request_data={
                "messages": request_info["messages"],
                "total_tokens": request_info["total_tokens"],
                "config": config,
                "stream": True,
                **kwargs,
            },
            **extra_config,
        )

        try:
            # 调用原始方法（会自动使用 LangSmith 追踪）
            response_stream = super().stream(messages, config, **kwargs)

            # 包装流式响应以记录日志
            return self._wrap_stream_response(response_stream, request_id, start_time)

        except Exception as e:
            # 计算响应时间
            response_time = time.time() - start_time

            # 记录错误
            ai_service_logger.log_ai_error(
                request_id=request_id,
                error_message=str(e),
                error_type=type(e).__name__,
            )

            # 记录错误响应
            ai_service_logger.log_ai_response(
                request_id=request_id,
                response_data={"error": str(e)},
                status_code=500,
                response_time=response_time,
                error_message=str(e),
            )

            raise

    async def astream(
        self,
        messages: Union[str, List[BaseMessage], List[Dict[str, str]]],
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ):
        """
        异步流式调用AI服务
        支持 LangSmith 追踪
        直接作为异步生成器，而不是返回生成器
        """
        request_id = get_ai_request_id()
        start_time = time.time()

        # 标准化消息格式
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        # 提取请求信息
        request_info = extract_request_info(messages)

        # 准备 LangSmith 配置
        service_name = getattr(self, "_service_name", "ChatOpenAI")
        run_name = kwargs.pop("run_name", None) or f"{service_name}_astream"
        tags = kwargs.pop("tags", None)
        metadata = kwargs.pop("metadata", None)
        config = self._prepare_langsmith_config(config, run_name, tags, metadata)

        # 记录请求
        # 准备额外的配置信息，排除已显式传递的参数
        config_info = getattr(self, "_config_info", {})
        extra_config = {k: v for k, v in config_info.items() if k not in ["model", "base_url"]}

        ai_service_logger.log_ai_request(
            request_id=request_id,
            service_name=service_name,
            model_name=config_info.get("model", "unknown"),
            base_url=config_info.get("base_url", "unknown"),
            request_data={
                "messages": request_info["messages"],
                "total_tokens": request_info["total_tokens"],
                "config": config,
                "stream": True,
                **kwargs,
            },
            **extra_config,
        )

        chunks = []
        try:
            # 调用原始方法（会自动使用 LangSmith 追踪）
            async for chunk in super().astream(messages, config, **kwargs):
                chunks.append(chunk)
                yield chunk

            # 计算总响应时间
            response_time = time.time() - start_time

            # 记录流式响应
            ai_service_logger.log_ai_response(
                request_id=request_id,
                response_data={
                    "stream": True,
                    "chunk_count": len(chunks),
                    "total_chunks": len(chunks),
                },
                status_code=200,
                response_time=response_time,
            )

        except Exception as e:
            # 计算响应时间
            response_time = time.time() - start_time

            # 记录错误
            ai_service_logger.log_ai_error(
                request_id=request_id,
                error_message=str(e),
                error_type=type(e).__name__,
            )

            # 记录错误响应
            ai_service_logger.log_ai_response(
                request_id=request_id,
                response_data={"error": str(e)},
                status_code=500,
                response_time=response_time,
                error_message=str(e),
            )

            raise

    def _wrap_stream_response(self, response_stream, request_id: str, start_time: float):
        """包装同步流式响应"""
        chunks = []

        try:
            for chunk in response_stream:
                chunks.append(chunk)
                yield chunk
        finally:
            # 计算总响应时间
            response_time = time.time() - start_time

            # 记录流式响应
            ai_service_logger.log_ai_response(
                request_id=request_id,
                response_data={
                    "stream": True,
                    "chunk_count": len(chunks),
                    "total_chunks": len(chunks),
                },
                status_code=200,
                response_time=response_time,
            )

    async def _wrap_async_stream_response(self, response_stream, request_id: str, start_time: float):
        """包装异步流式响应"""
        chunks = []

        try:
            async for chunk in response_stream:
                chunks.append(chunk)
                yield chunk
        finally:
            # 计算总响应时间
            response_time = time.time() - start_time

            # 记录流式响应
            ai_service_logger.log_ai_response(
                request_id=request_id,
                response_data={
                    "stream": True,
                    "chunk_count": len(chunks),
                    "total_chunks": len(chunks),
                },
                status_code=200,
                response_time=response_time,
            )
