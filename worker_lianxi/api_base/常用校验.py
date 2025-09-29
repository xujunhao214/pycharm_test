import time
import allure
import logging
import pytest
from lingkuan_827.conftest import var_manager
from lingkuan_827.commons.api_base import *
import requests
from lingkuan_827.commons.jsonpath_utils import JsonPathUtils

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


# ------------------------------------
# 大模块1：VPS策略下单-停止平仓功能验证
# ------------------------------------
@allure.feature("VPS策略下单-平仓的功能校验")
# @pytest.mark.skipif(True, reason=SKIP_REASON)
class TestVPSCoreFunctionality:
    @allure.story("场景1：平仓的停止功能验证")
    @allure.description("""
    ### 用例说明
    - 前置条件：有vps策略和vps跟单
    - 操作步骤：
      1. 进行开仓，手数：0.01-1，总订单数量5
      2. 进行平仓，平仓时间修改为30秒
      3. 点击平仓的停止按钮，校验平仓订单数量不等于下单数量
      4. 再次进行平仓
    - 预期结果：平仓的停止功能正确
    """)
    @allure.title("数据库校验-交易下单-主指令及订单详情数据检查")
    def test_dbquery_orderSend(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情表账号数据"):
            new_user = var_manager.get_variable("new_user")
            sql = f"""
                           SELECT 
                               fod.size,
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
                               foi.min_lot_size,
                               foi.max_lot_size,
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
                               """
            params = (
                '0',
                new_user["account"],
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.query_database_with_time_with_timezone(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="fod.open_time"
            )
        with allure.step("2. 数据校验"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
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

            with allure.step("验证手数范围-开始手数"):
                max_lot_size = db_data[0]["max_lot_size"]
                self.verify_data(
                    actual_value=float(max_lot_size),
                    expected_value=float(0.1),
                    op=CompareOp.EQ,
                    message="开始手数应符合预期",
                    attachment_name="开始手数详情"
                )
                logging.info(f"开始手数验证通过: {max_lot_size}")

            with allure.step("验证手数范围-结束手数"):
                min_lot_size = db_data[0]["min_lot_size"]
                self.verify_data(
                    actual_value=float(min_lot_size),
                    expected_value=float(trader_ordersend["endSize"]),
                    op=CompareOp.EQ,
                    message="结束手数应符合预期",
                    attachment_name="结束手数详情"
                )
                logging.info(f"结束手数验证通过: {min_lot_size}")

            with allure.step("验证指令总手数"):
                total_lots = db_data[0]["total_lots"]
                totalSzie = trader_ordersend["totalSzie"]
                self.verify_data(
                    actual_value=float(total_lots),
                    expected_value=float(totalSzie),
                    op=CompareOp.EQ,
                    message="指令总手数应符合预期",
                    attachment_name="指令总手数详情"
                )
                logging.info(f"指令总手数验证通过: {total_lots}")

            with allure.step("验证详情总手数"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                totalSzie = trader_ordersend["totalSzie"]
                size = [record["size"] for record in db_data]
                total = sum(size)
                self.verify_data(
                    actual_value=float(total),
                    expected_value=float(totalSzie),
                    op=CompareOp.EQ,
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
