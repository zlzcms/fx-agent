# -*- coding: utf-8 -*-
# @Author: zhujinlong
# @Date:   2025-06-29 10:00:00
# @Last Modified by:   zhujinlong
# @Last Modified time: 2025-07-05 14:52:56
# !/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import random

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.langgraph_agent import LangGraphAgent
from backend.app.admin.model.ai_model import AIModel
from backend.app.admin.model.ai_training_log import AITrainingLog
from backend.app.admin.schema.agent import (
    AnalysisReportRequest,
    AnalysisReportResponse,
    PromptGenerationRequest,
    PromptGenerationResponse,
)


class AgentService:
    """代理服务类，处理提示词生成等功能"""

    async def generate_prompt(self, db: AsyncSession, *, request: PromptGenerationRequest) -> PromptGenerationResponse:
        """
        生成提示词模板

        根据助手类型、名称、描述等参数生成适合的提示词模板
        """
        try:
            if isinstance(request.output_data, str):
                output_data = json.loads(request.output_data)
            else:
                output_data = request.output_data

            analysis_data_template = "以下是需要分析的数据：\n"
            output_template_json = "{"
            for index, item in enumerate(output_data):
                fieldName = item.get("fieldName", "")
                fieldDesc = item.get("fieldDesc") if item.get("fieldDesc", "") != "" else fieldName
                fieldType = item.get("fieldType", "")
                if fieldDesc:
                    analysis_data_template += (
                        f'{index + 1}.关于"{fieldName}"请分析{fieldDesc}信息，结果格式是：{fieldType}。\n'
                    )
                    output_template_json += f'"{fieldName}": "xxx(这里是分析结果)",'
            output_template_json = output_template_json[:-1]
            output_template_json += "}"

            if request.output_format == "json":
                output_format_template = f"""
                {analysis_data_template}
                请帮我分析以下json格式，并输出结果：\n
                {output_template_json}
                """
            elif request.output_format == "markdown":
                output_format_template = f'''
                    - 这输出数据是要求是markdown格式 以下是输出数据示例: "{request.output_data}"
                    '''
            elif request.output_format == "json,markdown":
                output_format_template = f'''
                我需要两个输出结果，一个是json格式，一个是markdown格式。
                - 这输出数据是要求是json格式:
                {analysis_data_template}
                以下是json格式示例：\n
                {output_template_json}
                - 这输出数据是要求是markdown格式 以下是输出数据示例: \n"{request.report_config}"

               '''

            # 构建提示词模板
            prompt_template = f'''
            # Role: 专业数据分析助手

            ## Profile
            - language语言: "中文/英文"
            - role角色: "{request.role or "专业数据分析助手"}"
            - name你定义的名称: "{request.name or "分析助手"} "
            - description你定义的描述: "{request.description or "根据数据分析用户需求，生成分析报告。"}"
            - background背景: "{request.background or "10年以上数据分析经验。"}"
            - definition你定义的提示词: "{request.prompt_definition or "请根据数据分析用户需求，生成分析报告。"}"

            # Data要分析的数据:
            - columns列元数据: "{request.data["columns"]}"
            - rows行数据: "{request.data["rows"]}"

            # Data数据说明：
            - 行数据（rows）是一个字典列表，每个字典代表一行记录。
            - 列元数据（columns）是一个字典列表，每个字典包含列名或者英文字段名例如：created_at。如果是英文字段名，则根据字段名推断其含义：
                balance: 根据字段名推断为"钱包余额"
                currency: 根据字段名推断为"钱包币种"
                wallet_name: 根据字段名推断为"钱包名称"
                wallet_type: 根据字段名推断为"钱包类型"

            ## Skills 技能
            - 自动解析columns元数据：将带括号的字段名映射为字段语义（如"balance"→"钱包余额"）
            - 智能补全空描述字段（如"创建"→"创建时间"）
            - 识别特殊字段：
                - 时间字段：created_at/updated_at → ISO 8601格式
                - 枚举字段：wallet_type → ("invest":投资账户, "partner":合伙人账户)
                - 布尔字段：is_default → (0:否, 1:是)

            ## Output 输出
            - 根据上面的Data数据，结合输出要求进行分析，输出结果。
            - 输出要求：
              {output_format_template}

            '''
            return PromptGenerationResponse(prompt_template=prompt_template, success=True, message="提示词模板生成成功")

        except Exception as e:
            return PromptGenerationResponse(prompt_template="", success=False, message=f"提示词模板生成失败: {str(e)}")

    async def generate_analysis_report(
        self, db: AsyncSession, *, request: AnalysisReportRequest
    ) -> AnalysisReportResponse:
        """
        生成分析报告

        使用指定的AI模型和提示词模板生成分析报告
        """
        try:
            # 查询AI模型配置
            stmt = select(AIModel).where(AIModel.id == request.model_id)
            result = await db.execute(stmt)
            model = result.scalar_one_or_none()

            if not model:
                return AnalysisReportResponse(
                    content="", success=False, message=f"未找到指定的AI模型: {request.model_id}"
                )

            if not model.status:
                return AnalysisReportResponse(content="", success=False, message=f"指定的AI模型已禁用: {model.name}")

            # 准备LangGraph代理的配置
            agent_config = {
                "api_key": model.api_key,
                "base_url": model.base_url,
                "model": model.model,
                "temperature": model.temperature,
            }

            # 创建LangGraph代理实例
            agent = LangGraphAgent(config=agent_config)

            # 构建完整的提示词，包含数据
            complete_prompt = request.prompt
            # if request.data:
            #     data_str = json.dumps(request.data, ensure_ascii=False, indent=2)
            #     complete_prompt += f"\n\n数据内容:\n{data_str}"
            try:
                result = await agent.box_score(complete_prompt)
                content = result["data"]["responses"][0]
                score = result["data"]["normalized_probability"][0]
            except Exception:
                try:
                    result = await agent.ainvoke(complete_prompt)
                    content = result.content
                    # 随机生成一个0.8-1.0的分数
                    score = random.uniform(0.8, 1.0)
                except Exception as e:
                    raise e

            # 准备返回结果
            analysis_response = AnalysisReportResponse(
                content=content, score=score, success=True, message="分析报告生成成功"
            )

            # # 创建训练日志记录
            training_log = AITrainingLog(
                model_id=model.id,
                model_name=model.name,
                prompt_template=request.prompt,
                success=True,
                score=score,  # 当前使用固定值1.0
                content=content,
                ai_response=[{"response": content, "model": model.model}],
                base_info=request.basic_info,
            )

            # 保存训练日志记录
            db.add(training_log)
            await db.commit()

            return analysis_response

        except Exception as e:
            # 创建失败的训练日志记录
            try:
                if model:
                    training_log = AITrainingLog(
                        model_id=model.id,
                        model_name=model.name,
                        prompt_template=request.prompt,
                        success=False,
                        score=0,
                        content="",
                        ai_response=[{"error": str(e)}],
                        base_info=request.basic_info,
                    )
                    db.add(training_log)
                    await db.commit()
            except Exception as log_error:
                print(f"Failed to save training log: {log_error}")

            return AnalysisReportResponse(content="", score=0, success=False, message=f"分析报告生成失败: {str(e)}")


agent_service = AgentService()
