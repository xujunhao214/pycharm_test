import time

import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuan_819.VAR.VAR import *
from lingkuan_819.conftest import var_manager
from lingkuan_819.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"


@allure.feature("跟单软件看板")
class TestDeleteFollowSlave(APITestBase):
    @allure.title("云策略-云策略列表-删除云跟单账号-手动下单")
    def test_delete_handcloudBatchAdd(self, logged_session, var_manager):
        # 1. 发送删除删除云跟单账号请求
        cloudTrader_traderList_handid = var_manager.get_variable("cloudTrader_traderList_handid")
        if cloudTrader_traderList_handid is None:
            pytest.skip("云跟单账号不存在")
        data = {
            "traderList": [
                cloudTrader_traderList_handid
            ]
        }
        response = self.send_post_request(
            logged_session,
            "/mascontrol/cloudTrader/cloudBatchDelete",
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "删除云跟单账号失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )
