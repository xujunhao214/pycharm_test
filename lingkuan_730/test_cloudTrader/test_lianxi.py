# lingkuan_730/tests/test_vps_ordersend.py
import time
import math

import allure
import logging
import pytest
from lingkuan_730.VAR.VAR import *
from lingkuan_730.conftest import var_manager
from lingkuan_730.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


# ---------------------------
# 修改模式、品种
# ---------------------------
@allure.feature("云策略策略下单-跟单修改模式、品种")
class TestVPSOrderSend_Scence(APITestBase):
    @allure.title("云策略-云策略列表-修改云策略跟单")
    def test_cloudTrader_cloudBatchUpdate(self, var_manager, logged_session):
        with allure.step("1. 发送修改跟单策略账号请求，将followClose改为0，关闭平仓"):
            cloudMaster_id = var_manager.get_variable("cloudMaster_id")
            traderList_cloudTrader_4 = var_manager.get_variable("traderList_cloudTrader_4")
            traderList_cloudTrader_3 = var_manager.get_variable("traderList_cloudTrader_3")
            user_accounts_cloudTrader_3 = var_manager.get_variable("user_accounts_cloudTrader_3")
            data = [
                {
                    "traderList": [
                        traderList_cloudTrader_4
                    ],
                    "cloudId": cloudMaster_id,
                    "masterId": traderList_cloudTrader_3,
                    "masterAccount": user_accounts_cloudTrader_3,
                    "followDirection": 0,
                    "followMode": 1,
                    "followParam": 1,
                    "remainder": 0,
                    "placedType": 0,
                    "templateId": 1,
                    "followStatus": 1,
                    "followOpen": 1,
                    "followClose": 0,
                    "fixedComment": "ceshi",
                    "commentType": "",
                    "digits": 0,
                    "followTraderIds": [],
                    "sort": "100"
                }
            ]

            response = self.send_post_request(
                logged_session,
                '/mascontrol/cloudTrader/cloudBatchUpdate',
                json_data=data
            )

        with allure.step("2. 验证JSON返回内容"):
            self.assert_response_status(
                response,
                200,
                "修改云跟单账号失败"
            )

            # 3. 验证JSON返回内容
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )
