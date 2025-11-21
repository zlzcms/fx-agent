#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from enum import Enum
from enum import IntEnum as SourceIntEnum
from typing import Any, Type, TypeVar

T = TypeVar("T", bound=Enum)


class _EnumBase:
    """枚举基类，提供通用方法"""

    @classmethod
    def get_member_keys(cls: Type[T]) -> list[str]:
        """获取枚举成员名称列表"""
        return [name for name in cls.__members__.keys()]

    @classmethod
    def get_member_values(cls: Type[T]) -> list:
        """获取枚举成员值列表"""
        return [item.value for item in cls.__members__.values()]

    @classmethod
    def get_member_dict(cls: Type[T]) -> dict[str, Any]:
        """获取枚举成员字典"""
        return {name: item.value for name, item in cls.__members__.items()}


class IntEnum(_EnumBase, SourceIntEnum):
    """整型枚举基类"""

    pass


class StrEnum(_EnumBase, str, Enum):
    """字符串枚举基类"""

    pass


class MenuType(IntEnum):
    """菜单类型"""

    directory = 0
    menu = 1
    button = 2
    embedded = 3
    link = 4


class RoleDataRuleOperatorType(IntEnum):
    """数据规则运算符"""

    AND = 0
    OR = 1


class RoleDataRuleExpressionType(IntEnum):
    """数据规则表达式"""

    eq = 0  # ==
    ne = 1  # !=
    gt = 2  # >
    ge = 3  # >=
    lt = 4  # <
    le = 5  # <=
    in_ = 6
    not_in = 7


class MethodType(StrEnum):
    """HTTP 请求方法"""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    OPTIONS = "OPTIONS"


class LoginLogStatusType(IntEnum):
    """登录日志状态"""

    fail = 0
    success = 1


class BuildTreeType(StrEnum):
    """构建树形结构类型"""

    traversal = "traversal"
    recursive = "recursive"


class OperaLogCipherType(IntEnum):
    """操作日志加密类型"""

    aes = 0
    md5 = 1
    itsdangerous = 2
    plan = 3


class StatusType(IntEnum):
    """状态类型"""

    disable = 0
    enable = 1


class UserSocialType(StrEnum):
    """用户社交类型"""

    github = "GitHub"
    google = "Google"
    linux_do = "LinuxDo"


class FileType(StrEnum):
    """文件类型"""

    image = "image"
    video = "video"


class PluginType(StrEnum):
    """插件类型"""

    zip = "zip"
    git = "git"


class UserPermissionType(StrEnum):
    """用户权限类型"""

    superuser = "superuser"
    staff = "staff"
    status = "status"
    multi_login = "multi_login"


class DataBaseType(StrEnum):
    """数据库类型"""

    mysql = "mysql"
    postgresql = "postgresql"


class PrimaryKeyType(StrEnum):
    """主键类型"""

    autoincrement = "autoincrement"
    snowflake = "snowflake"


class TrainingLogType(StrEnum):
    """训练日志类型"""

    ai_assistant = "ai_assistant"
    risk_control_assistant = "risk_control_assistant"


class AnalysisType(StrEnum):
    """分析类型"""

    risk = "risk"
    general = "general"
    comprehensive = "comprehensive"
    error = "error"
    exception = "exception"
    aggregated_analysis = "aggregated_analysis"
    final_report = "final_report"
    structured_data_analysis = "structured_data_analysis"
    structured_data_batch_analysis = "structured_data_batch_analysis"
    unknown = "unknown"


class DataTimeRangeType(StrEnum):
    """数据时间范围类型枚举"""

    DAY = "day"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"

    @classmethod
    def get_all_types(cls) -> list[dict]:
        """获取所有时间范围类型的列表"""
        return [
            {"value": cls.DAY, "label": "日"},
            {"value": cls.MONTH, "label": "月"},
            {"value": cls.QUARTER, "label": "季度"},
            {"value": cls.YEAR, "label": "年"},
        ]


class ModelTypeEnum(StrEnum):
    """模型类型枚举"""

    DEEPSEEK = "DeepSeek"
    OPENAI = "OpenAI"
    GOOGLE = "Google"
    BAIDU = "Baidu"
    ALIBABA = "Alibaba"
    HUOSHAN = "HuoShan"
    ANTHROPIC = "Anthropic"
    OTHER = "Other"


