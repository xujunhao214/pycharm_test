import time
import math
import allure
import logging
import pytest
from lingkuanMT5_1112.VAR.VAR import *
from lingkuanMT5_1112.conftest import var_manager
from lingkuanMT5_1112.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("VPS策略下单-开仓的场景校验-buy")
class TestVPSOrdersendbuy:
    @allure.story("场景3：平仓的订单方向功能校验-sell")
    @allure.description("""
        ### 测试说明
        - 前置条件：有vps策略和vps跟单
          1. 修改跟单账号，跟单方向-反向sell
          2. 进行开仓，手数范围：0.1-1，总订单数量4
          3. 交易下单-跟单账号自己平仓-buy
          4. 校验平仓的订单数，应该不等于4
          5. 交易下单-跟单账号自己平仓-sell
          6. 校验平仓的订单数,等于4
        - 预期结果：平仓的订单方向功能正确
        """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    class TestVPStradingOrders3(APITestBase):
        @pytest.mark.url("vps")
        @allure.title("修改跟单账号为反向跟单")
        def test_follow_updateSlave(self, class_random_str, var_manager, logged_session, encrypted_password):
            with allure.step("1. 修改跟单方向为反向"):
                # 1. 修改跟单方向为反向followDirection 1:反向 0：正向
                new_user = var_manager.get_variable("new_user")
                MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
                MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
                MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
                platformId = var_manager.get_variable("platformId")
                data = {
                    "traderId": MT5vps_trader_id,
                    "platform": new_user["platform"],
                    "account": MT5vps_user_accounts_1,
                    "password": encrypted_password,
                    "platformType": 1,
                    "remark": "",
                    "followDirection": 1,
                    "followMode": 1,
                    "remainder": 0,
                    "followParam": 1,
                    "placedType": 0,
                    "templateId": 1,
                    "followStatus": 1,
                    "followOpen": 1,
                    "followClose": 1,
                    "followRep": 0,
                    "fixedComment": "",
                    "commentType": "",
                    "digits": 0,
                    "cfd": "",
                    "forex": "",
                    "abRemark": "",
                    "id": MT5vps_addslave_id,
                    "platformId": platformId
                }
                response = self.send_post_request(
                    logged_session,
                    '/subcontrol/follow/updateSlave',
                    json_data=data
                )
            with allure.step("2. 验证响应状态码和内容"):
                self.assert_response_status(response, 200, "修改跟单账号失败")
                self.assert_json_value(response, "$.msg", "success", "响应msg应为success")

        @allure.title("VPS策略账号交易下单-复制下单")
        def test_copy_order_send(self, class_random_str, logged_session, var_manager):
            # 发送VPS策略账号交易下单-复制下单
            global symbol
            masOrderSend = var_manager.get_variable("masOrderSend")
            symbol = masOrderSend["symbol"]
            MT5vps_trader_user_id = var_manager.get_variable("MT5vps_trader_user_id")
            data = {
                "traderList": [MT5vps_trader_user_id],
                "type": 0,
                "tradeType": 1,
                "intervalTime": 0,
                "symbol": symbol,
                "placedType": 0,
                "startSize": "0.10",
                "endSize": "1.00",
                "totalNum": "4",
                "totalSzie": "",
                "remark": class_random_str
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

        @allure.title("VPS交易下单-交易平仓-跟单账号平仓-buy")
        def test_copy_order_close(self, class_random_str, var_manager, logged_session):
            MT5vps_user_ids_1 = var_manager.get_variable("MT5vps_user_ids_1")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 0,
                "num": "",
                "traderList": [
                    MT5vps_user_ids_1
                ],
                "closeType": 2,
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

        @allure.title("数据库校验-交易平仓-跟单指令及订单详情数据检查-没有订单")
        def test_dbquery_addsalve_orderSendclose(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
                MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
                sql = f"""
                       SELECT 
                           fod.size,
                           fod.close_no,
                           fod.magical,
                           fod.open_price,
                           fod.symbol,
                           fod.order_no,
                           fod.comment,
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
                           AND fod.comment = %s
                           AND fod.trader_id = %s
                           """
                params = (
                    '1',
                    MT5vps_user_accounts_1,
                    class_random_str,
                    MT5vps_addslave_id,
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.wait_for_database_no_record(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="foi.create_time"
                )
            with allure.step("2. 数据校验"):
                self.verify_data(
                    actual_value=len(db_data),
                    expected_value=0,
                    op=CompareOp.EQ,
                    message=f"平仓失败，应该没有平仓订单",
                    attachment_name="订单数量详情"
                )
                logging.info(f"平仓失败，应该没有平仓订单，结果有{len(db_data)}个订单")

        @allure.title("VPS交易下单-交易平仓-跟单账号平仓-sell")
        def test_copy_order_close2(self, class_random_str, var_manager, logged_session):
            MT5vps_user_ids_1 = var_manager.get_variable("MT5vps_user_ids_1")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 0,
                "num": "",
                "traderList": [MT5vps_user_ids_1],
                "closeType": 2,
                "remark": "",
                "symbol": "XAUUSD",
                "type": 1
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

        @allure.title("数据库校验-交易平仓-跟单指令及订单详情数据检查-有订单")
        def test_dbquery_addsalve_orderSendclose2(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
                MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
                sql = f"""
                          SELECT 
                              fod.size,
                              fod.close_no,
                              fod.magical,
                              fod.open_price,
                              fod.symbol,
                              fod.order_no,
                              fod.comment,
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
                              AND fod.comment = %s
                              AND fod.trader_id = %s
                              """
                params = (
                    '1',
                    MT5vps_user_accounts_1,
                    class_random_str,
                    MT5vps_addslave_id,
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
                        expected_value=4,
                        op=CompareOp.EQ,
                        message=f"平仓的订单方向正确，应该有4个平仓订单",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"平仓的订单方向正确，应该有4个平仓订单，结果有{len(db_data)}个订单")

        @allure.title("VPS交易下单-交易平仓-正常平仓")
        def test_copy_order_close3(self, class_random_str, var_manager, logged_session):
            MT5vps_trader_user_id = var_manager.get_variable("MT5vps_trader_user_id")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 0,
                "traderList": [MT5vps_trader_user_id],
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
        def test_dbquery_orderSendclose(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                new_user = var_manager.get_variable("new_user")
                sql = f"""
                            SELECT 
                                fod.size,
                                fod.close_no,
                                fod.magical,
                                fod.open_price,
                                fod.symbol,
                                fod.order_no,
                                fod.comment,
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
                    new_user["account"],
                    class_random_str
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
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=4,
                        op=CompareOp.EQ,
                        message=f"正常平仓，应该有4个平仓订单",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"正常平仓，应该有4个平仓订单，结果有{len(db_data)}个订单")
