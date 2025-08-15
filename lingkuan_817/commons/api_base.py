import allure
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
import datetime
from decimal import Decimal  # 确保导入Decimal
import json
import pymysql
from requests.exceptions import (
    RequestException, ConnectionError, Timeout,
    HTTPError, SSLError
)

from lingkuan_817.VAR.VAR import *
from lingkuan_817.commons.wait_utils import wait_for_condition

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class APITestBase:
    """API测试基础类，封装通用测试方法（增强版）"""

    def convert_decimal_to_float(self, data: Any) -> Any:
        """
        递归转换Decimal类型为float，同时处理datetime和date类型为字符串
        解决JSON序列化问题
        """
        # 处理Decimal类型
        if isinstance(data, Decimal):
            return float(data)

        # 处理datetime类型（使用完整模块路径）
        elif isinstance(data, datetime.datetime):  # 明确指定是datetime模块下的datetime类
            return data.strftime("%Y-%m-%d %H:%M:%S")

        # 处理date类型（使用完整模块路径）
        elif isinstance(data, datetime.date):  # 明确指定是datetime模块下的date类
            return data.strftime("%Y-%m-%d")

        # 递归处理列表
        elif isinstance(data, list):
            return [self.convert_decimal_to_float(item) for item in data]

        # 递归处理字典
        elif isinstance(data, dict):
            return {key: self.convert_decimal_to_float(value) for key, value in data.items()}

        # 处理元组和集合
        elif isinstance(data, (tuple, set)):
            return type(data)(self.convert_decimal_to_float(item) for item in data)

        # 其他类型不处理
        else:
            return data

    def serialize_data(self, data: Any) -> str:
        """序列化数据为JSON（包含datetime处理）"""
        converted_data = self.convert_decimal_to_float(data)
        try:
            return json.dumps(converted_data, ensure_ascii=False)
        except json.JSONDecodeError as e:
            logger.error(f"[{DATETIME_NOW}] 数据序列化失败: {str(e)} | 原始数据: {converted_data}")
            raise ValueError(f"数据序列化失败: {str(e)}") from e

    def deserialize_data(self, json_str: str) -> Any:
        """反序列化JSON字符串"""
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"[{DATETIME_NOW}] JSON反序列化失败: {str(e)} | 原始字符串: {json_str[:500]}")
            raise ValueError(f"JSON反序列化失败: {str(e)}") from e

    def send_post_request(self, logged_session, url, json_data=None, data=None, files=None,
                          sleep_seconds=SLEEP_SECONDS):
        """发送POST请求（增强异常捕获）"""
        with allure.step(f"发送POST请求到 {url}"):
            try:
                if files:
                    response = logged_session.post(url, data=data, files=files)
                    allure.attach(str(data), "请求表单数据", allure.attachment_type.JSON)
                    logger.info(f"[{DATETIME_NOW}] POST请求（带文件）: {url} | 表单数据: {data}")
                elif json_data:
                    response = logged_session.post(url, json=json_data)
                    allure.attach(str(json_data), "请求JSON数据", allure.attachment_type.JSON)
                    logger.info(f"[{DATETIME_NOW}] POST请求（JSON）: {url} | 数据: {json_data}")
                else:
                    response = logged_session.post(url, data=data)
                    allure.attach(str(data), "请求表单数据", allure.attachment_type.JSON)
                    logger.info(f"[{DATETIME_NOW}] POST请求（表单）: {url} | 数据: {data}")

                allure.attach(url, "请求URL", allure.attachment_type.TEXT)
                self._log_response(response)

                if sleep_seconds > 0:
                    logger.info(f"[{DATETIME_NOW}] 请求后等待 {sleep_seconds} 秒")
                    time.sleep(sleep_seconds)

                return response

            except SSLError as e:
                error_msg = f"{DATETIME_NOW}] POST请求SSL验证失败: {str(e)} | URL: {url}"
                logger.error(error_msg, exc_info=True)
                allure.attach(error_msg, "请求异常", allure.attachment_type.TEXT)
                raise
            except ConnectionError as e:
                error_msg = f"{DATETIME_NOW}] POST请求连接异常（可能包含DNS解析失败）: {str(e)} | URL: {url}"
                logger.error(error_msg, exc_info=True)
                allure.attach(error_msg, "请求异常", allure.attachment_type.TEXT)
                raise
            except Timeout as e:
                error_msg = f"[{DATETIME_NOW}] POST请求超时: {str(e)} | URL: {url}"
                logger.error(error_msg, exc_info=True)
                allure.attach(error_msg, "请求异常", allure.attachment_type.TEXT)
                raise
            except RequestException as e:
                error_msg = f"{DATETIME_NOW}] POST请求异常: {str(e)} | URL: {url}"
                logger.error(error_msg, exc_info=True)
                allure.attach(error_msg, "请求异常", allure.attachment_type.TEXT)
                raise

    def send_get_request(self, logged_session, url, params=None, sleep_seconds=SLEEP_SECONDS):
        """发送GET请求（增强异常捕获）"""
        with allure.step(f"发送GET请求到 {url}"):
            try:
                logger.info(f"[{DATETIME_NOW}] GET请求: {url} | 参数: {params}")
                response = logged_session.get(url, params=params)
                allure.attach(str(params), "请求参数", allure.attachment_type.JSON)
                self._log_response(response)

                if sleep_seconds > 0:
                    logger.info(f"[{DATETIME_NOW}] 请求后等待 {sleep_seconds} 秒")
                    time.sleep(sleep_seconds)
                return response

            except SSLError as e:
                error_msg = f"{DATETIME_NOW}] GET请求SSL验证失败: {str(e)} | URL: {url}"
                logger.error(error_msg, exc_info=True)
                allure.attach(error_msg, "请求异常", allure.attachment_type.TEXT)
                raise
            except ConnectionError as e:
                error_msg = f"{DATETIME_NOW}] GET请求连接异常（可能包含DNS解析失败）: {str(e)} | URL: {url}"
                logger.error(error_msg, exc_info=True)
                allure.attach(error_msg, "请求异常", allure.attachment_type.TEXT)
                raise
            except Timeout as e:
                error_msg = f"{DATETIME_NOW}] GET请求超时: {str(e)} | URL: {url}"
                logger.error(error_msg, exc_info=True)
                allure.attach(error_msg, "请求异常", allure.attachment_type.TEXT)
                raise
            except RequestException as e:
                error_msg = f"{DATETIME_NOW}] GET请求异常: {str(e)} | URL: {url}"
                logger.error(error_msg, exc_info=True)
                allure.attach(error_msg, "请求异常", allure.attachment_type.TEXT)
                raise

    def send_delete_request(self, logged_session, url, json_data=None, sleep_seconds=SLEEP_SECONDS):
        """发送DELETE请求（增强异常捕获）"""
        with allure.step(f"发送DELETE请求到 {url}"):
            try:
                logger.info(f"[{DATETIME_NOW}] DELETE请求: {url} | 数据: {json_data}")
                response = logged_session.delete(url, json=json_data)
                allure.attach(str(json_data), "请求参数", allure.attachment_type.JSON)
                self._log_response(response)

                if sleep_seconds > 0:
                    time.sleep(sleep_seconds)
                return response

            except SSLError as e:
                error_msg = f"{DATETIME_NOW}] DELETE请求SSL验证失败: {str(e)} | URL: {url}"
                logger.error(error_msg, exc_info=True)
                allure.attach(error_msg, "请求异常", allure.attachment_type.TEXT)
                raise
            except ConnectionError as e:
                error_msg = f"{DATETIME_NOW}] DELETE请求连接异常（可能包含DNS解析失败）: {str(e)} | URL: {url}"
                logger.error(error_msg, exc_info=True)
                allure.attach(error_msg, "请求异常", allure.attachment_type.TEXT)
                raise
            except Timeout as e:
                error_msg = f"{DATETIME_NOW}] DELETE请求超时: {str(e)} | URL: {url}"
                logger.error(error_msg, exc_info=True)
                allure.attach(error_msg, "请求异常", allure.attachment_type.TEXT)
                raise
            except RequestException as e:
                error_msg = f"{DATETIME_NOW}] DELETE请求异常: {str(e)} | URL: {url}"
                logger.error(error_msg, exc_info=True)
                allure.attach(error_msg, "请求异常", allure.attachment_type.TEXT)
                raise

    def send_put_request(self, logged_session, url, json_data=None, sleep_seconds=SLEEP_SECONDS):
        """发送PUT请求（增强异常捕获）"""
        with allure.step(f"发送PUT请求到 {url}"):
            try:
                logger.info(f"[{DATETIME_NOW}] PUT请求: {url} | 数据: {json_data}")
                response = logged_session.put(url, json=json_data)
                allure.attach(str(json_data), "请求参数", allure.attachment_type.JSON)
                self._log_response(response)

                if sleep_seconds > 0:
                    time.sleep(sleep_seconds)
                return response

            except SSLError as e:
                error_msg = f"{DATETIME_NOW}] PUT请求SSL验证失败: {str(e)} | URL: {url}"
                logger.error(error_msg, exc_info=True)
                allure.attach(error_msg, "请求异常", allure.attachment_type.TEXT)
                raise
            except ConnectionError as e:
                error_msg = f"{DATETIME_NOW}] PUT请求连接异常（可能包含DNS解析失败）: {str(e)} | URL: {url}"
                logger.error(error_msg, exc_info=True)
                allure.attach(error_msg, "请求异常", allure.attachment_type.TEXT)
                raise
            except Timeout as e:
                error_msg = f"{DATETIME_NOW}] PUT请求超时: {str(e)} | URL: {url}"
                logger.error(error_msg, exc_info=True)
                allure.attach(error_msg, "请求异常", allure.attachment_type.TEXT)
                raise
            except RequestException as e:
                error_msg = f"{DATETIME_NOW}] PUT请求异常: {str(e)} | URL: {url}"
                logger.error(error_msg, exc_info=True)
                allure.attach(error_msg, "请求异常", allure.attachment_type.TEXT)
                raise

    def _log_response(self, response):
        """记录响应日志（分级日志）"""
        logger.info(f"[{DATETIME_NOW}] 响应状态码: {response.status_code} | URL: {response.url}")
        logger.info(f"[{DATETIME_NOW}] 响应详情: 头信息={response.headers} | 内容={response.text[:1000]}")
        allure.attach(
            f"状态码: {response.status_code}\n内容: {response.text}",
            "响应结果",
            allure.attachment_type.TEXT
        )

    def assert_response_status(self, response, expected_status, error_msg):
        """断言响应状态码（增强错误信息）"""
        assert response.status_code == expected_status, (
            f"{error_msg}\n"
            f"URL: {response.url}\n"
            f"实际状态码: {response.status_code}\n"
            f"响应内容: {response.text[:500]}"
        )

    def assert_values_equal(self, actual_value, expected_value, error_msg):
        """
        断言两个值是否相等，增强错误信息提示
        :param actual_value: 实际获取的值
        :param expected_value: 期望的值
        :param error_msg: 自定义的错误提示前缀信息
        """
        assert actual_value == expected_value, (
            f"{error_msg}\n"
            f"实际值: {actual_value}\n"
            f"期望值: {expected_value}"
        )

    def assert_json_value(self, response, json_path, expected_value, error_msg):
        """断言JSON路径对应的值（增强错误处理）"""
        try:
            actual_value = response.extract_jsonpath(json_path)
            assert actual_value == expected_value, (
                f"{error_msg}\n"
                f"URL: {response.url}\n"
                f"JSON路径: {json_path}\n"
                f"实际值: {actual_value}\n"
                f"期望值: {expected_value}"
            )
        except Exception as e:
            logger.error(f"[{DATETIME_NOW}] JSON断言失败: {str(e)} | 路径: {json_path} | 响应: {response.text[:500]}")
            raise

    def query_database(self, db_transaction: pymysql.connections.Connection,
                       sql: str,
                       params: tuple = (),
                       order_by: str = "create_time DESC",
                       convert_decimal: bool = True,
                       dictionary_cursor: bool = True) -> List[Dict[str, Any]]:
        """
        基础数据库查询（增强异常处理和类型转换）

        Args:
            db_transaction: 数据库连接对象
            sql: SQL查询语句
            params: 查询参数
            order_by: 排序语句（会自动添加到SQL末尾）
            convert_decimal: 是否将Decimal类型转换为float
            dictionary_cursor: 是否使用字典格式返回结果
        """
        sql_upper = sql.upper()
        final_sql = sql

        # 处理排序
        if order_by and "ORDER BY" not in sql_upper:
            final_sql += f" ORDER BY {order_by}"
        elif order_by:
            logger.warning(f"[{DATETIME_NOW}] SQL已包含ORDER BY，忽略传入的排序: {order_by}")

        try:
            # 使用字典格式的游标
            cursor_type = pymysql.cursors.DictCursor if dictionary_cursor else None
            with db_transaction.cursor(cursor_type) as cursor:
                logger.info(f"[{DATETIME_NOW}] 执行SQL: {final_sql} | 参数: {params}")
                cursor.execute(final_sql, params)
                result = cursor.fetchall()
                logger.info(f"[{DATETIME_NOW}] 查询成功，结果数量: {len(result)} | SQL: {final_sql[:200]}")

                # 处理数据类型转换
                if result:
                    # 转换Decimal类型（如果需要）
                    if convert_decimal:
                        result = self.convert_decimal_to_float(result)

                    # 转换日期类型
                    result = self._convert_date_types(result)

                # 安全地记录查询结果（限制长度）
                try:
                    result_preview = json.dumps(result, ensure_ascii=False)[:1000]
                except Exception as e:
                    result_preview = f"无法序列化完整结果: {str(e)}"
                logger.info(f"[{DATETIME_NOW}] 查询结果: {result_preview}")

                return result

        except pymysql.Error as e:
            error_msg = (
                f"[{DATETIME_NOW}] 数据库错误 (错误码: {e.args[0]}): {str(e)} | "
                f"SQL: {final_sql[:200]} | 参数: {params}"
            )
            logger.error(error_msg, exc_info=True)
            raise

        except Exception as e:
            error_msg = f"[{DATETIME_NOW}] 未知异常: {str(e)} | SQL: {final_sql[:200]}"
            logger.error(error_msg, exc_info=True)
            raise

    def _convert_date_types(self, result: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """将结果中的日期和时间类型转换为字符串"""

        def convert_value(value):
            # 使用datetime模块的完整路径访问类型（与convert_decimal_to_float保持一致）
            if isinstance(value, datetime.datetime):  # 修正：明确是datetime模块下的datetime类
                return value.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(value, datetime.date):  # 修正：明确是datetime模块下的date类
                return value.strftime("%Y-%m-%d")
            return value

        return [{k: convert_value(v) for k, v in row.items()} for row in result]

    def query_database_with_time(self, db_transaction: pymysql.connections.Connection,
                                 sql: str,
                                 params: tuple = (),
                                 time_field: str = "create_time",
                                 time_range_minutes: int = 5,
                                 order_by: str = "create_time DESC",
                                 convert_decimal: bool = True) -> List[Dict[str, Any]]:
        """带时间范围的数据库查询（复用增强的query_database）"""
        sql_upper = sql.upper()
        final_sql = sql
        final_params = list(params)

        # 拼接时间条件
        time_condition = (
            f" {time_field} BETWEEN NOW() - INTERVAL %s MINUTE "
            f"AND NOW() + INTERVAL %s MINUTE "
        )

        if "WHERE" in sql_upper:
            final_sql += f" AND {time_condition}"
        else:
            final_sql += f" WHERE {time_condition}"
        final_params.extend([time_range_minutes, time_range_minutes])

        # 调用增强的query_database
        return self.query_database(
            db_transaction=db_transaction,
            sql=final_sql,
            params=tuple(final_params),
            order_by=order_by,
            convert_decimal=convert_decimal
        )

    def wait_for_database_deletion(self, db_transaction: pymysql.connections.Connection,
                                   sql: str,
                                   params: tuple = (),
                                   time_field: Optional[str] = None,
                                   time_range: int = MYSQL_TIME,
                                   order_by: str = "create_time DESC",
                                   timeout: int = DELETE_WAIT_TIMEOUT,
                                   poll_interval: int = POLL_INTERVAL) -> None:
        """轮询等待数据库记录删除（增强日志）"""
        import time
        start_time = time.time()
        logger.info(f"[{DATETIME_NOW}] 开始等待数据库记录删除 | SQL: {sql[:200]} | 超时: {timeout}秒")

        while time.time() - start_time < timeout:
            try:
                db_transaction.commit()  # 刷新事务

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

                if not result:
                    logger.info(f"[{DATETIME_NOW}] 删除成功（耗时{time.time() - start_time:.1f}秒）| SQL: {sql[:200]}")
                    return

                elapsed = time.time() - start_time
                logger.info(
                    f"[{DATETIME_NOW}] 记录仍存在（已等待{elapsed:.1f}秒）| 剩余时间: {timeout - elapsed:.1f}秒 | 结果数: {len(result)}")
                time.sleep(poll_interval)

            except Exception as e:
                logger.warning(f"[{DATETIME_NOW}] 轮询查询异常: {str(e)} | 继续等待...")
                time.sleep(poll_interval)

        # 超时处理
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
            f"最终结果数: {len(final_result)}"
        )

    def wait_for_database_record(
            self,
            db_transaction: pymysql.connections.Connection,
            sql: str,
            params: tuple = (),
            time_field: Optional[str] = None,
            time_range: int = MYSQL_TIME,
            order_by: str = "create_time DESC",
            timeout: int = WAIT_TIMEOUT,
            poll_interval: int = POLL_INTERVAL,
            stable_period: int = STBLE_PERIOD
    ) -> List[Dict[str, Any]]:
        """
        轮询等待数据库记录出现（等待数据稳定）
        """
        import time
        start_time = time.time()
        last_result = None
        stable_start_time = None
        has_data = False  # 标记是否查询到过数据

        logger.info(
            f"[{DATETIME_NOW}] 开始等待数据库记录稳定 | "
            f"SQL: {sql[:200]} | "
            f"超时: {timeout}秒 | "
            f"稳定期: {stable_period}秒"
        )

        while time.time() - start_time < timeout:
            try:
                db_transaction.commit()  # 刷新事务
                result = self._execute_query(
                    db_transaction, sql, params, time_field, order_by, time_range
                )

                # 检查是否有数据
                if len(result) > 0:
                    has_data = True
                    # 判断结果是否稳定（数量和内容都不变）
                    if self._is_result_stable(result, last_result):
                        if stable_start_time is None:
                            stable_start_time = time.time()
                            logger.debug(f"[{DATETIME_NOW}] 数据首次稳定，开始计时")
                        elif time.time() - stable_start_time >= stable_period:
                            logger.info(
                                f"[{DATETIME_NOW}] 数据已稳定{stable_period}秒（耗时{time.time() - start_time:.1f}秒）| "
                                f"结果数: {len(result)}"
                            )
                            return result
                    else:
                        stable_start_time = None  # 结果变化，重置稳定计时器
                        logger.debug(f"[{DATETIME_NOW}] 数据仍在变化，重置稳定计时器")
                else:
                    # 结果为空，重置稳定计时器
                    stable_start_time = None
                    has_data = False
                    logger.debug(f"[{DATETIME_NOW}] 查询结果为空，继续等待")

                last_result = result
                elapsed = time.time() - start_time
                logger.debug(
                    f"[{DATETIME_NOW}] 等待数据稳定（已等待{elapsed:.1f}秒）| "
                    f"当前结果数: {len(result)} | "
                    f"稳定时间: {time.time() - stable_start_time if stable_start_time else 0:.1f}/{stable_period}秒"
                )
                time.sleep(poll_interval)

            except Exception as e:
                logger.warning(f"[{DATETIME_NOW}] 轮询查询异常: {str(e)} | 继续等待...")
                time.sleep(poll_interval)

        # 超时处理
        final_result = self._execute_query(
            db_transaction, sql, params, time_field, order_by, time_range
        )

        if len(final_result) == 0:
            raise TimeoutError(
                f"等待超时（{timeout}秒），未查询到任何数据。\n"
                f"SQL: {sql}\n"
                f"参数: {params}"
            )
        else:
            raise TimeoutError(
                f"等待超时（{timeout}秒），数据未在{stable_period}秒内保持稳定。\n"
                f"SQL: {sql}\n"
                f"参数: {params}\n"
                f"最终结果数: {len(final_result)}\n"
                f"最终结果: {json.dumps(self._simplify_result(final_result[:3]), ensure_ascii=False)}..."
            )

    def _execute_query(
            self,
            db_transaction: pymysql.connections.Connection,
            sql: str,
            params: tuple,
            time_field: Optional[str],
            order_by: str,
            time_range: int
    ) -> List[Dict[str, Any]]:
        """执行数据库查询的辅助方法（避免代码重复）"""
        if time_field:
            return self.query_database_with_time(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field=time_field,
                time_range_minutes=time_range,
                order_by=order_by
            )
        else:
            return self.query_database(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                order_by=order_by
            )

    def wait_for_database_record_with_timezone(
            self,
            db_transaction: pymysql.connections.Connection,
            sql: str,
            params: tuple = (),
            time_field: Optional[str] = None,
            time_range: int = MYSQL_TIME,
            order_by: str = "create_time DESC",
            timeout: int = WAIT_TIMEOUT,
            poll_interval: int = POLL_INTERVAL,
            stable_period: int = STBLE_PERIOD,
            timezone_offset: int = TIMEZONE_OFFSET
    ) -> List[Dict[str, Any]]:
        """
        轮询等待数据库记录出现（等待数据稳定），支持时区转换
        """
        import time
        start_time = time.time()
        last_result = None
        stable_start_time = None
        has_data = False  # 标记是否查询到过数据

        # 生成时区偏移字符串（如 "+08:00"）
        offset_str = f"{timezone_offset:+03d}:00"

        logger.info(
            f"[{DATETIME_NOW}] 开始等待数据库记录稳定（时区偏移: {offset_str}）| "
            f"SQL: {sql[:200]} | "
            f"超时: {timeout}秒 | "
            f"稳定期: {stable_period}秒"
        )

        while time.time() - start_time < timeout:
            try:
                db_transaction.commit()  # 刷新事务
                result = self._execute_query_with_timezone(  # 调用带时区的执行方法
                    db_transaction, sql, params, time_field, order_by, time_range, offset_str
                )

                # 检查是否有数据
                if len(result) > 0:
                    has_data = True
                    # 判断结果是否稳定（数量和内容都不变）
                    if self._is_result_stable(result, last_result):
                        if stable_start_time is None:
                            stable_start_time = time.time()
                            logger.debug(f"[{DATETIME_NOW}] 数据首次稳定，开始计时")
                        elif time.time() - stable_start_time >= stable_period:
                            logger.info(
                                f"[{DATETIME_NOW}] 数据已稳定{stable_period}秒（耗时{time.time() - start_time:.1f}秒）| "
                                f"结果数: {len(result)}"
                            )
                            return result
                    else:
                        stable_start_time = None  # 结果变化，重置稳定计时器
                        logger.debug(f"[{DATETIME_NOW}] 数据仍在变化，重置稳定计时器")
                else:
                    # 结果为空，重置稳定计时器
                    stable_start_time = None
                    has_data = False
                    logger.debug(f"[{DATETIME_NOW}] 查询结果为空，继续等待")

                last_result = result
                elapsed = time.time() - start_time
                logger.debug(
                    f"[{DATETIME_NOW}] 等待数据稳定（已等待{elapsed:.1f}秒）| "
                    f"当前结果数: {len(result)} | "
                    f"稳定时间: {time.time() - stable_start_time if stable_start_time else 0:.1f}/{stable_period}秒"
                )
                time.sleep(poll_interval)

            except Exception as e:
                logger.warning(f"[{DATETIME_NOW}] 轮询查询异常: {str(e)} | 继续等待...")
                time.sleep(poll_interval)

        # 超时处理
        final_result = self._execute_query_with_timezone(  # 调用带时区的执行方法
            db_transaction, sql, params, time_field, order_by, time_range, offset_str
        )

        if len(final_result) == 0:
            raise TimeoutError(
                f"等待超时（{timeout}秒），未查询到任何数据。\n"
                f"SQL: {sql}\n"
                f"参数: {params}"
            )
        else:
            raise TimeoutError(
                f"等待超时（{timeout}秒），数据未在{stable_period}秒内保持稳定。\n"
                f"SQL: {sql}\n"
                f"参数: {params}\n"
                f"最终结果数: {len(final_result)}\n"
                f"最终结果: {json.dumps(self._simplify_result(final_result[:3]), ensure_ascii=False)}..."
            )

    def _execute_query_with_timezone(
            self,
            db_transaction: pymysql.connections.Connection,
            sql: str,
            params: tuple,
            time_field: Optional[str],
            order_by: str,
            time_range: int,
            timezone_offset: str  # 时区偏移字符串（如 "+08:00"）
    ) -> List[Dict[str, Any]]:
        """执行数据库查询的辅助方法（带时区转换）"""
        if time_field:
            # 对时间字段进行时区转换（假设数据库存储的是UTC时间）
            converted_time_field = f"CONVERT_TZ({time_field}, '+00:00', '{timezone_offset}')"

            # 复用原有的带时间范围查询逻辑，但使用转换后的时间字段
            sql_upper = sql.upper()
            final_sql = sql
            final_params = list(params)

            # 拼接时间条件（使用转换后的时间字段）
            time_condition = (
                f" {converted_time_field} BETWEEN NOW() - INTERVAL %s MINUTE "
                f"AND NOW() + INTERVAL %s MINUTE "
            )

            if "WHERE" in sql_upper:
                final_sql += f" AND {time_condition}"
            else:
                final_sql += f" WHERE {time_condition}"
            final_params.extend([time_range, time_range])

            return self.query_database(
                db_transaction=db_transaction,
                sql=final_sql,
                params=tuple(final_params),
                order_by=order_by
            )
        else:
            # 无时间字段时直接查询
            return self.query_database(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                order_by=order_by
            )

    def _is_result_stable(self, current: List[Dict], previous: List[Dict]) -> bool:
        """判断两次查询结果是否稳定（数量和内容都不变）"""
        if previous is None:
            return False  # 首次查询，肯定不稳定

        # 1. 检查记录数量是否相同
        if len(current) != len(previous):
            return False

        # 2. 检查每条记录的关键内容是否相同
        # 注意：这里假设结果有唯一标识字段"id"，根据实际情况调整
        current_map = {item.get('id'): item for item in current}
        previous_map = {item.get('id'): item for item in previous}

        # 如果ID集合不同，说明记录有变化
        if set(current_map.keys()) != set(previous_map.keys()):
            return False

        # 检查每条记录的关键字段是否相同（这里检查所有字段，可优化为只检查关键字段）
        for id, curr_item in current_map.items():
            prev_item = previous_map[id]
            for key in curr_item:
                # 跳过可能变化的字段（如时间戳），根据实际情况调整
                if key in {'create_time', 'update_time', 'response_time'}:
                    continue
                if curr_item[key] != prev_item[key]:
                    return False

        return True

    def _simplify_result(self, results: List[Dict]) -> List[Dict]:
        """简化结果，只保留关键信息用于日志输出"""
        if not results:
            return []

        # 获取第一条记录的字段名，确定哪些是关键字段
        sample = results[0]
        # 保留ID和其他可能的关键字段（根据实际情况调整）
        key_fields = ['id', 'account', 'symbol', 'size', 'create_time']
        key_fields = [f for f in key_fields if f in sample]

        # 如果没有匹配的关键字段，就只取前3个字段
        if not key_fields:
            key_fields = list(sample.keys())[:3]

        return [{k: v for k, v in item.items() if k in key_fields} for item in results]

    def wait_for_api_condition(self, logged_session, method, url, params=None, json_data=None,
                               expected_condition=None, timeout=WAIT_TIMEOUT, poll_interval=POLL_INTERVAL):
        """等待API响应满足特定条件（增强异常处理）"""
        if expected_condition is None:
            raise ValueError("必须提供expected_condition函数")

        def check_api():
            try:
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

            except Exception as e:
                logger.error(f"[{DATETIME_NOW}] API请求异常: {str(e)} | URL: {url}")
                # 返回False继续等待，避免因临时异常导致测试中断
                return False

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

    def assert_data_lists_equal(self, actual, expected, fields_to_compare, tolerance=1e-9):
        # 按统一字段order_no排序（替换原来的ticket）
        actual_sorted = sorted(actual, key=lambda x: x["order_no"])
        expected_sorted = sorted(expected, key=lambda x: x["order_no"])

        # 检查长度
        assert len(actual_sorted) == len(expected_sorted), \
            f"数据长度不一致: actual={len(actual_sorted)}, expected={len(expected_sorted)}"
        logging.info(f"两个数据：{actual_sorted} {expected_sorted}")

        # 逐个字段比较
        for a, e in zip(actual_sorted, expected_sorted):
            for field in fields_to_compare:
                actual_val = a[field]
                expected_val = e[field]

                # 浮点数比较
                if isinstance(actual_val, float) and isinstance(expected_val, float):
                    assert abs(actual_val - expected_val) <= tolerance, \
                        f"字段 {field} 不匹配: actual={actual_val}, expected={expected_val}"
                else:
                    assert actual_val == expected_val, \
                        f"字段 {field} 不匹配: actual={actual_val}, expected={expected_val}"
