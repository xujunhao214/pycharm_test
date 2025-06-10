# jsonpath_utils.py
from jsonpath_ng import parse
from typing import Optional, Any, List, Dict, Union


class JsonPathUtils:
    """JSONPath 提取工具类（基于 jsonpath-ng）"""

    @staticmethod
    def extract(
            data: Union[Dict, List],  # 支持字典或列表
            expr: str,
            default: Optional[Any] = None,
            multi_match: bool = False
    ) -> Any:
        """
        从 JSON 数据中提取值

        Args:
            data: 要提取的 JSON 数据（字典或列表）
            expr: JSONPath 表达式（如 "$.data.id"）
            default: 未匹配到时返回的默认值（默认为 None）
            multi_match: 是否返回所有匹配结果（默认返回第一个匹配值）

        Returns:
            匹配到的值（单个或列表），未匹配到返回 default
        """
        try:
            jsonpath_expr = parse(expr)
            matches: List[Any] = jsonpath_expr.find(data)

            if not matches:
                return default

            return matches if multi_match else matches[0].value
        except Exception as e:
            print(f"JSONPath 提取失败: {str(e)}")
            return default
