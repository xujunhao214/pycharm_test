# lingkuan_725/tests/test_vps_ordersend.py
import time
import math

import allure
import logging
import pytest
from lingkuan_725.VAR.VAR import *
from lingkuan_725.conftest import var_manager
from lingkuan_725.commons.api_base import APITestBase  # 导入基础类
from lingkuan_725.commons.redis_utils import *

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"


@allure.feature("云策略策略下单-跟单修改模式、品种")
class TestVPSOrderSend_Scence(APITestBase):
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库查询-提取数据库平台ID数据")
    def test_dbquery_trader(self, var_manager, db_transaction):
        with allure.step("1. 提取数据库平台ID数据"):
            new_user = var_manager.get_variable("new_user")
            # 执行数据库查询
            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_platform WHERE server = %s",
                (new_user["platform"],)
            )

            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            platformId = db_data[0]["id"]
            logging.info(f"平台ID: {platformId}")
            var_manager.set_runtime_variable("platformId", platformId)
