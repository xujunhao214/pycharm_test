# lingkuan_630/tests/test_vps_loukai.py
import allure
import logging
import pytest
from lingkuan_630.VAR.VAR import *
from lingkuan_630.conftest import var_manager
from lingkuan_630.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("VPS策略下单-漏平")
class TestLouping(APITestBase):
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
        with allure.step("3. 对数据进行校验"):
            # 定义验证函数
            def verify_order_status():
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

                follow_close = db_data[0]["follow_close"]
                if follow_close != 0:
                    pytest.fail(f"数据修改失败follow_close数据应该是0，实际是：{follow_close}")

            # 执行验证
            try:
                verify_order_status()
                allure.attach("订单状态验证通过", "成功详情", allure.attachment_type.TEXT)
            except AssertionError as e:
                allure.attach(str(e), "订单状态验证失败", allure.attachment_type.TEXT)
                raise

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
    # 跟单软件看板-VPS数据-策略平仓
    # ---------------------------
    @allure.title("跟单软件看板-VPS数据-策略平仓-出现漏平")
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
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "平仓失败"
        )

        # 3. 验证JSON返回内容
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
            new_user = var_manager.get_variable("new_user")
            symbol = new_user["symbol"]

            sql = f"""
            SELECT * 
            FROM follow_order_instruct 
            WHERE symbol LIKE %s 
              AND instruction_type = %s 
              AND master_order_status = %s 
              AND trader_id = %s
            """
            params = (
                f"%{symbol}%",
                "2",
                "1",
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

        with allure.step("2. 提取数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            master_order_status = db_data[0]["master_order_status"]
            logging.info(f"订单状态应该是0平仓失败: {master_order_status}")
            var_manager.set_runtime_variable("master_order_status", master_order_status)

    @allure.title("数据库校验-策略平仓-订单详情数据库检查平仓成功还是失败")
    def test_dbquery_orderSend_close(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否平仓失败"):
            vps_trader_louping = var_manager.get_variable("vps_trader_louping")
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")

            table_name = vps_trader_louping["table"]
            symbol = vps_trader_louping["symbol"]

            sql = f"""
            SELECT * 
            FROM {table_name} 
            WHERE symbol LIKE %s 
              AND account = %s 
              AND trader_id = %s 
              AND type = %s
            """
            params = (
                f"%{symbol}%",
                vps_trader_louping["account"],
                vps_addslave_id,
                vps_trader_louping["type"]
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
            with allure.step("3. 对数据进行校验"):
                # 定义验证函数
                def verify_order_status():
                    if not db_data:
                        pytest.fail("数据库查询结果为空，无法判断平仓状态")
                    close_status = db_data[0]["close_status"]
                    if close_status != 0:
                        pytest.fail(f"平仓失败close_status状态应该是0，实际状态为: {close_status}")

                # 执行验证
                try:
                    verify_order_status()
                    allure.attach("订单状态验证通过", "成功详情", allure.attachment_type.TEXT)
                except AssertionError as e:
                    allure.attach(str(e), "订单状态验证失败", allure.attachment_type.TEXT)
                    raise

        # ---------------------------
        # 跟单软件看板-VPS数据-策略开仓-一键补全
        # ---------------------------
        @pytest.mark.skip(reason="该功能暂不需要")
        @allure.title("跟单软件看板-VPS数据-开仓补全")
        def test_follow_repairSend(self, vps_api_session, var_manager, logged_session):
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

            with allure.step("3. 对数据进行校验"):
                # 定义验证函数
                def verify_order_status():
                    if not db_data:
                        pytest.fail("数据库查询结果为空，无法提取数据")

                    follow_close = db_data[0]["follow_close"]
                    if follow_close != 1:
                        pytest.fail(f"数据修改失败follow_close数据应该是1，实际是：{follow_close}")

                # 执行验证
                try:
                    verify_order_status()
                    allure.attach("订单状态验证通过", "成功详情", allure.attachment_type.TEXT)
                except AssertionError as e:
                    allure.attach(str(e), "订单状态验证失败", allure.attachment_type.TEXT)
                    raise

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
