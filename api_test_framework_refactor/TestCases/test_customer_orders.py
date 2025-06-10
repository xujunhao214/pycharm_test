import allure
import pytest
import time
from typing import Any
import requests
from api_test_framework_refactor.Common.base_test import BaseTest
from api_test_framework_refactor.Common.log_handler import LogHandler
from api_test_framework_refactor.Common.sign_utils import generate_sign
from api_test_framework_refactor.VAR.VAR import *


@allure.epic("客服后台-全部订单-查询校验")
class TestCustomerOrders:
    @pytest.fixture(autouse=True, scope="class")  # 类级fixture，在setup_class前执行
    def setup_base_test_class(self):
        """类级fixture：初始化日志器和基类，绑定到self"""
        self.logger = LogHandler("customer_orders").logger  # 初始化日志器
        self.base_url = PROJCET_URL
        self.base_test = BaseTest(self.logger, self.base_url)  # 初始化基类

    def setup_class(self):
        """类级初始化：在fixture之后执行，确保self.logger存在"""
        self.logger.info("------------------ 开始执行测试类 ------------------")

    def _login(self) -> str:
        """登录并返回token"""
        self.logger.info("开始执行登录测试")
        body = {
            "userName": USERNAME,
            "password": PASSWD
        }
        sign_str, timestamp = generate_sign(
            app_key=app_key,
            authorization=TOKEN_WEIXIU,
            platform=platform,
            body=body,
            secret=secret
        )
        headers = {
            "Authorization": TOKEN_WEIXIU,
            "AppKey": app_key,
            "Platform": platform,
            "Timestamp": timestamp,
            "Sign": sign_str,
            "Content-Type": "application/json",
            "city": "0755"
        }
        r1 = self.base_test.send_request("POST", "/support/auth/login", json=body, headers=headers)
        results = self._extract_value(r1, "$.msg")
        assert "OK" == results, f"登录失败，返回信息: {results}"
        token = self._extract_value(r1, "$.data.token")
        self.logger.info(f"登录成功，获取到token: {token}")
        return token

    def _extract_value(self, response: requests.Response, jsonpath_expr: str) -> Any:
        """从响应中提取值"""
        try:
            from jsonpath_ng import parse
            json_data = response.json()
            matches = [match.value for match in parse(jsonpath_expr).find(json_data)]
            if not matches:
                raise ValueError(f"未找到匹配项: {jsonpath_expr}")
            return matches[0]
        except Exception as e:
            self.logger.error(f"提取值失败: {str(e)}", exc_info=True)
            raise

    @allure.title("登录测试")
    def test_auth_login(self):
        self.token = self._login()

    @allure.title("全部订单测试")
    @pytest.mark.dependency(depends=["test_auth_login"])
    def test_order_list(self):
        self.logger.info("开始执行全部订单列表测试")
        body = {
            "shopName": "",
            "status": "",
            "faultName": "",
            "phone": "",
            "orderId": "",
            "time": [],
            "startTime": "",
            "endTime": "",
            "maintainerId": "",
            "page": 1,
            "limit": 20
        }
        sign_str, timestamp = generate_sign(
            app_key=app_key,
            authorization=self.token,
            platform=platform,
            body=body,
            secret=secret
        )
        headers = {
            "Authorization": self.token,
            "AppKey": app_key,
            "Platform": platform,
            "Timestamp": timestamp,
            "Sign": sign_str,
            "Content-Type": "application/json",
            "city": "0755"
        }
        r1 = self.base_test.send_request("POST", "/support/order/order-list", json=body, headers=headers)
        results = self._extract_value(r1, "$.msg")
        assert "OK" == results, f"获取订单列表失败，返回信息: {results}"
        self.logger.info("获取订单列表成功")
        order_id = self._extract_value(r1, "$.data.orderList[0].orderId")
        shop_name = self._extract_value(r1, "$.data.orderList[0].shopName")
        maintainer_id = self._extract_value(r1, "$.data.orderList[0].maintainerId")
        self.logger.info(f"获取到订单号: {order_id}")
        self.logger.info(f"获取到店铺名称: {shop_name}")
        self.logger.info(f"获取到维修工ID: {maintainer_id}")
