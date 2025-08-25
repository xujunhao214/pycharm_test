import allure
import logging
import pytest
import time
import math
from lingkuan_refine.VAR.VAR import *
from lingkuan_refine.conftest import var_manager
from lingkuan_refine.commons.api_base import APITestBase

logger = logging.getLogger(__name__)
SKIP_REASON = "该用例暂时跳过"


@allure.feature("VPS策略账号交易下单-平仓的功能校验")
class TestVPSMasOrderclose:
    @allure.story("场景10：平仓的订单类型功能校验-全部订单")
    @allure.description("""
       ### 测试说明
       - 前置条件：有vps策略和vps跟单
         1. 进行开仓，手数范围：0.1-1，总订单数量4
         2. 进行平仓-订单类型-外部订单
         3. 校验平仓的订单数，应该没有平仓订单
         4. 进行平仓-订单类型-全部订单
         5. 校验平仓的订单数,等于4
       - 预期结果：平仓的订单类型功能正确
       """)
    class TestVPStradingOrders10(APITestBase):
        @allure.title("VPS交易下单-复制下单请求")
        def test_copy_order_send(self, logged_session, var_manager):
            # 发送VPS交易下单-复制下单请求
            global symbol
            masOrderSend = var_manager.get_variable("masOrderSend")
            symbol = masOrderSend["symbol"]
            vps_trader_user_id = var_manager.get_variable("vps_trader_user_id")
            data = {
                "traderList": [vps_trader_user_id],
                "type": 0,
                "tradeType": 1,
                "intervalTime": 0,
                "symbol": symbol,
                "placedType": 0,
                "startSize": "0.10",
                "endSize": "1.00",
                "totalNum": "4",
                "totalSzie": "",
                "remark": ""
            }
            response = self.send_post_request(
                logged_session,
                '/bargain/masOrderSend',
                json_data=data
            )

            # 验证下单成功
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

        @allure.title("VPS交易下单-交易平仓-订单类型-外部订单")
        def test_copy_order_close(self, var_manager, logged_session):
            vps_trader_user_id = var_manager.get_variable("vps_trader_user_id")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 0,
                "num": "",
                "traderList": [vps_trader_user_id],
                "closeType": 1,
                "remark": "",
                "symbol": "XAUUSD",
                "type": 0
            }
            response = self.send_post_request(
                logged_session,
                '/bargain/masOrderClose',
                json_data=data
            )

            # 验证平仓成功
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

        @allure.title("数据库校验-交易平仓-主指令及订单详情数据检查-没有订单")
        def test_dbquery_orderSendclose(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情界面跟单账号数据"):
                new_user = var_manager.get_variable("new_user")
                sql = f"""
                           SELECT 
                                fod.size,
                                fod.close_no,
                                fod.magical,
                                fod.open_price,
                                fod.symbol,
                                fod.order_no,
                                fod.close_time,
                                foi.true_total_lots,
                                foi.order_no,
                                foi.operation_type,
                                foi.create_time,
                                foi.status,
                                foi.min_lot_size,
                                foi.max_lot_size,
                                foi.total_lots,
                                foi.master_order,
                                foi.total_orders
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
                db_data = self.wait_for_database_no_record(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="foi.create_time"
                )
            with allure.step("2. 数据校验"):
                assert len(db_data) == 0, f"平仓失败，应该没有平仓订单，结果有{len(db_data)}个订单"

        @allure.title("VPS交易下单-交易平仓-订单类型-内部订单")
        def test_copy_order_close2(self, var_manager, logged_session):
            vps_trader_user_id = var_manager.get_variable("vps_trader_user_id")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 0,
                "num": "",
                "traderList": [vps_trader_user_id],
                "closeType": 2,
                "remark": "",
                "symbol": "XAUUSD",
                "type": 0
            }
            response = self.send_post_request(
                logged_session,
                '/bargain/masOrderClose',
                json_data=data
            )

            # 验证平仓成功
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

        @allure.title("数据库校验-交易平仓-主指令及订单详情数据检查-有4个订单")
        def test_dbquery_orderSendclose2(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情界面跟单账号数据"):
                new_user = var_manager.get_variable("new_user")
                sql = f"""
                           SELECT 
                               fod.size,
                               fod.close_no,
                               fod.magical,
                               fod.open_price,
                               fod.symbol,
                               fod.order_no,
                               fod.close_time,
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
                assert len(db_data) == 4, f"平仓的订单数量功能错误，应该有4个平仓订单，结果有{len(db_data)}个订单"

        @allure.title("数据库校验-交易平仓-跟单指令及订单详情数据检查-有4个订单")
        def test_dbquery_addsalve_orderSendclose2(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情界面跟单账号数据"):
                vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
                vps_addslave_id = var_manager.get_variable("vps_addslave_id")
                sql = f"""
                            SELECT 
                                fod.size,
                                fod.close_no,
                                fod.magical,
                                fod.open_price,
                                fod.symbol,
                                fod.order_no,
                                fod.close_time,
                                foi.true_total_lots,
                                foi.order_no,
                                foi.operation_type,
                                foi.create_time,
                                foi.status,
                                foi.min_lot_size,
                                foi.max_lot_size,
                                foi.total_lots,
                                foi.master_order,
                                foi.total_orders
                            FROM 
                                follow_order_detail fod
                            INNER JOIN 
                                follow_order_instruct foi 
                            ON 
                                foi.order_no = fod.close_no COLLATE utf8mb4_0900_ai_ci
                            WHERE foi.operation_type = %s
                                AND fod.account = %s
                                AND fod.trader_id = %s
                                """
                params = (
                    '1',
                    vps_user_accounts_1,
                    vps_addslave_id,
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="foi.create_time"
                )
            with allure.step("2. 数据校验"):
                assert len(db_data) == 4, f"平仓的订单数量功能错误，应该有4个平仓订单，结果有{len(db_data)}个订单"