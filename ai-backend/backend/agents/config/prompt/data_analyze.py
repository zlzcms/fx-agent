DEFAULT_PROMPT_TEMPLATE = (
    """你是一个{role_prompt_template}，请根据用户输入以及提供的数据，给出准确的结果，切勿凭空编造。"""
)
DEFAULT_OUTPUT_ANALYTICAL_REPORT = ""
DEFAULT_OUTPUT_PROPERTY_ANALYSIS = "空"
DEFAULT_RISK_TAGS_TEMPLATE = "空"


PROPERTY_ANALYSIS_PROMPT = """
{prompt_template}

1. 查询条件如下：
```
{data_request}
```

2. 查询数据结果markdown如下：
```
{analysis_data}
```

3. 输出参数
  3.1 **property_analysis**提取value值:
      ```
        {output_property_analysis}
      ```
  3.2 **risk_tags**风险评分和打标签。风险标签如下：
      ```
        {risk_tags_template}
      ```


4. 输出要求
    4.1 请严格按以下JSON格式输出，确保可直接被`json.loads()`解析
    4.2 确保无歧义，可供系统自动解析和执行
    ```json
    {{
      "property_analysis": "请分析数据,提取property_analysis的value值,如果不存在数据,则返回空。例如：如果property_analysis是[{{'name': '资金', 'value': '' //总的资金时多少}}，{{'name': '用户数', 'value': '' //总的用户数是多少}}]，则返回[{{'name': '资金', 'value': '1000'}}，{{'name': '用户数', 'value': '50'}}]",
      "recommendations": "[请根据分析结果,生成优化建议]", // 可以多条建议
      "confidence": 0.0-1.0, // 报告的置信度，1为最高
      "metrics": "关键性能指标的数值化结果，用于效果评估。",
      "risk_score": 0-100,  // 风险评分范围是0-100分，越高表示存在的风险越大。
      "risk_tags": "[标签id]", // 可以打多个标签，也可以不打标签，根据标签描述结合数据实际情况打标签，如果风险标签为空，则返回空字符串。
      "description": "针对本次风控报告总结一个核心描述内容，简洁明了地概括主要风险点和关键发现，用于外部系统展示，长度控制在200字以内。" // 风险描述，用于外部系统展示
    }}
    ```
```
当前时间：{current_time} {week}
"""

ANALYSIS_PROMPT = """
{prompt_template}

【用户提问】
{user_query}
【系统指令】
对话规则：你回复时必须使用用户提问所使用的语言。请自动检测用户输入的语言，并保持一致
1. 查询条件如下：
```
{data_request}
```

2. 查询数据结果如下：
```
{analysis_data}
```

3. 输出要求
    {output_analytical_report}

当前时间：{current_time} {week}
"""
