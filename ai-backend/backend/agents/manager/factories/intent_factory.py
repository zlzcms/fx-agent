#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
意图处理器工厂
负责创建和管理各种意图处理器
"""

import importlib

from typing import Any, Dict, Type

from backend.agents.manager.factories.base_handler import IntentHandler
from backend.common.log import logger


class IntentHandlerFactory:
    """意图处理器工厂"""

    # 动态加载的处理器缓存
    _dynamic_handlers: Dict[str, Type[IntentHandler]] = {}

    @classmethod
    def create_handler(cls, intent_type: str, agent: Any) -> IntentHandler:
        """创建对应的意图处理器"""
        try:
            handler_class = cls.get_handler(intent_type)
        except Exception as e:
            error_message = f"❌ Error loading handler for intent type {intent_type}: {str(e)}"
            logger.error(error_message)
            raise ValueError(error_message)
        return handler_class(agent)

    @classmethod
    def get_handler(cls, intent_type: str) -> Type[IntentHandler]:
        """动态加载处理器"""

        try:
            # 尝试动态导入处理器模块
            module_name = f"{intent_type.lower()}_handler"
            # 构建完整的模块路径
            full_module_path = f"backend.agents.manager.handlers.{module_name}"

            # 尝试导入模块
            module = importlib.import_module(full_module_path)

            # 构造处理器类名
            handler_class_name = f"{intent_type.capitalize()}IntentHandler"

            # 获取处理器类
            if hasattr(module, handler_class_name):
                handler_class = getattr(module, handler_class_name)
                return handler_class
            else:
                error_message = f"❌ Handler class {handler_class_name} not found in module {full_module_path}"
                logger.error(error_message)
                raise ValueError(error_message)
        except ImportError as e:
            error_message = f"❌ Failed to import handler module for intent type {intent_type}: {str(e)}"
            logger.error(error_message)
            raise ValueError(error_message)
        except Exception as e:
            error_message = f"❌ Error loading handler for intent type {intent_type}: {str(e)}"
            logger.error(error_message)
            raise ValueError(error_message)
