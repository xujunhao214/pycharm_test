import time

import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuan_709.VAR.VAR import *
from lingkuan_709.conftest import var_manager
from lingkuan_709.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("跟单软件看板")
class TestDeleteFollowSlave(APITestBase):
    @allure.title("数据库校验-云策略平仓-云策略跟单账号数据校验")
    def test_dbbargain_masOrderSend4(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否有下单"):
            vps_cloudTrader_ids_2 = var_manager.get_variable("vps_cloudTrader_ids_2")

            sql = f"""
                       SELECT 
                            fod.size,
                            fod.close_no,
                            foi.true_total_lots,
                            foi.order_no,
                            foi.operation_type,
                            foi.create_time,
                            foi.status
                        FROM 
                            follow_order_detail fod
                        INNER JOIN 
                            follow_order_instruct foi 
                        ON 
                            foi.order_no = fod.close_no COLLATE utf8mb4_0900_ai_ci
                        WHERE foi.trader_id = %s
                            AND foi.operation_type = %s 
                       """
            params = (
                vps_cloudTrader_ids_2,
                "1"
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="foi.create_time",  # 按创建时间过滤
                time_range=MYSQL_TIME,  # 只查前后1分钟的数据
                timeout=WAIT_TIMEOUT,  # 最多等30秒
                poll_interval=POLL_INTERVAL,  # 每2秒查一次
                stable_period=STBLE_PERIOD,  # 新增：数据连续5秒不变则认为加载完成
                order_by="foi.create_time DESC"  # 按创建时间倒序
            )
        with allure.step("2. 对数据进行校验"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            size = [record["size"] for record in db_data]
            cloudOrderSend = var_manager.get_variable("cloudOrderSend")
            total = sum(size)
            totalSzie = cloudOrderSend["totalSzie"]
            assert float(total) == float(
                totalSzie), f"跟单总手数和下单的手数不相等 (实际: {total}, 预期: {totalSzie})"
            logging.info(f"跟单总手数和下单的手数 (实际: {total}, 预期: {totalSzie})")

            # time.sleep(90)
