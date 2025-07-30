# lingkuan_728/tests/test_masOrderSend.py
import allure
import logging
import pytest
import time
from lingkuan_728.VAR.VAR import *
from lingkuan_728.conftest import var_manager
from lingkuan_728.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("云策略-复制下单")
class TestMasordersend(APITestBase):
    # ---------------------------
    # 云策略-云策略列表-复制下单
    # ---------------------------
    @allure.title("云策略-云策略列表-复制下单")
    def test_cloudTrader_cloudOrderSend(self, api_session, var_manager, logged_session):
        # 1. 发送云策略复制下单请求
        cloudMaster_id = var_manager.get_variable("cloudMaster_id")
        data = {
            "id": cloudMaster_id,
            "type": 0,
            "tradeType": 1,
            "intervalTime": 100,
            "symbol": "XAUUSD",
            "placedType": 0,
            "startSize": "0.10",
            "endSize": "1.00",
            "totalNum": "3",
            "totalSzie": "1.00",
            "remark": "测试数据"
        }
        response = self.send_post_request(
            api_session,
            '/mascontrol/cloudTrader/cloudOrderSend',
            json_data=data,
        )

        # 2. 判断云策略复制下单是否成功
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    @allure.title("数据库校验-云策略列表-复制下单")
    def test_dbcloudTrader_cloudOrderSend(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否有下单"):
            cloudOrderSend = var_manager.get_variable("cloudOrderSend")
            vps_cloudTrader_ids_3 = var_manager.get_variable("vps_cloudTrader_ids_3")
            symbol = cloudOrderSend["symbol"]

            sql = f"""
            SELECT * 
            FROM follow_order_instruct 
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
                cloudOrderSend["type"],
                cloudOrderSend["endSize"],
                cloudOrderSend["startSize"],
                cloudOrderSend["remark"],
                cloudOrderSend["totalSzie"],
                vps_cloudTrader_ids_3
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

            order_nocloudOrderSend = db_data[0]["order_no"]
            logging.info(f"获取交易账号下单的订单号: {order_nocloudOrderSend}")
            var_manager.set_runtime_variable("order_nocloudOrderSend", order_nocloudOrderSend)

        with allure.step("3. 对数据进行校验"):
            operation_type = db_data[0]["operation_type"]
            assert operation_type == 0, f"操作类型operation_type应为0(下单)，实际状态为: {operation_type}"

            status = db_data[0]["status"]
            assert status in (0, 1), f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}"

    @allure.title("数据库校验-云策略复制下单-持仓检查")
    def test_dbquery_order_detail(self, var_manager, db_transaction):
        with allure.step("1. 根据下单指令仓库的order_no字段获取跟单账号订单数据"):
            order_nocloudOrderSend = var_manager.get_variable("order_nocloudOrderSend")
            vps_cloudTrader_ids_3 = var_manager.get_variable("vps_cloudTrader_ids_3")
            cloudOrderSend = var_manager.get_variable("cloudOrderSend")

            follow_order_detail = var_manager.get_variable("follow_order_detail")
            symbol = cloudOrderSend["symbol"]

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
                order_nocloudOrderSend,
                cloudOrderSend["type"],
                vps_cloudTrader_ids_3
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
            import math
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")
            addsalve_size = [record["size"] for record in db_data]
            total = sum(addsalve_size)
            logging.info(f"手数: {addsalve_size}   手数总和: {total}")
            totalSzie = cloudOrderSend["totalSzie"]
            assert math.isclose(float(total), float(totalSzie), rel_tol=1e-9,
                                abs_tol=1e-9), f"跟单总手数和下单的手数不相等 (实际: {total}, 预期: {totalSzie})"
            logging.info(f"跟单总手数和下单的手数相等(实际: {total}, 预期: {totalSzie})")

    # ---------------------------
    # 云策略-云策略列表-平仓
    # ---------------------------
    @allure.title("云策略-云策略列表-平仓")
    def test_cloudTrader_cloudOrderClose(self, api_session, var_manager, logged_session):
        cloudMaster_id = var_manager.get_variable("cloudMaster_id")
        # 1. 发送平仓请求
        data = {
            "isCloseAll": 1,
            "intervalTime": 100,
            "id": f"{cloudMaster_id}"
        }
        response = self.send_post_request(
            api_session,
            '/mascontrol/cloudTrader/cloudOrderClose',
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
    def test_dbcloudTrader_cloudOrderClose(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            cloudOrderSend = var_manager.get_variable("cloudOrderSend")
            user_accounts_cloudTrader_4 = var_manager.get_variable("user_accounts_cloudTrader_4")
            follow_order_detail = var_manager.get_variable("follow_order_detail")
            symbol = cloudOrderSend["symbol"]

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
                user_accounts_cloudTrader_4,
                user_accounts_cloudTrader_4,
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
        with ((allure.step("2. 提取数据"))):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            close_send_noscloudOrder = db_data[0]["close_no"]
            logging.info(f"平仓之后的跟单账号持仓订单号: {close_send_noscloudOrder}")
            var_manager.set_runtime_variable("close_send_noscloudOrder", close_send_noscloudOrder)
        with allure.step("3. 校验数据"):
            import math
            close_cloudOrder_size = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("close_cloudOrder_size", close_cloudOrder_size)
            total_cloudOrder = sum(close_cloudOrder_size)
            logging.info(f"手数: {close_cloudOrder_size} 手数总和: {total_cloudOrder}")
            totalSzie_cloudOrder = cloudOrderSend["totalSzie"]
            assert math.isclose(float(total_cloudOrder), float(totalSzie_cloudOrder), rel_tol=1e-9,
                                abs_tol=1e-9), f"跟单总手数和下单的手数不相等 (实际: {total_cloudOrder}, 预期: {totalSzie_cloudOrder})"
            logging.info(f"跟单总手数和下单的手数相等(实际: {total_cloudOrder}, 预期: {totalSzie_cloudOrder})")

    # ---------------------------
    # 数据库校验-交易平仓-云策略跟单平仓指令
    # ---------------------------
    @allure.title("数据库校验-交易平仓-云策略跟单平仓指令")
    def test_dbquery_close_detail(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否有平仓指令"):
            vps_cloudTrader_ids_3 = var_manager.get_variable("vps_cloudTrader_ids_3")
            close_send_noscloudOrder = var_manager.get_variable("close_send_noscloudOrder")

            sql = f"""
                SELECT * 
                FROM follow_order_instruct
                WHERE order_no = %s
                  AND trader_id = %s
                """
            params = (
                close_send_noscloudOrder,
                vps_cloudTrader_ids_3
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
            cloudOrder_no_close = db_data[0]["order_no"]
            logging.info(f"订单详情的订单号：{close_send_noscloudOrder} 平仓指令的订单号：{cloudOrder_no_close}")
            var_manager.set_runtime_variable("order_no_close", cloudOrder_no_close)
            assert set(close_send_noscloudOrder) == set(
                cloudOrder_no_close), f"订单详情的订单号：{close_send_noscloudOrder}和平仓指令的订单号：{cloudOrder_no_close}不一致"

            time.sleep(25)
