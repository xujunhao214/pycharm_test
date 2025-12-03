import allure
import logging
import pytest
import time
import math
from lingkuan_1127.VAR.VAR import *
from lingkuan_1127.conftest import var_manager
from lingkuan_1127.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("云策略复制下单-开仓的场景校验-buy")
class TestCloudStrategyOrderbuy:
    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    @allure.story("场景1：复制下单-手数0.1-1，总订单3，总手数1")
    @allure.description("""
    ### 测试说明
    - 前置条件：有云策略和云跟单
      1. 进行开仓，手数范围0.1-1，总订单3，总手数1
      2. 校验账号的数据是否正确
      3. 进行平仓
      4. 校验账号的数据是否正确
    - 预期结果：账号的数据正确
    """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    class TestMasOrderSend1(APITestBase):
        @allure.title("云策略列表-修改云跟单")
        def test_update_cloudtrader(self, class_random_str, logged_session, var_manager):
            """执行云策略复制下单操作并验证请求结果"""
            with allure.step("1.发送修改MT4账号云跟单请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")

                request_data = [
                    {
                        "traderList": [
                            cloudTrader_traderList_4
                        ],
                        "cloudId": cloudMaster_id,
                        "masterId": cloudTrader_traderList_2,
                        "masterAccount": cloudTrader_user_accounts_2,
                        "followDirection": 0,
                        "followMode": 1,
                        "followParam": "1",
                        "remainder": 0,
                        "placedType": 0,
                        "templateId": 1,
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
                        "forex": None
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

            with allure.step("3.发送修改MT5账号云跟单请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")
                cloudTrader_MT5traderID = var_manager.get_variable("cloudTrader_MT5traderID")
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")

                request_data = [
                    {
                        "traderList": [
                            cloudTrader_MT5traderID
                        ],
                        "cloudId": cloudMaster_id,
                        "masterId": cloudTrader_traderList_2,
                        "masterAccount": cloudTrader_user_accounts_2,
                        "followDirection": 0,
                        "followMode": 1,
                        "followParam": 1,
                        "remainder": 0,
                        "placedType": 0,
                        "templateId": 1,
                        "followStatus": 1,
                        "followOpen": 1,
                        "followClose": 1,
                        "fixedComment": None,
                        "commentType": None,
                        "digits": 0,
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
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")

                request_data = {
                    "id": cloudMaster_id,
                    "type": 0,
                    "tradeType": 1,
                    "intervalTime": 0,
                    "cloudTraderId": [cloudTrader_traderList_2],
                    "symbol": "XAUUSD",
                    "placedType": 0,
                    "startSize": "0.10",
                    "endSize": "1.00",
                    "totalNum": "3",
                    "totalSzie": "1.00",
                    "remark": class_random_str
                }

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudOrderSend',
                    json_data=request_data
                )

            with allure.step("2.验证响应结果"):
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
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
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
                params = ('0', cloudTrader_user_accounts_2, class_random_str)

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
                        expected_value=float(0.10),
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
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(totalSzie),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-云跟单-复制下单数据")
        def test_copy_verify_dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单后数据库中的订单数据正确性"""
            with allure.step("查询复制订单详情数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
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
                params = ('0', cloudTrader_user_accounts_4, class_random_str)

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
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(totalSzie),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-MT5云跟单-复制下单数据")
        def test_copy_verify_MT5dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单后数据库中的订单数据正确性"""
            with allure.step("查询复制订单详情数据"):
                addCloud_MT5Slave = var_manager.get_variable("addCloud_MT5Slave")
                account = addCloud_MT5Slave["account"]
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
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(totalSzie),
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
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")

                request_data = {
                    "isCloseAll": 1,
                    "intervalTime": 0,
                    "id": f"{cloudMaster_id}",
                    "cloudTraderId": [cloudTrader_traderList_2]
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
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
                cloudTrader_vps_ids_1 = var_manager.get_variable("cloudTrader_vps_ids_1")

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
                params = ('1', cloudTrader_user_accounts_2, cloudTrader_vps_ids_1, class_random_str)

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
                    totalSzie = trader_ordersend["totalSzie"]
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(totalSzie),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-云跟单-复制下单平仓数据")
        def test_copy_verify_close_dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单平仓后数据库中的订单数据正确性"""
            with allure.step("查询复制平仓订单数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
                cloudTrader_vps_ids_3 = var_manager.get_variable("cloudTrader_vps_ids_3")

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
                params = ('1', cloudTrader_user_accounts_4, cloudTrader_vps_ids_3, class_random_str)

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
                    totalSzie = trader_ordersend["totalSzie"]
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(totalSzie),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-MT5云跟单-复制下单平仓数据")
        def test_copy_verify_close_MT5dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单平仓后数据库中的订单数据正确性"""
            with allure.step("查询复制平仓订单数据"):
                addCloud_MT5Slave = var_manager.get_variable("addCloud_MT5Slave")
                account = addCloud_MT5Slave["account"]
                MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")

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
                params = ('1', account, MT5vps_addslave_id, class_random_str)

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
                    totalSzie = trader_ordersend["totalSzie"]
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(totalSzie),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    @allure.story("场景2：复制下单-手数0.01-0.01，总手数0.01")
    @allure.description("""
    ### 测试说明
    - 前置条件：有云策略和云跟单
      1. 进行开仓，手数范围0.01-0.01，总手数0.01
      2. 校验账号的数据是否正确
      3. 进行平仓
      4. 校验账号的数据是否正确
    - 预期结果：账号的数据正确
    """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    class TestMasOrderSend2(APITestBase):
        @allure.title("云策略-复制下单操作")
        def test_copy_place_order(self, class_random_str, logged_session, var_manager):
            """执行云策略复制下单操作并验证请求结果"""
            with allure.step("1.发送复制下单请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")

                request_data = {
                    "id": cloudMaster_id,
                    "type": 0,
                    "tradeType": 1,
                    "intervalTime": 0,
                    "cloudTraderId": [cloudTrader_traderList_2],
                    "symbol": "XAUUSD",
                    "placedType": 0,
                    "startSize": "0.01",
                    "endSize": "0.01",
                    "totalNum": "",
                    "totalSzie": "0.01",
                    "remark": class_random_str
                }

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudOrderSend',
                    json_data=request_data
                )

            with allure.step("2.验证响应结果"):
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
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
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
                params = ('0', cloudTrader_user_accounts_2, class_random_str)

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
                    logging.info(f"开始手数验证通过: {max_lot_size}")

                with allure.step("验证手数范围-结束手数"):
                    min_lot_size = db_data[0]["min_lot_size"]
                    self.verify_data(
                        actual_value=float(min_lot_size),
                        expected_value=float(0.01),
                        op=CompareOp.EQ,
                        message="结束手数应符合预期",
                        attachment_name="结束手数详情"
                    )
                    logging.info(f"结束手数验证通过: {min_lot_size}")

                with allure.step("验证指令总手数"):
                    total_lots = db_data[0]["total_lots"]
                    self.verify_data(
                        actual_value=float(total_lots),
                        expected_value=float(0.01),
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
                        expected_value=float(0.01),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-云跟单-复制下单数据")
        def test_copy_verify_dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单后数据库中的订单数据正确性"""
            with allure.step("查询复制订单详情数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
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
                params = ('0', cloudTrader_user_accounts_4, class_random_str)

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
                        expected_value=float(0.01),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-MT5云跟单-复制下单数据")
        def test_copy_verify_MT5dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单后数据库中的订单数据正确性"""
            with allure.step("查询复制订单详情数据"):
                addCloud_MT5Slave = var_manager.get_variable("addCloud_MT5Slave")
                account = addCloud_MT5Slave["account"]
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
                        expected_value=float(0.01),
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
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")

                request_data = {
                    "isCloseAll": 1,
                    "intervalTime": 0,
                    "id": f"{cloudMaster_id}",
                    "cloudTraderId": [cloudTrader_traderList_2]
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
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
                cloudTrader_vps_ids_1 = var_manager.get_variable("cloudTrader_vps_ids_1")

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
                params = ('1', cloudTrader_user_accounts_2, cloudTrader_vps_ids_1, class_random_str)

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
                        expected_value=float(0.01),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-云跟单-复制下单平仓数据")
        def test_copy_verify_close_dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单平仓后数据库中的订单数据正确性"""
            with allure.step("查询复制平仓订单数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
                cloudTrader_vps_ids_3 = var_manager.get_variable("cloudTrader_vps_ids_3")

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
                params = ('1', cloudTrader_user_accounts_4, cloudTrader_vps_ids_3, class_random_str)

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
                        expected_value=float(0.01),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-MT5云跟单-复制下单平仓数据")
        def test_copy_verify_close_MT5dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单平仓后数据库中的订单数据正确性"""
            with allure.step("查询复制平仓订单数据"):
                addCloud_MT5Slave = var_manager.get_variable("addCloud_MT5Slave")
                account = addCloud_MT5Slave["account"]
                MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")

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
                params = ('1', account, MT5vps_addslave_id, class_random_str)

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
                        expected_value=float(0.01),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    @allure.story("场景3：复制下单-手数0.01-1，总订单数10")
    @allure.description("""
    ### 测试说明
    - 前置条件：有云策略和云跟单
      1. 进行开仓，手数范围0.01-1，总订单数10
      2. 校验账号的数据是否正确
      3. 进行平仓
      4. 校验账号的数据是否正确
    - 预期结果：账号的数据正确
    """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    class TestMasOrderSend3(APITestBase):
        @allure.title("云策略-复制下单操作")
        def test_copy_place_order(self, class_random_str, logged_session, var_manager):
            """执行云策略复制下单操作并验证请求结果"""
            with allure.step("1.发送复制下单请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")

                request_data = {
                    "id": cloudMaster_id,
                    "type": 0,
                    "tradeType": 1,
                    "intervalTime": 0,
                    "cloudTraderId": [cloudTrader_traderList_2],
                    "symbol": "XAUUSD",
                    "placedType": 0,
                    "startSize": "0.01",
                    "endSize": "1.00",
                    "totalNum": "10",
                    "totalSzie": "",
                    "remark": class_random_str
                }

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudOrderSend',
                    json_data=request_data
                )

            with allure.step("2.验证响应结果"):
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
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
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
                params = ('0', cloudTrader_user_accounts_2, class_random_str)

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
                        expected_value=float(0.01),
                        op=CompareOp.EQ,
                        message="开始手数应符合预期",
                        attachment_name="开始手数详情"
                    )
                    logging.info(f"开始手数验证通过: {max_lot_size}")

                with allure.step("验证总订单数量"):
                    total_orders = db_data[0]["total_orders"]
                    self.verify_data(
                        actual_value=float(total_orders),
                        expected_value=float(10),
                        op=CompareOp.EQ,
                        message="总订单数量应符合预期",
                        attachment_name="总订单数量详情"
                    )
                    logging.info(f"总订单数量验证通过: {total_orders}")

        @allure.title("数据库校验-云跟单-复制下单数据")
        def test_copy_verify_dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单后数据库中的订单数据正确性"""
            with allure.step("查询复制订单详情数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
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
                params = ('0', cloudTrader_user_accounts_4, class_random_str)

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

                with allure.step("验证总订单数量"):
                    self.verify_data(
                        actual_value=float(len(db_data)),
                        expected_value=float(10),
                        op=CompareOp.EQ,
                        message="总订单数量应符合预期",
                        attachment_name="总订单数量详情"
                    )
                    logging.info(f"开始手数验证通过: {len(db_data)}")

        @allure.title("数据库校验-MT5云跟单-复制下单数据")
        def test_copy_verify_MT5dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单后数据库中的订单数据正确性"""
            with allure.step("查询复制订单详情数据"):
                addCloud_MT5Slave = var_manager.get_variable("addCloud_MT5Slave")
                account = addCloud_MT5Slave["account"]
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

                with allure.step("验证总订单数量"):
                    self.verify_data(
                        actual_value=float(len(db_data)),
                        expected_value=float(10),
                        op=CompareOp.EQ,
                        message="总订单数量应符合预期",
                        attachment_name="总订单数量详情"
                    )
                    logging.info(f"开始手数验证通过: {len(db_data)}")

        @allure.title("云策略-复制下单平仓操作")
        def test_copy_close_order(self, class_random_str, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("1.发送复制下单平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")

                request_data = {
                    "isCloseAll": 1,
                    "intervalTime": 0,
                    "id": f"{cloudMaster_id}",
                    "cloudTraderId": [cloudTrader_traderList_2]
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
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
                cloudTrader_vps_ids_1 = var_manager.get_variable("cloudTrader_vps_ids_1")

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
                params = ('1', cloudTrader_user_accounts_2, cloudTrader_vps_ids_1, class_random_str)

                # 轮询等待数据库记录
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )

            with allure.step("执行复制平仓数据校验"):
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

                with allure.step("验证订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=10,
                        op=CompareOp.EQ,
                        message=f"应该有10个订单",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"应该有10个订单，结果有{len(db_data)}个订单")

        @allure.title("数据库校验-云跟单-复制下单平仓数据")
        def test_copy_verify_close_dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单平仓后数据库中的订单数据正确性"""
            with allure.step("查询复制平仓订单数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
                cloudTrader_vps_ids_3 = var_manager.get_variable("cloudTrader_vps_ids_3")

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
                params = ('1', cloudTrader_user_accounts_4, cloudTrader_vps_ids_3, class_random_str)

                # 轮询等待数据库记录
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )

            with allure.step("执行复制平仓数据校验"):
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

                with allure.step("验证订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=10,
                        op=CompareOp.EQ,
                        message=f"应该有10个订单",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"应该有10个订单，结果有{len(db_data)}个订单")

        @allure.title("数据库校验-MT5云跟单-复制下单平仓数据")
        def test_copy_verify_close_MT5dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单平仓后数据库中的订单数据正确性"""
            with allure.step("查询复制平仓订单数据"):
                addCloud_MT5Slave = var_manager.get_variable("addCloud_MT5Slave")
                account = addCloud_MT5Slave["account"]
                MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")

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
                params = ('1', account, MT5vps_addslave_id, class_random_str)

                # 轮询等待数据库记录
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )

            with allure.step("执行复制平仓数据校验"):
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

                with allure.step("验证订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=10,
                        op=CompareOp.EQ,
                        message=f"应该有10个订单",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"应该有10个订单，结果有{len(db_data)}个订单")

    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    @allure.story("场景4：复制下单-手数0.01-1，总手数5")
    @allure.description("""
    ### 测试说明
    - 前置条件：有云策略和云跟单
      1. 进行开仓，手数范围0.01-1，总手数5
      2. 校验账号的数据是否正确
      3. 进行平仓
      4. 校验账号的数据是否正确
    - 预期结果：账号的数据正确
    """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    class TestMasOrderSend4(APITestBase):
        @allure.title("云策略-复制下单操作")
        def test_copy_place_order(self, class_random_str, logged_session, var_manager):
            """执行云策略复制下单操作并验证请求结果"""
            with allure.step("1.发送复制下单请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")

                request_data = {
                    "id": cloudMaster_id,
                    "type": 0,
                    "tradeType": 1,
                    "intervalTime": 0,
                    "cloudTraderId": [cloudTrader_traderList_2],
                    "symbol": "XAUUSD",
                    "placedType": 0,
                    "startSize": "0.01",
                    "endSize": "1.00",
                    "totalNum": "",
                    "totalSzie": "5",
                    "remark": class_random_str
                }

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudOrderSend',
                    json_data=request_data
                )

            with allure.step("2.验证响应结果"):
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
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
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
                params = ('0', cloudTrader_user_accounts_2, class_random_str)

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
                        expected_value=float(0.01),
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
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(5),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-云跟单-复制下单数据")
        def test_copy_verify_dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单后数据库中的订单数据正确性"""
            with allure.step("查询复制订单详情数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
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
                params = ('0', cloudTrader_user_accounts_4, class_random_str)

                # 轮询等待数据库记录
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )

            with allure.step("执行复制下单数据校验"):
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
                        expected_value=float(5),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-MT5云跟单-复制下单数据")
        def test_copy_verify_MT5dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单后数据库中的订单数据正确性"""
            with allure.step("查询复制订单详情数据"):
                addCloud_MT5Slave = var_manager.get_variable("addCloud_MT5Slave")
                account = addCloud_MT5Slave["account"]
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
                        expected_value=float(5),
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
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")

                request_data = {
                    "isCloseAll": 1,
                    "intervalTime": 0,
                    "id": f"{cloudMaster_id}",
                    "cloudTraderId": [cloudTrader_traderList_2]
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
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
                cloudTrader_vps_ids_1 = var_manager.get_variable("cloudTrader_vps_ids_1")

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
                params = ('1', cloudTrader_user_accounts_2, cloudTrader_vps_ids_1, class_random_str)

                # 轮询等待数据库记录
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )

            with allure.step("执行复制平仓数据校验"):
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
                        expected_value=float(5),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-云跟单-复制下单平仓数据")
        def test_copy_verify_close_dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单平仓后数据库中的订单数据正确性"""
            with allure.step("查询复制平仓订单数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
                cloudTrader_vps_ids_3 = var_manager.get_variable("cloudTrader_vps_ids_3")

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
                params = ('1', cloudTrader_user_accounts_4, cloudTrader_vps_ids_3, class_random_str)

                # 轮询等待数据库记录
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )

            with allure.step("执行复制平仓数据校验"):
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
                        expected_value=float(5),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-MT5云跟单-复制下单平仓数据")
        def test_copy_verify_close_MT5dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单平仓后数据库中的订单数据正确性"""
            with allure.step("查询复制平仓订单数据"):
                addCloud_MT5Slave = var_manager.get_variable("addCloud_MT5Slave")
                account = addCloud_MT5Slave["account"]
                MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")

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
                params = ('1', account, MT5vps_addslave_id, class_random_str)

                # 轮询等待数据库记录
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )

            with allure.step("执行复制平仓数据校验"):
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
                        expected_value=float(5),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    @allure.story("场景5：复制下单-手数0.1-1，总订单5-停止功能")
    @allure.description("""
    ### 测试说明
    - 前置条件：有云策略和云跟单
     1. 进行开仓，手数范围0.1-1，总订单5-停止功能
     2. 点击停止
     3. 校验账号的下单总手数和数据库的手数，应该不相等
     4. 进行平仓
     5. 校验账号的数据是否正确
    - 预期结果：云策略下单的停止功能正确
    """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    class TestMasOrderSend5(APITestBase):
        @allure.title("云策略-复制下单操作")
        def test_copy_place_order(self, class_random_str, logged_session, var_manager):
            """执行云策略复制下单操作并验证请求结果"""
            with allure.step("1.发送复制下单请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")

                request_data = {
                    "id": cloudMaster_id,
                    "type": 0,
                    "tradeType": 1,
                    "intervalTime": 10000,
                    "cloudTraderId": [cloudTrader_traderList_2],
                    "symbol": "XAUUSD",
                    "placedType": 0,
                    "startSize": "0.1",
                    "endSize": "1.00",
                    "totalNum": "5",
                    "totalSzie": "",
                    "remark": class_random_str
                }

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudOrderSend',
                    json_data=request_data
                )

            with allure.step("2.验证响应结果"):
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
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                sql = """
                       SELECT 
                           order_no
                       FROM 
                           follow_order_instruct
                       WHERE instruction_type = %s
                           AND cloud_type = %s
                           AND cloud_id = %s
                           AND cloud_name = %s
                           AND min_lot_size = %s
                           AND max_lot_size = %s
                   """
                params = ("1", "0", cloudMaster_id, "自动化测试", "1.00", "0.10")

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

        @allure.title("云策略-停止操作")
        def test_cloudTrader_cloudStopOrder(self, class_random_str, logged_session, var_manager):
            """执行云策略复制下单操作并验证请求结果"""
            with allure.step("发送停止操作请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")

                params = {
                    "id": cloudMaster_id,
                    "type": "0",
                    "orderNo": order_no
                }

                response = self.send_get_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudStopOrder',
                    params=params
                )

            with allure.step("验证停止操作响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

        @allure.title("数据库校验-云跟单-复制下单数据")
        def test_copy_verify_db2(self, class_random_str, var_manager, db_transaction):
            """验证复制下单后数据库中的订单数据正确性"""
            with allure.step("查询复制订单详情数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
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
                params = ('0', cloudTrader_user_accounts_4, class_random_str)

                # 轮询等待数据库记录
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )

            with allure.step("执行复制下单数据校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行复制下单校验")

                # 校验订单数和下单总订单数
                with allure.step("验证开仓的订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=5,
                        op=CompareOp.NE,
                        message=f"开仓的订单数量应该不是5",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"开仓的订单数量应该不是5，结果有{len(db_data)}个订单")

        @allure.title("数据库校验-MT5云跟单-复制下单数据")
        def test_copy_verify_MT5dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单后数据库中的订单数据正确性"""
            with allure.step("查询复制订单详情数据"):
                addCloud_MT5Slave = var_manager.get_variable("addCloud_MT5Slave")
                account = addCloud_MT5Slave["account"]
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

                # 校验订单数和下单总订单数
                with allure.step("验证开仓的订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=5,
                        op=CompareOp.NE,
                        message=f"开仓的订单数量应该不是5",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"开仓的订单数量应该不是5，结果有{len(db_data)}个订单")

        # @pytest.mark.skipif(True, reason=SKIP_REASON)
        @allure.title("云策略-复制下单平仓操作")
        def test_copy_close_order(self, class_random_str, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("1.发送复制下单平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")

                request_data = {
                    "isCloseAll": 1,
                    "intervalTime": 0,
                    "id": f"{cloudMaster_id}",
                    "cloudTraderId": [cloudTrader_traderList_2]
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

        time.sleep(30)

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
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    class TestMasOrderSend6(APITestBase):
        @allure.title("云策略-分配下单操作")
        def test_copy_place_order(self, class_random_str, logged_session, var_manager):
            """执行云策略复制下单操作并验证请求结果"""
            with allure.step("1.发送复制下单请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")

                request_data = {
                    "id": cloudMaster_id,
                    "type": 0,
                    "tradeType": 0,
                    "cloudTraderId": [cloudTrader_traderList_2],
                    "symbol": "XAUUSD",
                    "startSize": "0.10",
                    "endSize": "1.00",
                    "totalSzie": "1.00",
                    "remark": class_random_str,
                    "totalNum": 0
                }

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudOrderSend',
                    json_data=request_data
                )

            with allure.step("2.验证响应结果"):
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
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
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
                params = ('0', cloudTrader_user_accounts_2, class_random_str)

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
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(totalSzie),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-云跟单-复制下单数据")
        def test_copy_verify_dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单后数据库中的订单数据正确性"""
            with allure.step("查询复制订单详情数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
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
                params = ('0', cloudTrader_user_accounts_4, class_random_str)

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
                    totalSzie = trader_ordersend["totalSzie"]
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(totalSzie),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-MT5云跟单-复制下单数据")
        def test_copy_verify_MT5dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单后数据库中的订单数据正确性"""
            with allure.step("查询复制订单详情数据"):
                addCloud_MT5Slave = var_manager.get_variable("addCloud_MT5Slave")
                account = addCloud_MT5Slave["account"]
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
                    totalSzie = trader_ordersend["totalSzie"]
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(totalSzie),
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
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")

                request_data = {
                    "isCloseAll": 1,
                    "intervalTime": 0,
                    "id": f"{cloudMaster_id}",
                    "cloudTraderId": [cloudTrader_traderList_2]
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
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
                cloudTrader_vps_ids_1 = var_manager.get_variable("cloudTrader_vps_ids_1")

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
                params = ('1', cloudTrader_user_accounts_2, cloudTrader_vps_ids_1, class_random_str)

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
                    totalSzie = trader_ordersend["totalSzie"]
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(totalSzie),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-云跟单-复制下单平仓数据")
        def test_copy_verify_close_dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单平仓后数据库中的订单数据正确性"""
            with allure.step("查询复制平仓订单数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
                cloudTrader_vps_ids_3 = var_manager.get_variable("cloudTrader_vps_ids_3")

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
                params = ('1', cloudTrader_user_accounts_4, cloudTrader_vps_ids_3, class_random_str)

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
                    totalSzie = trader_ordersend["totalSzie"]
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(totalSzie),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-MT5云跟单-复制下单平仓数据")
        def test_copy_verify_close_MT5dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单平仓后数据库中的订单数据正确性"""
            with allure.step("查询复制平仓订单数据"):
                addCloud_MT5Slave = var_manager.get_variable("addCloud_MT5Slave")
                account = addCloud_MT5Slave["account"]
                MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")

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
                params = ('1', account, MT5vps_addslave_id, class_random_str)

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
                    totalSzie = trader_ordersend["totalSzie"]
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(totalSzie),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    @allure.story("场景7：复制下单-手数范围0.6-1，总手数1")
    @allure.description("""
    ### 测试说明
    - 前置条件：有云策略和云跟单
      1. 进行开仓，手数范围0.6-1，总手数1
      2. 校验账号的数据是否正确
      3. 进行平仓
      4. 校验账号的数据是否正确
    - 预期结果：账号的数据正确
    """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    class TestMasOrderSend7(APITestBase):
        @allure.title("云策略-复制下单操作")
        def test_copy_place_order(self, class_random_str, logged_session, var_manager):
            """执行云策略复制下单操作并验证请求结果"""
            with allure.step("1.发送复制下单请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")

                request_data = {
                    "id": cloudMaster_id,
                    "type": 0,
                    "tradeType": 1,
                    "intervalTime": 0,
                    "cloudTraderId": [cloudTrader_traderList_2],
                    "symbol": "XAUUSD",
                    "placedType": 0,
                    "startSize": "0.60",
                    "endSize": "1.00",
                    "totalNum": "",
                    "totalSzie": "1.00",
                    "remark": class_random_str
                }

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudOrderSend',
                    json_data=request_data
                )

            with allure.step("2.验证响应结果"):
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
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
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
                params = ('0', cloudTrader_user_accounts_2, class_random_str)

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
                        expected_value=float(0.6),
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

                with allure.step("验证订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=1,
                        op=CompareOp.EQ,
                        message="订单数量应符合预期",
                        attachment_name="订单数量"
                    )
                    logging.info(f"实际订单数量: {len(db_data)}")

                with allure.step("验证详情手数"):
                    size = db_data[0]["size"]
                    self.verify_data(
                        actual_value=float(size),
                        expected_value=0.6,
                        op=CompareOp.GE,
                        message="实际手数应符合预期",
                        attachment_name="实际手数"
                    )
                    logging.info(f"实际手数: {size}")

                with allure.step("验证详情手数和指令手数一致"):
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

        @allure.title("数据库校验-云跟单-复制下单数据")
        def test_copy_verify_dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单后数据库中的订单数据正确性"""
            with allure.step("查询复制订单详情数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
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
                params = ('0', cloudTrader_user_accounts_4, class_random_str)

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

                with allure.step("验证订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=1,
                        op=CompareOp.EQ,
                        message="订单数量应符合预期",
                        attachment_name="订单数量"
                    )
                    logging.info(f"实际订单数量: {len(db_data)}")

                with allure.step("验证详情手数"):
                    size = db_data[0]["size"]
                    self.verify_data(
                        actual_value=float(size),
                        expected_value=0.6,
                        op=CompareOp.GE,
                        message="实际手数应符合预期",
                        attachment_name="实际手数"
                    )
                    logging.info(f"实际手数: {size}")

                with allure.step("验证详情手数和指令手数一致"):
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

        @allure.title("数据库校验-MT5云跟单-复制下单数据")
        def test_copy_verify_MT5dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单后数据库中的订单数据正确性"""
            with allure.step("查询复制订单详情数据"):
                addCloud_MT5Slave = var_manager.get_variable("addCloud_MT5Slave")
                account = addCloud_MT5Slave["account"]
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

                with allure.step("验证订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=1,
                        op=CompareOp.EQ,
                        message="订单数量应符合预期",
                        attachment_name="订单数量"
                    )
                    logging.info(f"实际订单数量: {len(db_data)}")

                with allure.step("验证详情手数"):
                    size = db_data[0]["size"]
                    self.verify_data(
                        actual_value=float(size),
                        expected_value=0.6,
                        op=CompareOp.GE,
                        message="实际手数应符合预期",
                        attachment_name="实际手数"
                    )
                    logging.info(f"实际手数: {size}")

                with allure.step("验证详情手数和指令手数一致"):
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

        @allure.title("云策略-复制下单平仓操作")
        def test_copy_close_order(self, class_random_str, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("1.发送复制下单平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")

                request_data = {
                    "isCloseAll": 1,
                    "intervalTime": 0,
                    "id": f"{cloudMaster_id}",
                    "cloudTraderId": [cloudTrader_traderList_2]
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
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
                cloudTrader_vps_ids_1 = var_manager.get_variable("cloudTrader_vps_ids_1")

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
                params = ('1', cloudTrader_user_accounts_2, cloudTrader_vps_ids_1, class_random_str)

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

                with allure.step("验证详情手数"):
                    size = db_data[0]["size"]
                    self.verify_data(
                        actual_value=float(size),
                        expected_value=0.6,
                        op=CompareOp.GE,
                        message="实际手数应符合预期",
                        attachment_name="实际手数"
                    )
                    logging.info(f"实际手数: {size}")

        @allure.title("数据库校验-云跟单-复制下单平仓数据")
        def test_copy_verify_close_dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单平仓后数据库中的订单数据正确性"""
            with allure.step("查询复制平仓订单数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
                cloudTrader_vps_ids_3 = var_manager.get_variable("cloudTrader_vps_ids_3")

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
                params = ('1', cloudTrader_user_accounts_4, cloudTrader_vps_ids_3, class_random_str)

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

                with allure.step("验证详情手数"):
                    size = db_data[0]["size"]
                    self.verify_data(
                        actual_value=float(size),
                        expected_value=0.6,
                        op=CompareOp.GE,
                        message="实际手数应符合预期",
                        attachment_name="实际手数"
                    )
                    logging.info(f"实际手数: {size}")

        @allure.title("数据库校验-MT5云跟单-复制下单平仓数据")
        def test_copy_verify_close_MT5dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单平仓后数据库中的订单数据正确性"""
            with allure.step("查询复制平仓订单数据"):
                addCloud_MT5Slave = var_manager.get_variable("addCloud_MT5Slave")
                account = addCloud_MT5Slave["account"]
                MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")

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
                params = ('1', account, MT5vps_addslave_id, class_random_str)

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

                with allure.step("验证详情手数"):
                    size = db_data[0]["size"]
                    self.verify_data(
                        actual_value=float(size),
                        expected_value=0.6,
                        op=CompareOp.GE,
                        message="实际手数应符合预期",
                        attachment_name="实际手数"
                    )
                    logging.info(f"实际手数: {size}")

    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    @allure.story("场景8：复制下单-手数范围0.3-1，总订单数量1，总手数5")
    @allure.description("""
    ### 测试说明
    - 前置条件：有云策略和云跟单
      1. 进行开仓，手数范围0.3-1，总订单数量1，总手数5
      2. 校验权重，优先满足手数范围，然后是总手数
      3. 进行平仓
      4. 校验账号的数据是否正确
    - 预期结果：权重正确，优先满足手数范围，然后是总手数
    """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    class TestMasOrderSend8(APITestBase):
        @allure.title("云策略-复制下单操作")
        def test_copy_place_order(self, class_random_str, logged_session, var_manager):
            """执行云策略复制下单操作并验证请求结果"""
            with allure.step("1.发送复制下单请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")

                request_data = {
                    "id": cloudMaster_id,
                    "type": 0,
                    "tradeType": 1,
                    "intervalTime": 0,
                    "cloudTraderId": [cloudTrader_traderList_2],
                    "symbol": "XAUUSD",
                    "placedType": 0,
                    "startSize": "0.30",
                    "endSize": "1.00",
                    "totalNum": "1",
                    "totalSzie": "5.00",
                    "remark": class_random_str
                }

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudOrderSend',
                    json_data=request_data
                )

            with allure.step("2.验证响应结果"):
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
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
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
                params = ('0', cloudTrader_user_accounts_2, class_random_str)

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

                with allure.step("验证详情手数"):
                    size = [record["size"] for record in db_data]
                    for i in size:
                        self.verify_data(
                            actual_value=float(i),
                            expected_value=0.3,
                            op=CompareOp.GE,
                            message="实际手数应符合预期",
                            attachment_name="实际手数"
                        )
                    logging.info(f"实际手数: {size}")

                with allure.step("验证订单数量"):
                    total_orders = db_data[0]["total_orders"]
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=total_orders,
                        op=CompareOp.NE,
                        message="订单数量应符合预期",
                        attachment_name="订单数量"
                    )
                    logging.info(f"实际订单数量: {len(db_data)}")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=5,
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f'订单详情总手数是：{total}')

        @allure.title("数据库校验-云跟单-复制下单数据")
        def test_copy_verify_dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单后数据库中的订单数据正确性"""
            with allure.step("查询复制订单详情数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
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
                params = ('0', cloudTrader_user_accounts_4, class_random_str)

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

                with allure.step("验证详情手数"):
                    size = [record["size"] for record in db_data]
                    for i in size:
                        self.verify_data(
                            actual_value=float(i),
                            expected_value=0.3,
                            op=CompareOp.GE,
                            message="实际手数应符合预期",
                            attachment_name="实际手数"
                        )
                    logging.info(f"实际手数: {size}")

                with allure.step("验证订单数量"):
                    total_orders = db_data[0]["total_orders"]
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=total_orders,
                        op=CompareOp.NE,
                        message="订单数量应符合预期",
                        attachment_name="订单数量"
                    )
                    logging.info(f"实际订单数量: {len(db_data)}")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=5,
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f'订单详情总手数是：{total}')

        @allure.title("数据库校验-MT5云跟单-复制下单数据")
        def test_copy_verify_MT5dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单后数据库中的订单数据正确性"""
            with allure.step("查询复制订单详情数据"):
                addCloud_MT5Slave = var_manager.get_variable("addCloud_MT5Slave")
                account = addCloud_MT5Slave["account"]
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

                with allure.step("验证详情手数"):
                    size = [record["size"] for record in db_data]
                    for i in size:
                        self.verify_data(
                            actual_value=float(i),
                            expected_value=0.3,
                            op=CompareOp.GE,
                            message="实际手数应符合预期",
                            attachment_name="实际手数"
                        )
                    logging.info(f"实际手数: {size}")

                with allure.step("验证订单数量"):
                    total_orders = db_data[0]["total_orders"]
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=total_orders,
                        op=CompareOp.NE,
                        message="订单数量应符合预期",
                        attachment_name="订单数量"
                    )
                    logging.info(f"实际订单数量: {len(db_data)}")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=5,
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f'订单详情总手数是：{total}')

        @allure.title("云策略-复制下单平仓操作")
        def test_copy_close_order(self, class_random_str, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("1.发送复制下单平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")

                request_data = {
                    "isCloseAll": 1,
                    "intervalTime": 0,
                    "id": f"{cloudMaster_id}",
                    "cloudTraderId": [cloudTrader_traderList_2]
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
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
                cloudTrader_vps_ids_1 = var_manager.get_variable("cloudTrader_vps_ids_1")

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
                params = ('1', cloudTrader_user_accounts_2, cloudTrader_vps_ids_1, class_random_str)

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

                with allure.step("验证详情手数"):
                    size = [record["size"] for record in db_data]
                    for i in size:
                        self.verify_data(
                            actual_value=float(i),
                            expected_value=0.3,
                            op=CompareOp.GE,
                            message="实际手数应符合预期",
                            attachment_name="实际手数"
                        )
                    logging.info(f"实际手数: {size}")

                with allure.step("验证订单数量"):
                    total_orders = db_data[0]["total_orders"]
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=total_orders,
                        op=CompareOp.NE,
                        message="订单数量应符合预期",
                        attachment_name="订单数量"
                    )
                    logging.info(f"实际订单数量: {len(db_data)}")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=5,
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f'订单详情总手数是：{total}')

        @allure.title("数据库校验-云跟单-复制下单平仓数据")
        def test_copy_verify_close_dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单平仓后数据库中的订单数据正确性"""
            with allure.step("查询复制平仓订单数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
                cloudTrader_vps_ids_3 = var_manager.get_variable("cloudTrader_vps_ids_3")

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
                params = ('1', cloudTrader_user_accounts_4, cloudTrader_vps_ids_3, class_random_str)

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

                with allure.step("验证订单数量"):
                    total_orders = db_data[0]["total_orders"]
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=total_orders,
                        op=CompareOp.NE,
                        message="订单数量应符合预期",
                        attachment_name="订单数量"
                    )
                    logging.info(f"实际订单数量: {len(db_data)}")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=5,
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f'订单详情总手数是：{total}')

        @allure.title("数据库校验-MT5云跟单-复制下单平仓数据")
        def test_copy_verify_close_MT5dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单平仓后数据库中的订单数据正确性"""
            with allure.step("查询复制平仓订单数据"):
                addCloud_MT5Slave = var_manager.get_variable("addCloud_MT5Slave")
                account = addCloud_MT5Slave["account"]
                MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")

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
                params = ('1', account, MT5vps_addslave_id, class_random_str)

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

                with allure.step("验证订单数量"):
                    total_orders = db_data[0]["total_orders"]
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=total_orders,
                        op=CompareOp.NE,
                        message="订单数量应符合预期",
                        attachment_name="订单数量"
                    )
                    logging.info(f"实际订单数量: {len(db_data)}")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=5,
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f'订单详情总手数是：{total}')

    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    @allure.story("场景9：复制下单-手数范围0.01-1，总手数0.3")
    @allure.description("""
    ### 测试说明
    - 前置条件：有云策略和云跟单
      1. 修改跟单账号下单比例0.25，手数取余-取小数，合约比例0.5
      2. 进行开仓，手数范围0.01-1，总手数0.3
      3. 校验账号的数据是否正确-下单手数是0.3*0.25*0.5=0.0375，取小数是0.03
      4. 进行平仓
      5. 校验账号的数据是否正确
    - 预期结果：账号的数据正确
    """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    class TestMasOrderSend9(APITestBase):
        @allure.title("云策略列表-修改云跟单")
        def test_update_cloudtrader(self, class_random_str, logged_session, var_manager):
            """执行云策略复制下单操作并验证请求结果"""
            with allure.step("1.发送修改MT4账号云跟单请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
                cloudTrader_template_id2 = var_manager.get_variable("cloudTrader_template_id2")

                request_data = [
                    {
                        "traderList": [
                            cloudTrader_traderList_4
                        ],
                        "cloudId": cloudMaster_id,
                        "masterId": cloudTrader_traderList_2,
                        "masterAccount": cloudTrader_user_accounts_2,
                        "followDirection": 0,
                        "followMode": 1,
                        "followParam": "0.25",
                        "remainder": 1,
                        "placedType": 0,
                        "templateId": cloudTrader_template_id2,
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
                        "forex": None
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

            with allure.step("3.发送修改MT5账号云跟单请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")
                cloudTrader_MT5traderID = var_manager.get_variable("cloudTrader_MT5traderID")
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")

                request_data = [
                    {
                        "traderList": [
                            cloudTrader_MT5traderID
                        ],
                        "cloudId": cloudMaster_id,
                        "masterId": cloudTrader_traderList_2,
                        "masterAccount": cloudTrader_user_accounts_2,
                        "followDirection": 0,
                        "followMode": 1,
                        "followParam": "0.25",
                        "remainder": 1,
                        "placedType": 0,
                        "templateId": cloudTrader_template_id2,
                        "followStatus": 1,
                        "followOpen": 1,
                        "followClose": 1,
                        "fixedComment": None,
                        "commentType": None,
                        "digits": 0,
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
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")

                request_data = {
                    "id": cloudMaster_id,
                    "type": 0,
                    "tradeType": 1,
                    "intervalTime": 0,
                    "cloudTraderId": [cloudTrader_traderList_2],
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

            with allure.step("2.验证响应结果"):
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
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
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
                params = ('0', cloudTrader_user_accounts_2, class_random_str)

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
                        abs_tol=0.001,
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
                        abs_tol=0.001,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-云跟单-复制下单数据")
        def test_copy_verify_dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单后数据库中的订单数据正确性"""
            with allure.step("查询复制订单详情数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
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
                params = ('0', cloudTrader_user_accounts_4, class_random_str)

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
                        expected_value=float(0.03),
                        abs_tol=0.001,
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-MT5云跟单-复制下单数据")
        def test_copy_verify_MT5dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单后数据库中的订单数据正确性"""
            with allure.step("查询复制订单详情数据"):
                addCloud_MT5Slave = var_manager.get_variable("addCloud_MT5Slave")
                account = addCloud_MT5Slave["account"]
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
                        expected_value=float(0.03),
                        abs_tol=0.001,
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
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")

                request_data = {
                    "isCloseAll": 1,
                    "intervalTime": 0,
                    "id": f"{cloudMaster_id}",
                    "cloudTraderId": [cloudTrader_traderList_2]
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
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
                cloudTrader_vps_ids_1 = var_manager.get_variable("cloudTrader_vps_ids_1")

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
                params = ('1', cloudTrader_user_accounts_2, cloudTrader_vps_ids_1, class_random_str)

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
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
                cloudTrader_vps_ids_3 = var_manager.get_variable("cloudTrader_vps_ids_3")

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
                params = ('1', cloudTrader_user_accounts_4, cloudTrader_vps_ids_3, class_random_str)

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
                        expected_value=float(0.03),
                        abs_tol=0.001,
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-MT5云跟单-复制下单平仓数据")
        def test_copy_verify_close_MT5dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单平仓后数据库中的订单数据正确性"""
            with allure.step("查询复制平仓订单数据"):
                addCloud_MT5Slave = var_manager.get_variable("addCloud_MT5Slave")
                account = addCloud_MT5Slave["account"]
                MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")

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
                params = ('1', account, MT5vps_addslave_id, class_random_str)

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
                        expected_value=float(0.03),
                        abs_tol=0.001,
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

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
        @allure.title("云策略列表-修改云跟单")
        def test_update_cloudtrader(self, class_random_str, logged_session, var_manager):
            """执行云策略复制下单操作并验证请求结果"""
            with allure.step("1.发送修改MT4账号云跟单请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
                cloudTrader_template_id2 = var_manager.get_variable("cloudTrader_template_id2")

                request_data = [
                    {
                        "traderList": [
                            cloudTrader_traderList_4
                        ],
                        "cloudId": cloudMaster_id,
                        "masterId": cloudTrader_traderList_2,
                        "masterAccount": cloudTrader_user_accounts_2,
                        "followDirection": 0,
                        "followMode": 1,
                        "followParam": "0.25",
                        "remainder": 0,
                        "placedType": 0,
                        "templateId": cloudTrader_template_id2,
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
                        "forex": None
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

            with allure.step("3.发送修改MT5账号云跟单请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")
                cloudTrader_MT5traderID = var_manager.get_variable("cloudTrader_MT5traderID")
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")

                request_data = [
                    {
                        "traderList": [
                            cloudTrader_MT5traderID
                        ],
                        "cloudId": cloudMaster_id,
                        "masterId": cloudTrader_traderList_2,
                        "masterAccount": cloudTrader_user_accounts_2,
                        "followDirection": 0,
                        "followMode": 1,
                        "followParam": "0.25",
                        "remainder": 0,
                        "placedType": 0,
                        "templateId": cloudTrader_template_id2,
                        "followStatus": 1,
                        "followOpen": 1,
                        "followClose": 1,
                        "fixedComment": None,
                        "commentType": None,
                        "digits": 0,
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
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")

                request_data = {
                    "id": cloudMaster_id,
                    "type": 0,
                    "tradeType": 1,
                    "intervalTime": 0,
                    "cloudTraderId": [cloudTrader_traderList_2],
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

            with allure.step("2.验证响应结果"):
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
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
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
                params = ('0', cloudTrader_user_accounts_2, class_random_str)

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
                        abs_tol=0.001,
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
                        abs_tol=0.001,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-云跟单-复制下单数据")
        def test_copy_verify_dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单后数据库中的订单数据正确性"""
            with allure.step("查询复制订单详情数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
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
                params = ('0', cloudTrader_user_accounts_4, class_random_str)

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
                        abs_tol=0.001,
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-MT5云跟单-复制下单数据")
        def test_copy_verify_MT5dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单后数据库中的订单数据正确性"""
            with allure.step("查询复制订单详情数据"):
                addCloud_MT5Slave = var_manager.get_variable("addCloud_MT5Slave")
                account = addCloud_MT5Slave["account"]
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
                        abs_tol=0.001,
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
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")

                request_data = {
                    "isCloseAll": 1,
                    "intervalTime": 0,
                    "id": f"{cloudMaster_id}",
                    "cloudTraderId": [cloudTrader_traderList_2]
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
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
                cloudTrader_vps_ids_1 = var_manager.get_variable("cloudTrader_vps_ids_1")

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
                params = ('1', cloudTrader_user_accounts_2, cloudTrader_vps_ids_1, class_random_str)

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
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
                cloudTrader_vps_ids_3 = var_manager.get_variable("cloudTrader_vps_ids_3")

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
                params = ('1', cloudTrader_user_accounts_4, cloudTrader_vps_ids_3, class_random_str)

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
                        abs_tol=0.001,
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-MT5云跟单-复制下单平仓数据")
        def test_copy_verify_close_MT5dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单平仓后数据库中的订单数据正确性"""
            with allure.step("查询复制平仓订单数据"):
                addCloud_MT5Slave = var_manager.get_variable("addCloud_MT5Slave")
                account = addCloud_MT5Slave["account"]
                MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")

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
                params = ('1', account, MT5vps_addslave_id, class_random_str)

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
                        abs_tol=0.001,
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    @allure.story("场景11：复制下单-手数范围0.01-1，总手数0.01")
    @allure.description("""
    ### 测试说明
    - 前置条件：有云策略和云跟单
      1. 修改跟单账号下单比例0.25，手数取余-四舍五入，合约比例0.5
      2. 进行开仓，手数范围0.01-1，总手数0.01
      3. 校验账号的数据是否正确-下单手数是0.01*0.25*0.5=0.00125，最低下单手数是0.01
      4. 进行平仓
      5. 校验账号的数据是否正确
    - 预期结果：账号的数据正确
    """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    class TestMasOrderSend11(APITestBase):
        @allure.title("云策略列表-修改云跟单")
        def test_update_cloudtrader(self, class_random_str, logged_session, var_manager):
            """执行云策略复制下单操作并验证请求结果"""
            with allure.step("1.发送修改MT4账号云跟单请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
                cloudTrader_template_id2 = var_manager.get_variable("cloudTrader_template_id2")

                request_data = [
                    {
                        "traderList": [
                            cloudTrader_traderList_4
                        ],
                        "cloudId": cloudMaster_id,
                        "masterId": cloudTrader_traderList_2,
                        "masterAccount": cloudTrader_user_accounts_2,
                        "followDirection": 0,
                        "followMode": 1,
                        "followParam": "0.25",
                        "remainder": 0,
                        "placedType": 0,
                        "templateId": cloudTrader_template_id2,
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
                        "forex": None
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

            with allure.step("3.发送修改MT5账号云跟单请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")
                cloudTrader_MT5traderID = var_manager.get_variable("cloudTrader_MT5traderID")
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")

                request_data = [
                    {
                        "traderList": [
                            cloudTrader_MT5traderID
                        ],
                        "cloudId": cloudMaster_id,
                        "masterId": cloudTrader_traderList_2,
                        "masterAccount": cloudTrader_user_accounts_2,
                        "followDirection": 0,
                        "followMode": 1,
                        "followParam": "0.25",
                        "remainder": 0,
                        "placedType": 0,
                        "templateId": cloudTrader_template_id2,
                        "followStatus": 1,
                        "followOpen": 1,
                        "followClose": 1,
                        "fixedComment": None,
                        "commentType": None,
                        "digits": 0,
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
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")

                request_data = {
                    "id": cloudMaster_id,
                    "type": 0,
                    "tradeType": 1,
                    "intervalTime": 0,
                    "cloudTraderId": [cloudTrader_traderList_2],
                    "symbol": "XAUUSD",
                    "placedType": 0,
                    "startSize": "0.01",
                    "endSize": "1.00",
                    "totalNum": "",
                    "totalSzie": "0.01",
                    "remark": class_random_str
                }

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudOrderSend',
                    json_data=request_data
                )

            with allure.step("2.验证响应结果"):
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
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
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
                params = ('0', cloudTrader_user_accounts_2, class_random_str)

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
                        expected_value=float(0.01),
                        op=CompareOp.EQ,
                        abs_tol=0.001,
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
                        expected_value=float(0.01),
                        op=CompareOp.EQ,
                        abs_tol=0.001,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-云跟单-复制下单数据")
        def test_copy_verify_dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单后数据库中的订单数据正确性"""
            with allure.step("查询复制订单详情数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
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
                params = ('0', cloudTrader_user_accounts_4, class_random_str)

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
                        expected_value=float(0.01),
                        abs_tol=0.001,
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-MT5云跟单-复制下单数据")
        def test_copy_verify_MT5dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单后数据库中的订单数据正确性"""
            with allure.step("查询复制订单详情数据"):
                addCloud_MT5Slave = var_manager.get_variable("addCloud_MT5Slave")
                account = addCloud_MT5Slave["account"]
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
                        expected_value=float(0.01),
                        abs_tol=0.001,
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
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")

                request_data = {
                    "isCloseAll": 1,
                    "intervalTime": 0,
                    "id": f"{cloudMaster_id}",
                    "cloudTraderId": [cloudTrader_traderList_2]
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
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
                cloudTrader_vps_ids_1 = var_manager.get_variable("cloudTrader_vps_ids_1")

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
                params = ('1', cloudTrader_user_accounts_2, cloudTrader_vps_ids_1, class_random_str)

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
                        expected_value=float(0.01),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-云跟单-复制下单平仓数据")
        def test_copy_verify_close_dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单平仓后数据库中的订单数据正确性"""
            with allure.step("查询复制平仓订单数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
                cloudTrader_vps_ids_3 = var_manager.get_variable("cloudTrader_vps_ids_3")

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
                params = ('1', cloudTrader_user_accounts_4, cloudTrader_vps_ids_3, class_random_str)

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
                        expected_value=float(0.01),
                        abs_tol=0.001,
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-MT5云跟单-复制下单平仓数据")
        def test_copy_verify_close_MT5dbadd(self, class_random_str, var_manager, db_transaction):
            """验证复制下单平仓后数据库中的订单数据正确性"""
            with allure.step("查询复制平仓订单数据"):
                addCloud_MT5Slave = var_manager.get_variable("addCloud_MT5Slave")
                account = addCloud_MT5Slave["account"]
                MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")

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
                params = ('1', account, MT5vps_addslave_id, class_random_str)

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
                        expected_value=float(0.01),
                        abs_tol=0.001,
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")
