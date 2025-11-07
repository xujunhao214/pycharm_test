import time
import math
import allure
import logging
import pytest
from lingkuan_150.VAR.VAR import *
from lingkuan_150.conftest import var_manager
from lingkuan_150.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("VPS策略下单-开仓的场景校验-sell")
class TestVPSOrdersendsell:
    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    @allure.story("场景1：复制下单-手数0.1-1，总订单3，总手数1")
    @allure.description("""
    ### 测试说明
    - 前置条件：有vps策略和vps跟单
      1. 进行开仓，手数范围0.1-1，总订单3，总手数1
      2. 校验账号的数据是否正确
      3. 进行平仓
      4. 校验账号的数据是否正确
    - 预期结果：账号的数据正确
    """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    class TestVPSOrderSend1(APITestBase):
        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("VPS管理-VPS列表-校验服务器IP是否可用")
        def test_get_connect(self, logged_session, var_manager):
            # 1. 校验服务器IP是否可用
            add_VPS = var_manager.get_variable("add_VPS")
            response = self.send_get_request(
                logged_session,
                '/mascontrol/vps/connect',
                params={'ipAddress': add_VPS["ipAddress"]}
            )

            # 2. 验证响应状态码
            self.assert_response_status(
                response,
                200,
                "服务器IP不可用"
            )

            # 3. 验证JSON返回内容
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )
