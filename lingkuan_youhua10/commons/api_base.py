# lingkuan_youhua10/commons/api_base.py
import allure
import logging
import time
from typing import Dict, Any, List, Optional
from lingkuan_youhua10.commons.wait_utils import wait_for_condition

logger = logging.getLogger(__name__)


class APITestBase:
    """API测试基础类，封装通用测试方法"""

    def send_post_request(self, api_session, url, json_data=None, data=None, files=None, sleep_seconds=3):
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

    def send_get_request(self, api_session, url, params=None, sleep_seconds=3):
        """发送GET请求并返回响应"""
        with allure.step(f"发送GET请求到 {url}"):
            response = api_session.get(url, params=params)
            allure.attach(str(params), "请求参数", allure.attachment_type.JSON)
            self._log_response(response)
            time.sleep(sleep_seconds)
            return response

    def send_delete_request(self, api_session, url, json_data=None, sleep_seconds=3):
        """发送DELETE请求并返回响应"""
        with allure.step(f"发送DELETE请求到 {url}"):
            response = api_session.delete(url, json=json_data)
            allure.attach(str(json_data), "请求参数", allure.attachment_type.JSON)
            self._log_response(response)
            time.sleep(sleep_seconds)
            return response

    def send_put_request(self, api_session, url, json_data=None, sleep_seconds=3):
        """发送PUT请求并返回响应"""
        with allure.step(f"发送PUT请求到 {url}"):
            response = api_session.put(url, json=json_data)
            allure.attach(str(json_data), "请求参数", allure.attachment_type.JSON)
            self._log_response(response)
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
        actual_value = response.extract_jsonpath(json_path)
        assert actual_value == expected_value, (
            f"{error_msg}\n"
            f"实际值: {actual_value}\n"
            f"期望值: {expected_value}"
        )

    def query_database(self, db_transaction, sql, params, time_field: Optional[str] = None,
                       time_range_minutes: int = 3):
        """
        统一的数据库查询方法，支持添加时间范围过滤

        Args:
            db_transaction: 数据库事务对象
            sql: SQL查询语句
            params: 查询参数
            time_field: 时间字段名，若提供则自动添加时间范围条件
            time_range_minutes: 时间范围（分钟），默认±3分钟
        """
        # 如果指定了时间字段，则动态添加时间范围条件
        if time_field:
            # 检查SQL中是否已包含WHERE子句
            if "WHERE" in sql.upper():
                # 已有WHERE子句，添加AND条件
                sql += f" AND {time_field} BETWEEN NOW() - INTERVAL %s MINUTE AND NOW() + INTERVAL %s MINUTE"
                params = params + (time_range_minutes, time_range_minutes)
            else:
                # 没有WHERE子句，添加WHERE条件
                sql += f" WHERE {time_field} BETWEEN NOW() - INTERVAL %s MINUTE AND NOW() + INTERVAL %s MINUTE"
                params = params + (time_range_minutes, time_range_minutes)

        with db_transaction.cursor() as cursor:
            cursor.execute(sql, params)
            result = cursor.fetchall()
            logger.info(f"数据库查询结果: {result}", extra={"sql": sql, "params": params})
            return result

    def query_database_with_time(self, db_transaction, sql, params, time_field=None, time_range=3):
        """带时间范围的数据库查询 - 与query_database功能类似，保留以保持兼容性"""
        return self.query_database(db_transaction, sql, params, time_field, time_range)

    # lingkuan_youhua10.commons.api_base.py

    def wait_for_database_record(self, db_transaction, sql, params, time_field=None, time_range=3, timeout=30,
                                 poll_interval=2):
        """等待数据库记录出现，并记录详细轮询过程"""
        start_time = time.time()

        logger.info(f"开始等待数据库记录，SQL: {sql}")
        logger.info(f"查询参数: {params}")

        def check_db():
            result = self.query_database(db_transaction, sql, params, time_field, time_range)
            elapsed = time.time() - start_time

            # 每次查询都记录实际结果和耗时
            logger.info(f"轮询#{int(elapsed // poll_interval + 1)}: "
                        f"耗时={elapsed:.2f}s, "
                        f"结果数量={len(result)}")

            return result

        return wait_for_condition(
            condition=check_db,
            timeout=timeout,
            poll_interval=poll_interval,
            error_message=f"数据库查询超时，未找到记录 (SQL: {sql}, PARAMS: {params})",
            step_title="等待数据库记录出现"
        )
