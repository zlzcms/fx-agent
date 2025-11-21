from typing import Any

from pydantic import BaseModel, Field


class AnalyzeMessagesResult(BaseModel):
    """分析消息结果类"""

    result: Any = Field(..., description="分析消息结果")
    is_should_reduce_data: bool = Field(..., description="是否需要缩减数据")
    data: Any = Field(..., description="数据")
    property_prompt: str = Field(..., description="属性提示词")


class PropertyAnalysisResult(BaseModel):
    """属性分析结果类"""

    property_analysis: Any = Field(..., description="属性分析结果")
    recommendations: Any = Field(..., description="优化建议")
    confidence: float = Field(..., description="置信度")
    metrics: Any = Field(..., description="关键性能指标的数值化结果")
    risk_score: float = Field(..., description="风险评分")
    risk_tags: Any = Field(..., description="风险标签")
