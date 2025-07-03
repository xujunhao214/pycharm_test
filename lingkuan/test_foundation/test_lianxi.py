import time

import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuan_703.VAR.VAR import *
from lingkuan_703.conftest import var_manager
from lingkuan_703.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("跟单软件看板")
class TestDeleteFollowSlave(APITestBase):
    # ---------------------------
    # 数据库-获取主账号净值
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库-获取主账号净值")
    def test_dbtrader_euqit(self, var_manager, db_transaction):
        with allure.step("1. 获取主账号净值"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            table_trader = trader_ordersend["table_trader"]
            vps_trader_id = var_manager.get_variable("vps_trader_id")

            sql = f"""
                SELECT * 
                FROM {table_trader} 
                WHERE id = %s
                """
            params = (
                vps_trader_id
            )

            # 使用智能等待查询
            db_data = self.query_database(
                db_transaction,
                sql,
                params,
            )

        with allure.step("2. 提取数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            dbtrader_euqit = db_data[0]["euqit"]
            var_manager.set_runtime_variable("dbtrader_euqit", dbtrader_euqit)
            logging.info(f"主账号净值：{dbtrader_euqit}")

    # ---------------------------
    # 数据库-获取跟单账号净值
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库-获取跟单账号净值")
    def test_dbaddsalve_euqit(self, var_manager, db_transaction):
        with allure.step("1. 获取跟单账号净值"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            table_trader = trader_ordersend["table_trader"]
            vps_addslave_ids_3 = var_manager.get_variable("vps_addslave_ids_3")

            sql = f"""
                                    SELECT * 
                                    FROM {table_trader} 
                                    WHERE id = %s
                                    """
            params = (
                vps_addslave_ids_3
            )

            # 使用智能等待查询
            db_data = self.query_database(
                db_transaction,
                sql,
                params,
            )

        with allure.step("2. 提取数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            addsalve_euqit = db_data[0]["euqit"]
            var_manager.set_runtime_variable("addsalve_euqit", addsalve_euqit)
            logging.info(f"跟单账号净值：{addsalve_euqit}")

    # 数据库校验-策略开仓-修改净值
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略开仓-修改净值")
    def test_dbclose_euqit(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            vps_trader = var_manager.get_variable("vps_trader")
            table_name = trader_ordersend["table_detail"]
            user_accounts_4 = var_manager.get_variable("user_accounts_4")
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
                user_accounts_4,
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

        with allure.step("2. 校验数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            addsalve_size_euqit = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("addsalve_size_euqit", addsalve_size_euqit)
            total = sum(addsalve_size_euqit)
            dbtrader_euqit = var_manager.get_variable("dbtrader_euqit")
            addsalve_euqit = var_manager.get_variable("addsalve_euqit")
            # 校验除数非零
            if dbtrader_euqit == 0:
                pytest.fail("dbtrader_euqit为0，无法计算预期比例（避免除零）")

            true_size = addsalve_euqit / dbtrader_euqit * 1
            # 断言（调整误差范围为合理值，如±0.1）
            assert abs(total - true_size) < 1, f"size总和与预期比例偏差过大：预期{true_size}，实际{total}，误差超过1"
