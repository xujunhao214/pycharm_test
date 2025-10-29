import time
import allure
import logging
import pytest
import re
from lingkuanMT5_1029.conftest import var_manager
from lingkuanMT5_1029.commons.api_base import *
import requests
from lingkuanMT5_1029.commons.jsonpath_utils import JsonPathUtils

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


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
        def test_trader_orderSend(self, class_random_str, var_manager, logged_session):
            # 1. 发送策略开仓请求
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
            data = {
                "symbol": trader_ordersend["symbol"],
                "placedType": 0,
                "remark": class_random_str,
                "intervalTime": 100,
                "type": 0,
                "totalNum": "5",
                "totalSzie": "",
                "startSize": "0.01",
                "endSize": "1",
                "traderId": MT5vps_trader_id
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
        def test_trader_orderclose(self, class_random_str, var_manager, logged_session):
            with allure.step("1. 发送全平订单平仓请求"):
                MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
                new_user = var_manager.get_variable("new_user")
                data = {
                    "flag": 0,
                    "intervalTime": 10000,
                    "closeType": 2,
                    "remark": "",
                    "symbol": "XAUUSD",
                    "type": 2,
                    "traderId": MT5vps_trader_id,
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
        @pytest.mark.retry(n=0, delay=0)
        @allure.title("平仓停止功能验证")
        def test_trader_stopOrder(self, class_random_str, var_manager, logged_session):
            with allure.step("1. 发送停止平仓请求"):
                MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
                params = {
                    "type": "1",
                    "traderId": MT5vps_trader_id
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
        def test_dbquery_orderSendclose(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                new_user = var_manager.get_variable("new_user")
                sql = f"""
                    SELECT 
                        fod.size,
                        fod.close_no,
                        fod.magical,
                        fod.comment,
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
                        AND fod.comment = %s
                        """
                params = (
                    '1',
                    new_user["account"],
                    class_random_str
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time",
                    timezone_offset=0
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

            time.sleep(10)

        @pytest.mark.url("vps")
        @allure.title("策略账号再次平仓操作")
        def test_trader_orderclose2(self, class_random_str, var_manager, logged_session):
            with allure.step("1. 发送全平订单平仓请求"):
                MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
                new_user = var_manager.get_variable("new_user")
                data = {
                    "flag": 0,
                    "intervalTime": 0,
                    "closeType": 2,
                    "remark": "",
                    "symbol": "XAUUSD",
                    "type": 2,
                    "traderId": MT5vps_trader_id,
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
        def test_addtrader_orderclose(self, class_random_str, var_manager, logged_session):
            # 1. 发送全平订单平仓请求
            MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
            MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
            data = {
                "isCloseAll": 1,
                "intervalTime": 100,
                "traderId": MT5vps_addslave_id,
                "account": MT5vps_user_accounts_1
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