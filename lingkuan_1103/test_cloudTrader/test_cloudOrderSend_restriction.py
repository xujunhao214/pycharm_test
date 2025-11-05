import allure
import logging
import pytest
import time
import math
from lingkuan_1103.VAR.VAR import *
from lingkuan_1103.conftest import var_manager
from lingkuan_1103.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("云策略复制下单-开仓的场景校验-buy")
class TestCloudStrategyOrderbuy:
    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    @allure.story("场景1：交易分配-手数范围0.1-1，总手数0.01")
    @allure.description("""
        ### 测试说明
        - 前置条件：有云策略和云跟单
          1. 进行开仓，手数范围0.1-1，总手数0.01
          2. 预期下单失败：总手数不能低于最低手数
        - 预期结果：提示正确
        """)
    @pytest.mark.usefixtures("class_random_str")
    class TestMasOrderSend1(APITestBase):
        @allure.title("云策略-复制下单操作")
        def test_copy_place_order(self, class_random_str, logged_session, var_manager):
            """执行云策略复制下单操作并验证请求结果"""
            with allure.step("1.发送复制下单请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")

                request_data = {
                    "id": cloudMaster_id,
                    "type": 0,
                    "tradeType": 0,
                    "intervalTime": 100,
                    "cloudTraderId": [cloudTrader_traderList_2],
                    "symbol": "XAUUSD",
                    "placedType": 0,
                    "startSize": "0.1",
                    "endSize": "1.00",
                    "totalNum": "",
                    "totalSzie": "0.01",
                    "remark": "测试数据"
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
                    "总手数不能低于最低手数",
                    "响应msg字段应为：总手数不能低于最低手数"
                )

    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    @allure.story("场景2：交易分配-手数范围0.1-1，总手数2")
    @allure.description("""
        ### 测试说明
        - 前置条件：有云策略和云跟单
          1. 进行开仓，手数范围0.1-1，总手数2
          2. 预期下单失败：下单失败，请检查下单参数
        - 预期结果：提示正确
        """)
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
                    "tradeType": 0,
                    "intervalTime": 100,
                    "cloudTraderId": [cloudTrader_traderList_2],
                    "symbol": "XAUUSD",
                    "placedType": 0,
                    "startSize": "0.1",
                    "endSize": "1.00",
                    "totalNum": "",
                    "totalSzie": "2",
                    "remark": "测试数据"
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
                    "下单失败，请检查下单参数",
                    "响应msg字段应为：下单失败，请检查下单参数"
                )
