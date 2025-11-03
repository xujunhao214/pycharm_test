import allure
import logging
import pytest
import time
import math
from lingkuan_MT5.VAR.VAR import *
from lingkuan_MT5.conftest import var_manager
from lingkuan_MT5.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("云策略manager策略账号交易下单")
@allure.description("""
### 测试说明
包含两种云策略 manager策略账号交易下单模式的测试：
1. 分配下单：按指定手数范围分配订单
2. 复制下单：按复制模式生成订单
每种模式均包含下单、数据校验和平仓流程
""")
class TestCloudStrategyOrderSend(APITestBase):
    """云策略manager策略账号交易下单测试类"""

    # -------------------------- 分配下单场景 --------------------------
    @allure.story("分配下单场景")
    @allure.title("云策略manager策略账号-分配下单操作")
    def test_allocation_place_order(self, logged_session, var_manager):
        cloudOrderSend = var_manager.get_variable("cloudOrderSend")
        self.MT5cloudTrader_user_ids_3 = var_manager.get_variable("MT5cloudTrader_user_ids_3")

        request_data = {
            "traderList": [self.MT5cloudTrader_user_ids_3],
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
            json_data=request_data
        )

        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "分配下单响应msg字段应为success"
        )

    @allure.story("分配下单场景")
    @allure.title("数据库校验-分配下单开仓数据")
    def test_allocation_verify_open_db(self, var_manager, db_transaction):
        MT5cloudTrader_user_accounts_3 = var_manager.get_variable("MT5cloudTrader_user_accounts_3")
        sql = """
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
        params = ('0', MT5cloudTrader_user_accounts_3)

        db_data = self.query_database_with_time_with_timezone(
            db_transaction=db_transaction,
            sql=sql,
            params=params,
            time_field="fod.open_time"
        )

        trader_ordersend = var_manager.get_variable("trader_ordersend")
        if not db_data:
            pytest.fail("数据库查询结果为空，无法进行开仓数据校验")

        # 订单状态校验
        status = db_data[0]["status"]
        assert status in (0, 1), \
            f"订单状态应为0(处理中)或1(全部成功)，实际为: {status}"
        logger.info(f"分配下单开仓状态校验通过: {status}")

        # 结束手数校验
        min_lot_size = db_data[0]["min_lot_size"]
        endsize = trader_ordersend["endSize"]
        assert math.isclose(float(endsize), float(min_lot_size), rel_tol=1e-9, abs_tol=1e-9), \
            f'结束手数不匹配，预期: {endsize}, 实际: {min_lot_size}'
        logger.info(f"分配下单结束手数校验通过: {endsize}")

        # 开始手数校验
        max_lot_size = db_data[0]["max_lot_size"]
        startSize = trader_ordersend["startSize"]
        assert math.isclose(float(startSize), float(max_lot_size), rel_tol=1e-9, abs_tol=1e-9), \
            f'开始手数不匹配，预期: {startSize}, 实际: {max_lot_size}'
        logger.info(f"分配下单开始手数校验通过: {startSize}")

        # 总手数与指令表校验
        total_lots = db_data[0]["total_lots"]
        totalSzie = trader_ordersend["totalSzie"]
        assert math.isclose(float(totalSzie), float(total_lots), rel_tol=1e-9, abs_tol=1e-9), \
            f'总手数与指令表不匹配，预期: {totalSzie}, 实际: {total_lots}'
        logger.info(f"分配下单总手数与指令表校验通过: {totalSzie}")

        # 总手数与订单详情校验
        size_sum = sum(record["size"] for record in db_data)
        assert math.isclose(float(totalSzie), float(size_sum), rel_tol=1e-9, abs_tol=1e-9), \
            f'总手数与订单详情不匹配，预期: {totalSzie}, 实际: {size_sum}'
        logger.info(f"分配下单总手数与订单详情校验通过: {totalSzie}")

    @allure.story("分配下单场景")
    @allure.title("云策略manager策略账号-分配下单平仓操作")
    def test_allocation_close_order(self, logged_session, var_manager):
        MT5cloudTrader_user_ids_3 = var_manager.get_variable("MT5cloudTrader_user_ids_3")

        request_data = {
            "isCloseAll": 1,
            "intervalTime": 100,
            "traderList": [MT5cloudTrader_user_ids_3]
        }

        response = self.send_post_request(
            logged_session,
            '/bargain/masOrderClose',
            json_data=request_data
        )

        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "分配平仓响应msg字段应为success"
        )

    @allure.story("分配下单场景")
    @allure.title("数据库校验-分配下单平仓数据")
    def test_allocation_verify_close_db(self, var_manager, db_transaction):
        MT5cloudTrader_user_accounts_3 = var_manager.get_variable("MT5cloudTrader_user_accounts_3")
        MT5cloudTrader_MT5vps_ids_2 = var_manager.get_variable("MT5cloudTrader_MT5vps_ids_2")

        sql = """
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
        params = ('1', MT5cloudTrader_user_accounts_3, MT5cloudTrader_MT5vps_ids_2)

        db_data = self.query_database_with_time_with_timezone(
            db_transaction=db_transaction,
            sql=sql,
            params=params,
            time_field="fod.close_time"
        )

        trader_ordersend = var_manager.get_variable("trader_ordersend")
        if not db_data:
            pytest.fail("数据库查询结果为空，无法进行平仓数据校验")

        # 平仓状态校验
        status = db_data[0]["status"]
        assert status in (0, 1), \
            f"平仓状态应为0(处理中)或1(全部成功)，实际为: {status}"
        logger.info(f"分配下单平仓状态校验通过: {status}")

        # 平仓总手数校验
        totalSzie = trader_ordersend["totalSzie"]
        size_sum = sum(record["size"] for record in db_data)
        assert math.isclose(float(totalSzie), float(size_sum), rel_tol=1e-9, abs_tol=1e-9), \
            f'平仓总手数不匹配，预期: {totalSzie}, 实际: {size_sum}'
        logger.info(f"分配下单平仓总手数校验通过: {totalSzie}")

        time.sleep(60)

    # -------------------------- 复制下单场景 --------------------------
    @allure.story("复制下单场景")
    @allure.title("云策略manager策略账号-复制下单操作")
    def test_copy_place_order(self, logged_session, var_manager):
        cloudOrderSend = var_manager.get_variable("cloudOrderSend")
        self.MT5cloudTrader_user_ids_3 = var_manager.get_variable("MT5cloudTrader_user_ids_3")

        request_data = {
            "traderList": [self.MT5cloudTrader_user_ids_3],
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
            json_data=request_data
        )

        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    @allure.story("复制下单场景")
    @allure.title("数据库校验-复制下单开仓数据")
    def test_copy_verify_open_db(self, var_manager, db_transaction):
        MT5cloudTrader_user_accounts_3 = var_manager.get_variable("MT5cloudTrader_user_accounts_3")
        sql = """
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
        params = ('0', MT5cloudTrader_user_accounts_3)

        db_data = self.query_database_with_time_with_timezone(
            db_transaction=db_transaction,
            sql=sql,
            params=params,
            time_field="fod.open_time"
        )

        trader_ordersend = var_manager.get_variable("trader_ordersend")
        if not db_data:
            pytest.fail("数据库查询结果为空，无法进行开仓数据校验")

        # 订单状态校验
        status = db_data[0]["status"]
        assert status in (0, 1), \
            f"订单状态应为0(处理中)或1(全部成功)，实际为: {status}"
        logger.info(f"复制下单开仓状态校验通过: {status}")

        # 结束手数校验
        min_lot_size = db_data[0]["min_lot_size"]
        endsize = trader_ordersend["endSize"]
        assert math.isclose(float(endsize), float(min_lot_size), rel_tol=1e-9, abs_tol=1e-9), \
            f'结束手数不匹配，预期: {endsize}, 实际: {min_lot_size}'
        logger.info(f"复制下单结束手数校验通过: {endsize}")

        # 开始手数校验
        max_lot_size = db_data[0]["max_lot_size"]
        startSize = trader_ordersend["startSize"]
        assert math.isclose(float(startSize), float(max_lot_size), rel_tol=1e-9, abs_tol=1e-9), \
            f'开始手数不匹配，预期: {startSize}, 实际: {max_lot_size}'
        logger.info(f"复制下单开始手数校验通过: {startSize}")

        # 总订单数量校验
        total_orders = db_data[0]["total_orders"]
        totalNum = trader_ordersend["totalNum"]
        assert math.isclose(float(totalNum), float(total_orders), rel_tol=1e-9), \
            f'总订单数量不匹配，预期: {totalNum}, 实际: {total_orders}'
        logger.info(f"总订单数量校验通过: {totalNum}")

        # 总手数与指令表校验
        total_lots = db_data[0]["total_lots"]
        totalSzie = trader_ordersend["totalSzie"]
        assert math.isclose(float(totalSzie), float(total_lots), rel_tol=1e-9, abs_tol=1e-9), \
            f'总手数与指令表不匹配，预期: {totalSzie}, 实际: {total_lots}'
        logger.info(f"复制下单总手数与指令表校验通过: {totalSzie}")

        # 总手数与订单详情校验
        size_sum = sum(record["size"] for record in db_data)
        assert math.isclose(float(totalSzie), float(size_sum), rel_tol=1e-9, abs_tol=1e-9), \
            f'总手数与订单详情不匹配，预期: {totalSzie}, 实际: {size_sum}'
        logger.info(f"复制下单总手数与订单详情校验通过: {totalSzie}")

    @allure.story("复制下单场景")
    @allure.title("云策略manager策略账号-复制下单平仓操作")
    def test_copy_close_order(self, logged_session, var_manager):
        MT5cloudTrader_user_ids_3 = var_manager.get_variable("MT5cloudTrader_user_ids_3")

        request_data = {
            "isCloseAll": 1,
            "intervalTime": 100,
            "traderList": [MT5cloudTrader_user_ids_3]
        }

        response = self.send_post_request(
            logged_session,
            '/bargain/masOrderClose',
            json_data=request_data
        )

        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "复制平仓响应msg字段应为success"
        )

    @allure.story("复制下单场景")
    @allure.title("数据库校验-复制下单平仓数据")
    def test_copy_verify_close_db(self, var_manager, db_transaction):
        MT5cloudTrader_user_accounts_3 = var_manager.get_variable("MT5cloudTrader_user_accounts_3")
        MT5cloudTrader_MT5vps_ids_2 = var_manager.get_variable("MT5cloudTrader_MT5vps_ids_2")

        sql = """
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
        params = ('1', MT5cloudTrader_user_accounts_3, MT5cloudTrader_MT5vps_ids_2)

        db_data = self.query_database_with_time_with_timezone(
            db_transaction=db_transaction,
            sql=sql,
            params=params,
            time_field="fod.close_time"
        )

        trader_ordersend = var_manager.get_variable("trader_ordersend")
        if not db_data:
            pytest.fail("数据库查询结果为空，无法进行平仓数据校验")

        # 平仓状态校验
        status = db_data[0]["status"]
        assert status in (0, 1), \
            f"平仓状态应为0(处理中)或1(全部成功)，实际为: {status}"
        logger.info(f"复制下单平仓状态校验通过: {status}")

        # 平仓总手数校验
        totalSzie = trader_ordersend["totalSzie"]
        size_sum = sum(record["size"] for record in db_data)
        assert math.isclose(float(totalSzie), float(size_sum), rel_tol=1e-9, abs_tol=1e-9), \
            f'平仓总手数不匹配，预期: {totalSzie}, 实际: {size_sum}'
        logger.info(f"复制下单平仓总手数校验通过: {totalSzie}")

        time.sleep(25)
