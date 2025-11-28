import time
import allure
import logging
import pytest
from lingkuan_1126.conftest import var_manager
from lingkuan_1126.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("云策略-云策略列表-修改跟单账号")
class Testcloudtrader_moneyandscene:
    @allure.story("场景1：云策略-云策略列表-云跟单账号修改币种")
    @allure.description("""
    ### 用例说明
    - 前置条件：有云策略和云跟单
    - 操作步骤：
      1. 有三个账号，分别修改三个账号的后缀.@ .p .min
      2. 进行开仓
      3. 判断三个账号的币种手数是否正确
      4. 进行平仓
      5. 判断三个账号的币种手数是否正确
    - 预期结果：三个账号的币种手数正确
    """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    class Testcloudtrader_money(APITestBase):
        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("账号管理-账号列表-修改用户")
        def test_update_user(self, class_random_str, logged_session, var_manager, encrypted_password):
            # 1. 发送修改用户请求
            cloudTrader_user_ids_2 = var_manager.get_variable("cloudTrader_user_ids_2")
            cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
            new_user = var_manager.get_variable("new_user")
            cloudTrader_vps_ids_1 = var_manager.get_variable("cloudTrader_vps_ids_1")
            cloudTrader_vps_id = var_manager.get_variable("cloudTrader_vps_ids_2")
            cloudTrader_user_accounts_1 = var_manager.get_variable("cloudTrader_user_accounts_1")
            vpsId = var_manager.get_variable("vpsId")
            IP_ADDRESS = var_manager.get_variable("IP_ADDRESS")
            vpsname = var_manager.get_variable("vpsname")
            desc = IP_ADDRESS + "-" + vpsname + "-" + "-跟单账号"
            data = {
                "id": cloudTrader_user_ids_2,
                "account": cloudTrader_user_accounts_2,
                "password": encrypted_password,
                "platform": new_user["platform"],
                "accountType": "0",
                "platformType": 0,
                "serverNode": new_user["serverNode"],
                "remark": "参数化新增云策略账号",
                "sort": 100,
                "vpsDescs": [
                    {
                        "desc": desc,
                        "status": 0,
                        "statusExtra": "启动成功",
                        "forex": "",
                        "cfd": "",
                        "traderId": cloudTrader_vps_ids_1,
                        "sourceId": cloudTrader_vps_id,
                        "sourceAccount": cloudTrader_user_accounts_1,
                        "sourceName": "",
                        "loginNode": new_user["serverNode"],
                        "nodeType": 0,
                        "nodeName": "账号节点",
                        "type": None,
                        "vpsId": vpsId,
                        "vpsName": vpsname,
                        "ipAddress": IP_ADDRESS,
                        "traderType": 1,
                        "abRemark": None,
                        "accountMode": 0,
                        "cloudId": None
                    }
                ]
            }
            response = self.send_put_request(
                logged_session,
                "/mascontrol/user",
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
        def test_dbupdate_user(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 查询数据库验证是否编辑成功"):
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
                sql = f"SELECT * FROM follow_cloud_trader WHERE account = %s"
                params = (cloudTrader_user_accounts_2,)

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )

            with allure.step("2. 数据校验"):
                # 提取数据库中的值
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")
                cfd_value = db_data[0]["cfd"]
                # 允许为 None 或空字符串（去除空格后）
                assert cfd_value is None or cfd_value.strip() == "", f"修改个人信息失败（cfd字段应为空，实际值：{cfd_value}）"

        @allure.title("账号管理-交易下单-云策略账号复制下单")
        def test_bargain_masOrderSend(self, class_random_str, logged_session, var_manager):
            # 1. 发送云策略复制下单请求
            global cloudTrader_user_ids_2
            cloudTrader_user_ids_2 = var_manager.get_variable("cloudTrader_user_ids_2")
            data = {
                "traderList": [
                    cloudTrader_user_ids_2
                ],
                "type": 0,
                "tradeType": 1,
                "intervalTime": 0,
                "symbol": "XAUUSD",
                "placedType": 0,
                "startSize": "0.10",
                "endSize": "1.00",
                "totalNum": "3",
                "totalSzie": "1.00",
                "remark": class_random_str
            }

            response = self.send_post_request(
                logged_session,
                '/bargain/masOrderSend',
                json_data=data
            )

            # 2. 判断云策略复制下单是否成功
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库校验-云跟单账号策略开仓-修改币种@")
        def test_dbtrader_cfda(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                cloudTrader_user_accounts_8 = var_manager.get_variable("cloudTrader_user_accounts_8")
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
                    cloudTrader_user_accounts_8,
                    class_random_str
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
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
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
        @allure.title("数据库校验-云跟单账号策略开仓-修改币种p")
        def test_dbtrader_cfdp(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                cloudTrader_user_accounts_9 = var_manager.get_variable("cloudTrader_user_accounts_9")
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
                    cloudTrader_user_accounts_9,
                    class_random_str
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
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
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
        @allure.title("数据库校验-云跟单账号策略开仓-修改币种min")
        def test_dbtrader_cfdmin(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                cloudTrader_user_accounts_10 = var_manager.get_variable("cloudTrader_user_accounts_10")
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
                    cloudTrader_user_accounts_10,
                    class_random_str
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
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
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

        @allure.title("账号管理-交易下单-云策略平仓")
        def test_bargain_masOrderClose(self, class_random_str, logged_session, var_manager):
            cloudTrader_user_ids_2 = var_manager.get_variable("cloudTrader_user_ids_2")
            # 1. 发送平仓请求
            data = {
                "isCloseAll": 1,
                "intervalTime": 0,
                "traderList": [cloudTrader_user_ids_2]
            }
            response = self.send_post_request(
                logged_session,
                '/bargain/masOrderClose',
                json_data=data
            )

            # 2. 判断是否平仓成功
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

        @allure.title("云策略-云策略列表-平仓")
        def test_cloudTrader_OrderClose(self, class_random_str, logged_session, var_manager):
            cloudMaster_id = var_manager.get_variable("cloudMaster_id")
            # 1. 发送平仓请求
            data = {
                "isCloseAll": 1,
                "intervalTime": 0,
                "id": f"{cloudMaster_id}"
            }
            response = self.send_post_request(
                logged_session,
                '/mascontrol/cloudTrader/cloudOrderClose',
                json_data=data
            )

            # 2. 判断是否平仓成功
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库校验-云跟单账号策略平仓-修改币种@")
        def test_dbclose_cfda(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                cloudTrader_user_accounts_8 = var_manager.get_variable("cloudTrader_user_accounts_8")
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
                    cloudTrader_user_accounts_8,
                    class_random_str
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
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
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
        @allure.title("数据库校验-云跟单账号策略平仓-修改币种p")
        def test_dbclose_cfdp(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                cloudTrader_user_accounts_9 = var_manager.get_variable("cloudTrader_user_accounts_9")
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
                    cloudTrader_user_accounts_9,
                    class_random_str
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
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
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
        @allure.title("数据库校验-云跟单账号策略平仓-修改币种min")
        def test_dbclose_cfdmin(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                cloudTrader_user_accounts_10 = var_manager.get_variable("cloudTrader_user_accounts_10")
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
                    cloudTrader_user_accounts_10,
                    class_random_str
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
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
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

    @allure.story("场景2：云策略策略下单-跟单修改模式、品种")
    @allure.description("""
    ### 用例说明
    - 前置条件：有云策略和云跟单
    - 操作步骤：
      1. 有三个账号，分别修改三个账号：固定手数 品种 净值比例
      2. 进行开仓
      3. 判断三个账号的手数是否正确
      4. 进行平仓
      5. 判断三个账号的手数是否正确
    - 预期结果：三个账号的手数正确
    """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    class Testcloudtrader_Scence(APITestBase):
        @allure.title("账号管理-交易下单-云策略账号复制下单")
        def test_bargain_masOrderSend(self, class_random_str, logged_session, var_manager):
            # 1. 发送云策略复制下单请求
            global cloudTrader_user_ids_2
            cloudTrader_user_ids_2 = var_manager.get_variable("cloudTrader_user_ids_2")
            data = {
                "traderList": [
                    cloudTrader_user_ids_2
                ],
                "type": 0,
                "tradeType": 1,
                "intervalTime": 0,
                "symbol": "XAUUSD",
                "placedType": 0,
                "startSize": "0.10",
                "endSize": "1.00",
                "totalNum": "3",
                "totalSzie": "1.00",
                "remark": class_random_str
            }

            response = self.send_post_request(
                logged_session,
                '/bargain/masOrderSend',
                json_data=data
            )

            # 2. 判断云策略复制下单是否成功
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库校验-云跟单账号策略开仓-跟单账号固定手数")
        def test_dbdetail_followParam5(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                cloudTrader_user_accounts_5 = var_manager.get_variable("cloudTrader_user_accounts_5")
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
                    cloudTrader_user_accounts_5,
                    class_random_str
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
        @allure.title("数据库校验-云跟单账号策略开仓-跟单账号修改品种")
        def test_dbdetail_templateId3(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                cloudTrader_user_accounts_6 = var_manager.get_variable("cloudTrader_user_accounts_6")

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
                    cloudTrader_user_accounts_6,
                    class_random_str
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
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
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
        def test_dbtrader_euqit(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取主账号净值"):
                cloudTrader_vps_ids_2 = var_manager.get_variable("cloudTrader_vps_ids_2")

                sql = f"""
                            SELECT * FROM follow_trader WHERE id = %s
                            """
                params = (
                    cloudTrader_vps_ids_2
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

                cloud_euqit = db_data[0]["euqit"]
                var_manager.set_runtime_variable("cloud_euqit", cloud_euqit)
                logging.info(f"主账号净值：{cloud_euqit}")

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库-获取跟单账号净值")
        def test_dbaddsalve_euqit(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取跟单账号净值"):
                cloudTrader_vps_ids_6 = var_manager.get_variable("cloudTrader_vps_ids_6")

                sql = f"""
                        SELECT * FROM follow_trader WHERE id = %s
                        """
                params = (
                    cloudTrader_vps_ids_6
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

                cloudTrader_add_euqit = db_data[0]["euqit"]
                var_manager.set_runtime_variable("cloudTrader_add_euqit", cloudTrader_add_euqit)
                logging.info(f"跟单账号净值：{cloudTrader_add_euqit}")

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库校验-云跟单账号策略开仓-修改净值")
        def test_dbtrader_euqit2(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                cloudTrader_user_accounts_7 = var_manager.get_variable("cloudTrader_user_accounts_7")

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
                    cloudTrader_user_accounts_7,
                    class_random_str
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

                addsalve_size_euqit = [record["size"] for record in db_data]
                var_manager.set_runtime_variable("addsalve_size_euqit", addsalve_size_euqit)
                total = sum(addsalve_size_euqit)
                # 关键优化：四舍五入保留两位小数
                total = round(float(total), 2)
                cloud_euqit = var_manager.get_variable("cloud_euqit")
                cloudTrader_add_euqit = var_manager.get_variable("cloudTrader_add_euqit")
                # 校验除数非零
                if cloud_euqit == 0:
                    pytest.fail("cloud_euqit为0，无法计算预期比例（避免除零）")
                true_size = cloudTrader_add_euqit / cloud_euqit * 1

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

        @allure.title("账号管理-交易下单-云策略平仓")
        def test_bargain_masOrderClose(self, class_random_str, logged_session, var_manager):
            cloudTrader_user_ids_2 = var_manager.get_variable("cloudTrader_user_ids_2")
            # 1. 发送平仓请求
            data = {
                "isCloseAll": 1,
                "intervalTime": 0,
                "traderList": [cloudTrader_user_ids_2]
            }
            response = self.send_post_request(
                logged_session,
                '/bargain/masOrderClose',
                json_data=data
            )

            # 2. 判断是否平仓成功
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

        @allure.title("云策略-云策略列表-平仓")
        def test_cloudTrader_OrderClose(self, class_random_str, logged_session, var_manager):
            cloudMaster_id = var_manager.get_variable("cloudMaster_id")
            # 1. 发送平仓请求
            data = {
                "isCloseAll": 1,
                "intervalTime": 0,
                "id": f"{cloudMaster_id}",
                "cloudTraderId": []
            }
            response = self.send_post_request(
                logged_session,
                '/mascontrol/cloudTrader/cloudOrderClose',
                json_data=data
            )

            # 2. 判断是否平仓成功
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库校验-云跟单账号策略平仓-跟单账号固定手数")
        def test_dbclose_followParam5(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                cloudTrader_user_accounts_5 = var_manager.get_variable("cloudTrader_user_accounts_5")
                sql = f"""
                        SELECT 
                            fod.size,
                            fod.comment,
                            fod.close_no,
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
                    cloudTrader_user_accounts_5,
                    class_random_str
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
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(5),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库校验-云跟单账号策略平仓-跟单账号修改品种")
        def test_dbclose_templateId3(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                cloudTrader_user_accounts_6 = var_manager.get_variable("cloudTrader_user_accounts_6")

                sql = f"""
                        SELECT 
                            fod.size,
                            fod.comment,
                            fod.close_no,
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
                    cloudTrader_user_accounts_6,
                    class_random_str
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
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(3),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库校验-云跟单账号策略平仓-修改净值")
        def test_dbclose_euqit(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                cloudTrader_user_accounts_7 = var_manager.get_variable("cloudTrader_user_accounts_7")

                sql = f"""
                        SELECT 
                            fod.size,
                            fod.comment,
                            fod.close_no,
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
                    cloudTrader_user_accounts_7,
                    class_random_str
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

                addsalve_size_euqit = [record["size"] for record in db_data]
                var_manager.set_runtime_variable("addsalve_size_euqit", addsalve_size_euqit)
                total = sum(addsalve_size_euqit)
                # 关键优化：四舍五入保留两位小数
                total = round(float(total), 2)
                cloud_euqit = var_manager.get_variable("cloud_euqit")
                cloudTrader_add_euqit = var_manager.get_variable("cloudTrader_add_euqit")
                # 校验除数非零
                if cloud_euqit == 0:
                    pytest.fail("cloud_euqit为0，无法计算预期比例（避免除零）")

                true_size = cloudTrader_add_euqit / cloud_euqit * 1
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
