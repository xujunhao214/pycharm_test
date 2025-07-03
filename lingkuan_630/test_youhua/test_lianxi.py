# lingkuan_630/tests/test_vps_loukai.py
import allure
import logging
import pytest
from lingkuan_630.VAR.VAR import *
from lingkuan_630.conftest import var_manager
from lingkuan_630.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


class TestLianxi(APITestBase):
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略平仓-策略平仓主指令")
    def test_dbquery_traderclose(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否有策略平仓指令"):
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            vps_trader_isCloseAll = var_manager.get_variable("vps_trader_isCloseAll")
            table_name = vps_trader_isCloseAll["table"]
            sql = f"""
            SELECT * 
            FROM {table_name} 
            WHERE master_order_status = %s 
              AND trader_id = %s
              AND if_follow = %s
              AND instruction_type = %s
            """
            params = (
                "0",
                vps_trader_id,
                "0",
                "0"
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

        with allure.step("2. 提取数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            order_no_close = db_data[0]["order_no"]
            logging.info(f"获取策略平仓的订单号: {order_no_close}")
            var_manager.set_runtime_variable("order_no_close", order_no_close)

    # ---------------------------
    # 数据库校验-策略开仓-持仓检查
    # ---------------------------
    @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略平仓-持仓检查")
    def test_dbquery_closed_orderdetail(self, var_manager, db_transaction):
        with allure.step("1. 根据平仓指令仓库的order_no字段获取跟单账号订单数据"):
            order_no_close = var_manager.get_variable("order_no_close")
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            trader_ordersend = var_manager.get_variable("trader_ordersend")

            table_name = trader_ordersend["table_detail"]
            symbol = trader_ordersend["symbol"]

            sql = f"""
            SELECT * 
            FROM {table_name} 
            WHERE symbol LIKE %s 
              AND close_no = %s 
              AND type = %s 
              AND trader_id = %s
            """
            params = (
                f"%{symbol}%",
                order_no_close,
                trader_ordersend["type"],
                vps_trader_id
            )

            # 使用智能等待查询
            db_data = self.wait_for_database_record(
                db_transaction,
                sql,
                params,
                time_field="create_time",
                time_range=MYSQL_TIME,
                timeout=WAIT_TIMEOUT,
                poll_interval=POLL_INTERVAL
            )

            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            order_nos = list(map(lambda x: x["order_no"], db_data))
            logging.info(f"持仓订单的订单号: {order_nos}")
            var_manager.set_runtime_variable("order_nos", order_nos)

            addsalve_size = [record["size"] for record in db_data]
            logging.info(f"手数: {addsalve_size}")
            total = sum(addsalve_size)
            logging.info(f"手数总和: {total}")

            # 验证手数一致性
            if float(total) != float(trader_ordersend["totalSzie"]):
                error_msg = f"跟单总手数和下单的手数不相等 (实际: {total}, 预期: {trader_ordersend['totalSzie']})"
                allure.attach(error_msg, "手数验证失败", allure.attachment_type.TEXT)
                pytest.fail(error_msg)
            else:
                allure.attach("跟单总手数和下单的手数相等", "成功详情", allure.attachment_type.TEXT)
