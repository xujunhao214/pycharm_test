import time
import math
import allure
import logging
import pytest
import requests
import http.client
from lingkuan_refine.VAR.VAR import *
from lingkuan_refine.conftest import var_manager
from lingkuan_refine.commons.api_base import APITestBase  # 导入基础类
import requests
from lingkuan_refine.commons.jsonpath_utils import JsonPathUtils
import json

logger = logging.getLogger(__name__)
SKIP_REASON = "该用例暂时跳过"


# ------------------------------------
# 大模块2：VPS策略下单-平仓的订单方向验证
# ------------------------------------
@allure.feature("VPS策略下单-平仓的功能校验")
# @pytest.mark.skipif(True, reason=SKIP_REASON)
class TestVPSFollowDirection:
    @allure.story("场景2：平仓的订单方向功能验证-跟单是sell")
    @allure.description("""
    ### 用例说明
    - 前置条件：有vps策略和vps跟单
    - 操作步骤：
      1. 修改跟单账号的跟单方向为反向，进行开仓
      2. 跟单账号buy方向进行平仓，平仓失败，给出提示
      3. 跟单账号sell方向进行平仓，平仓成功
      4. 策略账号buy方向进行平仓
    - 预期结果：平仓的订单方向功能正确
    """)
    class TestReverseFollowClose_sell(APITestBase):
        @pytest.mark.url("vps")
        @allure.title("修改跟单账号为反向跟单")
        def test_follow_updateSlave(self, var_manager, logged_session, encrypted_password):
            with allure.step("1. 修改跟单方向为反向"):
                # 1. 修改跟单方向为反向followDirection 1:反向 0：正向
                new_user = var_manager.get_variable("new_user")
                vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
                vps_trader_id = var_manager.get_variable("vps_trader_id")
                vps_addslave_id = var_manager.get_variable("vps_addslave_id")
                platformId = var_manager.get_variable("platformId")
                data = {
                    "traderId": vps_trader_id,
                    "platform": new_user["platform"],
                    "account": vps_user_accounts_1,
                    "password": encrypted_password,
                    "remark": "",
                    "followDirection": 1,
                    "followMode": 1,
                    "remainder": 0,
                    "followParam": 1,
                    "placedType": 0,
                    "templateId": 1,
                    "followStatus": 1,
                    "followOpen": 1,
                    "followClose": 1,
                    "followRep": 0,
                    "fixedComment": "",
                    "commentType": "",
                    "digits": 0,
                    "cfd": "",
                    "forex": "",
                    "abRemark": "",
                    "id": vps_addslave_id,
                    "platformId": platformId
                }
                response = self.send_post_request(
                    logged_session,
                    '/subcontrol/follow/updateSlave',
                    json_data=data
                )
            with allure.step("2. 验证响应状态码和内容"):
                self.assert_response_status(response, 200, "修改跟单账号失败")
                self.assert_json_value(response, "$.msg", "success", "响应msg应为success")

        @pytest.mark.url("vps")
        @allure.title("策略账号开仓操作（反向跟单场景）")
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
                "totalNum": trader_ordersend["totalNum"],
                "totalSzie": trader_ordersend["totalSzie"],
                "startSize": trader_ordersend["startSize"],
                "endSize": trader_ordersend["endSize"],
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
        @allure.title("跟单账号平仓（buy方向，预期失败）")
        def test_trader_orderclose1(self, var_manager, logged_session):
            with allure.step("1. 发送跟单账号平仓请求（订单方向是buy）"):
                global new_user
                vps_addslave_id = var_manager.get_variable("vps_addslave_id")
                vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
                new_user = var_manager.get_variable("new_user")
                data = {
                    "flag": 0,
                    "intervalTime": 0,
                    "num": "",
                    "closeType": 2,
                    "remark": "",
                    "symbol": new_user["symbol"],
                    "type": 0,
                    "traderId": vps_addslave_id,
                    "account": vps_user_accounts_1
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
                    f"{vps_user_accounts_1}暂无可平仓订单",
                    f"{vps_user_accounts_1}暂无可平仓订单"
                )
                logging.info(f"{vps_user_accounts_1}暂无可平仓订单")

        @pytest.mark.url("vps")
        @allure.title("跟单账号平仓（sell方向，预期成功）")
        def test_trader_orderclose2(self, var_manager, logged_session):
            with allure.step("1. 发送跟单账号平仓请求（订单方向是sell）"):
                vps_addslave_id = var_manager.get_variable("vps_addslave_id")
                vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
                data = {
                    "flag": 0,
                    "intervalTime": 0,
                    "num": "",
                    "closeType": 2,
                    "remark": "",
                    "symbol": new_user["symbol"],
                    "type": 1,
                    "traderId": vps_addslave_id,
                    "account": vps_user_accounts_1
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
                logging.info("响应msg字段应为success")

        @pytest.mark.url("vps")
        @allure.title("策略账号平仓（buy方向，预期成功）")
        def test_trader_orderclose3(self, var_manager, logged_session):
            with allure.step("1. 发送策略账号平仓请求（订单方向是buy）"):
                vps_trader_id = var_manager.get_variable("vps_trader_id")
                data = {
                    "flag": 0,
                    "intervalTime": 0,
                    "num": "",
                    "closeType": 2,
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

    @allure.story("场景3：平仓的订单方向功能验证-跟单是buy")
    @allure.description("""
        ### 用例说明
        - 前置条件：有vps策略和vps跟单
        - 操作步骤：
          1. 修改跟单账号的跟单方向为正向，进行开仓
          2. 跟单账号sell方向进行平仓，平仓失败，给出提示
          3. 跟单账号buy方向进行平仓，平仓成功
          4. 策略账号buy方向进行平仓
        - 预期结果：平仓的订单方向功能正确
        """)
    class TestReverseFollowClose_buy(APITestBase):
        @pytest.mark.url("vps")
        @allure.title("修改跟单账号为正向跟单")
        def test_follow_updateSlave(self, var_manager, logged_session, encrypted_password):
            with allure.step("1. 修改跟单方向为正向"):
                # 1. 修改跟单方向正向followDirection 1:反向 0：正向
                new_user = var_manager.get_variable("new_user")
                vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
                vps_trader_id = var_manager.get_variable("vps_trader_id")
                vps_addslave_id = var_manager.get_variable("vps_addslave_id")
                platformId = var_manager.get_variable("platformId")
                data = {
                    "traderId": vps_trader_id,
                    "platform": new_user["platform"],
                    "account": vps_user_accounts_1,
                    "password": encrypted_password,
                    "remark": "",
                    "followDirection": 0,
                    "followMode": 1,
                    "remainder": 0,
                    "followParam": 1,
                    "placedType": 0,
                    "templateId": 1,
                    "followStatus": 1,
                    "followOpen": 1,
                    "followClose": 1,
                    "followRep": 0,
                    "fixedComment": "",
                    "commentType": "",
                    "digits": 0,
                    "cfd": "",
                    "forex": "",
                    "abRemark": "",
                    "id": vps_addslave_id,
                    "platformId": platformId
                }
                response = self.send_post_request(
                    logged_session,
                    '/subcontrol/follow/updateSlave',
                    json_data=data
                )
            with allure.step("2. 验证响应状态码和内容"):
                self.assert_response_status(response, 200, "修改跟单账号失败")
                self.assert_json_value(response, "$.msg", "success", "响应msg应为success")

        @pytest.mark.url("vps")
        @allure.title("策略账号开仓操作（正向跟单场景）")
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
                "totalNum": trader_ordersend["totalNum"],
                "totalSzie": trader_ordersend["totalSzie"],
                "startSize": trader_ordersend["startSize"],
                "endSize": trader_ordersend["endSize"],
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
        @allure.title("跟单账号平仓（sell方向，预期失败）")
        def test_trader_orderclose1(self, var_manager, logged_session):
            with allure.step("1. 发送跟单账号平仓请求（订单方向是sell）"):
                global new_user
                vps_addslave_id = var_manager.get_variable("vps_addslave_id")
                vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
                new_user = var_manager.get_variable("new_user")
                data = {
                    "flag": 0,
                    "intervalTime": 0,
                    "num": "",
                    "closeType": 2,
                    "remark": "",
                    "symbol": new_user["symbol"],
                    "type": 1,
                    "traderId": vps_addslave_id,
                    "account": vps_user_accounts_1
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
                    f"{vps_user_accounts_1}暂无可平仓订单",
                    f"{vps_user_accounts_1}暂无可平仓订单"
                )
                logging.info(f"{vps_user_accounts_1}暂无可平仓订单")

        @pytest.mark.url("vps")
        @allure.title("跟单账号平仓（buy方向，预期成功）")
        def test_trader_orderclose2(self, var_manager, logged_session):
            with allure.step("1. 发送跟单账号平仓请求（订单方向是buy）"):
                vps_addslave_id = var_manager.get_variable("vps_addslave_id")
                vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
                data = {
                    "flag": 0,
                    "intervalTime": 0,
                    "num": "",
                    "closeType": 2,
                    "remark": "",
                    "symbol": new_user["symbol"],
                    "type": 0,
                    "traderId": vps_addslave_id,
                    "account": vps_user_accounts_1
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
                logging.info("响应msg字段应为success")

        @pytest.mark.url("vps")
        @allure.title("策略账号平仓（buy方向，预期成功）")
        def test_trader_orderclose3(self, var_manager, logged_session):
            with allure.step("1. 发送策略账号平仓请求（订单方向是buy）"):
                vps_trader_id = var_manager.get_variable("vps_trader_id")
                data = {
                    "flag": 0,
                    "intervalTime": 0,
                    "num": "",
                    "closeType": 2,
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

    @allure.story("场景4：平仓的订单方向功能验证-平仓buy sell")
    @allure.description("""
            ### 用例说明
            - 前置条件：有vps策略和vps跟单
            - 操作步骤：
              1. 进行开仓
              2. 跟单账号sell方向进行平仓，平仓失败，给出提示
              3. 跟单账号buy sell方向进行平仓，平仓成功
              4. 策略账号buy方向进行平仓
            - 预期结果：平仓的订单方向功能正确
            """)
    class TestReverseFollowClose_all(APITestBase):
        @pytest.mark.url("vps")
        @allure.title("策略账号开仓操作（正向跟单场景）")
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
                "totalNum": trader_ordersend["totalNum"],
                "totalSzie": trader_ordersend["totalSzie"],
                "startSize": trader_ordersend["startSize"],
                "endSize": trader_ordersend["endSize"],
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
        @allure.title("跟单账号平仓（sell方向，预期失败）")
        def test_trader_orderclose1(self, var_manager, logged_session):
            with allure.step("1. 发送跟单账号平仓请求（订单方向是sell）"):
                global new_user
                vps_addslave_id = var_manager.get_variable("vps_addslave_id")
                vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
                new_user = var_manager.get_variable("new_user")
                data = {
                    "flag": 0,
                    "intervalTime": 0,
                    "num": "",
                    "closeType": 2,
                    "remark": "",
                    "symbol": new_user["symbol"],
                    "type": 1,
                    "traderId": vps_addslave_id,
                    "account": vps_user_accounts_1
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
                    f"{vps_user_accounts_1}暂无可平仓订单",
                    f"{vps_user_accounts_1}暂无可平仓订单"
                )
                logging.info(f"{vps_user_accounts_1}暂无可平仓订单")

        @pytest.mark.url("vps")
        @allure.title("跟单账号平仓（buy sell方向，预期成功）")
        def test_trader_orderclose2(self, var_manager, logged_session):
            with allure.step("1. 发送跟单账号平仓请求（订单方向是buy）"):
                vps_addslave_id = var_manager.get_variable("vps_addslave_id")
                vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
                data = {
                    "flag": 0,
                    "intervalTime": 0,
                    "num": "",
                    "closeType": 2,
                    "remark": "",
                    "symbol": new_user["symbol"],
                    "type": 2,
                    "traderId": vps_addslave_id,
                    "account": vps_user_accounts_1
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
                logging.info("响应msg字段应为success")

        @pytest.mark.url("vps")
        @allure.title("策略账号平仓（buy方向，预期成功）")
        def test_trader_orderclose3(self, var_manager, logged_session):
            with allure.step("1. 发送策略账号平仓请求（订单方向是buy）"):
                vps_trader_id = var_manager.get_variable("vps_trader_id")
                data = {
                    "flag": 0,
                    "intervalTime": 0,
                    "num": "",
                    "closeType": 2,
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