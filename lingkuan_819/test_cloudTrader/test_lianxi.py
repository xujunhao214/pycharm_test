import allure
import logging
import pytest
import time
import math
from lingkuan_819.VAR.VAR import *
from lingkuan_819.conftest import var_manager
from lingkuan_819.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"


# @pytest.mark.skipif(condition=True, reason=SKIP_REASON)
@allure.feature("云策略下单功能测试")
@allure.description("""
### 测试说明
- 前置条件：有云策略和云跟单
  1. 进行开仓，手数范围0.1-1，总订单5（停止功能）
  2. 点击停止
  2. 校验账号的下单总手数和数据库的手数，应该不相等
  3. 进行平仓
  4. 校验账号的数据是否正确
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

    @allure.title("数据库校验-复制下单数据")
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

    @allure.title("云策略-复制下单操作")
    def test_cloudTrader_cloudStopOrder(self, logged_session, var_manager):
        """执行云策略复制下单操作并验证请求结果"""
        with allure.step("发送复制下单请求"):
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

        with allure.step("验证复制下单响应结果"):
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
            db_data = self.wait_for_database_record_with_timezone(
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
            assert len(db_data) != 5, "订单数和下单总订单数不匹配"

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
