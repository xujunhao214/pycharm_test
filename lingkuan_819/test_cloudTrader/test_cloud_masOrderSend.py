import allure
import logging
import pytest
import time
import math
from lingkuan_819.VAR.VAR import *
from lingkuan_819.conftest import var_manager
from lingkuan_819.commons.api_base import APITestBase

logger = logging.getLogger(__name__)
SKIP_REASON = "该用例暂时跳过"


@allure.feature("云策略-策略账号交易下单-开仓的场景校验")
class TestCloudMasOrdersend:
    @allure.story("场景1：分配下单-手数0.1-1，总手数1")
    @allure.description("""
    ### 测试说明
    - 前置条件：有云策略和云跟单
      1. 进行开仓，手数范围0.1-1，总手数1
      2. 校验账号的数据是否正确
      3. 进行平仓
      4. 校验账号的数据是否正确
    - 预期结果：账号的数据正确
    """)
    class TestCloudtradingOrders1(APITestBase):
        @allure.title("云策略交易下单-分配下单请求")
        def test_copy_order_send(self, logged_session, var_manager):
            # 发送云策略交易下单-复制下单请求
            masOrderSend = var_manager.get_variable("masOrderSend")
            cloudTrader_user_ids_2 = var_manager.get_variable("cloudTrader_user_ids_2")
            data = {
                "traderList": [cloudTrader_user_ids_2],
                "type": 0,
                "tradeType": 0,
                "symbol": masOrderSend["symbol"],
                "startSize": "0.10",
                "endSize": "1.00",
                "totalSzie": "1.00",
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
                db_data = self.wait_for_database_record_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )
            with allure.step("2. 数据校验"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

                status = db_data[0]["status"]
                assert status in (0, 1), f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}"
                logging.info(f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}")

                min_lot_size = db_data[0]["min_lot_size"]
                endsize = trader_ordersend["endSize"]
                assert math.isclose(float(endsize), float(min_lot_size), rel_tol=1e-9), \
                    f'手数范围：结束手数是：{endsize}，实际是：{min_lot_size}'
                logging.info(f'手数范围：结束手数是：{endsize}，实际是：{min_lot_size}')

                max_lot_size = db_data[0]["max_lot_size"]
                startSize = trader_ordersend["startSize"]
                assert math.isclose(float(startSize), float(max_lot_size), rel_tol=1e-9), \
                    f'手数范围：开始手数是：{startSize}，实际是：{max_lot_size}'
                logging.info(f'手数范围：开始手数是：{startSize}，实际是：{max_lot_size}')

                total_lots = db_data[0]["total_lots"]
                totalSzie = trader_ordersend["totalSzie"]
                assert math.isclose(float(totalSzie), float(total_lots), rel_tol=1e-9), \
                    f'下单总手数是：{totalSzie}，实际是：{total_lots}'
                logging.info(f'下单总手数是：{totalSzie}，实际是：{total_lots}')

                totalSzie = trader_ordersend["totalSzie"]
                size = [record["size"] for record in db_data]
                total = sum(size)
                assert math.isclose(float(totalSzie), float(total), rel_tol=1e-9), \
                    f'下单总手数是：{totalSzie},订单详情总手数是：{total}'
                logging.info(f'下单总手数是：{totalSzie},订单详情总手数是：{total}')

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
                db_data = self.wait_for_database_record_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )

            with allure.step("2. 数据校验"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

                status = db_data[0]["status"]
                assert status in (0, 1), f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}"
                logging.info(f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}")

                total_lots = [record["total_lots"] for record in db_data]
                total_sumlots = sum(total_lots)
                totalSzie = trader_ordersend["totalSzie"]
                size = [record["size"] for record in db_data]
                total = sum(size)
                assert math.isclose(float(totalSzie), float(total_sumlots), rel_tol=1e-9) and \
                       math.isclose(float(totalSzie), float(total), rel_tol=1e-9), \
                    f'下单总手数是：{totalSzie}，指令表总手数是：{total_sumlots},订单详情总手数是：{total}'
                logging.info(f'下单总手数是：{totalSzie}，指令表总手数是：{total_sumlots},订单详情总手数是：{total}')

                self.assert_list_equal_ignore_order(
                    size,
                    total_lots,
                    f"订单详情列表的手数：{size}和指令列表的手数：{total_lots}不一致"
                )

        @allure.title("云策略交易下单-分配平仓")
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
                db_data = self.wait_for_database_record_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )
            with allure.step("2. 数据校验"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

                status = db_data[0]["status"]
                assert status in (0, 1), f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}"
                logging.info(f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}")

                totalSzie = trader_ordersend["totalSzie"]
                size = [record["size"] for record in db_data]
                total = sum(size)
                assert math.isclose(float(totalSzie), float(total), rel_tol=1e-9), \
                    f'下单总手数是：{totalSzie}，订单详情总手数是：{total}'
                logging.info(f'下单总手数是：{totalSzie}，订单详情总手数是：{total}')

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
                db_data = self.wait_for_database_record_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )
            with allure.step("2. 数据校验"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

                status = db_data[0]["status"]
                assert status in (0, 1), f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}"
                logging.info(f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}")

                totalSzie = trader_ordersend["totalSzie"]
                size = [record["size"] for record in db_data]
                total = sum(size)
                assert math.isclose(float(totalSzie), float(total), rel_tol=1e-9), \
                    f'下单总手数是：{totalSzie}，订单详情总手数是：{total}'
                logging.info(f'下单总手数是：{totalSzie}，订单详情总手数是：{total}')
                total_lots = [record["total_lots"] for record in db_data]
                self.assert_list_equal_ignore_order(
                    size,
                    total_lots,
                    f"订单详情列表的手数：{size}和指令列表的手数：{total_lots}不一致"
                )
                logging.info(f"订单详情列表的手数：{size}和指令列表的手数：{total_lots}")

            time.sleep(25)

    @allure.story("场景2：复制下单-手数0.1-1，总订单3，总手数1")
    @allure.description("""
    ### 测试说明
    - 前置条件：有云策略和云跟单
      1. 进行开仓，手数范围0.1-1，总订单3，总手数1
      2. 校验账号的数据是否正确
      3. 进行平仓
      4. 校验账号的数据是否正确
    - 预期结果：账号的数据正确
    """)
    class TestCloudtradingOrders2(APITestBase):
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
                "startSize": "0.10",
                "endSize": "1.00",
                "totalNum": "3",
                "totalSzie": "1.00",
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
                db_data = self.wait_for_database_record_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )
            with allure.step("2. 数据校验"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

                status = db_data[0]["status"]
                assert status in (0, 1), f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}"
                logging.info(f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}")

                min_lot_size = db_data[0]["min_lot_size"]
                endsize = trader_ordersend["endSize"]
                assert math.isclose(float(endsize), float(min_lot_size), rel_tol=1e-9), \
                    f'手数范围：结束手数是：{endsize}，实际是：{min_lot_size}'
                logging.info(f'手数范围：结束手数是：{endsize}，实际是：{min_lot_size}')

                max_lot_size = db_data[0]["max_lot_size"]
                startSize = trader_ordersend["startSize"]
                assert math.isclose(float(startSize), float(max_lot_size), rel_tol=1e-9), \
                    f'手数范围：开始手数是：{startSize}，实际是：{max_lot_size}'
                logging.info(f'手数范围：开始手数是：{startSize}，实际是：{max_lot_size}')

                total_orders = db_data[0]["total_orders"]
                totalNum = trader_ordersend["totalNum"]
                assert math.isclose(float(totalNum), float(total_orders), rel_tol=1e-9), \
                    f'总订单数量是：{totalNum}，实际是：{total_orders}'
                logging.info(f'总订单数量是：{totalNum}，实际是：{total_orders}')

                total_lots = db_data[0]["total_lots"]
                totalSzie = trader_ordersend["totalSzie"]
                assert math.isclose(float(totalSzie), float(total_lots), rel_tol=1e-9), \
                    f'下单总手数是：{totalSzie}，实际是：{total_lots}'
                logging.info(f'下单总手数是：{totalSzie}，实际是：{total_lots}')

                totalSzie = trader_ordersend["totalSzie"]
                size = [record["size"] for record in db_data]
                total = sum(size)
                assert math.isclose(float(totalSzie), float(total), rel_tol=1e-9), \
                    f'下单总手数是：{totalSzie},订单详情总手数是：{total}'
                logging.info(f'下单总手数是：{totalSzie},订单详情总手数是：{total}')

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
                db_data = self.wait_for_database_record_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )

            with allure.step("2. 数据校验"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

                status = db_data[0]["status"]
                assert status in (0, 1), f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}"
                logging.info(f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}")

                total_lots = [record["total_lots"] for record in db_data]
                total_sumlots = sum(total_lots)
                totalSzie = trader_ordersend["totalSzie"]
                size = [record["size"] for record in db_data]
                total = sum(size)
                assert math.isclose(float(totalSzie), float(total_sumlots), rel_tol=1e-9) and \
                       math.isclose(float(totalSzie), float(total), rel_tol=1e-9), \
                    f'下单总手数是：{totalSzie}，指令表总手数是：{total_sumlots},订单详情总手数是：{total}'
                logging.info(f'下单总手数是：{totalSzie}，指令表总手数是：{total_sumlots},订单详情总手数是：{total}')

                self.assert_list_equal_ignore_order(
                    size,
                    total_lots,
                    f"订单详情列表的手数：{size}和指令列表的手数：{total_lots}不一致"
                )

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
                db_data = self.wait_for_database_record_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )
            with allure.step("2. 数据校验"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

                status = db_data[0]["status"]
                assert status in (0, 1), f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}"
                logging.info(f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}")

                totalSzie = trader_ordersend["totalSzie"]
                size = [record["size"] for record in db_data]
                total = sum(size)
                assert math.isclose(float(totalSzie), float(total), rel_tol=1e-9), \
                    f'下单总手数是：{totalSzie}，订单详情总手数是：{total}'
                logging.info(f'下单总手数是：{totalSzie}，订单详情总手数是：{total}')

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
                db_data = self.wait_for_database_record_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )
            with allure.step("2. 数据校验"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

                status = db_data[0]["status"]
                assert status in (0, 1), f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}"
                logging.info(f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}")

                totalSzie = trader_ordersend["totalSzie"]
                size = [record["size"] for record in db_data]
                total = sum(size)
                assert math.isclose(float(totalSzie), float(total), rel_tol=1e-9), \
                    f'下单总手数是：{totalSzie}，订单详情总手数是：{total}'
                logging.info(f'下单总手数是：{totalSzie}，订单详情总手数是：{total}')
                total_lots = [record["total_lots"] for record in db_data]
                self.assert_list_equal_ignore_order(
                    size,
                    total_lots,
                    f"订单详情列表的手数：{size}和指令列表的手数：{total_lots}不一致"
                )
                logging.info(f"订单详情列表的手数：{size}和指令列表的手数：{total_lots}")

            time.sleep(25)

    @allure.story("场景3：复制下单-手数0.01-0.01，总手数0.01")
    @allure.description("""
    ### 测试说明
    - 前置条件：有云策略和云跟单
      1. 进行开仓，手数范围0.01-0.01，总手数0.01
      2. 校验账号的数据是否正确
      3. 进行平仓
      4. 校验账号的数据是否正确
    - 预期结果：账号的数据正确
    """)
    class TestCloudtradingOrders3(APITestBase):
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
                "startSize": "0.01",
                "endSize": "0.01",
                "totalNum": "",
                "totalSzie": "0.01",
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
                db_data = self.wait_for_database_record_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )
            with allure.step("2. 数据校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行复制下单校验")

                # 订单状态校验
                status = db_data[0]["status"]
                assert status in (0, 1), \
                    f"订单状态应为0(处理中)或1(全部成功)，实际为: {status}"
                logger.info(f"订单状态应为0(处理中)或1(全部成功)，实际为: {status}")

                # 结束手数校验
                min_lot_size = db_data[0]["min_lot_size"]
                assert math.isclose(float(0.01), float(min_lot_size), rel_tol=1e-9, abs_tol=1e-9), \
                    f'结束手数不匹配，预期: 0.01, 实际: {min_lot_size}'
                logger.info(f'结束手数预期: 0.01, 实际: {min_lot_size}')

                # 开始手数校验
                max_lot_size = db_data[0]["max_lot_size"]
                assert math.isclose(float(0.01), float(max_lot_size), rel_tol=1e-9, abs_tol=1e-9), \
                    f'开始手数不匹配，预期: 0.01, 实际: {max_lot_size}'
                logger.info(f'开始手数预期: 0.01, 实际: {max_lot_size}')

                # 总手数与指令表校验
                total_lots = db_data[0]["total_lots"]
                assert math.isclose(float(0.01), float(total_lots), rel_tol=1e-9, abs_tol=1e-9), \
                    f'总手数不匹配，预期: 0.01, 实际: {total_lots}'
                logger.info(f'总手数预期: 0.01, 实际: {total_lots}')

                # 总手数与订单详情校验
                size_sum = sum(record["size"] for record in db_data)
                assert math.isclose(float(0.01), float(size_sum), rel_tol=1e-9, abs_tol=1e-9), \
                    f'总手数与订单详情不匹配，预期: {0.01}, 实际: {size_sum}'
                logger.info(f'订单详情总手数预期: {0.01}, 实际: {size_sum}')

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
                db_data = self.wait_for_database_record_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )

            with allure.step("2. 数据校验"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

                status = db_data[0]["status"]
                assert status in (0, 1), f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}"
                logging.info(f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}")

                total_lots = [record["total_lots"] for record in db_data]
                total_sumlots = sum(total_lots)
                size = [record["size"] for record in db_data]
                total = sum(size)
                assert math.isclose(float(0.01), float(total_sumlots), rel_tol=1e-9) and \
                       math.isclose(float(0.01), float(total), rel_tol=1e-9), \
                    f'下单总手数是：0.01，指令表总手数是：{total_sumlots},订单详情总手数是：{total}'
                logging.info(f'下单总手数是：0.01，指令表总手数是：{total_sumlots},订单详情总手数是：{total}')

                self.assert_list_equal_ignore_order(
                    size,
                    total_lots,
                    f"订单详情列表的手数：{size}和指令列表的手数：{total_lots}不一致"
                )

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
                db_data = self.wait_for_database_record_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )
            with allure.step("2. 数据校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

                status = db_data[0]["status"]
                assert status in (0, 1), f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}"
                logging.info(f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}")

                size = [record["size"] for record in db_data]
                total = sum(size)
                assert math.isclose(float(0.01), float(total), rel_tol=1e-9), \
                    f'下单总手数是：0.01，订单详情总手数是：{total}'
                logging.info(f'下单总手数是：0.01，订单详情总手数是：{total}')

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
                db_data = self.wait_for_database_record_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )
            with allure.step("2. 数据校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

                status = db_data[0]["status"]
                assert status in (0, 1), f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}"
                logging.info(f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}")

                size = [record["size"] for record in db_data]
                total = sum(size)
                assert math.isclose(float(0.01), float(total), rel_tol=1e-9), \
                    f'下单总手数是：0.01，订单详情总手数是：{total}'
                logging.info(f'下单总手数是：0.01，订单详情总手数是：{total}')
                total_lots = [record["total_lots"] for record in db_data]
                self.assert_list_equal_ignore_order(
                    size,
                    total_lots,
                    f"订单详情列表的手数：{size}和指令列表的手数：{total_lots}不一致"
                )
                logging.info(f"订单详情列表的手数：{size}和指令列表的手数：{total_lots}")

            time.sleep(25)

    @allure.story("场景4：复制下单-手数0.01-1，总订单10")
    @allure.description("""
    ### 测试说明
    - 前置条件：有云策略和云跟单
      1. 进行开仓，手数范围0.01-1，总订单10
      2. 校验账号的数据是否正确
      3. 进行平仓
      4. 校验账号的数据是否正确
    - 预期结果：账号的数据正确
    """)
    class TestCloudtradingOrders4(APITestBase):
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
                "startSize": "0.01",
                "endSize": "1.00",
                "totalNum": "10",
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
                db_data = self.wait_for_database_record_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )
            with allure.step("2. 数据校验"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行复制下单校验")

                # 订单状态校验
                status = db_data[0]["status"]
                assert status in (0, 1), \
                    f"订单状态应为0(处理中)或1(全部成功)，实际为: {status}"
                logger.info(f"复制订单状态校验通过: {status}")

                # 结束手数校验
                min_lot_size = db_data[0]["min_lot_size"]
                endsize = trader_ordersend["endSize"]
                assert math.isclose(float(endsize), float(min_lot_size), rel_tol=1e-9, abs_tol=1e-9), \
                    f'结束手数不匹配，预期: {endsize}, 实际: {min_lot_size}'
                logger.info(f"复制下单结束手数校验通过: {endsize}")

                # 开始手数校验
                max_lot_size = db_data[0]["max_lot_size"]
                assert math.isclose(float(0.01), float(max_lot_size), rel_tol=1e-9, abs_tol=1e-9), \
                    f'开始手数不匹配，预期: 0.01, 实际: {max_lot_size}'
                logger.info(f"复制下单开始手数校验通过: {max_lot_size}")

                # 总订单数量校验
                total_orders = db_data[0]["total_orders"]
                assert math.isclose(float(10), float(total_orders), rel_tol=1e-9, abs_tol=1e-9), \
                    f'总订单数量不匹配，预期: 10, 实际: {total_orders}'
                logger.info(f"总订单数量校验通过: {total_orders}")

                assert len(db_data) == 10, f"应该有10个开仓订单，结果有{len(db_data)}个订单"

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
                db_data = self.wait_for_database_record_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )

            with allure.step("2. 数据校验"):
                assert len(db_data) == 10, f"应该有10个开仓订单，结果有{len(db_data)}个订单"

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
                db_data = self.wait_for_database_record_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )
            with allure.step("2. 数据校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

                status = db_data[0]["status"]
                assert status in (0, 1), f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}"
                logging.info(f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}")

                assert len(db_data) == 10, f"应该有10个开仓订单，结果有{len(db_data)}个订单"

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
                db_data = self.wait_for_database_record_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )
            with allure.step("2. 数据校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

                status = db_data[0]["status"]
                assert status in (0, 1), f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}"
                logging.info(f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}")

                size = [record["size"] for record in db_data]
                total_lots = [record["total_lots"] for record in db_data]
                self.assert_list_equal_ignore_order(
                    size,
                    total_lots,
                    f"订单详情列表的手数：{size}和指令列表的手数：{total_lots}不一致"
                )
                logging.info(f"订单详情列表的手数：{size}和指令列表的手数：{total_lots}")

                assert len(db_data) == 10, f"应该有10个开仓订单，结果有{len(db_data)}个订单"

            time.sleep(25)

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
                db_data = self.wait_for_database_record_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )
            with allure.step("2. 数据校验"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行复制下单校验")

                # 订单状态校验
                status = db_data[0]["status"]
                assert status in (0, 1), \
                    f"订单状态应为0(处理中)或1(全部成功)，实际为: {status}"
                logger.info(f"复制订单状态校验通过: {status}")

                # 结束手数校验
                min_lot_size = db_data[0]["min_lot_size"]
                endsize = trader_ordersend["endSize"]
                assert math.isclose(float(endsize), float(min_lot_size), rel_tol=1e-9, abs_tol=1e-9), \
                    f'结束手数不匹配，预期: {endsize}, 实际: {min_lot_size}'
                logger.info(f"复制下单结束手数校验通过: {endsize}")

                # 开始手数校验
                max_lot_size = db_data[0]["max_lot_size"]
                startSize = trader_ordersend["startSize"]
                assert math.isclose(float(startSize), float(max_lot_size), rel_tol=1e-9, abs_tol=1e-9), \
                    f'开始手数不匹配，预期: {startSize}, 实际: {max_lot_size}'
                logger.info(f"复制下单开始手数校验通过: {startSize}")

                # 总手数与指令表校验
                total_lots = db_data[0]["total_lots"]
                assert math.isclose(float(5), float(total_lots), rel_tol=1e-9, abs_tol=1e-9), \
                    f'总手数不匹配，预期: 5, 实际: {total_lots}'
                logger.info(f"复制下单总手数与指令表校验通过: {total_lots}")

                # 总手数与订单详情校验
                size_sum = sum(record["size"] for record in db_data)
                assert math.isclose(float(5), float(size_sum), rel_tol=1e-9, abs_tol=1e-9), \
                    f'总手数与订单详情不匹配，预期: 5, 实际: {size_sum}'
                logger.info(f"复制下单总手数与订单详情校验通过: {size_sum}")

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
                db_data = self.wait_for_database_record_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )

            with allure.step("2. 数据校验"):
                # 总手数与指令表校验
                total_lots = sum(record["total_lots"] for record in db_data)
                assert math.isclose(float(5), float(total_lots), rel_tol=1e-9, abs_tol=1e-9), \
                    f'总手数不匹配，预期: 5, 实际: {total_lots}'
                logger.info(f"复制下单总手数与指令表校验通过: {total_lots}")

                # 总手数与订单详情校验
                size_sum = sum(record["size"] for record in db_data)
                assert math.isclose(float(5), float(size_sum), rel_tol=1e-9, abs_tol=1e-9), \
                    f'总手数与订单详情不匹配，预期: 5, 实际: {size_sum}'
                logger.info(f"复制下单总手数与订单详情校验通过: {size_sum}")

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
                db_data = self.wait_for_database_record_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )
            with allure.step("2. 数据校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

                status = db_data[0]["status"]
                assert status in (0, 1), f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}"
                logging.info(f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}")

                # 总手数与指令表校验
                true_total_lots = db_data[0]["true_total_lots"]
                assert math.isclose(float(5), float(true_total_lots), rel_tol=1e-9, abs_tol=1e-9), \
                    f'总手数不匹配，预期: 5, 实际: {true_total_lots}'
                logger.info(f"复制下单总手数与指令表校验通过: {true_total_lots}")

                # 总手数与订单详情校验
                size_sum = sum(record["size"] for record in db_data)
                assert math.isclose(float(5), float(size_sum), rel_tol=1e-9, abs_tol=1e-9), \
                    f'总手数与订单详情不匹配，预期: 5, 实际: {size_sum}'
                logger.info(f"复制下单总手数与订单详情校验通过: {size_sum}")

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
                db_data = self.wait_for_database_record_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )
            with allure.step("2. 数据校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

                status = db_data[0]["status"]
                assert status in (0, 1), f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}"
                logging.info(f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}")

                size = [record["size"] for record in db_data]
                total_lots = [record["total_lots"] for record in db_data]
                self.assert_list_equal_ignore_order(
                    size,
                    total_lots,
                    f"订单详情列表的手数：{size}和指令列表的手数：{total_lots}不一致"
                )
                logging.info(f"订单详情列表的手数：{size}和指令列表的手数：{total_lots}")

                # 平仓总手数校验
                size_sum = sum(record["size"] for record in db_data)
                assert math.isclose(float(5), float(size_sum), rel_tol=1e-9, abs_tol=1e-9), \
                    f'复制平仓总手数不匹配，预期: 5, 实际: {size_sum}'
                logger.info(f"复制平仓总手数校验通过: {size_sum}")

            time.sleep(25)

    @allure.story("场景6：复制下单-手数0.1-1，总订单5-停止功能")
    @allure.description("""
    ### 测试说明
    - 前置条件：有云策略和云跟单
      1. 进行开仓，手数范围0.1-1，总订单5-停止功能
      2. 点击停止
      3. 校验账号的下单总手数和数据库的手数，应该不相等
      4. 进行平仓
      5. 校验账号的数据是否正确
    - 预期结果：账号的数据正确
    """)
    class TestCloudtradingOrders6(APITestBase):
        @allure.title("云策略交易下单-复制下单请求")
        def test_copy_order_send(self, logged_session, var_manager):
            # 发送云策略交易下单-复制下单请求
            masOrderSend = var_manager.get_variable("masOrderSend")
            cloudTrader_user_ids_2 = var_manager.get_variable("cloudTrader_user_ids_2")
            data = {
                "traderList": [cloudTrader_user_ids_2],
                "type": 0,
                "tradeType": 1,
                "intervalTime": 10000,
                "symbol": masOrderSend["symbol"],
                "placedType": 0,
                "startSize": "0.1",
                "endSize": "1.00",
                "totalNum": "5",
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

        @allure.title("数据库查询-获取停止的order_no")
        def test_copy_verify_db(self, var_manager, db_transaction):
            """验证复制下单后数据库中的订单数据正确性"""
            with allure.step("查询复制订单详情数据"):
                global order_no
                cloudTrader_vps_ids_1 = var_manager.get_variable("cloudTrader_vps_ids_1")
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
                params = ("1", "0", "1.00", "0.10", cloudTrader_vps_ids_1)

                # 轮询等待数据库记录
                db_data = self.wait_for_database_record(
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
        def test_cloudTrader_cloudStopOrder(self, logged_session, var_manager):
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
                    "复制下单响应msg字段应为success"
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
                db_data = self.wait_for_database_record_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )
            with allure.step("2. 数据校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行复制下单校验")

            assert len(db_data) != 5, f"开仓的订单数量应该不是5，结果有{len(db_data)}个订单"

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
                db_data = self.wait_for_database_record_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )

            with allure.step("2. 数据校验"):
                assert len(db_data) != 5, f"开仓的订单数量应该不是5，结果有{len(db_data)}个订单"

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
                db_data = self.wait_for_database_record_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )
            with allure.step("2. 数据校验"):
                assert len(db_data) != 5, f"平仓的订单数量应该不是5，结果有{len(db_data)}个订单"

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
                db_data = self.wait_for_database_record_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )
            with allure.step("2. 数据校验"):
                size = [record["size"] for record in db_data]
                total_lots = [record["total_lots"] for record in db_data]
                self.assert_list_equal_ignore_order(
                    size,
                    total_lots,
                    f"订单详情列表的手数：{size}和指令列表的手数：{total_lots}不一致"
                )
                logging.info(f"订单详情列表的手数：{size}和指令列表的手数：{total_lots}")

                assert len(db_data) != 5, f"平仓的订单数量应该不是5，结果有{len(db_data)}个订单"

            time.sleep(25)
