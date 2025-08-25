# lingkuan_728/tests/test_masOrderSend.py
import allure
import logging
import pytest
import time
from lingkuan_728.VAR.VAR import *
from lingkuan_728.conftest import var_manager
from lingkuan_728.commons.api_base import APITestBase

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("云策略-分配下单")
class TestMasordersend(APITestBase):
    # ---------------------------
    # 云策略-云策略列表-分配下单
    # ---------------------------
    @allure.title("云策略-云策略列表-分配下单")
    def test_cloudTrader_cloudOrderSend(self, api_session, var_manager, logged_session):
        # 1. 发送云策略分配下单请求
        cloudMaster_id = var_manager.get_variable("cloudMaster_id")
        data = {
            "id": cloudMaster_id,
            "type": 0,
            "tradeType": 0,
            "symbol": "XAUUSD",
            "startSize": "0.10",
            "endSize": "1.00",
            "totalSzie": "1.00",
            "remark": "测试数据",
            "totalNum": 0
        }
        response = self.send_post_request(
            api_session,
            '/mascontrol/cloudTrader/cloudOrderSend',
            json_data=data,
        )

        # 2. 判断云策略分配下单是否成功
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    @allure.title("数据库校验-云策略列表-云策略开仓")
    def test_dbcloudTrader_cloudOrderSend(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否有开仓订单"):
            cloudOrderSend = var_manager.get_variable("cloudOrderSend")
            vps_cloudTrader_ids_3 = var_manager.get_variable("vps_cloudTrader_ids_3")
            symbol = cloudOrderSend["symbol"]

            sql = f"""
            SELECT 
                fod.size,
                fod.send_no,
                fod.open_price,
                foi.true_total_lots,
                foi.order_no,
                foi.operation_type,
		        foi.status
            FROM 
                follow_order_detail fod
            INNER JOIN 
                follow_order_instruct foi 
            ON 
                foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
            WHERE foi.symbol LIKE %s 
              AND foi.master_order_status = %s 
              AND foi.type = %s 
              AND foi.min_lot_size = %s 
              AND foi.max_lot_size = %s 
              AND foi.remark = %s 
              AND foi.total_lots = %s 
              AND foi.trader_id = %s
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
                time_field="foi.create_time",  # 按创建时间过滤
                time_range=MYSQL_TIME,  # 只查前后2分钟的数据
                timeout=WAIT_TIMEOUT,  # 最多等36秒
                poll_interval=POLL_INTERVAL,  # 每2秒查一次
                stable_period=STBLE_PERIOD,  # 新增：数据连续3秒不变则认为加载完成
                order_by="foi.create_time DESC"  # 按创建时间倒序
            )

        with allure.step("2. 对数据进行校验"):
            if not db_data:
                pytest.fail("数据库查询结果为空，查询语句有误")

            operation_type = db_data[0]["operation_type"]
            assert operation_type == 0, f"操作类型operation_type应为0(下单)，实际状态为: {operation_type}"

            status = db_data[0]["status"]
            assert status in (0, 1), f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}"

            size = [record["size"] for record in db_data]
            true_total_lots = [record["true_total_lots"] for record in db_data]
            assert size == true_total_lots, f"持仓订单的手数：{size}和下单指令的手数：{true_total_lots}不一致，请检查！"
            logging.info(f"持仓订单的手数：{size} 下单指令的手数：{true_total_lots}")

            total = sum(size)
            totalSzie = cloudOrderSend["totalSzie"]
            assert float(total) == float(
                totalSzie), f"下单总手数和下单的手数不相等 (实际: {total}, 预期: {totalSzie})"
            logging.info(f"下单总手数和下单的手数不相等 (实际: {total}, 预期: {totalSzie})")

    # ---------------------------
    # 云策略-云策略列表-云策略平仓
    # ---------------------------
    @allure.title("云策略-云策略列表-云策略平仓")
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
    @allure.title("数据库校验-云策略列表-云策略平仓")
    def test_dbcloudTrader_cloudOrderClose(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否有平仓订单"):
            cloudOrderSend = var_manager.get_variable("cloudOrderSend")
            user_accounts_cloudTrader_4 = var_manager.get_variable("user_accounts_cloudTrader_4")
            symbol = cloudOrderSend["symbol"]

            sql = f"""
            SELECT 
                fod.size,
                fod.close_no,
                fod.close_price,
                foi.true_total_lots,
                foi.order_no,
                foi.operation_type,
                foi.status
            FROM 
                follow_order_detail fod
            INNER JOIN 
                follow_order_instruct foi 
            ON 
                foi.order_no = fod.close_no COLLATE utf8mb4_0900_ai_ci
            WHERE fod.symbol LIKE %s 
              AND fod.source_user = %s
              AND fod.account = %s
              AND fod.close_status = %s
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
                time_field="foi.create_time",  # 按创建时间过滤
                time_range=MYSQL_TIME,  # 只查前后2分钟的数据
                timeout=WAIT_TIMEOUT,  # 最多等36秒
                poll_interval=POLL_INTERVAL,  # 每2秒查一次
                stable_period=STBLE_PERIOD,  # 新增：数据连续3秒不变则认为加载完成
                order_by="foi.create_time DESC"  # 按创建时间倒序
            )
        with allure.step("2. 对数据进行校验"):
            if not db_data:
                pytest.fail("数据库查询结果为空，查询语句有误")

            size = [record["size"] for record in db_data]
            true_total_lots = [record["true_total_lots"] for record in db_data]
            assert size == true_total_lots, f"持仓订单的手数：{size}和下单指令的手数：{true_total_lots}不一致，请检查！"
            logging.info(f"持仓订单的手数：{size} 下单指令的手数：{true_total_lots}")

            total = sum(size)
            totalSzie = cloudOrderSend["totalSzie"]
            assert float(total) == float(
                totalSzie), f"下单总手数和下单的手数不相等 (实际: {total}, 预期: {totalSzie})"
            logging.info(f"下单总手数和下单的手数不相等 (实际: {total}, 预期: {totalSzie})")
