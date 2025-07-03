# lingkuan_702/tests/test_masOrderSend.py
import time

import allure
import logging
import pytest
from lingkuan_702.VAR.VAR import *
from lingkuan_702.conftest import var_manager
from lingkuan_702.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("VPS交易下单-复制下单")
class TestMasordersendcopy(APITestBase):
    # ---------------------------
    # 账号管理-交易下单-VPS复制下单
    # ---------------------------
    @allure.title("跟账号管理-交易下单-VPS复制下单")
    def test_bargain_masOrderSend(self, api_session, var_manager, logged_session):
        # 1. 发送VPS复制下单请求
        global user_ids_1
        masOrderSend = var_manager.get_variable("masOrderSend")
        user_ids_1 = var_manager.get_variable("user_ids_1")
        data = {
            "traderList": [user_ids_1],
            "type": 0,
            "tradeType": 1,
            "intervalTime": 100,
            "symbol": masOrderSend["symbol"],
            "placedType": 0,
            "startSize": "0.10",
            "endSize": "1.00",
            "totalNum": "3",
            "totalSzie": "1.00",
            "remark": "测试数据"
        }
        response = self.send_post_request(
            api_session,
            '/bargain/masOrderSend',
            json_data=data,
            sleep_seconds=0
        )

        # 2. 判断VPS分配下单是否成功
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    @allure.title("数据库校验-VPS下单-下单指令")
    def test_dbbargain_masOrderSend(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否有下单"):
            masOrderSend = var_manager.get_variable("masOrderSend")
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")

            table_name = masOrderSend["table"]
            symbol = masOrderSend["symbol"]

            sql = f"""
            SELECT * 
            FROM {table_name} 
            WHERE symbol LIKE %s 
              AND master_order_status = %s 
              AND type = %s 
              AND min_lot_size = %s 
              AND max_lot_size = %s 
              AND remark = %s 
              AND total_lots = %s 
              AND trader_id = %s
            """
            params = (
                f"%{symbol}%",
                "0",
                masOrderSend["type"],
                masOrderSend["endSize"],
                masOrderSend["startSize"],
                masOrderSend["remark"],
                masOrderSend["totalSzie"],
                vps_addslave_id
            )

            db_data = self.wait_for_database_record(
                db_transaction,
                sql,
                params,
                time_field="create_time",
                time_range=MYSQL_TIME,
                timeout=WAIT_TIMEOUT,
                poll_interval=POLL_INTERVAL
            )

        with allure.step("2. 提取数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            order_no = db_data[0]["order_no"]
            logging.info(f"获取交易账号下单的订单号: {order_no}")
            var_manager.set_runtime_variable("order_no", order_no)

        with allure.step("3. 对数据进行校验"):
            operation_type = db_data[0]["operation_type"]
            assert operation_type == 0, f"操作类型operation_type应为0(下单)，实际状态为: {operation_type}"

            status = db_data[0]["status"]
            assert status in (0, 1), f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}"

    @allure.title("数据库校验-VPS分配下单-持仓检查")
    def test_dbquery_order_detail(self, var_manager, db_transaction):
        with allure.step("1. 根据下单指令仓库的order_no字段获取跟单账号订单数据"):
            order_no = var_manager.get_variable("order_no")
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            masOrderSend = var_manager.get_variable("masOrderSend")

            table_name = masOrderSend["table_detail"]
            symbol = masOrderSend["symbol"]

            sql = f"""
            SELECT * 
            FROM {table_name} 
            WHERE symbol LIKE %s 
              AND send_no = %s 
              AND type = %s 
              AND trader_id = %s
            """
            params = (
                f"%{symbol}%",
                order_no,
                masOrderSend["type"],
                vps_addslave_id
            )

            db_data = self.wait_for_database_record(
                db_transaction,
                sql,
                params,
                time_field="create_time",
                time_range=MYSQL_TIME
            )

        with allure.step("2. 校验数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")
            addsalve_size = [record["size"] for record in db_data]
            total = sum(addsalve_size)
            logging.info(f"手数: {addsalve_size}   手数总和: {total}")
            totalSzie = trader_ordersend["totalSzie"]
            assert float(total) == float(
                totalSzie), f"跟单总手数和下单的手数不相等 (实际: {total}, 预期: {totalSzie})"

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
    # 数据库校验-交易平仓-跟单平仓指令
    # ---------------------------
    @allure.title("数据库校验-交易平仓-跟单平仓指令")
    def test_dbquery_close_addsalve(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否有平仓指令"):
            masOrderSend = var_manager.get_variable("masOrderSend")
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            table_name = masOrderSend["table"]

            sql = f"""
            SELECT * 
            FROM {table_name} 
            WHERE cloud_type = %s
              AND trader_id = %s
              AND operation_type = %s
            """
            params = (
                "0",
                vps_addslave_id,
                "1"
            )

            # 使用智能等待查询
            db_data = self.wait_for_database_record(
                db_transaction,
                sql,
                params,
                time_field="create_time",
                time_range=MYSQL_TIME,
                timeout=WAIT_TIMEOUT,
                poll_interval=POLL_INTERVAL,
                order_by="create_time DESC"
            )

        with ((allure.step("2. 提取数据"))):
            close_send_nos = db_data[0]["order_no"]
            logging.info(f"平仓之后的跟单账号持仓订单号: {close_send_nos}")
            var_manager.set_runtime_variable("close_send_nos", close_send_nos)

    # ---------------------------
    # 数据库校验-交易平仓-持仓检查跟单账号数据
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-交易平仓-持仓检查跟单账号数据")
    def test_dbquery_addsalve_clsesdetail(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            user_accounts_1 = var_manager.get_variable("user_accounts_1")
            table_name = trader_ordersend["table_detail"]
            close_send_nos = var_manager.get_variable("close_send_nos")

            sql = f"""
                SELECT * 
                FROM {table_name} 
                WHERE source_user = %s
                  AND account = %s
                  AND close_status = %s
                  AND close_no = %s
                """
            params = (
                user_accounts_1,
                user_accounts_1,
                "1",
                close_send_nos

            )

            # 使用智能等待查询
            db_data = self.wait_for_database_record(
                db_transaction,
                sql,
                params,
                time_field="create_time",
                time_range=MYSQL_TIME,
                timeout=WAIT_TIMEOUT,
                poll_interval=POLL_INTERVAL,
                order_by="create_time DESC"
            )
        with allure.step("2. 校验数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            close_addsalve_size = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("close_addsalve_size", close_addsalve_size)
            total = sum(close_addsalve_size)
            logging.info(f"手数: {close_addsalve_size} 手数总和: {total}")
            totalSzie = trader_ordersend["totalSzie"]
            assert float(total) == float(
                totalSzie), f"跟单总手数和下单的手数不相等 (实际: {total}, 预期: {totalSzie})"

            time.sleep(90)
