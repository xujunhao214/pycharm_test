import time

import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuan_704.VAR.VAR import *
from lingkuan_704.conftest import var_manager
from lingkuan_704.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("跟单软件看板")
class TestDeleteFollowSlave(APITestBase):
    @allure.title("数据库校验-VPS分配下单-持仓检查")
    def test_dbquery_order_detail(self, var_manager, db_transaction):
        with allure.step("1. 根据下单指令仓库的order_no字段获取跟单账号订单数据"):
            order_no = var_manager.get_variable("order_no")
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            masOrderSend = var_manager.get_variable("masOrderSend")

            table_name = masOrderSend["table_detail"]
            symbol = masOrderSend["symbol"]

            sql = f"""
                SELECT * 
                FROM {table_name} 
                WHERE symbol LIKE %s 
                  AND send_no = %s 
                  AND type = %s 
                  AND trader_id = %s
                """
            params = (
                f"%{symbol}%",
                order_no,
                masOrderSend["type"],
                vps_addslave_id
            )

            db_data = self.wait_for_database_record(
                db_transaction,
                sql,
                params,
                time_field="create_time",
                time_range=MYSQL_TIME
            )

        with allure.step("2. 校验数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")
            addsalve_size = [record["size"] for record in db_data]
            total = sum(addsalve_size)
            logging.info(f"手数: {addsalve_size}   手数总和: {total}")
            totalSzie = trader_ordersend["totalSzie"]
            assert float(total) == float(
                totalSzie), f"跟单总手数和下单的手数不相等 (实际: {total}, 预期: {totalSzie})"