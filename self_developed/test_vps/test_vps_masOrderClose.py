import allure
import logging
import pytest
import time
import re
from self_developed.conftest import var_manager
from self_developed.commons.api_base import *
import requests
from self_developed.commons.jsonpath_utils import JsonPathUtils

logger = logging.getLogger(__name__)
SKIP_REASON = "该用例暂时跳过"


@allure.feature("VPS策略账号交易下单-平仓的功能校验")
class TestVPSMasOrderclose:
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
            vps_trader_user_id = var_manager.get_variable("vps_trader_user_id")
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
                "remark": "changjing1"
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
        @pytest.mark.retry(n=3, delay=5)
        def test_dbquery_orderSendclose(self, var_manager, db_transaction):
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
                            """
                params = (
                    '1',
                    new_user["account"],
                    "changjing1"
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
                    message=f"平仓的币种错误，应该没有平仓订单",
                    attachment_name="订单数量详情"
                )
                logging.info(f"平仓的币种错误，应该没有平仓订单，结果有{len(db_data)}个订单")

        @allure.title("数据库校验-交易平仓-跟单指令及订单详情数据检查-没有订单")
        def test_dbquery_addsalve_orderSendclose(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
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
                    vps_user_accounts_1,
                    "changjing1",
                    vps_addslave_id,
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
                    message=f"平仓的币种错误，应该没有平仓订单",
                    attachment_name="订单数量详情"
                )
                logging.info(f"平仓的币种错误，应该没有平仓订单，结果有{len(db_data)}个订单")

        @allure.title("VPS交易下单-交易平仓-正常平仓")
        def test_copy_order_close2(self, var_manager, logged_session):
            vps_trader_user_id = var_manager.get_variable("vps_trader_user_id")
            masOrderSend = var_manager.get_variable("masOrderSend")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 0,
                "traderList": [vps_trader_user_id],
                "closeType": 0,
                "remark": "",
                "symbol": masOrderSend["symbol"],
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
                    "changjing1"
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
                        expected_value=2,
                        op=CompareOp.EQ,
                        message=f"正常平仓，应该有两个平仓订单",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"正常平仓，应该有两个平仓订单，结果有{len(db_data)}个订单")

        @allure.title("数据库校验-交易平仓-跟单指令及订单详情数据检查-有订单")
        def test_dbquery_addsalve_orderSendclose2(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
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
                    vps_user_accounts_1,
                    "changjing1",
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

                with allure.step("验证订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=2,
                        op=CompareOp.EQ,
                        message=f"正常平仓，应该有两个平仓订单",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"正常平仓，应该有两个平仓订单，结果有{len(db_data)}个订单")

    @allure.story("场景2：平仓的停止功能校验")
    @allure.description("""
    ### 测试说明
    - 前置条件：有vps策略和vps跟单
      1. 进行开仓，手数范围0.1-1，总订单5
      2. 进行平仓
      3. 发送停止请求
      4. 校验平仓的订单数，应该不等于5
      5. 进行平仓-正常平仓
      6. 校验平仓的订单数,等于5
    - 预期结果：平仓的停止功能正确
    """)
    class TestVPStradingOrders2(APITestBase):
        @allure.title("VPS交易下单-复制下单请求")
        def test_copy_order_send(self, logged_session, var_manager):
            # 发送VPS交易下单-复制下单请求
            global symbol
            masOrderSend = var_manager.get_variable("masOrderSend")
            symbol = masOrderSend["symbol"]
            vps_trader_user_id = var_manager.get_variable("vps_trader_user_id")
            data = {
                "traderList": [vps_trader_user_id],
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

        @allure.title("数据库查询-获取停止的order_no")
        def test_copy_verify_db(self, var_manager, db_transaction):
            """验证复制下单后数据库中的订单数据正确性"""
            with allure.step("查询复制订单详情数据"):
                global order_no
                vps_trader_id = var_manager.get_variable("vps_trader_id")
                sql = """
                    SELECT 
                        order_no
                    FROM 
                        follow_order_instruct
                    WHERE instruction_type = %s
                        AND cloud_type = %s
                        AND min_lot_size = %s
                        AND max_lot_size = %s
                        AND trader_id = %s
                    """
                params = ("1", "0", "1.00", "0.10", vps_trader_id)

                # 轮询等待数据库记录
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="create_time"
                )

            with allure.step("执行复制下单数据校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行复制下单校验")

                # 订单状态校验
                order_no = db_data[0]["order_no"]
                print("order_no:", order_no)

        @allure.title("VPS交易下单-交易平仓-平仓设置30秒间隔")
        def test_copy_order_close(self, var_manager, logged_session):
            vps_trader_user_id = var_manager.get_variable("vps_trader_user_id")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 30000,
                "traderList": [vps_trader_user_id],
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
            vps_trader_user_id = var_manager.get_variable("vps_trader_user_id")
            # 发送停止请求
            params = {
                "orderNo": "",
                "traderList": [vps_trader_user_id],
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

        @allure.title("数据库校验-交易平仓-主指令及订单详情数据检查-平仓订单不等于开仓总订单数")
        def test_dbquery_orderSend(self, var_manager, db_transaction):
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
                    new_user["account"],
                    "changjing2"
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="foi.create_time"
                )
            with allure.step("验证订单数量"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行复制平仓校验")

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
                    vps_user_accounts_1,
                    "changjing2",
                    vps_addslave_id,
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="foi.create_time"
                )
            with allure.step("验证订单数量"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法进行复制平仓校验")

                self.verify_data(
                    actual_value=len(db_data),
                    expected_value=5,
                    op=CompareOp.NE,
                    message=f"平仓的订单数量应该不是5",
                    attachment_name="订单数量详情"
                )
                logging.info(f"平仓的订单数量应该不是5，结果有{len(db_data)}个订单")

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
                        message=f"正常平仓，应该有5个平仓订单",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"正常平仓，应该有5个平仓订单，结果有{len(db_data)}个订单")

        @allure.title("数据库校验-交易平仓-跟单指令及订单详情数据检查-有订单")
        def test_dbquery_addsalve_orderSendclose2(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
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
                    vps_user_accounts_1,
                    "changjing2",
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

                with allure.step("验证订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=5,
                        op=CompareOp.EQ,
                        message=f"正常平仓，应该有5个平仓订单",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"正常平仓，应该有5个平仓订单，结果有{len(db_data)}个订单")

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
    class TestVPStradingOrders3(APITestBase):
        @pytest.mark.url("vps")
        @allure.title("修改跟单账号为反向跟单")
        def test_follow_updateSlave(self, var_manager, logged_session, encrypted_password):
            with allure.step("1. 修改跟单方向为反向"):
                # 1. 修改跟单方向为反向followDirection 1:反向 0：正向
                new_user = var_manager.get_variable("new_user")
                vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
                vps_trader_id = var_manager.get_variable("vps_trader_id")
                vps_addslave_id = var_manager.get_variable("vps_addslave_id")
                platformId = var_manager.get_variable("platformId")
                data = {
                    "traderId": vps_trader_id,
                    "platform": new_user["platform"],
                    "account": vps_user_accounts_1,
                    "password": encrypted_password,
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
                    "id": vps_addslave_id,
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

        @allure.title("VPS交易下单-复制下单请求")
        def test_copy_order_send(self, logged_session, var_manager):
            # 发送VPS交易下单-复制下单请求
            global symbol
            masOrderSend = var_manager.get_variable("masOrderSend")
            symbol = masOrderSend["symbol"]
            vps_trader_user_id = var_manager.get_variable("vps_trader_user_id")
            data = {
                "traderList": [vps_trader_user_id],
                "type": 0,
                "tradeType": 1,
                "intervalTime": 0,
                "symbol": symbol,
                "placedType": 0,
                "startSize": "0.10",
                "endSize": "1.00",
                "totalNum": "4",
                "totalSzie": "",
                "remark": "changjing3"
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
        def test_copy_order_close(self, var_manager, logged_session):
            vps_user_ids_1 = var_manager.get_variable("vps_user_ids_1")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 0,
                "num": "",
                "traderList": [
                    vps_user_ids_1
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
        def test_dbquery_addsalve_orderSendclose(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
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
                    vps_user_accounts_1,
                    "changjing3",
                    vps_addslave_id,
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
        def test_copy_order_close2(self, var_manager, logged_session):
            vps_user_ids_1 = var_manager.get_variable("vps_user_ids_1")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 0,
                "num": "",
                "traderList": [vps_user_ids_1],
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
        def test_dbquery_addsalve_orderSendclose2(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
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
                    vps_user_accounts_1,
                    "changjing3",
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
        def test_copy_order_close3(self, var_manager, logged_session):
            vps_trader_user_id = var_manager.get_variable("vps_trader_user_id")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 0,
                "traderList": [vps_trader_user_id],
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
                    "changjing3"
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

    @allure.story("场景4：平仓的订单方向功能校验-buy sell")
    @allure.description("""
    ### 测试说明
    - 前置条件：有vps策略和vps跟单
      1. 修改跟单账号，跟单方向-反向sell
      2. 进行开仓，手数范围：0.1-1，总订单数量4
      3. 交易下单-跟单账号自己平仓-buy
      4. 校验平仓的订单数，应该不等于4
      5. 交易下单-跟单账号自己平仓-buy sell
      6. 校验平仓的订单数,等于4
    - 预期结果：平仓的订单方向功能正确
    """)
    class TestVPStradingOrders4(APITestBase):
        @pytest.mark.url("vps")
        @allure.title("修改跟单账号为反向跟单")
        def test_follow_updateSlave(self, var_manager, logged_session, encrypted_password):
            with allure.step("1. 修改跟单方向为反向"):
                # 1. 修改跟单方向为反向followDirection 1:反向 0：正向
                new_user = var_manager.get_variable("new_user")
                vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
                vps_trader_id = var_manager.get_variable("vps_trader_id")
                vps_addslave_id = var_manager.get_variable("vps_addslave_id")
                platformId = var_manager.get_variable("platformId")
                data = {
                    "traderId": vps_trader_id,
                    "platform": new_user["platform"],
                    "account": vps_user_accounts_1,
                    "password": encrypted_password,
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
                    "id": vps_addslave_id,
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

        @allure.title("VPS交易下单-复制下单请求")
        def test_copy_order_send(self, logged_session, var_manager):
            # 发送VPS交易下单-复制下单请求
            global symbol
            masOrderSend = var_manager.get_variable("masOrderSend")
            symbol = masOrderSend["symbol"]
            vps_trader_user_id = var_manager.get_variable("vps_trader_user_id")
            data = {
                "traderList": [vps_trader_user_id],
                "type": 0,
                "tradeType": 1,
                "intervalTime": 0,
                "symbol": symbol,
                "placedType": 0,
                "startSize": "0.10",
                "endSize": "1.00",
                "totalNum": "4",
                "totalSzie": "",
                "remark": "changjing4"
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
        def test_copy_order_close(self, var_manager, logged_session):
            vps_user_ids_1 = var_manager.get_variable("vps_user_ids_1")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 0,
                "num": "",
                "traderList": [
                    vps_user_ids_1
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

        @allure.title("数据库校验-交易平仓-主指令及订单详情数据检查-没有订单")
        def test_dbquery_orderSendclose(self, var_manager, db_transaction):
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
                                     fod.close_time,
                                     fod.comment,
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
                                    """
                params = (
                    '1',
                    new_user["account"],
                    "changjing4"
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

        @allure.title("VPS交易下单-交易平仓-跟单账号平仓-buy sell")
        def test_copy_order_close2(self, var_manager, logged_session):
            vps_user_ids_1 = var_manager.get_variable("vps_user_ids_1")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 0,
                "num": "",
                "traderList": [vps_user_ids_1],
                "closeType": 2,
                "remark": "",
                "symbol": "XAUUSD",
                "type": 2
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
                                  fod.close_time,
                                  fod.comment,
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
                    vps_user_accounts_1,
                    vps_addslave_id,
                    "changjing4"
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
        def test_copy_order_close3(self, var_manager, logged_session):
            vps_trader_user_id = var_manager.get_variable("vps_trader_user_id")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 0,
                "traderList": [vps_trader_user_id],
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
                new_user = var_manager.get_variable("new_user")
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
                    "changjing4"
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

    @allure.story("场景5：平仓的订单方向功能校验-buy")
    @allure.description("""
    ### 测试说明
    - 前置条件：有vps策略和vps跟单
      1. 修改跟单账号，跟单方向-正向
      2. 进行开仓，手数范围：0.1-1，总订单数量4
      3. 交易下单-跟单账号自己平仓-sell
      4. 校验平仓的订单数，应该不等于4
      5. 交易下单-跟单账号自己平仓-buy
      6. 校验平仓的订单数,等于4
    - 预期结果：平仓的订单方向功能正确
    """)
    class TestVPStradingOrders5(APITestBase):
        @pytest.mark.url("vps")
        @allure.title("修改跟单账号为正向跟单")
        def test_follow_updateSlave(self, var_manager, logged_session, encrypted_password):
            with allure.step("1. 修改跟单方向为正向"):
                # 1. 修改跟单方向为正向followDirection 1:反向 0：正向
                new_user = var_manager.get_variable("new_user")
                vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
                vps_trader_id = var_manager.get_variable("vps_trader_id")
                vps_addslave_id = var_manager.get_variable("vps_addslave_id")
                platformId = var_manager.get_variable("platformId")
                data = {
                    "traderId": vps_trader_id,
                    "platform": new_user["platform"],
                    "account": vps_user_accounts_1,
                    "password": encrypted_password,
                    "remark": "",
                    "followDirection": 0,
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
                    "id": vps_addslave_id,
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

        @allure.title("VPS交易下单-复制下单请求")
        def test_copy_order_send(self, logged_session, var_manager):
            # 发送VPS交易下单-复制下单请求
            global symbol
            masOrderSend = var_manager.get_variable("masOrderSend")
            symbol = masOrderSend["symbol"]
            vps_trader_user_id = var_manager.get_variable("vps_trader_user_id")
            data = {
                "traderList": [vps_trader_user_id],
                "type": 0,
                "tradeType": 1,
                "intervalTime": 0,
                "symbol": symbol,
                "placedType": 0,
                "startSize": "0.10",
                "endSize": "1.00",
                "totalNum": "4",
                "totalSzie": "",
                "remark": "changjing5"
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

        @allure.title("VPS交易下单-交易平仓-跟单账号平仓-sell")
        def test_copy_order_close(self, var_manager, logged_session):
            vps_user_ids_1 = var_manager.get_variable("vps_user_ids_1")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 0,
                "num": "",
                "traderList": [
                    vps_user_ids_1
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
                            """
                params = (
                    '1',
                    new_user["account"],
                    "changjing5"
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

        @allure.title("VPS交易下单-交易平仓-跟单账号平仓-buy")
        def test_copy_order_close2(self, var_manager, logged_session):
            vps_user_ids_1 = var_manager.get_variable("vps_user_ids_1")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 0,
                "num": "",
                "traderList": [vps_user_ids_1],
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
                    vps_user_accounts_1,
                    "changjing5",
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
        def test_copy_order_close3(self, var_manager, logged_session):
            vps_trader_user_id = var_manager.get_variable("vps_trader_user_id")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 0,
                "traderList": [vps_trader_user_id],
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
                    "changjing5"
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

    @allure.story("场景6：平仓的订单数量功能校验-4")
    @allure.description("""
    ### 测试说明
    - 前置条件：有vps策略和vps跟单
      1. 进行开仓，手数范围：0.1-1，总订单数量4
      2. 进行平仓-订单数量2
      3. 校验平仓的订单数，应该等于2
      4. 进行平仓-订单数量2
      5. 校验平仓的订单数,等于4
    - 预期结果：平仓的订单数量功能正确
    """)
    class TestVPStradingOrders6(APITestBase):
        @allure.title("VPS交易下单-复制下单请求")
        def test_copy_order_send(self, logged_session, var_manager):
            # 发送VPS交易下单-复制下单请求
            global symbol
            masOrderSend = var_manager.get_variable("masOrderSend")
            symbol = masOrderSend["symbol"]
            vps_trader_user_id = var_manager.get_variable("vps_trader_user_id")
            data = {
                "traderList": [vps_trader_user_id],
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

        @allure.title("VPS交易下单-交易平仓-平仓2个订单")
        def test_copy_order_close(self, var_manager, logged_session):
            vps_trader_user_id = var_manager.get_variable("vps_trader_user_id")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 0,
                "num": "2",
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

        @allure.title("数据库校验-交易平仓-跟单指令及订单详情数据检查-有2个订单")
        def test_dbquery_addsalve_orderSendclose(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
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
                    vps_user_accounts_1,
                    "changjing6",
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
                self.verify_data(
                    actual_value=len(db_data),
                    expected_value=2,
                    op=CompareOp.EQ,
                    message=f"平仓的订单数量功能正确，应该有2个平仓订单",
                    attachment_name="订单数量详情"
                )
                logging.info(f"平仓的订单数量功能正确，应该有2个平仓订单，结果有{len(db_data)}个订单")

        @allure.title("VPS交易下单-交易平仓-平仓2个订单")
        def test_copy_order_close2(self, var_manager, logged_session):
            vps_trader_user_id = var_manager.get_variable("vps_trader_user_id")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 0,
                "num": "2",
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

        @allure.title("数据库校验-交易平仓-主指令及订单详情数据检查-有4个订单")
        def test_dbquery_orderSendclose(self, var_manager, db_transaction):
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
                    "changjing6",
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
                    vps_user_accounts_1,
                    "changjing6",
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

    @allure.story("场景7：平仓的订单数量功能校验-0/8")
    @allure.description("""
    ### 测试说明
    - 前置条件：有vps策略和vps跟单
      1. 进行开仓，手数范围：0.1-1，总订单数量4
      2. 进行平仓-订单数量0
      3. 校验平仓的订单数，应该没有平仓订单
      4. 进行平仓-订单数量8
      5. 校验平仓的订单数,等于4
    - 预期结果：平仓的订单数量功能正确
    """)
    class TestVPStradingOrders7(APITestBase):
        @allure.title("VPS交易下单-复制下单请求")
        def test_copy_order_send(self, logged_session, var_manager):
            # 发送VPS交易下单-复制下单请求
            global symbol
            masOrderSend = var_manager.get_variable("masOrderSend")
            symbol = masOrderSend["symbol"]
            vps_trader_user_id = var_manager.get_variable("vps_trader_user_id")
            data = {
                "traderList": [vps_trader_user_id],
                "type": 0,
                "tradeType": 1,
                "intervalTime": 0,
                "symbol": symbol,
                "placedType": 0,
                "startSize": "0.10",
                "endSize": "1.00",
                "totalNum": "4",
                "totalSzie": "",
                "remark": "changjing7"
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

        @allure.title("VPS交易下单-交易平仓-平仓订单数0")
        def test_copy_order_close(self, var_manager, logged_session):
            vps_trader_user_id = var_manager.get_variable("vps_trader_user_id")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 0,
                "num": "0",
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
                "总单数最少一单",
                "响应msg字段应为：总单数最少一单"
            )

        @allure.title("数据库校验-交易平仓-主指令及订单详情数据检查-没有订单")
        def test_dbquery_orderSendclose(self, var_manager, db_transaction):
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
                            """
                params = (
                    '1',
                    new_user["account"],
                    "changjing7"
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

        @allure.title("VPS交易下单-交易平仓-平仓订单数8")
        def test_copy_order_close2(self, var_manager, logged_session):
            vps_trader_user_id = var_manager.get_variable("vps_trader_user_id")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 0,
                "num": "8",
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

        @allure.title("数据库校验-交易平仓-主指令及订单详情数据检查-有4个订单")
        def test_dbquery_orderSendclose2(self, var_manager, db_transaction):
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
                    "changjing7",
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
                    vps_user_accounts_1,
                    "changjing7",
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

    @allure.story("场景8：平仓的订单类型功能校验-内部订单")
    @allure.description("""
    ### 测试说明
    - 前置条件：有vps策略和vps跟单
      1. 进行开仓，手数范围：0.1-1，总订单数量4
      2. 进行平仓-订单类型-外部订单
      3. 校验平仓的订单数，应该没有平仓订单
      4. 进行平仓-订单类型-内部订单
      5. 校验平仓的订单数,等于4
    - 预期结果：平仓的订单类型功能正确
    """)
    class TestVPStradingOrders8(APITestBase):
        @allure.title("VPS交易下单-复制下单请求")
        def test_copy_order_send(self, logged_session, var_manager):
            # 发送VPS交易下单-复制下单请求
            global symbol
            masOrderSend = var_manager.get_variable("masOrderSend")
            symbol = masOrderSend["symbol"]
            vps_trader_user_id = var_manager.get_variable("vps_trader_user_id")
            data = {
                "traderList": [vps_trader_user_id],
                "type": 0,
                "tradeType": 1,
                "intervalTime": 0,
                "symbol": symbol,
                "placedType": 0,
                "startSize": "0.10",
                "endSize": "1.00",
                "totalNum": "4",
                "totalSzie": "",
                "remark": "changjing8"
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

        @allure.title("VPS交易下单-交易平仓-订单类型-外部订单")
        def test_copy_order_close(self, var_manager, logged_session):
            vps_trader_user_id = var_manager.get_variable("vps_trader_user_id")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 0,
                "num": "",
                "traderList": [vps_trader_user_id],
                "closeType": 1,
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

        @allure.title("数据库校验-交易平仓-主指令及订单详情数据检查-没有订单")
        def test_dbquery_orderSendclose(self, var_manager, db_transaction):
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
                            """
                params = (
                    '1',
                    new_user["account"],
                    "changjing8"
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

        @allure.title("VPS交易下单-交易平仓-订单类型-内部订单")
        def test_copy_order_close2(self, var_manager, logged_session):
            vps_trader_user_id = var_manager.get_variable("vps_trader_user_id")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 0,
                "num": "",
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

        @allure.title("数据库校验-交易平仓-主指令及订单详情数据检查-有4个订单")
        def test_dbquery_orderSendclose2(self, var_manager, db_transaction):
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
                    "changjing8"
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
                    vps_user_accounts_1,
                    "changjing8",
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

        # time.sleep(30)

    @allure.story("场景9：平仓的订单类型功能校验-外部订单")
    @allure.description("""
    ### 测试说明
    - 前置条件：有vps策略和vps跟单
      1. MT4登录，然后进行开仓
      2. 进行平仓-订单类型-内部订单
      3. 校验平仓的订单数，应该没有平仓订单
      4. 进行平仓-订单类型-外部订单
      5. 校验平仓的订单数,等于1
    - 预期结果：平仓的订单类型功能正确
    """)
    @pytest.mark.skipif(True, reason=SKIP_REASON)
    class TestVPStradingOrders9(APITestBase):
        @allure.title("登录MT4账号获取token")
        def test_mt4_login(self, var_manager):
            global token_mt4, headers
            max_retries = 5  # 最大重试次数
            retry_interval = 5  # 重试间隔（秒）
            token_mt4 = None

            # 用于验证token格式的正则表达式（UUID格式）
            uuid_pattern = re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')

            for attempt in range(max_retries):
                try:
                    url = "https://mt4.mtapi.io/Connect?user=300151&password=Test123456&host=47.238.99.66&port=443&connectTimeoutSeconds=30"

                    headers = {
                        'Authorization': 'e5f9f574-fd0a-42bd-904b-3a7a088de27e',
                        'x-sign': '417B110F1E71BD2CFE96366E67849B0B',
                        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
                        'Content-Type': 'application/json',
                        'Accept': '*/*',
                        'Host': 'mt4.mtapi.io',
                        'Connection': 'keep-alive'
                    }

                    response = requests.request("GET", url, headers=headers, data={})
                    response_text = response.text.strip()  # 去除可能的空白字符

                    logging.info(f"第{attempt + 1}次登录尝试 - 响应内容: {response_text}")

                    # 验证响应是否为有效的UUID格式token
                    if uuid_pattern.match(response_text):
                        token_mt4 = response_text
                        logging.info(f"第{attempt + 1}次尝试成功 - 获取到token: {token_mt4}")
                        break
                    else:
                        logging.warning(f"第{attempt + 1}次尝试失败 - 无效的token格式: {response_text}")

                except Exception as e:
                    logging.error(f"第{attempt + 1}次尝试发生异常: {str(e)}")

                # 如果不是最后一次尝试，等待后重试
                if attempt < max_retries - 1:
                    logging.info(f"将在{retry_interval}秒后进行第{attempt + 2}次重试...")
                    time.sleep(retry_interval)

            # 最终验证结果
            if not token_mt4 or not uuid_pattern.match(token_mt4):
                logging.error(f"经过{max_retries}次尝试后，MT4登录仍失败")
                assert False, "MT4登录失败"
            else:
                print(f"登录MT4账号获取token: {token_mt4}")
                logging.info(f"登录MT4账号获取token: {token_mt4}")

        @allure.title("MT4平台开仓操作")
        def test_mt4_open(self, var_manager):
            url = f"https://mt4.mtapi.io/OrderSend?id={token_mt4}&symbol=XAUUSD&operation=Buy&volume=1&placedType=Client&price=0.00"

            payload = ""
            self.response = requests.request("GET", url, headers=headers, data=payload)
            self.json_utils = JsonPathUtils()
            self.response = self.response.json()
            ticket = self.json_utils.extract(self.response, "$.ticket")
            print(ticket)
            logging.info(ticket)

        @allure.title("VPS交易下单-交易平仓-订单类型-内部订单")
        def test_copy_order_close(self, var_manager, logged_session):
            vps_trader_user_id = var_manager.get_variable("vps_trader_user_id")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 0,
                "num": "",
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

        @allure.title("数据库校验-交易平仓-主指令及订单详情数据检查-没有订单")
        def test_dbquery_orderSendclose(self, var_manager, db_transaction):
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
                    new_user["account"],
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

        @allure.title("VPS交易下单-交易平仓-订单类型-外部订单")
        def test_copy_order_close2(self, var_manager, logged_session):
            vps_trader_user_id = var_manager.get_variable("vps_trader_user_id")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 0,
                "num": "",
                "traderList": [vps_trader_user_id],
                "closeType": 1,
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

        @allure.title("数据库校验-交易平仓-主指令及订单详情数据检查-有1个订单")
        def test_dbquery_orderSendclose2(self, var_manager, db_transaction):
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
                            fod.close_time,
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
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )
            with allure.step("2. 数据校验"):
                self.verify_data(
                    actual_value=len(db_data),
                    expected_value=1,
                    op=CompareOp.EQ,
                    message=f"平仓的订单数量应该是1",
                    attachment_name="订单数量详情"
                )
                logging.info(f"平仓的订单数量应该是1，结果有{len(db_data)}个订单")

        @allure.title("数据库校验-交易平仓-跟单指令及订单详情数据检查-有1个订单")
        def test_dbquery_addsalve_orderSendclose2(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
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
                self.verify_data(
                    actual_value=len(db_data),
                    expected_value=1,
                    op=CompareOp.EQ,
                    message=f"平仓的订单数量应该是1",
                    attachment_name="订单数量详情"
                )
                logging.info(f"平仓的订单数量应该是1，结果有{len(db_data)}个订单")

    @allure.story("场景10：平仓的订单类型功能校验-全部订单")
    @allure.description("""
    ### 测试说明
    - 前置条件：有vps策略和vps跟单
      1. 进行开仓，手数范围：0.1-1，总订单数量4
      2. 进行平仓-订单类型-外部订单
      3. 校验平仓的订单数，应该没有平仓订单
      4. 进行平仓-订单类型-全部订单
      5. 校验平仓的订单数,等于4
    - 预期结果：平仓的订单类型功能正确
    """)
    class TestVPStradingOrders10(APITestBase):
        @allure.title("VPS交易下单-复制下单请求")
        def test_copy_order_send(self, logged_session, var_manager):
            # 发送VPS交易下单-复制下单请求
            global symbol
            masOrderSend = var_manager.get_variable("masOrderSend")
            symbol = masOrderSend["symbol"]
            vps_trader_user_id = var_manager.get_variable("vps_trader_user_id")
            data = {
                "traderList": [vps_trader_user_id],
                "type": 0,
                "tradeType": 1,
                "intervalTime": 0,
                "symbol": symbol,
                "placedType": 0,
                "startSize": "0.10",
                "endSize": "1.00",
                "totalNum": "4",
                "totalSzie": "",
                "remark": "changjing10"
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

        @allure.title("VPS交易下单-交易平仓-订单类型-外部订单")
        def test_copy_order_close(self, var_manager, logged_session):
            vps_trader_user_id = var_manager.get_variable("vps_trader_user_id")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 0,
                "num": "",
                "traderList": [vps_trader_user_id],
                "closeType": 1,
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

        @allure.title("数据库校验-交易平仓-主指令及订单详情数据检查-没有订单")
        def test_dbquery_orderSendclose(self, var_manager, db_transaction):
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
                            """
                params = (
                    '1',
                    new_user["account"],
                    "changjing10"
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

        @allure.title("VPS交易下单-交易平仓-订单类型-内部订单")
        def test_copy_order_close2(self, var_manager, logged_session):
            vps_trader_user_id = var_manager.get_variable("vps_trader_user_id")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 0,
                "num": "",
                "traderList": [vps_trader_user_id],
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

        @allure.title("数据库校验-交易平仓-主指令及订单详情数据检查-有4个订单")
        def test_dbquery_orderSendclose2(self, var_manager, db_transaction):
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
                            foi.status
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
                    "changjing10"
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
                    vps_user_accounts_1,
                    "changjing10",
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

    @allure.story("场景11：平仓的订单备注功能校验")
    @allure.description("""
    ### 测试说明
    - 前置条件：有vps策略和vps跟单
      1. 进行开仓，手数范围：0.1-1，总订单数量4,订单备注：ceshipingcangbeizhu
      2. 进行平仓-订单备注：xxxxxxxxxxx
      3. 校验平仓的订单数，应该没有平仓订单
      4. 进行平仓-订单备注：ceshipingcangbeizhu
      5. 校验平仓的订单数,等于4
    - 预期结果：平仓的订单备注功能正确
    """)
    class TestVPStradingOrders11(APITestBase):
        @allure.title("VPS交易下单-复制下单请求")
        def test_copy_order_send(self, logged_session, var_manager):
            # 发送VPS交易下单-复制下单请求
            global symbol
            masOrderSend = var_manager.get_variable("masOrderSend")
            symbol = masOrderSend["symbol"]
            vps_trader_user_id = var_manager.get_variable("vps_trader_user_id")
            data = {
                "traderList": [vps_trader_user_id],
                "type": 0,
                "tradeType": 1,
                "intervalTime": 0,
                "symbol": symbol,
                "placedType": 0,
                "startSize": "0.10",
                "endSize": "1.00",
                "totalNum": "4",
                "totalSzie": "",
                "remark": "ceshipingcangbeizhu"
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

        @allure.title("VPS交易下单-交易平仓-订单备注：xxxxxxxxxxx")
        def test_copy_order_close(self, var_manager, logged_session):
            vps_trader_user_id = var_manager.get_variable("vps_trader_user_id")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 0,
                "num": "",
                "traderList": [vps_trader_user_id],
                "closeType": 0,
                "remark": "xxxxxxxxxxx",
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

        @allure.title("数据库校验-交易平仓-主指令及订单详情数据检查-没有订单")
        def test_dbquery_orderSendclose(self, var_manager, db_transaction):
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
                        """
                params = (
                    '1',
                    new_user["account"],
                    "ceshipingcangbeizhu"
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

        @allure.title("VPS交易下单-交易平仓-订单备注：ceshipingcangbeizhu")
        def test_copy_order_close2(self, var_manager, logged_session):
            vps_trader_user_id = var_manager.get_variable("vps_trader_user_id")
            # 发送平仓请求
            data = {
                "flag": 0,
                "intervalTime": 0,
                "num": "",
                "traderList": [vps_trader_user_id],
                "closeType": 0,
                "remark": "ceshipingcangbeizhu",
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
        def test_dbquery_orderSendclose2(self, var_manager, db_transaction):
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
                            foi.status
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
                    "ceshipingcangbeizhu"
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
                    vps_user_accounts_1,
                    "ceshipingcangbeizhu",
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
