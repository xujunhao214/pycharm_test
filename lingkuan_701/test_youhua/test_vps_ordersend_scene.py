# lingkuan_701/tests/test_vps_ordersend.py
import time

import allure
import logging
import pytest
from lingkuan_701.VAR.VAR import *
from lingkuan_701.conftest import var_manager
from lingkuan_701.commons.api_base import APITestBase  # 导入基础类

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
    # 数据库校验-策略开仓-持仓检查跟单账号数据-固定手数5
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略开仓-跟单账号固定手数")
    def test_dbdetail_followParam5(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            vps_trader = var_manager.get_variable("vps_trader")
            table_name = trader_ordersend["table_detail"]
            user_accounts_5 = var_manager.get_variable("user_accounts_5")
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
                user_accounts_5,
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

            addsalve_size_followParam = db_data[0]["size"]
            assert addsalve_size_followParam == 5, f"跟单账号实际下单手数 (实际: {addsalve_size_followParam}, 预期: 5)"

    # ---------------------------
    # 数据库校验-策略开仓-跟单账号修改下单比例
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略开仓-跟单账号修改下单比例")
    def test_dbdetail_followParam2(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            vps_trader = var_manager.get_variable("vps_trader")
            table_name = trader_ordersend["table_detail"]
            user_accounts_4 = var_manager.get_variable("user_accounts_4")
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
                user_accounts_4,
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

            addsalve_size_followParam2 = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("addsalve_size_followParam2", addsalve_size_followParam2)
            total = sum(addsalve_size_followParam2)
            assert float(total) == 2, f"修改下单比例之后下单手数之和应该是2，实际是：{total}"

    # ---------------------------
    # 数据库校验-策略开仓-修改品种
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略开仓-修改品种")
    def test_dbdetail_templateId3(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            vps_trader = var_manager.get_variable("vps_trader")
            table_name = trader_ordersend["table_detail"]
            user_accounts_6 = var_manager.get_variable("user_accounts_6")
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
                user_accounts_6,
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

            addsalve_size_templateId3 = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("addsalve_size_templateId3", addsalve_size_templateId3)
            total = sum(addsalve_size_templateId3)
            assert float(total) == 3, f"修改下单品种之后下单手数之和应该是3，实际是：{total}"

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
    # 数据库校验-策略开仓-持仓检查跟单账号数据-固定手数5
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略平仓-跟单账号固定手数")
    def test_dbclose_followParam5(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            vps_trader = var_manager.get_variable("vps_trader")
            table_name = trader_ordersend["table_detail"]
            user_accounts_5 = var_manager.get_variable("user_accounts_5")
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
                user_accounts_5,
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

        with allure.step("2. 校验数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            addsalve_size_followParam = db_data[0]["size"]
            assert addsalve_size_followParam == 5, f"跟单账号实际下单手数 (实际: {addsalve_size_followParam}, 预期: 5)"

    # ---------------------------
    # 数据库校验-策略平仓-跟单账号修改下单比例
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略平仓-跟单账号修改下单比例")
    def test_dbclose_followParam2(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            vps_trader = var_manager.get_variable("vps_trader")
            table_name = trader_ordersend["table_detail"]
            user_accounts_4 = var_manager.get_variable("user_accounts_4")
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
                user_accounts_4,
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

        with allure.step("2. 校验数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            addsalve_size_followParam2 = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("addsalve_size_followParam2", addsalve_size_followParam2)
            total = sum(addsalve_size_followParam2)
            assert float(total) == 2, f"修改下单比例之后平仓手数之和应该是2，实际是：{total}"

    # ---------------------------
    # 数据库校验-策略平仓-修改品种
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略平仓-修改品种")
    def test_dbclose_templateId3(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            vps_trader = var_manager.get_variable("vps_trader")
            table_name = trader_ordersend["table_detail"]
            user_accounts_6 = var_manager.get_variable("user_accounts_6")
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
                user_accounts_6,
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

        with allure.step("2. 校验数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            addsalve_size_templateId3 = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("addsalve_size_templateId3", addsalve_size_templateId3)
            total = sum(addsalve_size_templateId3)
            assert float(total) == 3, f"修改下单品种之后平仓手数之和应该是3，实际是：{total}"
