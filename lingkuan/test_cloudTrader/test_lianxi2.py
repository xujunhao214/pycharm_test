# lingkuan/tests/test_vps_ordersend.py
import time
import math
import allure
import logging
import pytest
from lingkuan.VAR.VAR import *
from lingkuan.conftest import var_manager
from lingkuan.commons.api_base import *
from lingkuan.commons.redis_utils import *

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


# ---------------------------
# 修改模式、品种
# ---------------------------
@allure.feature("云策略策略下单-跟单修改模式、品种")
class TestVPSOrderSend_Scence(APITestBase):
    # ---------------------------
    # 数据库查询-获取VPSID
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库查询-获取VPSID")
    def test_get_vpsID(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库数据"):
            ip_address = var_manager.get_variable("IP_ADDRESS")

            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_vps WHERE ip_address = %s",
                (ip_address,)
            )

            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            vpsId = db_data[0]["id"]
            # 存入变量管理器
            var_manager.set_runtime_variable("vpsId", vpsId)
            print(f"成功提取 VPS ID: {vpsId}")

    # ---------------------------
    # VPS管理-VPS列表-获取可见用户信息
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("VPS管理-VPS列表-获取可见用户信息")
    def test_get_user(self, logged_session, var_manager):
        # 1. 请求可见用户列表接口
        response = self.send_get_request(
            logged_session,
            '/sys/role/role'
        )

        # 2. 获取可见用户信息
        vps_user_data = response.extract_jsonpath("$.data")
        logging.info(f"获取的可见用户信息：{vps_user_data}")
        var_manager.set_runtime_variable("vps_user_data", vps_user_data)
