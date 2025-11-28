import allure
import logging
import pytest
import time
import math
from lingkuanMT5_1029copy.VAR.VAR import *
from lingkuanMT5_1029copy.conftest import var_manager
from lingkuanMT5_1029copy.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("云策略复制下单-开仓的场景校验-buy")
class TestCloudStrategyOrderbuy:
    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    @allure.story("场景10：复制下单-手数范围0.01-1，总手数0.3")
    @allure.description("""
    ### 测试说明
    - 前置条件：有云策略和云跟单
      1. 修改跟单账号下单比例0.25，手数取余-四舍五入，合约比例0.5
      2. 进行开仓，手数范围0.01-1，总手数0.3
      3. 校验账号的数据是否正确-下单手数是0.3*0.25*0.5=0.0375，四舍五入是0.04
      4. 进行平仓
      5. 校验账号的数据是否正确
    - 预期结果：账号的数据正确
    """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    class TestMasOrderSend10(APITestBase):
        @allure.title("云策略-修改云跟单-四舍五入")
        def test_update_trader(self, class_random_str, logged_session, var_manager):
            """执行云策略复制下单操作并验证请求结果"""
            with allure.step("1.发送修改MT5账号云跟单请求"):
                MT5cloudTrader_traderList_4 = var_manager.get_variable("MT5cloudTrader_traderList_4")
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                MT5cloudTrader_user_accounts_2 = var_manager.get_variable("MT5cloudTrader_user_accounts_2")
                MT5cloudTrader_traderList_2 = var_manager.get_variable("MT5cloudTrader_traderList_2")
                MT5cloudTrader_template_id2 = var_manager.get_variable("MT5cloudTrader_template_id2")

                request_data = [
                    {
                        "traderList": [
                            MT5cloudTrader_traderList_4
                        ],
                        "cloudId": cloudMaster_id,
                        "masterId": MT5cloudTrader_traderList_2,
                        "masterAccount": MT5cloudTrader_user_accounts_2,
                        "followDirection": 0,
                        "followMode": 1,
                        "followParam": "0.25",
                        "remainder": 0,
                        "placedType": 0,
                        "templateId": MT5cloudTrader_template_id2,
                        "followStatus": 1,
                        "followOpen": 1,
                        "followClose": 1,
                        "fixedComment": None,
                        "commentType": None,
                        "digits": 0,
                        "followTraderIds": [],
                        "sort": 100,
                        "remark": "",
                        "cfd": None,
                        "forex": None,
                    }
                ]

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudBatchUpdate',
                    json_data=request_data
                )

            with allure.step("2.验证响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

            with allure.step("3.发送修改MT4账号云跟单请求"):
                cloudTrader_MT4traderID = var_manager.get_variable("cloudTrader_MT4traderID")
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                MT5cloudTrader_user_accounts_2 = var_manager.get_variable("MT5cloudTrader_user_accounts_2")
                MT5cloudTrader_traderList_2 = var_manager.get_variable("MT5cloudTrader_traderList_2")

                request_data = [
                    {
                        "traderList": [
                            cloudTrader_MT4traderID
                        ],
                        "cloudId": cloudMaster_id,
                        "masterId": MT5cloudTrader_traderList_2,
                        "masterAccount": MT5cloudTrader_user_accounts_2,
                        "followDirection": 0,
                        "followMode": 1,
                        "followParam": "0.25",
                        "remainder": 0,
                        "placedType": 0,
                        "templateId": MT5cloudTrader_template_id2,
                        "followStatus": 1,
                        "followOpen": 1,
                        "followClose": 1,
                        "fixedComment": None,
                        "commentType": None,
                        "digits": "",
                        "followTraderIds": [],
                        "sort": 1,
                        "remark": "",
                        "cfd": None,
                        "forex": None
                    }
                ]

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudBatchUpdate',
                    json_data=request_data
                )

            with allure.step("4.验证响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

        @allure.title("云策略-复制下单操作")
        def test_copy_place_order(self, class_random_str, logged_session, var_manager):
            """执行云策略复制下单操作并验证请求结果"""
            with allure.step("1.发送复制下单请求"):
                # tradeType: 0 分配下单  1  复制下单
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                MT5cloudTrader_traderList_2 = var_manager.get_variable("MT5cloudTrader_traderList_2")

                request_data = {
                    "id": cloudMaster_id,
                    "type": 0,
                    "tradeType": 1,
                    "intervalTime": 0,
                    "cloudTraderId": [MT5cloudTrader_traderList_2],
                    "symbol": "XAUUSD",
                    "placedType": 0,
                    "startSize": "0.01",
                    "endSize": "1.00",
                    "totalNum": "",
                    "totalSzie": "0.3",
                    "remark": class_random_str
                }

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudOrderSend',
                    json_data=request_data
                )

            with allure.step("2.验证复制下单响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

        @allure.title("数据库校验-云策略-复制下单数据")
        def test_copy_verify_db(self, class_random_str, var_manager, db_transaction):
            """验证复制下单后数据库中的订单数据正确性"""
            with allure.step("查询复制订单详情数据"):
                MT5cloudTrader_user_accounts_2 = var_manager.get_variable("MT5cloudTrader_user_accounts_2")
                sql = """
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
                params = ('0', MT5cloudTrader_user_accounts_2, class_random_str)

                # 轮询等待数据库记录
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )

            with allure.step("执行复制下单数据校验"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行复制下单校验")

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
                        expected_value=float(1),
                        op=CompareOp.EQ,
                        message="结束手数应符合预期",
                        attachment_name="结束手数详情"
                    )
                    logging.info(f"结束手数验证通过: {trader_ordersend['endSize']}")

                with allure.step("验证指令总手数"):
                    total_lots = db_data[0]["total_lots"]
                    self.verify_data(
                        actual_value=float(total_lots),
                        expected_value=float(0.3),
                        op=CompareOp.EQ,
                        message="指令总手数应符合预期",
                        attachment_name="指令总手数详情"
                    )
                    logging.info(f"指令总手数验证通过: {total_lots}")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(0.3),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-云跟单-复制下单数据")
        def test_copy_verify_dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单后数据库中的订单数据正确性"""
            with allure.step("查询复制订单详情数据"):
                MT5cloudTrader_user_accounts_4 = var_manager.get_variable("MT5cloudTrader_user_accounts_4")
                sql = """
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
                params = ('0', MT5cloudTrader_user_accounts_4, class_random_str)

                # 轮询等待数据库记录
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )

            with allure.step("执行复制下单数据校验"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行复制下单校验")

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
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(0.04),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-MT4账号云跟单-复制下单数据")
        def test_copy_verify_MT4dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单后数据库中的订单数据正确性"""
            with allure.step("查询复制订单详情数据"):
                addCloud_MT4Slave = var_manager.get_variable("addCloud_MT4Slave")
                account = addCloud_MT4Slave["account"]
                sql = """
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
                params = ('0', account, class_random_str)

                # 轮询等待数据库记录
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )

            with allure.step("执行复制下单数据校验"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行复制下单校验")

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
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(0.04),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("云策略-复制下单平仓操作")
        def test_copy_close_order(self, class_random_str, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("1.发送复制下单平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                MT5cloudTrader_traderList_2 = var_manager.get_variable("MT5cloudTrader_traderList_2")

                request_data = {
                    "isCloseAll": 1,
                    "intervalTime": 0,
                    "id": f"{cloudMaster_id}",
                    "cloudTraderId": [MT5cloudTrader_traderList_2]
                }

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudOrderClose',
                    json_data=request_data
                )

            with allure.step("2.验证复制平仓响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制平仓响应msg字段应为success"
                )

        @allure.title("数据库校验-云策略-复制下单平仓数据")
        def test_copy_verify_close_db(self, class_random_str, var_manager, db_transaction):
            """验证复制下单平仓后数据库中的订单数据正确性"""
            with allure.step("查询复制平仓订单数据"):
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
                params = ('1', MT5cloudTrader_user_accounts_2, MT5cloudTrader_MT5vps_ids_1, class_random_str)

                # 轮询等待数据库记录
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )

            with allure.step("执行复制平仓数据校验"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行复制平仓校验")

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
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(0.3),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-云跟单-复制下单平仓数据")
        def test_copy_verify_close_dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单平仓后数据库中的订单数据正确性"""
            with allure.step("查询复制平仓订单数据"):
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
                params = ('1', MT5cloudTrader_user_accounts_4, MT5cloudTrader_MT5vps_ids_3, class_random_str)

                # 轮询等待数据库记录
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )

            with allure.step("执行复制平仓数据校验"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行复制平仓校验")

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
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(0.04),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-MT4账号云跟单-复制下单平仓数据")
        def test_copy_verify_close_MT4dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单平仓后数据库中的订单数据正确性"""
            with allure.step("查询复制平仓订单数据"):
                addCloud_MT4Slave = var_manager.get_variable("addCloud_MT4Slave")
                account = addCloud_MT4Slave["account"]
                MT4vps_addslave_id = var_manager.get_variable("MT4vps_addslave_id")

                sql = """
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
                params = ('1', account, MT4vps_addslave_id, class_random_str)

                # 轮询等待数据库记录
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )

            with allure.step("执行复制平仓数据校验"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行复制平仓校验")

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
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(0.04),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")
