import allure
import logging
import time
import json
import pymysql
from lingkuan_706.VAR.VAR import *
from typing import Dict, Any, List, Optional, Union
from decimal import Decimal
from lingkuan_706.commons.wait_utils import wait_for_condition

logger = logging.getLogger(__name__)


class APITestBase:
    """API测试基础类，封装通用测试方法"""

    def convert_decimal_to_float(self, data: Any) -> Any:
        """递归转换Decimal类型为float"""
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
        """序列化数据为JSON"""
        converted_data = self.convert_decimal_to_float(data)
        try:
            return json.dumps(converted_data, ensure_ascii=False)
        except json.JSONDecodeError as e:
            raise ValueError(f"数据序列化失败: {str(e)}") from e

    def deserialize_data(self, json_str: str) -> Any:
        """反序列化JSON字符串"""
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON反序列化失败: {str(e)}") from e

    def send_post_request(self, logged_session, url, json_data=None, data=None, files=None, sleep_seconds=5):
        """发送POST请求并返回响应"""
        with allure.step(f"发送POST请求到 {url}"):
            if files:
                response = logged_session.post(url, data=data, files=files)
                allure.attach(str(data), "请求表单数据", allure.attachment_type.JSON)
            elif json_data:
                response = logged_session.post(url, json=json_data)
                allure.attach(str(json_data), "请求JSON数据", allure.attachment_type.JSON)
            else:
                response = logged_session.post(url, data=data)
                allure.attach(str(data), "请求表单数据", allure.attachment_type.JSON)

            allure.attach(url, "请求URL", allure.attachment_type.TEXT)
            self._log_response(response)

            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

            return response

    def send_get_request(self, logged_session, url, params=None, sleep_seconds=5):
        """发送GET请求并返回响应"""
        with allure.step(f"发送GET请求到 {url}"):
            response = logged_session.get(url, params=params)
            allure.attach(str(params), "请求参数", allure.attachment_type.JSON)
            self._log_response(response)
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)
            return response

    def send_delete_request(self, logged_session, url, json_data=None, sleep_seconds=5):
        """发送DELETE请求并返回响应"""
        with allure.step(f"发送DELETE请求到 {url}"):
            response = logged_session.delete(url, json=json_data)
            allure.attach(str(json_data), "请求参数", allure.attachment_type.JSON)
            self._log_response(response)
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)
            return response

    def send_put_request(self, logged_session, url, json_data=None, sleep_seconds=5):
        """发送PUT请求并返回响应"""
        with allure.step(f"发送PUT请求到 {url}"):
            response = logged_session.put(url, json=json_data)
            allure.attach(str(json_data), "请求参数", allure.attachment_type.JSON)
            self._log_response(response)
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)
            return response

    def _log_response(self, response):
        """记录响应日志"""
        logger.info(f"[{DATETIME_NOW}] 响应状态码: {response.status_code}")
        logger.info(f"[{DATETIME_NOW}] 响应内容: {response.text}")
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

    def query_database(self, db_transaction: pymysql.connections.Connection,
                       sql: str,
                       params: tuple = (),
                       order_by: str = "",  # 可选排序，不再强制添加
                       convert_decimal: bool = True) -> List[Dict[str, Any]]:
        """
        基础数据库查询方法（不含自动时间范围）
        :param db_transaction: 数据库连接事务
        :param sql: SQL查询语句
        :param params: SQL参数（防止注入）
        :param order_by: 排序语句（如"create_time DESC"，为空则不排序）
        :param convert_decimal: 是否将Decimal类型转为float
        :return: 查询结果列表
        """
        sql_upper = sql.upper()
        final_sql = sql

        # 处理排序（仅当用户指定且SQL中无ORDER BY时）
        if order_by and "ORDER BY" not in sql_upper:
            final_sql += f" ORDER BY {order_by}"
        elif order_by:
            logging.warning(f"SQL已包含ORDER BY，忽略传入的排序: {order_by}")

        with db_transaction.cursor() as cursor:
            # 关键修改：直接在日志中格式化参数值
            logging.info(f"[{DATETIME_NOW}] 执行SQL: {final_sql}，参数: {params}")
            try:
                cursor.execute(final_sql, params)
                result = cursor.fetchall()
                logging.info(f"查询成功，结果数量: {len(result)}")
            except Exception as e:
                logging.error(f"SQL执行失败: {str(e)}", exc_info=True)
                raise

            # 转换Decimal类型（避免JSON序列化问题）
            if convert_decimal and result:
                result = self.convert_decimal_to_float(result)

            logging.info(f"[{DATETIME_NOW}] 查询结果（{len(result)}条）: {result}")
            return result

    def query_database_with_time(self, db_transaction: pymysql.connections.Connection,
                                 sql: str,
                                 params: tuple = (),
                                 time_field: str = "create_time",  # 时间字段名
                                 time_range_minutes: int = 5,  # 时间范围（分钟）
                                 order_by: str = "create_time DESC",
                                 convert_decimal: bool = True) -> List[Dict[str, Any]]:
        """
        带时间范围的数据库查询（手动指定时间字段和范围）
        :param time_field: 时间过滤字段（如"create_time"）
        :param time_range_minutes: 时间范围（前后N分钟）
        """
        sql_upper = sql.upper()
        final_sql = sql
        final_params = list(params)  # 转为列表方便追加

        # 拼接时间条件
        time_condition = (
            f" {time_field} BETWEEN NOW() - INTERVAL %s MINUTE "
            f"AND NOW() + INTERVAL %s MINUTE "
        )

        # 处理WHERE子句
        if "WHERE" in sql_upper:
            final_sql += f" AND {time_condition}"
        else:
            final_sql += f" WHERE {time_condition}"

        # 追加时间参数（前后各N分钟）
        final_params.extend([time_range_minutes, time_range_minutes])

        # 调用基础查询方法
        return self.query_database(
            db_transaction=db_transaction,
            sql=final_sql,
            params=tuple(final_params),
            order_by=order_by,
            convert_decimal=convert_decimal
        )

    def convert_decimal_to_float(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """将查询结果中的Decimal类型转为float（避免JSON序列化失败）"""
        converted = []
        for row in data:
            converted_row = {}
            for key, value in row.items():
                if isinstance(value, Decimal):
                    converted_row[key] = float(value)
                else:
                    converted_row[key] = value
            converted.append(converted_row)
        return converted

    def wait_for_database_deletion(self, db_transaction: pymysql.connections.Connection,
                                   sql: str,
                                   params: tuple = (),
                                   time_field: Optional[str] = None,  # 可选时间字段
                                   time_range: int = 1,  # 时间范围（分钟）
                                   order_by: str = "create_time DESC",
                                   timeout: int = 60,  # 超时时间（秒）
                                   poll_interval: int = 2) -> None:
        """
        轮询等待数据库记录被删除（即查询结果为空）
        :param timeout: 最大等待时间
        :param poll_interval: 轮询间隔（秒）
        """
        import time
        start_time = time.time()

        while time.time() - start_time < timeout:
            # 每次查询前刷新事务，确保能看到最新数据
            db_transaction.commit()

            # 根据是否需要时间范围选择查询方法
            if time_field:
                result = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field=time_field,
                    time_range_minutes=time_range,
                    order_by=order_by
                )
            else:
                result = self.query_database(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    order_by=order_by
                )

            # 修改判断逻辑：如果结果为空，表示数据已删除
            if not result:
                logging.info(f"[{DATETIME_NOW}] 删除成功（耗时{time.time() - start_time:.1f}秒），记录已不存在")
                return

            elapsed = time.time() - start_time
            logging.info(
                f"[{DATETIME_NOW}] 记录仍存在（已等待{elapsed:.1f}秒，剩余{timeout - elapsed:.1f}秒），结果: {result}")
            time.sleep(poll_interval)

        # 超时后最后一次查询
        db_transaction.commit()
        final_result = self.query_database_with_time(
            db_transaction=db_transaction,
            sql=sql,
            params=params,
            time_field=time_field,
            time_range_minutes=time_range,
            order_by=order_by
        ) if time_field else self.query_database(
            db_transaction=db_transaction,
            sql=sql,
            params=params,
            order_by=order_by
        )

        raise TimeoutError(
            f"等待超时（{timeout}秒），记录仍然存在。\n"
            f"SQL: {sql}\n"
            f"参数: {params}\n"
            f"最终结果: {final_result}"
        )

    def wait_for_database_record(self, db_transaction: pymysql.connections.Connection,
                                 sql: str,
                                 params: tuple = (),
                                 time_field: Optional[str] = None,  # 可选时间字段
                                 time_range: int = 1,  # 时间范围（分钟）
                                 order_by: str = "create_time DESC",
                                 timeout: int = 60,  # 超时时间（秒）
                                 poll_interval: int = 2) -> List[Dict[str, Any]]:
        """
        轮询等待数据库记录出现
        :param timeout: 最大等待时间
        :param poll_interval: 轮询间隔（秒）
        """
        import time
        start_time = time.time()

        while time.time() - start_time < timeout:
            # 每次查询前刷新事务，确保能看到最新数据
            db_transaction.commit()

            # 根据是否需要时间范围选择查询方法
            if time_field:
                result = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field=time_field,
                    time_range_minutes=time_range,
                    order_by=order_by
                )
            else:
                result = self.query_database(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    order_by=order_by
                )

            if result:
                logging.info(f"[{DATETIME_NOW}] 等待成功（耗时{time.time() - start_time:.1f}秒），结果: {result}")
                return result

            elapsed = time.time() - start_time
            logging.info(f"[{DATETIME_NOW}] 未查询到记录（已等待{elapsed:.1f}秒，剩余{timeout - elapsed:.1f}秒）")
            time.sleep(poll_interval)

        # 超时后最后一次查询
        db_transaction.commit()
        final_result = self.query_database_with_time(
            db_transaction=db_transaction,
            sql=sql,
            params=params,
            time_field=time_field,
            time_range_minutes=time_range,
            order_by=order_by
        ) if time_field else self.query_database(
            db_transaction=db_transaction,
            sql=sql,
            params=params,
            order_by=order_by
        )

        raise TimeoutError(
            f"等待超时（{timeout}秒），未查询到记录。\n"
            f"SQL: {sql}\n"
            f"参数: {params}\n"
            f"最终结果: {final_result}"
        )

    def wait_for_api_condition(self, logged_session, method, url, params=None, json_data=None,
                               expected_condition=None, timeout=30, poll_interval=2):
        """等待API响应满足特定条件"""
        if expected_condition is None:
            raise ValueError("必须提供expected_condition函数")

        def check_api():
            if method.upper() == 'GET':
                response = logged_session.get(url, params=params)
            elif method.upper() == 'POST':
                response = logged_session.post(url, json=json_data)
            elif method.upper() == 'PUT':
                response = logged_session.put(url, json=json_data)
            elif method.upper() == 'DELETE':
                response = logged_session.delete(url, json=json_data)
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
