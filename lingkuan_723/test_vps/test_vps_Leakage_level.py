# lingkuan_723/tests/test_vps_ordersend.py
import allure
import logging
import pytest
import time
import math
from lingkuan_723.VAR.VAR import *
from lingkuan_723.conftest import var_manager
from lingkuan_723.commons.api_base import APITestBase
from lingkuan_723.commons.redis_utils import *

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("VPS策略下单-漏平")
class TestLeakagelevel(APITestBase):
    # ---------------------------
    # 跟单软件看板-VPS数据-修改跟单账号
    # ---------------------------
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-修改跟单账号（漏平）")
    def test_update_slave(self, var_manager, logged_session, encrypted_password):
        # 1. 发送修改策略账号请求
        add_Slave = var_manager.get_variable("add_Slave")
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        vps_addslave_id = var_manager.get_variable("vps_addslave_id")
        # 平仓给关闭followClose：0
        data = {
            "traderId": vps_trader_id,
            "platform": add_Slave["platform"],
            "account": add_Slave["account"],
            "password": encrypted_password,
            "remark": add_Slave["remark"],
            "followDirection": 0,
            "followMode": 1,
            "remainder": 0,
            "followParam": 1,
            "placedType": 0,
            "templateId": 1,
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
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            follow_close = db_data[0]["follow_close"]
            assert follow_close == 0, f"数据修改失败follow_close数据应该是0，实际是：{follow_close}"

    # ---------------------------
    # 跟单软件看板-VPS数据-策略开仓
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-策略开仓")
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
            addsalve_size = [record["size"] for record in db_data]
            total = sum(addsalve_size)
            logging.info(f"手数: {addsalve_size}   手数总和: {total}")
            totalSzie = trader_ordersend["totalSzie"]
            assert math.isclose(float(total), float(totalSzie), rel_tol=1e-9,
                                abs_tol=1e-9), f"跟单总手数和下单的手数不相等 (实际: {total}, 预期: {totalSzie})"
            logging.info(f"跟单总手数和下单的手数相等(实际: {total}, 预期: {totalSzie})")

    # ---------------------------
    # 数据库校验-策略开仓-持仓检查跟单账号数据
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略开仓-持仓检查跟单账号数据")
    def test_dbquery_addsalve_detail(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情表账号数据"):
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
    def test_dbquery_orderSend_addsalve(self, var_manager, db_transaction):
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
    @allure.title("跟单软件看板-VPS数据-策略平仓-出现漏平")
    def test_trader_orderclose(self, var_manager, logged_session, db_transaction):
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
        with allure.step("1. 检查订单详情表的数据"):
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
            addsalve_size = [record["size"] for record in db_data]
            total = sum(addsalve_size)
            logging.info(f"手数: {addsalve_size} 手数总和: {total}")
            totalSzie = trader_ordersend["totalSzie"]
            assert math.isclose(float(total), float(totalSzie), rel_tol=1e-9,
                                abs_tol=1e-9), f"跟单总手数和下单的手数不相等 (实际: {total}, 预期: {totalSzie})"
            logging.info(f"跟单总手数和下单的手数相等(实际: {total}, 预期: {totalSzie})")

    # ---------------------------
    # 数据库校验-策略平仓-检查平仓订单是否出现漏平
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略平仓-检查平仓订单是否出现漏平")
    def test_dbquery_addsalve_clsesdetail(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情表账号数据"):
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
        with allure.step("2. 校验数据"):
            close_status = db_data[0]["close_status"]
            logging.info(f"出现漏平，平仓状态应该是0，实际是：{close_status}")
            assert close_status == 0, f"出现漏平，平仓状态应该是0，实际是：{close_status}"

            close_remark = db_data[0]["close_remark"]
            logging.info(f"出现漏平，平仓异常信息应该是未开通平仓状态，实际是：{close_remark}")
            assert close_remark == "未开通平仓状态", f"出现漏平，平仓异常信息应该是未开通平仓状态，实际是：{close_remark}"

    # ---------------------------
    # 出现漏平-redis数据和数据库的数据做比对
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("出现漏平-redis数据和数据库的数据做比对")
    def test_dbquery_redis(self, var_manager, db_transaction, redis_order_data_close):
        with allure.step("1. 获取订单详情表账号数据"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            new_user = var_manager.get_variable("new_user")
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
                new_user["account"],
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

        with allure.step("2. 转换Redis数据为可比较格式"):
            if not redis_order_data_close:
                pytest.fail("Redis中未查询到订单数据")

            # 转换Redis数据为与数据库一致的格式
            redis_comparable_list = convert_redis_orders_to_comparable_list(redis_order_data_close)
            logging.info(f"转换后的Redis数据: {redis_comparable_list}")

            # 将转换后的数据存入变量管理器
            var_manager.set_runtime_variable("redis_comparable_list", redis_comparable_list)

        with allure.step("5. 比较Redis与数据库数据"):
            # 假设db_data是之前从数据库查询的结果
            if not db_data:
                pytest.fail("数据库中未查询到订单数据")

            # 提取数据库中的关键字段（根据实际数据库表结构调整）
            db_comparable_list = [
                {
                    "order_no": record["order_no"],  # 数据库order_no → 统一字段order_no
                    "magical": record["magical"],  # 数据库magical → 统一字段magical
                    "size": float(record["size"]),  # 数据库size → 统一字段size
                    "open_price": float(record["open_price"]),
                    "symbol": record["symbol"]
                }
                for record in db_data
            ]
            logging.info(f"数据库转换后: {db_comparable_list}")
            # 比较两个列表（可根据需要调整比较逻辑）
            self.assert_data_lists_equal(
                actual=redis_comparable_list,
                expected=db_comparable_list,
                fields_to_compare=["order_no", "magical", "size", "open_price", "symbol"],
                tolerance=1e-6  # 浮点数比较容差
            )

    # ---------------------------
    # 跟单软件看板-VPS数据-修改跟单账号
    # ---------------------------
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-修改跟单账号（漏平）")
    def test_update_slave2(self, var_manager, logged_session, encrypted_password):
        # 1. 发送修改策略账号请求
        add_Slave = var_manager.get_variable("add_Slave")
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        vps_addslave_id = var_manager.get_variable("vps_addslave_id")
        # 平仓给开启followOpen：1
        data = {
            "traderId": vps_trader_id,
            "platform": add_Slave["platform"],
            "account": add_Slave["account"],
            "password": encrypted_password,
            "remark": add_Slave["remark"],
            "followDirection": 0,
            "followMode": 1,
            "remainder": 0,
            "followParam": 1,
            "placedType": 0,
            "templateId": 1,
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

            follow_close = db_data[0]["follow_close"]
            assert follow_close == 1, f"数据修改失败follow_close数据应该是1，实际是：{follow_close}"

    @allure.title("跟单软件看板-VPS数据-修改完之后进行平仓补全")
    @pytest.mark.url("vps")
    def test_follow_repairSend2(self, var_manager, logged_session):
        with allure.step("1. 发送平仓补全请求"):
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
        with allure.step("1. 获取订单详情表账号数据"):
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
            assert math.isclose(float(total), float(totalSzie), rel_tol=1e-9,
                                abs_tol=1e-9), f"跟单总手数和下单的手数不相等 (实际: {total}, 预期: {totalSzie})"
            logging.info(f"跟单总手数和下单的手数相等(实际: {total}, 预期: {totalSzie})")

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
            # order_no_close = [record["order_no"] for record in db_data]
            order_no_close = [
                record["order_no"]
                for record in db_data
                if record["order_no"] is not None and str(record["order_no"]).strip() != ""
            ]
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
