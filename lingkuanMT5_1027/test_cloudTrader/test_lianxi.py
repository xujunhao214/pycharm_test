import allure
import logging
import pytest
import time
import math
from lingkuanMT5_1027.VAR.VAR import *
from lingkuanMT5_1027.conftest import var_manager
from lingkuanMT5_1027.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("云策略复制下单-开仓的场景校验-buy")
class TestCloudStrategyOrderbuy(APITestBase):
    @allure.story("场景6：平仓的订单数量功能校验-4")
    @allure.description("""
       ### 测试说明
       - 前置条件：有云策略和云跟单
         1. 进行开仓，手数范围：0.1-1，总订单数量4
         2. 进行平仓-订单数量2
         3. 校验平仓的订单数，应该等于2
         4. 进行平仓-订单数量2
         5. 校验平仓的订单数,等于4
       - 预期结果：平仓的订单数量功能正确
       """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    class TestcloudtradingOrders6(APITestBase):
        @allure.title("云策略-策略账号交易下单-复制下单请求")
        def test_copy_order_send(self, class_random_str, logged_session, var_manager):
            # 发送云策略-策略账号交易下单-复制下单请求
            global symbol
            masOrderSend = var_manager.get_variable("masOrderSend")
            symbol = masOrderSend["symbol"]
            MT5cloudTrader_user_ids_2 = var_manager.get_variable("MT5cloudTrader_user_ids_2")
            data = {
                "traderList": [MT5cloudTrader_user_ids_2],
                "type": 0,
                "tradeType": 1,
                "intervalTime": 0,
                "symbol": symbol,
                "placedType": 0,
                "startSize": "0.10",
                "endSize": "1.00",
                "totalNum": "4",
                "totalSzie": "",
                "remark": class_random_str
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

        @allure.title("云策略-策略账号交易下单-交易平仓-平仓2个订单")
        def test_copy_order_close(self, class_random_str, var_manager, logged_session):
            MT5cloudTrader_user_ids_2 = var_manager.get_variable("MT5cloudTrader_user_ids_2")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 0,
                "num": "2",
                "traderList": [MT5cloudTrader_user_ids_2],
                "closeType": 0,
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

        @allure.title("数据库校验-交易平仓-主指令及订单详情数据检查-有2个订单")
        def test_dbquery_tradersalve_orderSendclose(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                MT5cloudTrader_user_accounts_2 = var_manager.get_variable("MT5cloudTrader_user_accounts_2")
                MT5cloudTrader_MT5vps_ids_1 = var_manager.get_variable("MT5cloudTrader_MT5vps_ids_1")
                sql = f"""
                              SELECT 
                                  fod.size,
                                  fod.close_no,
                                  fod.magical,
                                  fod.open_price,
                                  fod.comment,
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
                                  AND fod.comment = %s
                                  """
                params = (
                    '1',
                    MT5cloudTrader_user_accounts_2,
                    MT5cloudTrader_MT5vps_ids_1,
                    class_random_str,
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="foi.create_time"
                )
            with allure.step("2. 数据校验"):
                self.verify_data(
                    actual_value=len(db_data),
                    expected_value=2,
                    op=CompareOp.EQ,
                    message=f"平仓的订单数量功能正确，应该有2个平仓订单",
                    attachment_name="订单数量详情"
                )
                logging.info(f"平仓的订单数量功能正确，应该有2个平仓订单，结果有{len(db_data)}个订单")

        @allure.title("数据库校验-交易平仓-跟单指令及订单详情数据检查-有2个订单")
        def test_dbquery_addsalve_orderSendclose(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                MT5cloudTrader_user_accounts_4 = var_manager.get_variable("MT5cloudTrader_user_accounts_4")
                MT5cloudTrader_MT5vps_ids_3 = var_manager.get_variable("MT5cloudTrader_MT5vps_ids_3")
                sql = f"""
                          SELECT 
                              fod.size,
                              fod.close_no,
                              fod.magical,
                              fod.open_price,
                              fod.comment,
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
                              AND fod.comment = %s
                              """
                params = (
                    '1',
                    MT5cloudTrader_user_accounts_4,
                    MT5cloudTrader_MT5vps_ids_3,
                    class_random_str,
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="foi.create_time"
                )
            with allure.step("2. 数据校验"):
                self.verify_data(
                    actual_value=len(db_data),
                    expected_value=2,
                    op=CompareOp.EQ,
                    message=f"平仓的订单数量功能正确，应该有2个平仓订单",
                    attachment_name="订单数量详情"
                )
                logging.info(f"平仓的订单数量功能正确，应该有2个平仓订单，结果有{len(db_data)}个订单")

        @allure.title("云策略-策略账号交易下单-交易平仓-平仓2个订单")
        def test_copy_order_close2(self, class_random_str, var_manager, logged_session):
            MT5cloudTrader_user_ids_2 = var_manager.get_variable("MT5cloudTrader_user_ids_2")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 0,
                "num": "2",
                "traderList": [MT5cloudTrader_user_ids_2],
                "closeType": 0,
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
        def test_dbquery_orderSendclose2(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                MT5cloudTrader_user_accounts_2 = var_manager.get_variable("MT5cloudTrader_user_accounts_2")
                sql = f"""
                           SELECT 
                               fod.size,
                               fod.close_no,
                               fod.magical,
                               fod.comment,
                               fod.open_price,
                               fod.symbol,
                               fod.order_no,
                               fod.close_time,
                               foi.true_total_lots,
                               foi.order_no,
                               foi.operation_type,
                               foi.create_time,
                               foi.status,
                               foi.total_orders
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
                    MT5cloudTrader_user_accounts_2,
                    class_random_str
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
                    pytest.fail("数据库查询结果为空，无法进行复制下单校验")

                with allure.step("验证订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=4,
                        op=CompareOp.EQ,
                        message=f"平仓的订单数量功能正确，应该有4个平仓订单",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"平仓的订单数量功能正确，应该有4个平仓订单，结果有{len(db_data)}个订单")

        @allure.title("数据库校验-交易平仓-跟单指令及订单详情数据检查-有4个订单")
        def test_dbquery_addsalve_orderSendclose2(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                MT5cloudTrader_user_accounts_4 = var_manager.get_variable("MT5cloudTrader_user_accounts_4")
                MT5cloudTrader_MT5vps_ids_3 = var_manager.get_variable("MT5cloudTrader_MT5vps_ids_3")
                sql = f"""
                            SELECT 
                                fod.size,
                                fod.close_no,
                                fod.magical,
                                fod.comment,
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
                                AND fod.comment = %s
                                """
                params = (
                    '1',
                    MT5cloudTrader_user_accounts_4,
                    MT5cloudTrader_MT5vps_ids_3,
                    class_random_str
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="foi.create_time"
                )
            with allure.step("2. 数据校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行复制下单校验")

                with allure.step("验证订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=4,
                        op=CompareOp.EQ,
                        message=f"平仓的订单数量功能正确，应该有4个平仓订单",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"平仓的订单数量功能正确，应该有4个平仓订单，结果有{len(db_data)}个订单")