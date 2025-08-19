import allure
import logging
import pytest
import time
import math
from lingkuan_818.VAR.VAR import *
from lingkuan_818.conftest import var_manager
from lingkuan_818.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"


# @pytest.mark.skipif(condition=True, reason=SKIP_REASON)
@allure.feature("云策略下单功能测试")
@allure.description("""
### 测试说明
- 前置条件：有云策略和云跟单
  1. 进行开仓，手数范围0.1-1，总订单4，总手数无
  2. 进行平仓，点击停止
  3. 校验平仓的订单数，应该不等于开仓总订单
  4. 进行平仓
- 预期结果：平仓的停止功能正确
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

        with allure.step("执行复制平仓数据校验"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
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
