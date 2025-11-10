import time
import allure
import logging
import pytest
from lingkuan_919.conftest import var_manager
from lingkuan_919.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("VPS策略下单-修改跟单账号")
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
            new_user = var_manager.get_variable("new_user")
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            data = {
                "id": vps_trader_id,
                "account": new_user["account"],
                "password": encrypted_password,
                "platformType": 0,
                "remark": "",
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
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )

            with allure.step("2. 校验数据"):
                # 提取数据库中的值
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")
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
                "remark": "changjing1",
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
            with allure.step("1. 获取订单详情表账号数据"):
                vps_user_accounts_5 = var_manager.get_variable("vps_user_accounts_5")
                sql = f"""
                        SELECT 
                            fod.size,
                            fod.comment,
                            fod.send_no,
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
                            foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
                        WHERE foi.operation_type = %s
                            AND fod.account = %s
                            AND fod.comment = %s
                            """
                params = (
                    '0',
                    vps_user_accounts_5,
                    "changjing1"
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="foi.create_time"
                )

            with allure.step("2. 校验数据"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证详情总手数"):
                    trader_ordersend = var_manager.get_variable("trader_ordersend")
                    totalSzie = trader_ordersend["totalSzie"]
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(totalSzie),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

                with allure.step("验证币种"):
                    symbol = db_data[0]["symbol"]
                    self.verify_data(
                        actual_value=symbol,
                        expected_value=("XAUUSD@", "XAUUSD"),
                        op=CompareOp.IN,
                        use_isclose=False,
                        message="币种应符合预期",
                        attachment_name="币种详情"
                    )
                    logging.info(f"币种验证通过: {symbol}")

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库校验-策略开仓-修改币种p")
        def test_dbtrader_cfdp(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                vps_user_accounts_6 = var_manager.get_variable("vps_user_accounts_6")

                sql = f"""
                        SELECT 
                            fod.size,
                            fod.comment,
                            fod.send_no,
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
                            foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
                        WHERE foi.operation_type=%s
                            AND fod.account = %s
                            AND fod.comment = %s
                            """
                params = (
                    '0',
                    vps_user_accounts_6,
                    "changjing1"
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="foi.create_time"
                )

            with allure.step("2. 校验数据"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=(0.02, 0.03, 1.0),
                        op=CompareOp.IN,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

                with allure.step("验证币种"):
                    symbol = db_data[0]["symbol"]
                    self.verify_data(
                        actual_value=symbol,
                        expected_value=("XAUUSD.p", "XAUUSD"),
                        op=CompareOp.IN,
                        use_isclose=False,
                        message="币种应符合预期",
                        attachment_name="币种详情"
                    )
                    logging.info(f"币种验证通过: {symbol}")

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库校验-策略开仓-修改币种min")
        def test_dbtrader_cfdmin(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                vps_user_accounts_7 = var_manager.get_variable("vps_user_accounts_7")

                sql = f"""
                        SELECT 
                            fod.size,
                            fod.comment,
                            fod.send_no,
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
                            foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
                        WHERE foi.operation_type=%s
                            AND fod.account = %s
                            AND fod.comment = %s
                            """
                params = (
                    '0',
                    vps_user_accounts_7,
                    "changjing1"
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="foi.create_time"
                )

            with allure.step("2. 校验数据"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=(10, 1.0),
                        op=CompareOp.IN,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

                with allure.step("验证币种"):
                    symbol = db_data[0]["symbol"]
                    self.verify_data(
                        actual_value=symbol,
                        expected_value=("XAUUSD.min", "XAUUSD"),
                        op=CompareOp.IN,
                        use_isclose=False,
                        message="币种应符合预期",
                        attachment_name="币种详情"
                    )
                    logging.info(f"币种验证通过: {symbol}")

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
            with allure.step("1. 获取订单详情表账号数据"):
                vps_user_accounts_5 = var_manager.get_variable("vps_user_accounts_5")

                sql = f"""
                        SELECT 
                            fod.size,
                            fod.comment,
                            fod.close_no,
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
                        WHERE foi.operation_type=%s
                            AND fod.account = %s
                            AND fod.comment = %s
                            """
                params = (
                    "1",
                    vps_user_accounts_5,
                    "changjing1"
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="foi.create_time"
                )

            with allure.step("2. 校验数据"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证详情总手数"):
                    trader_ordersend = var_manager.get_variable("trader_ordersend")
                    totalSzie = trader_ordersend["totalSzie"]
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(totalSzie),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

                with allure.step("验证币种"):
                    symbol = db_data[0]["symbol"]
                    self.verify_data(
                        actual_value=symbol,
                        expected_value=("XAUUSD@", "XAUUSD"),
                        op=CompareOp.IN,
                        use_isclose=False,
                        message="币种应符合预期",
                        attachment_name="币种详情"
                    )
                    logging.info(f"币种验证通过: {symbol}")

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库校验-策略平仓-修改币种p")
        def test_dbclose_cfdp(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                vps_user_accounts_6 = var_manager.get_variable("vps_user_accounts_6")

                sql = f"""
                        SELECT 
                            fod.size,
                            fod.comment,
                            fod.close_no,
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
                        WHERE foi.operation_type=%s
                            AND fod.account = %s
                            AND fod.comment = %s
                            """
                params = (
                    '1',
                    vps_user_accounts_6,
                    "changjing1"
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="foi.create_time"
                )

            with allure.step("2. 校验数据"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=(0.02, 0.03, 1.0),
                        op=CompareOp.IN,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

                with allure.step("验证币种"):
                    symbol = db_data[0]["symbol"]
                    self.verify_data(
                        actual_value=symbol,
                        expected_value=("XAUUSD.p", "XAUUSD"),
                        op=CompareOp.IN,
                        use_isclose=False,
                        message="币种应符合预期",
                        attachment_name="币种详情"
                    )
                    logging.info(f"币种验证通过: {symbol}")

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库校验-策略平仓-修改币种min")
        def test_dbclose_cfdmin(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                vps_user_accounts_7 = var_manager.get_variable("vps_user_accounts_7")

                sql = f"""
                        SELECT 
                            fod.size,
                            fod.comment,
                            fod.close_no,
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
                        WHERE foi.operation_type=%s
                            AND fod.account = %s
                            AND fod.comment = %s
                            """
                params = (
                    '1',
                    vps_user_accounts_7,
                    "changjing1"
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="foi.create_time"
                )

            with allure.step("2. 校验数据"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=(10, 1.0),
                        op=CompareOp.IN,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

                with allure.step("验证币种"):
                    symbol = db_data[0]["symbol"]
                    self.verify_data(
                        actual_value=symbol,
                        expected_value=("XAUUSD.min", "XAUUSD"),
                        op=CompareOp.IN,
                        use_isclose=False,
                        message="币种应符合预期",
                        attachment_name="币种详情"
                    )
                    logging.info(f"币种验证通过: {symbol}")

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
                "remark": "changjing2",
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
                vps_user_accounts_2 = var_manager.get_variable("vps_user_accounts_2")

                sql = f"""
                        SELECT 
                            fod.size,
                            fod.comment,
                            fod.send_no,
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
                            foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
                        WHERE foi.operation_type=%s
                            AND fod.account = %s
                            AND fod.comment = %s
                    """
                params = (
                    '0',
                    vps_user_accounts_2,
                    "changjing2"
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="foi.create_time"
                )

            with allure.step("2. 校验数据"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证详情总手数"):
                    size = db_data[0]["size"]
                    self.verify_data(
                        actual_value=float(size),
                        expected_value=float(5),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {size}")

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库校验-策略开仓-跟单账号修改品种")
        def test_dbdetail_templateId3(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                vps_user_accounts_3 = var_manager.get_variable("vps_user_accounts_3")

                sql = f"""
                        SELECT 
                            fod.size,
                            fod.comment,
                            fod.send_no,
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
                            foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
                        WHERE foi.operation_type=%s
                            AND fod.account = %s
                            AND fod.comment = %s
                    """
                params = (
                    '0',
                    vps_user_accounts_3,
                    "changjing2"
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="foi.create_time"
                )

            with allure.step("2. 校验数据"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(3),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

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
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

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
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                vps_addsalve_euqit = db_data[0]["euqit"]
                var_manager.set_runtime_variable("vps_addsalve_euqit", vps_addsalve_euqit)
                logging.info(f"跟单账号净值：{vps_addsalve_euqit}")

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库校验-策略开仓-修改净值")
        def test_vps_dbtrader_euqit2(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                vps_user_accounts_4 = var_manager.get_variable("vps_user_accounts_4")

                sql = f"""
                        SELECT 
                            fod.size,
                            fod.comment,
                            fod.send_no,
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
                            foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
                        WHERE foi.operation_type=%s
                            AND fod.account = %s
                            AND fod.comment = %s
                    """
                params = (
                    '0',
                    vps_user_accounts_4,
                    "changjing2"
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="foi.create_time"
                )

            with allure.step("2. 校验数据"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                vps_addsalve_size_euqit = [record["size"] for record in db_data]
                var_manager.set_runtime_variable("vps_addsalve_size_euqit", vps_addsalve_size_euqit)
                total = sum(vps_addsalve_size_euqit)
                vps_dbtrader_euqit = var_manager.get_variable("vps_dbtrader_euqit")
                vps_addsalve_euqit = var_manager.get_variable("vps_addsalve_euqit")
                # 校验除数非零
                if vps_dbtrader_euqit == 0:
                    pytest.fail("vps_dbtrader_euqit为0，无法计算预期比例（避免除零）")

                true_size = vps_addsalve_euqit / vps_dbtrader_euqit * 1
                with allure.step("验证详情总手数"):
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(true_size),
                        op=CompareOp.EQ,
                        abs_tol=3,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

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
        @allure.title("数据库校验-策略平仓-跟单账号固定手数5")
        def test_dbclose_followParam5(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                vps_user_accounts_2 = var_manager.get_variable("vps_user_accounts_2")

                sql = f"""
                        SELECT 
                            fod.size,
                            fod.comment,
                            fod.send_no,
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
                            foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
                        WHERE foi.operation_type=%s
                            AND fod.account = %s
                            AND fod.comment = %s
                    """
                params = (
                    '0',
                    vps_user_accounts_2,
                    "changjing2"
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="foi.create_time"
                )

            with allure.step("2. 校验数据"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证详情总手数"):
                    size = db_data[0]["size"]
                    self.verify_data(
                        actual_value=float(size),
                        expected_value=float(5),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {size}")

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库校验-策略平仓-跟单账号修改品种")
        def test_dbclose_templateId3(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                vps_user_accounts_3 = var_manager.get_variable("vps_user_accounts_3")

                sql = f"""
                       SELECT 
                           fod.size,
                           fod.comment,
                           fod.send_no,
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
                           foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
                       WHERE foi.operation_type=%s
                           AND fod.account = %s
                           AND fod.comment = %s
                       """
                params = (
                    '0',
                    vps_user_accounts_3,
                    "changjing2"
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="foi.create_time"
                )

            with allure.step("2. 校验数据"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(3),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库校验-策略平仓-修改净值")
        def test_dbclose_euqit(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                vps_user_accounts_4 = var_manager.get_variable("vps_user_accounts_4")

                sql = f"""
                        SELECT 
                            fod.size,
                            fod.comment,
                            fod.send_no,
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
                            foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
                        WHERE foi.operation_type=%s
                            AND fod.account = %s
                            AND fod.comment = %s
                    """
                params = (
                    '0',
                    vps_user_accounts_4,
                    "changjing2"
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="foi.create_time"
                )

            with allure.step("2. 校验数据"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                vps_addsalve_size_euqit = [record["size"] for record in db_data]
                var_manager.set_runtime_variable("vps_addsalve_size_euqit", vps_addsalve_size_euqit)
                total = sum(vps_addsalve_size_euqit)
                vps_dbtrader_euqit = var_manager.get_variable("vps_dbtrader_euqit")
                vps_addsalve_euqit = var_manager.get_variable("vps_addsalve_euqit")
                # 校验除数非零
                if vps_dbtrader_euqit == 0:
                    pytest.fail("vps_dbtrader_euqit为0，无法计算预期比例（避免除零）")

                true_size = vps_addsalve_euqit / vps_dbtrader_euqit * 1
                with allure.step("验证详情总手数"):
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(true_size),
                        op=CompareOp.EQ,
                        abs_tol=3,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")
