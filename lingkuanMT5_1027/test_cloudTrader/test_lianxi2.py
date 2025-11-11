import time
import math
import allure
import logging
import pytest
from lingkuanMT5_1027.VAR.VAR import *
from lingkuanMT5_1027.conftest import var_manager
from lingkuanMT5_1027.commons.api_base import APITestBase
from lingkuanMT5_1027.commons.redis_utils import *

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


# ---------------------------
# 修改模式、品种
# ---------------------------
@allure.feature("云策略策略下单-跟单修改模式、品种")
class TestVPSOrderSend_Scence(APITestBase):
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库查询-获取券商名称和最大手数")
    def test_dbquery_platform(self, class_random_str, var_manager, db_transaction):
        with allure.step("1. 数据库的SQL查询"):
            new_user = var_manager.get_variable("new_user")
            sql = f""" SELECT * From follow_platform where server= %s """
            params = (
                new_user["platform"],
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.query_database(
                db_transaction=db_transaction,
                sql=sql,
                params=params
            )
        with allure.step("2. 提取数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，订单可能没有入库")

            max_lots = db_data[0]["max_lots"]
            var_manager.set_runtime_variable("max_lots", max_lots)

            broker_name = db_data[0]["broker_name"]
            var_manager.set_runtime_variable("broker_name", broker_name)

        with allure.step("3. 全局配置-数据库的SQL查询"):
            sql = f""" SELECT * From sys_params where param_name= %s """
            params = (
                "最大手数配置",
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.query_database(
                db_transaction=db_transaction,
                sql=sql,
                params=params
            )
        with allure.step("4. 提取数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，订单可能没有入库")

            param_value = db_data[0]["param_value"]
            var_manager.set_runtime_variable("param_value", param_value)
