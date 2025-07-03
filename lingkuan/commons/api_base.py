import allure
import logging
import time
import json
from typing import Dict, Any, List, Optional, Union
from decimal import Decimal
from lingkuan_703.commons.wait_utils import wait_for_condition

logger = logging.getLogger(__name__)


class APITestBase:
    """API测试基础类，封装通用测试方法"""

    def convert_decimal_to_float(self, data: Any) -> Any:
        """
        递归转换Decimal类型为float，支持处理列表、字典等复杂结构

        Args:
            data: 包含Decimal类型的原始数据

        Returns:
            转换后的新数据（Decimal已转为float）
        """
        if isinstance(data, Decimal):
            return float(data)
        elif isinstance(data, list):
            return [self.convert_decimal_to_float(item) for item in data]
        elif isinstance(data, dict):
            return {key: self.convert_decimal_to_float(value) for key, value in data.items()}
        elif isinstance(data, (tuple, set)):
            return type(data)(self.convert_decimal_to_float(item) for item in data)
        return data

    def serialize_data(self, data: Any) -> str:
        """
        序列化数据为JSON，自动处理Decimal类型

        Args:
            data: 要序列化的数据

        Returns:
            JSON格式的字符串

        Raises:
            ValueError: 数据无法序列化时抛出
        """
        # 先转换Decimal类型
        converted_data = self.convert_decimal_to_float(data)
        try:
            return json.dumps(converted_data, ensure_ascii=False)
        except json.JSONDecodeError as e:
            raise ValueError(f"数据序列化失败: {str(e)}") from e

    def deserialize_data(self, json_str: str) -> Any:
        """
        反序列化JSON字符串，返回原始数据类型

        Args:
            json_str: JSON格式的字符串

        Returns:
            反序列化后的原始数据
        """
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON反序列化失败: {str(e)}") from e

    def send_post_request(self, api_session, url, json_data=None, data=None, files=None, sleep_seconds=5):
        """
        发送POST请求并返回响应，支持三种类型的请求：
        1. JSON请求（json_data参数）
        2. 表单请求（data参数）
        3. 文件上传请求（files参数+data参数）
        """
        with allure.step(f"发送POST请求到 {url}"):
            # 根据参数决定请求类型
            if files:
                # 文件上传请求，使用form-data格式
                response = api_session.post(url, data=data, files=files)
                allure.attach(str(data), "请求表单数据", allure.attachment_type.JSON)
            elif json_data:
                # JSON请求
                response = api_session.post(url, json=json_data)
                allure.attach(str(json_data), "请求JSON数据", allure.attachment_type.JSON)
            else:
                # 普通表单请求
                response = api_session.post(url, data=data)
                allure.attach(str(data), "请求表单数据", allure.attachment_type.JSON)

            # 记录请求URL和响应信息
            allure.attach(url, "请求URL", allure.attachment_type.TEXT)
            self._log_response(response)

            # 等待指定秒数（用于测试间隔）
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

            return response

    def send_get_request(self, api_session, url, params=None, sleep_seconds=5):
        """发送GET请求并返回响应"""
        with allure.step(f"发送GET请求到 {url}"):
            response = api_session.get(url, params=params)
            allure.attach(str(params), "请求参数", allure.attachment_type.JSON)
            self._log_response(response)
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)
            return response

    def send_delete_request(self, api_session, url, json_data=None, sleep_seconds=5):
        """发送DELETE请求并返回响应"""
        with allure.step(f"发送DELETE请求到 {url}"):
            response = api_session.delete(url, json=json_data)
            allure.attach(str(json_data), "请求参数", allure.attachment_type.JSON)
            self._log_response(response)
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)
            return response

    def send_put_request(self, api_session, url, json_data=None, sleep_seconds=5):
        """发送PUT请求并返回响应"""
        with allure.step(f"发送PUT请求到 {url}"):
            response = api_session.put(url, json=json_data)
            allure.attach(str(json_data), "请求参数", allure.attachment_type.JSON)
            self._log_response(response)
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)
            return response

    def _log_response(self, response):
        """记录响应日志"""
        logger.info(f"响应状态码: {response.status_code}")
        logger.info(f"响应内容: {response.text}")
        allure.attach(
            f"状态码: {response.status_code}\n内容: {response.text}",
            "响应结果",
            allure.attachment_type.TEXT
        )

    def assert_response_status(self, response, expected_status, error_msg):
        """断言响应状态码"""
        assert response.status_code == expected_status, (
            f"{error_msg}\n"
            f"实际状态码: {response.status_code}\n"
            f"响应内容: {response.text}"
        )

    def assert_json_value(self, response, json_path, expected_value, error_msg):
        """断言JSON路径对应的值"""
        # 假设response对象有extract_jsonpath方法
        actual_value = response.extract_jsonpath(json_path)
        assert actual_value == expected_value, (
            f"{error_msg}\n"
            f"实际值: {actual_value}\n"
            f"期望值: {expected_value}"
        )

    def query_database(self, db_transaction, sql, params, time_field: Optional[str] = None,
                       time_range_minutes: int = 3, order_by: str = "create_time DESC",
                       convert_decimal: bool = True):
        """
        统一的数据库查询方法，支持添加时间范围过滤和排序条件

        Args:
            db_transaction: 数据库事务对象
            sql: SQL查询语句
            params: 查询参数
            time_field: 时间字段名，若提供则自动添加时间范围条件
            time_range_minutes: 时间范围（分钟），默认±3分钟
            order_by: 排序条件，默认为按create_time降序排列
            convert_decimal: 是否将Decimal类型转换为float，默认为True
        """
        # 保存原始SQL的大小写状态用于判断
        sql_upper = sql.upper()

        # 如果指定了时间字段，则动态添加时间范围条件
        if time_field:
            # 检查SQL中是否已包含WHERE子句
            if "WHERE" in sql_upper:
                # 已有WHERE子句，添加AND条件
                sql += f" AND {time_field} BETWEEN NOW() - INTERVAL %s MINUTE AND NOW() + INTERVAL %s MINUTE"
                params = params + (time_range_minutes, time_range_minutes)
            else:
                # 没有WHERE子句，添加WHERE条件
                sql += f" WHERE {time_field} BETWEEN NOW() - INTERVAL %s MINUTE AND NOW() + INTERVAL %s MINUTE"
                params = params + (time_range_minutes, time_range_minutes)

        # 添加排序条件（处理不同情况）
        if order_by:
            # 检查SQL中是否已包含ORDER BY子句
            if "ORDER BY" in sql_upper:
                # 已有ORDER BY子句，不重复添加
                logger.warning(f"SQL中已包含ORDER BY子句，使用原始排序: {sql}")
            else:
                # 没有ORDER BY子句，添加排序条件
                sql += f" ORDER BY {order_by}"

        with db_transaction.cursor() as cursor:
            logger.info(f"执行SQL查询: {sql}", extra={"params": params})
            cursor.execute(sql, params)
            result = cursor.fetchall()

            # 转换Decimal类型为float
            if convert_decimal and result:
                result = self.convert_decimal_to_float(result)

            logger.info(f"数据库查询结果: {result}", extra={"sql": sql, "params": params})
            return result

    def query_database_with_time(self, db_transaction, sql, params, time_field=None, time_range=3,
                                 order_by="create_time DESC", convert_decimal: bool = True):
        """带时间范围的数据库查询 - 与query_database功能类似，保留以保持兼容性"""
        return self.query_database(
            db_transaction, sql, params, time_field, time_range, order_by, convert_decimal
        )

    def wait_for_database_record(self, db_transaction, sql, params, time_field=None, time_range=3,
                                 order_by="create_time DESC", timeout=30, poll_interval=2,
                                 convert_decimal: bool = True):
        """
        等待数据库记录出现，支持时间范围

        Args:
            db_transaction: 数据库事务对象
            sql: SQL查询语句
            params: 查询参数
            time_field: 时间字段名
            time_range: 时间范围（分钟）
            order_by: 排序条件
            timeout: 超时时间（秒）
            poll_interval: 轮询间隔（秒）
            convert_decimal: 是否将Decimal类型转换为float，默认为True
        """

        def check_db():
            return self.query_database(
                db_transaction, sql, params, time_field, time_range, order_by, convert_decimal
            )

        return wait_for_condition(
            condition=check_db,
            timeout=timeout,
            poll_interval=poll_interval,
            error_message=f"数据库查询超时，未找到记录 (SQL: {sql}, PARAMS: {params})",
            step_title="等待数据库记录出现"
        )

    def wait_for_api_condition(self, api_session, method, url, params=None, json_data=None,
                               expected_condition=None, timeout=30, poll_interval=2):
        """
        等待API响应满足特定条件

        Args:
            api_session: API会话对象
            method: HTTP方法 ('GET', 'POST', 'PUT', 'DELETE')
            url: 请求URL
            params: GET请求参数
            json_data: POST/PUT请求的JSON数据
            expected_condition: 预期条件函数，接收响应对象并返回布尔值
            timeout: 超时时间（秒）
            poll_interval: 轮询间隔（秒）
        """
        if expected_condition is None:
            raise ValueError("必须提供expected_condition函数")

        def check_api():
            if method.upper() == 'GET':
                response = api_session.get(url, params=params)
            elif method.upper() == 'POST':
                response = api_session.post(url, json=json_data)
            elif method.upper() == 'PUT':
                response = api_session.put(url, json=json_data)
            elif method.upper() == 'DELETE':
                response = api_session.delete(url, json=json_data)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")

            self._log_response(response)
            return expected_condition(response)

        return wait_for_condition(
            condition=check_api,
            timeout=timeout,
            poll_interval=poll_interval,
            error_message=f"API条件验证超时 (URL: {url})",
            step_title="等待API条件满足"
        )

    def assert_list_equal_ignore_order(self, list1, list2, error_msg="列表元素不相等（忽略顺序）"):
        """断言两个列表元素相同（忽略顺序）"""
        from collections import Counter
        assert Counter(list1) == Counter(list2), error_msg

    def assert_dict_subset(self, subset_dict, full_dict, error_msg="子字典不匹配"):
        """断言一个字典是另一个字典的子集"""
        for key, value in subset_dict.items():
            assert key in full_dict, f"{error_msg}: 键 '{key}' 不存在"
            assert full_dict[key] == value, f"{error_msg}: 键 '{key}' 的值不匹配（{full_dict[key]} != {value}）"

    def get_batch_data_by_index(self, var_manager, var_name, index):
        """从批量数据中获取指定索引的数据"""
        data_list = var_manager.get_variable(var_name)
        if not isinstance(data_list, list):
            raise ValueError(f"{var_name}不是列表类型")

        if index < 0 or index >= len(data_list):
            raise IndexError(f"索引 {index} 超出了 {var_name} 的范围")

        return data_list[index]
