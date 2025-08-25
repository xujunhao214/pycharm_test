# lingkuan_815/tests/test_vps_ordersend.py
import time
import math
import allure
import logging
import pytest
from lingkuan_818.VAR.VAR import *
from lingkuan_818.conftest import var_manager
from lingkuan_818.commons.api_base import APITestBase
from lingkuan_818.commons.redis_utils import *

logger = logging.getLogger(__name__)
SKIP_REASON = "该用例暂时跳过"  # 统一跳过原因


# ---------------------------
# 修改模式、品种
# ---------------------------
@allure.feature("云策略策略下单-跟单修改模式、品种")
class TestVPSOrderSend_Scence(APITestBase):
    @allure.title("数据库查询-获取停止的order_no")
    def test_copy_verify_db(self, var_manager, db_transaction):
        """验证复制下单后数据库中的订单数据正确性"""
        with allure.step("查询复制订单详情数据"):
            global order_no
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            sql = """
                            SELECT 
                                order_no
                            FROM 
                                follow_order_instruct
                            WHERE instruction_type = %s
                                AND cloud_type = %s
                                AND min_lot_size = %s
                                AND max_lot_size = %s
                                AND trader_id = %s
                        """
            params = ("1", "0", "1.00", "0.10", vps_trader_id)

            # 轮询等待数据库记录
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="create_time"
            )

        with allure.step("执行复制下单数据校验"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法进行复制下单校验")

            # 订单状态校验
            order_no = db_data[0]["order_no"]
            print("order_no:", order_no)