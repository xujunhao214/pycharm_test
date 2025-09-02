import allure
import logging
import pytest
import time
import math
from self_developed_refine.VAR.VAR import *
from self_developed_refine.conftest import var_manager
from self_developed_refine.commons.api_base import *
import requests
from self_developed_refine.commons.jsonpath_utils import JsonPathUtils

logger = logging.getLogger(__name__)
SKIP_REASON = "该用例暂时跳过"


# ------------------------------------
# 大模块6：云策略复制下单-平仓的全平策略功能校验
# ------------------------------------
@allure.feature("云策略复制下单-平仓的功能校验")
# @pytest.mark.skipif(True, reason=SKIP_REASON)
class TestCloudClose:
    @allure.story("场景2：平仓的停止功能校验")
    @allure.description("""
   ### 测试说明
   - 前置条件：有云策略和云跟单
     1. 进行开仓，手数范围0.1-1，总订单5
     2. 进行平仓
     3. 发送停止请求
     4. 校验平仓的订单数，应该不等于5
     5. 进行平仓-正常平仓
     6. 校验平仓的订单数,等于5
   - 预期结果：平仓的停止功能正确
   """)
    class TestcloudtradingOrders2(APITestBase):
        @allure.title("云策略-策略账号交易下单-复制下单请求")
        def test_copy_order_send(self, logged_session, var_manager):
            # 发送云策略-策略账号交易下单-复制下单请求
            global symbol
            masOrderSend = var_manager.get_variable("masOrderSend")
            symbol = masOrderSend["symbol"]
            cloudTrader_user_ids_2 = var_manager.get_variable("cloudTrader_user_ids_2")
            data = {
                "traderList": [cloudTrader_user_ids_2],
                "type": 0,
                "tradeType": 1,
                "intervalTime": 0,
                "symbol": symbol,
                "placedType": 0,
                "startSize": "0.10",
                "endSize": "1.00",
                "totalNum": "5",
                "totalSzie": "",
                "remark": "changjing2"
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

        @allure.title("云策略-策略账号交易下单-交易平仓-平仓设置30秒间隔")
        def test_copy_order_close(self, var_manager, logged_session):
            cloudTrader_user_ids_2 = var_manager.get_variable("cloudTrader_user_ids_2")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 30000,
                "traderList": [cloudTrader_user_ids_2],
                "closeType": 0,
                "remark": "",
                "symbol": symbol,
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

        @allure.title("交易下单-交易平仓-发送停止请求")
        def test_copy_order_stopOrder(self, var_manager, logged_session):
            cloudTrader_user_ids_2 = var_manager.get_variable("cloudTrader_user_ids_2")
            # 发送停止请求
            params = {
                "orderNo": "",
                "traderList": [cloudTrader_user_ids_2],
                "type": "1"
            }
            response = self.send_get_request(
                logged_session,
                '/bargain/stopOrder',
                params=params
            )

            # 验证发送停止请求
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

        @allure.title("数据库校验-交易开仓-主指令及订单详情数据检查-平仓订单不等于开仓总订单数")
        def test_dbquery_orderSend(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
                sql = f"""
                                   SELECT 
                                       fod.size,
                                       fod.comment,
                                       fod.close_no,
                                       fod.magical,
                                       fod.open_price,
                                       fod.symbol,
                                       fod.order_no,
                                       fod.close_time,
                                       foi.true_total_lots,
                                       foi.order_no,
                                       foi.operation_type,
                                       foi.create_time,
                                       foi.status,
                                       foi.min_lot_size,
                                       foi.max_lot_size,
                                       foi.total_lots,
                                       foi.total_orders
                                   FROM 
                                       follow_order_detail fod
                                   INNER JOIN 
                                       follow_order_instruct foi 
                                   ON 
                                       foi.order_no = fod.close_no COLLATE utf8mb4_0900_ai_ci
                                   WHERE foi.operation_type = %s
                                       AND fod.account = %s
                                       AND fod.comment = %s
                                       """
                params = (
                    '1',
                    cloudTrader_user_accounts_2,
                    "changjing2"
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
                    pytest.fail("数据库查询结果为空，无法进行复制下单校验")

                with allure.step("验证订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=5,
                        op=CompareOp.NE,
                        message=f"平仓的订单数量应该不是5",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"平仓的订单数量应该不是5，结果有{len(db_data)}个订单")

        @allure.title("数据库校验-交易平仓-跟单指令及订单详情数据检查-平仓订单不等于开仓总订单数")
        def test_dbquery_addsalve_orderSendclose(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
                cloudTrader_vps_ids_3 = var_manager.get_variable("cloudTrader_vps_ids_3")
                sql = f"""
                           SELECT 
                               fod.size,
                               fod.comment,
                               fod.close_no,
                               fod.magical,
                               fod.open_price,
                               fod.symbol,
                               fod.order_no,
                               fod.close_time,
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
                               AND fod.comment = %s
                               """
                params = (
                    '1',
                    cloudTrader_user_accounts_4,
                    cloudTrader_vps_ids_3,
                    "changjing2"
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
                    pytest.fail("数据库查询结果为空，无法进行复制下单校验")

                with allure.step("验证订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=5,
                        op=CompareOp.NE,
                        message=f"平仓的订单数量应该不是5",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"平仓的订单数量应该不是5，结果有{len(db_data)}个订单")

        @allure.title("云策略-策略账号交易下单-交易平仓-正常平仓")
        def test_copy_order_close2(self, var_manager, logged_session):
            cloudTrader_user_ids_2 = var_manager.get_variable("cloudTrader_user_ids_2")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 0,
                "traderList": [cloudTrader_user_ids_2],
                "closeType": 0,
                "remark": "",
                "symbol": symbol,
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
        def test_dbquery_orderSendclose(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
                sql = f"""
                               SELECT 
                                   fod.size,
                                   fod.comment,
                                   fod.close_no,
                                   fod.magical,
                                   fod.open_price,
                                   fod.symbol,
                                   fod.order_no,
                                   fod.close_time,
                                   foi.true_total_lots,
                                   foi.order_no,
                                   foi.operation_type,
                                   foi.create_time,
                                   foi.status,
                                   foi.total_orders
                               FROM 
                                   follow_order_detail fod
                               INNER JOIN 
                                   follow_order_instruct foi 
                               ON 
                                   foi.order_no = fod.close_no COLLATE utf8mb4_0900_ai_ci
                               WHERE foi.operation_type = %s
                                   AND fod.account = %s
                                   AND fod.comment = %s
                                   """
                params = (
                    '1',
                    cloudTrader_user_accounts_2,
                    "changjing2"
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )
            with allure.step("2. 数据校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

                with allure.step("验证订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=5,
                        op=CompareOp.EQ,
                        message=f"正常平仓，应该有4个平仓订单",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"正常平仓，应该有4个平仓订单，结果有{len(db_data)}个订单")

        @allure.title("数据库校验-交易平仓-跟单指令及订单详情数据检查-有订单")
        def test_dbquery_addsalve_orderSendclose2(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
                cloudTrader_vps_ids_3 = var_manager.get_variable("cloudTrader_vps_ids_3")
                sql = f"""
                               SELECT 
                                   fod.size,
                                   fod.comment,
                                   fod.close_no,
                                   fod.magical,
                                   fod.open_price,
                                   fod.symbol,
                                   fod.order_no,
                                   fod.close_time,
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
                                   AND fod.comment = %s
                                   """
                params = (
                    '1',
                    cloudTrader_user_accounts_4,
                    cloudTrader_vps_ids_3,
                    "changjing2"
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

                with allure.step("验证订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=5,
                        op=CompareOp.EQ,
                        message=f"正常平仓，应该有4个平仓订单",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"正常平仓，应该有4个平仓订单，结果有{len(db_data)}个订单")
