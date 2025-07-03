# lingkuan_631/tests/test_vps_loukai.py
import allure
import logging
import pytest
from lingkuan_631.VAR.VAR import *
from lingkuan_631.conftest import var_manager
from lingkuan_631.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("VPS策略下单-跟单账号修改模式")
class TestLoukai(APITestBase):
    # ---------------------------
    # 跟单软件看板-VPS数据-修改跟单账号-模式改为固定手数
    # ---------------------------
    @allure.title("跟单软件看板-VPS数据-跟单账号修改模式")
    def test_update_slave(self, vps_api_session, var_manager, logged_session, db_transaction):
        # 1. 发送跟单账号修改模式请求
        add_Slave = var_manager.get_variable("add_Slave")
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        vps_addslave_id = var_manager.get_variable("vps_addslave_id")
        # 跟单账号修改模式followMode：0  手数改为followParam：2
        data = {
            "traderId": vps_trader_id,
            "platform": add_Slave["platform"],
            "account": add_Slave["account"],
            "password": add_Slave["password"],
            "remark": add_Slave["remark"],
            "followDirection": 0,
            "followMode": 0,
            "remainder": 0,
            "followParam": "2.00",
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

            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            followMode = db_data[0]["follow_mode"]
            logging.info(f"模式改为固定手数0: {followMode}")
            var_manager.set_runtime_variable("followMode", followMode)

            follow_mode = db_data[0]["follow_mode"]
            if follow_mode != 0:
                pytest.fail(f"数据修改失败follow_mode应该是0，实际是：{follow_mode}")

    # ---------------------------
    # 跟单软件看板-VPS数据-策略开仓
    # ---------------------------
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
            sleep_seconds=0
        )

        # 2. 判断是否添加成功
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

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
              AND instruction_type = %s 
              AND master_order_status = %s 
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
                "1",
                "0",
                trader_ordersend["type"],
                trader_ordersend["endSize"],
                trader_ordersend["startSize"],
                trader_ordersend["remark"],
                trader_ordersend["totalSzie"],
                trader_ordersend["totalNum"],
                vps_trader_id
            )

            db_data = self.wait_for_database_record(
                db_transaction,
                sql,
                params,
                time_field="create_time",
                time_range=MYSQL_TIME
            )

        with allure.step("2. 提取数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            order_no = db_data[0]["order_no"]
            logging.info(f"获取策略账号下单的订单号: {order_no}")
            var_manager.set_runtime_variable("order_no", order_no)

        with allure.step("3. 对数据进行校验"):
            # 定义验证函数
            def verify_order_status():
                master_order_status = db_data[0]["master_order_status"]
                if master_order_status != 0:
                    pytest.fail(f"下单后平仓状态master_order_status应为0（未平仓），实际状态为: {master_order_status}")
                operation_type = db_data[0]["operation_type"]
                if operation_type != 0:
                    pytest.fail(f"操作类型operation_type应为0(下单)，实际状态为: {operation_type}")
                status = db_data[0]["status"]
                if status not in (0, 1):  # 更清晰的写法
                    pytest.fail(f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}")

            # 执行验证
            try:
                verify_order_status()
                allure.attach("订单状态验证通过", "成功详情", allure.attachment_type.TEXT)
            except AssertionError as e:
                allure.attach(str(e), "订单状态验证失败", allure.attachment_type.TEXT)
                raise

        # ---------------------------
        # 数据库校验-策略开仓-跟单开仓指令
        # ---------------------------

    @allure.title("数据库校验-策略开仓-跟单开仓指令")
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
                 AND status = %s 
                 AND master_order_status = %s 
                 AND type = %s 
                 AND trader_id = %s
               """
            params = (
                f"%{symbol}%",
                "1",
                "0",
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

            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            master_orders = list(map(lambda x: x["master_order"], db_data))
            logging.info(f"主账号订单: {master_orders}")
            var_manager.set_runtime_variable("master_orders", master_orders)

    # ---------------------------
    # 数据库校验-策略开仓-持仓检查
    # ---------------------------
    @allure.title("数据库校验-策略开仓-持仓检查")
    def test_dbquery_order_detail(self, var_manager, db_transaction):
        with allure.step("1. 根据下单指令仓库的order_no字段获取跟单账号订单数据"):
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
                poll_interval=POLL_INTERVAL
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
            if float(total) != float(trader_ordersend["totalSzie"]):
                error_msg = f"跟单总手数和下单的手数不相等 (实际: {total}, 预期: {trader_ordersend['totalSzie']})"
                allure.attach(error_msg, "手数验证失败", allure.attachment_type.TEXT)
                pytest.fail(error_msg)
            else:
                allure.attach("跟单总手数和下单的手数相等", "成功详情", allure.attachment_type.TEXT)

    # ---------------------------
    # 跟单软件看板-VPS数据-策略平仓
    # ---------------------------
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
            json_data=data
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

    @allure.title("数据库校验-策略平仓-策略平仓指令")
    def test_dbquery_traderclose(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否有策略平仓指令"):
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            vps_trader_isCloseAll = var_manager.get_variable("vps_trader_isCloseAll")

            table_name = vps_trader_isCloseAll["table"]
            symbol = vps_trader_isCloseAll["symbol"]

            sql = f"""
               SELECT * 
               FROM {table_name} 
               WHERE symbol LIKE %s 
                 AND master_order_status = %s 
                 AND trader_id = %s
               """
            params = (
                f"%{symbol}%",
                "1",
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

        with allure.step("2. 验证订单状态"):
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
