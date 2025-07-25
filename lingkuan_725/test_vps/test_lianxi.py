import time

import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuan_725.VAR.VAR import *
from lingkuan_725.conftest import var_manager
from lingkuan_725.commons.api_base import APITestBase  # 导入基础类
from lingkuan_725.commons.redis_utils import *

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("跟单软件看板")
class TestDeleteFollowSlave(APITestBase):
    # ---------------------------
    # VPS管理-VPS列表列表-删除VPS数据
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("VPS管理-VPS列表列表-紧急停止VPS")
    def test_delete_Vps(self, api_session, var_manager, logged_session):
        vps_list_id = var_manager.get_variable("vps_list_id")
        # 定义白名单（不可删除数据的ID列表）
        WHITE_LIST_IDS = WHITE_LIST
        if vps_list_id in WHITE_LIST_IDS:
            logging.warning(f"VPS ID {vps_list_id} 在白名单中，跳过删除数据操作。")
            assert False, f"VPS ID {vps_list_id} 在白名单中，不能删除数据。"
        params = {
            "vpsIdList": vps_list_id
        }
        # 1. 发送删除VPS数据请求
        response = self.send_delete_request(
            api_session,
            '/closeServer/shutdown',
            json_data=params
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "紧急停止VPS数据失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )
