import time
import math
import allure
import logging
import pytest
from lingkuan_725.VAR.VAR import *
from lingkuan_725.conftest import var_manager
from lingkuan_725.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"


@allure.feature("VPS策略下单-跟随策略账号订单备注3种情况")
@allure.description("""
### 用例说明
- 前置条件：有vps策略和vps跟单，vps策略修改跟单备注开关
- 操作步骤：
  1. 修改vps策略备注
  2. 进行开仓
  3. 校验跟单备注信息
  4. 进行平仓
- 预期结果：跟单备注信息正确
""")
class TestVPSOrderSend_closeaddremark(APITestBase):
    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-修改跟单账号")
    def test_follow_updateSlave(self, var_manager, logged_session, encrypted_password):
        with allure.step("1. 发送修改跟单账号请求"):
            # 1. 发送修改跟单账号请求(跟单也有备注信息，走自己的备注)
            new_user = var_manager.get_variable("new_user")
            vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            platformId = var_manager.get_variable("platformId")
            data = {
                "traderId": vps_trader_id,
                "platform": new_user["platform"],
                "account": vps_user_accounts_1,
                "password": encrypted_password,
                "remark": "",
                "followDirection": 0,
                "followMode": 1,
                "remainder": 0,
                "followParam": 1,
                "placedType": 0,
                "templateId": 1,
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
        with allure.step("2. 验证响应状态码和JSON返回内容"):
            # 2. 验证响应状态码
            self.assert_response_status(
                response,
                200,
                "修改vps跟单信息失败"
            )

            # 3. 验证JSON返回内容
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )
