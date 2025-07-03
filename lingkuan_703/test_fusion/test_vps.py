# lingkuan_703/tests/test_vps_ordersend.py
import time

import allure
import logging
import pytest
from lingkuan_703.VAR.VAR import *
from lingkuan_703.conftest import var_manager
from lingkuan_703.commons.api_base import APITestBase  # 导入基础类

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
            total = sum(addsalve_size)
            logging.info(f"手数: {addsalve_size}   手数总和: {total}")
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
            var_manager.set_runtime_variable("addsalve_size", addsalve_size)
            total = sum(addsalve_size)
            logging.info(f"手数: {addsalve_size}    手数总和: {total}")
            totalSzie = trader_ordersend["totalSzie"]
            assert float(total) == float(totalSzie), f"跟单总手数和下单的手数不相等 (实际: {total}, 预期: {totalSzie})"

    # ---------------------------
    # 数据库校验-策略开仓-跟单开仓指令
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
            logging.info(f"订单详情的订单号：{send_nos}下单指令的订单号：{order_no}")
            self.assert_list_equal_ignore_order(
                send_nos,
                order_no,
                f"订单详情的订单号：{send_nos}和平仓指令的订单号：{order_no}不一致"
            )

            addsalve_size = var_manager.get_variable("addsalve_size")
            true_total_lots = [record["true_total_lots"] for record in db_data]
            logging.info(f"订单详情的下单手数:{addsalve_size} 下单指令的实际下单手数:{true_total_lots}")
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
        vps_trader_isCloseAll = var_manager.get_variable("vps_trader_isCloseAll")
        data = {
            "isCloseAll": 1,
            "intervalTime": 100,
            "traderId": vps_trader_id,
            "account": vps_trader_isCloseAll["account"]
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
            vps_trader_isCloseAll = var_manager.get_variable("vps_trader_isCloseAll")
            table_name = vps_trader_isCloseAll["table"]
            sql = f"""
                            SELECT * 
                            FROM {table_name} 
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
        with allure.step("1. 检查订单详情界面的数据"):
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
            total = sum(addsalve_size)
            logging.info(f"手数: {addsalve_size} 手数总和: {total}")
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
                "1",
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

            close_send_nos = [record["close_no"] for record in db_data]
            logging.info(f"平仓之后的跟单账号持仓订单号: {close_send_nos}")
            var_manager.set_runtime_variable("close_send_nos", close_send_nos)
        with allure.step("3. 校验数据"):
            close_addsalve_size = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("close_addsalve_size", close_addsalve_size)
            total = sum(close_addsalve_size)
            logging.info(f"手数: {close_addsalve_size} 手数总和: {total}")
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
                      AND operation_type = %s
                    """
            params = (
                f"%{symbol}%",
                "2",
                "1",
                "1",
                trader_ordersend["type"],
                vps_trader_id,
                "1",
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
            order_no_close = [record["order_no"] for record in db_data]
            logging.info(f"订单详情的订单号：{close_send_nos} 平仓指令的订单号：{order_no_close}")
            var_manager.set_runtime_variable("order_no_close", order_no_close)
            self.assert_list_equal_ignore_order(
                close_send_nos,
                order_no_close,
                f"订单详情的订单号：{close_send_nos}和平仓指令的订单号：{order_no_close}不一致"
            )

            close_addsalve_size = var_manager.get_variable("close_addsalve_size")
            true_total_lots = [record["true_total_lots"] for record in db_data]
            logging.info(f"订单详情的平仓手数:{close_addsalve_size} 平仓指令的实际平仓手数:{true_total_lots}")
            assert set(true_total_lots) == set(
                close_addsalve_size), f"订单详情的平仓手数{close_addsalve_size}和平仓指令{true_total_lots}的实际平仓手数不一致"

            time.sleep(90)


@allure.feature("VPS策略下单-漏平")
class TestLeakagelevel(APITestBase):
    # ---------------------------
    # 跟单软件看板-VPS数据-修改跟单账号
    # ---------------------------
    @allure.title("跟单软件看板-VPS数据-修改跟单账号（漏平）")
    def test_update_slave(self, vps_api_session, var_manager, logged_session, db_transaction):
        # 1. 发送修改策略账号请求
        add_Slave = var_manager.get_variable("add_Slave")
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        vps_addslave_id = var_manager.get_variable("vps_addslave_id")
        # 平仓给关闭followClose：0
        data = {
            "traderId": vps_trader_id,
            "platform": add_Slave["platform"],
            "account": add_Slave["account"],
            "password": add_Slave["password"],
            "remark": add_Slave["remark"],
            "followDirection": 0,
            "followMode": 1,
            "remainder": 0,
            "followParam": 1,
            "placedType": 0,
            "templateId": 35,
            "followStatus": 1,
            "followOpen": 1,
            "followClose": 0,
            "followRep": 0,
            "fixedComment": add_Slave["fixedComment"],
            "commentType": 2,
            "digits": 0,
            "cfd": "@",
            "forex": "",
            "abRemark": "",
            "id": vps_addslave_id
        }
        response = self.send_post_request(
            vps_api_session,
            '/subcontrol/follow/updateSlave',
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "修改跟单账号失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    @allure.title("数据库校验-VPS数据-修改跟单账号是否成功")
    def test_dbquery_updateslave(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否修改成功"):
            follow_trader_subscribe = var_manager.get_variable("follow_trader_subscribe")
            sql = f"SELECT * FROM {follow_trader_subscribe['table']} WHERE slave_account = %s"
            params = (follow_trader_subscribe["slave_account"],)

            db_data = self.query_database(
                db_transaction,
                sql,
                params
            )
        with allure.step("2. 对数据进行校验"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            follow_close = db_data[0]["follow_close"]
            assert follow_close == 0, f"数据修改失败follow_close数据应该是0，实际是：{follow_close}"

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
            total = sum(addsalve_size)
            logging.info(f"手数: {addsalve_size}   手数总和: {total}")
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
            var_manager.set_runtime_variable("addsalve_size", addsalve_size)
            total = sum(addsalve_size)
            logging.info(f"手数: {addsalve_size}    手数总和: {total}")
            totalSzie = trader_ordersend["totalSzie"]
            assert float(total) == float(totalSzie), f"跟单总手数和下单的手数不相等 (实际: {total}, 预期: {totalSzie})"

    # ---------------------------
    # 数据库校验-策略开仓-跟单开仓指令
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
            logging.info(f"订单详情的订单号：{send_nos}下单指令的订单号：{order_no}")
            self.assert_list_equal_ignore_order(
                send_nos,
                order_no,
                f"订单详情的订单号：{send_nos}和平仓指令的订单号：{order_no}不一致"
            )

            addsalve_size = var_manager.get_variable("addsalve_size")
            true_total_lots = [record["true_total_lots"] for record in db_data]
            logging.info(f"订单详情的下单手数:{addsalve_size} 下单指令的实际下单手数:{true_total_lots}")
            assert set(true_total_lots) == set(
                addsalve_size), f"订单详情的下单手数{addsalve_size}和下单指令{true_total_lots}的实际下单手数不一致"

    # ---------------------------
    # 跟单软件看板-VPS数据-策略平仓
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("跟单软件看板-VPS数据-策略平仓-出现漏平")
    def test_trader_orderclose(self, vps_api_session, var_manager, logged_session, db_transaction):
        # 1. 发送全平订单平仓请求
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        vps_trader_isCloseAll = var_manager.get_variable("vps_trader_isCloseAll")
        data = {
            "isCloseAll": 1,
            "intervalTime": 100,
            "traderId": vps_trader_id,
            "account": vps_trader_isCloseAll["account"]
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
            vps_trader_isCloseAll = var_manager.get_variable("vps_trader_isCloseAll")
            table_name = vps_trader_isCloseAll["table"]
            sql = f"""
                            SELECT * 
                            FROM {table_name} 
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
        with allure.step("1. 检查订单详情界面的数据"):
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
            total = sum(addsalve_size)
            logging.info(f"手数: {addsalve_size} 手数总和: {total}")
            totalSzie = trader_ordersend["totalSzie"]
            assert float(total) == float(totalSzie), f"跟单总手数和下单的手数不相等 (实际: {total}, 预期: {totalSzie})"

    # ---------------------------
    # 数据库校验-策略平仓-检查平仓订单是否出现漏平
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略平仓-检查平仓订单是否出现漏平")
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
        with allure.step("2. 校验数据"):
            close_status = db_data[0]["close_status"]
            logging.info(f"出现漏平，平仓状态应该是0，实际是：{close_status}")
            assert close_status == 0, f"出现漏平，平仓状态应该是0，实际是：{close_status}"

            close_remark = db_data[0]["close_remark"]
            logging.info(f"出现漏平，平仓异常信息应该是未开通平仓状态，实际是：{close_remark}")
            assert close_remark == "未开通平仓状态", f"出现漏平，平仓异常信息应该是未开通平仓状态，实际是：{close_remark}"

    # ---------------------------
    # 跟单软件看板-VPS数据-修改跟单账号
    # ---------------------------
    @allure.title("跟单软件看板-VPS数据-修改跟单账号（漏平）")
    def test_update_slave2(self, vps_api_session, var_manager, logged_session, db_transaction):
        # 1. 发送修改策略账号请求
        add_Slave = var_manager.get_variable("add_Slave")
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        vps_addslave_id = var_manager.get_variable("vps_addslave_id")
        # 平仓给开启followOpen：1
        data = {
            "traderId": vps_trader_id,
            "platform": add_Slave["platform"],
            "account": add_Slave["account"],
            "password": add_Slave["password"],
            "remark": add_Slave["remark"],
            "followDirection": 0,
            "followMode": 1,
            "remainder": 0,
            "followParam": 1,
            "placedType": 0,
            "templateId": 35,
            "followStatus": 1,
            "followOpen": 1,
            "followClose": 1,
            "followRep": 0,
            "fixedComment": add_Slave["fixedComment"],
            "commentType": 2,
            "digits": 0,
            "cfd": "@",
            "forex": "",
            "abRemark": "",
            "id": vps_addslave_id
        }
        response = self.send_post_request(
            vps_api_session,
            '/subcontrol/follow/updateSlave',
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "修改跟单账号失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    @allure.title("数据库校验-VPS数据-修改跟单账号是否成功")
    def test_dbquery_updateslave2(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否修改成功"):
            follow_trader_subscribe = var_manager.get_variable("follow_trader_subscribe")
            sql = f"SELECT * FROM {follow_trader_subscribe['table']} WHERE slave_account = %s ORDER BY create_time DESC"
            params = (follow_trader_subscribe["slave_account"],)

            db_data = self.wait_for_database_record(
                db_transaction,
                sql,
                params,
                timeout=WAIT_TIMEOUT,
                poll_interval=POLL_INTERVAL
            )

        with allure.step("2. 对数据进行校验"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            follow_close = db_data[0]["follow_close"]
            assert follow_close == 1, f"数据修改失败follow_close数据应该是1，实际是：{follow_close}"

    @allure.title("跟单软件看板-VPS数据-修改完之后进行平仓补全")
    def test_follow_repairSend2(self, vps_api_session, var_manager, logged_session):
        with allure.step("1. 发送平仓补全请求"):
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            data = {
                "type": 2,
                "masterId": vps_trader_id,
                "slaveId": vps_addslave_id
            }
            response = self.send_post_request(
                vps_api_session,
                '/subcontrol/follow/repairSend',
                json_data=data
            )

        with allure.step("2. 关仓成功"):
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

    # ---------------------------
    # 数据库校验-策略平仓-持仓检查跟单账号数据
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略平仓-持仓检查跟单账号数据")
    def test_dbquery_addsalve_clsesdetail2(self, var_manager, db_transaction):
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
        with (allure.step("2. 提取数据")):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            close_send_nos = [record["close_no"] for record in db_data]
            logging.info(f"平仓之后的跟单账号持仓订单号: {close_send_nos}")
            var_manager.set_runtime_variable("close_send_nos", close_send_nos)
        with allure.step("3. 校验数据"):
            close_addsalve_size = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("close_addsalve_size", close_addsalve_size)
            total = sum(close_addsalve_size)
            logging.info(f"手数: {close_addsalve_size} 手数总和: {total}")
            totalSzie = trader_ordersend["totalSzie"]
            assert float(total) == float(
                totalSzie), f"跟单总手数和下单的手数不相等 (实际: {total}, 预期: {totalSzie})"

            close_status = db_data[0]["close_status"]
            logging.info(f"漏平已修复，平仓状态应该是1，实际是：{close_status}")
            assert close_status == 1, f"漏平已修复，平仓状态应该是1，实际是：{close_status}"

            close_remark = db_data[0]["close_remark"]
            logging.info(f"漏平已修复，备注信息是补单成功，实际是：{close_remark}")
            assert close_remark == "补单成功", f"漏平已修复，备注信息是补单成功，实际是：{close_remark}"

    # ---------------------------
    # 数据库校验-策略平仓-跟单平仓指令
    # ---------------------------
    @allure.title("数据库校验-策略平仓-跟单平仓指令")
    def test_dbquery_close_addsalve2(self, var_manager, db_transaction):
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
                      AND operation_type = %s
                    """
            params = (
                f"%{symbol}%",
                "2",
                "1",
                "1",
                trader_ordersend["type"],
                vps_trader_id,
                "1",
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
            order_no_close = [record["order_no"] for record in db_data]
            logging.info(f"订单详情的订单号：{close_send_nos} 平仓指令的订单号：{order_no_close}")
            var_manager.set_runtime_variable("order_no_close", order_no_close)
            self.assert_list_equal_ignore_order(
                close_send_nos,
                order_no_close,
                f"订单详情的订单号：{close_send_nos}和平仓指令的订单号：{order_no_close}不一致"
            )

            close_addsalve_size = var_manager.get_variable("close_addsalve_size")
            true_total_lots = [record["true_total_lots"] for record in db_data]
            logging.info(f"订单详情的平仓手数:{close_addsalve_size} 平仓指令的实际平仓手数:{true_total_lots}")
            assert set(true_total_lots) == set(
                close_addsalve_size), f"订单详情的平仓手数{close_addsalve_size}和平仓指令{true_total_lots}的实际平仓手数不一致"

            time.sleep(90)


@allure.feature("VPS策略下单-漏开")
class TestLeakageopen(APITestBase):
    # ---------------------------
    # 跟单软件看板-VPS数据-修改跟单账号
    # ---------------------------
    @allure.title("跟单软件看板-VPS数据-修改跟单账号（漏开）")
    def test_update_slave(self, vps_api_session, var_manager, logged_session, db_transaction):
        # 1. 发送修改策略账号请求
        add_Slave = var_manager.get_variable("add_Slave")
        vps_addslave_id = var_manager.get_variable("vps_addslave_id")
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        # 开仓给关闭followOpen：0
        data = {
            "traderId": vps_trader_id,
            "platform": add_Slave["platform"],
            "account": add_Slave["account"],
            "password": add_Slave["password"],
            "remark": add_Slave["remark"],
            "followDirection": 0,
            "followMode": 1,
            "remainder": 0,
            "followParam": 1,
            "placedType": 0,
            "templateId": 35,
            "followStatus": 1,
            "followOpen": 0,
            "followClose": 1,
            "followRep": 0,
            "fixedComment": add_Slave["fixedComment"],
            "commentType": 2,
            "digits": 0,
            "cfd": "@",
            "forex": "",
            "abRemark": "",
            "id": vps_addslave_id
        }
        response = self.send_post_request(
            vps_api_session,
            '/subcontrol/follow/updateSlave',
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "修改跟单账号失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    @allure.title("数据库校验-VPS数据-修改跟单账号是否成功")
    def test_dbquery_updateslave(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否修改成功"):
            follow_trader_subscribe = var_manager.get_variable("follow_trader_subscribe")

            db_data = self.wait_for_database_record(
                db_transaction,
                f"SELECT * FROM {follow_trader_subscribe['table']} WHERE slave_account = %s",
                (follow_trader_subscribe["slave_account"],),
                timeout=WAIT_TIMEOUT,
                poll_interval=POLL_INTERVAL
            )
        with allure.step("2. 对数据进行校验"):
            follow_open = db_data[0]["follow_open"]
            assert follow_open == 0, f"follow_open的状态应该是0，实际是：{follow_open}"

    # ---------------------------
    # 跟单软件看板-VPS数据-策略开仓-出现漏单
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("跟单软件看板-VPS数据-策略开仓-出现漏单")
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
            total = sum(addsalve_size)
            logging.info(f"手数: {addsalve_size}   手数总和: {total}")
            totalSzie = trader_ordersend["totalSzie"]
            assert float(total) == float(totalSzie), f"跟单总手数和下单的手数不相等 (实际: {total}, 预期: {totalSzie})"

    # ---------------------------
    # 数据库校验-策略开仓-跟单开仓指令
    # ---------------------------
    @allure.title("数据库校验-策略开仓-跟单开仓指令-根据status状态发现有漏单")
    def test_dbquery_orderSend_addsalve(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否有跟单开仓指令"):
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            trader_ordersend = var_manager.get_variable("trader_ordersend")

            table_name = trader_ordersend["table"]
            symbol = trader_ordersend["symbol"]

            sql = f"""
                SELECT * 
                FROM {table_name} 
                WHERE symbol LIKE %s 
                  AND instruction_type = %s 
                  AND master_order_status = %s 
                  AND type = %s 
                  AND trader_id = %s
                """
            params = (
                f"%{symbol}%",
                "2",
                "0",
                trader_ordersend["type"],
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
        with allure.step("2. 对订单状态进行校验"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")
            status = db_data[0]["status"]
            assert status == 2, f"跟单失败，跟单状态status应该是2，实际是：{status}"

    # ---------------------------
    # 跟单软件看板-VPS数据-策略开仓-一键补全
    # ---------------------------
    @allure.title("跟单软件看板-VPS数据-开仓补全")
    def test_follow_repairSend(self, vps_api_session, var_manager, logged_session):
        with allure.step("1. 发送开仓补全请求"):
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            data = {
                "type": 2,
                "masterId": vps_trader_id,
                "slaveId": vps_addslave_id
            }
            response = self.send_post_request(
                vps_api_session,
                '/subcontrol/follow/repairSend',
                json_data=data
            )

        with allure.step("2. 没有开仓，需要提前开仓才可以补全"):
            self.assert_json_value(
                response,
                "$.msg",
                "请开启补仓开关",
                "响应msg字段应为'请开启补仓开关'"
            )

    # ---------------------------
    # 跟单软件看板-VPS数据-修改跟单账号
    # ---------------------------
    @allure.title("跟单软件看板-VPS数据-修改跟单账号")
    def test_update_slave2(self, vps_api_session, var_manager, logged_session, db_transaction):
        # 1. 发送修改策略账号请求
        add_Slave = var_manager.get_variable("add_Slave")
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        vps_addslave_id = var_manager.get_variable("vps_addslave_id")
        # 开仓给开启followOpen：1
        data = {
            "traderId": vps_trader_id,
            "platform": add_Slave["platform"],
            "account": add_Slave["account"],
            "password": add_Slave["password"],
            "remark": add_Slave["remark"],
            "followDirection": 0,
            "followMode": 1,
            "remainder": 0,
            "followParam": 1,
            "placedType": 0,
            "templateId": 35,
            "followStatus": 1,
            "followOpen": 1,
            "followClose": 1,
            "followRep": 0,
            "fixedComment": add_Slave["fixedComment"],
            "commentType": 2,
            "digits": 0,
            "cfd": "@",
            "forex": "",
            "abRemark": "",
            "id": vps_addslave_id
        }
        response = self.send_post_request(
            vps_api_session,
            '/subcontrol/follow/updateSlave',
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "修改跟单账号失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    @allure.title("数据库校验-VPS数据-修改跟单账号是否成功")
    def test_dbquery_updateslave2(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否修改成功"):
            follow_trader_subscribe = var_manager.get_variable("follow_trader_subscribe")
            sql = f"SELECT * FROM {follow_trader_subscribe['table']} WHERE slave_account = %s"
            params = (follow_trader_subscribe["slave_account"],)

            db_data = self.query_database(
                db_transaction,
                sql,
                params
            )

        with allure.step("2. 对数据进行校验"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")
            follow_open = db_data[0]["follow_open"]
            assert follow_open == 1, f"数据修改失败，数据follow_openy应该是1，实际是：{follow_open}"

    @allure.title("跟单软件看板-VPS数据-修改完之后进行开仓补全")
    def test_follow_repairSend2(self, vps_api_session, var_manager, logged_session):
        with allure.step("1. 发送开仓补全请求"):
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            data = {
                "type": 2,
                "masterId": vps_trader_id,
                "slaveId": vps_addslave_id
            }
            response = self.send_post_request(
                vps_api_session,
                '/subcontrol/follow/repairSend',
                json_data=data
            )

        with allure.step("2. 补仓成功"):
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

    # ---------------------------
    # 数据库校验-策略开仓-持仓检查跟单账号数据
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略开仓-补开之后检查数据")
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
            var_manager.set_runtime_variable("addsalve_size", addsalve_size)
            total = sum(addsalve_size)
            logging.info(f"手数: {addsalve_size}    手数总和: {total}")
            totalSzie = trader_ordersend["totalSzie"]
            assert float(total) == float(totalSzie), f"跟单总手数和下单的手数不相等 (实际: {total}, 预期: {totalSzie})"

    # ---------------------------
    # 数据库校验-策略开仓-跟单开仓指令
    # ---------------------------
    @allure.title("数据库校验-策略开仓-跟单开仓指令")
    def test_dbquery_orderSend_addsalve2(self, var_manager, db_transaction):
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
            logging.info(f"订单详情的订单号：{send_nos}下单指令的订单号：{order_no}")
            self.assert_list_equal_ignore_order(
                send_nos,
                order_no,
                f"订单详情的订单号：{send_nos}和平仓指令的订单号：{order_no}不一致"
            )

            addsalve_size = var_manager.get_variable("addsalve_size")
            true_total_lots = [record["true_total_lots"] for record in db_data]
            logging.info(f"订单详情的下单手数:{addsalve_size} 下单指令的实际下单手数:{true_total_lots}")
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
        vps_trader_isCloseAll = var_manager.get_variable("vps_trader_isCloseAll")
        data = {
            "isCloseAll": 1,
            "intervalTime": 100,
            "traderId": vps_trader_id,
            "account": vps_trader_isCloseAll["account"]
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
            vps_trader_isCloseAll = var_manager.get_variable("vps_trader_isCloseAll")
            table_name = vps_trader_isCloseAll["table"]
            sql = f"""
                            SELECT * 
                            FROM {table_name} 
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
        with allure.step("1. 检查订单详情界面的数据"):
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
            total = sum(addsalve_size)
            logging.info(f"手数: {addsalve_size} 手数总和: {total}")
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
                "1",
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

            close_send_nos = [record["close_no"] for record in db_data]
            logging.info(f"平仓之后的跟单账号持仓订单号: {close_send_nos}")
            var_manager.set_runtime_variable("close_send_nos", close_send_nos)
        with allure.step("3. 校验数据"):
            close_addsalve_size = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("close_addsalve_size", close_addsalve_size)
            total = sum(close_addsalve_size)
            logging.info(f"手数: {close_addsalve_size} 手数总和: {total}")
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
                      AND operation_type = %s
                    """
            params = (
                f"%{symbol}%",
                "2",
                "1",
                "1",
                trader_ordersend["type"],
                vps_trader_id,
                "1",
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
            order_no_close = [record["order_no"] for record in db_data]
            logging.info(f"订单详情的订单号：{close_send_nos} 平仓指令的订单号：{order_no_close}")
            var_manager.set_runtime_variable("order_no_close", order_no_close)
            self.assert_list_equal_ignore_order(
                close_send_nos,
                order_no_close,
                f"订单详情的订单号：{close_send_nos}和平仓指令的订单号：{order_no_close}不一致"
            )

            close_addsalve_size = var_manager.get_variable("close_addsalve_size")
            true_total_lots = [record["true_total_lots"] for record in db_data]
            logging.info(f"订单详情的平仓手数:{close_addsalve_size} 平仓指令的实际平仓手数:{true_total_lots}")
            assert set(true_total_lots) == set(
                close_addsalve_size), f"订单详情的平仓手数{close_addsalve_size}和平仓指令{true_total_lots}的实际平仓手数不一致"

            time.sleep(90)


@allure.feature("VPS交易下单-分配下单")
class TestMasordersend(APITestBase):
    # ---------------------------
    # 账号管理-交易下单-VPS分配下单
    # ---------------------------
    @allure.title("跟账号管理-交易下单-VPS分配下单")
    def test_bargain_masOrderSend(self, api_session, var_manager, logged_session):
        # 1. 发送VPS分配下单请求
        global trader_user_id
        masOrderSend = var_manager.get_variable("masOrderSend")
        trader_user_id = var_manager.get_variable("trader_user_id")
        data = {
            "traderList": [trader_user_id],
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
            "traderList": [trader_user_id]
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
    # 数据库校验-交易平仓-持仓检查跟单账号数据
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-交易平仓-持仓检查跟单账号数据")
    def test_dbquery_addsalve_clsesdetail(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
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
                add_Slave["account"],
                add_Slave["account"],
                "1",
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
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            close_send_nos = db_data[0]["close_no"]
            logging.info(f"平仓之后的跟单账号持仓订单号: {close_send_nos}")
            var_manager.set_runtime_variable("close_send_nos", close_send_nos)
        with allure.step("3. 校验数据"):
            close_addsalve_size = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("close_addsalve_size", close_addsalve_size)
            total = sum(close_addsalve_size)
            logging.info(f"手数: {close_addsalve_size} 手数总和: {total}")
            totalSzie = trader_ordersend["totalSzie"]
            assert float(total) == float(
                totalSzie), f"跟单总手数和下单的手数不相等 (实际: {total}, 预期: {totalSzie})"

    # ---------------------------
    # 数据库校验-交易平仓-跟单平仓指令
    # ---------------------------
    @allure.title("数据库校验-交易平仓-跟单平仓指令")
    def test_dbquery_close_addsalve(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否有平仓指令"):
            masOrderSend = var_manager.get_variable("masOrderSend")
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            close_send_nos = var_manager.get_variable("close_send_nos")
            table_name = masOrderSend["table"]

            sql = f"""
            SELECT * 
            FROM {table_name} 
            WHERE order_no = %s
              AND trader_id = %s
            """
            params = (
                close_send_nos,
                vps_addslave_id
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
            order_no_close = db_data[0]["order_no"]
            logging.info(f"订单详情的订单号：{close_send_nos} 平仓指令的订单号：{order_no_close}")
            var_manager.set_runtime_variable("order_no_close", order_no_close)
            assert set(close_send_nos) == set(
                order_no_close), f"订单详情的订单号：{close_send_nos}和平仓指令的订单号：{order_no_close}不一致"

            close_addsalve_size = var_manager.get_variable("close_addsalve_size")
            true_total_lots = [record["true_total_lots"] for record in db_data]
            logging.info(f"订单详情的平仓手数:{close_addsalve_size} 平仓指令的实际平仓手数:{true_total_lots}")
            assert set(true_total_lots) == set(
                close_addsalve_size), f"订单详情的平仓手数{close_addsalve_size}和平仓指令{true_total_lots}的实际平仓手数不一致"

            time.sleep(90)
