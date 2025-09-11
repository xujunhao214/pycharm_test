import time
import math
import allure
import logging
import pytest
from self_developed.VAR.VAR import *
from self_developed.conftest import var_manager
from self_developed.commons.api_base import APITestBase, CompareOp
from self_developed.commons.redis_utils import *

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


# ---------------------------
# 修改模式、品种
# ---------------------------
@allure.feature("云策略策略下单-跟单修改模式、品种")
class TestVPSOrderSend_Scence(APITestBase):
    @allure.title("数据库校验-策略开仓-跟单指令及订单详情数据检查")
    def test_dbquery_addsalve_orderSend(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情表账号数据"):
            vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
            sql = f"""
                        SELECT 
                            fod.size,
                            fod.comment,
                            fod.send_no,
                            fod.magical,
                            fod.open_price,
                            fod.symbol,
                            fod.order_no,
                            foi.true_total_lots,
                            foi.order_no,
                            foi.operation_type,
                            foi.create_time,
                            foi.status,
                            foi.total_lots,
                            foi.total_orders
                        FROM 
                            follow_order_detail fod
                        INNER JOIN 
                            follow_order_instruct foi 
                        ON 
                            foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
                        WHERE foi.operation_type = %s
                            AND fod.account = %s
                            AND fod.comment = %s
                            """
            params = (
                '0',
                vps_user_accounts_1,
                "changjing1"
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.query_database_with_time_with_timezone(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="fod.open_time",
                time_range=10
            )

        with allure.step("2. 数据校验"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            with allure.step("验证订单状态"):
                status = db_data[0]["status"]
                self.verify_data(
                    actual_value=status,
                    expected_value=(0, 1),
                    op=CompareOp.IN,
                    message="订单状态应为0或1",
                    attachment_name="订单状态详情"
                )
                logging.info(f"订单状态验证通过: {status}")

            with allure.step("验证详情总手数"):
                size = [record["size"] for record in db_data]
                total = sum(size)
                self.verify_data(
                    actual_value=float(total),
                    expected_value=float(0.12),
                    op=CompareOp.EQ,
                    rel_tol=1e-2,
                    message="详情总手数应符合预期",
                    attachment_name="详情总手数"
                )
                logging.info(f"详情总手数验证通过: {total}")

            with allure.step("验证详情手数和指令手数一致"):
                size = [record["size"] for record in db_data]
                true_total_lots = [record["true_total_lots"] for record in db_data]
                self.assert_list_equal_ignore_order(
                    size,
                    true_total_lots,
                    f"手数不一致: 详情{size}, 指令{true_total_lots}"
                )
                logger.info(f"手数一致: 详情{size}, 指令{true_total_lots}")
