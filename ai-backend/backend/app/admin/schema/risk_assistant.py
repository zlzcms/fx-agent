#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, validator

from backend.common.enums import RiskType


class RiskAssistantBase(BaseModel):
    """风控助手基础模型"""

    name: str = Field(..., min_length=1, max_length=100, description="风控助手名称")
    ai_model_id: str = Field(..., description="使用的AI模型ID")
    role: str = Field(..., min_length=1, max_length=200, description="角色定义")
    risk_type: Optional[RiskType] = Field(None, description="风险类型")
    background: Optional[str] = Field(None, max_length=2000, description="背景描述")
    task_prompt: str = Field(..., min_length=1, description="任务提示词")
    variable_config: Optional[str] = Field(None, description="变量配置JSON")
    report_config: Optional[str] = Field(None, description="报告配置JSON")
    setting: Optional[Dict[str, Any]] = Field(None, description="设置配置")
    status: bool = Field(True, description="状态")

    @validator("name")
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError("风控助手名称不能为空")
        return v.strip()

    @validator("task_prompt")
    def validate_task_prompt(cls, v):
        if not v or not v.strip():
            raise ValueError("任务提示词不能为空")
        return v.strip()

    @validator("risk_type")
    def validate_risk_type(cls, v):
        if v is not None and v not in RiskType:
            raise ValueError(f"无效的风险类型: {v}")
        return v


class CreateRiskAssistantParams(RiskAssistantBase):
    """创建风控助手参数"""

    pass


class UpdateRiskAssistantParams(BaseModel):
    """更新风控助手参数"""

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="风控助手名称")
    ai_model_id: Optional[str] = Field(None, description="使用的AI模型ID")
    role: Optional[str] = Field(None, min_length=1, max_length=200, description="角色定义")
    background: Optional[str] = Field(None, max_length=2000, description="背景描述")
    task_prompt: Optional[str] = Field(None, min_length=1, description="任务提示词")
    variable_config: Optional[str] = Field(None, description="变量配置JSON")
    report_config: Optional[str] = Field(None, description="报告配置JSON")
    setting: Optional[Dict[str, Any]] = Field(None, description="设置配置")
    status: Optional[bool] = Field(None, description="状态")

    ai_analysis_count: Optional[int] = Field(None, description="AI分析次数")
    last_analysis_time: Optional[datetime] = Field(None, description="最后一次分析时间")

    @validator("name")
    def validate_name(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError("风控助手名称不能为空")
        return v.strip() if v else v

    @validator("task_prompt")
    def validate_task_prompt(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError("任务提示词不能为空")
        return v.strip() if v else v


class RiskAssistant(RiskAssistantBase):
    """风控助手响应模型"""

    id: str = Field(..., description="风控助手ID")
    created_time: str = Field(..., description="创建时间")
    updated_time: str = Field(..., description="更新时间")

    model_config = ConfigDict(from_attributes=True)


class RiskAssistantParams(BaseModel):
    """风控助手查询参数"""

    name: Optional[str] = Field(None, description="风控助手名称（模糊搜索）")
    ai_model_id: Optional[str] = Field(None, description="AI模型ID筛选")
    risk_type: Optional[str] = Field(None, description="风险类型筛选")
    status: Optional[bool] = Field(None, description="状态筛选")
    setting_key: Optional[str] = Field(None, description="设置键名筛选")
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(10, gt=0, le=200, description="每页数量")


class DeleteParams(BaseModel):
    """删除参数"""

    ids: List[str] = Field(..., min_items=1, description="要删除的ID列表")


class DeleteResponse(BaseModel):
    """删除响应"""

    deleted_count: int = Field(..., description="删除的数量")


class UpdateStatusParams(BaseModel):
    """更新状态参数"""

    status: bool = Field(..., description="状态")
