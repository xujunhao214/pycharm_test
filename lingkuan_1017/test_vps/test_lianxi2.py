import time
import math
import allure
import logging
import pytest
from lingkuan_1017.VAR.VAR import *
from lingkuan_1017.conftest import var_manager
from lingkuan_1017.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("VPS策略下单-开仓的场景校验")
class TestVPSOrdersend(APITestBase):
    @pytest.mark.url("vps")
    @allure.title("修改跟单账号-手数取余-取小数")
    def test_follow_updateSlave(self, var_manager, logged_session, encrypted_password):
        with allure.step("1. 修改跟单账号"):
            # remainder  0 : 四舍五入  1：取小数
            new_user = var_manager.get_variable("new_user")
            vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            platformId = var_manager.get_variable("platformId")
            vps_template_id2 = var_manager.get_variable("vps_template_id2")
            data = {
                "traderId": vps_trader_id,
                "platform": new_user["platform"],
                "account": vps_user_accounts_1,
                "password": encrypted_password,
                "platformType": 0,
                "remark": "",
                "followDirection": 0,
                "followMode": 1,
                "remainder": 1,
                "followParam": "0.25",
                "placedType": 0,
                "templateId": vps_template_id2,
                "followStatus": 1,
                "followOpen": 1,
                "followClose": 1,
                "followRep": 0,
                "fixedComment": "",
                "commentType": "",
                "digits": 0,
                "cfd": "",
                "forex": "",
                "abRemark": "",
                "id": vps_addslave_id,
                "platformId": platformId
            }
            response = self.send_post_request(
                logged_session,
                '/subcontrol/follow/updateSlave',
                json_data=data
            )
        with allure.step("2. 验证响应状态码和内容"):
            self.assert_response_status(response, 200, "修改跟单账号失败")
            self.assert_json_value(response, "$.msg", "success", "响应msg应为success")
