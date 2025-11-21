# -*- coding: utf-8 -*-
# Token计数和数据拆分工具

from typing import Any, List, Tuple


def estimate_tokens(text: str) -> int:
    """
    估算文本的token数量
    使用更准确的规则：平均每个字符约0.75个token

    Args:
        text: 要估算的文本

    Returns:
        估算的token数量
    """
    if not text:
        return 0

    # 统计中文字符和英文字符
    chinese_chars = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
    english_chars = len(text) - chinese_chars

    # 更准确的token估算：
    # 中文字符：约1.5个token/字符
    # 英文字符：约1个token/字符（包括空格、标点等）
    estimated_tokens = int(chinese_chars * 1.5 + english_chars * 1)

    return estimated_tokens


def split_data_by_tokens(data: str, max_tokens: int = 3000) -> List[str]:
    """
    按token数量拆分数据

    Args:
        data: 要拆分的数据（markdown格式）
        max_tokens: 每个块的最大token数

    Returns:
        拆分后的数据列表
    """
    if not data:
        return []

    # 估算总token数
    total_tokens = estimate_tokens(data)

    # 如果数据不大，直接返回
    if total_tokens <= max_tokens:
        return [data]

    chunks = []

    # 按行拆分
    lines = data.split("\n")
    current_chunk = []
    current_tokens = 0

    for line in lines:
        line_tokens = estimate_tokens(line)

        # 如果单行就超过最大token，需要进一步拆分
        if line_tokens > max_tokens:
            if current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_tokens = 0

            # 对超长行进行字符级拆分
            line_chunks = split_long_line(line, max_tokens)
            chunks.extend(line_chunks)
        else:
            # 如果加上这行会超过限制，先保存当前块
            if current_tokens + line_tokens > max_tokens and current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = [line]
                current_tokens = line_tokens
            else:
                current_chunk.append(line)
                current_tokens += line_tokens

    # 添加最后一个块
    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks


def split_long_line(line: str, max_tokens: int) -> List[str]:
    """
    拆分超长行

    Args:
        line: 超长的行
        max_tokens: 最大token数

    Returns:
        拆分后的行列表
    """
    chunks = []
    # 估算每个字符的平均token数
    avg_tokens_per_char = estimate_tokens(line) / len(line) if line else 1
    # 计算每个块的最大字符数
    max_chars = int(max_tokens / avg_tokens_per_char)

    for i in range(0, len(line), max_chars):
        chunks.append(line[i : i + max_chars])

    return chunks


def split_json_data(data: Any, max_items_per_chunk: int = 100) -> List[Any]:
    """
    拆分JSON数据（列表或字典）

    Args:
        data: JSON数据（通常是列表或字典）
        max_items_per_chunk: 每个块的最大项目数

    Returns:
        拆分后的数据列表
    """
    if isinstance(data, list):
        # 如果是列表，按指定数量拆分
        chunks = []
        for i in range(0, len(data), max_items_per_chunk):
            chunks.append(data[i : i + max_items_per_chunk])
        return chunks
    elif isinstance(data, dict):
        # 如果是字典，按键值对拆分
        items = list(data.items())
        chunks = []
        for i in range(0, len(items), max_items_per_chunk):
            chunk_items = items[i : i + max_items_per_chunk]
            chunks.append(dict(chunk_items))
        return chunks
    else:
        # 其他类型直接返回
        return [data]


def check_token_limit(text: str, max_tokens: int = 4000) -> Tuple[bool, int]:
    """
    检查文本是否超过token限制

    Args:
        text: 要检查的文本
        max_tokens: token限制

    Returns:
        (是否超限, 实际token数)
    """
    tokens = estimate_tokens(text)
    return tokens > max_tokens, tokens
