# self_developed_model/tests/test_云策略_ordersend.py
import allure
import logging
import pytest
import time
from self_developed_model.conftest import var_manager
from self_developed_model.commons.api_base import *
from self_developed_model.commons.redis_utils import *

logger = logging.getLogger(__name__)
SKIP_REASON = "该用例暂时跳过"


@allure.feature("云策略-策略账号交易下单-漏单场景")
class TestcloudTrader_openandlevel:
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
                        "remark": "changjing4"
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

            @pytest.mark.retry(n=3, delay=5)
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
                    params = ('1', cloudTrader_user_accounts_4, "changjing4", cloudTrader_vps_ids_3)

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
                    params = ('1', cloudTrader_user_accounts_4, "changjing4", cloudTrader_vps_ids_3)

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
