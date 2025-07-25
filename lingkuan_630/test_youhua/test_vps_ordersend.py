# lingkuan_630/tests/test_vps_ordersend.py
import allure
import logging
import pytest
from lingkuan_630.VAR.VAR import *
from lingkuan_630.conftest import var_manager
from lingkuan_630.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("VPS策略下单-正常开仓平仓")
class TestVPSOrderSend(APITestBase):
    # ---------------------------
    # 跟单软件看板-VPS数据-策略开仓
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("跟单软件看板-VPS数据-策略开仓")
    def test_trader_orderSend(self, vps_api_session, var_manager, logged_session):
        # 1. 发送策略开仓请求
        trader_ordersend = var_manager.get_variable("trader_ordersend")
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        data = {
            "symbol": trader_ordersend["symbol"],
            "placedType": 0,
            "remark": trader_ordersend["remark"],
            "intervalTime": 100,
            "type": 0,
            "totalNum": trader_ordersend["totalNum"],
            "totalSzie": trader_ordersend["totalSzie"],
            "startSize": trader_ordersend["startSize"],
            "endSize": trader_ordersend["endSize"],
            "traderId": vps_trader_id
        }
        response = self.send_post_request(
            vps_api_session,
            '/subcontrol/trader/orderSend',
            json_data=data,
            sleep_seconds=3  # 不需要等待，由后续数据库查询处理
        )

        # 2. 验证响应状态码和内容
        self.assert_response_status(
            response,
            200,
            "策略开仓失败"
        )
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # ---------------------------
    # 数据库校验-策略开仓-策略开仓指令
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略开仓-策略开仓指令")
    def test_dbquery_orderSend(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否有策略开仓指令"):
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            trader_ordersend = var_manager.get_variable("trader_ordersend")

            table_name = trader_ordersend["table"]
            symbol = trader_ordersend["symbol"]

            sql = f"""
            SELECT * 
            FROM {table_name} 
            WHERE symbol LIKE %s 
              AND type = %s 
              AND min_lot_size = %s 
              AND max_lot_size = %s 
              AND remark = %s 
              AND total_lots = %s 
              AND total_orders = %s 
              AND trader_id = %s
            """
            params = (
                f"%{symbol}%",
                trader_ordersend["type"],
                trader_ordersend["endSize"],
                trader_ordersend["startSize"],
                trader_ordersend["remark"],
                trader_ordersend["totalSzie"],
                trader_ordersend["totalNum"],
                vps_trader_id
            )

            # 使用带时间范围的智能等待查询
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
            logging.info(f"获取策略账号下单的订单号: {order_no}")
            var_manager.set_runtime_variable("order_no", order_no)

        with allure.step("3. 对数据进行校验"):
            operation_type = db_data[0]["operation_type"]
            assert operation_type == 0, f"操作类型operation_type应为0(下单)，实际状态为: {operation_type}"

            status = db_data[0]["status"]
            assert status in (0, 1), f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}"

    # ---------------------------
    # 数据库校验-策略开仓-持仓检查
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略开仓-持仓检查主账号数据")
    def test_dbquery_order_detail(self, var_manager, db_transaction):
        with allure.step("1. 根据下单指令仓库的order_no字段获取订单详情"):
            order_no = var_manager.get_variable("order_no")
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            trader_ordersend = var_manager.get_variable("trader_ordersend")

            table_name = trader_ordersend["table_detail"]
            symbol = trader_ordersend["symbol"]

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
                trader_ordersend["type"],
                vps_trader_id
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

        with allure.step("2. 提取数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            order_nos = list(map(lambda x: x["order_no"], db_data))
            logging.info(f"持仓订单的订单号: {order_nos}")
            var_manager.set_runtime_variable("order_nos", order_nos)

        with allure.step("3. 校验数据"):
            addsalve_size = [record["size"] for record in db_data]
            logging.info(f"手数: {addsalve_size}")
            total = sum(addsalve_size)
            logging.info(f"手数总和: {total}")
            totalSzie = trader_ordersend["totalSzie"]
            assert float(total) == float(totalSzie), f"跟单总手数和下单的手数不相等 (实际: {total}, 预期: {totalSzie})"

    # ---------------------------
    # 数据库校验-策略开仓-持仓检查跟单账号数据
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略开仓-持仓检查跟单账号数据")
    def test_dbquery_addsalve_detail(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            vps_trader = var_manager.get_variable("vps_trader")
            add_Slave = var_manager.get_variable("add_Slave")
            table_name = trader_ordersend["table_detail"]
            symbol = trader_ordersend["symbol"]

            sql = f"""
                SELECT * 
                FROM {table_name} 
                WHERE symbol LIKE %s 
                  AND source_user = %s
                  AND account = %s
                """
            params = (
                f"%{symbol}%",
                vps_trader["account"],
                add_Slave["account"],
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

        with allure.step("2. 提取数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            send_nos = list(map(lambda x: x["send_no"], db_data))
            logging.info(f"持仓订单的订单号: {send_nos}")
            var_manager.set_runtime_variable("send_nos", send_nos)

        with allure.step("3. 校验数据"):
            addsalve_size = [record["size"] for record in db_data]
            logging.info(f"手数: {addsalve_size}")
            var_manager.set_runtime_variable("addsalve_size", addsalve_size)
            total = sum(addsalve_size)
            logging.info(f"手数总和: {total}")
            totalSzie = trader_ordersend["totalSzie"]
            assert float(total) == float(totalSzie), f"跟单总手数和下单的手数不相等 (实际: {total}, 预期: {totalSzie})"

    # ---------------------------
    # 数据库校验-策略开仓-跟单开仓指
    # ---------------------------
    @allure.title("数据库校验-策略开仓-跟单开仓指令")
    def test_dbquery_orderSend_addsalve(self, var_manager, db_transaction):
        with allure.step("1. 根据订单详情数据库数据，校验跟单指令数据是否正确"):
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            trader_ordersend = var_manager.get_variable("trader_ordersend")

            table_name = trader_ordersend["table"]
            symbol = trader_ordersend["symbol"]

            sql = f"""
                    SELECT * 
                    FROM {table_name} 
                    WHERE symbol LIKE %s 
                      AND instruction_type = %s
                      AND if_follow = %s
                      AND master_order_status = %s 
                      AND type = %s 
                      AND trader_id = %s
                    """
            params = (
                f"%{symbol}%",
                "2",
                "1",
                "0",
                trader_ordersend["type"],
                vps_trader_id,
            )

            # 使用智能等待查询
            db_data = self.wait_for_database_record(
                db_transaction,
                sql,
                params,
                time_field="create_time",
                time_range=MYSQL_TIME,
                timeout=WAIT_TIMEOUT,
                poll_interval=POLL_INTERVAL
            )

        with allure.step("2. 验证下单指令的跟单账号数据"):
            send_nos = var_manager.get_variable("send_nos")
            order_no = [record["order_no"] for record in db_data]
            assert set(send_nos) == set(order_no), f"订单详情的订单号{send_nos}和下单指令{order_no}的订单号不一致"

            addsalve_size = var_manager.get_variable("addsalve_size")
            true_total_lots = [record["true_total_lots"] for record in db_data]
            assert set(true_total_lots) == set(
                addsalve_size), f"订单详情的下单手数{addsalve_size}和下单指令{true_total_lots}的实际下单手数不一致"

    # ---------------------------
    # 跟单软件看板-VPS数据-策略平仓
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("跟单软件看板-VPS数据-策略平仓")
    def test_trader_orderclose(self, vps_api_session, var_manager, logged_session, db_transaction):
        # 1. 发送全平订单平仓请求
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        new_user = var_manager.get_variable("new_user")
        data = {
            "isCloseAll": 1,
            "intervalTime": 100,
            "traderId": vps_trader_id,
            "account": new_user["account"]
        }
        response = self.send_post_request(
            vps_api_session,
            '/subcontrol/trader/orderClose',
            json_data=data,
            sleep_seconds=3
        )

        # 2. 验证响应
        self.assert_response_status(
            response,
            200,
            "平仓失败"
        )
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # ---------------------------
    # 数据库校验-策略平仓-策略平仓主指令
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略平仓-策略平仓主指令")
    def test_dbquery_traderclose(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否有策略平仓指令"):
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            new_user = var_manager.get_variable("new_user")
            sql = f"""
                            SELECT * 
                            FROM follow_order_instruct 
                            WHERE master_order_status = %s 
                              AND trader_id = %s
                              AND if_follow = %s
                              AND instruction_type = %s
                            """
            params = (
                "0",
                vps_trader_id,
                "0",
                "0"
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

        with allure.step("2. 提取数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            order_no_close = db_data[0]["order_no"]
            logging.info(f"获取策略平仓的订单号: {order_no_close}")
            var_manager.set_runtime_variable("order_no_close", order_no_close)

    # ---------------------------
    # 数据库校验-策略平仓-平仓订单详情持仓检查
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略平仓-平仓订单详情持仓检查")
    def test_dbquery_closed_orderdetail(self, var_manager, db_transaction):
        with allure.step("1. 根据平仓指令仓库的order_no字段获取跟单账号订单数据"):
            order_no_close = var_manager.get_variable("order_no_close")
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            trader_ordersend = var_manager.get_variable("trader_ordersend")

            table_name = trader_ordersend["table_detail"]
            symbol = trader_ordersend["symbol"]

            sql = f"""
                SELECT * 
                FROM {table_name} 
                WHERE symbol LIKE %s 
                  AND close_no = %s 
                  AND type = %s 
                  AND trader_id = %s
                """
            params = (
                f"%{symbol}%",
                order_no_close,
                trader_ordersend["type"],
                vps_trader_id
            )

            # 使用智能等待查询
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

            order_nos = list(map(lambda x: x["order_no"], db_data))
            logging.info(f"持仓订单的订单号: {order_nos}")
            var_manager.set_runtime_variable("order_nos", order_nos)

        with allure.step("3. 校验数据"):
            addsalve_size = [record["size"] for record in db_data]
            logging.info(f"手数: {addsalve_size}")
            total = sum(addsalve_size)
            logging.info(f"手数总和: {total}")
            totalSzie = trader_ordersend["totalSzie"]
            assert float(total) == float(totalSzie), f"跟单总手数和下单的手数不相等 (实际: {total}, 预期: {totalSzie})"

    # ---------------------------
    # 数据库校验-策略平仓-持仓检查跟单账号数据
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略平仓-持仓检查跟单账号数据")
    def test_dbquery_addsalve_clsesdetail(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            vps_trader = var_manager.get_variable("vps_trader")
            add_Slave = var_manager.get_variable("add_Slave")
            table_name = trader_ordersend["table_detail"]
            symbol = trader_ordersend["symbol"]

            sql = f"""
                SELECT * 
                FROM {table_name} 
                WHERE symbol LIKE %s 
                  AND source_user = %s
                  AND account = %s
                  AND close_status = %s
                """
            params = (
                f"%{symbol}%",
                vps_trader["account"],
                add_Slave["account"],
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
        with (allure.step("2. 提取数据")):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            close_send_nos = [record["send_no"] for record in db_data]
            logging.info(f"持仓订单的订单号: {close_send_nos}")
            var_manager.set_runtime_variable("send_nos", close_send_nos)
        with allure.step("3. 校验数据"):
            close_addsalve_size = [record["size"] for record in db_data]
            logging.info(f"手数: {close_addsalve_size}")
            var_manager.set_runtime_variable("close_addsalve_size", close_addsalve_size)
            total = sum(close_addsalve_size)
            logging.info(f"手数总和: {total}")
            totalSzie = trader_ordersend["totalSzie"]
            assert float(total) == float(totalSzie), f"跟单总手数和下单的手数不相等 (实际: {total}, 预期: {totalSzie})"

    # ---------------------------
    # 数据库校验-策略平仓-跟单平仓指令
    # ---------------------------
    @allure.title("数据库校验-策略平仓-跟单平仓指令")
    def test_dbquery_close_addsalve(self, var_manager, db_transaction):
        with allure.step("1. 根据订单详情数据库数据，校验跟单指令数据是否正确"):
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            trader_ordersend = var_manager.get_variable("trader_ordersend")

            table_name = trader_ordersend["table"]
            symbol = trader_ordersend["symbol"]

            sql = f"""
                    SELECT * 
                    FROM {table_name} 
                    WHERE symbol LIKE %s 
                      AND instruction_type = %s
                      AND if_follow = %s
                      AND master_order_status = %s 
                      AND type = %s 
                      AND trader_id = %s
                    """
            params = (
                f"%{symbol}%",
                "2",
                "1",
                "1",
                trader_ordersend["type"],
                vps_trader_id,
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

        with allure.step("2. 验证下单指令的跟单账号数据"):
            close_send_nos = var_manager.get_variable("close_send_nos")
            order_no = [record["order_no"] for record in db_data]
            assert set(close_send_nos) == set(
                order_no), f"订单详情的订单号{close_send_nos}和平仓指令{order_no}的订单号不一致"

            close_addsalve_size = var_manager.get_variable("close_addsalve_size")
            true_total_lots = [record["true_total_lots"] for record in db_data]
            assert set(true_total_lots) == set(
                close_addsalve_size), f"订单详情的平仓手数{close_addsalve_size}和平仓指令{true_total_lots}的实际平仓手数不一致"
