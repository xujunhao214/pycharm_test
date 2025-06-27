# lingkuan_youhua9/tests/test_vps_loukai.py
import allure
import logging
import pytest
from lingkuan_youhua9.VAR.VAR import *
from lingkuan_youhua9.conftest import var_manager
from lingkuan_youhua9.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


class TestLianxi(APITestBase):
    # ---------------------------
    # 数据库校验-策略开仓-跟单开仓指令
    # ---------------------------
    @allure.title("数据库校验-策略开仓-跟单开仓指令")
    def test_dbquery_orderSend_addsalve(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否有跟单开仓指令"):
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            add_Slave = var_manager.get_variable("add_Slave")

            table_name = trader_ordersend["table"]
            symbol = trader_ordersend["symbol"]

            sql = f"""
            SELECT * 
            FROM {table_name} 
            WHERE symbol LIKE %s 
              AND status = %s 
              AND if_follow = %s
              AND master_order_status = %s 
              AND type = %s 
              AND trader_id = %s
            """
            params = (
                f"%{symbol}%",
                "1",
                "1",
                "0",
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

        with allure.step("2. 验证订单状态"):
            # 定义验证函数
            def verify_close_status():
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

                total_lots = list(map(lambda x: x["total_lots"], db_data))
                logging.info(f"总手数: {total_lots}")
                true_total_lots = list(map(lambda x: x["true_total_lots"], db_data))
                logging.info(f"实际总手数: {true_total_lots}")

                if total_lots != true_total_lots:
                    pytest.fail(f"总手数：{total_lots}  ！= 实际总手数：{true_total_lots}")

                traded_lots = list(map(lambda x: x["traded_lots"], db_data))
                traded_lots_sum = sum(traded_lots)
                print(traded_lots)
                followParam = add_Slave["followParam"]
                print(f"followParam的值：{followParam}")
                if float(traded_lots_sum) != float(followParam):
                    pytest.fail(f"手数的数据有问题，实际下单手数：{traded_lots} 下单手数：{followParam}")

            # 执行验证
            try:
                verify_close_status()
                allure.attach("数据校验正确", "成功详情", allure.attachment_type.TEXT)
            except AssertionError as e:
                allure.attach(str(e), "数据失败", allure.attachment_type.TEXT)
                raise
