# lingkuan_youhua9/tests/test_masOrderSend.py
import allure
import logging
import pytest
from lingkuan_youhua9.VAR.VAR import *
from lingkuan_youhua9.conftest import var_manager
from lingkuan_youhua9.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("VPS交易下单")
class TestMasordersend(APITestBase):
    # ---------------------------
    # 账号管理-交易下单-VPS分配下单
    # ---------------------------
    @allure.title("跟账号管理-交易下单-VPS分配下单")
    def test_bargain_masOrderSend(self, api_session, var_manager, logged_session):
        # 1. 发送VPS分配下单请求
        masOrderSend = var_manager.get_variable("masOrderSend")
        data = {
            "traderList": [3648],
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
            vps_trader_id = var_manager.get_variable("vps_trader_id")

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
                vps_trader_id
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

        with allure.step("2. 判断是否下单成功"):
            # 定义验证函数
            def verify_close_status():
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")
                order_no = db_data[0]["order_no"]
                logging.info(f"获取策略账号下单的订单号: {order_no}")
                var_manager.set_runtime_variable("order_no", order_no)

                status = db_data[0]["status"]
                if status not in (0, 1):
                    pytest.fail(f"下单失败status状态应该是2，实际状态为: {status}")

            # 执行验证
            try:
                verify_close_status()
                allure.attach("平仓状态验证通过", "成功详情", allure.attachment_type.TEXT)
            except AssertionError as e:
                allure.attach(str(e), "平仓状态验证失败", allure.attachment_type.TEXT)
                raise

    @allure.title("数据库校验-VPS分配下单-持仓检查")
    def test_dbquery_order_detail(self, var_manager, db_transaction):
        with allure.step("1. 根据下单指令仓库的order_no字段获取跟单账号订单数据"):
            order_no = var_manager.get_variable("order_no")
            vps_trader_id = var_manager.get_variable("vps_trader_id")
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
                vps_trader_id
            )

            db_data = self.wait_for_database_record(
                db_transaction,
                sql,
                params,
                time_field="create_time",
                time_range=MYSQL_TIME
            )

            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            order_nos = list(map(lambda x: x["order_no"], db_data))
            logging.info(f"持仓订单的订单号: {order_nos}")
            var_manager.set_runtime_variable("order_nos", order_nos)

            addsalve_size = [record["size"] for record in db_data]
            logging.info(f"手数: {addsalve_size}")
            total = sum(addsalve_size)
            logging.info(f"手数总和: {total}")

            # 验证手数一致性
            if float(total) != float(masOrderSend["totalSzie"]):
                error_msg = f"跟单总手数和下单的手数不相等 (实际: {total}, 预期: {masOrderSend['totalSzie']})"
                allure.attach(error_msg, "手数验证失败", allure.attachment_type.TEXT)
                pytest.fail(error_msg)
            else:
                allure.attach("跟单总手数和下单的手数相等", "成功详情", allure.attachment_type.TEXT)

    # ---------------------------
    # 账号管理-交易下单-平仓
    # ---------------------------
    @allure.title("跟账号管理-交易下单-平仓")
    def test_bargain_masOrderClose(self, api_session, var_manager, logged_session):
        # 1. 发送开仓请求
        data = {
            "isCloseAll": 1,
            "intervalTime": 100,
            "traderList": [3648]
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

    @allure.title("数据库校验-交易下单-平仓指令")
    def test_dbbargain_masOrderClose(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否有平仓指令"):
            masOrderSend = var_manager.get_variable("masOrderSend")
            vps_trader_id = var_manager.get_variable("vps_trader_id")

            table_name = masOrderSend["table"]
            symbol = masOrderSend["symbol"]

            sql = f"""
            SELECT * 
            FROM {table_name} 
            WHERE symbol LIKE %s 
              AND master_order_status = %s 
              AND type = %s 
              AND trader_id = %s
            """
            params = (
                f"%{symbol}%",
                "1",
                masOrderSend["type"],
                vps_trader_id
            )

            db_data = self.wait_for_database_record(
                db_transaction,
                sql,
                params,
                time_field="create_time",
                time_range=MYSQL_TIME
            )

        with allure.step("2. 判断是否平仓成功"):
            # 定义验证函数
            def verify_close_status():
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")
                master_order_status = db_data[0]["master_order_status"]
                if master_order_status != 1:
                    pytest.fail(f"平仓后订单状态master_order_status应为1，实际状态为: {master_order_status}")

            # 执行验证
            try:
                verify_close_status()
                allure.attach("平仓状态验证通过", "成功详情", allure.attachment_type.TEXT)
            except AssertionError as e:
                allure.attach(str(e), "平仓状态验证失败", allure.attachment_type.TEXT)
                raise
