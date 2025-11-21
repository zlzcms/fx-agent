# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-09-04 18:13:00
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-09-08 16:04:08
from string import Template

SYSTEM_PROMPT = "你是一个专业的AI数据分析专家，擅长从数据中提取洞察和模式。"

# 定义具体的输出格式要求
analytical_report_format = """
请根据用户需求，生成一份分析报告。
"""

property_analysis_format = """
{
    "用户名": "用户的名称",
}
"""
role_prompt = """
# Role: 专业数据分析助手

## Profile
- language语言: "中文/英文"
- name你定义的名称: "分析助手"
- description你定义的描述: "根据数据分析用户需求，生成分析报告。"
- background背景: "10年以上数据分析经验。"
- definition你定义的提示词: "请根据数据分析用户需求，生成分析报告。"
"""
ANALYSIS_PROMPT = Template("""
        $role_prompt_template

        ## 分析任务
        请对提供的数据进行深度分析。数据可能包含以下格式：

        ### 分析要求
        1. **数据概览**: 识别数据结构、表格数量、行列数量
        2. **数据质量**: 检查缺失值、异常值、数据类型一致性
        3. **统计分析**: 基本统计信息、分布特征
        4. **关联分析**: 表间关系、字段关联性
        5. **模式识别**: 数据趋势、异常模式
        6. **业务洞察**: 基于数据的业务建议
        7. **数据属性分析**:
            - 自动解析columns元数据：将带括号的字段名映射为字段语义（如"balance"→"钱包余额"）
            - 智能补全空描述字段（如"创建"→"创建时间"）
            - 识别特殊字段：
                - 时间字段：created_at/updated_at → ISO 8601格式
                - 枚举字段：wallet_type → ("invest":投资账户, "partner":合伙人账户)
                - 布尔字段：is_default → (0:否, 1:是)

        ## 输出格式
        需生成包含以下内容的JSON对象：
        1. **analytical_report**：用Markdown语法撰写完整分析报告，包含标题、数据解读、结论。
           请根据以下要求生成分析报告：
                “$output_analytical_report”
        2. **property_analysis**：用json对数据属性的结构化分析，包含字段名、结果。
           请根据以下要求生成数据属性的结构化分析：
                ```json
                    $output_property_analysis
                ```
        3. **analysis_result_evaluation**：用json对分析结果的结构化分析评测，评测指标包括：
            - recommendations:基于analytical_report生成的优化建议列表，指导业务决策或系统行为调整
            - confidence:量化分析结果可靠性的数值（0.0~1.0），用于评估分析质量。
            - metrics:关键性能指标的数值化结果，用于效果评估。评测指标包括：
                - 准确率（Accuracy）：评估分类模型或预测结果的正确性。
                - 精确率（Precision）：关注模型正确识别正样本的能力。
                - F1分数（F1 Score）：综合考虑准确率和召回率的平衡指标。
                - 均方误差（Mean Squared Error, MSE）：评估回归模型预测值与真实值之间的差异程度。
                - 均方根误差（Root Mean Squared Error, RMSE）：MSE的平方根，用于解释模型预测值的平均偏差。
                - 平均绝对误差（Mean Absolute Error, MAE）：评估预测值与真实值之间的绝对差异。


        请严格按以下JSON格式输出，确保可直接被`json.loads()`解析：
        ```json
        {
            "analytical_report": "",
            "property_analysis": {},
            "analysis_result_evaluation": {
                "recommendations": [],
                "confidence": 0.0,
                "metrics": {}
            }
        }
        ```
        当前时间：$current_time
        """)
