import time
import math
import allure
import logging
import pytest
from lingkuan_150.VAR.VAR import *
from lingkuan_150.conftest import var_manager
from lingkuan_150.commons.api_base import APITestBase
from lingkuan_150.commons.redis_utils import *

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("云策略策略下单-跟单修改模式、品种")
class TestVPSOrderSend_Scence(APITestBase):
    @allure.title("云策略列表-跟单账号平仓")
    def test_addtrader_close(self, logged_session, var_manager):
        cloudTrader_user_count = var_manager.get_variable("cloudTrader_user_count", 0)
        # 循环范围：5 到 cloudTrader_user_count（包含两端）
        for i in range(5, cloudTrader_user_count + 1):
            # 直接获取变量值（无需创建动态变量）
            trader_user_id = var_manager.get_variable(f"cloudTrader_traderList_{i}")
            # 验证变量存在（可选，避免值为None导致请求失败）
            assert trader_user_id is not None, f"变量 cloudTrader_traderList_{i} 未找到或值为空"

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
