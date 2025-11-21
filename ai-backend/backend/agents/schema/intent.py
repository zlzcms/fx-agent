from typing import Any, Dict, Optional


class IntentAnalysisResult:
    """意图分析结果类"""

    def __init__(self, query_type: Optional[str] = None, parameters: Dict[str, Any] = None, confidence: float = 0.0):
        self.query_type = query_type
        self.parameters = parameters or {}
        self.confidence = confidence

    def to_dict(self):
        """将结果转换为字典"""
        return {"query_type": self.query_type, "parameters": self.parameters, "confidence": self.confidence}

    def __repr__(self):
        return f"IntentAnalysisResult(query_type={self.query_type}, parameters={self.parameters}, confidence={self.confidence})"
