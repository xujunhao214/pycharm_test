# lingkuan/tests/test_vps_ordersend.py
import time
import math
import allure
import logging
import pytest
from lingkuan.VAR.VAR import *
from lingkuan.conftest import var_manager
from lingkuan.commons.api_base import APITestBase

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


# ---------------------------
# 修改币种
# ---------------------------
@allure.feature("VPS策略下单-跟单修改币种")
class TestVPSOrderSend_money(APITestBase):
    # ---------------------------
    # 账号管理-账号列表-修改用户
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("账号管理-账号列表-修改用户")
    def test_update_user(self, logged_session, var_manager, encrypted_password):
        # 1. 发送创建用户请求
        new_user = var_manager.get_variable("new_user")
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        data = {
            "id": vps_trader_id,
            "account": new_user["account"],
            "password": encrypted_password,
            "remark": "测试数据",
            "followStatus": 1,
            "templateId": 1,
            "type": 0,
            "cfd": "",
            "forex": "",
            "platform": new_user["platform"]
        }
        response = self.send_put_request(
            logged_session,
            "/subcontrol/trader",
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "编辑策略信息失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # ---------------------------
    # 数据库校验-账号列表-修改用户是否成功
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-账号列表-修改用户是否成功")
    def test_dbupdate_user(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否编辑成功"):
            new_user = var_manager.get_variable("new_user")
            sql = f"SELECT * FROM follow_trader WHERE account = %s"
            params = (new_user["account"],)

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params
            )

            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")
            cfd_value = db_data[0]["cfd"]
            # 允许为 None 或空字符串（去除空格后）
            assert cfd_value is None or cfd_value.strip() == "", f"修改个人信息失败（cfd字段应为空，实际值：{cfd_value}）"

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
            json_data=data
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
    # 数据库校验-策略开仓-修改币种@
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略开仓-修改币种@")
    def test_dbtrader_cfda(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情表账号数据"):
            new_user = var_manager.get_variable("new_user")
            vps_user_accounts_5 = var_manager.get_variable("vps_user_accounts_5")
            # symbol,order_no,size,trader_id,account
            sql = f"""
                SELECT * 
                FROM follow_order_detail 
                WHERE source_user = %s
                  AND account = %s
                """
            params = (
                new_user["account"],
                vps_user_accounts_5,
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="create_time",
                time_range=2
            )

        with allure.step("2. 校验数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            vps_addsalve_size_cfda = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("vps_addsalve_size_cfda", vps_addsalve_size_cfda)
            vps_addsalve_size_cfda_total = sum(vps_addsalve_size_cfda)
            assert math.isclose(vps_addsalve_size_cfda_total, 1.0,
                                rel_tol=1e-9), f"修改币种下单总手数应该是1，实际是：{vps_addsalve_size_cfda_total}"
            logging.info(f"修改币种下单总手数应该是1，实际是：{vps_addsalve_size_cfda_total}")

            symbol = db_data[0]["symbol"]
            assert symbol == "XAUUSD@" or symbol == "XAUUSD", f"下单的币种与预期的不一样，预期：XAUUSD@ 实际：{symbol}"

    # ---------------------------
    # 数据库校验-策略开仓-修改币种p
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略开仓-修改币种p")
    def test_dbtrader_cfdp(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情表账号数据"):
            new_user = var_manager.get_variable("new_user")
            vps_user_accounts_6 = var_manager.get_variable("vps_user_accounts_6")

            sql = f"""
                SELECT * 
                FROM follow_order_detail 
                WHERE source_user = %s
                  AND account = %s
                """
            params = (
                new_user["account"],
                vps_user_accounts_6,
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="create_time",
                time_range=2
            )

        with allure.step("2. 校验数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            vps_addsalve_size_cfdp = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("vps_addsalve_size_cfdp", vps_addsalve_size_cfdp)
            vps_addsalve_size_cfdp_total = sum(vps_addsalve_size_cfdp)
            assert (math.isclose(vps_addsalve_size_cfdp_total, 0.02, rel_tol=1e-9) or
                    math.isclose(vps_addsalve_size_cfdp_total, 0.03, rel_tol=1e-9) or
                    math.isclose(vps_addsalve_size_cfdp_total, 1.0,
                                 rel_tol=1e-9)), f"修改币种下单总手数应该是0.02或者0.03，如果币种不在交易时间就是1，实际是：{vps_addsalve_size_cfdp_total}"
            logging.info(
                f"修改币种下单总手数应该是0.02或者0.03，如果币种不在交易时间就是1，实际是：{vps_addsalve_size_cfdp_total}")

            symbol = db_data[0]["symbol"]
            assert symbol == "XAUUSD.p" or symbol == "XAUUSD", f"下单的币种与预期的不一样，预期：XAUUSD.p，如果这个币种不在交易时间就是XAUUSD 实际：{symbol}"

    # 数据库校验-策略开仓-修改币种min
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略开仓-修改币种min")
    def test_dbtrader_cfdmin(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情表账号数据"):
            new_user = var_manager.get_variable("new_user")
            vps_user_accounts_7 = var_manager.get_variable("vps_user_accounts_7")

            sql = f"""
                    SELECT * 
                    FROM follow_order_detail 
                    WHERE source_user = %s
                      AND account = %s
                    """
            params = (
                new_user["account"],
                vps_user_accounts_7,
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="create_time",
                time_range=2
            )

        with allure.step("2. 校验数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            vps_addsalve_size_cfdmin = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("vps_addsalve_size_cfdmin", vps_addsalve_size_cfdmin)
            vps_addsalve_size_cfdmin_total = sum(vps_addsalve_size_cfdmin)
            assert (math.isclose(vps_addsalve_size_cfdmin_total, 10.0, rel_tol=1e-9) or
                    math.isclose(vps_addsalve_size_cfdmin_total, 1.0,
                                 rel_tol=1e-9)), f"修改币种下单总手数应该是10,如果这个币种不在交易时间就是1，实际是：{vps_addsalve_size_cfdmin_total}"
            logging.info(
                f"修改币种下单总手数应该是10,如果这个币种不在交易时间就是1，实际是：{vps_addsalve_size_cfdmin_total}")

            symbol = db_data[0]["symbol"]
            assert symbol == "XAUUSD.min" or symbol == "XAUUSD", f"下单的币种与预期的不一样，预期：XAUUSD.min，如果这个币种不在交易时间就是XAUUSD，实际：{symbol}"

    # ---------------------------
    # 跟单软件看板-VPS数据-策略平仓
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-策略平仓")
    def test_trader_orderclose(self, var_manager, logged_session):
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

    # ---------------------------
    # 数据库校验-策略平仓-修改币种@
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略平仓-修改币种@")
    def test_dbclose_cfda(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情表账号数据"):
            new_user = var_manager.get_variable("new_user")
            vps_user_accounts_5 = var_manager.get_variable("vps_user_accounts_5")

            sql = f"""
                SELECT * 
                FROM follow_order_detail 
                WHERE source_user = %s
                  AND account = %s
                  AND close_status = %s
                """
            params = (
                new_user["account"],
                vps_user_accounts_5,
                "1"
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="create_time",
                time_range=2
            )

        with allure.step("2. 校验数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            vps_addsalve_size_cfda_close = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("vps_addsalve_size_cfda_close", vps_addsalve_size_cfda_close)
            vps_addsalve_size_cfda_total = sum(vps_addsalve_size_cfda_close)
            assert math.isclose(vps_addsalve_size_cfda_total, 1.0,
                                rel_tol=1e-9), f"修改币种下单总手数应该是1，实际是：{vps_addsalve_size_cfda_total}"
            logging.info(f"修改币种下单总手数应该是1，实际是：{vps_addsalve_size_cfda_total}")

            symbol = db_data[0]["symbol"]
            assert symbol == "XAUUSD@" or symbol == "XAUUSD", f"下单的币种与预期的不一样，预期：XAUUSD@ 实际：{symbol}"

    # ---------------------------
    # 数据库校验-策略平仓-修改币种p
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略平仓-修改币种p")
    def test_dbclose_cfdp(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情表账号数据"):
            new_user = var_manager.get_variable("new_user")
            vps_user_accounts_6 = var_manager.get_variable("vps_user_accounts_6")

            sql = f"""
                SELECT * 
                FROM follow_order_detail 
                WHERE source_user = %s
                  AND account = %s
                  AND close_status = %s
                """
            params = (
                new_user["account"],
                vps_user_accounts_6,
                "1"
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="create_time",
                time_range=2
            )

        with allure.step("2. 校验数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            vps_addsalve_size_cfdp_close = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("vps_addsalve_size_cfdp_close", vps_addsalve_size_cfdp_close)
            vps_addsalve_size_cfdp_total = sum(vps_addsalve_size_cfdp_close)
            assert (math.isclose(vps_addsalve_size_cfdp_total, 0.02, rel_tol=1e-9) or
                    math.isclose(vps_addsalve_size_cfdp_total, 0.03, rel_tol=1e-9) or
                    math.isclose(vps_addsalve_size_cfdp_total, 1.0,
                                 rel_tol=1e-9)), f"修改币种下单总手数应该是0.02或者0.03，如果币种不在交易时间就是1，实际是：{vps_addsalve_size_cfdp_total}"
            logging.info(
                f"修改币种下单总手数应该是0.02或者0.03，如果币种不在交易时间就是1，实际是：{vps_addsalve_size_cfdp_total}")

            symbol = db_data[0]["symbol"]
            assert symbol == "XAUUSD.p" or symbol == "XAUUSD", f"下单的币种与预期的不一样，预期：XAUUSD.p，如果这个币种不在交易时间就是XAUUSD 实际：{symbol}"

    # ---------------------------
    # 数据库校验-策略平仓-修改币种min
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略平仓-修改币种min")
    def test_dbclose_cfdmin(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情表账号数据"):
            new_user = var_manager.get_variable("new_user")
            vps_user_accounts_7 = var_manager.get_variable("vps_user_accounts_7")

            sql = f"""
                SELECT * 
                FROM follow_order_detail 
                WHERE source_user = %s
                  AND account = %s
                  AND close_status = %s
                """
            params = (
                new_user["account"],
                vps_user_accounts_7,
                "1"
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="create_time",
                time_range=2
            )

        with allure.step("2. 校验数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            vps_addsalve_size_cfdmin_close = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("vps_addsalve_size_cfdmin_close", vps_addsalve_size_cfdmin_close)
            vps_addsalve_size_cfdmin_total = sum(vps_addsalve_size_cfdmin_close)
            assert (math.isclose(vps_addsalve_size_cfdmin_total, 10.0, rel_tol=1e-9) or
                    math.isclose(vps_addsalve_size_cfdmin_total, 1.0,
                                 rel_tol=1e-9)), f"修改币种下单总手数应该是10,如果这个币种不在交易时间就是1，实际是：{vps_addsalve_size_cfdmin_total}"
            logging.info(
                f"修改币种下单总手数应该是10,如果这个币种不在交易时间就是1，实际是：{vps_addsalve_size_cfdmin_total}")

            symbol = db_data[0]["symbol"]
            assert symbol == "XAUUSD.min" or symbol == "XAUUSD", f"下单的币种与预期的不一样，预期：XAUUSD.min，如果这个币种不在交易时间就是XAUUSD，实际：{symbol}"

        time.sleep(25)
