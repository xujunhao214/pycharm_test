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
    # ---------------------------
    # 数据库校验-交易平仓-持仓检查跟单账号数据
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-交易平仓-持仓检查跟单账号数据")
    def test_dbquery_addsalve_clsesdetail(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            user_accounts_1 = var_manager.get_variable("user_accounts_1")
            table_name = trader_ordersend["table_detail"]
            close_send_nos = var_manager.get_variable("close_send_nos")

            sql = f"""
                    SELECT * 
                    FROM {table_name} 
                    WHERE source_user = %s
                      AND account = %s
                      AND close_status = %s
                      AND close_no = %s
                    """
            params = (
                user_accounts_1,
                user_accounts_1,
                "1",
                close_send_nos

            )

            # 使用智能等待查询
            db_data = self.wait_for_database_record(
                db_transaction,
                sql,
                params,
                time_field="create_time",
                time_range=20,
                timeout=WAIT_TIMEOUT,
                poll_interval=POLL_INTERVAL,
                order_by="create_time DESC"
            )
        with allure.step("2. 校验数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            close_addsalve_size = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("close_addsalve_size", close_addsalve_size)
            total = sum(close_addsalve_size)
            logging.info(f"手数: {close_addsalve_size} 手数总和: {total}")
            totalSzie = trader_ordersend["totalSzie"]
            assert float(total) == float(
                totalSzie), f"跟单总手数和下单的手数不相等 (实际: {total}, 预期: {totalSzie})"