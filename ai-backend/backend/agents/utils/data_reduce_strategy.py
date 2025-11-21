# -*- coding: utf-8 -*-
# 数据缩减策略模块 - 基于LangChain的map_reduce和summarize功能

import asyncio
import json

from typing import Any, AsyncGenerator, Dict, List, Optional

from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.agents.config.setting import settings
from backend.agents.tools.data_export_tool import DataExportTool
from backend.agents.utils.token_utils import estimate_tokens
from backend.common.log import logger


class DataReduceStrategy:
    """
    数据缩减策略类，用于处理大数据量时的token限制问题
    """

    def __init__(self, llm, **kwargs):
        """
        初始化数据缩减策略

        Args:
            llm: LLM实例
            kwargs: 配置参数，包含max_tokens, chunk_size, chunk_overlap, max_items_per_chunk
        """
        self.max_tokens = kwargs.get("max_tokens", settings.SPLIT_MAX_TOKEN)
        # 增加chunk_size以减少chunks数量，提高处理速度
        self.chunk_size = kwargs.get("chunk_size", settings.SPLIT_CHUNK_SIZE)
        self.chunk_overlap = kwargs.get("chunk_overlap", settings.SPLIT_CHUNK_OVERLAP)
        self.max_items_per_chunk = kwargs.get("max_items_per_chunk", settings.SPLIT_MAX_ITEMS_PER_CHUNK)

        self.llm = llm
        # 初始化文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap
        )

        self.data_export_tool = DataExportTool("data_reduce_strategy")

    async def _process_single_chunk_async(
        self, chunk_text: str, map_prompt_template: str, chunk_index: int, total_chunks: int
    ) -> str:
        """
        处理单个chunk（用于异步并发处理）

        Args:
            chunk_text: chunk文本
            map_prompt_template: 分析提示词模板
            chunk_index: chunk索引
            total_chunks: 总chunk数

        Returns:
            处理后的结果
        """
        try:
            logger.info(f"🔄 Processing chunk {chunk_index + 1}/{total_chunks}...")

            # 检查map_prompt_template是否有效
            if not map_prompt_template:
                raise ValueError("map_prompt_template is None or empty")

            # 检查map_prompt_template是否包含{text}占位符
            if "{text}" not in map_prompt_template:
                logger.warning(
                    f"map_prompt_template does not contain {{text}} placeholder: {map_prompt_template[:100]}..."
                )
                # 如果没有{text}占位符，直接使用模板
                prompt = map_prompt_template
            else:
                # 格式化prompt
                prompt = map_prompt_template.format(text=chunk_text)

            # 调用LLM（异步版本，性能更好）
            response = await self.llm.ainvoke(prompt)

            logger.info(f"✅ Chunk {chunk_index + 1}/{total_chunks} completed")
            return response.content

        except Exception as e:
            logger.error(f"❌ Chunk {chunk_index + 1}/{total_chunks} failed: {str(e)}")
            logger.error(f"map_prompt_template: {map_prompt_template[:200] if map_prompt_template else 'None'}...")
            logger.error(f"chunk_text length: {len(chunk_text) if chunk_text else 'None'}")
            return f"Chunk {chunk_index + 1} processing failed: {str(e)}"

    def split_structured_data(
        self, text_data: str, map_prompt_template: str = None, header_lines: int = 6, footer_lines: int = 1
    ) -> Dict[str, Any]:
        """
        将结构化数据拆分为头部、尾部、数据部分

        Args:
            text_data: 原始文本数据
            map_prompt_template: Map阶段的提示词模板（用于计算可用chunk_size）
            header_lines: 头部行数，默认6行
            footer_lines: 尾部行数，默认1行

        Returns:
            包含头部、尾部、数据部分chunks的字典
        """
        try:
            logger.info("Starting structured data splitting")

            # 按行分割数据
            lines = text_data.split("\n")
            total_lines = len(lines)

            logger.info(f"Total lines: {total_lines}")

            # 提取头部
            header_lines = min(header_lines, total_lines)
            header = "\n".join(lines[:header_lines])

            # 提取尾部
            footer_lines = min(footer_lines, total_lines - header_lines)
            footer = "\n".join(lines[-footer_lines:]) if footer_lines > 0 else ""

            # 提取数据部分（中间部分）
            data_start = header_lines
            data_end = total_lines - footer_lines
            data_lines = lines[data_start:data_end] if data_end > data_start else []
            data_content = "\n".join(data_lines)

            logger.info(f"Header lines: {header_lines}, Footer lines: {footer_lines}, Data lines: {len(data_lines)}")

            # 如果没有数据部分，直接返回
            if not data_content.strip():
                return {"header": header, "footer": footer, "data_chunks": [], "total_chunks": 0}

            # 计算可用的chunk_size
            available_chunk_size = self.chunk_size
            if map_prompt_template:
                # 估算map_prompt_template的token数
                prompt_tokens = estimate_tokens(map_prompt_template)
                # 预留一些空间给响应
                reserved_tokens = prompt_tokens + 500  # 预留500个token给响应
                available_chunk_size = max(100, self.chunk_size - reserved_tokens)
                logger.info(f"Map prompt tokens: {prompt_tokens}, Available chunk size: {available_chunk_size}")

            # 使用调整后的chunk_size创建文本分割器
            data_splitter = RecursiveCharacterTextSplitter(
                chunk_size=available_chunk_size, chunk_overlap=self.chunk_overlap
            )

            # 分割数据部分
            data_docs = data_splitter.create_documents([data_content])
            data_chunks_raw = [doc.page_content for doc in data_docs]

            # 将头部和尾部添加到每个chunk中
            data_chunks = []
            for i, chunk_content in enumerate(data_chunks_raw):
                # 检查chunk是否有实际数据内容（不只是空白或分隔符）
                chunk_content_clean = chunk_content.strip()
                if not chunk_content_clean or len(chunk_content_clean) < 10:
                    logger.warning(f"Skipping chunk {i} - no meaningful data content")
                    continue

                # 组合头部 + 数据chunk + 尾部
                full_chunk = f"{header}\n\n{chunk_content}\n\n{footer}".strip()
                data_chunks.append(full_chunk)
                self.data_export_tool.export_to_markdown(full_chunk, task_id=f"chunk_{i}")

            logger.info(f"Split data section into {len(data_chunks)} chunks (each with header and footer)")

            # 导出拆分结果用于调试
            # self.data_export_tool.export_to_markdown(header, task_id="split_header")
            # self.data_export_tool.export_to_markdown(footer, task_id="split_footer")
            # self.data_export_tool.export_to_markdown(data_content, task_id="split_data_content")
            # self.data_export_tool.export_to_markdown(map_prompt_template, task_id="map_prompt_template")

            return {
                "header": header,
                "footer": footer,
                "data_chunks": data_chunks,
                "total_chunks": len(data_chunks),
                "chunk_size_used": available_chunk_size,
                "original_chunk_size": self.chunk_size,
            }

        except Exception as e:
            logger.error(f"Structured data splitting failed: {str(e)}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            raise e

    async def reduce_data_async_stream(
        self,
        data: [list, str],
        map_prompt_template: str,
        combine_prompt_template: str,
        **kwargs,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        异步生成器版本的数据缩减方法，直接yield进度事件
        避免了回调模式和队列轮询，代码更简洁优雅
        
        Yields:
            Dict[str, Any]: 包含进度信息的事件字典
                - type: "chunk_completed" 或 "__final__"
                - chunk_index: chunk索引（仅chunk_completed）
                - total_chunks: 总chunk数（仅chunk_completed）
                - result: chunk处理结果（仅chunk_completed）
                - content: 最终结果（仅__final__）
        """
        if isinstance(data, list):
            async for event in self.process_data_chunks_async_stream(
                data,
                map_prompt_template,
                combine_prompt_template,
            ):
                yield event
        else:
            async for event in self.reduce_text_data_async_stream(
                data,
                map_prompt_template,
                combine_prompt_template,
                **kwargs,
            ):
                yield event

    async def reduce_text_data_async_stream(
        self,
        text_data: str,
        map_prompt_template: str = None,
        combine_prompt_template: str = None,
        header_lines: int = 6,
        footer_lines: int = 1,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        使用结构化拆分策略缩减文本数据（异步生成器版本）
        直接yield进度事件，避免回调模式

        Yields:
            Dict[str, Any]: 进度事件
        """
        try:
            logger.info("Starting structured text data reduction (async stream)")

            # 首先进行结构化拆分
            split_result = self.split_structured_data(text_data, map_prompt_template, header_lines, footer_lines)

            header = split_result["header"]
            footer = split_result["footer"]
            data_chunks = split_result["data_chunks"]

            if not data_chunks:
                logger.info("No data chunks to process, returning header and footer")
                final_content = f"{header}\n\n{footer}".strip()
                yield {"type": "__final__", "content": final_content}
                return

            # 定义默认的map_prompt_template
            if not map_prompt_template:
                map_prompt_template = """
                    请分析以下数据片段，提取关键信息和模式：

                    数据片段：
                    {text}

                    请提供：
                    1. 关键数据点
                    2. 重要趋势或模式
                    3. 异常值或值得注意的点
                    4. 简要总结
                    """

            if not combine_prompt_template:
                combine_prompt_template = """
                基于以下各个数据片段的分析结果，生成一份综合分析报告：

                分析结果：
                {text}

                请整合所有信息，提供：
                1. 整体数据概览
                2. 主要趋势和模式
                3. 关键发现
                4. 综合结论
                """

            # 处理数据chunks（异步生成器版本）
            async for event in self.process_data_chunks_async_stream(
                data_chunks,
                map_prompt_template,
                combine_prompt_template,
            ):
                yield event

        except Exception as e:
            logger.error(f"Structured text data reduction (async stream) failed: {str(e)}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            raise e

    async def process_data_chunks_async_stream(
        self,
        data_chunks: List[str],
        map_prompt_template: str,
        combine_prompt_template: str = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        异步生成器版本的处理数据chunks方法
        直接yield进度事件，避免回调模式，代码更简洁优雅

        Args:
            data_chunks: 数据chunks列表
            map_prompt_template: Map阶段的提示词模板
            combine_prompt_template: Reduce阶段的提示词模板

        Yields:
            Dict[str, Any]: 包含进度信息的事件字典
                - type: "chunk_completed" 或 "__final__"
                - chunk_index: chunk索引（仅chunk_completed）
                - total_chunks: 总chunk数（仅chunk_completed）
                - result: chunk处理结果（仅chunk_completed）
                - content: 最终结果（仅__final__）
        """
        total_chunks = len(data_chunks)
        map_results = [""] * total_chunks

        if settings.SPLIT_USE_PARALLEL and total_chunks > 1:
            logger.info(f"🚀 Starting ASYNC PARALLEL processing of {total_chunks} data chunks (stream)")

            # 创建任务并建立 task -> chunk_index 的映射
            task_to_index = {}
            for i, chunk_text in enumerate(data_chunks):
                task = asyncio.create_task(self._process_single_chunk_async(chunk_text, map_prompt_template, i, total_chunks))
                task_to_index[task] = i

            # 使用 asyncio.as_completed 按完成顺序处理任务
            async for task in asyncio.as_completed(task_to_index.keys()):
                idx = task_to_index[task]
                try:
                    result = await task
                except Exception as e:
                    logger.error(f"❌ Data chunk {idx + 1}/{total_chunks} failed: {str(e)}")
                    result = f"Data chunk {idx + 1} processing failed: {str(e)}"
                map_results[idx] = result
                # 直接yield进度事件，而不是通过回调
                yield {
                    "type": "chunk_completed",
                    "chunk_index": idx + 1,
                    "total_chunks": total_chunks,
                    "result": result,
                }

        else:
            logger.info(f"📊 Starting ASYNC SEQUENTIAL processing of {total_chunks} data chunks (stream)")

            for i, chunk_text in enumerate(data_chunks):
                try:
                    result = await self._process_single_chunk_async(chunk_text, map_prompt_template, i, total_chunks)
                except Exception as e:
                    logger.error(f"❌ Data chunk {i + 1}/{total_chunks} failed: {str(e)}")
                    result = f"Data chunk {i + 1} processing failed: {str(e)}"
                map_results[i] = result
                # 直接yield进度事件，而不是通过回调
                yield {
                    "type": "chunk_completed",
                    "chunk_index": i + 1,
                    "total_chunks": total_chunks,
                    "result": result,
                }

        # Reduce阶段：合并所有结果
        logger.info(f"🔄 Starting REDUCE phase to combine {len(map_results)} results...")
        logger.info("📋 All Map phase tasks completed, proceeding to Reduce phase")

        combined_text = "\n\n".join([f"数据片段 {i + 1} 分析结果:\n{result}" for i, result in enumerate(map_results)])

        # 使用combine prompt合并结果
        if not combine_prompt_template:
            combine_prompt_template = map_prompt_template
        final_prompt = combine_prompt_template.format(text=combined_text)

        logger.info(f"🎯 Executing final LLM call for Reduce phase")
        final_response = await self.llm.ainvoke(final_prompt)
        logger.info("✅ REDUCE phase completed successfully")

        # yield最终结果
        yield {"type": "__final__", "content": final_response.content}
