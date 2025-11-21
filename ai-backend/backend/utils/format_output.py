import datetime
import json
import logging
import re

from typing import Any, Dict, Optional

from backend.agents.schema.agent import YieldResponse

logger = logging.getLogger("risk_analysis")


def extract_json(content: str) -> Dict:
    """从字符串中提取JSON数据"""
    # 查找JSON代码块
    parsed_result = {}
    json_match = re.search(r"```json\s*({.*?})\s*```", content, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # 如果没有找到代码块，尝试直接解析整个响应
        json_str = content
    try:
        parsed_result = json.loads(json_str)
    except json.JSONDecodeError as e:
        # 如果JSON解析失败，尝试清理和修复
        cleaned_json = clean_json_string(json_str)
        try:
            parsed_result = json.loads(cleaned_json)
        except json.JSONDecodeError:
            raise Exception(f"无法解析AI返回的JSON格式: {str(e)}")
    return parsed_result


def format_ai_output(
    content: str,
) -> dict:
    # Extract JSON data (analysis and tags)
    json_data = []
    markdown_data = ""

    try:
        # Find all code blocks with their language identifiers
        code_block_pattern = r"```(\w*)\s*\n([\s\S]*?)```"
        code_blocks = re.findall(code_block_pattern, content)

        for lang, block_content in code_blocks:
            lang = lang.strip().lower()

            if lang == "json":
                try:
                    # First attempt: Parse as is
                    block_text = block_content.strip()
                    json_data.append(json.loads(block_text))
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON: {e}")

                    # Second attempt: Try with different cleanups
                    for attempt, cleanup in enumerate(
                        [
                            # Try removing language identifier if present at the beginning
                            lambda txt: txt[4:].strip() if txt.startswith("json") else txt,
                            # Try fixing escaped characters
                            lambda txt: txt.replace("\\n", "\n").replace("\\'", "'").replace('\\"', '"'),
                            # Try removing any trailing commas in objects or arrays
                            lambda txt: re.sub(r",\s*}", "}", re.sub(r",\s*]", "]", txt)),
                        ]
                    ):
                        try:
                            cleaned_text = cleanup(block_text)
                            if cleaned_text != block_text:
                                logger.debug(f"Cleanup attempt {attempt + 1}: Modified JSON")
                                json_data.append(json.loads(cleaned_text))
                                logger.info(f"Successfully parsed JSON after cleanup attempt {attempt + 1}")
                                break
                        except json.JSONDecodeError:
                            continue
                    else:
                        # If all cleanup attempts failed, log the error with content
                        logger.error(f"Failed to parse JSON after all cleanup attempts. Content: {block_text}")

            elif lang == "markdown":
                markdown_data = block_content.strip()

    except Exception as e:
        logger.exception(f"Error parsing content: {e}")

    return json_data, markdown_data


def convert_to_dict(obj: Any) -> Dict[str, Any]:
    """
    将各种类型的对象转换为字典格式

    支持的类型：
    - Pydantic模型（带有model_dump方法）
    - 带有__dict__属性的普通对象
    - 字符串（尝试解析为JSON）
    - 字典（直接返回）
    - 其他类型（尝试转换为字典，如果失败则包装在dict中）

    Args:
        obj: 要转换的对象

    Returns:
        转换后的字典
    """
    # 处理None值
    if obj is None:
        return {}

    # 处理Pydantic模型（v2版本使用model_dump）
    if hasattr(obj, "model_dump"):
        return obj.model_dump()

    # 处理Pydantic模型（v1版本使用dict）
    if hasattr(obj, "dict") and callable(getattr(obj, "dict")):
        return obj.dict()

    # 处理普通对象
    if hasattr(obj, "__dict__"):
        # 过滤掉私有属性（以_开头）
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_") and not callable(v)}

    # 处理字符串（尝试解析为JSON）
    if isinstance(obj, str):
        try:
            return json.loads(obj)
        except json.JSONDecodeError:
            return {"content": obj}

    # 处理字典
    if isinstance(obj, dict):
        # 递归处理字典中的值
        return {
            k: convert_to_dict(v)
            if isinstance(v, (dict, object)) and not isinstance(v, (str, int, float, bool, list))
            else v
            for k, v in obj.items()
        }

    # 处理列表
    if isinstance(obj, list):
        # 递归处理列表中的项
        return [
            convert_to_dict(item)
            if isinstance(item, (dict, object)) and not isinstance(item, (str, int, float, bool, list))
            else item
            for item in obj
        ]

    # 处理其他类型
    try:
        # 尝试转换为字典
        return dict(obj)
    except (TypeError, ValueError):
        # 如果无法转换，则包装在字典中
        return {"value": str(obj)}


def extract_limit(text: str) -> Optional[int]:
    """从文本中提取限制数量

    参数:
        text: 文本

    返回:
        提取的限制数量，如果未找到则返回None
    """
    pattern = r"(?:限制|最多|前)(?:显示|返回|查询)?\s*(\d+)\s*(?:条|笔|个|记录)?"
    match = re.search(pattern, text)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            pass
    return None


def extract_userid(text: str) -> Optional[str]:
    """从文本中提取用户ID

    参数:
        text: 文本

    返回:
        提取的用户ID，如果未找到则返回None
    """
    pattern = r"(?:用户|客户)(?:ID|id|编号)[是为:：]?\s*[\"\'](.*?)[\"\']"
    match = re.search(pattern, text)
    if match:
        return match.group(1)
    return None


def clean_json_string(json_str: str) -> str:
    """清理和修复JSON字符串"""
    import re

    # 移除多余的空白字符
    json_str = json_str.strip()

    # 移除可能的markdown标记
    json_str = re.sub(r"^```json\s*", "", json_str)
    json_str = re.sub(r"\s*```$", "", json_str)

    # 移除注释
    json_str = re.sub(r"//.*?\n", "\n", json_str)

    # 修复常见的JSON格式问题
    json_str = re.sub(r",\s*}", "}", json_str)  # 移除对象末尾多余的逗号
    json_str = re.sub(r",\s*]", "]", json_str)  # 移除数组末尾多余的逗号

    return json_str


def format_message(message: Any):
    """格式化消息，确保所有对象都能被JSON序列化"""
    if isinstance(message, YieldResponse):
        # 使用model_dump()并确保枚举被正确转换
        return message.model_dump(mode="json")
    elif isinstance(message, (dict, str)):
        return message
    elif hasattr(message, "value"):  # 处理枚举类型
        return message.value
    elif hasattr(message, "model_dump"):  # 处理其他Pydantic模型
        return message.model_dump(mode="json")
    else:
        return convert_to_dict(message)


def get_current_weekday() -> str:
    """获取今天是星期几（中文）

    返回:
        今天的星期几，例如"星期一"、"星期二"等
    """
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    # datetime.datetime.now().weekday() 返回 0-6，对应周一到周日
    return weekdays[datetime.datetime.now().weekday()]
