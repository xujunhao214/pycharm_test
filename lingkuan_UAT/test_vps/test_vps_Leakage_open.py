# lingkuan_UAT/tests/test_vps_ordersend.py
import allure
import logging
import pytest
import time
from lingkuan_UAT.VAR.VAR import *
from lingkuan_UAT.conftest import var_manager
from lingkuan_UAT.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("VPS策略下单-漏开")
class TestLeakageopen(APITestBase):
    # ---------------------------
    # 跟单软件看板-VPS数据-修改跟单账号
    # ---------------------------
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-修改跟单账号（漏开）")
    def test_update_slave(self, var_manager, logged_session, encrypted_password):
        # 1. 发送修改策略账号请求
        add_Slave = var_manager.get_variable("add_Slave")
        user_accounts_1 = var_manager.get_variable("user_accounts_1")
        vps_addslave_id = var_manager.get_variable("vps_addslave_id")
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        # 开仓给关闭followOpen：0
        data = {
            "traderId": vps_trader_id,
            "platform": add_Slave["platform"],
            "account": user_accounts_1,
            "password": encrypted_password,
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
            logged_session,
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
            user_accounts_1 = var_manager.get_variable("user_accounts_1")
            sql = f"SELECT * FROM follow_trader_subscribe WHERE slave_account = %s"
            params = (user_accounts_1,)

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                timeout=WAIT_TIMEOUT,  # 最多等36秒
                poll_interval=POLL_INTERVAL,  # 每2秒查一次
                stable_period=STBLE_PERIOD,  # 新增：数据连续3秒不变则认为加载完成
                order_by="create_time DESC"  # 按创建时间倒序
            )
        with allure.step("2. 对数据进行校验"):
            follow_open = db_data[0]["follow_open"]
            assert follow_open == 0, f"follow_open的状态应该是0，实际是：{follow_open}"

    # ---------------------------
    # 跟单软件看板-VPS数据-策略开仓-出现漏单
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-策略开仓-出现漏单")
    def test_trader_orderSend(self, var_manager, logged_session):
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
            logged_session,
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
            symbol = trader_ordersend["symbol"]

            sql = f"""
            SELECT * 
            FROM follow_order_instruct 
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

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="create_time",  # 按创建时间过滤
                time_range=MYSQL_TIME,  # 只查前后2分钟的数据
                timeout=WAIT_TIMEOUT,  # 最多等36秒
                poll_interval=POLL_INTERVAL,  # 每2秒查一次
                stable_period=STBLE_PERIOD,  # 新增：数据连续3秒不变则认为加载完成
                order_by="create_time DESC"  # 按创建时间倒序
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
            symbol = trader_ordersend["symbol"]

            sql = f"""
                SELECT * 
                FROM follow_order_detail 
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

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="create_time",  # 按创建时间过滤
                time_range=MYSQL_TIME,  # 只查前后2分钟的数据
                timeout=WAIT_TIMEOUT,  # 最多等36秒
                poll_interval=POLL_INTERVAL,  # 每2秒查一次
                stable_period=STBLE_PERIOD,  # 新增：数据连续3秒不变则认为加载完成
                order_by="create_time DESC"  # 按创建时间倒序
            )

        with allure.step("2. 提取数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            order_nos = list(map(lambda x: x["order_no"], db_data))
            logging.info(f"持仓订单的订单号: {order_nos}")
            var_manager.set_runtime_variable("order_nos", order_nos)

        with allure.step("3. 校验数据"):
            import math
            addsalve_size = [record["size"] for record in db_data]
            total = sum(addsalve_size)
            logging.info(f"手数: {addsalve_size}   手数总和: {total}")
            totalSzie = trader_ordersend["totalSzie"]
            assert math.isclose(float(total), float(totalSzie), rel_tol=1e-9,
                                abs_tol=1e-9), f"跟单总手数和下单的手数不相等 (实际: {total}, 预期: {totalSzie})"
            logging.info(f"跟单总手数和下单的手数相等(实际: {total}, 预期: {totalSzie})")

    # ---------------------------
    # 数据库校验-策略开仓-跟单开仓指令
    # ---------------------------
    @allure.title("数据库校验-策略开仓-跟单开仓指令-根据status状态发现有漏单")
    def test_dbquery_orderSend_addsalve(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否有跟单开仓指令"):
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            symbol = trader_ordersend["symbol"]

            sql = f"""
                SELECT * 
                FROM follow_order_instruct 
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

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="create_time",  # 按创建时间过滤
                time_range=MYSQL_TIME,  # 只查前后2分钟的数据
                timeout=WAIT_TIMEOUT,  # 最多等36秒
                poll_interval=POLL_INTERVAL,  # 每2秒查一次
                stable_period=STBLE_PERIOD,  # 新增：数据连续3秒不变则认为加载完成
                order_by="create_time DESC"  # 按创建时间倒序
            )
        with allure.step("2. 对订单状态进行校验"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")
            status = db_data[0]["status"]
            assert status == 2, f"跟单失败，跟单状态status应该是2，实际是：{status}"

    # ---------------------------
    # 跟单软件看板-VPS数据-策略开仓-一键补全
    # ---------------------------
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-开仓补全")
    def test_follow_repairSend(self, var_manager, logged_session):
        with allure.step("1. 发送开仓补全请求"):
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            data = {
                "type": 2,
                "masterId": vps_trader_id,
                "slaveId": vps_addslave_id
            }
            response = self.send_post_request(
                logged_session,
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
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-修改跟单账号")
    def test_update_slave2(self, var_manager, logged_session, encrypted_password):
        # 1. 发送修改策略账号请求
        add_Slave = var_manager.get_variable("add_Slave")
        user_accounts_1 = var_manager.get_variable("user_accounts_1")
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        vps_addslave_id = var_manager.get_variable("vps_addslave_id")
        # 开仓给开启followOpen：1
        data = {
            "traderId": vps_trader_id,
            "platform": add_Slave["platform"],
            "account": user_accounts_1,
            "password": encrypted_password,
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
            logged_session,
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
            user_accounts_1 = var_manager.get_variable("user_accounts_1")
            sql = f"SELECT * FROM follow_trader_subscribe WHERE slave_account = %s"
            params = (user_accounts_1,)

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                timeout=WAIT_TIMEOUT,  # 最多等36秒
                poll_interval=POLL_INTERVAL,  # 每2秒查一次
                stable_period=STBLE_PERIOD,  # 新增：数据连续3秒不变则认为加载完成
                order_by="create_time DESC"  # 按创建时间倒序
            )

        with allure.step("2. 对数据进行校验"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")
            follow_open = db_data[0]["follow_open"]
            assert follow_open == 1, f"数据修改失败，数据follow_openy应该是1，实际是：{follow_open}"

    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-修改完之后进行开仓补全")
    def test_follow_repairSend2(self, var_manager, logged_session):
        with allure.step("1. 发送开仓补全请求"):
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            data = {
                "type": 2,
                "masterId": vps_trader_id,
                "slaveId": vps_addslave_id
            }
            response = self.send_post_request(
                logged_session,
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
            new_user = var_manager.get_variable("new_user")
            user_accounts_1 = var_manager.get_variable("user_accounts_1")
            symbol = trader_ordersend["symbol"]

            sql = f"""
                SELECT * 
                FROM follow_order_detail 
                WHERE symbol LIKE %s 
                  AND source_user = %s
                  AND account = %s
                """
            params = (
                f"%{symbol}%",
                new_user["account"],
                user_accounts_1,
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="create_time",  # 按创建时间过滤
                time_range=MYSQL_TIME,  # 只查前后2分钟的数据
                timeout=WAIT_TIMEOUT,  # 最多等36秒
                poll_interval=POLL_INTERVAL,  # 每2秒查一次
                stable_period=STBLE_PERIOD,  # 新增：数据连续3秒不变则认为加载完成
                order_by="create_time DESC"  # 按创建时间倒序
            )

        with allure.step("2. 提取数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            send_nos = list(map(lambda x: x["send_no"], db_data))
            logging.info(f"持仓订单的订单号: {send_nos}")
            var_manager.set_runtime_variable("send_nos", send_nos)

        with allure.step("3. 校验数据"):
            import math
            addsalve_size = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("addsalve_size", addsalve_size)
            total = sum(addsalve_size)
            logging.info(f"手数: {addsalve_size}    手数总和: {total}")
            totalSzie = trader_ordersend["totalSzie"]
            assert math.isclose(float(total), float(totalSzie), rel_tol=1e-9,
                                abs_tol=1e-9), f"跟单总手数和下单的手数不相等 (实际: {total}, 预期: {totalSzie})"
            logging.info(f"跟单总手数和下单的手数相等(实际: {total}, 预期: {totalSzie})")

    # ---------------------------
    # 数据库校验-策略开仓-跟单开仓指令
    # ---------------------------
    @allure.title("数据库校验-策略开仓-跟单开仓指令")
    def test_dbquery_orderSend_addsalve2(self, var_manager, db_transaction):
        with allure.step("1. 根据订单详情数据库数据，校验跟单指令数据是否正确"):
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            symbol = trader_ordersend["symbol"]

            sql = f"""
                    SELECT * 
                    FROM follow_order_instruct 
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

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="create_time",  # 按创建时间过滤
                time_range=MYSQL_TIME,  # 只查前后2分钟的数据
                timeout=WAIT_TIMEOUT,  # 最多等36秒
                poll_interval=POLL_INTERVAL,  # 每2秒查一次
                stable_period=STBLE_PERIOD,  # 新增：数据连续3秒不变则认为加载完成
                order_by="create_time DESC"  # 按创建时间倒序
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
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-策略平仓")
    def test_trader_orderclose(self, var_manager, logged_session, db_transaction):
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
            logged_session,
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

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="create_time",  # 按创建时间过滤
                time_range=MYSQL_TIME,  # 只查前后2分钟的数据
                timeout=WAIT_TIMEOUT,  # 最多等36秒
                poll_interval=POLL_INTERVAL,  # 每2秒查一次
                stable_period=STBLE_PERIOD,  # 新增：数据连续3秒不变则认为加载完成
                order_by="create_time DESC"  # 按创建时间倒序
            )

        with allure.step("2. 提取数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            order_no_detail = db_data[0]["order_no"]
            logging.info(f"获取策略平仓的订单号: {order_no_detail}")
            var_manager.set_runtime_variable("order_no_detail", order_no_detail)

    # ---------------------------
    # 数据库校验-策略平仓-平仓订单详情持仓检查
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略平仓-平仓订单详情持仓检查")
    def test_dbquery_closed_orderdetail(self, var_manager, db_transaction):
        with allure.step("1. 检查订单详情界面的数据"):
            order_no_detail = var_manager.get_variable("order_no_detail")
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            symbol = trader_ordersend["symbol"]

            sql = f"""
                SELECT * 
                FROM follow_order_detail 
                WHERE symbol LIKE %s 
                  AND close_no = %s 
                  AND type = %s 
                  AND trader_id = %s
                """
            params = (
                f"%{symbol}%",
                order_no_detail,
                trader_ordersend["type"],
                vps_trader_id
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                timeout=WAIT_TIMEOUT,  # 最多等36秒
                poll_interval=POLL_INTERVAL,  # 每2秒查一次
                stable_period=STBLE_PERIOD,  # 新增：数据连续3秒不变则认为加载完成
                order_by="create_time DESC"  # 按创建时间倒序
            )

        with allure.step("2. 提取数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            order_nos = list(map(lambda x: x["order_no"], db_data))
            logging.info(f"持仓订单的订单号: {order_nos}")
            var_manager.set_runtime_variable("order_nos", order_nos)

        with allure.step("3. 校验数据"):
            import math
            addsalve_size = [record["size"] for record in db_data]
            total = sum(addsalve_size)
            logging.info(f"手数: {addsalve_size} 手数总和: {total}")
            totalSzie = trader_ordersend["totalSzie"]
            assert math.isclose(float(total), float(totalSzie), rel_tol=1e-9,
                                abs_tol=1e-9), f"跟单总手数和下单的手数不相等 (实际: {total}, 预期: {totalSzie})"
            logging.info(f"跟单总手数和下单的手数相等(实际: {total}, 预期: {totalSzie})")

    # ---------------------------
    # 数据库校验-策略平仓-持仓检查跟单账号数据
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略平仓-持仓检查跟单账号数据")
    def test_dbquery_addsalve_clsesdetail(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            new_user = var_manager.get_variable("new_user")
            user_accounts_1 = var_manager.get_variable("user_accounts_1")
            symbol = trader_ordersend["symbol"]

            sql = f"""
                SELECT * 
                FROM follow_order_detail 
                WHERE symbol LIKE %s 
                  AND source_user = %s
                  AND account = %s
                  AND close_status = %s
                """
            params = (
                f"%{symbol}%",
                new_user["account"],
                user_accounts_1,
                "1",
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="create_time",  # 按创建时间过滤
                time_range=MYSQL_TIME,  # 只查前后2分钟的数据
                timeout=WAIT_TIMEOUT,  # 最多等36秒
                poll_interval=POLL_INTERVAL,  # 每2秒查一次
                stable_period=STBLE_PERIOD,  # 新增：数据连续3秒不变则认为加载完成
                order_by="create_time DESC"  # 按创建时间倒序
            )
        with (allure.step("2. 提取数据")):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            close_send_nos = [record["close_no"] for record in db_data]
            logging.info(f"平仓之后的跟单账号持仓订单号: {close_send_nos}")
            var_manager.set_runtime_variable("close_send_nos", close_send_nos)
        with allure.step("3. 校验数据"):
            import math
            close_addsalve_size = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("close_addsalve_size", close_addsalve_size)
            total = sum(close_addsalve_size)
            logging.info(f"手数: {close_addsalve_size} 手数总和: {total}")
            totalSzie = trader_ordersend["totalSzie"]
            assert math.isclose(float(total), float(totalSzie), rel_tol=1e-9,
                                abs_tol=1e-9), f"跟单总手数和下单的手数不相等 (实际: {total}, 预期: {totalSzie})"
            logging.info(f"跟单总手数和下单的手数相等(实际: {total}, 预期: {totalSzie})")

    # ---------------------------
    # 数据库校验-策略平仓-跟单平仓指令
    # ---------------------------
    @allure.title("数据库校验-策略平仓-跟单平仓指令")
    def test_dbquery_close_addsalve(self, var_manager, db_transaction):
        with allure.step("1. 根据订单详情数据库数据，校验跟单指令数据是否正确"):
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            symbol = trader_ordersend["symbol"]

            sql = f"""
                    SELECT * 
                    FROM follow_order_instruct 
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

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="create_time",  # 按创建时间过滤
                time_range=MYSQL_TIME,  # 只查前后2分钟的数据
                timeout=WAIT_TIMEOUT,  # 最多等36秒
                poll_interval=POLL_INTERVAL,  # 每2秒查一次
                stable_period=STBLE_PERIOD,  # 新增：数据连续3秒不变则认为加载完成
                order_by="create_time DESC"  # 按创建时间倒序
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

            time.sleep(25)
