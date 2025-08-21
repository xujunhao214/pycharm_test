# lingkuan_723/tests/test_masOrderSend.py
import allure
import logging
import pytest
import time
from lingkuan_723.VAR.VAR import *
from lingkuan_723.conftest import var_manager
from lingkuan_723.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("VPS交易下单-分配下单")
class TestMasordersend(APITestBase):
    # ---------------------------
    # 账号管理-交易下单-VPS分配下单
    # ---------------------------
    @allure.title("跟账号管理-交易下单-VPS分配下单")
    def test_bargain_masOrderSend(self, api_session, var_manager, logged_session):
        # 1. 发送VPS分配下单请求
        global user_ids_1
        masOrderSend = var_manager.get_variable("masOrderSend")
        user_ids_1 = var_manager.get_variable("user_ids_1")
        data = {
            "traderList": [user_ids_1],
            "type": 0,
            "tradeType": 0,
            "symbol": masOrderSend["symbol"],
            "startSize": "0.10",
            "endSize": "1.00",
            "totalSzie": "1.00",
            "remark": "测试数据",
            "totalNum": 0
        }
        response = self.send_post_request(
            api_session,
            '/bargain/masOrderSend',
            json_data=data
        )

        # 2. 判断VPS分配下单是否成功
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # ---------------------------
    # 数据库校验-交易下单-VPS分配下单
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-交易开仓-主指令及订单详情数据检查")
    def test_dbquery_orderSend(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            user_accounts_1 = var_manager.get_variable("user_accounts_1")
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
                    foi.total_lots
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
                user_accounts_1,
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="foi.create_time",  # 按创建时间过滤
                time_range=MYSQL_TIME,  # 只查前后2分钟的数据
                timeout=WAIT_TIMEOUT,  # 最多等36秒
                poll_interval=POLL_INTERVAL,  # 每2秒查一次
                stable_period=STBLE_PERIOD,  # 新增：数据连续3秒不变则认为加载完成
                order_by="foi.create_time DESC"  # 按创建时间倒序
            )
        with allure.step("2. 数据校验"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            status = db_data[0]["status"]
            assert status in (0, 1), f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}"
            logging.info(f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}")

            min_lot_size = db_data[0]["min_lot_size"]
            endsize = trader_ordersend["endSize"]
            assert float(endsize) == float(min_lot_size), f'手数范围：结束手数是：{endsize}，实际是：{min_lot_size}'
            logging.info(f'手数范围：结束手数是：{endsize}，实际是：{min_lot_size}')

            max_lot_size = db_data[0]["max_lot_size"]
            startSize = trader_ordersend["startSize"]
            assert float(startSize) == float(max_lot_size), f'手数范围：开始手数是：{startSize}，实际是：{max_lot_size}'
            logging.info(f'手数范围：开始手数是：{startSize}，实际是：{max_lot_size}')

            total_lots = db_data[0]["total_lots"]
            totalSzie = trader_ordersend["totalSzie"]
            assert float(totalSzie) == float(total_lots), f'下单总手数是：{totalSzie}，实际是：{total_lots}'
            logging.info(f'下单总手数是：{totalSzie}，实际是：{total_lots}')

            totalSzie = trader_ordersend["totalSzie"]
            size = [record["size"] for record in db_data]
            total = sum(size)
            assert float(totalSzie) == float(
                total), f'下单总手数是：{totalSzie},订单详情总手数是：{total}'
            logging.info(f'下单总手数是：{totalSzie},订单详情总手数是：{total}')

    # ---------------------------
    # 账号管理-交易下单-平仓
    # ---------------------------
    @allure.title("跟账号管理-交易下单-平仓")
    def test_bargain_masOrderClose(self, api_session, var_manager, logged_session):
        # 1. 发送开仓请求
        data = {
            "isCloseAll": 1,
            "intervalTime": 100,
            "traderList": [user_ids_1]
        }
        response = self.send_post_request(
            api_session,
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

    # ---------------------------
    # 数据库校验-策略平仓-主指令及订单详情数据检查
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-交易平仓-主指令及订单详情数据检查")
    def test_dbquery_orderSendclose(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            user_accounts_1 = var_manager.get_variable("user_accounts_1")
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
                    foi.status
                FROM 
                    follow_order_detail fod
                INNER JOIN 
                    follow_order_instruct foi 
                ON 
                    foi.order_no = fod.close_no COLLATE utf8mb4_0900_ai_ci
                WHERE foi.operation_type = %s
                    AND fod.account = %s
                    """
            params = (
                '1',
                user_accounts_1,
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="foi.create_time",  # 按创建时间过滤
                time_range=MYSQL_TIME,  # 只查前后2分钟的数据
                timeout=WAIT_TIMEOUT,  # 最多等36秒
                poll_interval=POLL_INTERVAL,  # 每2秒查一次
                stable_period=STBLE_PERIOD,  # 新增：数据连续3秒不变则认为加载完成
                order_by="foi.create_time DESC"  # 按创建时间倒序
            )
        with allure.step("2. 数据校验"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            status = db_data[0]["status"]
            assert status in (0, 1), f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}"
            logging.info(f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}")

            totalSzie = trader_ordersend["totalSzie"]
            size = [record["size"] for record in db_data]
            total = sum(size)
            assert float(totalSzie) == float(
                total), f'下单总手数是：{totalSzie}，订单详情总手数是：{total}'
            logging.info(f'下单总手数是：{totalSzie}，订单详情总手数是：{total}')

        time.sleep(25)