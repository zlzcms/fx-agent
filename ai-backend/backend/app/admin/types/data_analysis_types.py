#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据分析服务相关的类型定义
"""

from typing import Any, Dict, List, Literal, Optional, TypedDict, Union

from backend.common.enums import AnalysisType, RiskType, TrainingLogType


class TimeRange(TypedDict, total=False):
    """时间范围类型定义"""

    data_start_date: Optional[str]
    data_end_date: Optional[str]


class DataSourceConfig(TypedDict):
    """数据源配置类型定义"""

    user_id: List[str]
    range_time: TimeRange


class QueryCondition(TypedDict, total=False):
    """查询条件类型定义"""

    data_time_range_type: Optional[str]
    data_time_value: Optional[int]
    fixed_end_time: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]


class SqlData(TypedDict, total=False):
    """SQL数据配置类型定义"""

    data_sources: Optional[List[str]]
    query_condition: Optional[QueryCondition]


class BasicInfo(TypedDict, total=False):
    """基础信息类型定义"""

    ai_model_id: Optional[str]
    assistant_id: Optional[str]
    name: Optional[str]
    description: Optional[str]
    background: Optional[str]
    model_definition: Optional[str]
    output_format_table: Optional[Dict[str, Any]]
    output_format_document: Optional[str]
    analysis_type: Optional[AnalysisType]
    risk_type: Optional[RiskType]
    training_type: Optional[TrainingLogType]
    model: Optional[Dict[str, Any]]


class UserDataResult(TypedDict):
    """用户数据结果类型定义"""

    success: bool
    message: str
    data: Optional[Dict[str, Any]]


class AnalysisResult(TypedDict, total=False):
    """分析结果类型定义"""

    status: Literal["accepted", "rejected"]
    message: str
    data: Optional["DataAnalyzeAgentResult"]  # DataAnalyzeAgent.result 的详细结构
    confidence: Optional[float]
    analytical_report: Optional[str]
    property_analysis: Optional[Dict[str, Any]]


class RiskTagTemplate(TypedDict):
    """风险标签模板类型定义"""

    id: str
    name: str
    description: str


class AnalysisPrompt(TypedDict, total=False):
    """分析提示类型定义"""

    role_prompt_template: str
    property_analysis_format: Union[Dict[str, Any], str]
    analytical_report_format: str
    risk_tags_template: Optional[List[RiskTagTemplate]]
    risk_tags: Optional[List[str]]


class ModelConfig(TypedDict, total=False):
    """模型配置类型定义"""

    id: Optional[str]
    name: Optional[str]
    api_key: Optional[str]
    base_url: Optional[str]
    model_name: Optional[str]
    temperature: Optional[float]


class TrainingLogResult(TypedDict):
    """训练日志结果类型定义"""

    success: bool
    message: str


class ProcessAnalysisResult(TypedDict, total=False):
    """处理分析结果类型定义"""

    assistant_id: str
    model_id: str
    member_ids: List[Any]
    sql_data: Optional[str]
    prompt_data: str
    input_prompt: str
    report_status: bool
    report_score: float
    report_result: str
    report_table: str
    report_document: str
    ai_response: Any
    id: Optional[str]


class SaveTrainingLogParams(TypedDict, total=False):
    """保存训练日志参数类型定义"""

    assistant_id: str
    model_id: str
    model_name: str
    log_type: TrainingLogType
    data: Dict[str, Any]
    ai_response: Optional[Dict[str, Any]]
    success: bool
    prompt: str
    basic_info: Optional[Dict[str, Any]]


class BuildBasicInfoParams(TypedDict, total=False):
    """构建基础信息参数类型定义"""

    assistant_id: str
    ai_model_id: str
    name: str
    description: Optional[str]
    background: Optional[str]
    model_definition: Optional[str]
    output_format_table: Optional[Dict[str, Any]]
    output_format_document: Optional[str]
    analysis_type: AnalysisType
    risk_type: Optional[RiskType]
    training_type: Optional[TrainingLogType]


class UsersInfo(TypedDict, total=False):
    """用户信息类型定义"""

    data: Optional[Dict[str, Any]]
    success: Optional[bool]
    message: Optional[str]


class AIDataAnalysisResult(TypedDict, total=False):
    """AI数据分析结果的数据结构"""

    analytical_report: str
    property_analysis: List[Dict[str, Any]]
    recommendations: List[str]
    confidence: float
    metrics: Dict[str, Any]
    risk_score: int
    risk_tags: List[str]
    description: Optional[str]  # 风险描述，用于外部系统展示


class DataAnalyzeAgentResult(TypedDict):
    """DataAnalyzeAgent.result 的数据结构"""

    analyze_data: str
    prompt: str
    output: str
    data: AIDataAnalysisResult
    response: Dict[str, Any]


class AnalysisServiceResult(TypedDict):
    """data_analysis_service.analyze_user_data 返回结果的数据结构"""

    status: str
    message: str
    data: DataAnalyzeAgentResult


class RiskReportLogData(TypedDict):
    """_build_risk_report_log_for_db 返回的数据结构"""

    assistant_id: str
    model_id: Optional[str]
    risk_type: Optional[RiskType]
    input_prompt: str
    member_name: str
    member_id: int
    report_score: float
    score: int
    report_tags: List[str]
    report_document: str
    report_table: List[Dict[str, Any]]
    handle_suggestion: str
    description: Optional[str]
    report_result: str
    analysis_type: str
    trigger_sources: Optional[str]
    ai_response: Dict[str, Any]
    detection_window_info: Optional[Dict[str, Any]]
    sql_data: SqlData
    prompt_data: Dict[str, Any]
