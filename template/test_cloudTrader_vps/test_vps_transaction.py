import time
import math
import allure
import logging
import pytest
from template.VAR.VAR import *
from template.conftest import var_manager
from template.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("VPS策略交易下单-复制下单")
class TestVPSOrdersend(APITestBase):
    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    @allure.title("VPS交易下单-复制下单")
    def test_trader_openorderSend(self, var_manager, logged_vps):
        with allure.step("1. 发生策略开仓请求"):
            # 1. 发送策略开仓请求
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            data = {
                "traderList": [vps_trader_id],
                "type": 0,
                "tradeType": 1,
                "intervalTime": 100,
                "symbol": trader_ordersend["symbol"],
                "placedType": 0,
                "startSize": trader_ordersend["startSize"],
                "endSize": trader_ordersend["endSize"],
                "totalNum": trader_ordersend["totalNum"],
                "totalSzie": trader_ordersend["totalSzie"],
                "remark": "gendanshequ"
            }
            response = self.send_post_request(
                logged_vps,
                '/bargain/masOrderSend',
                json_data=data,
            )
        with allure.step("2. 验证响应状态码和内容"):
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

    @pytest.mark.retry(n=3, delay=5)
    @allure.title("数据库校验-策略开仓-主指令及订单详情数据检查")
    def test_dbquery_orderSend(self, var_manager, dbvps_transaction):
        with allure.step("1. 获取订单详情表账号数据"):
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
                "gendanshequ"
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.queryvps_database_with_time_with_timezone(
                dbvps_transaction=dbvps_transaction,
                sql=sql,
                params=params,
                time_field="fod.open_time"
            )
        with allure.step("2. 数据校验"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            if not db_data:
                pytest.fail("数据库查询结果为空，订单可能没有入库")

            with allure.step("验证订单状态"):
                status = db_data[0]["status"]
                self.verify_data(
                    actual_value=status,
                    expected_value=(0, 1),
                    op=CompareOp.IN,
                    message="订单状态应为0或1",
                    attachment_name="订单状态详情"
                )
                logging.info(f"订单状态验证通过: {status}")

            with allure.step("验证手数范围-开始手数"):
                max_lot_size = db_data[0]["max_lot_size"]
                self.verify_data(
                    actual_value=float(max_lot_size),
                    expected_value=float(0.01),
                    op=CompareOp.EQ,
                    message="开始手数应符合预期",
                    attachment_name="开始手数详情"
                )
                logging.info(f"开始手数验证通过: {trader_ordersend['startSize']}")

            with allure.step("验证手数范围-结束手数"):
                min_lot_size = db_data[0]["min_lot_size"]
                self.verify_data(
                    actual_value=float(min_lot_size),
                    expected_value=float(trader_ordersend["endSize"]),
                    op=CompareOp.EQ,
                    message="结束手数应符合预期",
                    attachment_name="结束手数详情"
                )
                logging.info(f"结束手数验证通过: {trader_ordersend['endSize']}")

            with allure.step("总订单数量校验"):
                total_orders = db_data[0]["total_orders"]
                totalNum = trader_ordersend["totalNum"]
                self.verify_data(
                    actual_value=float(total_orders),
                    expected_value=float(totalNum),
                    op=CompareOp.EQ,
                    message="总订单数量应符合预期",
                    attachment_name="总订单数量详情"
                )
                logging.info(f"总订单数量验证通过: {total_orders}")

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

    @allure.title("数据库校验-策略开仓-跟单指令及订单详情数据检查")
    def test_dbquery_addsalve_orderSend(self, var_manager, dbvps_transaction):
        with allure.step("1. 获取订单详情表账号数据"):
            vps_user_accounts_2 = var_manager.get_variable("vps_user_accounts_2")
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
                vps_user_accounts_2,
                "gendanshequ"
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.queryvps_database_with_time_with_timezone(
                dbvps_transaction=dbvps_transaction,
                sql=sql,
                params=params,
                time_field="fod.open_time"
            )

        with allure.step("2. 数据校验"):
            if not db_data:
                pytest.fail("数据库查询结果为空，订单可能没有入库")

            with allure.step("验证订单状态"):
                status = db_data[0]["status"]
                self.verify_data(
                    actual_value=status,
                    expected_value=(0, 1),
                    op=CompareOp.IN,
                    message="订单状态应为0或1",
                    attachment_name="订单状态详情"
                )
                logging.info(f"订单状态验证通过: {status}")

            with allure.step("验证详情总手数"):
                size = [record["size"] for record in db_data]
                total = sum(size)
                self.verify_data(
                    actual_value=float(total),
                    expected_value=float(0.01),
                    op=CompareOp.EQ,
                    message="详情总手数应符合预期",
                    attachment_name="详情总手数"
                )
                logging.info(f'订单详情总手数是：{total}')

            with allure.step("验证详情手数和指令手数一致"):
                size = [record["size"] for record in db_data]
                true_total_lots = [record["true_total_lots"] for record in db_data]
                self.assert_list_equal_ignore_order(
                    size,
                    true_total_lots,
                    f"手数不一致: 详情{size}, 指令{true_total_lots}"
                )
                logger.info(f"手数一致: 详情{size}, 指令{true_total_lots}")

    @allure.title("VPS交易下单-交易平仓")
    def test_trader_orderclose(self, var_manager, logged_vps):
        with allure.step("1. 策略账号发送全平订单请求"):
            # 1. 发送全平订单平仓请求
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            data = {
                "isCloseAll": 1,
                "intervalTime": 100,
                "traderList": [vps_trader_id]
            }
            response = self.send_post_request(
                logged_vps,
                '/bargain/masOrderClose',
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
                "intervalTime": 100,
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
    def test_dbquery_orderSendclose(self, var_manager, dbvps_transaction):
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
                "gendanshequ"
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.queryvps_database_with_time_with_timezone(
                dbvps_transaction=dbvps_transaction,
                sql=sql,
                params=params,
                time_field="fod.close_time"
            )
        with allure.step("2. 数据校验"):
            if not db_data:
                pytest.fail("数据库查询结果为空，订单可能没有入库")

            with allure.step("验证订单状态"):
                status = db_data[0]["status"]
                self.verify_data(
                    actual_value=status,
                    expected_value=(0, 1),
                    op=CompareOp.IN,
                    message="订单状态应为0或1",
                    attachment_name="订单状态详情"
                )
                logging.info(f"订单状态验证通过: {status}")

            with allure.step("验证详情总手数"):
                size = [record["size"] for record in db_data]
                total = sum(size)
                self.verify_data(
                    actual_value=float(total),
                    expected_value=float(0.01),
                    op=CompareOp.EQ,
                    message="详情总手数应符合预期",
                    attachment_name="详情总手数"
                )
                logging.info(f'订单详情总手数是：{total}')

    @allure.title("数据库校验-策略平仓-跟单指令及订单详情数据检查")
    def test_dbquery_addsalve_orderSendclose(self, var_manager, dbvps_transaction):
        with allure.step("1. 获取订单详情表账号数据"):
            vps_user_accounts_2 = var_manager.get_variable("vps_user_accounts_2")
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
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
            params = (
                '1',
                vps_user_accounts_2,
                vps_addslave_id,
                "gendanshequ"
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.queryvps_database_with_time_with_timezone(
                dbvps_transaction=dbvps_transaction,
                sql=sql,
                params=params,
                time_field="fod.close_time"
            )
        with allure.step("2. 数据校验"):
            if not db_data:
                pytest.fail("数据库查询结果为空，订单可能没有入库")

            with allure.step("验证订单状态"):
                status = db_data[0]["status"]
                self.verify_data(
                    actual_value=status,
                    expected_value=(0, 1),
                    op=CompareOp.IN,
                    message="订单状态应为0或1",
                    attachment_name="订单状态详情"
                )
                logging.info(f"订单状态验证通过: {status}")

            with allure.step("验证详情总手数"):
                size = [record["size"] for record in db_data]
                total = sum(size)
                self.verify_data(
                    actual_value=float(total),
                    expected_value=float(0.01),
                    op=CompareOp.EQ,
                    message="详情总手数应符合预期",
                    attachment_name="详情总手数"
                )
                logging.info(f'订单详情总手数是：{total}')

            with allure.step("验证详情手数和指令手数一致"):
                size = [record["size"] for record in db_data]
                true_total_lots = [record["true_total_lots"] for record in db_data]
                self.assert_list_equal_ignore_order(
                    size,
                    true_total_lots,
                    f"手数不一致: 详情{size}, 指令{true_total_lots}"
                )
                logger.info(f"手数一致: 详情{size}, 指令{true_total_lots}")
