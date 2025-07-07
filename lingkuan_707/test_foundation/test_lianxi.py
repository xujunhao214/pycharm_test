import time

import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuan_707.VAR.VAR import *
from lingkuan_707.conftest import var_manager
from lingkuan_707.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("跟单软件看板")
class TestDeleteFollowSlave(APITestBase):
    # ---------------------------
    # 数据库校验-策略平仓-平仓订单详情持仓检查
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略平仓-平仓订单详情持仓检查")
    def test_dbquery_closed_orderdetail(self, var_manager, db_transaction):
        with allure.step("1. 检查订单详情界面的数据"):
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

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="create_time",  # 按创建时间过滤
                time_range=10,  # 只查前后1分钟的数据
                timeout=WAIT_TIMEOUT,  # 最多等60秒
                poll_interval=POLL_INTERVAL,  # 每2秒查一次
                stable_period=STBLE_PERIOD,  # 新增：数据连续5秒不变则认为加载完成
                order_by="create_time DESC"  # 按创建时间倒序
            )

        with allure.step("2. 提取数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            order_nos = list(map(lambda x: x["order_no"], db_data))
            logging.info(f"持仓订单的订单号: {order_nos}")
            var_manager.set_runtime_variable("order_nos", order_nos)

        with allure.step("3. 校验数据"):
            addsalve_size = [record["size"] for record in db_data]
            total = sum(addsalve_size)
            logging.info(f"手数: {addsalve_size} 手数总和: {total}")
            totalSzie = trader_ordersend["totalSzie"]
            assert float(total) == float(totalSzie), f"跟单总手数和下单的手数不相等 (实际: {total}, 预期: {totalSzie})"