import time
import allure
import logging
import pytest
from lingkuan_1029.conftest import var_manager
from lingkuan_1029.commons.api_base import *
from lingkuan_1029.commons.jsonpath_utils import JsonPathUtils

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"


@allure.feature("仪表盘")
class TestVPSOrderSend_newScenarios:
    @allure.story("仪表盘-vps策略数据")
    @allure.description("""
    ### 测试说明
    - 功能校验，校验仪表盘的数据是否正确
    - 前置条件：有vps策略和vps跟单
      1. 进行开仓，手数范围0.1-1，总手数1
      2. 获取仪表数据，提取数据库数据，然后进行校验
      3. 数据正确
    - 预期结果：数据正确
    """)
    @pytest.mark.usefixtures("class_random_str")
    class TestVPSOrderSend1(APITestBase):
        # @pytest.mark.skipif(True, reason="跳过")
        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-策略平仓-防止数据残留")
        def test_trader_orderprevent_close(self, class_random_str, var_manager, logged_session):
            # 1. 发送全平订单平仓请求
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            new_user = var_manager.get_variable("new_user")
            vps_user_accounts = new_user["account"]
            data = {
                "isCloseAll": 1,
                "intervalTime": 100,
                "traderId": vps_trader_id,
                "account": vps_user_accounts
            }
            response = self.send_post_request(
                logged_session,
                '/subcontrol/trader/orderClose',
                json_data=data,
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

        @pytest.mark.url("vps")
        # @pytest.mark.skipif(True, reason=SKIP_REASON)
        @allure.title("跟单软件看板-VPS数据-策略开仓")
        def test_trader_orderSend(self, class_random_str, var_manager, logged_session):
            # 1. 发送策略开仓请求
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            data = {
                "symbol": trader_ordersend["symbol"],
                "placedType": 0,
                "remark": trader_ordersend["remark"],
                "intervalTime": 100,
                "type": 0,
                "totalNum": "",
                "totalSzie": "1.00",
                "startSize": "0.10",
                "endSize": "1.00",
                "traderId": vps_trader_id
            }
            response = self.send_post_request(
                logged_session,
                '/subcontrol/trader/orderSend',
                json_data=data,
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

        @allure.title("数据库校验-策略开仓-提取数据")
        def test_dbquery_orderSend(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                global profit_sum, total, order_num, margin_proportion, free_margin, euqit
                new_user = var_manager.get_variable("new_user")
                vps_user_accounts = new_user["account"]
                sql = f"""
                   SELECT 
                       fod.size,
                       fod.send_no,
                       fod.profit,
                       fod.open_time,
                       fod.order_no,
                       foi.operation_type,
                       foi.create_time
                   FROM 
                       follow_order_detail fod
                   INNER JOIN 
                       follow_order_instruct foi 
                   ON 
                       foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
                   WHERE foi.operation_type = %s
                       AND fod.account = %s
                       """
                params = (
                    '0',
                    vps_user_accounts,
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )
            with allure.step("2. 提取数据"):
                profit_db = [record["profit"] for record in db_data]
                profit_sum = sum(profit_db)

                size = [record["size"] for record in db_data]
                total = sum(size)
                # 关键优化：四舍五入保留两位小数
                total = round(float(total), 2)

                order_num = len(db_data)

            with allure.step("3. 获取follow_trader表账号数据"):
                sql = f"""SELECT free_margin,euqit FROM follow_trader WHERE account = %s"""
                params = (vps_user_accounts,)

                db_data = self.query_database(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )
            with allure.step("4. 提取数据"):
                free_margin = db_data[0]["free_margin"]
                euqit = db_data[0]["euqit"]
                margin_proportion = (euqit / free_margin) * 100
                # 使用 round 函数保留两位小数，round 函数的第二个参数指定保留的小数位数
                margin_proportion = round(margin_proportion, 2)

        @pytest.mark.flaky(reruns=0, reruns_delay=0)
        @allure.title("仪表盘-账号数据校验")
        def test_dashboard_getAccountDataPage(self, class_random_str, var_manager, logged_session):
            with allure.step("1. 获取仪表盘-账号数据"):
                new_user = var_manager.get_variable("new_user")
                vps_user_accounts = new_user["account"]
                params = {
                    "page": 1,
                    "limit": 10,
                    "order": "",
                    "asc": False,
                    "deleted": None,
                    "brokerName": "AS",
                    "account": vps_user_accounts,
                }
                response = self.send_get_request(
                    logged_session,
                    '/dashboard/getAccountDataPage',
                    params=params,
                )
            with allure.step("2. 验证响应"):
                self.assert_response_status(
                    response,
                    200,
                    "获取仪表盘数据失败"
                )
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )
            with allure.step("3. 提取数据"):
                self.json_utils = JsonPathUtils()
                response = response.json()
                sourceAccount = self.json_utils.extract(response, "$.data[0].account")
                profit = self.json_utils.extract(response, "$.data[0].profit")
                orderNum = self.json_utils.extract(response, "$.data[0].orderNum")
                lots = self.json_utils.extract(response, "$.data[0].lots")
                marginProportion = self.json_utils.extract(response, "$.data[0].marginProportion")
                proportion = self.json_utils.extract(response, "$.data[0].proportion")
                equity = self.json_utils.extract(response, "$.data[0].equity")
                logging.info(
                    f"提取的数据:{sourceAccount, profit, orderNum, lots, marginProportion, proportion, equity}")

            with allure.step("4. 数据校验"):
                with allure.step("5.1 验证账号"):
                    self.verify_data(
                        actual_value=sourceAccount,
                        expected_value=vps_user_accounts,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"账号数据符合预期",
                        attachment_name="账号详情"
                    )
                    logging.info(f"账号数据符合预期，实际是{sourceAccount}")

                # with allure.step("5.2 验证盈利"):
                #         self.verify_data(
                #             actual_value=float(profit),
                #             expected_value=float(profit_sum),
                #             op=CompareOp.EQ,
                #             use_isclose=True,
                #             abs_tol=100,
                #             message=f"盈利数据符合预期",
                #             attachment_name="盈利详情"
                #         )
                #         logging.info(f"盈利数据符合预期，实际是{profit_sum}")

                with allure.step("5.3 验证持仓订单量"):
                    self.verify_data(
                        actual_value=float(orderNum),
                        expected_value=float(order_num),
                        op=CompareOp.EQ,
                        use_isclose=True,
                        abs_tol=0,
                        message=f"持仓订单量数据符合预期",
                        attachment_name="持仓订单量详情"
                    )
                    logging.info(f"持仓订单量数据符合预期，实际是{order_num}")

                with allure.step("5.4 验证持仓手数"):
                    self.verify_data(
                        actual_value=float(lots),
                        expected_value=float(total),
                        op=CompareOp.EQ,
                        use_isclose=True,
                        abs_tol=0,
                        message=f"持仓手数符合预期",
                        attachment_name="持仓手数详情"
                    )
                    logging.info(f"持仓手数符合预期，实际是{total}")

                with allure.step("5.5 验证可用预付款-容差150000"):
                    self.verify_data(
                        actual_value=float(marginProportion),
                        expected_value=float(free_margin),
                        op=CompareOp.EQ,
                        use_isclose=True,
                        abs_tol=150000,
                        message=f"可用预付款符合预期",
                        attachment_name="可用预付款详情"
                    )
                    logging.info(f"可用预付款符合预期，实际是{free_margin}")

                with allure.step("5.6 验证可用预付款比例-容差5"):
                    self.verify_data(
                        actual_value=float(proportion),
                        expected_value=float(margin_proportion),
                        op=CompareOp.EQ,
                        use_isclose=True,
                        abs_tol=5,
                        message=f"可用预付款比例符合预期",
                        attachment_name="可用预付款比例详情"
                    )
                    logging.info(f"可用预付款比例符合预期，实际是{margin_proportion}")

                with allure.step("5.7 验证净值-容差150000"):
                    self.verify_data(
                        actual_value=float(equity),
                        expected_value=float(euqit),
                        op=CompareOp.EQ,
                        use_isclose=True,
                        abs_tol=150000,
                        message=f"净值符合预期",
                        attachment_name="净值详情"
                    )
                    logging.info(f"净值符合预期，实际是{euqit}")

        @pytest.mark.skipif(True, reason="跳过")
        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-策略平仓")
        def test_trader_orderclose(self, class_random_str, var_manager, logged_session):
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
                json_data=data,
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

    @allure.story("仪表盘-vps跟单数据")
    @allure.description("""
    ### 测试说明
    - 功能校验，校验仪表盘的数据是否正确
    - 前置条件：有vps策略和vps跟单
      1. 进行开仓，手数范围0.1-1，总手数1
      2. 获取仪表数据，提取数据库数据，然后进行校验
      3. 数据正确
    - 预期结果：数据正确
    """)
    @pytest.mark.usefixtures("class_random_str")
    class TestVPSOrderSend2(APITestBase):
        @pytest.mark.url("vps")
        @pytest.mark.skipif(True, reason="跳过")
        @allure.title("跟单软件看板-VPS数据-策略开仓")
        def test_trader_orderSend(self, class_random_str, var_manager, logged_session):
            # 1. 发送策略开仓请求
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            data = {
                "symbol": trader_ordersend["symbol"],
                "placedType": 0,
                "remark": trader_ordersend["remark"],
                "intervalTime": 100,
                "type": 0,
                "totalNum": "",
                "totalSzie": "1.00",
                "startSize": "0.10",
                "endSize": "1.00",
                "traderId": vps_trader_id
            }
            response = self.send_post_request(
                logged_session,
                '/subcontrol/trader/orderSend',
                json_data=data,
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

        @allure.title("数据库校验-策略开仓-提取数据")
        def test_dbquery_orderSend(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                global profit_sum, total, order_num, margin_proportion, free_margin, euqit
                vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
                sql = f"""
                           SELECT 
                               fod.size,
                               fod.send_no,
                               fod.profit,
                               fod.open_time,
                               fod.order_no,
                               foi.operation_type,
                               foi.create_time
                           FROM 
                               follow_order_detail fod
                           INNER JOIN 
                               follow_order_instruct foi 
                           ON 
                               foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
                           WHERE foi.operation_type = %s
                               AND fod.account = %s
                               """
                params = (
                    '0',
                    vps_user_accounts_1,
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )
            with allure.step("2. 提取数据"):
                profit_db = [record["profit"] for record in db_data]
                profit_sum = sum(profit_db)

                size = [record["size"] for record in db_data]
                total = sum(size)
                # 关键优化：四舍五入保留两位小数
                total = round(float(total), 2)

                order_num = len(db_data)

            with allure.step("3. 获取follow_trader表账号数据"):
                sql = f"""SELECT free_margin,euqit FROM follow_trader WHERE account = %s"""
                params = (vps_user_accounts_1,)

                db_data = self.query_database(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )
            with allure.step("4. 提取数据"):
                free_margin = db_data[0]["free_margin"]
                euqit = db_data[0]["euqit"]
                margin_proportion = (euqit / free_margin) * 100
                # 使用 round 函数保留两位小数，round 函数的第二个参数指定保留的小数位数
                margin_proportion = round(margin_proportion, 2)

        @pytest.mark.flaky(reruns=0, reruns_delay=0)
        @allure.title("仪表盘-账号数据校验")
        def test_dashboard_getAccountDataPage(self, class_random_str, var_manager, logged_session):
            with allure.step("1. 获取仪表盘-账号数据"):
                vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
                params = {
                    "page": 1,
                    "limit": 10,
                    "order": "",
                    "asc": False,
                    "deleted": None,
                    "brokerName": "AS",
                    "account": vps_user_accounts_1,
                }
                response = self.send_get_request(
                    logged_session,
                    '/dashboard/getAccountDataPage',
                    params=params,
                )
            with allure.step("2. 验证响应"):
                self.assert_response_status(
                    response,
                    200,
                    "获取仪表盘数据失败"
                )
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )
            with allure.step("3. 提取数据"):
                self.json_utils = JsonPathUtils()
                response = response.json()
                sourceAccount = self.json_utils.extract(response, "$.data[0].account")
                profit = self.json_utils.extract(response, "$.data[0].profit")
                orderNum = self.json_utils.extract(response, "$.data[0].orderNum")
                lots = self.json_utils.extract(response, "$.data[0].lots")
                marginProportion = self.json_utils.extract(response, "$.data[0].marginProportion")
                proportion = self.json_utils.extract(response, "$.data[0].proportion")
                equity = self.json_utils.extract(response, "$.data[0].equity")
                logging.info(
                    f"提取的数据:{sourceAccount, profit, orderNum, lots, marginProportion, proportion, equity}")

            with allure.step("4. 数据校验"):
                with allure.step("5.1 验证账号"):
                    self.verify_data(
                        actual_value=sourceAccount,
                        expected_value=vps_user_accounts_1,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"账号数据符合预期",
                        attachment_name="账号详情"
                    )
                    logging.info(f"账号数据符合预期，实际是{sourceAccount}")

                # with allure.step("5.2 验证盈利"):
                #         self.verify_data(
                #             actual_value=float(profit),
                #             expected_value=float(profit_sum),
                #             op=CompareOp.EQ,
                #             use_isclose=True,
                #             abs_tol=100,
                #             message=f"盈利数据符合预期",
                #             attachment_name="盈利详情"
                #         )
                #         logging.info(f"盈利数据符合预期，实际是{profit_sum}")

                with allure.step("5.3 验证持仓订单量"):
                    self.verify_data(
                        actual_value=float(orderNum),
                        expected_value=float(order_num),
                        op=CompareOp.EQ,
                        use_isclose=True,
                        abs_tol=0,
                        message=f"持仓订单量数据符合预期",
                        attachment_name="持仓订单量详情"
                    )
                    logging.info(f"持仓订单量数据符合预期，实际是{order_num}")

                with allure.step("5.4 验证持仓手数"):
                    self.verify_data(
                        actual_value=float(lots),
                        expected_value=float(total),
                        op=CompareOp.EQ,
                        use_isclose=True,
                        abs_tol=0,
                        message=f"持仓手数符合预期",
                        attachment_name="持仓手数详情"
                    )
                    logging.info(f"持仓手数符合预期，实际是{total}")

                with allure.step("5.5 验证可用预付款-容差150000"):
                    self.verify_data(
                        actual_value=float(marginProportion),
                        expected_value=float(free_margin),
                        op=CompareOp.EQ,
                        use_isclose=True,
                        abs_tol=150000,
                        message=f"可用预付款符合预期",
                        attachment_name="可用预付款详情"
                    )
                    logging.info(f"可用预付款符合预期，实际是{free_margin}")

                with allure.step("5.6 验证可用预付款比例-容差5"):
                    self.verify_data(
                        actual_value=float(proportion),
                        expected_value=float(margin_proportion),
                        op=CompareOp.EQ,
                        use_isclose=True,
                        abs_tol=5,
                        message=f"可用预付款比例符合预期",
                        attachment_name="可用预付款比例详情"
                    )
                    logging.info(f"可用预付款比例符合预期，实际是{margin_proportion}")

                with allure.step("5.7 验证净值-容差150000"):
                    self.verify_data(
                        actual_value=float(equity),
                        expected_value=float(euqit),
                        op=CompareOp.EQ,
                        use_isclose=True,
                        abs_tol=150000,
                        message=f"净值符合预期",
                        attachment_name="净值详情"
                    )
                    logging.info(f"净值符合预期，实际是{euqit}")

        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-策略平仓")
        def test_trader_orderclose(self, class_random_str, var_manager, logged_session):
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
                json_data=data,
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

        @pytest.mark.skip(reason=SKIP_REASON)
        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-跟单平仓")
        def test_addtrader_orderclose(self, class_random_str, var_manager, logged_session):
            # 1. 发送全平订单平仓请求
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
            data = {
                "isCloseAll": 1,
                "intervalTime": 100,
                "traderId": vps_addslave_id,
                "account": vps_user_accounts_1
            }
            response = self.send_post_request(
                logged_session,
                '/subcontrol/trader/orderClose',
                json_data=data,
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
