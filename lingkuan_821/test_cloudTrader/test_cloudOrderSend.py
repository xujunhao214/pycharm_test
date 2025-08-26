import allure
import logging
import pytest
import time
import math
from lingkuan_821.VAR.VAR import *
from lingkuan_821.conftest import var_manager
from lingkuan_821.commons.api_base import APITestBase

logger = logging.getLogger(__name__)
SKIP_REASON = "该用例暂时跳过"


@allure.feature("云策略复制下单-开仓的场景校验")
class TestCloudStrategyOrder:
    # @pytest.mark.skipif(condition=True, reason=SKIP_REASON)
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
    class TestMasOrderSend1(APITestBase):
        @allure.title("云策略-复制下单操作")
        def test_copy_place_order(self, logged_session, var_manager):
            """执行云策略复制下单操作并验证请求结果"""
            with allure.step("发送复制下单请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")

                request_data = {
                    "id": cloudMaster_id,
                    "type": 0,
                    "tradeType": 1,
                    "intervalTime": 100,
                    "cloudTraderId": [cloudTrader_traderList_4],
                    "symbol": "XAUUSD",
                    "placedType": 0,
                    "startSize": "0.10",
                    "endSize": "1.00",
                    "totalNum": "3",
                    "totalSzie": "1.00",
                    "remark": "测试数据"
                }

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudOrderSend',
                    json_data=request_data
                )

            with allure.step("验证复制下单响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制下单响应msg字段应为success"
                )

        @allure.title("数据库校验-复制下单数据")
        def test_copy_verify_db(self, var_manager, db_transaction):
            """验证复制下单后数据库中的订单数据正确性"""
            with allure.step("查询复制订单详情数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
                sql = """
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
                params = ('0', cloudTrader_user_accounts_4)

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

                # 总订单数量校验
                total_orders = db_data[0]["total_orders"]
                totalNum = trader_ordersend["totalNum"]
                assert math.isclose(float(totalNum), float(total_orders), rel_tol=1e-9, abs_tol=1e-9), \
                    f'总订单数量不匹配，预期: {totalNum}, 实际: {total_orders}'
                logger.info(f"总订单数量校验通过: {totalNum}")

                # 总手数与指令表校验
                total_lots = db_data[0]["total_lots"]
                totalSzie = trader_ordersend["totalSzie"]
                assert math.isclose(float(totalSzie), float(total_lots), rel_tol=1e-9, abs_tol=1e-9), \
                    f'总手数不匹配，预期: {totalSzie}, 实际: {total_lots}'
                logger.info(f"复制下单总手数与指令表校验通过: {totalSzie}")

                # 总手数与订单详情校验
                size_sum = sum(record["size"] for record in db_data)
                assert math.isclose(float(totalSzie), float(size_sum), rel_tol=1e-9, abs_tol=1e-9), \
                    f'总手数与订单详情不匹配，预期: {totalSzie}, 实际: {size_sum}'
                logger.info(f"复制下单总手数与订单详情校验通过: {totalSzie}")

        @allure.title("云策略-复制下单平仓操作")
        def test_copy_close_order(self, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("发送复制下单平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")

                request_data = {
                    "isCloseAll": 1,
                    "intervalTime": 100,
                    "id": f"{cloudMaster_id}",
                    "cloudTraderId": [cloudTrader_traderList_4]
                }

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudOrderClose',
                    json_data=request_data
                )

            with allure.step("验证复制平仓响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制平仓响应msg字段应为success"
                )

        @allure.title("数据库校验-复制下单平仓数据")
        def test_copy_verify_close_db(self, var_manager, db_transaction):
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
                params = ('1', cloudTrader_user_accounts_4, cloudTrader_vps_ids_3)

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

                # 平仓状态校验
                status = db_data[0]["status"]
                assert status in (0, 1), \
                    f"平仓状态应为0(处理中)或1(全部成功)，实际为: {status}"
                logger.info(f"复制平仓状态校验通过: {status}")

                # 平仓总手数校验
                totalSzie = trader_ordersend["totalSzie"]
                size_sum = sum(record["size"] for record in db_data)
                assert math.isclose(float(totalSzie), float(size_sum), rel_tol=1e-9, abs_tol=1e-9), \
                    f'复制平仓总手数不匹配，预期: {totalSzie}, 实际: {size_sum}'
                logger.info(f"复制平仓总手数校验通过: {totalSzie}")

            time.sleep(25)

    # @pytest.mark.skipif(condition=True, reason=SKIP_REASON)
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
    class TestMasOrderSend2(APITestBase):
        @allure.title("云策略-复制下单操作")
        def test_copy_place_order(self, logged_session, var_manager):
            """执行云策略复制下单操作并验证请求结果"""
            with allure.step("发送复制下单请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")

                request_data = {
                    "id": cloudMaster_id,
                    "type": 0,
                    "tradeType": 1,
                    "intervalTime": 100,
                    "cloudTraderId": [cloudTrader_traderList_4],
                    "symbol": "XAUUSD",
                    "placedType": 0,
                    "startSize": "0.01",
                    "endSize": "0.01",
                    "totalNum": "",
                    "totalSzie": "0.01",
                    "remark": ""
                }

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudOrderSend',
                    json_data=request_data
                )

            with allure.step("验证复制下单响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制下单响应msg字段应为success"
                )

        @allure.title("数据库校验-复制下单数据")
        @pytest.mark.retry(n=3, delay=5)
        def test_copy_verify_db(self, var_manager, db_transaction):
            """验证复制下单后数据库中的订单数据正确性"""
            with allure.step("查询复制订单详情数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
                sql = """
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
                params = ('0', cloudTrader_user_accounts_4)

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

        @allure.title("云策略-复制下单平仓操作")
        def test_copy_close_order(self, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("发送复制下单平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")

                request_data = {
                    "isCloseAll": 1,
                    "intervalTime": 100,
                    "id": f"{cloudMaster_id}",
                    "cloudTraderId": [cloudTrader_traderList_4]
                }

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudOrderClose',
                    json_data=request_data
                )

            with allure.step("验证复制平仓响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制平仓响应msg字段应为success"
                )

        @allure.title("数据库校验-复制下单平仓数据")
        def test_copy_verify_close_db(self, var_manager, db_transaction):
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
                params = ('1', cloudTrader_user_accounts_4, cloudTrader_vps_ids_3)

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

                # 平仓状态校验
                status = db_data[0]["status"]
                assert status in (0, 1), \
                    f"平仓状态应为0(处理中)或1(全部成功)，实际为: {status}"
                logger.info(f"复制平仓状态校验通过: {status}")

                # 平仓总手数校验
                size_sum = sum(record["size"] for record in db_data)
                assert math.isclose(float(0.01), float(size_sum), rel_tol=1e-9, abs_tol=1e-9), \
                    f'复制平仓总手数不匹配，预期: 0.01, 实际: {size_sum}'
                logger.info(f'复制平仓总手数匹配，预期: 0.01, 实际: {size_sum}')

            time.sleep(25)

    # @pytest.mark.skipif(condition=True, reason=SKIP_REASON)
    @allure.story("场景3：复制下单-手数0.01-1，总订单10")
    @allure.description("""
    ### 测试说明
    - 前置条件：有云策略和云跟单
      1. 进行开仓，手数范围0.01-1，总订单10
      2. 校验账号的数据是否正确
      3. 进行平仓
      4. 校验账号的数据是否正确
    - 预期结果：账号的数据正确
    """)
    class TestMasOrderSend3(APITestBase):
        @allure.title("云策略-复制下单操作")
        def test_copy_place_order(self, logged_session, var_manager):
            """执行云策略复制下单操作并验证请求结果"""
            with allure.step("发送复制下单请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")

                request_data = {
                    "id": cloudMaster_id,
                    "type": 0,
                    "tradeType": 1,
                    "intervalTime": 100,
                    "cloudTraderId": [cloudTrader_traderList_4],
                    "symbol": "XAUUSD",
                    "placedType": 0,
                    "startSize": "0.01",
                    "endSize": "1.00",
                    "totalNum": "10",
                    "totalSzie": "",
                    "remark": ""
                }

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudOrderSend',
                    json_data=request_data
                )

            with allure.step("验证复制下单响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制下单响应msg字段应为success"
                )

        @allure.title("数据库校验-复制下单数据")
        def test_copy_verify_db(self, var_manager, db_transaction):
            """验证复制下单后数据库中的订单数据正确性"""
            with allure.step("查询复制订单详情数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
                sql = """
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
                params = ('0', cloudTrader_user_accounts_4)

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

        @allure.title("云策略-复制下单平仓操作")
        def test_copy_close_order(self, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("发送复制下单平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")

                request_data = {
                    "isCloseAll": 1,
                    "intervalTime": 100,
                    "id": f"{cloudMaster_id}",
                    "cloudTraderId": [cloudTrader_traderList_4]
                }

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudOrderClose',
                    json_data=request_data
                )

            with allure.step("验证复制平仓响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制平仓响应msg字段应为success"
                )

        @allure.title("数据库校验-复制下单平仓数据")
        def test_copy_verify_close_db(self, var_manager, db_transaction):
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
                params = ('1', cloudTrader_user_accounts_4, cloudTrader_vps_ids_3)

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

                # 平仓状态校验
                status = db_data[0]["status"]
                assert status in (0, 1), \
                    f"平仓状态应为0(处理中)或1(全部成功)，实际为: {status}"
                logger.info(f"复制平仓状态校验通过: {status}")

            time.sleep(25)

    # @pytest.mark.skipif(condition=True, reason=SKIP_REASON)
    @allure.story("场景4：复制下单-手数0.1-1，总手数5")
    @allure.description("""
    ### 测试说明
    - 前置条件：有云策略和云跟单
      1. 进行开仓，手数范围0.1-1，总手数5
      2. 校验账号的数据是否正确
      3. 进行平仓
      4. 校验账号的数据是否正确
    - 预期结果：账号的数据正确
    """)
    class TestMasOrderSend4(APITestBase):
        @allure.title("云策略-复制下单操作")
        def test_copy_place_order(self, logged_session, var_manager):
            """执行云策略复制下单操作并验证请求结果"""
            with allure.step("发送复制下单请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")

                request_data = {
                    "id": cloudMaster_id,
                    "type": 0,
                    "tradeType": 1,
                    "intervalTime": 100,
                    "cloudTraderId": [cloudTrader_traderList_4],
                    "symbol": "XAUUSD",
                    "placedType": 0,
                    "startSize": "0.1",
                    "endSize": "1.00",
                    "totalNum": "",
                    "totalSzie": "5",
                    "remark": "测试数据"
                }

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudOrderSend',
                    json_data=request_data
                )

            with allure.step("验证复制下单响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制下单响应msg字段应为success"
                )

        @allure.title("数据库校验-复制下单数据")
        def test_copy_verify_db(self, var_manager, db_transaction):
            """验证复制下单后数据库中的订单数据正确性"""
            with allure.step("查询复制订单详情数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
                sql = """
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
                params = ('0', cloudTrader_user_accounts_4)

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

        # @pytest.mark.skipif(condition=True, reason=SKIP_REASON)
        @allure.title("云策略-复制下单平仓操作")
        def test_copy_close_order(self, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("发送复制下单平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")

                request_data = {
                    "isCloseAll": 1,
                    "intervalTime": 100,
                    "id": f"{cloudMaster_id}",
                    "cloudTraderId": [cloudTrader_traderList_4]
                }

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudOrderClose',
                    json_data=request_data
                )

            with allure.step("验证复制平仓响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制平仓响应msg字段应为success"
                )

        # @pytest.mark.skipif(condition=True, reason=SKIP_REASON)
        @allure.title("数据库校验-复制下单平仓数据")
        def test_copy_verify_close_db(self, var_manager, db_transaction):
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
                params = ('1', cloudTrader_user_accounts_4, cloudTrader_vps_ids_3)

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

                # 平仓状态校验
                status = db_data[0]["status"]
                assert status in (0, 1), \
                    f"平仓状态应为0(处理中)或1(全部成功)，实际为: {status}"
                logger.info(f"复制平仓状态校验通过: {status}")

                # 平仓总手数校验
                size_sum = sum(record["size"] for record in db_data)
                assert math.isclose(float(5), float(size_sum), rel_tol=1e-9, abs_tol=1e-9), \
                    f'复制平仓总手数不匹配，预期: 5, 实际: {size_sum}'
                logger.info(f"复制平仓总手数校验通过: {size_sum}")

            time.sleep(25)

    # @pytest.mark.skipif(condition=True, reason=SKIP_REASON)
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
    class TestMasOrderSend5(APITestBase):
        @allure.title("云策略-复制下单操作")
        def test_copy_place_order(self, logged_session, var_manager):
            """执行云策略复制下单操作并验证请求结果"""
            with allure.step("发送复制下单请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")

                request_data = {
                    "id": cloudMaster_id,
                    "type": 0,
                    "tradeType": 1,
                    "intervalTime": 10000,
                    "cloudTraderId": [cloudTrader_traderList_4],
                    "symbol": "XAUUSD",
                    "placedType": 0,
                    "startSize": "0.1",
                    "endSize": "1.00",
                    "totalNum": "5",
                    "totalSzie": "",
                    "remark": "测试数据"
                }

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudOrderSend',
                    json_data=request_data
                )

            with allure.step("验证复制下单响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制下单响应msg字段应为success"
                )

        @allure.title("数据库查询-获取停止的order_no")
        def test_copy_verify_db(self, var_manager, db_transaction):
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
        def test_cloudTrader_cloudStopOrder(self, logged_session, var_manager):
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
                    "复制下单响应msg字段应为success"
                )

        @allure.title("数据库校验-复制下单数据")
        def test_copy_verify_db2(self, var_manager, db_transaction):
            """验证复制下单后数据库中的订单数据正确性"""
            with allure.step("查询复制订单详情数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
                sql = """
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
                params = ('0', cloudTrader_user_accounts_4)

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

                # 校验订单数和下单总订单数
                assert len(db_data) != 5, f"开仓的订单数量应该不是5，结果有{len(db_data)}个订单"

        # @pytest.mark.skipif(condition=True, reason=SKIP_REASON)
        @allure.title("云策略-复制下单平仓操作")
        def test_copy_close_order(self, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("发送复制下单平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")

                request_data = {
                    "isCloseAll": 1,
                    "intervalTime": 100,
                    "id": f"{cloudMaster_id}",
                    "cloudTraderId": [cloudTrader_traderList_4]
                }

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudOrderClose',
                    json_data=request_data
                )

            with allure.step("验证复制平仓响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制平仓响应msg字段应为success"
                )

            time.sleep(25)

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
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")

                request_data = {
                    "id": cloudMaster_id,
                    "type": 0,
                    "tradeType": 0,
                    "cloudTraderId": [cloudTrader_traderList_4],
                    "symbol": "XAUUSD",
                    "startSize": "0.10",
                    "endSize": "1.00",
                    "totalSzie": "1.00",
                    "remark": "测试数据",
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

        @allure.title("数据库校验-分配下单数据")
        def test_allocation_verify_db(self, var_manager, db_transaction):
            """验证分配下单后数据库中的订单数据正确性"""
            with allure.step("查询订单详情数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
                sql = """
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
                params = ('0', cloudTrader_user_accounts_4)

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

                # 订单状态校验
                status = db_data[0]["status"]
                assert status in (0, 1), \
                    f"订单状态应为0(处理中)或1(全部成功)，实际为: {status}"
                logger.info(f"订单状态校验通过: {status}")

                # 结束手数校验
                min_lot_size = db_data[0]["min_lot_size"]
                endsize = trader_ordersend["endSize"]
                assert math.isclose(float(endsize), float(min_lot_size), rel_tol=1e-9, abs_tol=1e-9), \
                    f'结束手数不匹配，预期: {endsize}, 实际: {min_lot_size}'
                logger.info(f"结束手数校验通过: {endsize}")

                # 开始手数校验
                max_lot_size = db_data[0]["max_lot_size"]
                startSize = trader_ordersend["startSize"]
                assert math.isclose(float(startSize), float(max_lot_size), rel_tol=1e-9, abs_tol=1e-9), \
                    f'开始手数不匹配，预期: {startSize}, 实际: {max_lot_size}'
                logger.info(f"开始手数校验通过: {startSize}")

                # 总手数与指令表校验
                total_lots = db_data[0]["total_lots"]
                totalSzie = trader_ordersend["totalSzie"]
                assert math.isclose(float(totalSzie), float(total_lots), rel_tol=1e-9, abs_tol=1e-9), \
                    f'总手数不匹配，预期: {totalSzie}, 实际: {total_lots}'
                logger.info(f"总手数与指令表校验通过: {totalSzie}")

                # 总手数与订单详情校验
                size_sum = sum(record["size"] for record in db_data)
                assert math.isclose(float(totalSzie), float(size_sum), rel_tol=1e-9, abs_tol=1e-9), \
                    f'总手数与订单详情不匹配，预期: {totalSzie}, 实际: {size_sum}'
                logger.info(f"总手数与订单详情校验通过: {totalSzie}")

        @allure.title("云策略-分配下单平仓操作")
        def test_allocation_close_order(self, logged_session, var_manager):
            """执行分配下单的平仓操作并验证结果"""
            with allure.step("发送平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")

                request_data = {
                    "isCloseAll": 1,
                    "intervalTime": 100,
                    "id": f"{cloudMaster_id}",
                    "cloudTraderId": [cloudTrader_traderList_4]
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

        @allure.title("数据库校验-分配下单平仓数据")
        def test_allocation_verify_close_db(self, var_manager, db_transaction):
            """验证分配下单平仓后数据库中的订单数据正确性"""
            with allure.step("查询平仓订单数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
                cloudTrader_vps_ids_3 = var_manager.get_variable("cloudTrader_vps_ids_3")

                sql = """
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
                params = ('1', cloudTrader_user_accounts_4, cloudTrader_vps_ids_3)

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

                # 平仓状态校验
                status = db_data[0]["status"]
                assert status in (0, 1), \
                    f"平仓状态应为0(处理中)或1(全部成功)，实际为: {status}"
                logger.info(f"平仓状态校验通过: {status}")

                # 平仓总手数校验
                totalSzie = trader_ordersend["totalSzie"]
                size_sum = sum(record["size"] for record in db_data)
                assert math.isclose(float(totalSzie), float(size_sum), rel_tol=1e-9, abs_tol=1e-9), \
                    f'平仓总手数不匹配，预期: {totalSzie}, 实际: {size_sum}'
                logger.info(f"平仓总手数校验通过: {totalSzie}")

            time.sleep(25)
