import allure
import logging
import pytest
import time
import math
from lingkuanMT5_1027.VAR.VAR import *
from lingkuanMT5_1027.conftest import var_manager
from lingkuanMT5_1027.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("云策略复制下单-开仓的场景校验-buy")
class TestCloudStrategyOrderbuy(APITestBase):
    @allure.title("云策略列表-跟单账号平仓")
    def test_addtrader_close(self, logged_session, var_manager):
        MT5cloudTrader_user_count = var_manager.get_variable("MT5cloudTrader_user_count", 0)
        # 循环范围：5 到 MT5cloudTrader_user_count（包含两端）
        for i in range(5, MT5cloudTrader_user_count + 1):
            # 直接获取变量值（无需创建动态变量）
            trader_user_id = var_manager.get_variable(f"MT5cloudTrader_traderList_{i}")
            # 验证变量存在（可选，避免值为None导致请求失败）
            assert trader_user_id is not None, f"变量 MT5cloudTrader_traderList_{i} 未找到或值为空"

            with allure.step(f"1. 云策略列表-跟单账号平仓（traderUserId={trader_user_id}）"):
                data = {
                    "traderUserId": trader_user_id,
                    "isCloseAll": 1
                }

                # 1. 发送新增VPS组别请求
                response = self.send_post_request(
                    logged_session,
                    "/mascontrol/cloudTrader/orderClose",
                    json_data=data
                )
            with allure.step(f"2. 验证云策略列表-跟单账号平仓结果"):
                # 2. 验证响应状态码
                self.assert_response_status(
                    response,
                    200,
                    f"云策略组别平仓失败（traderUserId={trader_user_id}）"
                )

                # 3. 验证JSON返回内容
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    f"响应msg字段应为success（traderUserId={trader_user_id}）"
                )
