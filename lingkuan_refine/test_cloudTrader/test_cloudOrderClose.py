import allure
import logging
import pytest
import time
import math
from lingkuan_refine.VAR.VAR import *
from lingkuan_refine.conftest import var_manager
from lingkuan_refine.commons.api_base import APITestBase  # 导入基础类
import requests
from lingkuan_refine.commons.jsonpath_utils import JsonPathUtils

logger = logging.getLogger(__name__)
SKIP_REASON = "该用例暂时跳过"


# ------------------------------------
# 大模块1：云策略复制下单-平仓的停止功能校验
# ------------------------------------
@allure.feature("云策略复制下单-平仓的功能校验（多场景汇总）")
# @pytest.mark.skipif(True, reason=SKIP_REASON)
@pytest.mark.retry(n=3, delay=5)
class TestCloudCoreFunctionality:
    @allure.story("场景1：平仓的停止功能校验")
    @allure.description("""
    ### 测试说明
    - 前置条件：有云策略和云跟单
      1. 进行开仓，手数范围0.1-1，总订单4
      2. 进行平仓，校验币种，币种错误应该没有开仓订单
      3. 进行平仓，点击停止
      4. 校验平仓的订单数，应该不等于开仓总订单
      5. 进行平仓
    - 预期结果：平仓的停止功能正确
    """)
    class TestMasOrderSend1(APITestBase):
        @allure.title("云策略-复制下单操作")
        def test_copy_place_order(self, logged_session, var_manager):
            """执行云策略复制下单操作并验证请求结果"""
            with allure.step("发送复制下单请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
                new_user = var_manager.get_variable("new_user")

                request_data = {
                    "id": cloudMaster_id,
                    "type": 0,
                    "tradeType": 1,
                    "intervalTime": 100,
                    "cloudTraderId": [cloudTrader_traderList_4],
                    "symbol": new_user['symbol'],
                    "placedType": 0,
                    "startSize": "0.10",
                    "endSize": "1.00",
                    "totalNum": "4",
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

        @allure.title("云策略-复制下单平仓操作-币种错误")
        def test_copy_close_symbol(self, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("发送复制下单平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
                new_user = var_manager.get_variable("new_user")

                request_data = {
                    "id": cloudMaster_id,
                    "flag": 0,
                    "intervalTime": 10000,
                    "closeType": 0,
                    "remark": "",
                    "cloudTraderId": [cloudTrader_traderList_4],
                    "symbol": "XAGEUR",
                    "type": 0
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
        def test_copy_verify_close_dbsymbol(self, var_manager, db_transaction):
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
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )

            with allure.step("执行复制平仓数据校验-订单不等于开仓总订单数量"):
                assert len(db_data) == 0, "数据库中存在处理的平仓订单，不符合预期"

        @allure.title("云策略-复制下单平仓操作")
        def test_copy_close_order(self, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("发送复制下单平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
                new_user = var_manager.get_variable("new_user")

                request_data = {
                    "id": cloudMaster_id,
                    "flag": 0,
                    "intervalTime": 10000,
                    "closeType": 0,
                    "remark": "",
                    "cloudTraderId": [cloudTrader_traderList_4],
                    "symbol": new_user['symbol'],
                    "type": 0
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

        @allure.title("云策略-复制下单平仓-停止操作")
        def test_copy_close_cloudStopOrder(self, logged_session, var_manager):
            with allure.step("发送停止平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")

                params = {
                    "id": cloudMaster_id,
                    "type": "1"
                }

                response = self.send_get_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudStopOrder',
                    params=params
                )

            with allure.step("验证停止平仓响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "停止平仓响应msg字段应为success"
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
                db_data = self.wait_for_database_record_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )

            with allure.step("执行复制平仓数据校验-订单不等于开仓总订单数量"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行复制平仓校验")

                assert len(db_data) != 4, "复制平仓数据应该不等于开仓总订单数量"

        @allure.title("云策略-复制下单平仓操作")
        def test_copy_close_order2(self, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("发送复制下单平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
                new_user = var_manager.get_variable("new_user")

                request_data = {
                    "id": cloudMaster_id,
                    "flag": 0,
                    "intervalTime": 0,
                    "closeType": 0,
                    "remark": "",
                    "cloudTraderId": [cloudTrader_traderList_4],
                    "symbol": new_user['symbol'],
                    "type": 0
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
            time.sleep(30)


# ------------------------------------
# 大模块2：云策略复制下单-平仓的订单方向验证
# ------------------------------------
@allure.feature("云策略复制下单-平仓的功能校验（多场景汇总）")
# @pytest.mark.skipif(True, reason=SKIP_REASON)
@pytest.mark.retry(n=3, delay=5)
class TestCloudFollowDirection:
    @allure.story("场景2：平仓的订单方向功能校验-sell")
    @allure.description("""
    ### 测试说明
    - 前置条件：有云策略和云跟单
      1. 进行开仓，手数范围0.1-1，总订单3，总手数1
      2. 平仓-订单方向-sell，平仓失败
      3. 校验数据库是否有平仓订单-应该没有
      4. 平仓-订单方向-buy，平仓成功
      5. 校验订单数据是否正确
    - 预期结果：平仓的订单方向功能正确
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

        @allure.title("云策略-复制下单平仓操作-sell-平仓失败")
        def test_copy_close_order(self, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("发送复制下单平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
                new_user = var_manager.get_variable("new_user")

                request_data = {
                    "id": cloudMaster_id,
                    "flag": 0,
                    "intervalTime": 0,
                    "closeType": 0,
                    "remark": "",
                    "cloudTraderId": [cloudTrader_traderList_4],
                    "symbol": new_user['symbol'],
                    "type": 1
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

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
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
                           AND foi.total_orders = %s
                   """
                params = ('1', cloudTrader_user_accounts_4, cloudTrader_vps_ids_3, "3")

                # 轮询等待数据库记录
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.create_time"
                )

            with allure.step("执行复制平仓数据校验-没有订单"):
                assert len(db_data) == 0, "数据库中存在处理的平仓订单，不符合预期"

        @allure.title("云策略-复制下单平仓操作-buy-平仓成功")
        def test_copy_close_order2(self, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("发送复制下单平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
                new_user = var_manager.get_variable("new_user")

                request_data = {
                    "id": cloudMaster_id,
                    "flag": 0,
                    "intervalTime": 0,
                    "closeType": 0,
                    "remark": "",
                    "cloudTraderId": [cloudTrader_traderList_4],
                    "symbol": new_user['symbol'],
                    "type": 0
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

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
        def test_copy_verify_close_db2(self, var_manager, db_transaction):
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
                db_data = self.wait_for_database_record_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )

            with allure.step("执行复制平仓数据校验-有订单"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行复制平仓校验")

                # 平仓总手数校验
                totalSzie = trader_ordersend["totalSzie"]
                size_sum = sum(record["size"] for record in db_data)
                assert math.isclose(float(totalSzie), float(size_sum), rel_tol=1e-9, abs_tol=1e-9), \
                    f'复制平仓总手数不匹配，预期: {totalSzie}, 实际: {size_sum}'
                logger.info(f"复制平仓总手数校验通过: {totalSzie}")

        time.sleep(30)

    # @pytest.mark.skipif(condition=True, reason=SKIP_REASON)
    @allure.story("场景3：平仓的订单方向功能校验-buy sell")
    @allure.description("""
    ### 测试说明
    - 前置条件：有云策略和云跟单
      1. 进行开仓，手数范围0.1-1，总订单3，总手数1
      2. 平仓-订单方向-sell，平仓失败
      3. 校验数据库是否有平仓订单-应该没有
      4. 平仓-订单方向-buy sell，平仓成功
      5. 校验订单数据是否正确
    - 预期结果：平仓的订单方向功能正确
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
                    "startSize": "0.10",
                    "endSize": "1.00",
                    "totalNum": "4",
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

        @allure.title("云策略-复制下单平仓操作-sell-平仓失败")
        def test_copy_close_order(self, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("发送复制下单平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
                new_user = var_manager.get_variable("new_user")

                request_data = {
                    "id": cloudMaster_id,
                    "flag": 0,
                    "intervalTime": 0,
                    "closeType": 0,
                    "remark": "",
                    "cloudTraderId": [cloudTrader_traderList_4],
                    "symbol": new_user['symbol'],
                    "type": 1
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

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
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
                           AND foi.total_orders = %s
                   """
                params = ('1', cloudTrader_user_accounts_4, cloudTrader_vps_ids_3, "4")

                # 轮询等待数据库记录
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.create_time"
                )

            with allure.step("执行复制平仓数据校验-没有订单"):
                assert len(db_data) == 0, "数据库中存在处理的平仓订单，不符合预期"

        @allure.title("云策略-复制下单平仓操作-buy sell-平仓成功")
        def test_copy_close_order2(self, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("发送复制下单平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
                new_user = var_manager.get_variable("new_user")

                request_data = {
                    "id": cloudMaster_id,
                    "flag": 0,
                    "intervalTime": 0,
                    "closeType": 0,
                    "remark": "",
                    "cloudTraderId": [cloudTrader_traderList_4],
                    "symbol": new_user['symbol'],
                    "type": 2
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

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
        def test_copy_verify_close_db2(self, var_manager, db_transaction):
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
                db_data = self.wait_for_database_record_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )

            with allure.step("执行复制平仓数据校验-有订单"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行复制平仓校验")

                # 平仓总手数校验
                totalSzie = trader_ordersend["totalSzie"]
                size_sum = sum(record["size"] for record in db_data)
                assert math.isclose(float(totalSzie), float(size_sum), rel_tol=1e-9, abs_tol=1e-9), \
                    f'复制平仓总手数不匹配，预期: {totalSzie}, 实际: {size_sum}'
                logger.info(f"复制平仓总手数校验通过: {totalSzie}")

            time.sleep(30)


# ------------------------------------
# 大模块3：云策略复制下单-平仓的订单数量功能校验
# ------------------------------------
@allure.feature("云策略复制下单-平仓的功能校验（多场景汇总）")
# @pytest.mark.skipif(True, reason=SKIP_REASON)
@pytest.mark.retry(n=3, delay=5)
class TestCloudOrderQuantityControl:
    @allure.story("场景4：平仓的订单数量功能校验")
    @allure.description("""
    ### 测试说明
    - 前置条件：有云策略和云跟单
      1. 进行开仓，手数范围0.1-1，总订单数量4
      2. 平仓-平仓订单数量-2
      3. 校验数据库是否有2个平仓订单
      4. 平仓-平仓订单数量-2
      5. 校验订单数据是否正确
    - 预期结果：平仓的订单数量功能正确
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
                    "startSize": "0.10",
                    "endSize": "1.00",
                    "totalNum": "4",
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

        @allure.title("云策略-复制下单平仓操作-平仓两个订单")
        def test_copy_close_order(self, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("发送复制下单平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
                new_user = var_manager.get_variable("new_user")

                request_data = {
                    "id": cloudMaster_id,
                    "flag": 0,
                    "intervalTime": 0,
                    "num": "2",
                    "closeType": 0,
                    "remark": "",
                    "cloudTraderId": [cloudTrader_traderList_4],
                    "symbol": new_user['symbol'],
                    "type": 0
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

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
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
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.create_time"
                )

            with allure.step("执行复制平仓数据校验-有两个订单"):
                assert len(db_data) == 2, "数据库中没有2个处理的平仓订单，不符合预期"

        @allure.title("云策略-复制下单平仓操作-再次平仓两个订单")
        def test_copy_close_order2(self, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("发送复制下单平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
                new_user = var_manager.get_variable("new_user")

                request_data = {
                    "id": cloudMaster_id,
                    "flag": 0,
                    "intervalTime": 0,
                    "num": "2",
                    "closeType": 0,
                    "remark": "",
                    "cloudTraderId": [cloudTrader_traderList_4],
                    "symbol": new_user['symbol'],
                    "type": 0
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

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
        def test_copy_verify_close_db2(self, var_manager, db_transaction):
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
                db_data = self.wait_for_database_record_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )

            with allure.step("执行复制平仓数据校验-有四个订单"):
                assert len(db_data) == 4, "数据库中没有4个处理的平仓订单，不符合预期"

            time.sleep(30)


# ------------------------------------
# 大模块4：云策略复制下单-平仓的订单类型功能校验
# ------------------------------------
@allure.feature("云策略复制下单-平仓的功能校验（多场景汇总）")
# @pytest.mark.skipif(True, reason=SKIP_REASON)
@pytest.mark.retry(n=3, delay=5)
class TestCloudOrderType:
    @allure.story("场景5：平仓的订单类型功能校验-内部订单")
    @allure.description("""
    ### 测试说明
    - 前置条件：有云策略和云跟单
      1. 进行开仓，手数范围0.1-1，总订单数量2
      2. 平仓-平仓订单数量-1，订单类型-外部订单
      3. 校验数据库是否有平仓订单-应该没有
      4. 平仓-平仓订单数量-1，订单类型-内部订单
      5. 校验订单数据是否正确
    - 预期结果：平仓的订单类型功能正确
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
                    "intervalTime": 100,
                    "cloudTraderId": [cloudTrader_traderList_4],
                    "symbol": "XAUUSD",
                    "placedType": 0,
                    "startSize": "0.10",
                    "endSize": "1.00",
                    "totalNum": "2",
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

        @allure.title("云策略-复制下单平仓操作-订单类型-外部订单")
        def test_copy_close_order(self, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("发送复制下单平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
                new_user = var_manager.get_variable("new_user")

                request_data = {
                    "id": cloudMaster_id,
                    "flag": 0,
                    "intervalTime": 0,
                    "num": "",
                    "closeType": 1,
                    "remark": "",
                    "cloudTraderId": [cloudTrader_traderList_4],
                    "symbol": new_user['symbol'],
                    "type": 0
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

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
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
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.create_time"
                )

            with allure.step("执行复制平仓数据校验-没有订单"):
                assert len(db_data) != 2, "数据库中存在2个处理的平仓订单，不符合预期"

        @allure.title("云策略-复制下单平仓操作-订单类型-内部订单")
        def test_copy_close_order2(self, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("发送复制下单平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
                new_user = var_manager.get_variable("new_user")

                request_data = {
                    "id": cloudMaster_id,
                    "flag": 0,
                    "intervalTime": 0,
                    "num": "2",
                    "closeType": 0,
                    "remark": "",
                    "cloudTraderId": [cloudTrader_traderList_4],
                    "symbol": new_user['symbol'],
                    "type": 0
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

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
        def test_copy_verify_close_db2(self, var_manager, db_transaction):
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
                db_data = self.wait_for_database_record_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )

            with allure.step("执行复制平仓数据校验-2个订单"):
                assert len(db_data) == 2, "数据库中没有2个处理的平仓订单，不符合预期"

            time.sleep(30)

    # @pytest.mark.skipif(condition=True, reason=SKIP_REASON)
    @allure.story("场景6：平仓的订单类型功能校验-外部订单")
    @allure.description("""
    ### 测试说明
    - 前置条件：有云策略和云跟单
      1. 进行开仓，手数范围0.1-1，总订单数量2
      2. 平仓-平仓订单数量-1，订单类型-内部订单
      3. 校验数据库是否有平仓订单-应该没有
      4. 平仓-平仓订单数量-1，订单类型-外部订单
      5. 校验订单数据是否正确
    - 预期结果：平仓的订单类型功能正确
    """)
    class TestMasOrderSend6(APITestBase):
        @allure.title("登录MT4账号获取token")
        @pytest.mark.retry(n=3, delay=5)
        def test_mt4_login(self, var_manager):
            global token_mt4, headers
            url = "https://mt4.mtapi.io/Connect?user=300162&password=Test123456&host=47.238.99.66&port=443&connectTimeoutSeconds=30"

            payload = {}
            headers = {
                'Authorization': 'e5f9f574-fd0a-42bd-904b-3a7a088de27e',
                'x-sign': '417B110F1E71BD2CFE96366E67849B0B',
                'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
                'Content-Type': 'application/json',
                'Accept': '*/*',
                'Host': 'mt4.mtapi.io',
                'Connection': 'keep-alive'
            }

            response = requests.request("GET", url, headers=headers, data=payload)
            token_mt4 = response.text
            print(token_mt4)

        @allure.title("MT4平台开仓操作")
        def test_mt4_open(self, var_manager):
            url = f"https://mt4.mtapi.io/OrderSend?id={token_mt4}&symbol=XAUUSD&operation=Buy&volume=1&placedType=Client&price=0.00"

            payload = ""
            self.response = requests.request("GET", url, headers=headers, data=payload)
            self.json_utils = JsonPathUtils()
            self.response = self.response.json()  # 解析JSON响应
            ticket = self.json_utils.extract(self.response, "$.ticket")
            print(ticket)

        @allure.title("云策略-复制下单平仓操作-订单类型-内部订单")
        def test_copy_close_order(self, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("发送复制下单平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
                new_user = var_manager.get_variable("new_user")

                request_data = {
                    "id": cloudMaster_id,
                    "flag": 0,
                    "intervalTime": 0,
                    "num": "1",
                    "closeType": 0,
                    "remark": "",
                    "cloudTraderId": [cloudTrader_traderList_4],
                    "symbol": new_user['symbol'],
                    "type": 0
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

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
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
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.create_time"
                )

            with allure.step("执行复制平仓数据校验-没有订单"):
                assert len(db_data) != 1, "数据库中存在1个处理的平仓订单，不符合预期"

        @allure.title("云策略-复制下单平仓操作-订单类型-外部订单")
        def test_copy_close_order2(self, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("发送复制下单平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
                new_user = var_manager.get_variable("new_user")

                request_data = {
                    "id": cloudMaster_id,
                    "flag": 0,
                    "intervalTime": 0,
                    "num": "",
                    "closeType": 1,
                    "remark": "",
                    "cloudTraderId": [cloudTrader_traderList_4],
                    "symbol": new_user['symbol'],
                    "type": 0
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

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
        def test_copy_verify_close_db2(self, var_manager, db_transaction):
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
                db_data = self.wait_for_database_record_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )

            with allure.step("执行复制平仓数据校验-有订单"):
                assert len(db_data) == 1, "数据库中没有处理的平仓订单，不符合预期"

            time.sleep(30)

    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    @allure.story("场景7：平仓的订单类型功能校验-全部订单")
    @allure.description("""
    ### 测试说明
    - 前置条件：有云策略和云跟单
      1. 进行开仓，手数范围0.1-1，总订单数量2
      2. 平仓-平仓订单数量-1，订单类型-外部订单
      3. 校验数据库是否有平仓订单-应该没有
      4. 平仓-平仓订单数量-1，订单类型-全部订单
      5. 校验订单数据是否正确
    - 预期结果：平仓的订单类型功能正确
    """)
    class TestMasOrderSend7(APITestBase):
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
                    "totalNum": "2",
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

        @allure.title("云策略-复制下单平仓操作-订单类型-外部订单")
        def test_copy_close_order(self, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("发送复制下单平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
                new_user = var_manager.get_variable("new_user")

                request_data = {
                    "id": cloudMaster_id,
                    "flag": 0,
                    "intervalTime": 0,
                    "num": "",
                    "closeType": 1,
                    "remark": "",
                    "cloudTraderId": [cloudTrader_traderList_4],
                    "symbol": new_user['symbol'],
                    "type": 0
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

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
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
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.create_time"
                )

            with allure.step("执行复制平仓数据校验-没有订单"):
                assert len(db_data) != 2, "数据库中存在2个处理的平仓订单，不符合预期"

        @allure.title("云策略-复制下单平仓操作-订单类型-全部订单")
        def test_copy_close_order2(self, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("发送复制下单平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
                new_user = var_manager.get_variable("new_user")

                request_data = {
                    "id": cloudMaster_id,
                    "flag": 0,
                    "intervalTime": 0,
                    "num": "",
                    "closeType": 2,
                    "remark": "",
                    "cloudTraderId": [cloudTrader_traderList_4],
                    "symbol": new_user['symbol'],
                    "type": 0
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

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
        def test_copy_verify_close_db2(self, var_manager, db_transaction):
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
                db_data = self.wait_for_database_record_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )

            with allure.step("执行复制平仓数据校验-2个订单"):
                assert len(db_data) == 2, "数据库中没有2个处理的平仓订单，不符合预期"

            time.sleep(30)


# ------------------------------------
# 大模块5：云策略复制下单-平仓的订单备注功能校验
# ------------------------------------
@allure.feature("云策略复制下单-平仓的功能校验（多场景汇总）")
# @pytest.mark.skipif(True, reason=SKIP_REASON)
@pytest.mark.retry(n=3, delay=5)
class TestCloudCloseRemark:
    @allure.story("场景8：平仓的订单备注功能校验")
    @allure.description("""
    ### 测试说明
    - 前置条件：有云策略和云跟单
      1. 进行开仓，手数范围0.1-1，总订单数量2，备注是：ceshipingcangbeizhu
      2. 平仓-平仓备注是：xxxxxxxx
      3. 校验数据库是否有平仓订单-应该没有
      4. 平仓-平仓备注是：ceshipingcangbeizhu
      5. 校验订单数据是否正确
    - 预期结果：平仓的订单备注功能正确
    """)
    class TestMasOrderSend8(APITestBase):
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
                    "totalNum": "2",
                    "totalSzie": "",
                    "remark": "ceshipingcangbeizhu"
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

        @allure.title("云策略-复制下单平仓操作-平仓备注-xxxxxxxxxx")
        def test_copy_close_order(self, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("发送复制下单平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
                new_user = var_manager.get_variable("new_user")

                request_data = {
                    "id": cloudMaster_id,
                    "flag": 0,
                    "intervalTime": 0,
                    "num": "",
                    "closeType": 0,
                    "remark": "xxxxxxxxxx",
                    "cloudTraderId": [cloudTrader_traderList_4],
                    "symbol": new_user['symbol'],
                    "type": 0
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

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
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
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.create_time"
                )

            with allure.step("执行复制平仓数据校验-没有订单"):
                assert len(db_data) != 2, "数据库中存在2个处理的平仓订单，不符合预期"

        @allure.title("云策略-复制下单平仓操作-订单备注-ceshipingcangbeizhu")
        def test_copy_close_order2(self, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("发送复制下单平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
                new_user = var_manager.get_variable("new_user")

                request_data = {
                    "id": cloudMaster_id,
                    "flag": 0,
                    "intervalTime": 0,
                    "num": "",
                    "closeType": 0,
                    "remark": "ceshipingcangbeizhu",
                    "cloudTraderId": [cloudTrader_traderList_4],
                    "symbol": new_user['symbol'],
                    "type": 0
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

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
        def test_copy_verify_close_db2(self, var_manager, db_transaction):
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
                db_data = self.wait_for_database_record_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )

            with allure.step("执行复制平仓数据校验-2个订单"):
                assert len(db_data) == 2, "数据库中没有2个处理的平仓订单，不符合预期"

            time.sleep(30)


# ------------------------------------
# 大模块6：云策略复制下单-平仓的全平策略功能校验
# ------------------------------------
@allure.feature("云策略复制下单-平仓的功能校验（多场景汇总）")
# @pytest.mark.skipif(True, reason=SKIP_REASON)
@pytest.mark.retry(n=3, delay=5)
class TestCloudClose:
    @allure.story("场景9：平仓的功能校验-全平策略")
    @allure.description("""
    ### 测试说明
    - 前置条件：有云策略和云跟单
      1. 进行开仓，手数范围0.1-1，总订单数量2
      2. 平仓-换个云策略进行平仓-全平策略
      3. 校验数据库是否有平仓订单-应该没有
      4. 平仓-换个云策略进行平仓-平仓1个
      5. 校验订单数据是否正确
      6. 平仓-云策略进行平仓-平仓1个
      7. 校验订单数据是否正确
    - 预期结果：平仓的功能校验-全平策略功能正确
    """)
    class TestMasOrderSend9(APITestBase):
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
                    "totalNum": "2",
                    "totalSzie": "",
                    "remark": "ceshipingcangbeizhu"
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

        @allure.title("云策略-复制下单平仓操作-全平策略")
        def test_copy_close_order2(self, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("发送复制下单平仓请求"):
                cloudMaster_id_hand = var_manager.get_variable("cloudMaster_id_hand")
                cloudTrader_traderList_handid = var_manager.get_variable("cloudTrader_traderList_handid")

                request_data = {
                    "flag": 1,
                    "id": cloudMaster_id_hand,
                    "cloudTraderId": [cloudTrader_traderList_handid]
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

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
        def test_copy_verify_close_db2(self, var_manager, db_transaction):
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
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.create_time"
                )

            with allure.step("执行复制平仓数据校验-没有订单"):
                assert len(db_data) != 2, "数据库中存在2个处理的平仓订单，不符合预期"

        @allure.title("云策略-复制下单平仓操作-平仓1个")
        def test_copy_close_order(self, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("发送复制下单平仓请求"):
                cloudMaster_id_hand = var_manager.get_variable("cloudMaster_id_hand")
                cloudTrader_traderList_handid = var_manager.get_variable("cloudTrader_traderList_handid")
                new_user = var_manager.get_variable("new_user")

                request_data = {
                    "id": cloudMaster_id_hand,
                    "flag": 0,
                    "intervalTime": 0,
                    "num": "1",
                    "closeType": 0,
                    "remark": "",
                    "cloudTraderId": [cloudTrader_traderList_handid],
                    "symbol": new_user['symbol'],
                    "type": 0
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

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
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
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.create_time"
                )

            with allure.step("执行复制平仓数据校验-有订单"):
                assert len(db_data) == 1, "数据库中没有1个处理的平仓订单，不符合预期"

        @allure.title("云策略-复制下单平仓操作-平仓1个")
        def test_copy_close_order3(self, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("发送复制下单平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
                new_user = var_manager.get_variable("new_user")

                request_data = {
                    "id": cloudMaster_id,
                    "flag": 0,
                    "intervalTime": 0,
                    "num": "",
                    "closeType": 0,
                    "remark": "ceshipingcangbeizhu",
                    "cloudTraderId": [cloudTrader_traderList_4],
                    "symbol": new_user['symbol'],
                    "type": 0
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

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
        def test_copy_verify_close_db3(self, var_manager, db_transaction):
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
                db_data = self.wait_for_database_record_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )

            with allure.step("执行复制平仓数据校验-2个订单"):
                assert len(db_data) == 2, "数据库中没有2个处理的平仓订单，不符合预期"

            time.sleep(30)

    @allure.story("场景10：平仓的功能校验-全平订单")
    @allure.description("""
    ### 测试说明
    - 前置条件：有云策略和云跟单
      1. 进行开仓，手数范围0.1-1，总订单数量2
      2. 平仓-换个云策略进行平仓-全平策略
      3. 校验数据库是否有平仓订单-应该没有
      4. 平仓-换个云策略进行平仓-平仓1个
      5. 校验订单数据是否正确
      6. 平仓-云策略进行平仓-全平订单
      7. 校验订单数据是否正确
    - 预期结果：平仓的功能校验-全平订单功能正确
    """)
    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    class TestMasOrderSend10(APITestBase):
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
                    "totalNum": "2",
                    "totalSzie": "",
                    "remark": "ceshipingcangbeizhu"
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

        @allure.title("云策略-复制下单平仓操作-全平策略")
        def test_copy_close_order2(self, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("发送复制下单平仓请求"):
                cloudMaster_id_hand = var_manager.get_variable("cloudMaster_id_hand")
                cloudTrader_traderList_handid = var_manager.get_variable("cloudTrader_traderList_handid")

                request_data = {
                    "flag": 1,
                    "id": cloudMaster_id_hand,
                    "cloudTraderId": [cloudTrader_traderList_handid]
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

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
        def test_copy_verify_close_db2(self, var_manager, db_transaction):
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
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.create_time"
                )

            with allure.step("执行复制平仓数据校验-没有订单"):
                assert len(db_data) != 2, "数据库中存在2个处理的平仓订单，不符合预期"

        @allure.title("云策略-复制下单平仓操作-平仓1个")
        def test_copy_close_order(self, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("发送复制下单平仓请求"):
                cloudMaster_id_hand = var_manager.get_variable("cloudMaster_id_hand")
                cloudTrader_traderList_handid = var_manager.get_variable("cloudTrader_traderList_handid")
                new_user = var_manager.get_variable("new_user")

                request_data = {
                    "id": cloudMaster_id_hand,
                    "flag": 0,
                    "intervalTime": 0,
                    "num": "1",
                    "closeType": 0,
                    "remark": "",
                    "cloudTraderId": [cloudTrader_traderList_handid],
                    "symbol": new_user['symbol'],
                    "type": 0
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

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
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
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.create_time"
                )

            with allure.step("执行复制平仓数据校验-有订单"):
                assert len(db_data) == 1, "数据库中没有1个处理的平仓订单，不符合预期"

        @allure.title("云策略-复制下单平仓操作-全平订单")
        def test_copy_close_order3(self, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("发送复制下单平仓请求"):
                cloudMaster_id_hand = var_manager.get_variable("cloudMaster_id_hand")
                cloudTrader_traderList_handid = var_manager.get_variable("cloudTrader_traderList_handid")

                request_data = {
                    "isCloseAll": 1,
                    "intervalTime": 0,
                    "id": cloudMaster_id_hand,
                    "cloudTraderId": [cloudTrader_traderList_handid]
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

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
        def test_copy_verify_close_db3(self, var_manager, db_transaction):
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
                db_data = self.wait_for_database_record_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )

            with allure.step("执行复制平仓数据校验-2个订单"):
                assert len(db_data) == 2, "数据库中没有2个处理的平仓订单，不符合预期"

            time.sleep(30)

    @allure.story("场景11：平仓的功能校验-全平订单")
    @allure.description("""
        ### 测试说明
        - 前置条件：有云策略和云跟单
          1. 进行开仓，手数范围0.1-1，总订单数量2
          2. 平仓-全平策略
          3. 校验订单数据是否正确
        - 预期结果：平仓的功能校验-全平订单功能正确
        """)
    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    class TestMasOrderSend11(APITestBase):
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
                    "totalNum": "2",
                    "totalSzie": "",
                    "remark": "ceshipingcangbeizhu"
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

        @allure.title("云策略-复制下单平仓操作-全平策略")
        def test_copy_close_order(self, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("发送复制下单平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")

                request_data = {
                    "flag": 1,
                    "id": cloudMaster_id,
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

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
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
                db_data = self.wait_for_database_record_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )

            with allure.step("执行复制平仓数据校验-2个订单"):
                assert len(db_data) == 2, "数据库中没有2个处理的平仓订单，不符合预期"

            time.sleep(30)
