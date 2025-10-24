import allure
import logging
import pytest
import time
import math
from lingkuan_MT5.VAR.VAR import *
from lingkuan_MT5.conftest import var_manager
from lingkuan_MT5.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("云策略复制下单-开仓的场景校验")
class TestCloudStrategyOrder:
    @allure.story("场景6：分配下单-手数0.1-1，总手数1")
    @allure.description("""
       ### 测试说明
       - 前置条件：有云策略和云跟单
         1. 进行开仓，手数范围0.1-1，总手数1
         2. 校验账号的数据是否正确
         3. 进行平仓
         4. 校验账号的数据是否正确
       - 预期结果：云策略分配下单功能正确
       """)
    class TestMasOrderSend6(APITestBase):
        @allure.title("云策略-分配下单操作")
        def test_allocation_place_order(self, logged_session, var_manager):
            """执行云策略分配下单操作并验证请求结果"""
            with allure.step("发送分配下单请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                MT5cloudTrader_traderList_2 = var_manager.get_variable("MT5cloudTrader_traderList_2")

                request_data = {
                    "id": cloudMaster_id,
                    "type": 0,
                    "tradeType": 0,
                    "cloudTraderId": [MT5cloudTrader_traderList_2],
                    "symbol": "XAUUSD",
                    "startSize": "0.10",
                    "endSize": "1.00",
                    "totalSzie": "1.00",
                    "remark": "changjing6",
                    "totalNum": 0
                }

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudOrderSend',
                    json_data=request_data
                )

            with allure.step("验证下单响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "分配下单响应msg字段应为success"
                )

        @allure.title("数据库校验-云策略-分配下单数据")
        def test_allocation_verify_db(self, var_manager, db_transaction):
            """验证分配下单后数据库中的订单数据正确性"""
            with allure.step("查询订单详情数据"):
                MT5cloudTrader_user_accounts_2 = var_manager.get_variable("MT5cloudTrader_user_accounts_2")
                sql = """
                           SELECT 
                               fod.size,
                               fod.send_no,
                               fod.magical,
                               fod.open_price,
                               fod.symbol,
                               fod.comment,
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
                params = ('0', MT5cloudTrader_user_accounts_2, "changjing6")

                # 轮询等待数据库记录
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )

            with allure.step("执行数据校验"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行校验")

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证手数范围-开始手数"):
                    max_lot_size = db_data[0]["max_lot_size"]
                    self.verify_data(
                        actual_value=float(max_lot_size),
                        expected_value=float(0.1),
                        op=CompareOp.EQ,
                        message="开始手数应符合预期",
                        attachment_name="开始手数详情"
                    )
                    logging.info(f"开始手数验证通过: {max_lot_size}")

                with allure.step("验证手数范围-结束手数"):
                    min_lot_size = db_data[0]["min_lot_size"]
                    self.verify_data(
                        actual_value=float(min_lot_size),
                        expected_value=float(trader_ordersend["endSize"]),
                        op=CompareOp.EQ,
                        message="结束手数应符合预期",
                        attachment_name="结束手数详情"
                    )
                    logging.info(f"结束手数验证通过: {min_lot_size}")

                with allure.step("验证指令总手数"):
                    total_lots = db_data[0]["total_lots"]
                    totalSzie = trader_ordersend["totalSzie"]
                    self.verify_data(
                        actual_value=float(total_lots),
                        expected_value=float(totalSzie),
                        op=CompareOp.EQ,
                        message="指令总手数应符合预期",
                        attachment_name="指令总手数详情"
                    )
                    logging.info(f"指令总手数验证通过: {total_lots}")

                with allure.step("验证详情总手数"):
                    totalSzie = trader_ordersend["totalSzie"]
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(totalSzie),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-云跟单-分配下单数据")
        def test_allocation_verify_dbadd(self, var_manager, db_transaction):
            """验证分配下单后数据库中的订单数据正确性"""
            with allure.step("查询订单详情数据"):
                MT5cloudTrader_user_accounts_4 = var_manager.get_variable("MT5cloudTrader_user_accounts_4")
                sql = """
                           SELECT 
                               fod.size,
                               fod.send_no,
                               fod.magical,
                               fod.open_price,
                               fod.symbol,
                               fod.comment,
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
                params = ('0', MT5cloudTrader_user_accounts_4, "changjing6")

                # 轮询等待数据库记录
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )

            with allure.step("执行数据校验"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行校验")

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证详情总手数"):
                    totalSzie = trader_ordersend["totalSzie"]
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(totalSzie),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("云策略-分配下单平仓操作")
        def test_allocation_close_order(self, logged_session, var_manager):
            """执行分配下单的平仓操作并验证结果"""
            with allure.step("发送平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                MT5cloudTrader_traderList_2 = var_manager.get_variable("MT5cloudTrader_traderList_2")

                request_data = {
                    "isCloseAll": 1,
                    "intervalTime": 100,
                    "id": f"{cloudMaster_id}",
                    "cloudTraderId": [MT5cloudTrader_traderList_2]
                }

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudOrderClose',
                    json_data=request_data
                )

            with allure.step("验证平仓响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "平仓响应msg字段应为success"
                )

        @allure.title("数据库校验-云策略-分配下单平仓数据")
        def test_allocation_verify_close_db(self, var_manager, db_transaction):
            """验证分配下单平仓后数据库中的订单数据正确性"""
            with allure.step("查询平仓订单数据"):
                MT5cloudTrader_user_accounts_4 = var_manager.get_variable("MT5cloudTrader_user_accounts_4")
                MT5cloudTrader_MT5vps_ids_3 = var_manager.get_variable("MT5cloudTrader_MT5vps_ids_3")

                sql = """
                           SELECT 
                               fod.size,
                               fod.close_no,
                               fod.magical,
                               fod.open_price,
                               fod.comment,
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
                               AND fod.comment = %s
                       """
                params = ('1', MT5cloudTrader_user_accounts_4, MT5cloudTrader_MT5vps_ids_3, "changjing6")

                # 轮询等待数据库记录
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )

            with allure.step("执行平仓数据校验"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行平仓校验")

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证详情总手数"):
                    totalSzie = trader_ordersend["totalSzie"]
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(totalSzie),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-云跟单-分配下单平仓数据")
        def test_allocation_verify_close_dbadd(self, var_manager, db_transaction):
            """验证分配下单平仓后数据库中的订单数据正确性"""
            with allure.step("查询平仓订单数据"):
                MT5cloudTrader_user_accounts_2 = var_manager.get_variable("MT5cloudTrader_user_accounts_2")
                MT5cloudTrader_MT5vps_ids_1 = var_manager.get_variable("MT5cloudTrader_MT5vps_ids_1")

                sql = """
                           SELECT 
                               fod.size,
                               fod.close_no,
                               fod.magical,
                               fod.open_price,
                               fod.comment,
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
                               AND fod.comment = %s
                               """
                params = ('1', MT5cloudTrader_user_accounts_2, MT5cloudTrader_MT5vps_ids_1, "changjing6")

                # 轮询等待数据库记录
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time",
                    timezone_offset=0
                )

            with allure.step("执行平仓数据校验"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行平仓校验")

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证详情总手数"):
                    totalSzie = trader_ordersend["totalSzie"]
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(totalSzie),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")