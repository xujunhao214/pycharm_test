import time
import math
import allure
import logging
import pytest
from lingkuan_819.VAR.VAR import *
from lingkuan_819.conftest import var_manager
from lingkuan_819.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该用例暂时跳过"


@allure.story("场景：场景三：手数范围0.1-1，总手数5")
@allure.description("""
### 用例说明
- 前置条件：有vps策略和vps跟单
  1. 开仓手数范围0.1-1，总手数5
  2. 检验喊单和跟单账号数据是否正确
  3. 进行平仓
  4. 检验喊单和跟单账号数据是否正确
- 预期结果：检验喊单和跟单账号数据正确
- 场景一：手数范围0.1-1，总订单3，总手数1
- 场景二：手数范围0.01-0.01，总手数0.01
- 场景三：手数范围0.1-1，总手数5
- 场景四：手数范围0.01-1，总订单10
- 场景五：手数范围0.1-1，总手数1（停止功能）
""")
# @pytest.mark.skipif(True, reason=SKIP_REASON)
class TestVPSOrderSend1(APITestBase):
    """合并五种开仓平仓场景的测试类，通过Story区分场景"""

    @allure.title("VPS复制下单请求")
    def test_copy_order_send(self, logged_session, var_manager):
        # 发送VPS复制下单请求
        masOrderSend = var_manager.get_variable("masOrderSend")
        vps_user_ids_1 = var_manager.get_variable("vps_user_ids_1")  # 使用实例变量存储
        data = {
            "traderList": [vps_user_ids_1],
            "type": 0,
            "tradeType": 1,
            "intervalTime": 100,
            "symbol": masOrderSend["symbol"],
            "placedType": 0,
            "startSize": "0.10",
            "endSize": "1.00",
            "totalNum": "5",
            "totalSzie": "",
            "remark": "测试数据"
        }
        response = self.send_post_request(
            logged_session,
            '/bargain/masOrderSend',
            json_data=data,
            sleep_seconds=0
        )

        # 验证下单成功
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    @allure.title("数据库校验-复制下单开仓数据")
    def test_copy_open_verify(self, var_manager, db_transaction):
        with allure.step("获取开仓订单数据"):
            vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
            sql = """
                    SELECT 
                        fod.size, fod.send_no, fod.magical, fod.open_price,
                        fod.symbol, fod.order_no, foi.true_total_lots, foi.order_no,
                        foi.operation_type, foi.create_time, foi.status,
                        foi.min_lot_size, foi.max_lot_size, foi.total_lots, foi.total_orders
                    FROM 
                        follow_order_detail fod
                    INNER JOIN 
                        follow_order_instruct foi 
                    ON 
                        foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
                    WHERE foi.operation_type = %s
                        AND fod.account = %s
                """
            params = ('0', vps_user_accounts_1)

            # 轮询等待数据
            db_data = self.wait_for_database_record_with_timezone(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="fod.open_time"
            )

        with allure.step("验证开仓数据"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            # 订单状态校验
            status = db_data[0]["status"]
            assert status in (0, 1), f"订单状态应为0或1，实际为: {status}"
            logger.info(f"订单状态验证通过: {status}")

            # 手数范围校验
            assert math.isclose(
                float(trader_ordersend["endSize"]),
                float(db_data[0]["min_lot_size"]),
                rel_tol=1e-9, abs_tol=1e-9
            ), f'结束手数不匹配: 预期{trader_ordersend["endSize"]}, 实际{db_data[0]["min_lot_size"]}'

            assert math.isclose(
                float(trader_ordersend["startSize"]),
                float(db_data[0]["max_lot_size"]),
                rel_tol=1e-9, abs_tol=1e-9
            ), f'开始手数不匹配: 预期{trader_ordersend["startSize"]}, 实际{db_data[0]["max_lot_size"]}'

            total_orders = db_data[0]["total_orders"]
            assert math.isclose(float(5), float(total_orders), rel_tol=1e-9), \
                f'总订单数量是：5，实际是：{total_orders}'
            logging.info(f'总订单数量是：5，实际是：{total_orders}')

    @allure.title("VPS复制下单平仓")
    def test_copy_order_close(self, var_manager, logged_session):
        vps_user_ids_1 = var_manager.get_variable("vps_user_ids_1")
        # 发送平仓请求
        data = {
            "isCloseAll": 1,
            "intervalTime": 100,
            "traderList": [vps_user_ids_1]
        }
        response = self.send_post_request(
            logged_session,
            '/bargain/masOrderClose',
            json_data=data
        )

        # 验证平仓成功
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    @allure.title("数据库校验-复制下单平仓数据")
    def test_copy_close_verify(self, var_manager, db_transaction):
        with allure.step("获取平仓订单数据"):
            vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            sql = """
                    SELECT 
                        fod.size, fod.close_no, fod.magical, fod.open_price,
                        fod.symbol, fod.order_no, foi.true_total_lots, foi.order_no,
                        foi.operation_type, foi.create_time, foi.status,
                        foi.min_lot_size, foi.max_lot_size, foi.total_lots,
                        foi.master_order, foi.total_orders
                    FROM 
                        follow_order_detail fod
                    INNER JOIN 
                        follow_order_instruct foi 
                    ON 
                        foi.order_no = fod.close_no COLLATE utf8mb4_0900_ai_ci
                    WHERE foi.operation_type = %s
                        AND fod.account = %s
                        AND fod.trader_id = %s
                """
            params = ('1', vps_user_accounts_1, vps_addslave_id)

            # 轮询等待数据
            db_data = self.wait_for_database_record_with_timezone(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="fod.close_time"
            )

        with allure.step("验证平仓数据"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            # 订单状态校验
            status = db_data[0]["status"]
            assert status in (0, 1), f"订单状态应为0或1，实际为: {status}"
            logger.info(f"平仓订单状态验证通过: {status}")

        # time.sleep(25)
