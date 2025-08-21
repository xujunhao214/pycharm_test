import time
import math
import allure
import logging
import pytest
import requests
import http.client
from lingkuan_818.VAR.VAR import *
from lingkuan_818.conftest import var_manager
from lingkuan_818.commons.api_base import APITestBase  # 导入基础类
import requests
from lingkuan_818.commons.jsonpath_utils import JsonPathUtils
import json

logger = logging.getLogger(__name__)
SKIP_REASON = "该用例暂时跳过"


@allure.feature("VPS策略下单-平仓的功能校验")
# @pytest.mark.skipif(True, reason=SKIP_REASON)
class TestVPSOrderType:
    @allure.story("场景6：平仓的订单类型功能验证（MT4外部订单）")
    @allure.description("""
    ### 用例说明
    - 前置条件：有vps策略和vps跟单
    - 操作步骤：
      1. 登录MT4账号
      2. 使用mt4接口进行开仓
      3. 在自研平台进行平仓-订单类型-内部订单，平仓失败
      4. 在自研平台进行平仓-订单类型-外部订单，平仓成功
    - 预期结果：平仓的订单类型功能正确
    """)
    class TestMT4ExternalOrderClose(APITestBase):
        @allure.title("登录MT4账号获取token")
        @pytest.mark.retry(n=3, delay=5)
        def test_mt4_login(self, var_manager):
            global token_mt4, headers
            url = "https://mt4.mtapi.io/Connect?user=300151&password=Test123456&host=47.238.99.66&port=443&connectTimeoutSeconds=30"

            payload = {}
            headers = {
                'Authorization': 'e5f9f574-fd0a-42bd-904b-3a7a088de27e',
                'x-sign': '417B110F1E71BD2CFE96366E67849B0B',
                'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
                'Content-Type': 'application/json',
                'Accept': '*/*',
                'Host': 'mt4.mtapi.io',
                'Connection': 'keep-alive'
            }

            response = requests.request("GET", url, headers=headers, data=payload)
            token_mt4 = response.text
            print(token_mt4)
            logging.info(token_mt4)

        @allure.title("MT4平台开仓操作")
        def test_mt4_open(self, var_manager):
            url = f"https://mt4.mtapi.io/OrderSend?id={token_mt4}&symbol=XAUUSD&operation=Buy&volume=1&placedType=Client&price=0.00"

            payload = ""
            self.response = requests.request("GET", url, headers=headers, data=payload)
            self.json_utils = JsonPathUtils()
            self.response = self.response.json()  # 解析JSON响应
            ticket = self.json_utils.extract(self.response, "$.ticket")
            print(ticket)
            logging.info(ticket)

        @pytest.mark.url("vps")
        @allure.title("自研平台平仓（内部订单，预期失败）")
        def test_trader_orderclose(self, var_manager, logged_session):
            with allure.step("1. 发送全平订单平仓请求"):
                vps_trader_id = var_manager.get_variable("vps_trader_id")
                new_user = var_manager.get_variable("new_user")
                data = {
                    "flag": 0,
                    "intervalTime": 0,
                    "num": "1",
                    "closeType": 0,
                    "remark": "",
                    "symbol": "XAUUSD",
                    "type": 0,
                    "traderId": vps_trader_id,
                    "account": new_user["account"]
                }
                response = self.send_post_request(
                    logged_session,
                    '/subcontrol/trader/orderClose',
                    json_data=data,
                )
            with allure.step("2. 验证响应"):
                self.assert_response_status(response, 200, "平仓失败")
                self.assert_json_value(response, "$.msg", f"{new_user['account']}暂无可平仓订单",
                                       f"响应msg字段应为{new_user['account']}暂无可平仓订单")

        @pytest.mark.url("vps")
        @allure.title("自研平台平仓（外部订单，预期成功）")
        def test_trader_orderclose2(self, var_manager, logged_session):
            with allure.step("1. 发送全平订单平仓请求"):
                vps_trader_id = var_manager.get_variable("vps_trader_id")
                new_user = var_manager.get_variable("new_user")
                data = {
                    "flag": 0,
                    "intervalTime": 0,
                    "num": "1",
                    "closeType": 1,
                    "remark": "",
                    "symbol": "XAUUSD",
                    "type": 0,
                    "traderId": vps_trader_id,
                    "account": new_user["account"]
                }
                response = self.send_post_request(
                    logged_session,
                    '/subcontrol/trader/orderClose',
                    json_data=data,
                )
            with allure.step("2. 验证响应"):
                self.assert_response_status(response, 200, "平仓失败")
                self.assert_json_value(response, "$.msg", "success", "响应msg字段应为success")

    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    class TestVPSInternalOrderType:
        @allure.story("场景7：平仓的订单类型功能验证（内部订单）")
        @allure.description("""
        ### 用例说明
        - 前置条件：有vps策略和vps跟单
        - 操作步骤：
          1. 进行开仓，开仓订单数量控制为1个
          2. 进行平仓，平仓的订单类型-外部订单-平仓失败
          3. 进行平仓，平仓的订单类型-内部订单-平仓成功
        - 预期结果：平仓的订单类型功能正确
        """)
        class TestInternalOrderClose(APITestBase):
            @pytest.mark.url("vps")
            @allure.title("策略开仓（1单，内部订单）")
            def test_trader_orderSend(self, var_manager, logged_session):
                # 1. 发送策略开仓请求
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                vps_trader_id = var_manager.get_variable("vps_trader_id")
                data = {
                    "symbol": trader_ordersend["symbol"],
                    "placedType": 0,
                    "remark": trader_ordersend["remark"],
                    "intervalTime": 100,
                    "type": 0,
                    "totalNum": "1",
                    "totalSzie": "",
                    "startSize": "0.01",
                    "endSize": "1",
                    "traderId": vps_trader_id
                }
                response = self.send_post_request(
                    logged_session,
                    '/subcontrol/trader/orderSend',
                    json_data=data,
                )

                # 2. 验证响应状态码和内容
                self.assert_response_status(
                    response,
                    200,
                    "策略开仓失败"
                )
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

            @pytest.mark.url("vps")
            @allure.title("平仓（外部订单，预期失败）")
            def test_trader_orderclose1(self, var_manager, logged_session):
                with allure.step("1. 发送平仓请求（外部订单）"):
                    vps_trader_id = var_manager.get_variable("vps_trader_id")
                    new_user = var_manager.get_variable("new_user")
                    data = {
                        "flag": 0,
                        "intervalTime": 0,
                        "num": "1",
                        "closeType": 1,
                        "remark": "",
                        "symbol": new_user["symbol"],
                        "type": 0,
                        "traderId": vps_trader_id,
                        "account": new_user["account"]
                    }
                    response = self.send_post_request(
                        logged_session,
                        '/subcontrol/trader/orderClose',
                        json_data=data,
                    )
                with allure.step("2. 验证响应"):
                    self.assert_response_status(
                        response,
                        200,
                        "平仓失败"
                    )
                    self.assert_json_value(
                        response,
                        "$.msg",
                        f"{new_user['account']}暂无可平仓订单",
                        f"{new_user['account']}暂无可平仓订单"
                    )
                    logging.info(f"{new_user['account']}暂无可平仓订单")

            @pytest.mark.url("vps")
            @allure.title("平仓（内部订单，预期成功）")
            def test_trader_orderclose2(self, var_manager, logged_session):
                with allure.step("1. 发送平仓请求（内部订单）"):
                    vps_trader_id = var_manager.get_variable("vps_trader_id")
                    new_user = var_manager.get_variable("new_user")
                    data = {
                        "flag": 0,
                        "intervalTime": 0,
                        "num": "1",
                        "closeType": 0,
                        "remark": "",
                        "symbol": new_user["symbol"],
                        "type": 0,
                        "traderId": vps_trader_id,
                        "account": new_user["account"]
                    }
                    response = self.send_post_request(
                        logged_session,
                        '/subcontrol/trader/orderClose',
                        json_data=data,
                    )
                with allure.step("2. 验证响应"):
                    self.assert_response_status(
                        response,
                        200,
                        "平仓失败"
                    )
                    self.assert_json_value(
                        response,
                        "$.msg",
                        "success",
                        "响应msg字段应为success"
                    )
