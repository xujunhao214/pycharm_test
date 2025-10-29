import logging
from jsonpath_ng import parse
from typing import Optional, Any, List, Dict, Union


class JsonPathUtils:
    """JSONPath工具类，用于从JSON响应中提取数据"""

    def extract(self, class_random_str, data: dict, expression: str, default: Any = None, multi_match: bool = False) -> Any:
        """
        使用JSONPath表达式从数据中提取值
        :param data: JSON数据
        :param expression: JSONPath表达式
        :param default: 未找到匹配时的默认值
        :param multi_match: 是否允许多匹配结果
        :return: 单个匹配值、多匹配列表或默认值
        """
        try:
            jsonpath_expr = parse(expression)
            matches = jsonpath_expr.find(data)

            if not matches:
                return default

            if multi_match:
                return [match.value for match in matches]
            else:
                return matches[0].value if matches else default

        except Exception as e:
            # 处理无效表达式等异常
            logging.info(f"JSONPath解析错误: {e}")
            return default

    def assert_value(self, class_random_str, data: dict, expression: str, expected: any) -> None:
        """断言JSONPath表达式提取的值与预期值相等"""
        actual = self.extract(data, expression)
        assert actual == expected, f"断言失败：预期值 '{expected}'，实际值 '{actual}'"

    def assert_contains(self, class_random_str, data: dict, expression: str, expected: any) -> None:
        """断言JSONPath表达式提取的值包含预期值"""
        actual = self.extract(data, expression)
        assert expected in actual, f"断言失败：'{actual}' 不包含 '{expected}'"
