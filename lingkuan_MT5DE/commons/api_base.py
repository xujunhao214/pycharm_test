import allure
import logging
import time
import json
import pytest
import math
from typing import List, Dict, Any, Optional, Tuple
import datetime
from decimal import Decimal
import pymysql
import requests
from requests.exceptions import (
    RequestException, ConnectionError, Timeout,
    HTTPError, SSLError
)
from jsonpath_ng import parse
from lingkuan_MT5DE.VAR.VAR import *
from lingkuan_MT5DE.commons.wait_utils import wait_for_condition

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
from enum import Enum


# 定义比较操作枚举，方便调用时清晰表达意图
class CompareOp(Enum):
    EQ = "=="  # 相等
    NE = "!="  # 不相等
    GT = ">"  # 大于
    LT = "<"  # 小于
    GE = ">="  # 大于等于
    LE = "<="  # 小于等于
    IN = "in"  # 包含于（实际值在预期值中）
    NOT_IN = "not in"  # 不包含于


class APITestBase:
    """API测试基础类，封装通用测试方法（Allure分层提示全覆盖：HTTP请求+数据库操作+异常处理）"""

    def convert_decimal_to_float(self, data: Any) -> Any:
        """递归转换Decimal类型为float，处理datetime/date为字符串"""
        if isinstance(data, Decimal):
            return float(data)
        elif isinstance(data, datetime.datetime):
            return data.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(data, datetime.date):
            return data.strftime("%Y-%m-%d")
        elif isinstance(data, list):
            return [self.convert_decimal_to_float(item) for item in data]
        elif isinstance(data, dict):
            return {key: self.convert_decimal_to_float(value) for key, value in data.items()}
        elif isinstance(data, (tuple, set)):
            return type(data)(self.convert_decimal_to_float(item) for item in data)
        else:
            return data

    def serialize_data(self, data: Any) -> str:
        """序列化数据为JSON（包含datetime处理）"""
        converted_data = self.convert_decimal_to_float(data)
        try:
            return json.dumps(converted_data, ensure_ascii=False, indent=2)
        except json.JSONDecodeError as e:
            with allure.step("数据序列化操作"):
                allure.attach(f"序列化失败: {str(e)}", "失败原因", allure.attachment_type.TEXT)
                allure.attach(str(converted_data), "原始数据", allure.attachment_type.TEXT)
            logger.error(f"[{self._get_current_time()}] 数据序列化失败: {str(e)} \n原始数据: {converted_data}")
            raise ValueError("Failed: 数据序列化失败") from e

    def deserialize_data(self, json_str: str) -> Any:
        """反序列化JSON字符串"""
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            with allure.step("JSON反序列化操作"):
                allure.attach(f"反序列化失败: {str(e)}", "失败原因", allure.attachment_type.TEXT)
                allure.attach(json_str[:500] + "..." if len(json_str) > 500 else json_str,
                              "原始JSON字符串", allure.attachment_type.TEXT)
            logger.error(f"[{self._get_current_time()}] JSON反序列化失败: {str(e)} \n原始字符串: {json_str[:500]}")
            raise ValueError("Failed: JSON反序列化失败") from e

    def _get_current_time(self) -> str:
        """获取当前时间字符串（统一日志格式）"""
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ------------------------------ HTTP请求封装（异常分层优化优化） ------------------------------
    def _attach_request_details(
            self,
            method: str,
            url: str,
            headers: Dict[str, str],
            body: Optional[Any],
            is_json: bool = True,
    ) -> None:
        """统一附加请求详情到Allure步骤"""
        with allure.step("请求详情"):
            allure.attach(url, "请求URL", allure.attachment_type.TEXT)
            allure.attach(
                json.dumps(dict(headers), ensure_ascii=False, indent=2),
                "请求头",
                allure.attachment_type.JSON,
            )
            if body is not None:
                body_type = "请求体（JSON）" if is_json else "请求体（表单/文件）"
                allure.attach(
                    self.serialize_data(body) if is_json else str(body),
                    body_type,
                    allure.attachment_type.JSON if is_json else allure.attachment_type.TEXT,
                )

    def _attach_response_details(self, response: requests.Response) -> None:
        """统一附加响应详情到Allure步骤"""
        with allure.step("响应详情"):
            allure.attach(str(response.status_code), "响应状态码", allure.attachment_type.TEXT)
            allure.attach(
                json.dumps(dict(response.headers), ensure_ascii=False, indent=2),
                "响应头",
                allure.attachment_type.JSON,
            )
            try:
                response_json = response.json()
                allure.attach(
                    json.dumps(response_json, ensure_ascii=False, indent=2),
                    "响应体（JSON）",
                    allure.attachment_type.JSON,
                )
            except json.JSONDecodeError:
                allure.attach(
                    response.text[:1000] + "..." if len(response.text) > 1000 else response.text,
                    "响应体（文本）",
                    allure.attachment_type.TEXT,
                )

    def send_post_request(self, logged_session, url, json_data=None, data=None, files=None,
                          sleep_seconds=SLEEP_SECONDS):
        """发送POST请求（异常分层优化）"""
        method = "POST"
        with allure.step(f"执行 {method} 请求"):
            try:
                self._attach_request_details(
                    method=method,
                    url=url,
                    headers=logged_session.headers,
                    body=json_data if json_data else data,
                    is_json=bool(json_data),
                )

                if files:
                    response = logged_session.post(url, data=data, files=files)
                    logger.info(f"[{self._get_current_time()}] POST请求（带文件）: {url} \n表单数据: {data}")
                elif json_data:
                    response = logged_session.post(url, json=json_data)
                    logger.info(f"[{self._get_current_time()}] POST请求（JSON）: {url} \n数据: {json_data}")
                else:
                    response = logged_session.post(url, data=data)
                    logger.info(f"[{self._get_current_time()}] POST请求（表单）: {url} \n数据: {data}")

                self._attach_response_details(response)

                if sleep_seconds > 0:
                    logger.info(f"[{self._get_current_time()}] 请求后等待 {sleep_seconds} 秒")
                    time.sleep(sleep_seconds)

                return response

            except (SSLError, ConnectionError, Timeout, RequestException) as e:
                with allure.step(f"{method} 请求异常"):
                    self._attach_request_details(
                        method=method,
                        url=url,
                        headers=logged_session.headers,
                        body=json_data if json_data else data,
                        is_json=bool(json_data),
                    )
                    error_detail = (
                        f"请求异常: {str(e)}\n"
                        f"URL: {url}\n"
                        f"请求头: {logged_session.headers}\n"
                        f"请求体: {json_data if json_data else data}"
                    )
                    allure.attach(error_detail, "请求异常详情", allure.attachment_type.TEXT)
                logger.error(f"[{self._get_current_time()}] {method} 请求异常: {str(e)} \nURL: {url}", exc_info=True)
                raise ConnectionError(f"Failed: {method} 请求异常（{str(e)[:1000]}）") from e

    def send_get_request(self, logged_session, url, params=None, sleep_seconds=SLEEP_SECONDS):
        """发送GET请求（异常分层优化）"""
        method = "GET"
        with allure.step(f"执行 {method} 请求"):
            try:
                self._attach_request_details(
                    method=method,
                    url=url,
                    headers=logged_session.headers,
                    body=params,
                    is_json=False,
                )

                response = logged_session.get(url, params=params)
                logger.info(f"[{self._get_current_time()}] GET请求: {url} \n参数: {params}")

                self._attach_response_details(response)

                if sleep_seconds > 0:
                    time.sleep(sleep_seconds)
                return response

            except (SSLError, ConnectionError, Timeout, RequestException) as e:
                with allure.step(f"{method} 请求异常"):
                    self._attach_request_details(
                        method=method,
                        url=url,
                        headers=logged_session.headers,
                        body=params,
                        is_json=False,
                    )
                    error_detail = (
                        f"请求异常: {str(e)}\n"
                        f"URL: {url}\n"
                        f"请求头: {logged_session.headers}\n"
                        f"请求参数: {params}"
                    )
                    allure.attach(error_detail, "请求异常详情", allure.attachment_type.TEXT)
                logger.error(f"[{self._get_current_time()}] {method} 请求异常: {str(e)} \nURL: {url}", exc_info=True)
                raise ConnectionError(f"Failed: {method} 请求异常（{str(e)[:1000]}）") from e

    def send_delete_request(self, logged_session, url, json_data=None, sleep_seconds=SLEEP_SECONDS):
        """发送DELETE请求（异常分层优化）"""
        method = "DELETE"
        with allure.step(f"执行 {method} 请求"):
            try:
                self._attach_request_details(
                    method=method,
                    url=url,
                    headers=logged_session.headers,
                    body=json_data,
                    is_json=True,
                )

                response = logged_session.delete(url, json=json_data)
                logger.info(f"[{self._get_current_time()}] DELETE请求: {url} \n数据: {json_data}")

                self._attach_response_details(response)

                if sleep_seconds > 0:
                    time.sleep(sleep_seconds)
                return response

            except (SSLError, ConnectionError, Timeout, RequestException) as e:
                with allure.step(f"{method} 请求异常"):
                    self._attach_request_details(
                        method=method,
                        url=url,
                        headers=logged_session.headers,
                        body=json_data,
                        is_json=True,
                    )
                    error_detail = (
                        f"请求异常: {str(e)}\n"
                        f"URL: {url}\n"
                        f"请求头: {logged_session.headers}\n"
                        f"请求体: {json_data}"
                    )
                    allure.attach(error_detail, "请求异常详情", allure.attachment_type.TEXT)
                logger.error(f"[{self._get_current_time()}] {method} 请求异常: {str(e)} \nURL: {url}", exc_info=True)
                raise ConnectionError(f"Failed: {method} 请求异常（{str(e)[:1000]}）") from e

    def send_put_request(self, logged_session, url, json_data=None, sleep_seconds=SLEEP_SECONDS):
        """发送PUT请求（异常分层优化）"""
        method = "PUT"
        with allure.step(f"执行 {method} 请求"):
            try:
                self._attach_request_details(
                    method=method,
                    url=url,
                    headers=logged_session.headers,
                    body=json_data,
                    is_json=True,
                )

                response = logged_session.put(url, json=json_data)
                logger.info(f"[{self._get_current_time()}] PUT请求: {url} \n数据: {json_data}")

                self._attach_response_details(response)

                if sleep_seconds > 0:
                    time.sleep(sleep_seconds)
                return response

            except (SSLError, ConnectionError, Timeout, RequestException) as e:
                with allure.step(f"{method} 请求异常"):
                    self._attach_request_details(
                        method=method,
                        url=url,
                        headers=logged_session.headers,
                        body=json_data,
                        is_json=True,
                    )
                    error_detail = (
                        f"请求异常: {str(e)}\n"
                        f"URL: {url}\n"
                        f"请求头: {logged_session.headers}\n"
                        f"请求体: {json_data}"
                    )
                    allure.attach(error_detail, "请求异常详情", allure.attachment_type.TEXT)
                logger.error(f"[{self._get_current_time()}] {method} 请求异常: {str(e)} \nURL: {url}", exc_info=True)
                raise ConnectionError(f"Failed: {method} 请求异常（{str(e)[:1000]}）") from e

    def send_options_request(self, logged_session, url, params=None, sleep_seconds=SLEEP_SECONDS):
        """发送OPTIONS请求（异常分层优化）"""
        method = "OPTIONS"
        with allure.step(f"执行 {method} 请求"):
            try:
                self._attach_request_details(
                    method=method,
                    url=url,
                    headers=logged_session.headers,
                    body=params,
                    is_json=False,
                )

                response = logged_session.options(url, params=params)
                logger.info(f"[{self._get_current_time()}] OPTIONS请求: {url} \n参数: {params}")

                self._attach_response_details(response)

                if sleep_seconds > 0:
                    logger.info(f"[{self._get_current_time()}] 请求后等待 {sleep_seconds} 秒")
                    time.sleep(sleep_seconds)

                return response

            except (SSLError, ConnectionError, Timeout, RequestException) as e:
                with allure.step(f"{method} 请求异常"):
                    self._attach_request_details(
                        method=method,
                        url=url,
                        headers=logged_session.headers,
                        body=params,
                        is_json=False,
                    )
                    error_detail = (
                        f"请求异常: {str(e)}\n"
                        f"URL: {url}\n"
                        f"请求头: {logged_session.headers}\n"
                        f"请求参数: {params}"
                    )
                    allure.attach(error_detail, "请求异常详情", allure.attachment_type.TEXT)
                logger.error(f"[{self._get_current_time()}] {method} 请求异常: {str(e)} \nURL: {url}", exc_info=True)
                raise ConnectionError(f"Failed: {method} 请求异常（{str(e)[:1000]}）") from e

    def _log_response(self, response):
        """记录响应日志（分级日志）"""
        logger.info(f"[{self._get_current_time()}] 响应状态码: {response.status_code} \nURL: {response.url}")
        logger.info(f"[{self._get_current_time()}] 响应详情: 头信息={response.headers} \n内容={response.text[:1000]}")

    # ------------------------------ 断言方法（异常分层优化） ------------------------------
    def assert_response_status(self, response, expected_status, error_msg_prefix):
        """断言响应状态码（分层提示优化）"""
        with allure.step("断言响应状态码"):
            actual_status = response.status_code
            allure.attach(response.url, "请求URL", allure.attachment_type.TEXT)
            allure.attach(f"期望值: {expected_status}", "预期状态码", allure.attachment_type.TEXT)
            allure.attach(f"实际值: {actual_status}", "实际状态码", allure.attachment_type.TEXT)
            allure.attach(response.text, "响应内容", allure.attachment_type.TEXT)

        try:
            assert actual_status == expected_status, \
                f"Failed: {error_msg_prefix}（状态码不匹配）"
        except AssertionError as e:
            with allure.step("状态码断言失败"):
                allure.attach(f"预期: {expected_status}, 实际: {actual_status}", "断言结果",
                              allure.attachment_type.TEXT)
            raise e

    def assert_values_equal(self, actual_value, expected_value, error_msg_prefix):
        """断言两个值相等（分层分层提示优化）"""
        with allure.step("断言值相等"):
            allure.attach(f"期望值: {self.serialize_data(expected_value)}", "预期值", allure.attachment_type.TEXT)
            allure.attach(f"实际值: {self.serialize_data(actual_value)}", "实际值", allure.attachment_type.TEXT)

        try:
            assert actual_value == expected_value, \
                f"Failed: {error_msg_prefix}（值不匹配）"
        except AssertionError as e:
            with allure.step("值相等断言失败"):
                allure.attach(f"预期: {expected_value}, 实际: {actual_value}", "断言结果", allure.attachment_type.TEXT)
            raise e

    def extract_jsonpath(self, response: requests.Response, json_path: str) -> Any:
        """使用jsonpath-ng解析JSON路径（分层提示优化）"""
        try:
            json_data = response.json()
            jsonpath_expr = parse(json_path)
            matches = jsonpath_expr.find(json_data)
            return [match.value for match in matches] if matches else None
        except Exception as e:
            with allure.step("JSONPath解析异常"):
                allure.attach(json_path, "解析路径", allure.attachment_type.TEXT)
                allure.attach(response.text, "响应内容", allure.attachment_type.TEXT)
                allure.attach(str(e), "解析错误", allure.attachment_type.TEXT)
            logger.error(f"JSONPath解析失败: {json_path} \n响应: {response.text[:500]}")
            raise ValueError(f"Failed: JSONPath解析失败（{json_path}）") from e

    def assert_json_value(self, response, json_path, expected_value, error_msg_prefix):
        """断言JSON路径对应的值（分层提示优化）"""
        try:
            actual_value = self.extract_jsonpath(response, json_path)
            if isinstance(actual_value, list) and len(actual_value) == 1:
                actual_value = actual_value[0]

            with allure.step(f"断言JSON路径: {json_path}"):
                allure.attach(response.url, "请求URL", allure.attachment_type.TEXT)
                allure.attach(f"期望值: {self.serialize_data(expected_value)}", "预期值", allure.attachment_type.TEXT)
                allure.attach(f"实际值: {self.serialize_data(actual_value)}", "实际值", allure.attachment_type.TEXT)

            assert actual_value == expected_value, \
                f"Failed: {error_msg_prefix}（JSON路径值不匹配）"
        except Exception as e:
            with allure.step(f"JSON断言失败: {json_path}"):
                allure.attach(json_path, "JSON路径", allure.attachment_type.TEXT)
                allure.attach(str(expected_value), "预期值", allure.attachment_type.TEXT)
                allure.attach(response.text, "响应内容", allure.attachment_type.TEXT)
            logger.error(
                f"[{self._get_current_time()}] JSON断言失败: {str(e)} \n路径: {json_path} \n响应: {response.text[:500]}")
            raise AssertionError(f"Failed: {error_msg_prefix}（JSON断言失败）") from e

    # ------------------------------ 数据库操作（异常分层优化） ------------------------------
    def query_database(self, db_transaction: pymysql.connections.Connection,
                       sql: str,
                       params: tuple = (),
                       order_by: str = "create_time DESC",
                       convert_decimal: bool = True,
                       dictionary_cursor: bool = True,
                       attach_to_allure: bool = True) -> List[Dict[str, Any]]:
        """基础数据库查询（单次查询，带Allure分层提示）"""
        sql_upper = sql.upper()
        final_sql = sql

        if order_by and "ORDER BY" not in sql_upper:
            final_sql += f" ORDER BY {order_by}"
        elif order_by:
            logger.warning(f"[{self._get_current_time()}] SQL已包含ORDER BY，忽略传入的排序: {order_by}")

        try:
            with allure.step("执行数据库查询"):
                cursor_type = pymysql.cursors.DictCursor if dictionary_cursor else None
                with db_transaction.cursor(cursor_type) as cursor:
                    logger.info(f"[{self._get_current_time()}] 执行SQL: \n{final_sql} \n参数: {params}")
                    cursor.execute(final_sql, params)
                    result = cursor.fetchall()
                    logger.info(
                        f"[{self._get_current_time()}] 查询成功，结果数量: {len(result)}")

                    if result:
                        if convert_decimal:
                            result = self.convert_decimal_to_float(result)
                        result = self._convert_date_types(result)

                    try:
                        result_preview = json.dumps(result, ensure_ascii=False)
                    except Exception as e:
                        result_preview = f"无法序列化完整结果: {str(e)}"
                    logger.info(f"[{self._get_current_time()}] 查询结果: {result_preview[:500]}")

                    if attach_to_allure:
                        display_count = min(len(result), 50)
                        with allure.step("数据库查询结果"):
                            allure.attach(
                                self.serialize_data(result[:display_count]),
                                f"查询结果（共{len(result)}条，显示前50条）",
                                allure.attachment_type.JSON
                            )
                            allure.attach(final_sql, "执行SQL", allure.attachment_type.TEXT)
                            allure.attach(str(params), "SQL参数", allure.attachment_type.TEXT)

                return result

        except pymysql.Error as e:
            with allure.step("数据库查询异常（pymysql错误）"):
                allure.attach(final_sql, "执行SQL", allure.attachment_type.TEXT)
                allure.attach(str(params), "SQL参数", allure.attachment_type.TEXT)
                allure.attach(f"错误码: {e.args[0]} \n信息: {str(e)}", "错误详情", allure.attachment_type.TEXT)
            error_msg = (
                f"[{self._get_current_time()}] 数据库错误 (错误码: {e.args[0]}): {str(e)} \n"
                f"SQL: {final_sql[:200]} \n参数: {params}"
            )
            logger.error(error_msg, exc_info=True)
            raise pymysql.Error(f"Failed: 数据库查询错误（错误码: {e.args[0]}）") from e

        except Exception as e:
            with allure.step("数据库查询异常（未知错误）"):
                allure.attach(final_sql, "执行SQL", allure.attachment_type.TEXT)
                allure.attach(str(params), "SQL参数", allure.attachment_type.TEXT)
                allure.attach(str(e), "错误详情", allure.attachment_type.TEXT)
            error_msg = f"[{self._get_current_time()}] 未知异常: {str(e)} \nSQL: {final_sql[:200]}"
            logger.error(error_msg, exc_info=True)
            raise RuntimeError(f"Failed: 数据库查询异常") from e

    def _convert_date_types(self, result: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """将结果中的日期和时间类型转换为字符串"""

        def convert_value(value):
            if isinstance(value, datetime.datetime):
                return value.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(value, datetime.date):
                return value.strftime("%Y-%m-%d")
            return value

        return [{k: convert_value(v) for k, v in row.items()} for row in result]

    # ------------------------------ 核心：轮询版数据库查询（异常分层优化） ------------------------------
    def query_database_with_time(
            self,
            db_transaction: pymysql.connections.Connection,
            sql: str,
            params: tuple = (),
            time_field: Optional[str] = None,
            time_range: int = MYSQL_TIME,  # 时间范围（分钟），默认使用你的全局变量
            order_by: str = "create_time DESC",
            timeout: int = WAIT_TIMEOUT,  # 轮询总超时，默认全局变量
            poll_interval: int = POLL_INTERVAL,  # 轮询间隔，默认全局变量
            stable_period: int = STBLE_PERIOD,  # 数据稳定期，默认全局变量
            attach_to_allure: bool = True
    ) -> List[Dict[str, Any]]:
        """轮询等待数据库记录稳定（核心改造：使用固定时间范围，避免数据过期）"""
        start_time = time.time()
        last_result = None
        stable_start_time = None
        final_result = None
        has_data = False

        # 生成固定时间范围（轮询开始时计算一次）
        poll_start_datetime = datetime.datetime.now()
        fixed_time_start = (poll_start_datetime - datetime.timedelta(minutes=time_range)).strftime(
            "%Y-%m-%d %H:%M:%S")
        fixed_time_end = (poll_start_datetime + datetime.timedelta(minutes=time_range)).strftime(
            "%Y-%m-%d %H:%M:%S")
        logger.info(
            f"[{self._get_current_time()}] 开始轮询等待数据稳定 | "
            f"超时: {timeout}秒 | 稳定期: {stable_period}秒"
        )

        with allure.step(f"轮询等待数据稳定（超时: {timeout}秒，稳定期: {stable_period}秒）"):
            while time.time() - start_time < timeout:
                try:
                    db_transaction.commit()  # 刷新事务

                    # 传入固定时间范围，而非动态计算
                    result = self._execute_query(
                        db_transaction=db_transaction,
                        sql=sql,
                        params=params,
                        time_field=time_field,
                        order_by=order_by,
                        fixed_time_start=fixed_time_start,  # 传递固定开始时间
                        fixed_time_end=fixed_time_end,  # 传递固定结束时间
                        attach_to_allure=False  # 轮询过程中不重复附加报告
                    )

                    # 记录轮询状态（原有逻辑不变）
                    elapsed = time.time() - start_time
                    with allure.step(f"轮询中（已等待{elapsed:.1f}秒）"):
                        allure.attach(f"结果数量: {len(result)}", "当前状态", allure.attachment_type.TEXT)
                        allure.attach(f"剩余时间: {timeout - elapsed:.1f}秒", "超时倒计时",
                                      allure.attachment_type.TEXT)

                    # 检查数据是否稳定（原有逻辑不变）
                    if len(result) > 0:
                        has_data = True
                        if self._is_result_stable(result, last_result):
                            if stable_start_time is None:
                                stable_start_time = time.time()
                                logger.debug(f"[{self._get_current_time()}] 数据首次稳定，开始计时")
                                with allure.step("数据首次稳定"):
                                    allure.attach(f"开始稳定期计时（需保持{stable_period}秒）", "状态说明",
                                                  allure.attachment_type.TEXT)
                            elif time.time() - stable_start_time >= stable_period:
                                final_result = result
                                logger.info(
                                    f"[{self._get_current_time()}] 数据已稳定{stable_period}秒（耗时{time.time() - start_time:.1f}秒）| "
                                    f"结果数: {len(result)}"
                                )
                                with allure.step("数据稳定达标"):
                                    allure.attach(
                                        f"已稳定{stable_period}秒（总耗时{time.time() - start_time:.1f}秒）",
                                        "结果说明", allure.attachment_type.TEXT)
                                break
                        else:
                            stable_start_time = None  # 数据变化，重置计时器
                            logger.debug(f"[{self._get_current_time()}] 数据仍在变化，重置稳定计时器")
                            with allure.step("数据发生变化"):
                                allure.attach("重置稳定期计时器", "状态说明", allure.attachment_type.TEXT)
                    else:
                        stable_start_time = None
                        has_data = False
                        logger.debug(
                            f"[{self._get_current_time()}] 查询结果为空，继续等待")
                        with allure.step("查询结果为空"):
                            allure.attach("继续等待数据出现", "状态说明", allure.attachment_type.TEXT)

                    last_result = result
                    time.sleep(poll_interval)

                except Exception as e:
                    with allure.step("轮询查询异常（单次查询失败）"):
                        allure.attach(sql, "执行SQL", allure.attachment_type.TEXT)
                        allure.attach(str(params), "SQL参数", allure.attachment_type.TEXT)
                        allure.attach(f"固定时间范围: {fixed_time_start} ~ {fixed_time_end}", "查询时间窗口",
                                      allure.attachment_type.TEXT)
                        allure.attach(str(e), "错误详情", allure.attachment_type.TEXT)
                    logger.warning(f"[{self._get_current_time()}] 轮询查询异常: {str(e)} \n继续等待...")
                    time.sleep(poll_interval)

            # 超时处理：获取最终结果（仍使用固定时间范围）
            if final_result is None:
                with allure.step("轮询超时处理"):
                    allure.attach(
                        f"超过{timeout}秒未达到稳定状态，获取最终结果",
                        "处理说明",
                        allure.attachment_type.TEXT)
                final_result = self._execute_query(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field=time_field,
                    order_by=order_by,
                    fixed_time_start=fixed_time_start,
                    fixed_time_end=fixed_time_end,
                    attach_to_allure=attach_to_allure
                )

            # 附加最终结果到报告（原有逻辑不变）
            if attach_to_allure:
                display_count = min(len(final_result), 50)
                with allure.step("数据库查询结果（最终稳定结果）"):
                    allure.attach(
                        self.serialize_data(final_result[:display_count]),
                        f"查询结果（共{len(final_result)}条，显示前50条）",
                        allure.attachment_type.JSON
                    )
                    allure.attach(sql, "执行SQL", allure.attachment_type.TEXT)
                    allure.attach(str(params), "SQL参数", allure.attachment_type.TEXT)
                    allure.attach(f"固定时间范围: {fixed_time_start} ~ {fixed_time_end}", "查询时间窗口",
                                  allure.attachment_type.TEXT)  # Allure展示固定时间

            # 判断超时场景（原有逻辑不变）
            if len(final_result) == 0:
                with allure.step("轮询超时（无结果）"):
                    allure.attach(
                        f"等待{timeout}秒后仍无查询结果",
                        "超时详情", allure.attachment_type.TEXT)
                error_msg = f"Failed: 等待记录出现超时（{timeout}秒）"
                raise TimeoutError(error_msg)
            elif final_result is None:
                with allure.step("轮询超时（未稳定）"):
                    allure.attach(
                        f"数据未在{stable_period}秒内稳定（总超时{timeout}秒）",
                        "超时详情",
                        allure.attachment_type.TEXT)
                error_msg = f"Failed: 数据未在{stable_period}秒内稳定（超时{timeout}秒）"
                raise TimeoutError(error_msg)

            return final_result

    def _execute_query(
            self,
            db_transaction: pymysql.connections.Connection,
            sql: str,
            params: tuple,
            time_field: Optional[str],
            order_by: str,
            # 参数替换（删除time_range，新增固定时间范围）
            fixed_time_start: Optional[str] = None,
            fixed_time_end: Optional[str] = None,
            attach_to_allure: bool = True
    ) -> List[Dict[str, Any]]:
        """执行单次数据库查询（核心改造：使用固定时间范围拼接SQL，而非动态NOW()）"""
        with allure.step("执行单次数据库查询"):
            if time_field and fixed_time_start and fixed_time_end:
                # 拼接固定时间条件（而非动态INTERVAL）
                sql_upper = sql.upper()
                final_sql = sql
                final_params = list(params)

                # 固定时间条件：使用BETWEEN固定时间点，而非NOW()±INTERVAL
                time_condition = f" {time_field} BETWEEN %s AND %s "

                # 拼接WHERE子句（原有逻辑不变，但条件内容改为固定时间）
                if "WHERE" in sql_upper:
                    final_sql += f" AND {time_condition}"
                else:
                    final_sql += f" WHERE {time_condition}"
                # 追加固定时间参数（而非time_range）
                final_params.extend([fixed_time_start, fixed_time_end])

                # Allure和日志展示固定时间范围
                allure.attach(f"固定时间范围: {time_field} BETWEEN {fixed_time_start} AND {fixed_time_end}",
                              "查询条件", allure.attachment_type.TEXT)
                logger.debug(f"执行单次查询（固定时间）: SQL={final_sql[:200]} \n参数={final_params}")
                return self.query_database(
                    db_transaction=db_transaction,
                    sql=final_sql,
                    params=tuple(final_params),
                    order_by=order_by,
                    attach_to_allure=attach_to_allure
                )
            elif time_field:
                # 异常处理：若指定了time_field但未传固定时间，报错提示
                err_msg = f"使用time_field={time_field}时，必须传入fixed_time_start和fixed_time_end"
                allure.attach(err_msg, "参数异常", allure.attachment_type.TEXT)
                raise ValueError(err_msg)
            else:
                # 不限制时间范围（原有逻辑不变）
                allure.attach("不限制时间范围", "查询条件", allure.attachment_type.TEXT)
                logger.debug(f"执行单次查询（无时间限制）: SQL={sql[:200]} \n参数={params}")
                return self.query_database(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    order_by=order_by,
                    attach_to_allure=attach_to_allure
                )

    def _is_result_stable(self, current: List[Dict], previous: List[Dict]) -> bool:
        """判断两次查询结果是否稳定（自动识别唯一键）"""
        with allure.step("判断结果稳定性"):
            if previous is None or len(current) == 0:
                allure.attach("首次查询或结果为空，无对比", "判断结果", allure.attachment_type.TEXT)
                return False

            # 1. 自动识别唯一键（按优先级匹配：可根据业务调整顺序）
            candidate_keys = ['account', 'order_no', 'send_no', 'close_no', 'foi.order_no', 'fod.send_no',
                              'fod.close_no', 'id', 'comment']  # 优先级从高到低
            unique_key = None
            sample_item = current[0]  # 取第一条结果当样本
            for key in candidate_keys:
                if key in sample_item:
                    unique_key = key
                    break
            # 若没有匹配到候选键，报错提示
            if not unique_key:
                err_msg = f"未识别到唯一键（候选键: {candidate_keys}，结果字段: {list(sample_item.keys())}）"
                allure.attach(err_msg, "判断异常", allure.attachment_type.TEXT)
                raise ValueError(err_msg)
            allure.attach(f"自动识别唯一键: {unique_key}", "唯一键信息", allure.attachment_type.TEXT)

            # 2. 后续逻辑和方案1一致（数量对比→唯一键映射→内容对比）
            if len(current) != len(previous):
                allure.attach(f"数量变化: 前{len(previous)}条 → 现{len(current)}条", "判断结果",
                              allure.attachment_type.TEXT)
                return False

            current_map = {item[unique_key]: item for item in current}
            previous_map = {item[unique_key]: item for item in previous}

            if set(current_map.keys()) != set(previous_map.keys()):
                added = current_map.keys() - previous_map.keys()
                removed = previous_map.keys() - current_map.keys()
                allure.attach(f"唯一键变化: 新增{added}，删除{removed}", "判断结果", allure.attachment_type.TEXT)
                return False

            ignore_fields = {'create_time', 'update_time', 'response_time', 'open_time', 'close_time'}
            for key in current_map:
                curr_item = current_map[key]
                prev_item = previous_map[key]
                for field in curr_item:
                    if field in ignore_fields:
                        continue
                    if curr_item[field] != prev_item[field]:
                        allure.attach(f"唯一键[{key}]的字段'{field}'变化: {prev_item[field]} → {curr_item[field]}",
                                      "判断结果", allure.attachment_type.TEXT)
                        return False

            allure.attach("数量和内容均未变化，结果稳定", "判断结果", allure.attachment_type.TEXT)
            return True

    # ------------------------------ 其他数据库工具方法（异常分层优化） ------------------------------
    def wait_for_database_deletion(self, db_transaction: pymysql.connections.Connection,
                                   sql: str,
                                   params: tuple = (),
                                   time_field: Optional[str] = None,
                                   time_range: int = MYSQL_TIME,
                                   order_by: str = "create_time DESC",
                                   timeout: int = DELETE_WAIT_TIMEOUT,
                                   poll_interval: int = POLL_INTERVAL) -> None:
        """轮询等待数据库记录删除（带Allure分层提示）"""
        start_time = time.time()

        # 生成固定时间范围（轮询开始时计算一次）
        poll_start_datetime = datetime.datetime.now()
        fixed_time_start = (poll_start_datetime - datetime.timedelta(minutes=time_range)).strftime(
            "%Y-%m-%d %H:%M:%S")
        fixed_time_end = (poll_start_datetime + datetime.timedelta(minutes=time_range)).strftime(
            "%Y-%m-%d %H:%M:%S")

        logger.info(f"[{self._get_current_time()}] 开始等待数据库记录删除 | 超时: {timeout}秒")

        with allure.step(f"等待数据库记录删除（超时: {timeout}秒）"):
            while time.time() - start_time < timeout:
                try:
                    db_transaction.commit()

                    if time_field:
                        result = self._execute_query(
                            db_transaction=db_transaction,
                            sql=sql,
                            params=params,
                            time_field=time_field,
                            order_by=order_by,
                            fixed_time_start=fixed_time_start,
                            fixed_time_end=fixed_time_end,
                            attach_to_allure=False
                        )
                    else:
                        result = self.query_database(
                            db_transaction=db_transaction,
                            sql=sql,
                            params=params,
                            order_by=order_by,
                            attach_to_allure=False
                        )

                    elapsed = time.time() - start_time
                    with allure.step(f"等待中（已等待{elapsed:.1f}秒）"):
                        allure.attach(f"剩余记录数: {len(result)}", "当前状态", allure.attachment_type.TEXT)
                        allure.attach(f"剩余时间: {timeout - elapsed:.1f}秒", "超时倒计时", allure.attachment_type.TEXT)

                    if not result:
                        logger.info(
                            f"[{self._get_current_time()}] 删除成功（耗时{time.time() - start_time:.1f}秒）")
                        with allure.step("删除验证成功"):
                            allure.attach(f"耗时{time.time() - start_time:.1f}秒，记录已删除", "结果说明",
                                          allure.attachment_type.TEXT)
                            allure.attach(sql, "执行SQL", allure.attachment_type.TEXT)
                            allure.attach(str(params), "SQL参数", allure.attachment_type.TEXT)
                        return

                    logger.info(
                        f"[{self._get_current_time()}] 记录仍存在（已等待{elapsed:.1f}秒）| 剩余时间: {timeout - elapsed:.1f}秒 | 结果数: {len(result)}")
                    time.sleep(poll_interval)

                except Exception as e:
                    with allure.step("删除等待异常"):
                        allure.attach(sql, "执行SQL", allure.attachment_type.TEXT)
                        allure.attach(str(params), "SQL参数", allure.attachment_type.TEXT)
                        allure.attach(str(e), "错误详情", allure.attachment_type.TEXT)
                    logger.warning(f"[{self._get_current_time()}] 轮询查询异常: {str(e)} \n继续等待...")
                    time.sleep(poll_interval)

            # 超时处理
            db_transaction.commit()
            if time_field:
                final_result = self._execute_query(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field=time_field,
                    order_by=order_by,
                    fixed_time_start=fixed_time_start,
                    fixed_time_end=fixed_time_end,
                    attach_to_allure=True
                )
            else:
                final_result = self.query_database(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    order_by=order_by,
                    attach_to_allure=True
                )

            display_count = min(len(final_result), 50)
            with allure.step("等待删除超时"):
                allure.attach(f"超过{timeout}秒仍有{len(final_result)}条记录未删除", "超时说明",
                              allure.attachment_type.TEXT)
                allure.attach(
                    self.serialize_data(final_result[:display_count]),
                    f"剩余记录（共{len(final_result)}条）",
                    allure.attachment_type.JSON
                )
                allure.attach(sql, "执行SQL", allure.attachment_type.TEXT)
                allure.attach(str(params), "SQL参数", allure.attachment_type.TEXT)
                allure.attach(f"固定时间范围: {fixed_time_start} ~ {fixed_time_end}", "查询时间窗口",
                              allure.attachment_type.TEXT)

            raise TimeoutError(f"等待记录删除超时（{timeout}秒）")

    def wait_for_database_no_record(
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
            attach_to_allure: bool = True
    ) -> List[Dict[str, Any]]:
        """
        轮询等待数据库无符合条件的记录，并返回最终查询结果（带Allure分层提示）
        用于“校验无数据”场景，支持后续assert判断
        """
        start_time = time.time()
        stable_start_time = None  # 无记录稳定期计时器

        # 生成固定时间范围（轮询开始时计算一次）
        poll_start_datetime = datetime.datetime.now()
        fixed_time_start = (poll_start_datetime - datetime.timedelta(minutes=time_range)).strftime(
            "%Y-%m-%d %H:%M:%S")
        fixed_time_end = (poll_start_datetime + datetime.timedelta(minutes=time_range)).strftime(
            "%Y-%m-%d %H:%M:%S")

        logger.info(
            f"[{self._get_current_time()}] 开始轮询等待无记录 | 超时: {timeout}秒"
        )

        with allure.step(f"轮询等待无记录（超时: {timeout}秒，稳定期: {stable_period}秒）"):
            while time.time() - start_time < timeout:
                try:
                    db_transaction.commit()
                    result = self._execute_query(
                        db_transaction=db_transaction,
                        sql=sql,
                        params=params,
                        time_field=time_field,
                        order_by=order_by,
                        fixed_time_start=fixed_time_start,  # 传递固定时间参数
                        fixed_time_end=fixed_time_end,
                        attach_to_allure=False
                    )

                    elapsed = time.time() - start_time
                    with allure.step(f"等待中（已等待{elapsed:.1f}秒）"):
                        allure.attach(f"当前记录数: {len(result)}", "查询状态", allure.attachment_type.TEXT)
                        allure.attach(f"剩余时间: {timeout - elapsed:.1f}秒", "超时倒计时", allure.attachment_type.TEXT)

                    # 检查是否无记录并进入稳定期
                    if len(result) == 0:
                        if stable_start_time is None:
                            stable_start_time = time.time()
                            logger.debug(f"[{self._get_current_time()}] 首次无记录，开始稳定期计时")
                            with allure.step("首次无记录"):
                                allure.attach(f"开始稳定期计时（需保持{stable_period}秒）", "状态说明",
                                              allure.attachment_type.TEXT)
                        elif time.time() - stable_start_time >= stable_period:
                            elapsed_total = time.time() - start_time
                            logger.info(
                                f"[{self._get_current_time()}] 无记录稳定{stable_period}秒，符合预期（耗时{elapsed_total:.1f}秒）")
                            if attach_to_allure:
                                with allure.step("无记录状态稳定"):
                                    allure.attach(f"无记录稳定{stable_period}秒", "结果说明",
                                                  allure.attachment_type.TEXT)
                            return result  # 无记录，返回空列表
                    else:
                        stable_start_time = None  # 有记录，重置计时器
                        logger.debug(f"[{self._get_current_time()}] 查到{len(result)}条记录，重置稳定期")
                        with allure.step("检测到记录"):
                            allure.attach(f"查到{len(result)}条记录，重置稳定期计时器", "状态说明",
                                          allure.attachment_type.TEXT)

                    time.sleep(poll_interval)

                except Exception as e:
                    with allure.step("无记录等待异常"):
                        allure.attach(sql, "执行SQL", allure.attachment_type.TEXT)
                        allure.attach(str(params), "SQL参数", allure.attachment_type.TEXT)
                        allure.attach(str(e), "错误详情", allure.attachment_type.TEXT)
                    logger.warning(f"轮询异常: {str(e)}，继续等待...")
                    time.sleep(poll_interval)

            # 超时处理：返回最终查询结果（无论是否有记录）
            final_result = self._execute_query(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field=time_field,
                order_by=order_by,
                fixed_time_start=fixed_time_start,
                fixed_time_end=fixed_time_end,
                attach_to_allure=attach_to_allure
            )

            if attach_to_allure:
                with allure.step("超时后最终结果"):
                    allure.attach(f"超时{timeout}秒，查到{len(final_result)}条记录", "结果说明",
                                  allure.attachment_type.TEXT)
                    allure.attach(sql, "执行SQL", allure.attachment_type.TEXT)
                    allure.attach(str(params), "SQL参数", allure.attachment_type.TEXT)
                    allure.attach(f"固定时间范围: {fixed_time_start} ~ {fixed_time_end}", "查询时间窗口",
                                  allure.attachment_type.TEXT)

            return final_result  # 超时后返回实际查询结果（可能非空）

    # ------------------------------ 带时区的轮询查询（异常分层优化） ------------------------------
    def query_database_with_time_with_timezone(
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
            timezone_offset: int = TIMEZONE_OFFSET,
            attach_to_allure: bool = True
    ) -> List[Dict[str, Any]]:
        """带时区转换的轮询查询（带Allure分层提示）"""
        offset_str = f"{timezone_offset:+03d}:00"  # 转换为时区字符串（如+08:00）
        start_time = time.time()
        last_result = None
        stable_start_time = None
        final_result = None

        # 生成固定时间范围（轮询开始时计算一次）
        poll_start_datetime = datetime.datetime.now()
        fixed_time_start = (poll_start_datetime - datetime.timedelta(minutes=time_range)).strftime(
            "%Y-%m-%d %H:%M:%S")
        fixed_time_end = (poll_start_datetime + datetime.timedelta(minutes=time_range)).strftime(
            "%Y-%m-%d %H:%M:%S")

        logger.info(f"[{self._get_current_time()}] 开始轮询（时区{offset_str}）| 超时: {timeout}秒")

        with allure.step(f"轮询等待数据稳定（时区{offset_str}，超时{timeout}秒）"):
            while time.time() - start_time < timeout:
                try:
                    db_transaction.commit()
                    # 执行带时区转换的单次查询
                    result = self._execute_query_with_timezone(
                        db_transaction=db_transaction,
                        sql=sql,
                        params=params,
                        time_field=time_field,
                        order_by=order_by,
                        fixed_time_start=fixed_time_start,  # 传递固定时间参数
                        fixed_time_end=fixed_time_end,
                        timezone_offset=offset_str,
                        attach_to_allure=False
                    )

                    # 记录轮询状态
                    elapsed = time.time() - start_time
                    with allure.step(f"轮询中（已等待{elapsed:.1f}秒）"):
                        allure.attach(f"结果数量: {len(result)}", "当前状态", allure.attachment_type.TEXT)
                        allure.attach(f"剩余时间: {timeout - elapsed:.1f}秒", "超时倒计时", allure.attachment_type.TEXT)

                    # 复用数据稳定判断逻辑
                    if len(result) > 0 and self._is_result_stable(result, last_result):
                        if stable_start_time is None:
                            stable_start_time = time.time()
                            with allure.step("数据首次稳定"):
                                allure.attach(f"开始稳定期计时（需保持{stable_period}秒）", "状态说明",
                                              allure.attachment_type.TEXT)
                        elif time.time() - stable_start_time >= stable_period:
                            final_result = result
                            logger.info(f"[{self._get_current_time()}] 数据稳定，轮询结束")
                            with allure.step("数据稳定达标"):
                                allure.attach(f"已稳定{stable_period}秒（总耗时{time.time() - start_time:.1f}秒）",
                                              "结果说明", allure.attachment_type.TEXT)
                            break
                    else:
                        stable_start_time = None
                        with allure.step("数据发生变化"):
                            allure.attach("重置稳定期计时器", "状态说明", allure.attachment_type.TEXT)

                    last_result = result
                    time.sleep(poll_interval)

                except Exception as e:
                    with allure.step("时区查询轮询异常"):
                        allure.attach(sql, "执行SQL", allure.attachment_type.TEXT)
                        allure.attach(str(params), "SQL参数", allure.attachment_type.TEXT)
                        allure.attach(str(e), "错误详情", allure.attachment_type.TEXT)
                    logger.warning(f"[{self._get_current_time()}] 轮询异常: {str(e)} \n继续等待")
                    time.sleep(poll_interval)

            # 超时处理
            if final_result is None:
                with allure.step("时区查询轮询超时"):
                    allure.attach(f"超过{timeout}秒未达到稳定状态，获取最终结果", "处理说明",
                                  allure.attachment_type.TEXT)
                final_result = self._execute_query_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field=time_field,
                    order_by=order_by,
                    fixed_time_start=fixed_time_start,
                    fixed_time_end=fixed_time_end,
                    timezone_offset=offset_str,
                    attach_to_allure=True
                )

            # 附加结果到报告
            if final_result and attach_to_allure:
                with allure.step("带时区查询最终结果"):
                    display_result = min(len(final_result), 50)
                    allure.attach(self.serialize_data(final_result[:display_result]),
                                  f"查询结果（共{len(final_result)}条，显示前50条）", allure.attachment_type.JSON)
                    allure.attach(sql, "执行SQL", allure.attachment_type.TEXT)
                    allure.attach(str(params), "SQL参数", allure.attachment_type.TEXT)
                    allure.attach(f"{timezone_offset}", "时区偏移量（小时）", allure.attachment_type.TEXT)
                    allure.attach(f"固定时间范围: {fixed_time_start} ~ {fixed_time_end}", "查询时间窗口",
                                  allure.attachment_type.TEXT)

            if not final_result:
                with allure.step("时区查询无结果"):
                    allure.attach(f"轮询{timeout}秒后仍无查询结果", "异常详情", allure.attachment_type.TEXT)
                    allure.attach(sql, "执行SQL", allure.attachment_type.TEXT)
                    allure.attach(str(params), "SQL参数", allure.attachment_type.TEXT)
                    allure.attach(f"{timezone_offset}", "时区偏移量（小时）", allure.attachment_type.TEXT)
                    allure.attach(f"固定时间范围: {fixed_time_start} ~ {fixed_time_end}", "查询时间窗口",
                                  allure.attachment_type.TEXT)
                raise TimeoutError(f"Failed: 时区查询超时（{timeout}秒）")
            return final_result

    def _execute_query_with_timezone(
            self,
            db_transaction: pymysql.connections.Connection,
            sql: str,
            params: tuple,
            time_field: Optional[str],
            order_by: str,
            timezone_offset: str,
            # 新增：接收固定时间参数
            fixed_time_start: Optional[str] = None,
            fixed_time_end: Optional[str] = None,
            attach_to_allure: bool = True
    ) -> List[Dict[str, Any]]:
        """带时区转换的单次查询辅助方法（带Allure分层提示）"""
        with allure.step(f"带时区转换查询（目标时区: {timezone_offset}）"):
            if time_field and fixed_time_start and fixed_time_end:
                # 转换时间字段时区（假设数据库存储UTC时间）
                converted_time_field = f"CONVERT_TZ({time_field}, '+00:00', '{timezone_offset}')"
                sql_upper = sql.upper()
                final_sql = sql
                final_params = list(params)

                # 使用固定时间范围（已转换为时区对应的时间）
                time_condition = f" {converted_time_field} BETWEEN %s AND %s "

                if "WHERE" in sql_upper:
                    final_sql += f" AND {time_condition}"
                else:
                    final_sql += f" WHERE {time_condition}"
                final_params.extend([fixed_time_start, fixed_time_end])

                allure.attach(f"时间字段转换: {time_field} (UTC → {timezone_offset})", "时区处理",
                              allure.attachment_type.TEXT)
                allure.attach(
                    f"带时区固定时间范围: {converted_time_field} BETWEEN {fixed_time_start} AND {fixed_time_end}",
                    "查询条件", allure.attachment_type.TEXT)
                return self.query_database(
                    db_transaction=db_transaction,
                    sql=final_sql,
                    params=tuple(final_params),
                    order_by=order_by,
                    attach_to_allure=attach_to_allure
                )
            elif time_field:
                # 异常处理：缺少固定时间参数
                err_msg = f"使用time_field={time_field}时，必须传入fixed_time_start和fixed_time_end"
                allure.attach(err_msg, "参数异常", allure.attachment_type.TEXT)
                raise ValueError(err_msg)
            else:
                allure.attach("不涉及时间字段转换", "时区处理", allure.attachment_type.TEXT)
                return self.query_database(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    order_by=order_by,
                    attach_to_allure=attach_to_allure
                )

    # ------------------------------ 其他辅助方法（异常分层优化） ------------------------------
    def wait_for_api_condition(self, logged_session, method, url, params=None, json_data=None,
                               expected_condition=None, timeout=WAIT_TIMEOUT, poll_interval=POLL_INTERVAL):
        """等待API响应满足特定条件（带Allure分层提示）"""
        if expected_condition is None:
            with allure.step("参数异常"):
                allure.attach("expected_condition参数为None", "错误详情", allure.attachment_type.TEXT)
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
                    with allure.step("不支持的HTTP方法"):
                        allure.attach(f"方法: {method}", "错误详情", allure.attachment_type.TEXT)
                    raise ValueError(f"不支持的HTTP方法: {method}")

                self._log_response(response)
                return expected_condition(response)

            except Exception as e:
                with allure.step("API条件检查异常"):
                    allure.attach(f"{method} {url}", "请求地址", allure.attachment_type.TEXT)
                    allure.attach(str(e), "错误详情", allure.attachment_type.TEXT)
                logger.error(f"[{self._get_current_time()}] API请求异常: {str(e)} \nURL: {url}")
                return False

        try:
            with allure.step(f"等待API条件满足（{method} {url}）"):
                allure.attach(f"超时时间: {timeout}秒", "等待配置", allure.attachment_type.TEXT)
                allure.attach(f"轮询间隔: {poll_interval}秒", "等待配置", allure.attachment_type.TEXT)
                return wait_for_condition(
                    condition=check_api,
                    timeout=timeout,
                    poll_interval=poll_interval,
                    error_message=f"API条件验证超时 (URL: {url})",
                    step_title="等待API条件满足"
                )
        except TimeoutError as e:
            with allure.step("API条件等待超时"):
                allure.attach(f"{method} {url}", "请求地址", allure.attachment_type.TEXT)
                allure.attach(str(params or json_data), "请求参数", allure.attachment_type.TEXT)
            raise TimeoutError(f"Failed: API条件等待超时（{url}）") from e

    def assert_list_equal_ignore_order(self, list1, list2, list3, error_msg_prefix="断言失败，列表元素不匹配"):
        """
        断言列表元素相同（忽略顺序），精准拆分断言逻辑，明确展示匹配关系
        :param list1: 总手数列表
        :param list2: 预期列表
        :param list3: 实际总手数列表
        :param error_msg_prefix: 错误提示前缀
        """
        from collections import Counter

        # 分别计算三个列表的元素计数
        counter1 = Counter(list1)
        counter2 = Counter(list2)
        counter3 = Counter(list3)

        with allure.step("断言列表元素相同（忽略顺序）"):
            # allure.attach(self.serialize_data(list1), "总手数列表", attachment_type="text/plain")
            # allure.attach(self.serialize_data(list3), "实际总手数列表", attachment_type="text/plain")
            # allure.attach(self.serialize_data(list2), "详情手数列表", attachment_type="text/plain")

            try:
                # 先判断总手数列表是否与预期匹配
                if counter1 == counter2:
                    with allure.step("总手数列表与详情手数列表匹配"):
                        allure.attach(f"总手数列表: {list1} \n详情手数列表: {list2}", "匹配结果",
                                      attachment_type="text/plain")
                    return  # 匹配成功，直接返回

                # 再判断实际总手数列表是否与预期匹配
                elif counter3 == counter2:
                    with allure.step("实际总手数列表与详情手数列表匹配"):
                        allure.attach(f"实际总手数列表: {list3} \n详情手数列表: {list2}", "匹配结果",
                                      attachment_type="text/plain")
                    return  # 匹配成功，直接返回

                # 两者都不匹配时抛出断言错误
                else:
                    raise AssertionError(f"Failed: {error_msg_prefix}（忽略顺序）")

            except AssertionError as e:
                with allure.step("列表元素断言失败"):
                    allure.attach(str(e), "错误详情", attachment_type="text/plain")
                raise e

    def assert_dict_subset(self, subset_dict, full_dict, error_msg_prefix="子字典不匹配"):
        """断言一个字典是另一个字典的子集（带Allure分层提示）"""
        with allure.step("断言子字典匹配"):
            allure.attach(self.serialize_data(subset_dict), "预期子字典", allure.attachment_type.TEXT)
            allure.attach(self.serialize_data(full_dict), "实际完整字典", allure.attachment_type.TEXT)

        try:
            for key, value in subset_dict.items():
                assert key in full_dict, f"Failed: {error_msg_prefix}（键 '{key}' 不存在）"
                assert full_dict[key] == value, f"Failed: {error_msg_prefix}（键 '{key}' 值不匹配）"
        except AssertionError as e:
            with allure.step("子字典断言失败"):
                allure.attach(str(e), "错误详情", allure.attachment_type.TEXT)
            raise e

    def get_batch_data_by_index(self, var_manager, var_name, index):
        """从批量数据中获取指定索引的数据（带Allure分层提示）"""
        try:
            data_list = var_manager.get_variable(var_name)
            with allure.step(f"获取批量数据: {var_name}[{index}]"):
                allure.attach(f"变量名: {var_name}", "变量信息", allure.attachment_type.TEXT)
                allure.attach(f"索引: {index}", "访问索引", allure.attachment_type.TEXT)
                allure.attach(self.serialize_data(data_list[:5]), "数据预览（前5条）", allure.attachment_type.TEXT)

            if not isinstance(data_list, list):
                raise ValueError(f"{var_name}不是列表类型")

            if index < 0 or index >= len(data_list):
                raise IndexError(f"索引 {index} 超出了 {var_name} 的范围")

            return data_list[index]
        except Exception as e:
            with allure.step(f"获取批量数据失败: {var_name}[{index}]"):
                allure.attach(str(e), "错误信息", allure.attachment_type.TEXT)
            raise RuntimeError(f"Failed: 获取批量数据异常（{var_name}[{index}]）") from e

    def assert_data_lists_equal(self, actual, expected, fields_to_compare, tolerance=1e-9,
                                error_msg_prefix="数据列表不匹配"):
        """断言两个数据列表的指定字段相等（带Allure分层提示）"""
        actual_sorted = sorted(actual, key=lambda x: x["order_no"])
        expected_sorted = sorted(expected, key=lambda x: x["order_no"])

        with allure.step("断言数据列表相等"):
            allure.attach(f"比较字段: {fields_to_compare}", "比较维度", allure.attachment_type.TEXT)
            allure.attach(f"浮点数容差: {tolerance}", "精度设置", allure.attachment_type.TEXT)
            allure.attach(self.serialize_data(actual_sorted), "实际列表", allure.attachment_type.JSON)
            allure.attach(self.serialize_data(expected_sorted), "预期列表", allure.attachment_type.JSON)

        try:
            # assert len(actual_sorted) == len(expected_sorted), \
            #     f"Failed: {error_msg_prefix}（长度不匹配）"
            for a, e in zip(actual_sorted, expected_sorted):
                for field in fields_to_compare:
                    actual_val = a[field]
                    expected_val = e[field]

                    if isinstance(actual_val, float) and isinstance(expected_val, float):
                        assert abs(actual_val - expected_val) <= tolerance, \
                            f"Failed: {error_msg_prefix}（字段 {field} 精度不匹配）"
                    else:
                        assert actual_val == expected_val, \
                            f"Failed: {error_msg_prefix}（字段 {field} 值不匹配）"
        except AssertionError as e:
            with allure.step("数据列表断言失败"):
                allure.attach(str(e), "错误详情", allure.attachment_type.TEXT)
            raise e

    def assert_expected_in_actual(self, actual, expected, fields_to_compare, tolerance=1e-9,
                                  error_msg_prefix="预期数据不在实际列表中"):
        """
        断言预期列表的所有元素都包含在实际列表中（按order_no匹配，验证指定字段）
        :param actual: 实际数据列表（大列表）
        :param expected: 预期数据列表（子集列表）
        :param fields_to_compare: 需要验证的字段列表（如["magical", "open_price", "symbol"]）
        :param tolerance: 浮点数比较容差
        :param error_msg_prefix: 错误提示前缀
        """
        # 1. 预处理：将实际列表转为 {order_no: 元素} 的字典，方便快速查找（核心优化）
        actual_order_map = {item["order_no"]: item for item in actual}

        # 2. Allure 日志附件（保留分层提示）
        with allure.step("断言预期列表是实际列表的子集"):
            allure.attach(f"比较字段: {fields_to_compare}", "比较维度", allure.attachment_type.TEXT)
            allure.attach(f"浮点数容差: {tolerance}", "精度设置", allure.attachment_type.TEXT)
            allure.attach(self.serialize_data(actual), "实际列表（完整）", allure.attachment_type.JSON)
            allure.attach(self.serialize_data(expected), "预期列表（需包含）", allure.attachment_type.JSON)

        # 3. 遍历预期列表，逐个验证是否在实际列表中
        try:
            # 先断言预期列表非空（可选，根据需求决定是否保留）
            assert len(expected) > 0, f"{error_msg_prefix}：预期列表为空"

            for expected_item in expected:
                expected_order_no = expected_item["order_no"]

                # 步骤1：验证 order_no 在实际列表中存在
                assert expected_order_no in actual_order_map, \
                    f"{error_msg_prefix}：预期订单号 {expected_order_no} 未在实际列表中找到"

                # 步骤2：获取实际列表中对应的元素
                actual_item = actual_order_map[expected_order_no]

                # 步骤3：验证指定字段的值一致
                for field in fields_to_compare:
                    # 确保字段在两个元素中都存在（可选校验，避免KeyError）
                    assert field in actual_item, f"实际元素缺少字段: {field}（订单号: {expected_order_no}）"
                    assert field in expected_item, f"预期元素缺少字段: {field}（订单号: {expected_order_no}）"

                    actual_val = actual_item[field]
                    expected_val = expected_item[field]

                    # 浮点数精度比较，其他类型直接相等比较
                    if isinstance(actual_val, float) and isinstance(expected_val, float):
                        assert abs(actual_val - expected_val) <= tolerance, \
                            f"{error_msg_prefix}（订单号: {expected_order_no}）" \
                            f"字段 {field} 不匹配：实际={actual_val}, 预期={expected_val}, 容差={tolerance}"
                    else:
                        assert actual_val == expected_val, \
                            f"{error_msg_prefix}（订单号: {expected_order_no}）" \
                            f"字段 {field} 不匹配：实际={actual_val}, 预期={expected_val}"

            # 所有预期元素验证通过
            with allure.step("断言成功"):
                allure.attach(f"预期列表的 {len(expected)} 个元素均包含在实际列表中，且指定字段匹配", "结果",
                              allure.attachment_type.TEXT)

        except AssertionError as e:
            # 断言失败时，附加详细错误信息到Allure
            with allure.step("断言失败"):
                allure.attach(str(e), "错误详情", allure.attachment_type.TEXT)
            raise e

    def verify_data(
            self,
            actual_value,
            expected_value,
            op: CompareOp,
            message: str,
            attachment_name: str,
            attachment_type="text/plain",
            use_isclose=True,  # 新增参数：是否启用math.isclose容错（默认启用）
            rel_tol=1e-9,  # 相对容差（仅当use_isclose=True时生效）
            abs_tol=0  # 绝对容差（仅当use_isclose=True时生效）
    ):
        """
        通用数据校验函数，支持浮点容错比较
        :param actual_value: 实际值
        :param expected_value: 预期值
        :param op: 比较操作，CompareOp 枚举
        :param message: 校验失败时的提示信息
        :param attachment_name: Allure 附件名称
        :param attachment_type: Allure 附件类型，默认文本
        :param use_isclose: 是否使用math.isclose进行浮点容错比较
        :param rel_tol: 相对容差（默认1e-9）
        :param abs_tol: 绝对容差（默认0.0）
        其他参数同前
        """
        with allure.step(f"校验: {message}"):
            result = False
            try:
                # 处理浮点容错比较（仅对EQ/NE操作生效）
                if use_isclose and op in (CompareOp.EQ, CompareOp.NE):
                    if not (isinstance(actual_value, (int, float)) and
                            isinstance(expected_value, (int, float))):
                        # 非数字类型自动禁用isclose，避免报错
                        use_isclose = False
                        logging.warning(f"自动禁用isclose：非数字类型比较（实际值类型：{type(actual_value)}）")

                    # 计算isclose结果
                    is_close = math.isclose(
                        actual_value,
                        expected_value,
                        rel_tol=rel_tol,
                        abs_tol=abs_tol
                    )
                    # 根据操作类型取反
                    result = is_close if op == CompareOp.EQ else not is_close

                # 普通比较逻辑
                else:
                    if op == CompareOp.EQ:
                        result = actual_value == expected_value
                    elif op == CompareOp.NE:
                        result = actual_value != expected_value
                    elif op == CompareOp.GT:
                        result = actual_value > expected_value
                    elif op == CompareOp.LT:
                        result = actual_value < expected_value
                    elif op == CompareOp.GE:
                        result = actual_value >= expected_value
                    elif op == CompareOp.LE:
                        result = actual_value <= expected_value
                    elif op == CompareOp.IN:
                        result = actual_value in expected_value
                    elif op == CompareOp.NOT_IN:
                        result = actual_value not in expected_value

            except TypeError as e:
                print(
                    f"校验类型错误: {str(e)}\n实际值类型: {type(actual_value)}, 预期值类型: {type(expected_value)}")

            # 生成详细提示信息（包含容差参数）
            detail_msg = (
                f"\n实际: {actual_value}\n"
                f"操作: {op.value}\n"
                f"预期: {expected_value}\n"
            )

            # 添加allure.attach，将信息写入报告
            allure.attach(
                detail_msg,  # 附件内容
                name=attachment_name,  # 附件名称（来自参数）
                attachment_type=attachment_type  # 附件类型
            )

            if not result:
                print(f"校验失败: {message}\n{detail_msg}")
            logging.info(f"校验通过: {message}\n{detail_msg}")
