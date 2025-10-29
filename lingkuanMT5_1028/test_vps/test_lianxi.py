import time
import math
import allure
import logging
import pytest
from lingkuanMT5_1028.VAR.VAR import *
from lingkuanMT5_1028.conftest import var_manager
from lingkuanMT5_1028.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("VPS策略下单-开仓的场景校验")
class TestVPSOrdersend:
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
    class TestVPSOrderSend1(APITestBase):
        @pytest.mark.url("vps")
        @allure.title("修改跟单账号")
        def test_follow_updateSlave(self, var_manager, logged_session, encrypted_password):
            with allure.step("1. 修改跟单账号"):
                # followMode  0 : 固定手数  1：手数比例 2：净值比例
                # remainder  0 : 四舍五入  1：取小数
                new_user = var_manager.get_variable("new_user")
                MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
                MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
                MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
                platformId = var_manager.get_variable("platformId")
                data = {
                    "traderId": MT5vps_trader_id,
                    "platform": new_user["platform"],
                    "account": MT5vps_user_accounts_1,
                    "password": encrypted_password,
                    "platformType": 1,
                    "remark": "",
                    "followDirection": 0,
                    "followMode": 1,
                    "remainder": 0,
                    "followParam": "1",
                    "placedType": 0,
                    "templateId": 1,
                    "followStatus": 1,
                    "followOpen": 1,
                    "followClose": 1,
                    "followRep": 0,
                    "fixedComment": "",
                    "commentType": None,
                    "digits": 0,
                    "cfd": "",
                    "forex": "",
                    "abRemark": "",
                    "id": MT5vps_addslave_id,
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
