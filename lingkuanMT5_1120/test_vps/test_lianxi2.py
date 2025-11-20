import allure
import logging
import pytest
import time
from lingkuanMT5_1120.conftest import var_manager
from lingkuanMT5_1120.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("VPS策略账号交易下单-开仓的场景校验")
class TestVPSMasOrdersend(APITestBase):
    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-新增策略账号")
    def test_add_trader(self, class_random_str, var_manager, logged_session, encrypted_password):
        # 1. 发送新增策略账号请求
        new_user = var_manager.get_variable("new_user")
        data = {
            "type": 0,
            "account": new_user["account"],
            "password": encrypted_password,
            "platform": new_user["platform"],
            "remark": "",
            "platformId": "",
            "templateId": 1,
            "followStatus": 1,
            "cfd": "",
            "forex": "",
            "followOrderRemark": 1,
            "fixedComment": "",
            "commentType": "",
            "digits": "",
            "platformType": 1,
            "followTraderSymbolEntityList": []
        }
        response = self.send_post_request(
            logged_session,
            '/subcontrol/trader',
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "新增策略账号失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )
