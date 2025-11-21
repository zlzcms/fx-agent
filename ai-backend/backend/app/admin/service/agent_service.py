import uuid

from langchain_core.messages import HumanMessage, SystemMessage

from backend.agents.agents.general_chat_agent import GeneralChatAgent
from backend.app.admin.schema.agent import (
    ContentPolishRequest,
    ContentPolishResponse,
    SmartAssistantCreateRequest,
    SmartAssistantCreateResponse,
)
from backend.utils.format_output import extract_json


class AgentService:
    """智能助手服务类"""

    async def create_assistant(self, request: SmartAssistantCreateRequest) -> SmartAssistantCreateResponse:
        """创建智能助手"""
        prompt_template = f"""
        ## 用户需求：{request.question}
        ## 输出格式
            - **model_definition**:根据用户需求，给出一份简洁的模型定义，主要用于模型的理解和应用。
            - **table_output**:表示特定的属性输出,请根据要求提供0-3个参考属性，每个属性都有属性名、属性类型、属性描述：
                属性类型：string/number/boolean
                属性名：属性的名称，可以中文或英文
                属性描述：属性的详细描述
            - **document_output**:请根据用户需求，给出一份详细的报告markdown格式的文档模板。
                例如：
                    ```
                        # 分析报告

                        ## 数据概况
                        - 数据源：[数据源名称]
                        - 时间范围：[时间范围]

                        ## 关键指标
                        | 指标 | 数值 | 变化 |
                        |------|------|------|
                        | 指标1 | [数值] | [变化] |
                        | 指标2 | [数值] | [变化] |
                        | 指标3 | [数值] | [变化] |

                        ## 主要发现
                        [简要描述主要发现]

                        ## 建议
                        - [建议1]
                        - [建议2]
                        - [建议3]
                        ···

            - 请严格按以下JSON格式输出，确保可直接被`json.loads()`解析：
                ```json
                {{
                    "name": "助手名称",
                    "description": "助手类型",
                    "model_definition": "助手模型定义",
                    "table_output": [
                        {{
                            "fieldName": "属性1",
                            "fieldType": "类型",
                            "fieldDesc": "属性1描述"
                        }},
                        {{
                            "fieldName": "属性2",
                            "fieldType": "类型",
                            "fieldDesc": "属性2描述"
                        }},
                        ...

                    ],
                    "document_output": ""
                }}```
        """

        agent_config = {
            "system_prompt": "你是一个智能创建助手，你需要根据用户的需求创建智能助手",
            "prompt_template": prompt_template,
        }

        try:
            task_id = str(uuid.uuid4())
            agent = GeneralChatAgent(task_id=task_id, config=agent_config)

            result = await agent.analyze_intent(request.question)

            if not result.success:
                raise Exception(f"智能体分析失败: {result.message}")

            ai_response_content = result.data

            parsed_result = extract_json(ai_response_content)

            response = SmartAssistantCreateResponse(
                name=parsed_result.get("name", "智能助手"),
                description=parsed_result.get("description", "智能助手描述"),
                model_definition=parsed_result.get("model_definition", "智能助手模型定义"),
                table_output=parsed_result.get("table_output", []),
                document_output=parsed_result.get("document_output", ""),
            )

            return response

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"创建智能助手失败: {str(e)}")

            return SmartAssistantCreateResponse(
                name=f"基于'{request.question}'的智能助手",
                description="根据用户需求自动生成的智能助手",
                model_definition=f"专门处理'{request.question}'相关任务的智能助手",
                table_output=[{"fieldName": "结果", "fieldType": "string", "fieldDesc": "处理结果描述"}],
                document_output=f"这是一个专门处理'{request.question}'的智能助手，能够提供相关的分析和建议。",
            )

    async def polish_content(self, request: ContentPolishRequest) -> ContentPolishResponse:
        """AI内容润色"""
        task = request.task or """对内容进行润色，使其更加流畅、准确和易读,功能、能力和使用场景要符合要求"""
        prompt_template = f"""
        ## 润色任务
            {task}
        ## 要求
            1. 保持原文的核心意思不变
            2. 改进语言表达的流畅性和准确性
            3. 根据指定的润色类型调整语言风格

        ## 原始内容
            [[[{request.content}]]]

        ## 直接输出润色后的提示词
            - 模型的定义：基于ai的数据分析模型
            - 应用场景：客服对话、智能助手
            - 需要的能力：理解用户意图、生成自然语言回复
            例如：
            “
            ## 模型定义
            数据资源深度分析和智能处理

            ## 应用场景
            - 数据资源深度分析和智能处理
            - 智能决策支持
            - 自动化分析报告生成
            - 数据可视化

            ## 需要的能力
            - 理解用户意图
            - 生成自然语言回复
            - 数据可视化
        """

        agent_config = {
            "system_prompt": f"你是一个专业的{request.role}内容润色助手，擅长根据不同需求对文本进行润色和改进",
            "prompt_template": prompt_template,
        }

        try:
            task_id = str(uuid.uuid4())
            agent = GeneralChatAgent(task_id=task_id, config=agent_config)

            system_prompt = agent_config.get("system_prompt", "")
            prompt_template = agent_config.get("prompt_template", "")

            messages = []
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
            messages.append(HumanMessage(content=prompt_template))

            ai_response = await agent.ainvoke(messages, f"内容润色【{request.content[:50]}...】")
            ai_response_content = ai_response.content.strip()

            if not ai_response_content:
                raise Exception("AI返回的内容为空")

            response = ContentPolishResponse(original_content=request.content, polished_content=ai_response_content)

            return response

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"内容润色失败: {str(e)}")

            raise Exception(f"内容润色失败: {str(e)}")


agent_service = AgentService()
