import time
import allure
import logging
import pytest
from lingkuan_refine.conftest import var_manager
from lingkuan_refine.commons.api_base import *
from lingkuan_refine.commons.jsonpath_utils import JsonPathUtils

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"


@allure.feature("仪表盘")
class TestVPSOrderSend_newScenarios:
    @allure.story("场景5：复制下单-手数0.1-1，总手数5")
    @allure.description("""
        ### 测试说明
        - 前置条件：有云策略和云跟单
          1. 进行开仓，手数范围0.1-1，总手数5
          2. 校验账号的数据是否正确
          3. 进行平仓
          4. 校验账号的数据是否正确
        - 预期结果：账号的数据正确
        """)
    class TestCloudtradingOrders5(APITestBase):
        @allure.title("云策略交易下单-复制下单请求")
        def test_copy_order_send(self, logged_session, var_manager):
            # 发送云策略交易下单-复制下单请求
            masOrderSend = var_manager.get_variable("masOrderSend")
            cloudTrader_user_ids_2 = var_manager.get_variable("cloudTrader_user_ids_2")
            data = {
                "traderList": [cloudTrader_user_ids_2],
                "type": 0,
                "tradeType": 1,
                "intervalTime": 100,
                "symbol": masOrderSend["symbol"],
                "placedType": 0,
                "startSize": "0.1",
                "endSize": "1.00",
                "totalNum": "",
                "totalSzie": "5",
                "remark": "测试数据"
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

        @allure.title("数据库校验-交易下单-主指令及订单详情数据检查")
        def test_dbquery_orderSend(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
                sql = f"""
                           SELECT 
                               fod.size,
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
                               """
                params = (
                    '0',
                    cloudTrader_user_accounts_2,
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )
            with allure.step("2. 数据校验"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行复制下单校验")

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

                with allure.step("验证手数范围-开始手数"):
                    max_lot_size = db_data[0]["max_lot_size"]
                    self.verify_data(
                        actual_value=float(max_lot_size),
                        expected_value=float(0.10),
                        op=CompareOp.EQ,
                        message="开始手数应符合预期",
                        attachment_name="开始手数详情"
                    )
                    logging.info(f"开始手数验证通过: {trader_ordersend['startSize']}")

                with allure.step("验证指令总手数"):
                    total_lots = db_data[0]["total_lots"]
                    self.verify_data(
                        actual_value=float(total_lots),
                        expected_value=float(5),
                        op=CompareOp.EQ,
                        message="指令总手数应符合预期",
                        attachment_name="指令总手数详情"
                    )
                    logging.info(f"指令总手数验证通过: {total_lots}")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(5),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-交易下单-跟单指令及订单详情数据检查")
        def test_dbquery_addsalve_orderSend(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
                sql = f"""
                           SELECT 
                               fod.size,
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
                               """
                params = (
                    '0',
                    cloudTrader_user_accounts_4,
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )

            with allure.step("2. 数据校验"):
                with allure.step("验证指令总手数"):
                    total_lots = [record["total_lots"] for record in db_data]
                    total_lotssum = sum(total_lots)
                    self.verify_data(
                        actual_value=float(total_lotssum),
                        expected_value=float(5),
                        op=CompareOp.EQ,
                        message="指令总手数应符合预期",
                        attachment_name="指令总手数详情"
                    )
                    logging.info(f"指令总手数验证通过: {total_lots}")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(5),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("云策略交易下单-交易平仓")
        def test_copy_order_close(self, var_manager, logged_session):
            cloudTrader_user_ids_2 = var_manager.get_variable("cloudTrader_user_ids_2")
            # 发送平仓请求
            data = {
                "isCloseAll": 1,
                "intervalTime": 100,
                "traderList": [cloudTrader_user_ids_2]
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

        @allure.title("数据库校验-交易平仓-主指令及订单详情数据检查")
        def test_dbquery_orderSendclose(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
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
                    cloudTrader_user_accounts_2,
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

                with allure.step("验证指令总手数"):
                    true_total_lots = db_data[0]["true_total_lots"]
                    self.verify_data(
                        actual_value=float(true_total_lots),
                        expected_value=float(5),
                        op=CompareOp.EQ,
                        message="指令总手数应符合预期",
                        attachment_name="指令总手数详情"
                    )
                    logging.info(f"指令总手数验证通过: {true_total_lots}")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(5),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-交易平仓-跟单指令及订单详情数据检查")
        def test_dbquery_addsalve_orderSendclose(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
                cloudTrader_vps_ids_3 = var_manager.get_variable("cloudTrader_vps_ids_3")
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
                    cloudTrader_user_accounts_4,
                    cloudTrader_vps_ids_3,
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
                        expected_value=float(5),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

                with allure.step("验证详情手数和指令手数一致"):
                    size = [record["size"] for record in db_data]
                    true_total_lots = [record["true_total_lots"] for record in db_data]
                    self.assert_list_equal_ignore_order(
                        size,
                        true_total_lots,
                        f"手数不一致: 详情{size}, 指令{true_total_lots}"
                    )
                    logger.info(f"手数一致: 详情{size}, 指令{true_total_lots}")
