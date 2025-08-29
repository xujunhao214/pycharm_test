import allure
import logging
import pytest
import time
import math
from lingkuan_825.VAR.VAR import *
from lingkuan_825.conftest import var_manager
from lingkuan_825.commons.api_base import *
import requests
from lingkuan_825.commons.jsonpath_utils import JsonPathUtils

logger = logging.getLogger(__name__)
SKIP_REASON = "该用例暂时跳过"


@allure.feature("云策略-策略账号交易下单-平仓的功能校验")
class TestVPSMasOrderclose:
    @allure.story("场景5：平仓的订单方向功能校验-buy")
    @allure.description("""
        ### 测试说明
        - 前置条件：有云策略和云跟单
          1. 修改跟单账号，跟单方向-正向
          2. 进行开仓
          3. 交易下单-跟单账号自己平仓-sell
          4. 校验平仓的订单数，应该不等于4
          5. 交易下单-跟单账号自己平仓-buy
          6. 校验平仓的订单数,等于4
        - 预期结果：平仓的订单方向功能正确
        """)
    class TestcloudtradingOrders5(APITestBase):
        @allure.title("修改跟单账号为正向跟单")
        def test_follow_updateSlave(self, var_manager, logged_session, encrypted_password):
            with allure.step("1. 修改跟单方向为正向"):
                # 1. 修改跟单方向为正向followDirection 1:反向 0：正向
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                data = [
                    {
                        "traderList": [
                            cloudTrader_traderList_4
                        ],
                        "cloudId": cloudMaster_id,
                        "masterId": cloudTrader_traderList_2,
                        "masterAccount": cloudTrader_user_accounts_2,
                        "followDirection": 0,
                        "followMode": 1,
                        "followParam": 1,
                        "remainder": 0,
                        "placedType": 0,
                        "templateId": 1,
                        "followStatus": 1,
                        "followOpen": 1,
                        "followClose": 1,
                        "fixedComment": "",
                        "commentType": None,
                        "digits": 0,
                        "followTraderIds": [],
                        "sort": 100,
                        "remark": "",
                        "cfd": None,
                        "forex": None
                    }
                ]
                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudBatchUpdate',
                    json_data=data
                )
            with allure.step("2. 验证响应状态码和内容"):
                self.assert_response_status(response, 200, "修改跟单账号失败")
                self.assert_json_value(response, "$.msg", "success", "响应msg应为success")

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
                "totalNum": "4",
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

        @allure.title("云策略-策略账号交易下单-交易平仓-跟单账号平仓-sell")
        def test_copy_order_close(self, var_manager, logged_session):
            cloudTrader_user_ids_4 = var_manager.get_variable("cloudTrader_user_ids_4")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 0,
                "num": "",
                "traderList": [
                    cloudTrader_user_ids_4
                ],
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

        @allure.title("数据库校验-交易平仓-主指令及订单详情数据检查-没有订单")
        def test_dbquery_orderSendclose(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
                sql = f"""
                            SELECT 
                                 fod.size,
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
                                """
                params = (
                    '1',
                    cloudTrader_user_accounts_2,
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

        @allure.title("云策略-策略账号交易下单-交易平仓-跟单账号平仓-buy")
        def test_copy_order_close2(self, var_manager, logged_session):
            cloudTrader_user_ids_4 = var_manager.get_variable("cloudTrader_user_ids_4")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 0,
                "num": "",
                "traderList": [cloudTrader_user_ids_4],
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

        @allure.title("数据库校验-交易平仓-跟单指令及订单详情数据检查-有订单")
        def test_dbquery_addsalve_orderSendclose2(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
                cloudTrader_vps_ids_3 = var_manager.get_variable("cloudTrader_vps_ids_3")
                sql = f"""
                          SELECT 
                              fod.size,
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
                              """
                params = (
                    '1',
                    cloudTrader_user_accounts_4,
                    cloudTrader_vps_ids_3,
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

        @allure.title("云策略-策略账号交易下单-交易平仓-正常平仓")
        def test_copy_order_close3(self, var_manager, logged_session):
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
        def test_dbquery_orderSendclose2(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
                sql = f"""
                            SELECT 
                                fod.size,
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
                                """
                params = (
                    '1',
                    cloudTrader_user_accounts_2,
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
                        expected_value=4,
                        op=CompareOp.EQ,
                        message=f"正常平仓，应该有4个平仓订单",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"正常平仓，应该有4个平仓订单，结果有{len(db_data)}个订单")

                time.sleep(30)

    @allure.story("场景6：平仓的订单数量功能校验-4")
    @allure.description("""
        ### 测试说明
        - 前置条件：有云策略和云跟单
          1. 进行开仓，手数范围：0.1-1，总订单数量4
          2. 进行平仓-订单数量2
          3. 校验平仓的订单数，应该等于2
          4. 进行平仓-订单数量2
          5. 校验平仓的订单数,等于4
        - 预期结果：平仓的订单数量功能正确
        """)
    class TestcloudtradingOrders6(APITestBase):
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
                "totalNum": "4",
                "totalSzie": "",
                "remark": "changjing6"
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

        @allure.title("云策略-策略账号交易下单-交易平仓-平仓2个订单")
        def test_copy_order_close(self, var_manager, logged_session):
            cloudTrader_user_ids_2 = var_manager.get_variable("cloudTrader_user_ids_2")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 0,
                "num": "2",
                "traderList": [cloudTrader_user_ids_2],
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

        @allure.title("数据库校验-交易平仓-跟单指令及订单详情数据检查-有2个订单")
        def test_dbquery_addsalve_orderSendclose(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
                cloudTrader_vps_ids_3 = var_manager.get_variable("cloudTrader_vps_ids_3")
                sql = f"""
                       SELECT 
                           fod.size,
                           fod.close_no,
                           fod.magical,
                           fod.open_price,
                           fod.comment,
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
                    'changjing6',
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="foi.create_time"
                )
            with allure.step("2. 数据校验"):
                self.verify_data(
                    actual_value=len(db_data),
                    expected_value=2,
                    op=CompareOp.EQ,
                    message=f"平仓的订单数量功能正确，应该有2个平仓订单",
                    attachment_name="订单数量详情"
                )
                logging.info(f"平仓的订单数量功能正确，应该有2个平仓订单，结果有{len(db_data)}个订单")

        @allure.title("云策略-策略账号交易下单-交易平仓-平仓2个订单")
        def test_copy_order_close2(self, var_manager, logged_session):
            cloudTrader_user_ids_2 = var_manager.get_variable("cloudTrader_user_ids_2")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 0,
                "num": "2",
                "traderList": [cloudTrader_user_ids_2],
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

        @allure.title("数据库校验-交易平仓-主指令及订单详情数据检查-有4个订单")
        def test_dbquery_orderSendclose(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
                sql = f"""
                            SELECT 
                                fod.size,
                                fod.close_no,
                                fod.magical,
                                fod.comment,
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
                    "changjing6"
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
                    pytest.fail("数据库查询结果为空，无法进行复制下单校验")

                with allure.step("验证订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=4,
                        op=CompareOp.EQ,
                        message=f"平仓的订单数量功能正确，应该有4个平仓订单",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"平仓的订单数量功能正确，应该有4个平仓订单，结果有{len(db_data)}个订单")

        @allure.title("数据库校验-交易平仓-跟单指令及订单详情数据检查-有4个订单")
        def test_dbquery_addsalve_orderSendclose2(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
                cloudTrader_vps_ids_3 = var_manager.get_variable("cloudTrader_vps_ids_3")
                sql = f"""
                             SELECT 
                                 fod.size,
                                 fod.close_no,
                                 fod.magical,
                                 fod.comment,
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
                    "changjing6"
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
                        message=f"平仓的订单数量功能正确，应该有4个平仓订单",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"平仓的订单数量功能正确，应该有4个平仓订单，结果有{len(db_data)}个订单")
