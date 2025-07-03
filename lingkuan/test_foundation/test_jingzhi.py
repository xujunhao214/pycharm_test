# lingkuan/tests/test_vps_ordersend.py
import time

import allure
import logging
import pytest
from lingkuan.VAR.VAR import *
from lingkuan.conftest import var_manager
from lingkuan.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("VPS策略下单-正常开仓平仓")
class TestVPSOrderSend(APITestBase):
    # ---------------------------
    # 数据库校验-策略开仓-持仓检查跟单账号数据-固定手数5
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略开仓-跟单账号固定手数")
    def test_dbdetail_followParam5(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            vps_trader = var_manager.get_variable("vps_trader")
            table_name = trader_ordersend["table_detail"]
            user_accounts_5 = var_manager.get_variable("user_accounts_5")
            symbol = trader_ordersend["symbol"]

            sql = f"""
                    SELECT * 
                    FROM {table_name} 
                    WHERE symbol LIKE %s 
                      AND source_user = %s
                      AND account = %s
                    """
            params = (
                f"%{symbol}%",
                vps_trader["account"],
                user_accounts_5,
            )

            # 使用智能等待查询
            db_data = self.wait_for_database_record(
                db_transaction,
                sql,
                params,
                time_field="create_time",
                time_range=MYSQL_TIME,
                timeout=WAIT_TIMEOUT,
                poll_interval=POLL_INTERVAL,
                order_by="create_time DESC"
            )
