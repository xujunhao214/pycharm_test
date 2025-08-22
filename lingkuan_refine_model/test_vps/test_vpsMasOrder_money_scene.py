# lingkuan_refine_model/tests/test_vps_ordersend.py
import time
import math

import allure
import logging
import pytest
from lingkuan_refine_model.VAR.VAR import *
from lingkuan_refine_model.conftest import var_manager
from lingkuan_refine_model.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该用例暂时跳过"


@allure.feature("跟单软件看板-vps数据-修改跟单账号（多场景汇总）")
class TestVPSMasOrder_money_scene:
    @allure.story("场景1：VPS策略下单-跟单修改币种")
    @allure.description("""
    ### 用例说明
    - 前置条件：有vps策略和vps跟单
    - 操作步骤：
      1. 有三个账号，分别修改三个账号的后缀.@ .p .min
      2. 进行开仓
      3. 判断三个账号的币种手数是否正确
      4. 进行平仓
      5. 判断三个账号的币种手数是否正确
    - 预期结果：三个账号的币种手数正确
    """)
    class TestVPSOrderSend_money(APITestBase):
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

            with allure.step("2. 校验数据"):
                # 提取数据库中的值
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")
                cfd_value = db_data[0]["cfd"]
                # 允许为 None 或空字符串（去除空格后）
                assert cfd_value is None or cfd_value.strip() == "", f"修改个人信息失败（cfd字段应为空，实际值：{cfd_value}）"

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

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库校验-策略开仓-修改币种@")
        def test_dbtrader_cfda(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情界面跟单账号数据"):
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

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库校验-策略开仓-修改币种p")
        def test_dbtrader_cfdp(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情界面跟单账号数据"):
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

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库校验-策略开仓-修改币种min")
        def test_dbtrader_cfdmin(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情界面跟单账号数据"):
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

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库校验-策略平仓-修改币种@")
        def test_dbclose_cfda(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情界面跟单账号数据"):
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

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库校验-策略平仓-修改币种p")
        def test_dbclose_cfdp(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情界面跟单账号数据"):
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

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库校验-策略平仓-修改币种min")
        def test_dbclose_cfdmin(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情界面跟单账号数据"):
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

    @allure.story("场景2：VPS策略下单-跟单修改模式、品种")
    @allure.description("""
    ### 用例说明
    - 前置条件：有vps策略和vps跟单
    - 操作步骤：
      1. 有三个账号，分别修改三个账号：固定手数 品种 净值比例
      2. 进行开仓
      3. 判断三个账号的手数是否正确
      4. 进行平仓
      5. 判断三个账号的手数是否正确
    - 预期结果：三个账号的手数正确
    """)
    class TestVPSOrderSend_Scence(APITestBase):
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

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库校验-策略开仓-跟单账号固定手数5")
        def test_dbdetail_followParam5(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情界面跟单账号数据"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                new_user = var_manager.get_variable("new_user")
                vps_user_accounts_2 = var_manager.get_variable("vps_user_accounts_2")
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
                    vps_user_accounts_2,
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

                addsalve_size_followParam = db_data[0]["size"]
                assert addsalve_size_followParam == 5, f"跟单账号实际下单手数 (实际: {addsalve_size_followParam}, 预期: 5)"
                logging.info(f"跟单账号实际下单手数 (实际: {addsalve_size_followParam}, 预期: 5)")

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库校验-策略开仓-跟单账号修改品种")
        def test_dbdetail_templateId3(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情界面跟单账号数据"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                new_user = var_manager.get_variable("new_user")
                vps_user_accounts_3 = var_manager.get_variable("vps_user_accounts_3")
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
                    vps_user_accounts_3,
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

                addsalve_size_templateId3 = [record["size"] for record in db_data]
                total = sum(addsalve_size_templateId3)
                # assert float(total) == 3, f"修改下单品种之后下单手数之和应该是3，实际是：{total}"
                assert math.isclose(float(total), 3,
                                    rel_tol=1e-9), f"修改下单品种之后下单手数之和应该是3，实际是：{total}"
                logging.info(f"修改下单品种之后下单手数之和应该是3，实际是：{total}")

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库-获取主账号净值")
        def test_vps_dbtrader_euqit(self, var_manager, db_transaction):
            with allure.step("1. 获取主账号净值"):
                vps_trader_id = var_manager.get_variable("vps_trader_id")

                sql = f"""
                SELECT * FROM follow_trader WHERE id = %s
                        """
                params = (
                    vps_trader_id
                )

                # 使用智能等待查询
                db_data = self.query_database(
                    db_transaction,
                    sql,
                    params,
                )

            with allure.step("2. 提取数据"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

                vps_dbtrader_euqit = db_data[0]["euqit"]
                var_manager.set_runtime_variable("vps_dbtrader_euqit", vps_dbtrader_euqit)
                logging.info(f"主账号净值：{vps_dbtrader_euqit}")

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库-获取跟单账号净值")
        def test_dbvps_addsalve_euqit(self, var_manager, db_transaction):
            with allure.step("1. 获取跟单账号净值"):
                vps_addslave_ids_3 = var_manager.get_variable("vps_addslave_ids_3")

                sql = f"""
                        SELECT * FROM follow_trader WHERE id = %s
                        """
                params = (vps_addslave_ids_3)

                # 使用智能等待查询
                db_data = self.query_database(
                    db_transaction,
                    sql,
                    params,
                )

            with allure.step("2. 提取数据"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

                vps_addsalve_euqit = db_data[0]["euqit"]
                var_manager.set_runtime_variable("vps_addsalve_euqit", vps_addsalve_euqit)
                logging.info(f"跟单账号净值：{vps_addsalve_euqit}")

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库校验-策略开仓-修改净值")
        def test_vps_dbtrader_euqit2(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情界面跟单账号数据"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                new_user = var_manager.get_variable("new_user")
                vps_user_accounts_4 = var_manager.get_variable("vps_user_accounts_4")
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
                    vps_user_accounts_4,
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

                vps_addsalve_size_euqit = [record["size"] for record in db_data]
                var_manager.set_runtime_variable("vps_addsalve_size_euqit", vps_addsalve_size_euqit)
                total = sum(vps_addsalve_size_euqit)
                vps_dbtrader_euqit = var_manager.get_variable("vps_dbtrader_euqit")
                vps_addsalve_euqit = var_manager.get_variable("vps_addsalve_euqit")
                # 校验除数非零
                if vps_dbtrader_euqit == 0:
                    pytest.fail("vps_dbtrader_euqit为0，无法计算预期比例（避免除零）")

                true_size = vps_addsalve_euqit / vps_dbtrader_euqit * 1
                # 断言（调整误差范围为合理值，如±0.1）
                assert abs(total - true_size) < 3, f"size总和与预期比例偏差过大：预期{true_size}，实际{total}，误差超过3"
                logging.info(f"预期: {true_size} 实际: {total}")

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

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库校验-策略平仓-跟单账号固定手数")
        def test_dbclose_followParam5(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情界面跟单账号数据"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                new_user = var_manager.get_variable("new_user")
                vps_user_accounts_2 = var_manager.get_variable("vps_user_accounts_2")
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
                    vps_user_accounts_2,
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

                addsalve_size_followParam = db_data[0]["size"]
                assert addsalve_size_followParam == 5, f"跟单账号实际下单手数 (实际: {addsalve_size_followParam}, 预期: 5)"
                logging.info(f"跟单账号实际下单手数 (实际: {addsalve_size_followParam}, 预期: 5)")

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库校验-策略平仓-跟单账号修改品种")
        def test_dbclose_templateId3(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情界面跟单账号数据"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                new_user = var_manager.get_variable("new_user")
                vps_user_accounts_3 = var_manager.get_variable("vps_user_accounts_3")
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
                    vps_user_accounts_3,
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

                addsalve_size_templateId3 = [record["size"] for record in db_data]
                total = sum(addsalve_size_templateId3)
                assert math.isclose(float(total), 3,
                                    rel_tol=1e-9), f"修改下单品种之后下单手数之和应该是3，实际是：{total}"
                logging.info(f"修改下单品种之后平仓手数之和应该是3，实际是：{total}")

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库校验-策略平仓-修改净值")
        def test_dbclose_euqit(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情界面跟单账号数据"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                new_user = var_manager.get_variable("new_user")
                vps_user_accounts_4 = var_manager.get_variable("vps_user_accounts_4")
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
                    vps_user_accounts_4,
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

                vps_addsalve_size_euqit = [record["size"] for record in db_data]
                var_manager.set_runtime_variable("vps_addsalve_size_euqit", vps_addsalve_size_euqit)
                total = sum(vps_addsalve_size_euqit)
                vps_dbtrader_euqit = var_manager.get_variable("vps_dbtrader_euqit")
                vps_addsalve_euqit = var_manager.get_variable("vps_addsalve_euqit")
                # 校验除数非零
                if vps_dbtrader_euqit == 0:
                    pytest.fail("vps_dbtrader_euqit为0，无法计算预期比例（避免除零）")

                true_size = vps_addsalve_euqit / vps_dbtrader_euqit * 1
                # 断言（调整误差范围为合理值，如±0.1）
                assert abs(total - true_size) < 3, f"size总和与预期比例偏差过大：预期{true_size}，实际{total}，误差超过3"
                logging.info(f"预期:{true_size}实际:{total}")

            time.sleep(25)
