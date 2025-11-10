import time
import math
import allure
import logging
import pytest
from lingkuan_1027.VAR.VAR import *
from lingkuan_1027.conftest import var_manager
from lingkuan_1027.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("VPS策略下单-开仓的场景校验-buy")
class TestVPSOrdersendbuy:
    @allure.story("场景3：复制下单-手数0.1-1，总订单3，总手数1")
    @allure.description("""
    ### 测试说明
    - 前置条件：有vps策略和vps跟单
      1. 获取该服务器最大手数
      2. 交易下单-复制下单-策略账号进行开仓，手数21-21，总订单1
    - 预期结果：开仓失败，超过最大手数限制
    """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    @pytest.mark.usefixtures("class_random_str")
    class TestVPSOrderSend3(APITestBase):
        @allure.title("数据库提取该服务器最大手数限制")
        def test_dbquery_maxlots(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 平台列表-数据库的SQL查询"):
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