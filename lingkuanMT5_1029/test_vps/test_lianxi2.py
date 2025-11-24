import allure
import logging
import pytest
import time
from lingkuanMT5_1029.conftest import var_manager
from lingkuanMT5_1029.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("VPS策略账号交易下单-开仓的场景校验")
class TestVPSMasOrdersend(APITestBase):
    @allure.story("场景6：复制下单-手数0.1-1，总订单5-停止功能")
    @allure.description("""
        ### 测试说明
        - 前置条件：有vps策略和vps跟单
          1. 进行开仓，手数范围0.1-1，总订单5-停止功能
          2. 点击停止
          3. 校验账号的下单总手数和数据库的手数，应该不相等
          4. 进行平仓
          5. 校验账号的数据是否正确
        - 预期结果：账号的数据正确
        """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    class TestVPStradingOrders6(APITestBase):
        @allure.title("VPS策略账号交易下单-复制下单")
        def test_copy_order_send(self, class_random_str, logged_session, var_manager):
            # 发送VPS策略账号交易下单-复制下单
            masOrderSend = var_manager.get_variable("masOrderSend")
            MT5vps_trader_user_id = var_manager.get_variable("MT5vps_trader_user_id")
            data = {
                "traderList": [MT5vps_trader_user_id],
                "type": 0,
                "tradeType": 1,
                "intervalTime": 10000,
                "symbol": masOrderSend["symbol"],
                "placedType": 0,
                "startSize": "0.1",
                "endSize": "1.00",
                "totalNum": "5",
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

        @allure.title("数据库查询-获取停止的order_no")
        def test_copy_verify_db(self, class_random_str, var_manager, db_transaction):
            """验证复制下单后数据库中的订单数据正确性"""
            with allure.step("查询复制订单详情数据"):
                global order_no
                MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
                sql = """
                        SELECT 
                            order_no
                        FROM 
                            follow_order_instruct
                        WHERE instruction_type = %s
                            AND cloud_type = %s
                            AND min_lot_size = %s
                            AND max_lot_size = %s
                            AND trader_id = %s
                            """
                params = ("1", "0", "1.00", "0.10", MT5vps_trader_id)

                # 轮询等待数据库记录
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="create_time"
                )

            with allure.step("执行复制下单数据校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行复制下单校验")

                # 订单状态校验
                order_no = db_data[0]["order_no"]
                print("order_no:", order_no)

        @allure.title("交易下单-停止操作")
        def test_cloudTrader_cloudStopOrder(self, class_random_str, logged_session, var_manager):
            """执行云策略复制下单操作并验证请求结果"""
            with allure.step("发送停止操作请求"):
                params = {
                    "type": "0",
                    "orderNo": order_no
                }

                response = self.send_get_request(
                    logged_session,
                    '/bargain/stopOrder',
                    params=params
                )

            with allure.step("验证停止操作响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

        @allure.title("数据库校验-交易下单-主指令及订单详情数据检查")
        def test_dbquery_orderSend(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                new_user = var_manager.get_variable("new_user")
                sql = f"""
                           SELECT 
                               fod.size,
                               fod.send_no,
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
                    new_user["account"],
                    class_random_str
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )
            with allure.step("2. 数据校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行复制下单校验")

                with allure.step("验证订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=5,
                        op=CompareOp.NE,
                        message=f"平仓的订单数量应该不是5",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"平仓的订单数量应该不是5，结果有{len(db_data)}个订单")

        @allure.title("数据库校验-交易下单-跟单指令及订单详情数据检查")
        def test_dbquery_addsalve_orderSend(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
                sql = f"""
                           SELECT 
                               fod.size,
                               fod.send_no,
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
                    MT5vps_user_accounts_1,
                    class_random_str
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )

            with allure.step("2. 数据校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行复制平仓校验")

                with allure.step("验证订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=5,
                        op=CompareOp.NE,
                        message=f"平仓的订单数量应该不是5",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"平仓的订单数量应该不是5，结果有{len(db_data)}个订单")

        @allure.title("VPS交易下单-交易平仓")
        def test_copy_order_close(self, class_random_str, var_manager, logged_session):
            MT5vps_trader_user_id = var_manager.get_variable("MT5vps_trader_user_id")
            # 发送平仓请求
            data = {
                "isCloseAll": 1,
                "intervalTime": 100,
                "traderList": [MT5vps_trader_user_id]
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
        def test_dbquery_orderSendclose(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                new_user = var_manager.get_variable("new_user")
                sql = f"""
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
                    time_field="fod.close_time"
                )
            with allure.step("2. 数据校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行复制平仓校验")

                with allure.step("验证订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=5,
                        op=CompareOp.NE,
                        message=f"平仓的订单数量应该不是5",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"平仓的订单数量应该不是5，结果有{len(db_data)}个订单")

        @allure.title("数据库校验-交易平仓-跟单指令及订单详情数据检查")
        def test_dbquery_addsalve_orderSendclose(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
                MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
                sql = f"""
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
                params = (
                    '1',
                    MT5vps_user_accounts_1,
                    MT5vps_addslave_id,
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
                size = [record["size"] for record in db_data]
                true_total_lots = [record["true_total_lots"] for record in db_data]
                total_lots = [record["total_lots"] for record in db_data]
                self.assert_list_equal_ignore_order(
                    total_lots,
                    size,
                    true_total_lots,
                    f"手数不一致: 详情手数{size}, 总手数{total_lots}, 实际总手数{true_total_lots}"
                )
                logger.info(f"手数一致: 详情手数{size}, 总手数{total_lots}, 实际总手数{true_total_lots}")

                with allure.step("验证订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=5,
                        op=CompareOp.NE,
                        message=f"平仓的订单数量应该不是5",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"平仓的订单数量应该不是5，结果有{len(db_data)}个订单")
