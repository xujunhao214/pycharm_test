import logging
from jsonpath_ng import parse
from typing import Optional, Any, List, Dict, Union


class JsonPathUtils:
    """JSONPath工具类，用于从JSON响应中提取数据（增强日志版）"""

    def __init__(self):
        # 初始化日志，确保日志可追溯
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def extract(self, data: dict, expression: str, default: Any = None, multi_match: bool = False) -> Any:
        """
        使用JSONPath表达式从数据中提取值
        :param data: JSON数据
        :param expression: JSONPath表达式
        :param default: 未找到匹配时的默认值
        :param multi_match: 是否允许多匹配结果
        :return: 单个匹配值、多匹配列表或默认值
        """
        try:
            # 新增日志：打印输入的表达式和数据顶层结构（便于排错）
            self.logger.info(f"开始JSONPath提取 | 表达式: {expression}")
            self.logger.info(f"数据顶层键: {list(data.keys()) if isinstance(data, dict) else '非字典数据'}")

            # 解析表达式并执行匹配
            jsonpath_expr = parse(expression)
            matches = jsonpath_expr.find(data)

            # 处理匹配结果
            if not matches:
                self.logger.warning(f"未找到匹配结果 | 表达式: {expression} | 返回默认值: {default}")
                return default

            if multi_match:
                result = [match.value for match in matches]
                self.logger.info(f"多匹配模式 | 表达式: {expression} | 匹配数量: {len(matches)} | 结果: {result}")
                return result
            else:
                result = matches[0].value
                self.logger.info(f"单匹配模式 | 表达式: {expression} | 结果: {result}")
                return result

        except Exception as e:
            # 捕获所有异常，打印完整堆栈（便于定位语法/数据问题）
            self.logger.error(f"JSONPath解析失败 | 表达式: {expression} | 错误信息: {str(e)}", exc_info=True)
            return default

    def assert_value(self, data: dict, expression: str, expected: any) -> None:
        """断言JSONPath表达式提取的值与预期值相等"""
        actual = self.extract(data, expression)
        assert actual == expected, f"断言失败：表达式={expression} | 预期值='{expected}' | 实际值='{actual}'"

    def assert_contains(self, data: dict, expression: str, expected: any) -> None:
        """断言JSONPath表达式提取的值包含预期值"""
        actual = self.extract(data, expression)
        # 先判断actual是否为可迭代类型（避免非容器类型报错）
        if not isinstance(actual, (str, list, dict, tuple)):
            assert False, f"断言失败：表达式={expression} | 提取值'{actual}'不是可包含类型"
        assert expected in actual, f"断言失败：表达式={expression} | 提取值'{actual}'不包含'{expected}'"
