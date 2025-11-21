# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-09-04 18:13:00
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-09-08 16:35:49
# 查询结果分析模板
QUERY_RESULT_ANALYSIS_TEMPLATE = """
用户提问：{user_query}
以下是查询的数据：{query_result}
数据范围：{data_range}
请将根据用户需求结合数据，做分析和总结，并给出建议，最后给出总结报告。
【核心指令】
**语言一致性**：请始终使用我提问时使用的同一种语言进行回复。
【系统指令】
对话规则：你回复时必须使用用户提问所使用的语言。请自动检测用户输入的语言，并保持一致

注意：如果查询的数据为空，表示无数据此时仅需要提示用户。当前时间：{current_time}
"""

# 错误处理模板
ERROR_TEMPLATES = {
    "assistant_not_found": "告诉用户'{assistant_name}'不在下列助手列表中：{assistants_list}",
    "error": "请先抱歉，然后告诉用户'{user_query}'出现{error_message}的情况，并给出建议。请用亲切的语气，精简回答，并且给这段话加上提示的样式。请自动检测用户输入的语言，并保持一致",
}

# 确认助手的数据模板
CONFIRM_ASSISTANT_DATA_TEMPLATE = """
以下是‘{assistant_name}’助手需要的数据：{assistant_query_type_names}，
识别到用户提供的数据：{user_query_types}，
请用确实使用助手的数据，还是使用用户提供的数据。
【核心指令】
**语言一致性**：请始终使用我提问时使用的同一种语言进行回复。
【系统指令】
对话规则：你回复时必须使用用户提问所使用的语言。请自动检测用户输入的语言，并保持一致
示例：
"你提供的数据是['登录']信息，而“客户风控助理”助手需要的数据包括：['MT5持仓', 'MT5用户', 'MT4用户', 'MT5交易', 'MT4交易', 'MT登录', '转账', '登录', '资金', '基本信息']。
你提供的数据与助手需要的数据不完全匹配可能影响报告的准确性。是否使用助手需要的数据呢？回答为“是”或“否”即可。"
"""

# 默认配置
DEFAULT_CONFIG = {
    "max_retry_attempts": 3,
    "timeout_seconds": 30,
    "default_assistant": "通用助手",
    "fallback_intent": "chat",
}
# 报告生成计划模板
REPORT_PLAN_TEMPLATE = """
用户提问：{user_query}
以下是意图分析的结果：{intent_result}
以下是助手信息：{assistant}
生成报告的计划如下：{report_task_steps}
【核心指令】
**语言一致性**：请始终使用我提问时使用的同一种语言进行回复。
【系统指令】
对话规则：你回复时必须使用用户提问所使用的语言。请自动检测用户输入的语言，并保持一致
请根据以上信息，概述整个报告的计划过程,以步骤和简单描述，最后概要等形式。
# 输出格式markdown
  先写标题，然后写步骤，最后写概要总结。
# 示例：
"我将为您通过某某助手生成一份完整的报告的生成计划，确保您清楚每一步是如何进行的。以下是详细的流程：
 1. 从MCP服务获取数据
 2. 数据处理和拆分
 3. AI数据分析
 4. 生成报告
整个报告生成过程是一个循序渐进、系统化的流程，从数据获取到最终报告生成，每一步都经过精心设计，以确保最终报告的准确性和实用性。如果您有任何疑问或需要进一步了解某一步骤，请随时告诉我！😊

注意：1如果用户没有提供助手，则不使用助手。
     2.每一步要有标号。
     3.步骤标题粗体，步骤和概要总结正常。
"""

PARAM_ANALYSIS_TEMPLATE = """
你是一个数据识别助手，具备准确解析用户深层需求并提取关键参数。

# 以下是要识别的数据：
{slot_data}

# 参数说明:
**query_type**数据类型
  {query_type_list}
  请提取query_type的键值，根据数据对应的query_type的value值结合上面的列表找到键值，例如：value值为'资金,登录'，则query_type为['user_amount_log', 'user_login_log']，如果value值为空，则query_type为空。
**username**用户名
  请提取username的值，根据数据对应的username或user_identifier的value值，如果value值为空，则username为空。
**user_id**用户ID
  请提取user_id的键值，根据数据对应的user_id的value值，如果value值为空，则user_id为空。
**start_time 和 end_time**时间
  请计算start_time 和 end_time的值，根据数据对应的time_range的value值，计算出开始时间和结束时间，例如：time_range的value为'10天'，则start_time为当前时间减去10天，end_time为当前时间。当前时间是：{current_time}
**其他参数**
  请提取其他参数的键值，根据数据对应的其他参数的value值，如果value值为空，则其他参数为空。

# 输出格式
请严格按照以下JSON格式返回结果：

```json
{{
  "query_type": [],
  "data_params": {{
    "username": "",
    "user_id": "",
    "start_time": "",
    "end_time": ""
  }}
}}
```
# 示例
数据：
```json
{{
  "query_type": {{'description': '获取数据类型', 'status': 'filled', 'value': '基本信息', 'required': True}},
  "user_identifier": {{'description': '用户标识', 'status': 'filled', 'value': '张三', 'required': True}},
  "time_range": {{'description': '时间范围', 'status': 'filled', 'value': '30天', 'required': True}}
}}
```

输出：
```json
{{
  "query_type": ['user_data'],
  "data_params": {{
    "username": "张三",
    "user_id": "",
    "start_time": "2025-07-27",
    "end_time": "2025-08-26"
  }}
}}
```
"""
