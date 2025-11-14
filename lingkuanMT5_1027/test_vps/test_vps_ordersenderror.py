import time
import math
import allure
import logging
import pytest
from lingkuanMT5_1027.VAR.VAR import *
from lingkuanMT5_1027.conftest import var_manager
from lingkuanMT5_1027.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("VPS策略下单-下单限制")
class TestVPSOrdersenderror:
    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    @allure.story("场景1： VPS看板-策略账号超过最大手数")
    @allure.description("""
    ### 测试说明
    - 前置条件：有vps策略和vps跟单
      1. 获取该服务器最大手数
      2. VPS看板-策略账号进行开仓
    - 预期结果：开仓失败，超过最大手数限制
    """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    @pytest.mark.usefixtures("class_random_str")
    class TestVPSOrderSend1(APITestBase):
        @allure.title("数据库提取该服务器最大手数限制")
        def test_dbquery_maxlots(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 数据库的SQL查询"):
                new_user = var_manager.get_variable("new_user")
                sql = f""" SELECT * From follow_platform where server= %s """
                params = (
                    new_user["platform"],
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )
            with allure.step("2. 提取数据"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                max_lots = db_data[0]["max_lots"]
                var_manager.set_runtime_variable("max_lots", max_lots)

            with allure.step("3. 全局配置-数据库的SQL查询"):
                sql = f""" SELECT * From sys_params where param_name= %s """
                params = (
                    "最大手数配置",
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )
            with allure.step("4. 提取数据"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                param_value = db_data[0]["param_value"]
                var_manager.set_runtime_variable("param_value", param_value)

        @pytest.mark.url("vps")
        # @pytest.mark.skipif(True, reason=SKIP_REASON)
        @allure.title("跟单软件看板-VPS数据-策略开仓")
        def test_trader_orderSend(self, class_random_str, var_manager, logged_session):
            # 1. 发送策略开仓请求
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
            max_lots = var_manager.get_variable("max_lots")
            param_value = var_manager.get_variable("param_value")
            if max_lots == None:
                max_lots = float(param_value) + 1
                data = {
                    "symbol": trader_ordersend["symbol"],
                    "placedType": 0,
                    "remark": class_random_str,
                    "intervalTime": 100,
                    "type": 0,
                    "totalNum": "1",
                    "totalSzie": "",
                    "startSize": max_lots,
                    "endSize": max_lots,
                    "traderId": MT5vps_trader_id
                }
                response = self.send_post_request(
                    logged_session,
                    '/subcontrol/trader/orderSend',
                    json_data=data,
                )
            else:
                max_lots = max_lots + 1
                data = {
                    "symbol": trader_ordersend["symbol"],
                    "placedType": 0,
                    "remark": class_random_str,
                    "intervalTime": 100,
                    "type": 0,
                    "totalNum": "1",
                    "totalSzie": "",
                    "startSize": max_lots,
                    "endSize": max_lots,
                    "traderId": MT5vps_trader_id
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

        @allure.title("数据库校验-策略开仓-主指令及订单详情数据检查")
        def test_dbquery_orderSend(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                new_user = var_manager.get_variable("new_user")
                sql = f"""
                       SELECT 
                           fod.size,
                           fod.comment,
                           fod.send_no,
                           fod.magical,
                           fod.open_price,
                           fod.remark,
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
                           foi.total_orders
                       FROM 
                           follow_order_detail fod
                       INNER JOIN 
                           follow_order_instruct foi 
                       ON 
                           foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
                       WHERE fod.account = %s
                           AND fod.comment = %s
                           """
                params = (
                    new_user["account"],
                    class_random_str
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
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证备注信息"):
                    open_remark = db_data[0]["remark"]
                    self.verify_data(
                        actual_value=open_remark,
                        expected_value=("超过最大手数限制"),
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message="开仓失败信息符合预期",
                        attachment_name="失败信息详情"
                    )
                    logging.info(f"失败信息验证通过: {open_remark}")

    @allure.story("场景2：分配下单-策略账号超过最大手数")
    @allure.description("""
    ### 测试说明
    - 前置条件：有vps策略和vps跟单
      1. 获取该服务器最大手数
      2. 交易下单-分配下单-策略账号进行开仓
    - 预期结果：开仓失败，超过最大手数限制
    """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    @pytest.mark.usefixtures("class_random_str")
    class TestVPSOrderSend2(APITestBase):
        @allure.title("数据库提取该服务器最大手数限制")
        def test_dbquery_maxlots(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 数据库的SQL查询"):
                new_user = var_manager.get_variable("new_user")
                sql = f""" SELECT * From follow_platform where server= %s """
                params = (
                    new_user["platform"],
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )

            with allure.step("2. 提取数据"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                max_lots = db_data[0]["max_lots"]
                var_manager.set_runtime_variable("max_lots", max_lots)

            with allure.step("3. 全局配置-数据库的SQL查询"):
                sql = f""" SELECT * From sys_params where param_name= %s """
                params = (
                    "最大手数配置",
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )
            with allure.step("4. 提取数据"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                param_value = db_data[0]["param_value"]
                var_manager.set_runtime_variable("param_value", param_value)

        @allure.title("VPS交易下单-分配下单")
        def test_copy_order_send(self, class_random_str, logged_session, var_manager):
            # 发送VPS策略账号交易下单-复制下单
            masOrderSend = var_manager.get_variable("masOrderSend")
            MT5vps_trader_user_id = var_manager.get_variable("MT5vps_trader_user_id")
            max_lots = var_manager.get_variable("max_lots")
            param_value = var_manager.get_variable("param_value")
            if max_lots == None:
                max_lots = float(param_value) + 1
                data = {
                    "traderList": [MT5vps_trader_user_id],
                    "type": 0,
                    "tradeType": 0,
                    "symbol": masOrderSend["symbol"],
                    "startSize": max_lots,
                    "endSize": max_lots,
                    "totalSzie": max_lots,
                    "remark": class_random_str
                }
                response = self.send_post_request(
                    logged_session,
                    '/bargain/masOrderSend',
                    json_data=data
                )
            else:
                max_lots = max_lots + 1
                data = {
                    "traderList": [MT5vps_trader_user_id],
                    "type": 0,
                    "tradeType": 0,
                    "symbol": masOrderSend["symbol"],
                    "startSize": max_lots,
                    "endSize": max_lots,
                    "totalSzie": max_lots,
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

        @allure.title("数据库校验-策略开仓-主指令及订单详情数据检查")
        def test_dbquery_orderSend(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                new_user = var_manager.get_variable("new_user")
                MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
                account = new_user["account"]
                sql = f"""
                       SELECT 
                           fod.size,
                           fod.comment,
                           fod.send_no,
                           fod.magical,
                           fod.open_price,
                           fod.remark,
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
                           foi.total_orders
                       FROM 
                           follow_order_detail fod
                       INNER JOIN 
                           follow_order_instruct foi 
                       ON 
                       foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
                   WHERE fod.account = %s
                        AND fod.trader_id = %s
                           """
                params = (
                    account, MT5vps_trader_id
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
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证备注信息"):
                    open_remark = db_data[0]["remark"]
                    self.verify_data(
                        actual_value=open_remark,
                        expected_value=("超过最大手数限制"),
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message="开仓失败信息符合预期",
                        attachment_name="失败信息详情"
                    )
                    logging.info(f"失败信息验证通过: {open_remark}")

    @allure.story("场景3：复制下单-策略账号超过最大手数")
    @allure.description("""
    ### 测试说明
    - 前置条件：有vps策略和vps跟单
      1. 获取该服务器最大手数
      2. 交易下单-复制下单-策略账号进行开仓
    - 预期结果：开仓失败，超过最大手数限制
    """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    @pytest.mark.usefixtures("class_random_str")
    class TestVPSOrderSend3(APITestBase):
        @allure.title("数据库提取该服务器最大手数限制")
        def test_dbquery_maxlots(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 数据库的SQL查询"):
                new_user = var_manager.get_variable("new_user")
                sql = f""" SELECT * From follow_platform where server= %s """
                params = (
                    new_user["platform"],
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )

            with allure.step("2. 提取数据"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                max_lots = db_data[0]["max_lots"]
                var_manager.set_runtime_variable("max_lots", max_lots)

            with allure.step("3. 全局配置-数据库的SQL查询"):
                sql = f""" SELECT * From sys_params where param_name= %s """
                params = (
                    "最大手数配置",
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )
            with allure.step("4. 提取数据"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                param_value = db_data[0]["param_value"]
                var_manager.set_runtime_variable("param_value", param_value)

        @allure.title("VPS策略账号交易下单-复制下单")
        def test_copy_order_send(self, class_random_str, logged_session, var_manager):
            # 发送VPS策略账号交易下单-复制下单
            masOrderSend = var_manager.get_variable("masOrderSend")
            MT5vps_trader_user_id = var_manager.get_variable("MT5vps_trader_user_id")
            max_lots = var_manager.get_variable("max_lots")
            param_value = var_manager.get_variable("param_value")
            if max_lots == None:
                max_lots = float(param_value) + 1
                data = {
                    "traderList": [MT5vps_trader_user_id],
                    "type": 0,
                    "tradeType": 1,
                    "intervalTime": 100,
                    "symbol": masOrderSend["symbol"],
                    "placedType": 0,
                    "startSize": max_lots,
                    "endSize": max_lots,
                    "totalNum": "1",
                    "totalSzie": "",
                    "remark": class_random_str
                }
                response = self.send_post_request(
                    logged_session,
                    '/bargain/masOrderSend',
                    json_data=data
                )
            else:
                max_lots = max_lots + 1
                data = {
                    "traderList": [MT5vps_trader_user_id],
                    "type": 0,
                    "tradeType": 1,
                    "intervalTime": 100,
                    "symbol": masOrderSend["symbol"],
                    "placedType": 0,
                    "startSize": max_lots,
                    "endSize": max_lots,
                    "totalNum": "1",
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

        @allure.title("数据库校验-策略开仓-主指令及订单详情数据检查")
        def test_dbquery_orderSend(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                new_user = var_manager.get_variable("new_user")
                MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
                account = new_user["account"]
                sql = f"""
                       SELECT 
                           fod.size,
                           fod.comment,
                           fod.send_no,
                           fod.magical,
                           fod.open_price,
                           fod.remark,
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
                           foi.total_orders
                       FROM 
                           follow_order_detail fod
                       INNER JOIN 
                           follow_order_instruct foi 
                       ON 
                       foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
                   WHERE fod.account = %s
                        AND fod.trader_id = %s
                           """
                params = (
                    account, MT5vps_trader_id
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
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证备注信息"):
                    open_remark = db_data[0]["remark"]
                    self.verify_data(
                        actual_value=open_remark,
                        expected_value=("超过最大手数限制"),
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message="开仓失败信息符合预期",
                        attachment_name="失败信息详情"
                    )
                    logging.info(f"失败信息验证通过: {open_remark}")

    @allure.story("场景4：VPS交易分配-手数范围0.1-1，总手数0.01")
    @allure.description("""
    ### 测试说明
    - 场景校验：手数范围>总手数>订单数量
    - 前置条件：有vps策略和vps跟单
     1. 进行开仓，手数范围0.1-1，总手数0.01
     2. 预期下单失败：总手数不能低于最低手数
    - 预期结果：提示正确
    """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    class TestVPStradingOrders4(APITestBase):
        @allure.title("VPS交易下单-分配下单")
        def test_copy_order_send(self, class_random_str, logged_session, var_manager):
            # 发送VPS策略账号交易下单-复制下单
            masOrderSend = var_manager.get_variable("masOrderSend")
            MT5vps_trader_user_id = var_manager.get_variable("MT5vps_trader_user_id")
            data = {
                "traderList": [MT5vps_trader_user_id],
                "type": 0,
                "tradeType": 0,
                "symbol": masOrderSend["symbol"],
                "startSize": "0.10",
                "endSize": "1.00",
                "totalSzie": "0.01",
                "remark": "测试数据"
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
                "总手数不能低于最低手数",
                "响应msg字段应为：总手数不能低于最低手数"
            )

    @allure.story("场景5：VPS交易分配-手数范围0.1-1，总手数2")
    @allure.description("""
    ### 测试说明
    - 场景校验：手数范围>总手数>订单数量
    - 前置条件：有vps策略和vps跟单
     1. 进行开仓，手数范围0.1-1，总手数2
     2. 预期下单失败：下单失败，请检查下单参数
    - 预期结果：提示正确
    """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    class TestVPStradingOrders5(APITestBase):
        @allure.title("VPS交易下单-分配下单")
        def test_copy_order_send(self, class_random_str, logged_session, var_manager):
            # 发送VPS策略账号交易下单-复制下单
            masOrderSend = var_manager.get_variable("masOrderSend")
            MT5vps_trader_user_id = var_manager.get_variable("MT5vps_trader_user_id")
            data = {
                "traderList": [MT5vps_trader_user_id],
                "type": 0,
                "tradeType": 0,
                "symbol": masOrderSend["symbol"],
                "startSize": "0.10",
                "endSize": "1.00",
                "totalSzie": "2",
                "remark": "测试数据"
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
                "下单失败，请检查下单参数",
                "响应msg字段应为：下单失败，请检查下单参数"
            )
