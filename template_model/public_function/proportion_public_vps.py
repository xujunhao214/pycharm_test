import time
import math
import allure
import logging
import pytest
from template_model.VAR.VAR import *
from template_model.conftest import var_manager
from template_model.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("VPS策略下单")
class PublicVpsUtils(APITestBase):
    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-策略开仓")
    def test_trader_openorderSend(self, class_random_str, var_manager, logged_vps):
        # 1. 发送策略开仓请求
        trader_ordersend = var_manager.get_variable("trader_ordersend")
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        data = {
            "symbol": trader_ordersend["symbol"],
            "placedType": 0,
            "remark": class_random_str,
            "intervalTime": 0,
            "type": 0,
            "totalNum": trader_ordersend["totalNum"],
            "totalSzie": trader_ordersend["totalSzie"],
            "startSize": trader_ordersend["startSize"],
            "endSize": trader_ordersend["endSize"],
            "traderId": vps_trader_id
        }
        response = self.send_post_request(
            logged_vps,
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

    @allure.title("数据库校验-策略开仓-主指令及订单详情数据检查")
    def test_dbquery_orderSend(self, class_random_str, var_manager, dbvps_transaction):
        with allure.step("1. 数据库提取订单号和手数"):
            vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
            sql = f"""
                        SELECT 
                            fod.size,
                            fod.comment,
                            fod.send_no,
                            fod.magical,
                            fod.open_price,
                            fod.symbol,
                            fod.order_no,
                            foi.true_total_lots,
                            foi.order_no,
                            foi.operation_type,
                            foi.create_time,
                            foi.status,
                            foi.min_lot_size,
                            foi.max_lot_size,
                            foi.total_lots,
                            foi.total_orders
                        FROM 
                            follow_order_detail fod
                        INNER JOIN 
                            follow_order_instruct foi 
                        ON 
                            foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
                        WHERE foi.operation_type = %s
                            AND fod.account = %s
                            AND fod.comment = %s
                            """
            params = (
                '0',
                vps_user_accounts_1,
                class_random_str
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.queryvps_database_with_time_with_timezone(
                dbvps_transaction=dbvps_transaction,
                sql=sql,
                params=params,
                time_field="fod.open_time"
            )
        with allure.step("2. 提取数据库数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，订单可能没有入库")

            master_order = db_data[0]["master_order"]
            var_manager.set_runtime_variable("ticket_open", master_order)
            total_lots = db_data[0]["total_lots"]
            var_manager.set_runtime_variable("lots_open", total_lots)

    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-策略平仓")
    def test_trader_orderclose(self, var_manager, logged_vps):
        # 1. 发送全平订单平仓请求
        with allure.step("1. 策略账号发送全平订单请求"):
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
            data = {
                "isCloseAll": 1,
                "intervalTime": 0,
                "traderId": vps_trader_id,
                "account": vps_user_accounts_1
            }
            response = self.send_post_request(
                logged_vps,
                '/subcontrol/trader/orderClose',
                json_data=data,
            )

        with allure.step("2. 验证响应"):
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

    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-跟单平仓")
    def test_addtrader_orderclose(self, var_manager, logged_vps):
        # 1. 发送全平订单平仓请求
        with allure.step("1. 跟单账号发送全平订单请求"):
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            vps_user_accounts_2 = var_manager.get_variable("vps_user_accounts_2")
            data = {
                "isCloseAll": 1,
                "intervalTime": 0,
                "traderId": vps_addslave_id,
                "account": vps_user_accounts_2
            }
            response = self.send_post_request(
                logged_vps,
                '/subcontrol/trader/orderClose',
                json_data=data,
            )

        with allure.step("2. 验证响应"):
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

    @allure.title("数据库校验-策略平仓-主指令及订单详情数据检查")
    def test_dbquery_orderSendclose(self, class_random_str, var_manager, dbvps_transaction):
        with allure.step("1. 获取订单详情表账号数据"):
            vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
            sql = f"""
                       SELECT 
                           fod.size,
                           fod.comment,
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
                           AND fod.comment = %s
                           """
            params = (
                '1',
                vps_user_accounts_1,
                class_random_str
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.queryvps_database_with_time_with_timezone(
                dbvps_transaction=dbvps_transaction,
                sql=sql,
                params=params,
                time_field="fod.close_time"
            )
        with allure.step("2. 提取数据库数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，订单可能没有入库")

            master_order = db_data[0]["master_order"]
            var_manager.set_runtime_variable("ticket_open", master_order)
            total_lots = db_data[0]["total_lots"]
            var_manager.set_runtime_variable("lots_open", total_lots)
