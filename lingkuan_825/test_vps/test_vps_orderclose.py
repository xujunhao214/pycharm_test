import time
import allure
import logging
import pytest
from lingkuan_825.conftest import var_manager
from lingkuan_825.commons.api_base import *
import requests
from lingkuan_825.commons.jsonpath_utils import JsonPathUtils

logger = logging.getLogger(__name__)
SKIP_REASON = "该用例暂时跳过"


# ------------------------------------
# 大模块1：VPS策略下单-停止平仓功能验证
# ------------------------------------
@allure.feature("VPS策略下单-平仓的功能校验")
# @pytest.mark.skipif(True, reason=SKIP_REASON)
class TestVPSCoreFunctionality:
    @allure.story("场景1：平仓的停止功能验证")
    @allure.description("""
    ### 用例说明
    - 前置条件：有vps策略和vps跟单
    - 操作步骤：
      1. 进行开仓，手数：0.01-1，总订单数量5
      2. 进行平仓，平仓时间修改为30秒
      3. 点击平仓的停止按钮，校验平仓订单数量不等于下单数量
      4. 再次进行平仓
    - 预期结果：平仓的停止功能正确
    """)
    class TestStopCloseFunctionality(APITestBase):
        @pytest.mark.url("vps")
        @allure.title("策略账号开仓操作")
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
                "totalNum": "5",
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
        @allure.title("策略账号平仓-时间间隔30秒")
        def test_trader_orderclose(self, var_manager, logged_session):
            with allure.step("1. 发送全平订单平仓请求"):
                vps_trader_id = var_manager.get_variable("vps_trader_id")
                new_user = var_manager.get_variable("new_user")
                data = {
                    "flag": 0,
                    "intervalTime": 10000,
                    "closeType": 2,
                    "remark": "",
                    "symbol": "XAUUSD",
                    "type": 2,
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

        @pytest.mark.url("vps")
        @pytest.mark.retry(n=3, delay=5)
        @allure.title("平仓停止功能验证")
        def test_trader_stopOrder(self, var_manager, logged_session):
            with allure.step("1. 发送停止平仓请求"):
                vps_trader_id = var_manager.get_variable("vps_trader_id")
                params = {
                    "type": "1",
                    "traderId": vps_trader_id
                }
                response = self.send_get_request(
                    logged_session,
                    '/subcontrol/trader/stopOrder',
                    params=params,
                )
            with allure.step("2. 验证响应"):
                self.assert_response_status(
                    response,
                    200,
                    "停止平仓失败"
                )
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

        @allure.title("数据库校验-停止平仓-平仓手数不等于开仓手数")
        def test_dbquery_orderSendclose(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                new_user = var_manager.get_variable("new_user")
                sql = f"""
                    SELECT 
                        fod.size,
                        fod.close_no,
                        fod.magical,
                        fod.open_price,
                        fod.symbol,
                        fod.order_no,
                        foi.true_total_lots,
                        foi.order_no,
                        foi.operation_type,
                        foi.create_time,
                        foi.status
                    FROM 
                        follow_order_detail fod
                    INNER JOIN 
                        follow_order_instruct foi 
                    ON 
                        foi.order_no = fod.close_no COLLATE utf8mb4_0900_ai_ci
                    WHERE foi.operation_type = %s
                        AND fod.account = %s
                        """
                params = (
                    '1',
                    new_user["account"],
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )
            with allure.step("2. 数据校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

                with allure.step("验证订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=5,
                        op=CompareOp.NE,
                        message=f"平仓的订单数量应该不是5",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"平仓的订单数量应该不是5，结果有{len(db_data)}个订单")

        @pytest.mark.url("vps")
        @allure.title("策略账号再次平仓操作")
        def test_trader_orderclose2(self, var_manager, logged_session):
            with allure.step("1. 发送全平订单平仓请求"):
                vps_trader_id = var_manager.get_variable("vps_trader_id")
                new_user = var_manager.get_variable("new_user")
                data = {
                    "flag": 0,
                    "intervalTime": 0,
                    "closeType": 2,
                    "remark": "",
                    "symbol": "XAUUSD",
                    "type": 2,
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

        @pytest.mark.url("vps")
        @allure.title("跟单账号平仓操作")
        def test_addtrader_orderclose(self, var_manager, logged_session):
            # 1. 发送全平订单平仓请求
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
            data = {
                "isCloseAll": 1,
                "intervalTime": 100,
                "traderId": vps_addslave_id,
                "account": vps_user_accounts_1
            }
            response = self.send_post_request(
                logged_session,
                '/subcontrol/trader/orderClose',
                json_data=data,
            )

            # 2. 验证响应
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
        @allure.title("策略账号开仓操作")
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
        @allure.title("跟单账号平仓-币种错误")
        def test_trader_symbol(self, var_manager, logged_session):
            with allure.step("1. 发送跟单账号平仓请求-币种错误"):
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
                    "symbol": "XAGEUR",
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
                    f"{vps_user_accounts_1}无此品种订单",
                    f"{vps_user_accounts_1}无此品种订单"
                )
                logging.info(f"{vps_user_accounts_1}无此品种订单")

        @pytest.mark.url("vps")
        @allure.title("跟单账号平仓-buy方向-预期失败")
        def test_trader_orderclose1(self, var_manager, logged_session):
            with allure.step("1. 发送跟单账号平仓请求，订单方向是buy"):
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
        @allure.title("跟单账号平仓-sell方向-预期成功")
        def test_trader_orderclose2(self, var_manager, logged_session):
            with allure.step("1. 发送跟单账号平仓请求，订单方向是sell"):
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
        @allure.title("策略账号平仓-buy方向-预期成功")
        def test_trader_orderclose3(self, var_manager, logged_session):
            with allure.step("1. 发送策略账号平仓请求，订单方向是buy"):
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
        @allure.title("策略账号开仓操作")
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
        @allure.title("跟单账号平仓-sell方向-预期失败")
        def test_trader_orderclose1(self, var_manager, logged_session):
            with allure.step("1. 发送跟单账号平仓请求，订单方向是sell"):
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
        @allure.title("跟单账号平仓-buy方向-预期成功")
        def test_trader_orderclose2(self, var_manager, logged_session):
            with allure.step("1. 发送跟单账号平仓请求，订单方向是buy"):
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
        @allure.title("策略账号平仓-buy方向-预期成功")
        def test_trader_orderclose3(self, var_manager, logged_session):
            with allure.step("1. 发送策略账号平仓请求，订单方向是buy"):
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
        @allure.title("策略账号开仓操作")
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
        @allure.title("跟单账号平仓-sell方向-预期失败")
        def test_trader_orderclose1(self, var_manager, logged_session):
            with allure.step("1. 发送跟单账号平仓请求，订单方向是sell"):
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
        @allure.title("跟单账号平仓-buy sell方向-预期成功")
        def test_trader_orderclose2(self, var_manager, logged_session):
            with allure.step("1. 发送跟单账号平仓请求，订单方向是buy"):
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
        @allure.title("策略账号平仓-buy方向-预期成功")
        def test_trader_orderclose3(self, var_manager, logged_session):
            with allure.step("1. 发送策略账号平仓请求，订单方向是buy"):
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


# ------------------------------------
# 大模块3：VPS策略下单-平仓的订单数量功能验证
# ------------------------------------
@allure.feature("VPS策略下单-平仓的功能校验")
# @pytest.mark.skipif(True, reason=SKIP_REASON)
class TestVPSOrderQuantityControl:
    @allure.story("场景5：平仓的订单数量功能验证")
    @allure.description("""
    ### 用例说明
    - 前置条件：有vps策略和vps跟单
    - 操作步骤：
      1. 进行开仓，开仓订单数量控制为两个
      2. 进行平仓，平仓一个
      3. 进行平仓，平仓一个
      4. 进行平仓，平仓一个，平仓失败，没有可平订单
    - 预期结果：平仓的订单数量功能正确
    """)
    class TestBatchCloseFunctionality(APITestBase):
        @pytest.mark.url("vps")
        @allure.title("策略开仓-订单数量为2")
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
                "totalNum": "2",
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
        @allure.title("策略平仓-第一次平仓-订单数量为1")
        def test_trader_orderclose1(self, var_manager, logged_session):
            with allure.step("1. 发送平仓请求-订单数量为1"):
                vps_trader_id = var_manager.get_variable("vps_trader_id")
                new_user = var_manager.get_variable("new_user")
                data = {
                    "flag": 0,
                    "intervalTime": 0,
                    "num": "1",
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

        @pytest.mark.url("vps")
        @allure.title("策略平仓-第二次平仓-订单数量为1")
        def test_trader_orderclose2(self, var_manager, logged_session):
            with allure.step("1. 发送平仓请求-订单数量为1"):
                vps_trader_id = var_manager.get_variable("vps_trader_id")
                new_user = var_manager.get_variable("new_user")
                data = {
                    "flag": 0,
                    "intervalTime": 0,
                    "num": "1",
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

        @pytest.mark.url("vps")
        @allure.title("策略平仓-第三次平仓-空单验证")
        def test_trader_orderclose3(self, var_manager, logged_session):
            with allure.step("1. 发送平仓请求-订单数量为1-预期失败"):
                vps_trader_id = var_manager.get_variable("vps_trader_id")
                new_user = var_manager.get_variable("new_user")
                data = {
                    "flag": 0,
                    "intervalTime": 0,
                    "num": "1",
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
                    f"{new_user['account']}暂无可平仓订单",
                    f"{new_user['account']}暂无可平仓订单"
                )
                logging.info(f"{new_user['account']}暂无可平仓订单")


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
            print(f"登录MT4账号获取token:{token_mt4}")
            logging.info(f"登录MT4账号获取token:{token_mt4}")

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

    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    class TestVPSInternalOrderType:
        @allure.story("场景7：平仓的订单类型功能验证-内部订单")
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
            @allure.title("策略开仓")
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
            @allure.title("vps策略平仓-外部订单-预期失败")
            def test_trader_orderclose1(self, var_manager, logged_session):
                with allure.step("1. 发送平仓请求"):
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
            @allure.title("vps策略平仓-内部订单-预期成功")
            def test_trader_orderclose2(self, var_manager, logged_session):
                with allure.step("1. 发送平仓请求"):
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

    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    class TestVPSAllOrderType:
        @allure.story("场景8：平仓的订单类型功能验证-全部订单")
        @allure.description("""
        ### 用例说明
        - 前置条件：有vps策略和vps跟单
        - 操作步骤：
          1. 进行开仓，开仓订单数量控制为1个
          2. 进行平仓，平仓的订单类型-外部订单-平仓失败
          3. 进行平仓，平仓的订单类型-全部订单-平仓成功
        - 预期结果：平仓的订单类型功能正确
        """)
        class TestAllOrderClose(APITestBase):
            @pytest.mark.url("vps")
            @allure.title("策略开仓")
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
            @allure.title("vps策略平仓-外部订单-预期失败")
            def test_trader_orderclose1(self, var_manager, logged_session):
                with allure.step("1. 发送平仓请求"):
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
            @allure.title("vps策略平仓-全部订单-预期成功")
            def test_trader_orderclose2(self, var_manager, logged_session):
                with allure.step("1. 发送平仓请求-全部订单"):
                    vps_trader_id = var_manager.get_variable("vps_trader_id")
                    new_user = var_manager.get_variable("new_user")
                    data = {
                        "flag": 0,
                        "intervalTime": 0,
                        "num": "1",
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


# ------------------------------------
# 大模块5：VPS策略下单-平仓的备注功能验证
# ------------------------------------
@allure.feature("VPS策略下单-平仓的功能校验")
# @pytest.mark.skipif(True, reason=SKIP_REASON)
class TestVPSCloseRemark:
    @allure.story("场景9：平仓的备注功能验证")
    @allure.description("""
    ### 用例说明
    - 前置条件：有vps策略和vps跟单
    - 操作步骤：
      1. 修改跟单账号的固定注释：ceshipingcangbeizhu
      2. 进行开仓
      3. 跟单账号进行平仓，平仓备注写：xxxxxxxx,平仓失败，给出提示
      4. 跟单账号进行平仓，平仓备注写：ceshipingcangbeizhu,平仓成功
      5. 策略账号进行平仓
    - 预期结果：平仓的备注功能正确
    """)
    class TestFixedCommentMatching(APITestBase):
        @pytest.mark.url("vps")
        @allure.title("修改跟单账号固定注释")
        def test_follow_updateSlave(self, var_manager, logged_session, encrypted_password):
            with allure.step("1. 修改跟单账号的固定注释为空"):
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
        @allure.title("策略开仓-带固定备注")
        def test_trader_orderSend(self, var_manager, logged_session):
            with allure.step("1. 发送策略开仓请求"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                vps_trader_id = var_manager.get_variable("vps_trader_id")
                data = {
                    "symbol": trader_ordersend["symbol"],
                    "placedType": 0,
                    "remark": "ceshipingcangbeizhu",
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
            with allure.step("2. 验证响应状态码和内容"):
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
        @allure.title("跟单账号平仓-错误备注-预期失败")
        def test_trader_orderclose1(self, var_manager, logged_session):
            with allure.step("1. 发送跟单账号平仓请求-错误备注"):
                global new_user
                vps_addslave_id = var_manager.get_variable("vps_addslave_id")
                vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
                new_user = var_manager.get_variable("new_user")
                data = {
                    "flag": 0,
                    "intervalTime": 0,
                    "num": "",
                    "closeType": 2,
                    "remark": "xxxxxxxx",
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
        @allure.title("跟单账号平仓-正确备注-预期成功")
        def test_trader_orderclose2(self, var_manager, logged_session):
            with allure.step("1. 发送跟单账号平仓请求-正确备注"):
                vps_addslave_id = var_manager.get_variable("vps_addslave_id")
                vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
                data = {
                    "flag": 0,
                    "intervalTime": 0,
                    "num": "",
                    "closeType": 2,
                    "remark": "ceshipingcangbeizhu",
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
        @allure.title("策略账号平仓-正确备注")
        def test_trader_orderclose3(self, var_manager, logged_session):
            with allure.step("1. 发送策略账号平仓请求"):
                vps_trader_id = var_manager.get_variable("vps_trader_id")
                data = {
                    "flag": 0,
                    "intervalTime": 0,
                    "num": "",
                    "closeType": 2,
                    "remark": "ceshipingcangbeizhu",
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

            time.sleep(25)
