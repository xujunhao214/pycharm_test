import time
import math
import allure
import logging
import pytest
from lingkuan_827.VAR.VAR import *
from lingkuan_827.conftest import var_manager
from lingkuan_827.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"


@allure.story("VPS交易分配-下单的场景校验")
@allure.description("""
### 测试说明
- 场景校验：手数范围>总手数>订单数量
- 前置条件：有vps策略和vps跟单
  1. 进行开仓，手数范围0.1-1，总手数2
  2. 预期下单失败：下单失败，请检查下单参数
- 预期结果：提示正确
""")
class TestVPSOrderSend2(APITestBase):
    class TestVPStradingOrders1(APITestBase):
        @allure.title("VPS交易下单-分配下单请求")
        def test_copy_order_send(self, logged_session, var_manager):
            # 发送VPS交易下单-复制下单请求
            masOrderSend = var_manager.get_variable("masOrderSend")
            vps_trader_user_id = var_manager.get_variable("vps_trader_user_id")
            data = {
                "traderList": [vps_trader_user_id],
                "type": 0,
                "tradeType": 0,
                "symbol": masOrderSend["symbol"],
                "startSize": "0.10",
                "endSize": "1.00",
                "totalSzie": "2",
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
                "下单失败，请检查下单参数",
                "响应msg字段应为：下单失败，请检查下单参数"
            )
