# lingkuan_919/tests/test_vps_ordersend.py
import time

import allure
import logging
import pytest
import math
from lingkuan_919.VAR.VAR import *
from lingkuan_919.conftest import var_manager
from lingkuan_919.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "该用例暂时跳过"


@allure.feature("VPS策略下单-跟单修改模式、品种")
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
        with allure.step("1. 获取订单详情表账号数据"):
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
            db_data = self.query_database_with_time(
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
        with allure.step("1. 获取订单详情表账号数据"):
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
            db_data = self.query_database_with_time(
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
            assert math.isclose(float(total), 3, rel_tol=1e-9), f"修改下单品种之后下单手数之和应该是3，实际是：{total}"
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
        with allure.step("1. 获取订单详情表账号数据"):
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
            db_data = self.query_database_with_time(
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
        with allure.step("1. 获取订单详情表账号数据"):
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
            db_data = self.query_database_with_time(
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
        with allure.step("1. 获取订单详情表账号数据"):
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
            db_data = self.query_database_with_time(
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
            assert math.isclose(float(total), 3, rel_tol=1e-9), f"修改下单品种之后下单手数之和应该是3，实际是：{total}"
            logging.info(f"修改下单品种之后平仓手数之和应该是3，实际是：{total}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-策略平仓-修改净值")
    def test_dbclose_euqit(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情表账号数据"):
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
            db_data = self.query_database_with_time(
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

        time.sleep(40)
