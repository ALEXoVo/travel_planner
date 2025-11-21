"""
JSON修复工具模块

提供修复不完整或格式错误的JSON字符串的功能，
主要用于处理AI返回的可能被截断的JSON响应。
"""
import json
import re
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def fix_incomplete_json(json_str: str) -> str:
    """
    修复不完整的JSON字符串。

    处理策略：
    1. 移除Markdown代码块标记
    2. 修复缺失的逗号（在对象和数组之间）
    3. 闭合未闭合的字符串（添加引号）
    4. 平衡所有括号
    5. 智能截断不完整的最后一行/字段

    Args:
        json_str: 可能不完整的JSON字符串

    Returns:
        str: 修复后的JSON字符串

    Examples:
        >>> fix_incomplete_json('{"key": "value"')
        '{"key": "value"}'
        >>> fix_incomplete_json('[{"a": 1}{"b": 2}]')
        '[{"a": 1},{"b": 2}]'
    """
    # 移除可能的代码块标记
    json_str = json_str.replace('```json', '').replace('```', '').strip()

    # 核心修复循环
    while True:
        original_json_str = json_str

        # 1. 修复缺失的逗号 (在 }{、][、}[、]{ 之间)
        json_str = re.sub(r'(\})\s*(\{)', r'\1,\2', json_str)
        json_str = re.sub(r'(\])\s*(\[)', r'\1,\2', json_str)
        json_str = re.sub(r'(\})\s*(\[)', r'\1,\2', json_str)
        json_str = re.sub(r'(\])\s*(\{)', r'\1,\2', json_str)

        # 2. 移除末尾多余的逗号
        json_str = re.sub(r',\s*([}\]])', r'\1', json_str.strip())

        # 3. 尝试闭合未闭合的字符串 (引号修复)
        quote_count = json_str.count('"')
        if quote_count % 2 != 0 and json_str.endswith('"') is False:
            # 如果引号数量是奇数且字符串末尾没有引号，尝试在末尾添加引号
            json_str += '"'

        # 4. 补充缺失的括号
        open_braces = json_str.count('{')
        close_braces = json_str.count('}')
        open_brackets = json_str.count('[')
        close_brackets = json_str.count(']')

        temp_json_str = json_str
        temp_json_str += '}' * max(0, open_braces - close_braces)
        temp_json_str += ']' * max(0, open_brackets - close_brackets)

        # 5. 尝试解析
        try:
            json.loads(temp_json_str)
            return temp_json_str  # 成功，返回
        except json.JSONDecodeError as e:
            # 6. 智能截断：找到最后一个有效分隔符，截断其后的内容。
            last_comma_pos = json_str.rfind(',')
            last_valid_pos = max(json_str.rfind('}'), json_str.rfind(']'))

            if last_comma_pos != -1 and (last_comma_pos > last_valid_pos or last_valid_pos == -1):
                # 如果找到逗号，且它在最后一个闭合符之后（或没有闭合符），截断到逗号之前。
                json_str = json_str[:last_comma_pos]
            elif last_valid_pos != -1:
                # 否则，如果有一个闭合符，截断到该闭合符之后，以清除后续的垃圾字符。
                json_str = json_str[:last_valid_pos + 1]
            else:
                # 没有任何有效分隔符，无法修复
                break

            # 7. 检查修复是否产生了变化
            if json_str == original_json_str:
                break

            # 修复导致字符串变化，继续循环
            continue

        except Exception:
            # 捕获其他异常，防止无限循环
            break

    return original_json_str


def extract_json_from_text(text: str) -> Optional[dict]:
    """
    从文本中提取JSON部分并解析。

    Args:
        text: 包含JSON的文本字符串

    Returns:
        Optional[dict]: 解析后的字典对象，失败返回None

    Examples:
        >>> extract_json_from_text('Some text {"key": "value"} more text')
        {'key': 'value'}
    """
    # 尝试提取JSON部分
    json_match = re.search(r'\{.*\}|\[.*\]', text, re.DOTALL)

    if not json_match:
        logger.warning("No JSON structure found in text")
        return None

    json_str = json_match.group()

    # 尝试解析
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        logger.info("JSON parsing failed, attempting to fix...")
        # 尝试修复
        try:
            fixed_json = fix_incomplete_json(json_str)
            return json.loads(fixed_json)
        except Exception as e:
            logger.error(f"JSON fix failed: {str(e)}")
            return None


def validate_json_structure(data: dict, required_keys: list) -> bool:
    """
    验证JSON数据是否包含必需的键。

    Args:
        data: 要验证的字典数据
        required_keys: 必需的键列表

    Returns:
        bool: 如果包含所有必需键返回True，否则False

    Examples:
        >>> validate_json_structure({'a': 1, 'b': 2}, ['a', 'b'])
        True
        >>> validate_json_structure({'a': 1}, ['a', 'b'])
        False
    """
    return all(key in data for key in required_keys)
