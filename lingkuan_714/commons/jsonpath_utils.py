from jsonpath_ng import parse

class JsonPathUtils:
    """JSONPath工具类，用于从JSON响应中提取数据"""

    def extract(self, data: dict, expression: str) -> any:
        """使用JSONPath表达式从数据中提取值"""
        jsonpath_expr = parse(expression)
        result = [match.value for match in jsonpath_expr.find(data)]
        if result:
            return result[0] if len(result) == 1 else result
        return None

    def assert_value(self, data: dict, expression: str, expected: any) -> None:
        """断言JSONPath表达式提取的值与预期值相等"""
        actual = self.extract(data, expression)
        assert actual == expected, f"断言失败：预期值 '{expected}'，实际值 '{actual}'"

    def assert_contains(self, data: dict, expression: str, expected: any) -> None:
        """断言JSONPath表达式提取的值包含预期值"""
        actual = self.extract(data, expression)
        assert expected in actual, f"断言失败：'{actual}' 不包含 '{expected}'"