import time
import math
import random
import allure
import logging
import pytest
from lingkuan_1120.VAR.VAR import *
from lingkuan_1120.conftest import var_manager
from lingkuan_1120.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"

# 全局中断标志：用于检测到 Trade timeout 时终止所有执行
GLOBAL_STOP_FLAG = False


@allure.feature("VPS策略下单-开仓的场景校验")
class TestVPSOrdersendbuy:
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    class TestVPSOrderSend1(APITestBase):
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

            with allure.step("2. 提取数据库数据"):
                # 提取数据库中的值
                if not db_data:
                    pytest.fail("数据库查询结果为空")

                vpsId = db_data[0]["id"]
                var_manager.set_runtime_variable("vpsId", vpsId)
                print(f"成功提取 VPS ID: {vpsId}")

                vpsname = db_data[0]["name"]
                var_manager.set_runtime_variable("vpsname", vpsname)
                print(f"成功提取vpsname: {vpsname}")
