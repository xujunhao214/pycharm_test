import time
import math
import allure
import logging
import pytest
import re
from lingkuan_828.VAR.VAR import *
from lingkuan_828.conftest import var_manager
from lingkuan_828.commons.api_base import *
from lingkuan_828.commons.jsonpath_utils import *

logger = logging.getLogger(__name__)
SKIP_REASON = "该用例暂时跳过"


# ------------------------------------
# 大模块4：VPS策略下单-平仓的订单类型功能验证
# ------------------------------------
@allure.feature("VPS策略下单-平仓的功能校验")
# @pytest.mark.skipif(True, reason=SKIP_REASON)
class TestVPSOrderType:
    @allure.story("场景6：平仓的订单类型功能验证-MT4外部订单")
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
        def test_mt4_login(self, var_manager):
            global token_mt4, headers
            max_retries = 5  # 最大重试次数
            retry_interval = 5  # 重试间隔（秒）
            token_mt4 = None

            # 用于验证token格式的正则表达式（UUID格式）
            uuid_pattern = re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')

            for attempt in range(max_retries):
                try:
                    url = "https://mt4.mtapi.io/Connect?user=300151&password=Test123456&host=47.238.99.66&port=443&connectTimeoutSeconds=30"

                    headers = {
                        'Authorization': 'e5f9f574-fd0a-42bd-904b-3a7a088de27e',
                        'x-sign': '417B110F1E71BD2CFE96366E67849B0B',
                        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
                        'Content-Type': 'application/json',
                        'Accept': '*/*',
                        'Host': 'mt4.mtapi.io',
                        'Connection': 'keep-alive'
                    }

                    response = requests.request("GET", url, headers=headers, data={})
                    response_text = response.text.strip()  # 去除可能的空白字符

                    logging.info(f"第{attempt + 1}次登录尝试 - 响应内容: {response_text}")

                    # 验证响应是否为有效的UUID格式token
                    if uuid_pattern.match(response_text):
                        token_mt4 = response_text
                        logging.info(f"第{attempt + 1}次尝试成功 - 获取到token: {token_mt4}")
                        break
                    else:
                        logging.warning(f"第{attempt + 1}次尝试失败 - 无效的token格式: {response_text}")

                except Exception as e:
                    logging.error(f"第{attempt + 1}次尝试发生异常: {str(e)}")

                # 如果不是最后一次尝试，等待后重试
                if attempt < max_retries - 1:
                    logging.info(f"将在{retry_interval}秒后进行第{attempt + 2}次重试...")
                    time.sleep(retry_interval)

            # 最终验证结果
            if not token_mt4 or not uuid_pattern.match(token_mt4):
                logging.error(f"经过{max_retries}次尝试后，MT4登录仍失败")
                assert False, "MT4登录失败"
            else:
                print(f"登录MT4账号获取token: {token_mt4}")
                logging.info(f"登录MT4账号获取token: {token_mt4}")

        @allure.title("MT4平台开仓操作")
        def test_mt4_open(self, var_manager):
            url = f"https://mt4.mtapi.io/OrderSend?id={token_mt4}&symbol=XAUUSD&operation=Buy&volume=1&placedType=Client&price=0.00"

            payload = ""
            self.response = requests.request("GET", url, headers=headers, data=payload)
            self.json_utils = JsonPathUtils()
            self.response = self.response.json()
            ticket = self.json_utils.extract(self.response, "$.ticket")
            print(ticket)
            logging.info(ticket)

        @pytest.mark.url("vps")
        @allure.title("自研平台平仓-内部订单-预期失败")
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
        @allure.title("自研平台平仓-外部订单-预期成功")
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
