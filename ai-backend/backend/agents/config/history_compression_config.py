# -*- coding: utf-8 -*-
"""
历史对话压缩配置

这个文件包含了历史对话压缩功能的各种配置选项和场景化配置。
"""

from typing import Any, Dict


class HistoryCompressionConfig:
    """历史对话压缩配置类"""

    # 默认配置
    DEFAULT = {
        "enable_history_compression": True,  # 是否启用压缩
        "compression_min_rounds": 3,  # 最小压缩轮数（3轮 = 6条消息）
    }

    # 激进压缩配置（适用于长对话场景，更早触发压缩）
    AGGRESSIVE = {
        "enable_history_compression": True,
        "compression_min_rounds": 2,  # 2轮就开始压缩
    }

    # 保守压缩配置（适用于短对话场景，较晚触发压缩）
    CONSERVATIVE = {
        "enable_history_compression": True,
        "compression_min_rounds": 5,  # 5轮才开始压缩
    }

    # 禁用压缩配置（适用于调试或需要完整历史的场景）
    DISABLED = {
        "enable_history_compression": False,
        "compression_min_rounds": 999,  # 设置很大的值，实际上不会触发
    }

    # 场景化配置
    SCENARIOS = {
        # 意图识别场景
        "intent_recognition": {
            "enable_history_compression": True,
            "compression_min_rounds": 3,
            "description": "意图识别场景，平衡压缩比和信息保留",
        },
        # 参数提取场景
        "parameter_extraction": {
            "enable_history_compression": True,
            "compression_min_rounds": 4,
            "description": "参数提取场景，保守压缩以保留更多细节",
        },
        # 报告生成场景
        "report_generation": {
            "enable_history_compression": True,
            "compression_min_rounds": 2,
            "description": "报告生成场景，激进压缩以减少token消耗",
        },
        # 通用对话场景
        "general_chat": {
            "enable_history_compression": False,
            "compression_min_rounds": 999,
            "description": "通用对话场景，保留完整对话历史以保持连贯性",
        },
        # 数据查询场景
        "data_query": {
            "enable_history_compression": True,
            "compression_min_rounds": 3,
            "description": "数据查询场景，标准压缩配置",
        },
        # 开发调试场景
        "development": {
            "enable_history_compression": False,
            "compression_min_rounds": 999,
            "description": "开发调试场景，禁用压缩以便于调试",
        },
    }

    @staticmethod
    def get_config(scenario: str = "default") -> Dict[str, Any]:
        """
        获取指定场景的配置

        Args:
            scenario: 场景名称，可选值:
                - "default": 默认配置
                - "aggressive": 激进压缩
                - "conservative": 保守压缩
                - "disabled": 禁用压缩
                - "intent_recognition": 意图识别
                - "parameter_extraction": 参数提取
                - "report_generation": 报告生成
                - "general_chat": 通用对话
                - "data_query": 数据查询
                - "development": 开发调试

        Returns:
            配置字典
        """
        scenario_lower = scenario.lower()

        if scenario_lower == "default":
            return HistoryCompressionConfig.DEFAULT.copy()
        elif scenario_lower == "aggressive":
            return HistoryCompressionConfig.AGGRESSIVE.copy()
        elif scenario_lower == "conservative":
            return HistoryCompressionConfig.CONSERVATIVE.copy()
        elif scenario_lower == "disabled":
            return HistoryCompressionConfig.DISABLED.copy()
        elif scenario_lower in HistoryCompressionConfig.SCENARIOS:
            config = HistoryCompressionConfig.SCENARIOS[scenario_lower].copy()
            config.pop("description", None)  # 移除描述字段
            return config
        else:
            # 未知场景，返回默认配置
            return HistoryCompressionConfig.DEFAULT.copy()

    @staticmethod
    def get_scenario_description(scenario: str) -> str:
        """
        获取场景描述

        Args:
            scenario: 场景名称

        Returns:
            场景描述字符串
        """
        scenario_lower = scenario.lower()
        if scenario_lower in HistoryCompressionConfig.SCENARIOS:
            return HistoryCompressionConfig.SCENARIOS[scenario_lower].get("description", "")
        return ""

    @staticmethod
    def list_scenarios() -> Dict[str, str]:
        """
        列出所有可用的场景及其描述

        Returns:
            场景名称到描述的映射字典
        """
        scenarios = {
            "default": "默认配置，适用于大多数场景",
            "aggressive": "激进压缩配置，适用于长对话场景",
            "conservative": "保守压缩配置，适用于短对话场景",
            "disabled": "禁用压缩配置，适用于调试或需要完整历史的场景",
        }

        for name, config in HistoryCompressionConfig.SCENARIOS.items():
            scenarios[name] = config.get("description", "")

        return scenarios


# 使用示例
if __name__ == "__main__":
    print("=" * 60)
    print("历史对话压缩配置示例")
    print("=" * 60)

    # 示例1: 获取默认配置
    print("\n1. 默认配置:")
    config = HistoryCompressionConfig.get_config("default")
    print(f"   {config}")

    # 示例2: 获取意图识别场景配置
    print("\n2. 意图识别场景配置:")
    config = HistoryCompressionConfig.get_config("intent_recognition")
    print(f"   {config}")
    print(f"   描述: {HistoryCompressionConfig.get_scenario_description('intent_recognition')}")

    # 示例3: 获取激进压缩配置
    print("\n3. 激进压缩配置:")
    config = HistoryCompressionConfig.get_config("aggressive")
    print(f"   {config}")

    # 示例4: 列出所有场景
    print("\n4. 所有可用场景:")
    scenarios = HistoryCompressionConfig.list_scenarios()
    for name, description in scenarios.items():
        print(f"   - {name}: {description}")

    # 示例5: 在智能体中使用
    print("\n5. 在智能体中使用配置:")
    print("   from backend.agents.config.history_compression_config import HistoryCompressionConfig")
    print("   ")
    print("   # 获取意图识别场景的配置")
    print("   config = HistoryCompressionConfig.get_config('intent_recognition')")
    print("   ")
    print("   # 使用配置执行智能体")
    print("   async for result in agent.execute(")
    print("       user_query=query,")
    print("       conversation_history=history,")
    print("       **config  # 展开配置字典")
    print("   ):")
    print("       print(result)")

    print("\n" + "=" * 60)
