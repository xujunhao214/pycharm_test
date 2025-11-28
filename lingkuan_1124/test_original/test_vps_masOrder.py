import allure
import logging
import pytest
import time
import math
from lingkuan_1124.VAR.VAR import *
from lingkuan_1124.conftest import var_manager
from lingkuan_1124.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("VPS交易下单（分配与复制）")
@allure.description("""
### 测试说明
包含两种VPS交易下单模式的测试：
1. 分配下单：按指定手数范围分配订单
2. 复制下单：按复制模式生成订单
每种模式均包含下单、数据校验和平仓流程
""")
class TestVPStradingOrders(APITestBase):
    """整合VPS分配下单和复制下单的测试类"""

    # -------------------------- 分配下单测试 --------------------------
    @allure.story("模式一：分配下单")
    @allure.title("VPS分配下单请求")
    def test_allocation_order_send(self, logged_session, var_manager):
        # 发送VPS分配下单请求
        masOrderSend = var_manager.get_variable("masOrderSend")
        vps_user_ids_1 = var_manager.get_variable("vps_user_ids_1")  
        data = {
            "traderList": [vps_user_ids_1],
            "type": 0,
            "tradeType": 0,
            "symbol": masOrderSend["symbol"],
            "startSize": "0.10",
            "endSize": "1.00",
            "totalSzie": "1.00",
            "remark": "测试数据"
        }
        response = self.send_post_request(
            logged_session,
            '/bargain/masOrderSend',
            json_data=data
        )

        # 验证下单成功
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    @allure.story("模式一：分配下单")
    @allure.title("数据库校验-分配下单开仓数据")
    def test_allocation_open_verify(self, var_manager,   db_transaction):
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
            db_data = self.query_database_with_time_with_timezone(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="fod.open_time"
            )

        with allure.step("验证开仓数据"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            if not db_data:
                pytest.fail("数据库查询结果为空，订单可能没有入库")

            # 订单状态校验
            status = db_data[0]["status"]
            assert status in (0, 1), f"订单状态应为0或1或3，实际为: {status}"
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

            # 总手数校验
            total_lots = db_data[0]["total_lots"]
            assert math.isclose(
                float(trader_ordersend["totalSzie"]),
                float(total_lots),
                rel_tol=1e-9, abs_tol=1e-9
            ), f'总手数不匹配: 预期{trader_ordersend["totalSzie"]}, 实际{total_lots}'

            # 订单详情总手数校验
            total_size = sum(float(record["size"]) for record in db_data)
            assert math.isclose(
                float(trader_ordersend["totalSzie"]),
                total_size,
                rel_tol=1e-9, abs_tol=1e-9
            ), f'订单详情总手数不匹配: 预期{trader_ordersend["totalSzie"]}, 实际{total_size}'

    @allure.story("模式一：分配下单")
    @allure.title("VPS分配下单平仓")
    def test_allocation_order_close(self, var_manager,   logged_session):
        vps_user_ids_1 = var_manager.get_variable("vps_user_ids_1")
        # 发送平仓请求
        data = {
            "isCloseAll": 1,
            "intervalTime": 0,
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

    @allure.story("模式一：分配下单")
    @allure.title("数据库校验-分配下单平仓数据")
    def test_allocation_close_verify(self, var_manager,   db_transaction):
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
            db_data = self.query_database_with_time_with_timezone(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="fod.close_time"
            )

        with allure.step("验证平仓数据"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            if not db_data:
                pytest.fail("数据库查询结果为空，订单可能没有入库")

            # 订单状态校验
            status = db_data[0]["status"]
            assert status in (0, 1), f"订单状态应为0或1或3，实际为: {status}"
            logger.info(f"平仓订单状态验证通过: {status}")

            # 平仓总手数校验
            total_size = sum(float(record["size"]) for record in db_data)
            assert math.isclose(
                float(trader_ordersend["totalSzie"]),
                total_size,
                rel_tol=1e-9, abs_tol=1e-9
            ), f'平仓总手数不匹配: 预期{trader_ordersend["totalSzie"]}, 实际{total_size}'

        time.sleep(60)

    # -------------------------- 复制下单测试 --------------------------
    @allure.story("模式二：复制下单")
    @allure.title("VPS复制下单请求")
    def test_copy_order_send(self, logged_session, var_manager):
        # 发送VPS复制下单请求
        masOrderSend = var_manager.get_variable("masOrderSend")
        vps_user_ids_1 = var_manager.get_variable("vps_user_ids_1")  
        data = {
            "traderList": [vps_user_ids_1],
            "type": 0,
            "tradeType": 1,
            "intervalTime": 0,
            "symbol": masOrderSend["symbol"],
            "placedType": 0,
            "startSize": "0.10",
            "endSize": "1.00",
            "totalNum": "3",
            "totalSzie": "1.00",
            "remark": "测试数据"
        }
        response = self.send_post_request(
            logged_session,
            '/bargain/masOrderSend',
            json_data=data
        )

        # 验证下单成功
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    @allure.story("模式二：复制下单")
    @allure.title("数据库校验-复制下单开仓数据")
    def test_copy_open_verify(self, var_manager,   db_transaction):
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
            db_data = self.query_database_with_time_with_timezone(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="fod.open_time"
            )

        with allure.step("验证开仓数据"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            if not db_data:
                pytest.fail("数据库查询结果为空，订单可能没有入库")

            # 订单状态校验
            status = db_data[0]["status"]
            assert status in (0, 1), f"订单状态应为0或1或3，实际为: {status}"
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

            # 总手数校验
            total_lots = db_data[0]["total_lots"]
            assert math.isclose(
                float(trader_ordersend["totalSzie"]),
                float(total_lots),
                rel_tol=1e-9, abs_tol=1e-9
            ), f'总手数不匹配: 预期{trader_ordersend["totalSzie"]}, 实际{total_lots}'

            # 订单详情总手数校验
            total_size = sum(float(record["size"]) for record in db_data)
            assert math.isclose(
                float(trader_ordersend["totalSzie"]),
                total_size,
                rel_tol=1e-9, abs_tol=1e-9
            ), f'订单详情总手数不匹配: 预期{trader_ordersend["totalSzie"]}, 实际{total_size}'

    @allure.story("模式二：复制下单")
    @allure.title("VPS复制下单平仓")
    def test_copy_order_close(self, var_manager,   logged_session):
        vps_user_ids_1 = var_manager.get_variable("vps_user_ids_1")
        # 发送平仓请求
        data = {
            "isCloseAll": 1,
            "intervalTime": 0,
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

    @allure.story("模式二：复制下单")
    @allure.title("数据库校验-复制下单平仓数据")
    def test_copy_close_verify(self, var_manager,   db_transaction):
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
            db_data = self.query_database_with_time_with_timezone(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="fod.close_time"
            )

        with allure.step("验证平仓数据"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            if not db_data:
                pytest.fail("数据库查询结果为空，订单可能没有入库")

            # 订单状态校验
            status = db_data[0]["status"]
            assert status in (0, 1), f"订单状态应为0或1或3，实际为: {status}"
            logger.info(f"平仓订单状态验证通过: {status}")

            # 平仓总手数校验
            total_size = sum(float(record["size"]) for record in db_data)
            assert math.isclose(
                float(trader_ordersend["totalSzie"]),
                total_size,
                rel_tol=1e-9, abs_tol=1e-9
            ), f'平仓总手数不匹配: 预期{trader_ordersend["totalSzie"]}, 实际{total_size}'

        time.sleep(25)
