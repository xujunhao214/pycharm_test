# lingkuan/tests/test_vps_ordersend.py
import time

import allure
import logging
import pytest
from lingkuan.VAR.VAR import *
from lingkuan.conftest import var_manager
from lingkuan.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("VPS策略下单-正常开仓平仓")
class TestVPSOrderSend_Scene(APITestBase):
    # ---------------------------
    # 账号管理-账号列表-修改用户
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-账号列表-修改用户")
    def test_update_user(self, api_session, var_manager, logged_session, db_transaction):
        # 1. 发送创建用户请求
        new_user = var_manager.get_variable("new_user")
        trader_user_id = var_manager.get_variable("trader_user_id")
        password = var_manager.get_variable("password")
        data = {
            "id": trader_user_id,
            "account": new_user["account"],
            "password": password,
            "platform": new_user["platform"],
            "accountType": "0",
            "serverNode": new_user["serverNode"],
            "remark": "编辑个人用户",
            "sort": 12,
            "vpsDescs": [
                {
                    "desc": "39.99.136.49-主VPS-跟单策略",
                    "status": 0,
                    "statusExtra": "启动成功",
                    "forex": "",
                    "cfd": "",
                    "traderId": 5733,
                    "ipAddress": "39.99.136.49",
                    "sourceId": None,
                    "sourceAccount": None,
                    "sourceName": None,
                    "loginNode": "47.83.21.167:443",
                    "nodeType": 0,
                    "nodeName": "账号节点",
                    "type": None,
                    "vpsId": 6,
                    "traderType": None,
                    "abRemark": None
                }
            ]
        }
        response = self.send_put_request(
            api_session,
            "/mascontrol/user",
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "新增单个用户失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # ---------------------------
    # 数据库校验-账号列表-修改用户
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-账号列表-修改用户是否成功")
    def test_dbupdate_user(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否编辑成功"):
            db_query = var_manager.get_variable("db_query")

            # 优化后的数据库查询
            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM {db_query['table']} WHERE account = %s",
                (db_query["account"],),
            )

            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")
            remark = db_data[0]["remark"]
            assert remark == "编辑个人用户", "修改个人信息失败"

    # ---------------------------
    # 数据库-获取主账号净值
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库-获取主账号净值")
    def test_dbtrader_euqit(self, var_manager, db_transaction):
        with allure.step("1. 获取主账号净值"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            table_trader = trader_ordersend["table_trader"]
            vps_trader_id = var_manager.get_variable("vps_trader_id")

            sql = f"""
                                                SELECT * 
                                                FROM {table_trader} 
                                                WHERE id = %s
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

            dbtrader_euqit = db_data[0]["euqit"]
            var_manager.set_runtime_variable("dbtrader_euqit", dbtrader_euqit)
            logging.info(f"主账号净值：{dbtrader_euqit}")

    # ---------------------------
    # 数据库-获取跟单账号净值
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库-获取跟单账号净值")
    def test_dbaddsalve_euqit(self, var_manager, db_transaction):
        with allure.step("1. 获取跟单账号净值"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            table_trader = trader_ordersend["table_trader"]
            vps_addslave_ids_3 = var_manager.get_variable("vps_addslave_ids_3")

            sql = f"""
                                    SELECT * 
                                    FROM {table_trader} 
                                    WHERE id = %s
                                    """
            params = (
                vps_addslave_ids_3
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

            addsalve_euqit = db_data[0]["euqit"]
            var_manager.set_runtime_variable("addsalve_euqit", addsalve_euqit)
            logging.info(f"跟单账号净值：{addsalve_euqit}")

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
            user_accounts_2 = var_manager.get_variable("user_accounts_2")
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
                user_accounts_2,
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
    # 数据库校验-策略开仓-跟单账号修改品种
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略开仓-跟单账号修改品种")
    def test_dbdetail_templateId3(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            vps_trader = var_manager.get_variable("vps_trader")
            table_name = trader_ordersend["table_detail"]
            user_accounts_3 = var_manager.get_variable("user_accounts_3")
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
                user_accounts_3,
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

    # 数据库校验-策略开仓-修改净值
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略开仓-修改净值")
    def test_dbtrader_euqit(self, var_manager, db_transaction):
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

            addsalve_size_euqit = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("addsalve_size_euqit", addsalve_size_euqit)
            total = sum(addsalve_size_euqit)
            dbtrader_euqit = var_manager.get_variable("dbtrader_euqit")
            addsalve_euqit = var_manager.get_variable("addsalve_euqit")
            # 校验除数非零
            if dbtrader_euqit == 0:
                pytest.fail("dbtrader_euqit为0，无法计算预期比例（避免除零）")

            true_size = addsalve_euqit / dbtrader_euqit * 1
            # 断言（调整误差范围为合理值，如±0.1）
            assert abs(total - true_size) < 1, f"size总和与预期比例偏差过大：预期{true_size}，实际{total}，误差超过1"

    # ---------------------------
    # 数据库校验-策略开仓-持仓检查跟单账号数据-修改币种@
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略开仓-修改币种@")
    def test_dbtrader_cfda(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            vps_trader = var_manager.get_variable("vps_trader")
            table_name = trader_ordersend["table_detail"]
            user_accounts_5 = var_manager.get_variable("user_accounts_5")

            sql = f"""
                SELECT * 
                FROM {table_name} 
                WHERE source_user = %s
                  AND account = %s
                """
            params = (
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

            addsalve_size_cfda = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("addsalve_size_cfda", addsalve_size_cfda)
            addsalve_size_cfda_total = sum(addsalve_size_cfda)
            assert float(
                addsalve_size_cfda_total) == 1, f"修改币种下单总手数应该是1，实际是：{addsalve_size_cfda_total}"
            logging.info(f"修改币种下单总手数应该是1，实际是：{addsalve_size_cfda_total}")

            symbol = db_data[0]["symbol"]
            assert symbol == "XAUUSD@", f"下单的币种与预期的不一样，预期：XAUUSD@ 实际：{symbol}"

    # ---------------------------
    # 数据库校验-策略开仓-修改币种p
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略开仓-修改币种p")
    def test_dbtrader_cfdp(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            vps_trader = var_manager.get_variable("vps_trader")
            table_name = trader_ordersend["table_detail"]
            user_accounts_6 = var_manager.get_variable("user_accounts_6")

            sql = f"""
                SELECT * 
                FROM {table_name} 
                WHERE source_user = %s
                  AND account = %s
                """
            params = (
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

            addsalve_size_cfdp = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("addsalve_size_cfdp", addsalve_size_cfdp)
            addsalve_size_cfdp_total = sum(addsalve_size_cfdp)
            assert float(
                addsalve_size_cfdp_total) != 0, f"修改币种下单总手数应该是0.01的倍数，实际是：{addsalve_size_cfdp_total}"
            logging.info(f"修改币种下单总手数应该是0.01的倍数，实际是：{addsalve_size_cfdp_total}")

            symbol = db_data[0]["symbol"]
            assert symbol == "XAUUSD.p", f"下单的币种与预期的不一样，预期：XAUUSD.p 实际：{symbol}"

    # 数据库校验-策略开仓-修改币种min
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略开仓-修改币种min")
    def test_dbtrader_cfdmin(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            vps_trader = var_manager.get_variable("vps_trader")
            table_name = trader_ordersend["table_detail"]
            user_accounts_7 = var_manager.get_variable("user_accounts_7")

            sql = f"""
                    SELECT * 
                    FROM {table_name} 
                    WHERE source_user = %s
                      AND account = %s
                    """
            params = (
                vps_trader["account"],
                user_accounts_7,
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

            addsalve_size_cfdmin = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("addsalve_size_cfdmin", addsalve_size_cfdmin)
            addsalve_size_cfdmin_total = sum(addsalve_size_cfdmin)
            assert float(
                addsalve_size_cfdmin_total) == 10, f"修改币种下单总手数应该是10，实际是：{addsalve_size_cfdmin_total}"
            logging.info(f"修改币种下单总手数应该是10，实际是：{addsalve_size_cfdmin_total}")

            symbol = db_data[0]["symbol"]
            assert symbol == "XAUUSD.min", f"下单的币种与预期的不一样，预期：XAUUSD.min 实际：{symbol}"

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
            user_accounts_2 = var_manager.get_variable("user_accounts_2")
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
                user_accounts_2,
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
    # 数据库校验-策略平仓-跟单账号修改品种
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略平仓-跟单账号修改品种")
    def test_dbclose_templateId3(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            vps_trader = var_manager.get_variable("vps_trader")
            table_name = trader_ordersend["table_detail"]
            user_accounts_3 = var_manager.get_variable("user_accounts_3")
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
                user_accounts_3,
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

    # ---------------------------
    # 数据库校验-策略平仓-修改净值
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略平仓-修改净值")
    def test_dbclose_euqit(self, var_manager, db_transaction):
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

            addsalve_size_euqit = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("addsalve_size_euqit", addsalve_size_euqit)
            total = sum(addsalve_size_euqit)
            dbtrader_euqit = var_manager.get_variable("dbtrader_euqit")
            addsalve_euqit = var_manager.get_variable("addsalve_euqit")
            # 校验除数非零
            if dbtrader_euqit == 0:
                pytest.fail("dbtrader_euqit为0，无法计算预期比例（避免除零）")

            true_size = addsalve_euqit / dbtrader_euqit * 1
            # 断言（调整误差范围为合理值，如±0.1）
            assert abs(total - true_size) < 1, f"size总和与预期比例偏差过大：预期{true_size}，实际{total}，误差超过1"

    # ---------------------------
    # 数据库校验-策略平仓-修改币种@
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略平仓-修改币种@")
    def test_dbclose_cfda(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            vps_trader = var_manager.get_variable("vps_trader")
            table_name = trader_ordersend["table_detail"]
            user_accounts_5 = var_manager.get_variable("user_accounts_5")

            sql = f"""
                SELECT * 
                FROM {table_name} 
                WHERE source_user = %s
                  AND account = %s
                  AND close_status = %s
                """
            params = (
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

            addsalve_size_cfda_close = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("addsalve_size_cfda_close", addsalve_size_cfda_close)
            addsalve_size_cfda_total = sum(addsalve_size_cfda_close)
            assert float(addsalve_size_cfda_total) == 1, f"修改币种下单总手数应该是1，实际是：{addsalve_size_cfda_total}"
            logging.info(f"修改币种下单总手数应该是1，实际是：{addsalve_size_cfda_total}")

            symbol = db_data[0]["symbol"]
            assert symbol == "XAUUSD@", f"下单的币种与预期的不一样，预期：XAUUSD@ 实际：{symbol}"

    # ---------------------------
    # 数据库校验-策略平仓-修改币种p
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略平仓-修改币种p")
    def test_dbclose_cfdp(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            vps_trader = var_manager.get_variable("vps_trader")
            table_name = trader_ordersend["table_detail"]
            user_accounts_6 = var_manager.get_variable("user_accounts_6")

            sql = f"""
                SELECT * 
                FROM {table_name} 
                WHERE source_user = %s
                  AND account = %s
                  AND close_status = %s
                """
            params = (
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

            addsalve_size_cfdp_close = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("addsalve_size_cfdp_close", addsalve_size_cfdp_close)
            addsalve_size_cfdp_total = sum(addsalve_size_cfdp_close)
            assert float(
                addsalve_size_cfdp_total) != 0, f"修改币种下单总手数应该是0.01的倍数，实际是：{addsalve_size_cfdp_total}"
            logging.info(f"修改币种下单总手数应该是0.01的倍数，实际是：{addsalve_size_cfdp_total}")

            symbol = db_data[0]["symbol"]
            assert symbol == "XAUUSD.p", f"下单的币种与预期的不一样，预期：XAUUSD.p 实际：{symbol}"

    # ---------------------------
    # 数据库校验-策略平仓-修改币种min
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略平仓-修改币种min")
    def test_dbclose_cfdmin(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            vps_trader = var_manager.get_variable("vps_trader")
            table_name = trader_ordersend["table_detail"]
            user_accounts_7 = var_manager.get_variable("user_accounts_7")

            sql = f"""
                SELECT * 
                FROM {table_name} 
                WHERE source_user = %s
                  AND account = %s
                  AND close_status = %s
                """
            params = (
                vps_trader["account"],
                user_accounts_7,
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

            addsalve_size_cfdmin_close = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("addsalve_size_cfdmin_close", addsalve_size_cfdmin_close)
            addsalve_size_cfdmin_total = sum(addsalve_size_cfdmin_close)
            assert float(
                addsalve_size_cfdmin_total) == 10, f"修改币种下单总手数应该是10，实际是：{addsalve_size_cfdmin_total}"
            logging.info(f"修改币种下单总手数应该是10，实际是：{addsalve_size_cfdmin_total}")

            symbol = db_data[0]["symbol"]
            assert symbol == "XAUUSD.min", f"下单的币种与预期的不一样，预期：XAUUSD.min 实际：{symbol}"
