import allure
import logging
import pytest
import time
import re
from lingkuan_1027.conftest import var_manager
from lingkuan_1027.commons.api_base import *
import requests
from lingkuan_1027.commons.jsonpath_utils import JsonPathUtils

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


# ------------------------------------
# 大模块1：云策略复制下单-平仓的停止功能校验
# ------------------------------------
@allure.feature("云策略复制下单-平仓的功能校验")
# @pytest.mark.skipif(True, reason=SKIP_REASON)
class TestCloudCoreFunctionality:
    @allure.story("场景1：平仓的停止功能校验")
    @allure.description("""
    ### 测试说明
    - 前置条件：有云策略和云跟单
      1. 进行开仓，手数范围0.1-1，总订单5
      2. 进行平仓，校验币种，币种错误应该没有开仓订单
      3. 进行平仓，点击停止
      4. 校验平仓的订单数，应该不等于开仓总订单
      5. 进行平仓
    - 预期结果：平仓的停止功能正确
    """)
    @pytest.mark.usefixtures("class_random_str")
    class TestMasOrderSend1(APITestBase):
        @allure.title("云策略列表-修改云跟单")
        def test_update_cloudtrader(self, class_random_str, logged_session, var_manager):
            """执行云策略复制下单操作并验证请求结果"""
            with allure.step("1.发送修改云跟单请求"):
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

            with allure.step("2.验证复制下单响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制下单响应msg字段应为success"
                )

        @allure.title("云策略-复制下单操作")
        def test_copy_place_order(self, class_random_str, logged_session, var_manager):
            """执行云策略复制下单操作并验证请求结果"""
            with allure.step("1.发送复制下单请求"):
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
                    "totalNum": "5",
                    "totalSzie": "",
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
                    "复制下单响应msg字段应为success"
                )

        @allure.title("云策略-复制下单平仓操作-币种错误")
        def test_copy_close_symbol(self, class_random_str, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("1.发送复制下单平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")

                request_data = {
                    "id": cloudMaster_id,
                    "flag": 0,
                    "intervalTime": 0,
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
            with allure.step("2.验证复制平仓响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制平仓响应msg字段应为success"
                )

        @pytest.mark.retry(n=0, delay=0)
        @allure.title("数据库校验-复制下单平仓数据-数据校验")
        def test_copy_verify_close_dbsymbol(self, class_random_str, var_manager, db_transaction):
            """验证复制下单平仓后数据库中的订单数据正确性"""
            with allure.step("查询复制平仓订单数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
                cloudTrader_vps_ids_3 = var_manager.get_variable("cloudTrader_vps_ids_3")

                sql = """
                            SELECT 
                                fod.comment,
                                fod.size,
                                fod.close_no,
                                fod.magical,
                                fod.open_price,
                                fod.symbol,
                                fod.order_no,
                                fod.comment,
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
                                AND fod.comment = %s
                                AND fod.trader_id = %s
                        """
                params = ('1', cloudTrader_user_accounts_4, class_random_str, cloudTrader_vps_ids_3)

                # 轮询等待数据库记录
                db_data = self.wait_for_database_no_record(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="foi.create_time"
                )

            with allure.step("执行复制平仓数据校验-订单不等于开仓总订单数量"):
                self.verify_data(
                    actual_value=len(db_data),
                    expected_value=0,
                    op=CompareOp.EQ,
                    message=f"平仓失败，应该没有平仓订单",
                    attachment_name="订单数量详情"
                )
                logging.info(f"平仓失败，应该没有平仓订单，结果有{len(db_data)}个订单")

        @allure.title("云策略-复制下单平仓操作")
        def test_copy_close_order(self, class_random_str, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("1.发送复制下单平仓请求"):
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

            with allure.step("2.验证复制平仓响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制平仓响应msg字段应为success"
                )

        @allure.title("云策略-复制下单平仓-停止操作")
        def test_copy_close_cloudStopOrder(self, class_random_str, logged_session, var_manager):
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

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
        def test_copy_verify_close_db(self, class_random_str, var_manager, db_transaction):
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
                        fod.comment,
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
                        AND fod.comment = %s
                        AND fod.trader_id = %s
                """
                params = ('1', cloudTrader_user_accounts_4, class_random_str, cloudTrader_vps_ids_3)

                # 轮询等待数据库记录
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )

            with allure.step("执行复制平仓数据校验-订单不等于开仓总订单数量"):
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

        @allure.title("云策略-复制下单平仓操作")
        def test_copy_close_order2(self, class_random_str, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("1.发送复制下单平仓请求"):
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

            with allure.step("2.验证复制平仓响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制平仓响应msg字段应为success"
                )


# ------------------------------------
# 大模块2：云策略复制下单-平仓的订单方向验证
# ------------------------------------
@allure.feature("云策略复制下单-平仓的功能校验")
# @pytest.mark.skipif(True, reason=SKIP_REASON)
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
    @pytest.mark.usefixtures("class_random_str")
    class TestMasOrderSend2(APITestBase):
        @allure.title("云策略-复制下单操作")
        def test_copy_place_order(self, class_random_str, logged_session, var_manager):
            """执行云策略复制下单操作并验证请求结果"""
            with allure.step("1.发送复制下单请求"):
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
                    "复制下单响应msg字段应为success"
                )

        @allure.title("云策略-复制下单平仓操作-sell-平仓失败")
        def test_copy_close_order(self, class_random_str, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("1.发送复制下单平仓请求"):
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

            with allure.step("2.验证复制平仓响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制平仓响应msg字段应为success"
                )

        @pytest.mark.retry(n=0, delay=0)
        @allure.title("数据库校验-复制下单平仓数据-数据校验")
        def test_copy_verify_close_db(self, class_random_str, var_manager, db_transaction):
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
                           fod.comment,
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
                           AND fod.comment = %s
                           AND fod.trader_id = %s
                           AND foi.total_orders = %s
                   """
                params = ('1', cloudTrader_user_accounts_4, class_random_str, cloudTrader_vps_ids_3, "3")

                # 轮询等待数据库记录
                db_data = self.wait_for_database_no_record(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="foi.create_time"
                )

            with allure.step("执行复制平仓数据校验-没有订单"):
                self.verify_data(
                    actual_value=len(db_data),
                    expected_value=0,
                    op=CompareOp.EQ,
                    message=f"平仓失败，应该没有平仓订单",
                    attachment_name="订单数量详情"
                )
                logging.info(f"平仓失败，应该没有平仓订单，结果有{len(db_data)}个订单")

        @allure.title("云策略-复制下单平仓操作-buy-平仓成功")
        def test_copy_close_order2(self, class_random_str, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("1.发送复制下单平仓请求"):
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

            with allure.step("2.验证复制平仓响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制平仓响应msg字段应为success"
                )

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
        def test_copy_verify_close_db2(self, class_random_str, var_manager, db_transaction):
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
                                   fod.comment,
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
                                   AND fod.comment = %s
                                   AND fod.trader_id = %s
                           """
                params = ('1', cloudTrader_user_accounts_4, class_random_str, cloudTrader_vps_ids_3)

                # 轮询等待数据库记录
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )

            with allure.step("执行复制平仓数据校验-有订单"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行复制平仓校验")

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

    # @pytest.mark.skipif(reason=SKIP_REASON)
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
    @pytest.mark.usefixtures("class_random_str")
    class TestMasOrderSend3(APITestBase):
        @allure.title("云策略-复制下单操作")
        def test_copy_place_order(self, class_random_str, logged_session, var_manager):
            """执行云策略复制下单操作并验证请求结果"""
            with allure.step("1.发送复制下单请求"):
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
                    "复制下单响应msg字段应为success"
                )

        @allure.title("云策略-复制下单平仓操作-sell-平仓失败")
        def test_copy_close_order(self, class_random_str, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("1.发送复制下单平仓请求"):
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

            with allure.step("2.验证复制平仓响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制平仓响应msg字段应为success"
                )

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
        def test_copy_verify_close_db(self, class_random_str, var_manager, db_transaction):
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
                               fod.comment,
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
                               AND fod.comment = %s
                               AND fod.trader_id = %s
                               AND foi.total_orders = %s
                       """
                params = ('1', cloudTrader_user_accounts_4, class_random_str, cloudTrader_vps_ids_3, "4")

                # 轮询等待数据库记录
                db_data = self.wait_for_database_no_record(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="foi.create_time"
                )

            with allure.step("执行复制平仓数据校验-没有订单"):
                self.verify_data(
                    actual_value=len(db_data),
                    expected_value=0,
                    op=CompareOp.EQ,
                    message=f"平仓失败，应该没有平仓订单",
                    attachment_name="订单数量详情"
                )
                logging.info(f"平仓失败，应该没有平仓订单，结果有{len(db_data)}个订单")

        @allure.title("云策略-复制下单平仓操作-buy sell-平仓成功")
        def test_copy_close_order2(self, class_random_str, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("1.发送复制下单平仓请求"):
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

            with allure.step("2.验证复制平仓响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制平仓响应msg字段应为success"
                )

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
        def test_copy_verify_close_db2(self, class_random_str, var_manager, db_transaction):
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
                                       fod.comment,
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
                                       AND fod.comment = %s
                                       AND fod.trader_id = %s
                               """
                params = ('1', cloudTrader_user_accounts_4, class_random_str, cloudTrader_vps_ids_3)

                # 轮询等待数据库记录
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )

            with allure.step("执行复制平仓数据校验-有订单"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行复制平仓校验")

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


# ------------------------------------
# 大模块3：云策略复制下单-平仓的订单数量功能校验
# ------------------------------------
@allure.feature("云策略复制下单-平仓的功能校验")
# @pytest.mark.skipif(True, reason=SKIP_REASON)
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
    @pytest.mark.usefixtures("class_random_str")
    class TestMasOrderSend4(APITestBase):
        @allure.title("云策略-复制下单操作")
        def test_copy_place_order(self, class_random_str, logged_session, var_manager):
            """执行云策略复制下单操作并验证请求结果"""
            with allure.step("1.发送复制下单请求"):
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
                    "复制下单响应msg字段应为success"
                )

        @allure.title("云策略-复制下单平仓操作-平仓两个订单")
        def test_copy_close_order(self, class_random_str, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("1.发送复制下单平仓请求"):
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

            with allure.step("2.验证复制平仓响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制平仓响应msg字段应为success"
                )

        @pytest.mark.retry(n=0, delay=0)
        @allure.title("数据库校验-复制下单平仓数据-数据校验")
        def test_copy_verify_close_db(self, class_random_str, var_manager, db_transaction):
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
                           fod.comment,
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
                           AND fod.comment = %s
                           AND fod.trader_id = %s
                   """
                params = ('1', cloudTrader_user_accounts_4, class_random_str, cloudTrader_vps_ids_3)

                # 轮询等待数据库记录
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.create_time"
                )

            with allure.step("执行复制平仓数据校验-有两个订单"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行复制下单校验")

                with allure.step("验证订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=2,
                        op=CompareOp.EQ,
                        message=f"平仓的订单数量应该是2",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"平仓的订单数量应该是2，结果有{len(db_data)}个订单")

        @allure.title("云策略-复制下单平仓操作-再次平仓两个订单")
        def test_copy_close_order2(self, class_random_str, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("1.发送复制下单平仓请求"):
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

            with allure.step("2.验证复制平仓响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制平仓响应msg字段应为success"
                )

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
        def test_copy_verify_close_db2(self, class_random_str, var_manager, db_transaction):
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
                               fod.comment,
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
                               AND fod.comment = %s
                               AND fod.trader_id = %s
                       """
                params = ('1', cloudTrader_user_accounts_4, class_random_str, cloudTrader_vps_ids_3)

                # 轮询等待数据库记录
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )

            with allure.step("执行复制平仓数据校验-有四个订单"):
                self.verify_data(
                    actual_value=len(db_data),
                    expected_value=4,
                    op=CompareOp.EQ,
                    message=f"正常平仓，应该有4个平仓订单",
                    attachment_name="订单数量详情"
                )
                logging.info(f"正常平仓，应该有4个平仓订单，结果有{len(db_data)}个订单")


# ------------------------------------
# 大模块4：云策略复制下单-平仓的订单类型功能校验
# ------------------------------------
@allure.feature("云策略复制下单-平仓的功能校验")
# @pytest.mark.skipif(True, reason=SKIP_REASON)
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
    @pytest.mark.usefixtures("class_random_str")
    class TestMasOrderSend5(APITestBase):
        @allure.title("云策略-复制下单操作")
        def test_copy_place_order(self, class_random_str, logged_session, var_manager):
            """执行云策略复制下单操作并验证请求结果"""
            with allure.step("1.发送复制下单请求"):
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
                    "复制下单响应msg字段应为success"
                )

        @allure.title("云策略-复制下单平仓操作-订单类型-外部订单")
        def test_copy_close_order(self, class_random_str, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("1.发送复制下单平仓请求"):
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

            with allure.step("2.验证复制平仓响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制平仓响应msg字段应为success"
                )

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
        def test_copy_verify_close_db(self, class_random_str, var_manager, db_transaction):
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
                           fod.comment,
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
                           AND fod.comment = %s
                           AND fod.trader_id = %s
                   """
                params = ('1', cloudTrader_user_accounts_4, class_random_str, cloudTrader_vps_ids_3)

                # 轮询等待数据库记录
                db_data = self.wait_for_database_no_record(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="foi.create_time"
                )

            with allure.step("执行复制平仓数据校验-没有订单"):
                self.verify_data(
                    actual_value=len(db_data),
                    expected_value=0,
                    op=CompareOp.EQ,
                    message=f"平仓失败，应该没有平仓订单",
                    attachment_name="订单数量详情"
                )
                logging.info(f"平仓失败，应该没有平仓订单，结果有{len(db_data)}个订单")

        @allure.title("云策略-复制下单平仓操作-订单类型-内部订单")
        def test_copy_close_order2(self, class_random_str, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("1.发送复制下单平仓请求"):
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

            with allure.step("2.验证复制平仓响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制平仓响应msg字段应为success"
                )

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
        def test_copy_verify_close_db2(self, class_random_str, var_manager, db_transaction):
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
                               fod.comment,
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
                               AND fod.comment = %s
                               AND fod.trader_id = %s
                       """
                params = ('1', cloudTrader_user_accounts_4, class_random_str, cloudTrader_vps_ids_3)

                # 轮询等待数据库记录
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )

            with allure.step("执行复制平仓数据校验-2个订单"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行复制下单校验")

                with allure.step("验证订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=2,
                        op=CompareOp.EQ,
                        message=f"平仓的订单数量应该是2",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"平仓的订单数量应该是2，结果有{len(db_data)}个订单")

            # time.sleep(30)

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
    @pytest.mark.usefixtures("class_random_str")
    @pytest.mark.skipif(True, reason=SKIP_REASON)
    class TestMasOrderSend6(APITestBase):
        @allure.title("登录MT4账号获取token")
        def test_mt4_login(self, class_random_str, var_manager):
            global token_mt4, headers
            max_retries = 5  # 最大重试次数
            retry_interval = 5  # 重试间隔（秒）
            token_mt4 = None

            # 用于验证token格式的正则表达式（UUID格式）
            uuid_pattern = re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')

            for attempt in range(max_retries):
                try:
                    url = "https://mt4.mtapi.io/Connect?user=300162&password=Test123456&host=47.238.99.66&port=443&connectTimeoutSeconds=30"

                    headers = {
                        'Authorization': 'e5f9f574-fd0a-42bd-904b-3a7a088de27e',
                        'x-sign': '417B110F1E71BD2CFE96366E67849B0B',
                        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
                        'Content-Type': 'application/json',
                        'Accept': '*/*',
                        'Host': 'mt4.mtapi.io',
                        'Connection': 'keep-alive'
                    }

                    response = requests.request("GET", url, headers=headers, data={})
                    response_text = response.text.strip()  # 去除可能的空白字符

                    logging.info(f"第{attempt + 1}次登录尝试 - 响应内容: {response_text}")

                    # 验证响应是否为有效的UUID格式token
                    if uuid_pattern.match(response_text):
                        token_mt4 = response_text
                        logging.info(f"第{attempt + 1}次尝试成功 - 获取到token: {token_mt4}")
                        break
                    else:
                        logging.warning(f"第{attempt + 1}次尝试失败 - 无效的token格式: {response_text}")

                except Exception as e:
                    logging.error(f"第{attempt + 1}次尝试发生异常: {str(e)}")

                # 如果不是最后一次尝试，等待后重试
                if attempt < max_retries - 1:
                    logging.info(f"将在{retry_interval}秒后进行第{attempt + 2}次重试...")
                    time.sleep(retry_interval)

            # 最终验证结果
            if not token_mt4 or not uuid_pattern.match(token_mt4):
                logging.error(f"经过{max_retries}次尝试后，MT4登录仍失败")
                assert False, "MT4登录失败"
            else:
                print(f"登录MT4账号获取token: {token_mt4}")
                logging.info(f"登录MT4账号获取token: {token_mt4}")

        @allure.title("MT4平台开仓操作")
        def test_mt4_open(self, class_random_str, var_manager):
            url = f"https://mt4.mtapi.io/OrderSend?id={token_mt4}&symbol=XAUUSD&operation=Buy&volume=1&placedType=Client&price=0.00"

            payload = ""
            self.response = requests.request("GET", url, headers=headers, data=payload)
            self.json_utils = JsonPathUtils()
            self.response = self.response.json()
            ticket = self.json_utils.extract(self.response, "$.ticket")
            print(ticket)

        @allure.title("云策略-复制下单平仓操作-订单类型-内部订单")
        def test_copy_close_order(self, class_random_str, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("1.发送复制下单平仓请求"):
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

            with allure.step("2.验证复制平仓响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制平仓响应msg字段应为success"
                )

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
        def test_copy_verify_close_db(self, class_random_str, var_manager, db_transaction):
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
                           fod.comment,
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
                db_data = self.wait_for_database_no_record(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="foi.create_time"
                )

            with allure.step("执行复制平仓数据校验-没有订单"):
                self.verify_data(
                    actual_value=len(db_data),
                    expected_value=0,
                    op=CompareOp.EQ,
                    message=f"平仓失败，应该没有平仓订单",
                    attachment_name="订单数量详情"
                )
                logging.info(f"平仓失败，应该没有平仓订单，结果有{len(db_data)}个订单")

        @allure.title("云策略-复制下单平仓操作-订单类型-外部订单")
        def test_copy_close_order2(self, class_random_str, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("1.发送复制下单平仓请求"):
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

            with allure.step("2.验证复制平仓响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制平仓响应msg字段应为success"
                )

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
        def test_copy_verify_close_db2(self, class_random_str, var_manager, db_transaction):
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
                               fod.comment,
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

            with allure.step("执行复制平仓数据校验-有订单"):
                self.verify_data(
                    actual_value=len(db_data),
                    expected_value=1,
                    op=CompareOp.EQ,
                    message=f"平仓的订单数量应该是1",
                    attachment_name="订单数量详情"
                )
                logging.info(f"平仓的订单数量应该是1，结果有{len(db_data)}个订单")

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
    @pytest.mark.usefixtures("class_random_str")
    class TestMasOrderSend7(APITestBase):
        @allure.title("云策略-复制下单操作")
        def test_copy_place_order(self, class_random_str, logged_session, var_manager):
            """执行云策略复制下单操作并验证请求结果"""
            with allure.step("1.发送复制下单请求"):
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
                    "复制下单响应msg字段应为success"
                )

        @allure.title("云策略-复制下单平仓操作-订单类型-外部订单")
        def test_copy_close_order(self, class_random_str, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("1.发送复制下单平仓请求"):
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

            with allure.step("2.验证复制平仓响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制平仓响应msg字段应为success"
                )

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
        def test_copy_verify_close_db(self, class_random_str, var_manager, db_transaction):
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
                           fod.comment,
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
                           AND fod.comment = %s
                           AND fod.trader_id = %s
                   """
                params = ('1', cloudTrader_user_accounts_4, class_random_str, cloudTrader_vps_ids_3)

                # 轮询等待数据库记录
                db_data = self.wait_for_database_no_record(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="foi.create_time"
                )

            with allure.step("执行复制平仓数据校验-没有订单"):
                self.verify_data(
                    actual_value=len(db_data),
                    expected_value=0,
                    op=CompareOp.EQ,
                    message=f"平仓失败，应该没有平仓订单",
                    attachment_name="订单数量详情"
                )
                logging.info(f"平仓失败，应该没有平仓订单，结果有{len(db_data)}个订单")

        @allure.title("云策略-复制下单平仓操作-订单类型-全部订单")
        def test_copy_close_order2(self, class_random_str, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("1.发送复制下单平仓请求"):
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

            with allure.step("2.验证复制平仓响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制平仓响应msg字段应为success"
                )

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
        def test_copy_verify_close_db2(self, class_random_str, var_manager, db_transaction):
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
                               fod.comment,
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
                               AND fod.comment = %s
                               AND fod.trader_id = %s
                       """
                params = ('1', cloudTrader_user_accounts_4, class_random_str, cloudTrader_vps_ids_3)

                # 轮询等待数据库记录
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )

            with allure.step("执行复制平仓数据校验-2个订单"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行复制下单校验")

                with allure.step("验证订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=2,
                        op=CompareOp.EQ,
                        message=f"平仓的订单数量应该是2",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"平仓的订单数量应该是2，结果有{len(db_data)}个订单")


# ------------------------------------
# 大模块5：云策略复制下单-平仓的订单备注功能校验
# ------------------------------------
@allure.feature("云策略复制下单-平仓的功能校验")
# @pytest.mark.skipif(True, reason=SKIP_REASON)
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
    @pytest.mark.usefixtures("class_random_str")
    class TestMasOrderSend8(APITestBase):
        @allure.title("云策略-复制下单操作")
        def test_copy_place_order(self, class_random_str, logged_session, var_manager):
            """执行云策略复制下单操作并验证请求结果"""
            with allure.step("1.发送复制下单请求"):
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

            with allure.step("2.验证复制下单响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制下单响应msg字段应为success"
                )

        @allure.title("云策略-复制下单平仓操作-平仓备注-xxxxxxxxxx")
        def test_copy_close_order(self, class_random_str, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("1.发送复制下单平仓请求"):
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

            with allure.step("2.验证复制平仓响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制平仓响应msg字段应为success"
                )

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
        def test_copy_verify_close_db(self, class_random_str, var_manager, db_transaction):
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
                           fod.comment,
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
                           AND fod.comment = %s
                           AND fod.trader_id = %s
                   """
                params = ('1', cloudTrader_user_accounts_4, "ceshipingcangbeizhu", cloudTrader_vps_ids_3)

                # 轮询等待数据库记录
                db_data = self.wait_for_database_no_record(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="foi.create_time"
                )

            with allure.step("执行复制平仓数据校验-没有订单"):
                self.verify_data(
                    actual_value=len(db_data),
                    expected_value=0,
                    op=CompareOp.EQ,
                    message=f"平仓失败，应该没有平仓订单",
                    attachment_name="订单数量详情"
                )
                logging.info(f"平仓失败，应该没有平仓订单，结果有{len(db_data)}个订单")

        @allure.title("云策略-复制下单平仓操作-订单备注-ceshipingcangbeizhu")
        def test_copy_close_order2(self, class_random_str, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("1.发送复制下单平仓请求"):
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

            with allure.step("2.验证复制平仓响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制平仓响应msg字段应为success"
                )

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
        def test_copy_verify_close_db2(self, class_random_str, var_manager, db_transaction):
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
                               fod.comment,
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
                               AND fod.comment = %s
                               AND fod.trader_id = %s
                       """
                params = ('1', cloudTrader_user_accounts_4, "ceshipingcangbeizhu", cloudTrader_vps_ids_3)

                # 轮询等待数据库记录
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )

            with allure.step("执行复制平仓数据校验-2个订单"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行复制下单校验")

                with allure.step("验证订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=2,
                        op=CompareOp.EQ,
                        message=f"平仓的订单数量应该是2",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"平仓的订单数量应该是2，结果有{len(db_data)}个订单")


# ------------------------------------
# 大模块6：云策略复制下单-平仓的全平策略功能校验
# ------------------------------------
@allure.feature("云策略复制下单-平仓的功能校验")
# @pytest.mark.skipif(True, reason=SKIP_REASON)
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
    @pytest.mark.usefixtures("class_random_str")
    class TestMasOrderSend9(APITestBase):
        @allure.title("云策略-复制下单操作")
        def test_copy_place_order(self, class_random_str, logged_session, var_manager):
            """执行云策略复制下单操作并验证请求结果"""
            with allure.step("1.发送复制下单请求"):
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
                    "复制下单响应msg字段应为success"
                )

        @allure.title("云策略-复制下单平仓操作-全平策略")
        def test_copy_close_order2(self, class_random_str, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("1.发送复制下单平仓请求"):
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

            with allure.step("2.验证复制平仓响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制平仓响应msg字段应为success"
                )

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
        def test_copy_verify_close_db2(self, class_random_str, var_manager, db_transaction):
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
                                   fod.comment,
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
                                   AND fod.comment = %s
                                   AND fod.trader_id = %s
                           """
                params = ('1', cloudTrader_user_accounts_4, class_random_str, cloudTrader_vps_ids_3)

                # 轮询等待数据库记录
                db_data = self.wait_for_database_no_record(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="foi.create_time"
                )

            with allure.step("执行复制平仓数据校验-没有订单"):
                self.verify_data(
                    actual_value=len(db_data),
                    expected_value=0,
                    op=CompareOp.EQ,
                    message=f"平仓失败，应该没有平仓订单",
                    attachment_name="订单数量详情"
                )
                logging.info(f"平仓失败，应该没有平仓订单，结果有{len(db_data)}个订单")

        @allure.title("云策略-复制下单平仓操作-平仓1个")
        def test_copy_close_order(self, class_random_str, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("1.发送复制下单平仓请求"):
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

            with allure.step("2.验证复制平仓响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制平仓响应msg字段应为success"
                )

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
        def test_copy_verify_close_db(self, class_random_str, var_manager, db_transaction):
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
                           fod.comment,
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
                           AND fod.comment = %s
                           AND fod.trader_id = %s
                   """
                params = ('1', cloudTrader_user_accounts_4, class_random_str, cloudTrader_vps_ids_3)

                # 轮询等待数据库记录
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.create_time"
                )

            with allure.step("执行复制平仓数据校验-有订单"):
                self.verify_data(
                    actual_value=len(db_data),
                    expected_value=1,
                    op=CompareOp.EQ,
                    message=f"平仓的订单数量应该是1",
                    attachment_name="订单数量详情"
                )
                logging.info(f"平仓的订单数量应该是1，结果有{len(db_data)}个订单")

        @allure.title("云策略-复制下单平仓操作-平仓1个")
        def test_copy_close_order3(self, class_random_str, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("1.发送复制下单平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
                new_user = var_manager.get_variable("new_user")

                request_data = {
                    "id": cloudMaster_id,
                    "flag": 0,
                    "intervalTime": 0,
                    "num": "",
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

            with allure.step("2.验证复制平仓响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制平仓响应msg字段应为success"
                )

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
        def test_copy_verify_close_db3(self, class_random_str, var_manager, db_transaction):
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
                               fod.comment,
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
                               AND fod.comment = %s
                               AND fod.trader_id = %s
                       """
                params = ('1', cloudTrader_user_accounts_4, class_random_str, cloudTrader_vps_ids_3)

                # 轮询等待数据库记录
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )

            with allure.step("执行复制平仓数据校验-2个订单"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行复制下单校验")

                with allure.step("验证订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=2,
                        op=CompareOp.EQ,
                        message=f"平仓的订单数量应该是2",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"平仓的订单数量应该是2，结果有{len(db_data)}个订单")

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
    @pytest.mark.usefixtures("class_random_str")
    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    class TestMasOrderSend10(APITestBase):
        @allure.title("云策略-复制下单操作")
        def test_copy_place_order(self, class_random_str, logged_session, var_manager):
            """执行云策略复制下单操作并验证请求结果"""
            with allure.step("1.发送复制下单请求"):
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
                    "复制下单响应msg字段应为success"
                )

        @allure.title("云策略-复制下单平仓操作-全平策略")
        def test_copy_close_order2(self, class_random_str, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("1.发送复制下单平仓请求"):
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

            with allure.step("2.验证复制平仓响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制平仓响应msg字段应为success"
                )

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
        def test_copy_verify_close_db2(self, class_random_str, var_manager, db_transaction):
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
                                       fod.comment,
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
                                       AND fod.comment = %s
                                       AND fod.trader_id = %s
                               """
                params = ('1', cloudTrader_user_accounts_4, class_random_str, cloudTrader_vps_ids_3)

                # 轮询等待数据库记录
                db_data = self.wait_for_database_no_record(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="foi.create_time"
                )

            with allure.step("执行复制平仓数据校验-没有订单"):
                self.verify_data(
                    actual_value=len(db_data),
                    expected_value=0,
                    op=CompareOp.EQ,
                    message=f"平仓失败，应该没有平仓订单",
                    attachment_name="订单数量详情"
                )
                logging.info(f"平仓失败，应该没有平仓订单，结果有{len(db_data)}个订单")

        @allure.title("云策略-复制下单平仓操作-平仓1个")
        def test_copy_close_order(self, class_random_str, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("1.发送复制下单平仓请求"):
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

            with allure.step("2.验证复制平仓响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制平仓响应msg字段应为success"
                )

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
        def test_copy_verify_close_db(self, class_random_str, var_manager, db_transaction):
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
                               fod.comment,
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
                               AND fod.comment = %s
                               AND fod.trader_id = %s
                       """
                params = ('1', cloudTrader_user_accounts_4, class_random_str, cloudTrader_vps_ids_3)

                # 轮询等待数据库记录
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.create_time"
                )

            with allure.step("执行复制平仓数据校验-有订单"):
                self.verify_data(
                    actual_value=len(db_data),
                    expected_value=1,
                    op=CompareOp.EQ,
                    message=f"平仓的订单数量应该是1",
                    attachment_name="订单数量详情"
                )
                logging.info(f"平仓的订单数量应该是1，结果有{len(db_data)}个订单")

        @allure.title("云策略-复制下单平仓操作-全平订单")
        def test_copy_close_order3(self, class_random_str, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("1.发送复制下单平仓请求"):
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

            with allure.step("2.验证复制平仓响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制平仓响应msg字段应为success"
                )

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
        def test_copy_verify_close_db3(self, class_random_str, var_manager, db_transaction):
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
                           fod.comment,
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
                           AND fod.comment = %s
                           AND fod.trader_id = %s
                           """
                params = ('1', cloudTrader_user_accounts_4, class_random_str, cloudTrader_vps_ids_3)

                # 轮询等待数据库记录
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )

            with allure.step("执行复制平仓数据校验-2个订单"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行复制下单校验")

                with allure.step("验证订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=2,
                        op=CompareOp.EQ,
                        message=f"平仓的订单数量应该是2",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"平仓的订单数量应该是2，结果有{len(db_data)}个订单")

    @allure.story("场景11：平仓的功能校验-全平订单")
    @allure.description("""
    ### 测试说明
    - 前置条件：有云策略和云跟单
      1. 进行开仓，手数范围0.1-1，总订单数量2
      2. 平仓-全平策略
      3. 校验订单数据是否正确
    - 预期结果：平仓的功能校验-全平订单功能正确
    """)
    @pytest.mark.usefixtures("class_random_str")
    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    class TestMasOrderSend11(APITestBase):
        @allure.title("云策略-复制下单操作")
        def test_copy_place_order(self, class_random_str, logged_session, var_manager):
            """执行云策略复制下单操作并验证请求结果"""
            with allure.step("1.发送复制下单请求"):
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
                    "复制下单响应msg字段应为success"
                )

        @allure.title("云策略-复制下单平仓操作-全平策略")
        def test_copy_close_order(self, class_random_str, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("1.发送复制下单平仓请求"):
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

            with allure.step("2.验证复制平仓响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制平仓响应msg字段应为success"
                )

        @allure.title("数据库校验-复制下单平仓数据-数据校验")
        def test_copy_verify_close_db(self, class_random_str, var_manager, db_transaction):
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
                                   fod.comment,
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
                                   AND fod.comment = %s
                                   AND fod.trader_id = %s
                           """
                params = ('1', cloudTrader_user_accounts_4, class_random_str, cloudTrader_vps_ids_3)

                # 轮询等待数据库记录
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )

            with allure.step("执行复制平仓数据校验-2个订单"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行复制下单校验")

                with allure.step("验证订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=2,
                        op=CompareOp.EQ,
                        message=f"平仓的订单数量应该是2",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"平仓的订单数量应该是2，结果有{len(db_data)}个订单")
