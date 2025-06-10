# Common/base_test.py
import allure
import logging
import requests
from requests.exceptions import RequestException
from typing import Dict, Any, Optional


class BaseTest:
    def __init__(self, logger: logging.Logger, base_url: str):
        self.logger = logger
        self.base_url = base_url
        self.req_handler = self._init_request_handler()

    def _init_request_handler(self) -> requests.Session:
        """初始化带异常处理的请求处理器"""
        handler = requests.Session()
        return handler

    def send_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """统一请求方法，自动捕获异常并记录日志"""
        full_url = f"{self.base_url}{url}"

        # 记录请求信息
        self.logger.info(f"发送{method.upper()}请求到: {full_url}")
        self.logger.info(f"请求头: {kwargs.get('headers', {})}")
        self.logger.info(f"请求体: {kwargs.get('json', kwargs.get('data', {}))}")

        with allure.step(f"发送{method.upper()}请求: {full_url}"):
            allure.attach(str(kwargs.get('headers', {})), "请求头", allure.attachment_type.JSON)
            allure.attach(str(kwargs.get('json', kwargs.get('data', {}))), "请求体", allure.attachment_type.JSON)

            try:
                response = self.req_handler.request(method, full_url, **kwargs)
                self._log_response(response)
                return response
            except RequestException as e:
                self._log_exception(e, "请求异常")
                raise
            except Exception as e:
                self._log_exception(e, "系统异常")
                raise

    def _log_response(self, response: requests.Response) -> None:
        """记录正常响应日志"""
        self.logger.info(f"响应状态码: {response.status_code}")
        self.logger.info(f"响应内容: {response.text[:500]}")  # 截断长内容
        allure.attach(response.text, "响应内容", allure.attachment_type.JSON)

    def _log_exception(self, e: Exception, error_type: str) -> None:
        """记录异常日志"""
        self.logger.error(f"{error_type}: {str(e)}", exc_info=True)
        with allure.step(f"{error_type}详情"):
            allure.attach(
                f"错误类型: {type(e).__name__}\n错误信息: {str(e)}",
                "异常日志",
                allure.attachment_type.TEXT
            )