class SubscriptionType(StrEnum):
    """订阅类型枚举"""

    CLIENT = "client"  # 客户端
    SERVER = "server"  # 服务端

    @classmethod
    def get_display_name(cls, subscription_type: str) -> str:
        """获取订阅类型的显示名称"""
        display_names = {
            cls.CLIENT: "客户端",
            cls.SERVER: "服务端",
        }
        return display_names.get(subscription_type, subscription_type)

    @classmethod
    def get_all_types(cls) -> list[dict]:
        """获取所有订阅类型的列表"""
        return [
            {"value": cls.CLIENT, "label": "客户端"},
            {"value": cls.SERVER, "label": "服务端"},
        ]

    @classmethod
    def get_values(cls) -> list[str]:
        """获取所有枚举值"""
        return [cls.CLIENT, cls.SERVER]


class RiskType(StrEnum):
    """风控类型枚举"""

    ALL_EMPLOYEE = "all_employee"  # 客户风控，包含全部用户
    AGENT_USER = "agent_user"  # 代理商风控
    CRM_USER = "crm_user"  # 员工风控，特定用户
    PAYMENT = "payment"  # 出金风控

    @classmethod
    def get_display_name(cls, risk_type: str) -> str:
        """获取风控类型的显示名称"""
        display_names = {
            cls.ALL_EMPLOYEE: "客户风控",
            cls.AGENT_USER: "代理商风控",
            cls.CRM_USER: "员工风控",
            cls.PAYMENT: "出金风控",
        }
        return display_names.get(risk_type, risk_type)

    @classmethod
    def get_all_types(cls) -> list[dict]:
        """获取所有风控类型的列表"""
        return [
            {"value": cls.ALL_EMPLOYEE, "label": "客户风控"},
            {"value": cls.AGENT_USER, "label": "代理商风控"},
            {"value": cls.CRM_USER, "label": "员工风控"},
            {"value": cls.PAYMENT, "label": "出金风控"},
        ]

    @classmethod
    def get_tag_category_name(cls, risk_type: str) -> str:
        """根据风控类型获取对应的标签分类名称"""
        category_mapping = {
            cls.ALL_EMPLOYEE: "客户风控",
            cls.CRM_USER: "员工风控",
            cls.AGENT_USER: "代理商风控",
            cls.PAYMENT: "出金风控",
        }
        return category_mapping.get(risk_type, "客户风控")


class RiskAnalysisType(StrEnum):
    """风控分析类型枚举"""

    STOCK = "STOCK"  # 存量分析
    INCREMENTAL = "INCREMENTAL"  # 增量分析
    TRIGGERED = "TRIGGERED"  # 触发式分析

    @classmethod
    def get_display_name(cls, analysis_type: str) -> str:
        """获取分析类型的显示名称"""
        display_names = {
            cls.STOCK: "存量分析",
            cls.INCREMENTAL: "增量分析",
            cls.TRIGGERED: "触发式分析",
        }
        return display_names.get(analysis_type, analysis_type)

    @classmethod
    def get_all_types(cls) -> list[dict]:
        """获取所有分析类型的列表"""
        return [
            {"value": cls.STOCK, "label": "存量分析"},
            {"value": cls.INCREMENTAL, "label": "增量分析"},
            {"value": cls.TRIGGERED, "label": "触发式分析"},
        ]


class TriggerSource(StrEnum):
    """触发源枚举"""

    NEW_REGISTER = "new_register"  # 新注册
    NEW_LOGIN = "new_login"  # 新登录
    NEW_TRANSFER = "new_transfer"  # 新转账
    NEW_OPERATION = "new_operation"  # 新操作
    NEW_MT4_TRADE = "new_mt4_trade"  # MT4新交易
    NEW_MT5_TRADE = "new_mt5_trade"  # MT5新交易

    @classmethod
    def get_display_name(cls, trigger_source: str) -> str:
        """获取触发源的显示名称"""
        display_names = {
            cls.NEW_REGISTER: "新注册",
            cls.NEW_LOGIN: "新登录",
            cls.NEW_TRANSFER: "新转账",
            cls.NEW_OPERATION: "新操作",
            cls.NEW_MT4_TRADE: "MT4新交易",
            cls.NEW_MT5_TRADE: "MT5新交易",
        }
        return display_names.get(trigger_source, trigger_source)

    @classmethod
    def get_all_sources(cls) -> list[dict]:
        """获取所有触发源的列表"""
        return [
            {"value": cls.NEW_REGISTER, "label": "新注册"},
            {"value": cls.NEW_LOGIN, "label": "新登录"},
            {"value": cls.NEW_TRANSFER, "label": "新转账"},
            {"value": cls.NEW_OPERATION, "label": "新操作"},
            {"value": cls.NEW_MT4_TRADE, "label": "MT4新交易"},
            {"value": cls.NEW_MT5_TRADE, "label": "MT5新交易"},
        ]
