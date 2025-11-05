import allure
import logging
import pytest
import time
import math
from lingkuanMT5_1027.VAR.VAR import *
from lingkuanMT5_1027.conftest import var_manager
from lingkuanMT5_1027.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("云策略复制下单-开仓的场景校验-buy")
class TestCloudStrategyOrderbuy:
    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    @allure.story("场景3：交易分配-手数范围0.1-1，总手数0.01")
    @allure.description("""
        ### 测试说明
        - 前置条件：有云策略和云跟单
          1. 进行开仓，手数范围0.1-1，总手数0.01
          2. 预期下单失败：总手数不能低于最低手数
        - 预期结果：提示正确
        """)
    @pytest.mark.usefixtures("class_random_str")
    class TestMasOrderSend3(APITestBase):
        @allure.title("数据库校验-云策略-复制下单数据")
        def test_db_query_maxlots(self, class_random_str, var_manager, db_transaction):
            """验证复制下单后数据库中的订单数据正确性"""
            with allure.step("1.查询复制订单详情数据"):
                new_user = var_manager.get_variable("new_user")
                sql = """
                                SELECT * from where broker_name = s% 
                            """
                params = (new_user["FXAdamantStone-Real"],)

                # 轮询等待数据库记录
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )

            with allure.step("2.数据库提取数据"):
                if not db_data:
                    pytest.fail("数据库查询为空")

                max_lots = db_data[0]["max_lots"]
                var_manager.set_runtime_variable("max_lots", max_lots)
                print(f"max_lots: {max_lots}")
