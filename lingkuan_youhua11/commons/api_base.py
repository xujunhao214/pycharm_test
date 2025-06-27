import allure
import logging
import time
import json
from typing import Dict, Any, List, Optional
from jsonschema import validate as jsonschema_validate, ValidationError
from lingkuan_youhua11.commons.wait_utils import wait_for_condition

logger = logging.getLogger(__name__)


class APITestBase:
    """API测试基础类，封装通用测试方法"""

    def send_request(self, method, api_session, url, **kwargs):
        """统一的API请求方法，支持所有HTTP方法"""
        method = method.upper()
        with allure.step(f"发送{method}请求到 {url}"):
            # 提取sleep_seconds参数，避免传递给requests
            sleep_seconds = kwargs.pop("sleep_seconds", 3)

            # 记录请求参数
            request_data = {
                "method": method,
                "url": url,
                "params": kwargs.get("params"),
                "json": kwargs.get("json"),
                "data": kwargs.get("data"),
                "files": kwargs.get("files"),
            }

            # 添加请求日志和Allure附件
            logger.info(f"发送{method}请求: {url}, 参数: {request_data}")
            allure.attach(str(request_data), "请求参数", allure.attachment_type.JSON)

            # 处理JSON请求
            if "json" in kwargs and "files" not in kwargs:
                kwargs.setdefault("headers", {})
                kwargs["headers"].setdefault("Content-Type", "application/json; charset=utf-8")
                json_data = kwargs.pop("json")
                kwargs["data"] = json.dumps(json_data, ensure_ascii=False).encode("utf-8")
                logger.info(f"JSON请求体: {json_data}")

            # 发送请求（不再传递sleep_seconds）
            response = api_session.request(method, url, **kwargs)

            # 记录响应并添加到Allure报告
            self._log_response(response)

            # 等待指定秒数
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

            return response

    def send_post_request(self, api_session, url, json_data=None, data=None, files=None, sleep_seconds=3):
        """发送POST请求并返回响应"""
        return self.send_request("POST", api_session, url,
                                 json=json_data, data=data, files=files,
                                 sleep_seconds=sleep_seconds)

    def send_get_request(self, api_session, url, params=None, sleep_seconds=3):
        """发送GET请求并返回响应"""
        return self.send_request("GET", api_session, url,
                                 params=params, sleep_seconds=sleep_seconds)

    def send_delete_request(self, api_session, url, json_data=None, sleep_seconds=3):
        """发送DELETE请求并返回响应"""
        return self.send_request("DELETE", api_session, url,
                                 json=json_data, sleep_seconds=sleep_seconds)

    def send_put_request(self, api_session, url, json_data=None, sleep_seconds=3):
        """发送PUT请求并返回响应"""
        return self.send_request("PUT", api_session, url,
                                 json=json_data, sleep_seconds=sleep_seconds)

    def _log_response(self, response):
        """增强版响应日志记录，包含更详细的信息"""
        try:
            # 尝试解析JSON响应
            response_json = response.json()
            response_body = json.dumps(response_json, indent=2)
            content_type = "application/json"
        except:
            # 非JSON响应
            response_body = response.text
            content_type = response.headers.get("Content-Type", "text/plain")

        # 记录日志
        logger.info(f"响应状态码: {response.status_code}")
        logger.info(f"响应内容类型: {content_type}")
        logger.info(f"响应内容: {response_body}")

        # 添加到Allure报告
        allure.attach(
            f"状态码: {response.status_code}\n内容类型: {content_type}\n内容: {response_body}",
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

    def build_sql_condition(self, table, conditions, time_field=None, time_range=3):
        """
        构建SQL查询条件，支持动态添加时间范围
        返回：SQL语句, 参数元组
        """
        base_sql = f"SELECT * FROM {table} WHERE 1=1"
        sql_conditions = []
        params = []

        for key, value in conditions.items():
            if key == "like":  # 处理LIKE条件
                sql_conditions.append(f"{value['field']} LIKE %s")
                params.append(f"%{value['value']}%")
            else:
                sql_conditions.append(f"{key} = %s")
                params.append(value)

        # 添加时间范围条件
        if time_field:
            sql_conditions.append(f"{time_field} BETWEEN NOW() - INTERVAL %s MINUTE AND NOW() + INTERVAL %s MINUTE")
            params.extend([time_range, time_range])

        return f"{base_sql} {' AND '.join(sql_conditions)}", tuple(params)  # 将params转为元组

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

    def wait_for_db_record(self, db_transaction, table, conditions,
                           time_field="create_time", time_range=3,
                           timeout=30, poll_interval=2):
        """
        等待数据库记录出现，使用条件字典而非SQL字符串
        """
        sql, params = self.build_sql_condition(table, conditions, time_field, time_range)

        start_time = time.time()
        logger.info(f"开始等待数据库记录，表: {table}, 条件: {conditions}")

        def check_db():
            with db_transaction.cursor() as cursor:
                cursor.execute(sql, params)
                result = cursor.fetchall()
                elapsed = time.time() - start_time
                logger.info(f"轮询#{int(elapsed // poll_interval + 1)}: "
                            f"耗时={elapsed:.2f}s, "
                            f"结果数量={len(result)}")
                return result

        return wait_for_condition(
            condition=check_db,
            timeout=timeout,
            poll_interval=poll_interval,
            error_message=f"数据库查询超时，表: {table}, 条件: {conditions}",
            step_title=f"等待数据出现在 {table} 表中"
        )

    def verify_db_status(self, db_data, status_field="status", expected=1, error_msg="状态验证失败"):
        """验证数据库查询结果中的状态字段"""
        if not db_data:
            pytest.fail("数据库查询结果为空，无法验证状态")
        actual_status = db_data[0][status_field]
        if actual_status != expected:
            pytest.fail(f"{error_msg}: 期望{expected}，实际{actual_status}")
        allure.attach(f"状态验证通过: {actual_status}", "验证结果", allure.attachment_type.TEXT)

    def log_and_assert(self, condition, error_message):
        """带日志记录的断言"""
        logger.info(f"断言: {error_message}")
        assert condition, error_message

    def verify_response_schema(self, response, schema):
        """验证响应JSON是否符合指定模式"""
        try:
            response_json = response.json()
            jsonschema_validate(response_json, schema)
            logger.info("响应JSON格式验证通过")
            allure.attach(str(schema), "期望JSON格式", allure.attachment_type.JSON)
            return True
        except ValidationError as e:
            logger.error(f"响应JSON格式验证失败: {str(e)}")
            allure.attach(f"验证失败: {str(e)}", "JSON格式错误", allure.attachment_type.TEXT)
            return False

    def verify_list_size(self, items, expected_size, error_msg="列表大小不符合预期"):
        """验证列表大小"""
        actual_size = len(items)
        self.log_and_assert(
            actual_size == expected_size,
            f"{error_msg}: 期望大小 {expected_size}，实际 {actual_size}"
        )
        return actual_size
