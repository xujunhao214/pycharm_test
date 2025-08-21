import allure
import logging
import pytest
import time
import math
from lingkuan_819.VAR.VAR import *
from lingkuan_819.conftest import var_manager
from lingkuan_819.commons.api_base import APITestBase

logger = logging.getLogger(__name__)
SKIP_REASON = "该用例暂时跳过"


@allure.story("场景1：平仓的品种功能校验")
@allure.description("""
### 测试说明
- 前置条件：有vps策略和vps跟单
  1. 进行开仓，手数范围0.1-1，总订单2
  2. 进行平仓-错误的币种
  3. 校验平仓订单数-应该没有开仓订单
  4. 进行平仓-正常平仓
  5. 校验平仓的订单数
- 预期结果：平仓的品种功能正确
""")
class TestVPStradingOrders1(APITestBase):
    @allure.title("VPS交易下单-复制下单请求")
    def test_copy_order_send(self, logged_session, var_manager):
        # 发送VPS交易下单-复制下单请求
        masOrderSend = var_manager.get_variable("masOrderSend")
        vps_trader_user_id = var_manager.get_variable("vps_trader_user_id")  # 使用实例变量存储
        data = {
            "traderList": [vps_trader_user_id],
            "type": 0,
            "tradeType": 1,
            "intervalTime": 100,
            "symbol": masOrderSend["symbol"],
            "placedType": 0,
            "startSize": "0.10",
            "endSize": "1.00",
            "totalNum": "2",
            "totalSzie": "",
            "remark": ""
        }
        response = self.send_post_request(
            logged_session,
            '/bargain/masOrderSend',
            json_data=data
        )

        # 验证下单成功
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    @allure.title("VPS交易下单-交易平仓-币种错误")
    def test_copy_order_close(self, var_manager, logged_session):
        vps_trader_user_id = var_manager.get_variable("vps_trader_user_id")
        # 发送平仓请求
        data = {
            "flag": 0,
            "intervalTime": 0,
            "traderList": [vps_trader_user_id],
            "closeType": 0,
            "remark": "",
            "symbol": "XAGEUR",
            "type": 0
        }
        response = self.send_post_request(
            logged_session,
            '/bargain/masOrderClose',
            json_data=data
        )

        # 验证平仓成功
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    @allure.title("数据库校验-交易平仓-主指令及订单详情数据检查-没有订单")
    def test_dbquery_orderSendclose(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            new_user = var_manager.get_variable("new_user")
            sql = f"""
                    SELECT 
                        fod.size,
                        fod.close_no,
                        fod.magical,
                        fod.open_price,
                        fod.symbol,
                        fod.order_no,
                        foi.true_total_lots,
                        foi.order_no,
                        foi.operation_type,
                        foi.create_time,
                        foi.status
                    FROM 
                        follow_order_detail fod
                    INNER JOIN 
                        follow_order_instruct foi 
                    ON 
                        foi.order_no = fod.close_no COLLATE utf8mb4_0900_ai_ci
                    WHERE foi.operation_type = %s
                        AND fod.account = %s
                        """
            params = (
                '1',
                new_user["account"],
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.query_database_with_time(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="fod.close_time"
            )
        with allure.step("2. 数据校验"):
            assert len(db_data) == 0, "平仓的币种错误，应该没有平仓订单，不符合预期结果"

    @allure.title("数据库校验-交易平仓-跟单指令及订单详情数据检查-没有订单")
    def test_dbquery_addsalve_orderSendclose(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            sql = f"""
                    SELECT 
                        fod.size,
                        fod.close_no,
                        fod.magical,
                        fod.open_price,
                        fod.symbol,
                        fod.order_no,
                        foi.true_total_lots,
                        foi.order_no,
                        foi.operation_type,
                        foi.create_time,
                        foi.status,
                        foi.min_lot_size,
                        foi.max_lot_size,
                        foi.total_lots,
                        foi.master_order,
                        foi.total_orders
                    FROM 
                        follow_order_detail fod
                    INNER JOIN 
                        follow_order_instruct foi 
                    ON 
                        foi.order_no = fod.close_no COLLATE utf8mb4_0900_ai_ci
                    WHERE foi.operation_type = %s
                        AND fod.account = %s
                        AND fod.trader_id = %s
                        """
            params = (
                '1',
                vps_user_accounts_1,
                vps_addslave_id,
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.query_database_with_time(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="fod.close_time"
            )
        with allure.step("2. 数据校验"):
            assert len(db_data) == 0, "平仓的币种错误，应该没有平仓订单，不符合预期结果"

    @allure.title("VPS交易下单-交易平仓-正常平仓")
    def test_copy_order_close2(self, var_manager, logged_session):
        vps_trader_user_id = var_manager.get_variable("vps_trader_user_id")
        # 发送平仓请求
        data = {
            "flag": 0,
            "intervalTime": 0,
            "traderList": [vps_trader_user_id],
            "closeType": 0,
            "remark": "",
            "symbol": "XAUUSD",
            "type": 0
        }
        response = self.send_post_request(
            logged_session,
            '/bargain/masOrderClose',
            json_data=data
        )

        # 验证平仓成功
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    @allure.title("数据库校验-交易平仓-主指令及订单详情数据检查-有订单")
    def test_dbquery_orderSendclose2(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            new_user = var_manager.get_variable("new_user")
            sql = f"""
                        SELECT 
                            fod.size,
                            fod.close_no,
                            fod.magical,
                            fod.open_price,
                            fod.symbol,
                            fod.order_no,
                            foi.true_total_lots,
                            foi.order_no,
                            foi.operation_type,
                            foi.create_time,
                            foi.status
                        FROM 
                            follow_order_detail fod
                        INNER JOIN 
                            follow_order_instruct foi 
                        ON 
                            foi.order_no = fod.close_no COLLATE utf8mb4_0900_ai_ci
                        WHERE foi.operation_type = %s
                            AND fod.account = %s
                            """
            params = (
                '1',
                new_user["account"],
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.query_database_with_time(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="foi.create_time"
            )
        with allure.step("2. 数据校验"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            assert len(db_data) == 2, "正常平仓，应该有两个平仓订单，不符合预期结果"

    @allure.title("数据库校验-交易平仓-跟单指令及订单详情数据检查-有订单")
    def test_dbquery_addsalve_orderSendclose2(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            sql = f"""
                        SELECT 
                            fod.size,
                            fod.close_no,
                            fod.magical,
                            fod.open_price,
                            fod.symbol,
                            fod.order_no,
                            foi.true_total_lots,
                            foi.order_no,
                            foi.operation_type,
                            foi.create_time,
                            foi.status,
                            foi.min_lot_size,
                            foi.max_lot_size,
                            foi.total_lots,
                            foi.master_order,
                            foi.total_orders
                        FROM 
                            follow_order_detail fod
                        INNER JOIN 
                            follow_order_instruct foi 
                        ON 
                            foi.order_no = fod.close_no COLLATE utf8mb4_0900_ai_ci
                        WHERE foi.operation_type = %s
                            AND fod.account = %s
                            AND fod.trader_id = %s
                            """
            params = (
                '1',
                vps_user_accounts_1,
                vps_addslave_id,
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.query_database_with_time(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="foi.create_time"
            )
        with allure.step("2. 数据校验"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            assert len(db_data) == 2, "正常平仓，应该有两个平仓订单，不符合预期结果"

    time.sleep(25)
