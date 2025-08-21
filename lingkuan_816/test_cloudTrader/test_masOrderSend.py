# lingkuan_816/tests/test_云策略_ordersend.py
import allure
import logging
import pytest
import time
import math
from lingkuan_816.VAR.VAR import *
from lingkuan_816.conftest import var_manager
from lingkuan_816.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"


@allure.feature("交易下单-云策略manager策略账号分配下单")
class TestbargainmasOrderSend_allocation(APITestBase):
    @allure.title("账号管理-交易下单-云策略manager策略账号分配下单")
    def test_bargain_masOrderSend(self, logged_session, var_manager):
        # 1. 发送云策略分配下单请求
        global cloudTrader_user_ids_3
        cloudOrderSend = var_manager.get_variable("cloudOrderSend")
        cloudTrader_user_ids_3 = var_manager.get_variable("cloudTrader_user_ids_3")
        data = {
            "traderList": [cloudTrader_user_ids_3],
            "type": 0,
            "tradeType": 0,
            "symbol": cloudOrderSend["symbol"],
            "placedType": 0,
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

        # 2. 判断云策略复制下单是否成功
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    @allure.title("数据库校验-交易开仓-指令及订单详情数据检查")
    def test_dbquery_orderSend(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            cloudTrader_user_accounts_3 = var_manager.get_variable("cloudTrader_user_accounts_3")
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
                cloudTrader_user_accounts_3,
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record_with_timezone(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="fod.open_time"
            )

        with allure.step("2. 数据校验"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            status = db_data[0]["status"]
            assert status in (0, 1), f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}"
            logging.info(f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}")

            # 手数范围：结束手数校验
            min_lot_size = db_data[0]["min_lot_size"]
            endsize = trader_ordersend["endSize"]
            assert math.isclose(float(endsize), float(min_lot_size), rel_tol=1e-9, abs_tol=1e-9), \
                f'手数范围：结束手数是：{endsize}，实际是：{min_lot_size}'
            logging.info(f'手数范围：结束手数是：{endsize}，实际是：{min_lot_size}')

            # 手数范围：开始手数校验
            max_lot_size = db_data[0]["max_lot_size"]
            startSize = trader_ordersend["startSize"]
            assert math.isclose(float(startSize), float(max_lot_size), rel_tol=1e-9, abs_tol=1e-9), \
                f'手数范围：开始手数是：{startSize}，实际是：{max_lot_size}'
            logging.info(f'手数范围：开始手数是：{startSize}，实际是：{max_lot_size}')

            # 下单总手数与指令表总手数校验
            total_lots = db_data[0]["total_lots"]
            totalSzie = trader_ordersend["totalSzie"]
            assert math.isclose(float(totalSzie), float(total_lots), rel_tol=1e-9, abs_tol=1e-9), \
                f'下单总手数是：{totalSzie}，实际是：{total_lots}'
            logging.info(f'下单总手数是：{totalSzie}，实际是：{total_lots}')

            # 下单总手数与订单详情总手数校验
            totalSzie = trader_ordersend["totalSzie"]
            size = [record["size"] for record in db_data]
            total = sum(size)
            assert math.isclose(float(totalSzie), float(total), rel_tol=1e-9, abs_tol=1e-9), \
                f'下单总手数是：{totalSzie},订单详情总手数是：{total}'
            logging.info(f'下单总手数是：{totalSzie},订单详情总手数是：{total}')

    @allure.title("跟账号管理-交易下单-平仓")
    def test_bargain_masOrderClose(self, logged_session, var_manager):
        cloudTrader_user_ids_3 = var_manager.get_variable("cloudTrader_user_ids_3")
        # 1. 发送平仓请求
        data = {
            "isCloseAll": 1,
            "intervalTime": 100,
            "traderList": [cloudTrader_user_ids_3]
        }
        response = self.send_post_request(
            logged_session,
            '/bargain/masOrderClose',
            json_data=data
        )

        # 2. 判断是否平仓成功
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    @allure.title("数据库校验-交易平仓-指令及订单详情数据检查")
    def test_dbquery_addsalve_orderSendclose(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            cloudTrader_user_accounts_3 = var_manager.get_variable("cloudTrader_user_accounts_3")
            cloudTrader_vps_ids_2 = var_manager.get_variable("cloudTrader_vps_ids_2")
            sql = f"""
                SELECT 
                    fod.size,
                    fod.close_no,
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
                    foi.master_order,
                    foi.total_orders
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
            params = (
                '1',
                cloudTrader_user_accounts_3,
                cloudTrader_vps_ids_2,
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record_with_timezone(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="fod.close_time"
            )
        with allure.step("2. 数据校验"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            status = db_data[0]["status"]
            assert status in (0, 1), f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}"
            logging.info(f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}")

            # 平仓总手数校验
            totalSzie = trader_ordersend["totalSzie"]
            size = [record["size"] for record in db_data]
            total = sum(size)
            assert math.isclose(float(totalSzie), float(total), rel_tol=1e-9, abs_tol=1e-9), \
                f'下单总手数是：{totalSzie}，订单详情总手数是：{total}'
            logging.info(f'下单总手数是：{totalSzie}，订单详情总手数是：{total}')

        time.sleep(60)


@allure.feature("交易下单-云策略manager策略账号复制下单")
class TestbargainmasOrderSend_copy(APITestBase):
    @allure.title("账号管理-交易下单-云策略manager策略账号复制下单")
    def test_bargain_masOrderSend(self, logged_session, var_manager):
        # 1. 发送云策略复制下单请求
        global cloudTrader_user_ids_3
        cloudOrderSend = var_manager.get_variable("cloudOrderSend")
        cloudTrader_user_ids_3 = var_manager.get_variable("cloudTrader_user_ids_3")
        data = {
            "traderList": [cloudTrader_user_ids_3],
            "type": 0,
            "tradeType": 1,
            "intervalTime": 100,
            "symbol": cloudOrderSend["symbol"],
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

        # 2. 判断云策略复制下单是否成功
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    @allure.title("数据库校验-交易开仓-指令及订单详情数据检查")
    def test_dbquery_orderSend(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            cloudTrader_user_accounts_3 = var_manager.get_variable("cloudTrader_user_accounts_3")
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
                cloudTrader_user_accounts_3,
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record_with_timezone(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="fod.open_time"
            )

        with allure.step("2. 数据校验"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            status = db_data[0]["status"]
            assert status in (0, 1), f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}"
            logging.info(f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}")

            # 手数范围：结束手数校验
            min_lot_size = db_data[0]["min_lot_size"]
            endsize = trader_ordersend["endSize"]
            assert math.isclose(float(endsize), float(min_lot_size), rel_tol=1e-9, abs_tol=1e-9), \
                f'手数范围：结束手数是：{endsize}，实际是：{min_lot_size}'
            logging.info(f'手数范围：结束手数是：{endsize}，实际是：{min_lot_size}')

            # 手数范围：开始手数校验
            max_lot_size = db_data[0]["max_lot_size"]
            startSize = trader_ordersend["startSize"]
            assert math.isclose(float(startSize), float(max_lot_size), rel_tol=1e-9, abs_tol=1e-9), \
                f'手数范围：开始手数是：{startSize}，实际是：{max_lot_size}'
            logging.info(f'手数范围：开始手数是：{startSize}，实际是：{max_lot_size}')

            total_orders = db_data[0]["total_orders"]
            totalNum = trader_ordersend["totalNum"]
            assert math.isclose(float(totalNum), float(total_orders), rel_tol=1e-9), \
                f'总订单数量是：{totalNum}，实际是：{total_orders}'
            logging.info(f'总订单数量是：{totalNum}，实际是：{total_orders}')

            # 下单总手数与指令表总手数校验
            total_lots = db_data[0]["total_lots"]
            totalSzie = trader_ordersend["totalSzie"]
            assert math.isclose(float(totalSzie), float(total_lots), rel_tol=1e-9, abs_tol=1e-9), \
                f'下单总手数是：{totalSzie}，实际是：{total_lots}'
            logging.info(f'下单总手数是：{totalSzie}，实际是：{total_lots}')

            # 下单总手数与订单详情总手数校验
            totalSzie = trader_ordersend["totalSzie"]
            size = [record["size"] for record in db_data]
            total = sum(size)
            assert math.isclose(float(totalSzie), float(total), rel_tol=1e-9, abs_tol=1e-9), \
                f'下单总手数是：{totalSzie},订单详情总手数是：{total}'
            logging.info(f'下单总手数是：{totalSzie},订单详情总手数是：{total}')

    @allure.title("跟账号管理-交易下单-平仓")
    def test_bargain_masOrderClose(self, logged_session, var_manager):
        cloudTrader_user_ids_3 = var_manager.get_variable("cloudTrader_user_ids_3")
        # 1. 发送平仓请求
        data = {
            "isCloseAll": 1,
            "intervalTime": 100,
            "traderList": [cloudTrader_user_ids_3]
        }
        response = self.send_post_request(
            logged_session,
            '/bargain/masOrderClose',
            json_data=data
        )

        # 2. 判断是否平仓成功
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    @allure.title("数据库校验-交易平仓-指令及订单详情数据检查")
    def test_dbquery_addsalve_orderSendclose(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            cloudTrader_user_accounts_3 = var_manager.get_variable("cloudTrader_user_accounts_3")
            cloudTrader_vps_ids_2 = var_manager.get_variable("cloudTrader_vps_ids_2")
            sql = f"""
                SELECT 
                    fod.size,
                    fod.close_no,
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
                    foi.master_order,
                    foi.total_orders
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
            params = (
                '1',
                cloudTrader_user_accounts_3,
                cloudTrader_vps_ids_2,
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record_with_timezone(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="fod.close_time"
            )
        with allure.step("2. 数据校验"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            status = db_data[0]["status"]
            assert status in (0, 1), f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}"
            logging.info(f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}")

            # 平仓总手数校验
            totalSzie = trader_ordersend["totalSzie"]
            size = [record["size"] for record in db_data]
            total = sum(size)
            assert math.isclose(float(totalSzie), float(total), rel_tol=1e-9, abs_tol=1e-9), \
                f'下单总手数是：{totalSzie}，订单详情总手数是：{total}'
            logging.info(f'下单总手数是：{totalSzie}，订单详情总手数是：{total}')

        time.sleep(25)
