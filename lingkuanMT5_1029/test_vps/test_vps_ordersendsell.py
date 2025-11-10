import time
import math
import allure
import logging
import pytest
from lingkuanMT5_1029.VAR.VAR import *
from lingkuanMT5_1029.conftest import var_manager
from lingkuanMT5_1029.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("VPS策略下单-开仓的场景校验-sell")
class TestVPSOrdersendsell:
    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    @allure.story("场景1：复制下单-手数0.1-1，总订单3，总手数1")
    @allure.description("""
    ### 测试说明
    - 前置条件：有vps策略和vps跟单
      1. 进行开仓，手数范围0.1-1，总订单3，总手数1
      2. 校验账号的数据是否正确
      3. 进行平仓
      4. 校验账号的数据是否正确
    - 预期结果：账号的数据正确
    """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    class TestVPSOrderSend1(APITestBase):
        @pytest.mark.url("vps")
        @allure.title("修改跟单账号")
        def test_follow_updateSlave(self, class_random_str, var_manager, logged_session, encrypted_password):
            with allure.step("1. 修改跟单账号"):
                # followMode  0 : 固定手数  1：手数比例 2：净值比例
                # remainder  0 : 四舍五入  1：取小数
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
                    "followDirection": 0,
                    "followMode": 1,
                    "remainder": 0,
                    "followParam": "1",
                    "placedType": 0,
                    "templateId": 1,
                    "followStatus": 1,
                    "followOpen": 1,
                    "followClose": 1,
                    "followRep": 0,
                    "fixedComment": "",
                    "commentType": None,
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

        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-策略开仓")
        def test_trader_orderSend(self, class_random_str, var_manager, logged_session):
            # 1. 发送策略开仓请求
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
            data = {
                "symbol": trader_ordersend["symbol"],
                "placedType": 0,
                "remark": class_random_str,
                "intervalTime": 100,
                "type": 1,
                "totalNum": trader_ordersend["totalNum"],
                "totalSzie": trader_ordersend["totalSzie"],
                "startSize": trader_ordersend["startSize"],
                "endSize": trader_ordersend["endSize"],
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
                    WHERE foi.operation_type = %s
                        AND fod.account = %s
                        AND fod.comment = %s
                        """
                params = (
                    '0',
                    new_user["account"],
                    class_random_str
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )
            with allure.step("2. 数据校验"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证手数范围-开始手数"):
                    max_lot_size = db_data[0]["max_lot_size"]
                    self.verify_data(
                        actual_value=float(max_lot_size),
                        expected_value=float(0.10),
                        op=CompareOp.EQ,
                        message="开始手数应符合预期",
                        attachment_name="开始手数详情"
                    )
                    logging.info(f"开始手数验证通过: {trader_ordersend['startSize']}")

                with allure.step("验证手数范围-结束手数"):
                    min_lot_size = db_data[0]["min_lot_size"]
                    self.verify_data(
                        actual_value=float(min_lot_size),
                        expected_value=float(trader_ordersend["endSize"]),
                        op=CompareOp.EQ,
                        message="结束手数应符合预期",
                        attachment_name="结束手数详情"
                    )
                    logging.info(f"结束手数验证通过: {trader_ordersend['endSize']}")

                with allure.step("总订单数量校验"):
                    total_orders = db_data[0]["total_orders"]
                    totalNum = trader_ordersend["totalNum"]
                    self.verify_data(
                        actual_value=float(total_orders),
                        expected_value=float(totalNum),
                        op=CompareOp.EQ,
                        message="总订单数量应符合预期",
                        attachment_name="总订单数量详情"
                    )
                    logging.info(f"总订单数量验证通过: {total_orders}")

                with allure.step("验证指令总手数"):
                    total_lots = db_data[0]["total_lots"]
                    totalSzie = trader_ordersend["totalSzie"]
                    self.verify_data(
                        actual_value=float(total_lots),
                        expected_value=float(totalSzie),
                        op=CompareOp.EQ,
                        message="指令总手数应符合预期",
                        attachment_name="指令总手数详情"
                    )
                    logging.info(f"指令总手数验证通过: {total_lots}")

                with allure.step("验证详情总手数"):
                    totalSzie = trader_ordersend["totalSzie"]
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    totalSzie = round(float(totalSzie), 2)

                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(totalSzie),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-策略开仓-跟单指令及订单详情数据检查")
        def test_dbquery_addsalve_orderSend(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
                sql = f"""
                    SELECT 
                        fod.size,
                        fod.comment,
                        fod.send_no,
                        fod.magical,
                        fod.open_price,
                        fod.symbol,
                        fod.order_no,
                        foi.true_total_lots,
                        foi.order_no,
                        foi.operation_type,
                        foi.create_time,
                        foi.status,
                        foi.total_lots,
                        foi.total_orders
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
                    MT5vps_user_accounts_1,
                    class_random_str
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )

            with allure.step("2. 数据校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=1,
                        op=CompareOp.EQ,
                        message="详情总手数符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f'订单详情总手数是：{total}')

                with allure.step("验证详情手数和指令手数一致"):
                    size = [record["size"] for record in db_data]
                    total_lots = [record["total_lots"] for record in db_data]
                    self.assert_list_equal_ignore_order(
                        size,
                        total_lots,
                        f"手数不一致: 详情{size}, 指令{total_lots}"
                    )
                    logger.info(f"手数一致: 详情{size}, 指令{total_lots}")

        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-策略平仓")
        def test_trader_orderclose(self, class_random_str, var_manager, logged_session):
            # 1. 发送全平订单平仓请求
            MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
            new_user = var_manager.get_variable("new_user")
            data = {
                "isCloseAll": 1,
                "intervalTime": 100,
                "traderId": MT5vps_trader_id,
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

        # @pytest.mark.skip(reason=SKIP_REASON)
        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-跟单平仓")
        def test_addtrader_orderclose(self, class_random_str, var_manager, logged_session):
            # 1. 发送全平订单平仓请求
            MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
            MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
            data = {
                "isCloseAll": 1,
                "intervalTime": 100,
                "traderId": MT5vps_addslave_id,
                "account": MT5vps_user_accounts_1
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

        @allure.title("数据库校验-策略平仓-主指令及订单详情数据检查")
        def test_dbquery_orderSendclose(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                new_user = var_manager.get_variable("new_user")
                sql = f"""
                    SELECT 
                        fod.size,
                        fod.comment,
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

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=1,
                        op=CompareOp.EQ,
                        message="详情总手数符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f'订单详情总手数是：{total}')

        @allure.title("数据库校验-策略平仓-跟单指令及订单详情数据检查")
        def test_dbquery_addsalve_orderSendclose(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
                MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
                sql = f"""
                    SELECT 
                        fod.size,
                        fod.comment,
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
                        AND fod.comment = %s
                        """
                params = (
                    '1',
                    MT5vps_user_accounts_1,
                    MT5vps_addslave_id,
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

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=1,
                        op=CompareOp.EQ,
                        message="详情总手数符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f'订单详情总手数是：{total}')

                with allure.step("验证详情手数和指令手数一致"):
                    size = [record["size"] for record in db_data]
                    true_total_lots = [record["true_total_lots"] for record in db_data]
                    self.assert_list_equal_ignore_order(
                        size,
                        true_total_lots,
                        f"手数不一致: 详情{size}, 指令{true_total_lots}"
                    )
                    logger.info(f"手数一致: 详情{size}, 指令{true_total_lots}")

    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    @allure.story("场景2：复制下单-手数范围0.01-0.01，总手数0.01")
    @allure.description("""
    ### 测试说明
    - 前置条件：有云策略和云跟单
      1. 进行开仓，手数范围0.01-0.01，总手数0.01
      2. 校验账号的数据是否正确
      3. 进行平仓
      4. 校验账号的数据是否正确
    - 预期结果：账号的数据正确
    """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    class TestVPSOrderSend2(APITestBase):
        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-策略开仓")
        def test_trader_orderSend(self, class_random_str, var_manager, logged_session):
            # 1. 发送策略开仓请求
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
            data = {
                "symbol": trader_ordersend["symbol"],
                "placedType": 0,
                "remark": class_random_str,
                "intervalTime": 100,
                "type": 1,
                "totalNum": "",
                "totalSzie": "0.01",
                "startSize": "0.01",
                "endSize": "0.01",
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
                    WHERE foi.operation_type = %s
                        AND fod.account = %s
                        AND fod.comment = %s
                        """
                params = (
                    '0',
                    new_user["account"],
                    class_random_str
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )
            with allure.step("2. 数据校验"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证手数范围-开始手数"):
                    max_lot_size = db_data[0]["max_lot_size"]
                    self.verify_data(
                        actual_value=float(max_lot_size),
                        expected_value=float(0.01),
                        op=CompareOp.EQ,
                        message="开始手数应符合预期",
                        attachment_name="开始手数详情"
                    )
                    logging.info(f"开始手数验证通过: {trader_ordersend['startSize']}")

                with allure.step("验证手数范围-结束手数"):
                    min_lot_size = db_data[0]["min_lot_size"]
                    self.verify_data(
                        actual_value=float(min_lot_size),
                        expected_value=float(0.01),
                        op=CompareOp.EQ,
                        message="结束手数应符合预期",
                        attachment_name="结束手数详情"
                    )
                    logging.info(f"结束手数验证通过: {trader_ordersend['endSize']}")

                with allure.step("验证指令总手数"):
                    total_lots = db_data[0]["total_lots"]
                    self.verify_data(
                        actual_value=float(total_lots),
                        expected_value=float(0.01),
                        op=CompareOp.EQ,
                        message="指令总手数应符合预期",
                        attachment_name="指令总手数详情"
                    )
                    logging.info(f"指令总手数验证通过: {total_lots}")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(0.01),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-策略开仓-跟单指令及订单详情数据检查")
        def test_dbquery_addsalve_orderSend(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
                sql = f"""
                    SELECT 
                        fod.size,
                        fod.comment,
                        fod.send_no,
                        fod.magical,
                        fod.open_price,
                        fod.symbol,
                        fod.order_no,
                        foi.true_total_lots,
                        foi.order_no,
                        foi.operation_type,
                        foi.create_time,
                        foi.status,
                        foi.total_lots,
                        foi.total_orders
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
                    MT5vps_user_accounts_1,
                    class_random_str
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )

            with allure.step("2. 数据校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=0.01,
                        op=CompareOp.EQ,
                        message="详情总手数符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f'订单详情总手数是：{total}')

                with allure.step("验证详情手数和指令手数一致"):
                    size = [record["size"] for record in db_data]
                    total_lots = [record["total_lots"] for record in db_data]
                    self.assert_list_equal_ignore_order(
                        size,
                        total_lots,
                        f"手数不一致: 详情{size}, 指令{total_lots}"
                    )
                    logger.info(f"手数一致: 详情{size}, 指令{total_lots}")

        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-策略平仓")
        def test_trader_orderclose(self, class_random_str, var_manager, logged_session):
            # 1. 发送全平订单平仓请求
            MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
            new_user = var_manager.get_variable("new_user")
            data = {
                "isCloseAll": 1,
                "intervalTime": 100,
                "traderId": MT5vps_trader_id,
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

        # @pytest.mark.skip(reason=SKIP_REASON)
        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-跟单平仓")
        def test_addtrader_orderclose(self, class_random_str, var_manager, logged_session):
            # 1. 发送全平订单平仓请求
            MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
            MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
            data = {
                "isCloseAll": 1,
                "intervalTime": 100,
                "traderId": MT5vps_addslave_id,
                "account": MT5vps_user_accounts_1
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

        @allure.title("数据库校验-策略平仓-主指令及订单详情数据检查")
        def test_dbquery_orderSendclose(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                new_user = var_manager.get_variable("new_user")
                sql = f"""
                    SELECT 
                        fod.size,
                        fod.comment,
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

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=0.01,
                        op=CompareOp.EQ,
                        message="详情总手数符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f'订单详情总手数是：{total}')

        @allure.title("数据库校验-策略平仓-跟单指令及订单详情数据检查")
        def test_dbquery_addsalve_orderSendclose(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
                MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
                sql = f"""
                    SELECT 
                        fod.size,
                        fod.comment,
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
                        AND fod.comment = %s
                        """
                params = (
                    '1',
                    MT5vps_user_accounts_1,
                    MT5vps_addslave_id,
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

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=0.01,
                        op=CompareOp.EQ,
                        message="详情总手数符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f'订单详情总手数是：{total}')

                with allure.step("验证详情手数和指令手数一致"):
                    size = [record["size"] for record in db_data]
                    true_total_lots = [record["true_total_lots"] for record in db_data]
                    self.assert_list_equal_ignore_order(
                        size,
                        true_total_lots,
                        f"手数不一致: 详情{size}, 指令{true_total_lots}"
                    )
                    logger.info(f"手数一致: 详情{size}, 指令{true_total_lots}")

    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    @allure.story("场景3：复制下单-手数范围0.01-1，总订单数10")
    @allure.description("""
    ### 测试说明
    - 前置条件：有云策略和云跟单
      1. 进行开仓，手数范围0.01-1，总订单数10
      2. 校验账号的数据是否正确
      3. 进行平仓
      4. 校验账号的数据是否正确
    - 预期结果：账号的数据正确
    """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    class TestVPSOrderSend3(APITestBase):
        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-策略开仓")
        def test_trader_orderSend(self, class_random_str, var_manager, logged_session):
            # 1. 发送策略开仓请求
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
            data = {
                "symbol": trader_ordersend["symbol"],
                "placedType": 0,
                "remark": class_random_str,
                "intervalTime": 100,
                "type": 1,
                "totalNum": "10",
                "totalSzie": "",
                "startSize": "0.01",
                "endSize": "1",
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
                    WHERE foi.operation_type = %s
                        AND fod.account = %s
                        AND fod.comment = %s
                        """
                params = (
                    '0',
                    new_user["account"],
                    class_random_str
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )
            with allure.step("2. 数据校验"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证手数范围-结束手数"):
                    min_lot_size = db_data[0]["min_lot_size"]
                    self.verify_data(
                        actual_value=float(min_lot_size),
                        expected_value=float(trader_ordersend["endSize"]),
                        op=CompareOp.EQ,
                        message="结束手数应符合预期",
                        attachment_name="结束手数详情"
                    )
                    logging.info(f"结束手数验证通过: {trader_ordersend['endSize']}")

                with allure.step("验证手数范围-开始手数"):
                    max_lot_size = db_data[0]["max_lot_size"]
                    self.verify_data(
                        actual_value=float(max_lot_size),
                        expected_value=float(0.01),
                        op=CompareOp.EQ,
                        message="开始手数应符合预期",
                        attachment_name="开始手数详情"
                    )
                    logging.info(f"开始手数验证通过: {max_lot_size}")

                with allure.step("验证总订单数量"):
                    total_orders = db_data[0]["total_orders"]
                    self.verify_data(
                        actual_value=float(total_orders),
                        expected_value=float(10),
                        op=CompareOp.EQ,
                        message="总订单数量应符合预期",
                        attachment_name="总订单数量详情"
                    )
                    logging.info(f"开始手数验证通过: {total_orders}")

        @allure.title("数据库校验-策略开仓-跟单指令及订单详情数据检查")
        def test_dbquery_addsalve_orderSend(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
                sql = f"""
                    SELECT 
                        fod.size,
                        fod.comment,
                        fod.send_no,
                        fod.magical,
                        fod.open_price,
                        fod.symbol,
                        fod.order_no,
                        foi.true_total_lots,
                        foi.order_no,
                        foi.operation_type,
                        foi.create_time,
                        foi.status,
                        foi.total_lots,
                        foi.total_orders
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
                    MT5vps_user_accounts_1,
                    class_random_str
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )

            with allure.step("2. 数据校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证总订单数量"):
                    self.verify_data(
                        actual_value=float(len(db_data)),
                        expected_value=float(10),
                        op=CompareOp.EQ,
                        message="总订单数量应符合预期",
                        attachment_name="总订单数量详情"
                    )
                    logging.info(f"开始手数验证通过: {len(db_data)}")

                with allure.step("验证详情手数和指令手数一致"):
                    size = [record["size"] for record in db_data]
                    total_lots = [record["total_lots"] for record in db_data]
                    self.assert_list_equal_ignore_order(
                        size,
                        total_lots,
                        f"手数不一致: 详情{size}, 指令{total_lots}"
                    )
                    logger.info(f"手数一致: 详情{size}, 指令{total_lots}")

        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-策略平仓")
        def test_trader_orderclose(self, class_random_str, var_manager, logged_session):
            # 1. 发送全平订单平仓请求
            MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
            new_user = var_manager.get_variable("new_user")
            data = {
                "isCloseAll": 1,
                "intervalTime": 100,
                "traderId": MT5vps_trader_id,
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

        # @pytest.mark.skip(reason=SKIP_REASON)
        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-跟单平仓")
        def test_addtrader_orderclose(self, class_random_str, var_manager, logged_session):
            # 1. 发送全平订单平仓请求
            MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
            MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
            data = {
                "isCloseAll": 1,
                "intervalTime": 100,
                "traderId": MT5vps_addslave_id,
                "account": MT5vps_user_accounts_1
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

        @allure.title("数据库校验-策略平仓-主指令及订单详情数据检查")
        def test_dbquery_orderSendclose(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                new_user = var_manager.get_variable("new_user")
                sql = f"""
                    SELECT 
                        fod.size,
                        fod.comment,
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

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证总订单数量"):
                    self.verify_data(
                        actual_value=float(len(db_data)),
                        expected_value=float(10),
                        op=CompareOp.EQ,
                        message="总订单数量应符合预期",
                        attachment_name="总订单数量详情"
                    )
                    logging.info(f"开始手数验证通过: {len(db_data)}")

        @allure.title("数据库校验-策略平仓-跟单指令及订单详情数据检查")
        def test_dbquery_addsalve_orderSendclose(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
                MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
                sql = f"""
                    SELECT 
                        fod.size,
                        fod.comment,
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
                        AND fod.comment = %s
                        """
                params = (
                    '1',
                    MT5vps_user_accounts_1,
                    MT5vps_addslave_id,
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

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证总订单数量"):
                    self.verify_data(
                        actual_value=float(len(db_data)),
                        expected_value=float(10),
                        op=CompareOp.EQ,
                        message="总订单数量应符合预期",
                        attachment_name="总订单数量详情"
                    )
                    logging.info(f"开始手数验证通过: {len(db_data)}")

                with allure.step("验证详情手数和指令手数一致"):
                    size = [record["size"] for record in db_data]
                    true_total_lots = [record["true_total_lots"] for record in db_data]
                    self.assert_list_equal_ignore_order(
                        size,
                        true_total_lots,
                        f"手数不一致: 详情{size}, 指令{true_total_lots}"
                    )
                    logger.info(f"手数一致: 详情{size}, 指令{true_total_lots}")

    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    @allure.story("场景4：复制下单-手数0.01-1，总手数5")
    @allure.description("""
    ### 测试说明
    - 前置条件：有云策略和云跟单
      1. 进行开仓，手数0.01-1，总手数5
      2. 校验账号的数据是否正确
      3. 进行平仓
      4. 校验账号的数据是否正确
    - 预期结果：账号的数据正确
    """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    class TestVPSOrderSend4(APITestBase):
        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-策略开仓")
        def test_trader_orderSend(self, class_random_str, var_manager, logged_session):
            # 1. 发送策略开仓请求
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
            data = {
                "symbol": trader_ordersend["symbol"],
                "placedType": 0,
                "remark": class_random_str,
                "intervalTime": 100,
                "type": 1,
                "totalNum": "",
                "totalSzie": "5",
                "startSize": "0.01",
                "endSize": "1",
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
                    WHERE foi.operation_type = %s
                        AND fod.account = %s
                        AND fod.comment = %s
                        """
                params = (
                    '0',
                    new_user["account"],
                    class_random_str
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )
            with allure.step("2. 数据校验"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证手数范围-结束手数"):
                    min_lot_size = db_data[0]["min_lot_size"]
                    self.verify_data(
                        actual_value=float(min_lot_size),
                        expected_value=float(trader_ordersend["endSize"]),
                        op=CompareOp.EQ,
                        message="结束手数应符合预期",
                        attachment_name="结束手数详情"
                    )
                    logging.info(f"结束手数验证通过: {trader_ordersend['endSize']}")

                with allure.step("验证手数范围-开始手数"):
                    max_lot_size = db_data[0]["max_lot_size"]
                    self.verify_data(
                        actual_value=float(max_lot_size),
                        expected_value=float(0.01),
                        op=CompareOp.EQ,
                        message="开始手数应符合预期",
                        attachment_name="开始手数详情"
                    )
                    logging.info(f"开始手数验证通过: {max_lot_size}")

                with allure.step("验证指令总手数"):
                    total_lots = db_data[0]["total_lots"]
                    self.verify_data(
                        actual_value=float(total_lots),
                        expected_value=float(5),
                        op=CompareOp.EQ,
                        message="指令总手数应符合预期",
                        attachment_name="指令总手数详情"
                    )
                    logging.info(f"指令总手数验证通过: {total_lots}")

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

        @allure.title("数据库校验-策略开仓-跟单指令及订单详情数据检查")
        def test_dbquery_addsalve_orderSend(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
                sql = f"""
                    SELECT 
                        fod.size,
                        fod.comment,
                        fod.send_no,
                        fod.magical,
                        fod.open_price,
                        fod.symbol,
                        fod.order_no,
                        foi.true_total_lots,
                        foi.order_no,
                        foi.operation_type,
                        foi.create_time,
                        foi.status,
                        foi.total_lots,
                        foi.total_orders
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
                    MT5vps_user_accounts_1,
                    class_random_str
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )

            with allure.step("2. 数据校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

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

                with allure.step("验证详情手数和指令手数一致"):
                    size = [record["size"] for record in db_data]
                    total_lots = [record["total_lots"] for record in db_data]
                    self.assert_list_equal_ignore_order(
                        size,
                        total_lots,
                        f"手数不一致: 详情{size}, 指令{total_lots}"
                    )
                    logger.info(f"手数一致: 详情{size}, 指令{total_lots}")

        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-策略平仓")
        def test_trader_orderclose(self, class_random_str, var_manager, logged_session):
            # 1. 发送全平订单平仓请求
            MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
            new_user = var_manager.get_variable("new_user")
            data = {
                "isCloseAll": 1,
                "intervalTime": 100,
                "traderId": MT5vps_trader_id,
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

        # @pytest.mark.skip(reason=SKIP_REASON)
        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-跟单平仓")
        def test_addtrader_orderclose(self, class_random_str, var_manager, logged_session):
            # 1. 发送全平订单平仓请求
            MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
            MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
            data = {
                "isCloseAll": 1,
                "intervalTime": 100,
                "traderId": MT5vps_addslave_id,
                "account": MT5vps_user_accounts_1
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

        @allure.title("数据库校验-策略平仓-主指令及订单详情数据检查")
        def test_dbquery_orderSendclose(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                new_user = var_manager.get_variable("new_user")
                sql = f"""
                    SELECT 
                        fod.size,
                        fod.comment,
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

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

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

        @allure.title("数据库校验-策略平仓-跟单指令及订单详情数据检查")
        def test_dbquery_addsalve_orderSendclose(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
                MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
                sql = f"""
                    SELECT 
                        fod.size,
                        fod.comment,
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
                        AND fod.comment = %s
                        """
                params = (
                    '1',
                    MT5vps_user_accounts_1,
                    MT5vps_addslave_id,
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

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

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

                with allure.step("验证详情手数和指令手数一致"):
                    size = [record["size"] for record in db_data]
                    true_total_lots = [record["true_total_lots"] for record in db_data]
                    self.assert_list_equal_ignore_order(
                        size,
                        true_total_lots,
                        f"手数不一致: 详情{size}, 指令{true_total_lots}"
                    )
                    logger.info(f"手数一致: 详情{size}, 指令{true_total_lots}")

    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    @allure.story("场景5：复制下单-手数0.1-1，总订单5-停止功能")
    @allure.description("""
    ### 测试说明
    - 前置条件：有云策略和云跟单
      1. 进行开仓，手数范围0.1-1，总订单5-停止功能
      2. 点击停止
      3. 校验账号的下单总手数和数据库的手数，应该不相等
      4. 进行平仓
      5. 校验账号的数据是否正确
    - 预期结果：云策略下单的停止功能正确
    """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    class TestVPSOrderSend5(APITestBase):
        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-策略开仓")
        def test_trader_orderSend(self, class_random_str, var_manager, logged_session):
            # 1. 发送策略开仓请求
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
            data = {
                "symbol": trader_ordersend["symbol"],
                "placedType": 0,
                "remark": class_random_str,
                "intervalTime": 30000,
                "type": 1,
                "totalNum": "5",
                "totalSzie": "",
                "startSize": "0.1",
                "endSize": "1",
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

        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-策略开仓停止")
        def test_scenario_trader_stopOrder(self, class_random_str, var_manager, logged_session):
            # 发送策略开仓停止请求
            MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
            params = {
                "type": "0",
                "traderId": MT5vps_trader_id
            }
            response = self.send_get_request(
                logged_session,
                '/subcontrol/trader/stopOrder',
                params=params
            )

            # 验证响应状态码和内容
            self.assert_response_status(
                response,
                200,
                "策略开仓停止失败"
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
                    WHERE foi.operation_type = %s
                        AND fod.account = %s
                        AND fod.comment = %s
                        """
                params = (
                    '0',
                    new_user["account"],
                    class_random_str
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )
            with allure.step("2. 数据校验"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证手数范围-结束手数"):
                    min_lot_size = db_data[0]["min_lot_size"]
                    self.verify_data(
                        actual_value=float(min_lot_size),
                        expected_value=float(trader_ordersend["endSize"]),
                        op=CompareOp.EQ,
                        message="结束手数应符合预期",
                        attachment_name="结束手数详情"
                    )
                    logging.info(f"结束手数验证通过: {trader_ordersend['endSize']}")

                with allure.step("验证手数范围-开始手数"):
                    max_lot_size = db_data[0]["max_lot_size"]
                    self.verify_data(
                        actual_value=float(max_lot_size),
                        expected_value=float(0.1),
                        op=CompareOp.EQ,
                        message="开始手数应符合预期",
                        attachment_name="开始手数详情"
                    )
                    logging.info(f"开始手数验证通过: {max_lot_size}")

                with allure.step("验证开仓的订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=5,
                        op=CompareOp.NE,
                        message=f"开仓的订单数量应该不是5",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"开仓的订单数量应该不是5，结果有{len(db_data)}个订单")

        @allure.title("数据库校验-策略开仓-跟单指令及订单详情数据检查")
        def test_dbquery_addsalve_orderSend(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
                sql = f"""
                    SELECT 
                        fod.size,
                        fod.comment,
                        fod.send_no,
                        fod.magical,
                        fod.open_price,
                        fod.symbol,
                        fod.order_no,
                        foi.true_total_lots,
                        foi.order_no,
                        foi.operation_type,
                        foi.create_time,
                        foi.status,
                        foi.total_lots,
                        foi.total_orders
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
                    MT5vps_user_accounts_1,
                    class_random_str
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )

            with allure.step("2. 数据校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证开仓的订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=5,
                        op=CompareOp.NE,
                        message=f"开仓的订单数量应该不是5",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"开仓的订单数量应该不是5，结果有{len(db_data)}个订单")

                with allure.step("验证详情手数和指令手数一致"):
                    size = [record["size"] for record in db_data]
                    total_lots = [record["total_lots"] for record in db_data]
                    self.assert_list_equal_ignore_order(
                        size,
                        total_lots,
                        f"手数不一致: 详情{size}, 指令{total_lots}"
                    )
                    logger.info(f"手数一致: 详情{size}, 指令{total_lots}")

        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-策略平仓")
        def test_trader_orderclose(self, class_random_str, var_manager, logged_session):
            # 1. 发送全平订单平仓请求
            MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
            new_user = var_manager.get_variable("new_user")
            data = {
                "isCloseAll": 1,
                "intervalTime": 100,
                "traderId": MT5vps_trader_id,
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

        # @pytest.mark.skip(reason=SKIP_REASON)
        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-跟单平仓")
        def test_addtrader_orderclose(self, class_random_str, var_manager, logged_session):
            # 1. 发送全平订单平仓请求
            MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
            MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
            data = {
                "isCloseAll": 1,
                "intervalTime": 100,
                "traderId": MT5vps_addslave_id,
                "account": MT5vps_user_accounts_1
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

        @allure.title("数据库校验-策略平仓-主指令及订单详情数据检查")
        def test_dbquery_orderSendclose(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                new_user = var_manager.get_variable("new_user")
                sql = f"""
                    SELECT 
                        fod.size,
                        fod.comment,
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

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证开仓的订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=5,
                        op=CompareOp.NE,
                        message=f"开仓的订单数量应该不是5",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"开仓的订单数量应该不是5，结果有{len(db_data)}个订单")

        @allure.title("数据库校验-策略平仓-跟单指令及订单详情数据检查")
        def test_dbquery_addsalve_orderSendclose(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
                MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
                sql = f"""
                    SELECT 
                        fod.size,
                        fod.comment,
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
                        AND fod.comment = %s
                        """
                params = (
                    '1',
                    MT5vps_user_accounts_1,
                    MT5vps_addslave_id,
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

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证开仓的订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=5,
                        op=CompareOp.NE,
                        message=f"开仓的订单数量应该不是5",
                        attachment_name="订单数量详情"
                    )
                    logging.info(f"开仓的订单数量应该不是5，结果有{len(db_data)}个订单")

                with allure.step("验证详情手数和指令手数一致"):
                    size = [record["size"] for record in db_data]
                    true_total_lots = [record["true_total_lots"] for record in db_data]
                    self.assert_list_equal_ignore_order(
                        size,
                        true_total_lots,
                        f"手数不一致: 详情{size}, 指令{true_total_lots}"
                    )
                    logger.info(f"手数一致: 详情{size}, 指令{true_total_lots}")

            time.sleep(30)

    @allure.story("场景6：VPS策略下单-手数范围0.6-1，总手数1")
    @allure.description("""
    ### 测试说明
    - 场景校验：手数范围>总手数>订单数量
    - 前置条件：有vps策略和vps跟单
      1. 进行开仓，手数范围0.6-1，总手数1
      2. 校验手数范围限制是否生效，只有一个订单，订单手数大于等于0.6
      3. 进行平仓
      4. 校验账号的数据是否正确
    - 预期结果：账号的数据正确，权重正确
    """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    class TestVPSOrderSend6(APITestBase):
        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-策略开仓")
        def test_trader_orderSend(self, class_random_str, var_manager, logged_session):
            # 1. 发送策略开仓请求
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
            data = {
                "symbol": trader_ordersend["symbol"],
                "placedType": 0,
                "remark": class_random_str,
                "intervalTime": 100,
                "type": 1,
                "totalNum": "",
                "totalSzie": "1.00",
                "startSize": "0.60",
                "endSize": "1.00",
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
                        fod.send_no,
                        fod.magical,
                        fod.open_price,
                        fod.symbol,
                        fod.order_no,
                        fod.comment,
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
                    WHERE foi.operation_type = %s
                        AND fod.account = %s
                        AND fod.comment = %s
                        """
                params = (
                    '0',
                    new_user["account"],
                    class_random_str
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )
            with allure.step("2. 数据校验"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证手数范围-开始手数"):
                    max_lot_size = db_data[0]["max_lot_size"]
                    self.verify_data(
                        actual_value=float(max_lot_size),
                        expected_value=float(0.6),
                        op=CompareOp.EQ,
                        message="开始手数应符合预期",
                        attachment_name="开始手数详情"
                    )
                    logging.info(f"开始手数验证通过: {max_lot_size}")

                with allure.step("验证手数范围-结束手数"):
                    min_lot_size = db_data[0]["min_lot_size"]
                    self.verify_data(
                        actual_value=float(min_lot_size),
                        expected_value=float(trader_ordersend["endSize"]),
                        op=CompareOp.EQ,
                        message="结束手数应符合预期",
                        attachment_name="结束手数详情"
                    )
                    logging.info(f"结束手数验证通过: {min_lot_size}")

                with allure.step("验证订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=1,
                        op=CompareOp.EQ,
                        message="订单数量符合预期",
                        attachment_name="订单数量"
                    )
                    logging.info(f"实际订单数量: {len(db_data)}")

                with allure.step("验证详情手数"):
                    size = db_data[0]["size"]
                    self.verify_data(
                        actual_value=float(size),
                        expected_value=0.6,
                        op=CompareOp.GE,
                        message="实际手数符合预期",
                        attachment_name="实际手数"
                    )
                    logging.info(f"实际手数: {size}")

                with allure.step("验证详情手数和指令手数一致"):
                    size = [record["size"] for record in db_data]
                    true_total_lots = [record["true_total_lots"] for record in db_data]
                    self.assert_list_equal_ignore_order(
                        size,
                        true_total_lots,
                        f"手数不一致: 详情{size}, 指令{true_total_lots}"
                    )
                    logger.info(f"手数一致: 详情{size}, 指令{true_total_lots}")

        @allure.title("数据库校验-策略开仓-跟单指令及订单详情数据检查")
        def test_dbquery_addsalve_orderSend(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
                sql = f"""
                    SELECT 
                        fod.size,
                        fod.send_no,
                        fod.magical,
                        fod.open_price,
                        fod.symbol,
                        fod.order_no,
                        fod.comment,
                        foi.true_total_lots,
                        foi.order_no,
                        foi.operation_type,
                        foi.create_time,
                        foi.status,
                        foi.total_lots,
                        foi.total_orders
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
                    MT5vps_user_accounts_1,
                    class_random_str
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )
            with allure.step("2. 数据校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=1,
                        op=CompareOp.EQ,
                        message="订单数量符合预期",
                        attachment_name="订单数量"
                    )
                    logging.info(f"实际订单数量: {len(db_data)}")

                with allure.step("验证详情手数"):
                    size = db_data[0]["size"]
                    self.verify_data(
                        actual_value=float(size),
                        expected_value=0.6,
                        op=CompareOp.GE,
                        message="实际手数符合预期",
                        attachment_name="实际手数"
                    )
                    logging.info(f"实际手数: {size}")

        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-策略平仓")
        def test_trader_orderclose(self, class_random_str, var_manager, logged_session):
            # 1. 发送全平订单平仓请求
            MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
            new_user = var_manager.get_variable("new_user")
            data = {
                "isCloseAll": 1,
                "intervalTime": 100,
                "traderId": MT5vps_trader_id,
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

        # @pytest.mark.skip(reason=SKIP_REASON)
        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-跟单平仓")
        def test_addtrader_orderclose(self, class_random_str, var_manager, logged_session):
            # 1. 发送全平订单平仓请求
            MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
            MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
            data = {
                "isCloseAll": 1,
                "intervalTime": 100,
                "traderId": MT5vps_addslave_id,
                "account": MT5vps_user_accounts_1
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

        @allure.title("数据库校验-策略平仓-主指令及订单详情数据检查")
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

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=1,
                        op=CompareOp.EQ,
                        message="订单数量符合预期",
                        attachment_name="订单数量"
                    )
                    logging.info(f"实际订单数量: {len(db_data)}")

                with allure.step("验证详情手数"):
                    size = db_data[0]["size"]
                    self.verify_data(
                        actual_value=float(size),
                        expected_value=0.6,
                        op=CompareOp.GE,
                        message="实际手数符合预期",
                        attachment_name="实际手数"
                    )
                    logging.info(f"实际手数: {size}")

        @allure.title("数据库校验-策略平仓-跟单指令及订单详情数据检查")
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
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )
            with allure.step("2. 验证主指令开仓数据"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=1,
                        op=CompareOp.EQ,
                        message="订单数量符合预期",
                        attachment_name="订单数量"
                    )
                    logging.info(f"实际订单数量: {len(db_data)}")

                with allure.step("验证详情手数"):
                    size = db_data[0]["size"]
                    self.verify_data(
                        actual_value=float(size),
                        expected_value=0.6,
                        op=CompareOp.GE,
                        message="实际手数符合预期",
                        attachment_name="实际手数"
                    )
                    logging.info(f"实际手数: {size}")

    @allure.story("场景7：VPS策略下单-手数范围0.3-1，总订单数量1，总手数5")
    @allure.description("""
    ### 测试说明
    - 场景校验：手数范围>总手数>订单数量
    - 前置条件：有vps策略和vps跟单
      1. 进行开仓，手数范围0.3-1，总订单数量1，总手数5
      2. 校验权重，优先满足手数范围，然后是总手数
      3. 进行平仓
      4. 校验账号的数据是否正确
    - 预期结果：权重正确，优先满足手数范围，然后是总手数
    """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    class TestVPSOrderSend7(APITestBase):
        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-策略开仓")
        def test_trader_orderSend(self, class_random_str, var_manager, logged_session):
            # 1. 发送策略开仓请求
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
            data = {
                "symbol": trader_ordersend["symbol"],
                "placedType": 0,
                "remark": class_random_str,
                "intervalTime": 100,
                "type": 1,
                "totalNum": "1",
                "totalSzie": "5.00",
                "startSize": "0.30",
                "endSize": "1.00",
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
                        fod.account,
                        fod.size,
                        fod.send_no,
                        fod.magical,
                        fod.open_price,
                        fod.symbol,
                        fod.order_no,
                        fod.comment,
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
                    WHERE foi.operation_type = %s
                        AND fod.account = %s
                        AND fod.comment = %s
                        """
                params = (
                    '0',
                    new_user["account"],
                    class_random_str
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )
            with allure.step("2. 数据校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证详情手数"):
                    size = [record["size"] for record in db_data]
                    for i in size:
                        self.verify_data(
                            actual_value=float(i),
                            expected_value=0.3,
                            op=CompareOp.GE,
                            message="实际手数符合预期",
                            attachment_name="实际手数"
                        )
                    logging.info(f"实际手数: {size}")

                with allure.step("验证订单数量"):
                    total_orders = db_data[0]["total_orders"]
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=total_orders,
                        op=CompareOp.NE,
                        message="订单数量符合预期",
                        attachment_name="订单数量"
                    )
                    logging.info(f"实际订单数量: {len(db_data)}")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=5,
                        op=CompareOp.EQ,
                        message="详情总手数符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f'订单详情总手数是：{total}')

        @allure.title("数据库校验-策略开仓-跟单指令及订单详情数据检查")
        def test_dbquery_addsalve_orderSend(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
                sql = f"""
                    SELECT 
                        fod.account,
                        fod.size,
                        fod.send_no,
                        fod.magical,
                        fod.open_price,
                        fod.symbol,
                        fod.order_no,
                        fod.comment,
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
                    WHERE foi.operation_type = %s
                        AND fod.account = %s
                        AND fod.comment = %s
                        """
                params = (
                    '0',
                    MT5vps_user_accounts_1,
                    class_random_str
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )
            with allure.step("2. 数据校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证详情手数"):
                    size = db_data[0]["size"]
                    self.verify_data(
                        actual_value=float(size),
                        expected_value=0.3,
                        op=CompareOp.GE,
                        message="实际手数符合预期",
                        attachment_name="实际手数"
                    )
                    logging.info(f"实际手数: {size}")

                with allure.step("验证订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=1,
                        op=CompareOp.NE,
                        message="订单数量符合预期",
                        attachment_name="订单数量"
                    )
                    logging.info(f"实际订单数量: {len(db_data)}")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=5,
                        op=CompareOp.EQ,
                        message="详情总手数符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f'订单详情总手数是：{total}')

                with allure.step("验证指令总手数"):
                    true_total_lots = [record["true_total_lots"] for record in db_data]
                    true_total_lotssum = sum(true_total_lots)
                    # 关键优化：四舍五入保留两位小数
                    true_total_lotssum = round(float(true_total_lotssum), 2)
                    self.verify_data(
                        actual_value=float(true_total_lotssum),
                        expected_value=5,
                        op=CompareOp.EQ,
                        message="指令总手数符合预期",
                        attachment_name="指令总手数"
                    )
                    logging.info(f"指令总手数符合预期: {float(true_total_lotssum)}")

                with allure.step("验证详情手数和指令手数一致"):
                    size = [record["size"] for record in db_data]
                    total_lots = [record["total_lots"] for record in db_data]
                    self.assert_list_equal_ignore_order(
                        size,
                        total_lots,
                        f"手数不一致: 详情{size}, 指令{total_lots}"
                    )
                    logger.info(f"手数一致: 详情{size}, 指令{total_lots}")

        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-策略平仓")
        def test_trader_orderclose(self, class_random_str, var_manager, logged_session):
            # 1. 发送全平订单平仓请求
            MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
            new_user = var_manager.get_variable("new_user")
            data = {
                "isCloseAll": 1,
                "intervalTime": 100,
                "traderId": MT5vps_trader_id,
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

        # @pytest.mark.skip(reason=SKIP_REASON)
        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-跟单平仓")
        def test_addtrader_orderclose(self, class_random_str, var_manager, logged_session):
            # 1. 发送全平订单平仓请求
            MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
            MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
            data = {
                "isCloseAll": 1,
                "intervalTime": 100,
                "traderId": MT5vps_addslave_id,
                "account": MT5vps_user_accounts_1
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

        @allure.title("数据库校验-策略平仓-主指令及订单详情数据检查")
        def test_dbquery_orderSendclose(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                new_user = var_manager.get_variable("new_user")
                sql = f"""
                    SELECT 
                        fod.account,
                        fod.size,
                        fod.close_no,
                        fod.magical,
                        fod.open_price,
                        fod.symbol,
                        fod.order_no,
                        fod.comment,
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

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证详情手数"):
                    size = db_data[0]["size"]
                    self.verify_data(
                        actual_value=float(size),
                        expected_value=0.3,
                        op=CompareOp.GE,
                        message="实际手数符合预期",
                        attachment_name="实际手数"
                    )
                    logging.info(f"实际手数: {size}")

                with allure.step("验证订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=1,
                        op=CompareOp.NE,
                        message="订单数量符合预期",
                        attachment_name="订单数量"
                    )
                    logging.info(f"实际订单数量: {len(db_data)}")

        @allure.title("数据库校验-策略平仓-跟单指令及订单详情数据检查")
        def test_dbquery_addsalve_orderSendclose(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
                MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
                sql = f"""
                    SELECT 
                        fod.account,
                        fod.size,
                        fod.close_no,
                        fod.magical,
                        fod.open_price,
                        fod.symbol,
                        fod.order_no,
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
                        AND fod.trader_id = %s
                        """
                params = (
                    '1',
                    MT5vps_user_accounts_1,
                    class_random_str,
                    MT5vps_addslave_id,
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

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证详情手数"):
                    size = db_data[0]["size"]
                    self.verify_data(
                        actual_value=float(size),
                        expected_value=0.3,
                        op=CompareOp.GE,
                        message="实际手数符合预期",
                        attachment_name="实际手数"
                    )
                    logging.info(f"实际手数: {size}")

                with allure.step("验证订单数量"):
                    self.verify_data(
                        actual_value=len(db_data),
                        expected_value=1,
                        op=CompareOp.NE,
                        message="订单数量符合预期",
                        attachment_name="订单数量"
                    )
                    logging.info(f"实际订单数量: {len(db_data)}")

    @allure.story("场景8：VPS交易分配-手数范围0.1-1，总手数0.01")
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
    class TestVPStradingOrders8(APITestBase):
        @allure.title("VPS交易下单-分配下单请求")
        def test_copy_order_send(self, class_random_str, logged_session, var_manager):
            # 发送VPS策略账号交易下单-复制下单
            masOrderSend = var_manager.get_variable("masOrderSend")
            MT5vps_trader_user_id = var_manager.get_variable("MT5vps_trader_user_id")
            data = {
                "traderList": [MT5vps_trader_user_id],
                "type": 1,
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

    @allure.story("场景9：VPS交易分配-手数范围0.1-1，总手数2")
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
    class TestVPStradingOrders9(APITestBase):
        @allure.title("VPS交易下单-分配下单请求")
        def test_copy_order_send(self, class_random_str, logged_session, var_manager):
            # 发送VPS策略账号交易下单-复制下单
            masOrderSend = var_manager.get_variable("masOrderSend")
            MT5vps_trader_user_id = var_manager.get_variable("MT5vps_trader_user_id")
            data = {
                "traderList": [MT5vps_trader_user_id],
                "type": 1,
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

    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    @allure.story("场景10：复制下单-手数范围0.01-1，总手数0.3")
    @allure.description("""
    ### 测试说明
    - 前置条件：有vps策略和vps跟单
      1. 修改跟单账号下单比例0.25，手数取余-取小数，合约比例0.5
      2. 进行开仓，手数范围0.01-1，总手数0.3
      3. 校验账号的数据是否正确-下单手数是0.3*0.25*0.5=0.0375，取小数是0.03
      4. 进行平仓
      5. 校验账号的数据是否正确
    - 预期结果：账号的数据正确
    """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    class TestVPSOrderSend10(APITestBase):
        @pytest.mark.url("vps")
        @allure.title("修改跟单账号-手数取余-取小数")
        def test_follow_updateSlave(self, class_random_str, var_manager, logged_session, encrypted_password):
            with allure.step("1. 修改跟单账号"):
                # remainder  0 : 四舍五入  1：取小数
                new_user = var_manager.get_variable("new_user")
                MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
                MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
                MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
                platformId = var_manager.get_variable("platformId")
                MT5vps_template_id2 = var_manager.get_variable("MT5vps_template_id2")
                data = {
                    "traderId": MT5vps_trader_id,
                    "platform": new_user["platform"],
                    "account": MT5vps_user_accounts_1,
                    "password": encrypted_password,
                    "platformType": 1,
                    "remark": "",
                    "followDirection": 0,
                    "followMode": 1,
                    "remainder": 1,
                    "followParam": "0.25",
                    "placedType": 0,
                    "templateId": MT5vps_template_id2,
                    "followStatus": 1,
                    "followOpen": 1,
                    "followClose": 1,
                    "followRep": 0,
                    "fixedComment": "",
                    "commentType": None,
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

        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-策略开仓")
        def test_trader_orderSend(self, class_random_str, var_manager, logged_session):
            # 1. 发送策略开仓请求
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
            data = {
                "symbol": trader_ordersend["symbol"],
                "placedType": 0,
                "remark": class_random_str,
                "intervalTime": 100,
                "type": 1,
                "totalNum": "",
                "totalSzie": "0.3",
                "startSize": "0.01",
                "endSize": "1.0",
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
                    WHERE foi.operation_type = %s
                        AND fod.account = %s
                        AND fod.comment = %s
                        """
                params = (
                    '0',
                    new_user["account"],
                    class_random_str
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )
            with allure.step("2. 数据校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(0.3),
                        op=CompareOp.EQ,
                        abs_tol=0.001,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-策略开仓-跟单指令及订单详情数据检查")
        def test_dbquery_addsalve_orderSend(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
                sql = f"""
                    SELECT 
                        fod.size,
                        fod.comment,
                        fod.send_no,
                        fod.magical,
                        fod.open_price,
                        fod.symbol,
                        fod.order_no,
                        foi.true_total_lots,
                        foi.order_no,
                        foi.operation_type,
                        foi.create_time,
                        foi.status,
                        foi.total_lots,
                        foi.total_orders
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
                    MT5vps_user_accounts_1,
                    class_random_str
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )

            with allure.step("2. 数据校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(0.03),
                        op=CompareOp.EQ,
                        abs_tol=0.001,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-策略平仓")
        def test_trader_orderclose(self, class_random_str, var_manager, logged_session):
            # 1. 发送全平订单平仓请求
            MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
            new_user = var_manager.get_variable("new_user")
            data = {
                "isCloseAll": 1,
                "intervalTime": 100,
                "traderId": MT5vps_trader_id,
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

        # @pytest.mark.skip(reason=SKIP_REASON)
        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-跟单平仓")
        def test_addtrader_orderclose(self, class_random_str, var_manager, logged_session):
            # 1. 发送全平订单平仓请求
            MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
            MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
            data = {
                "isCloseAll": 1,
                "intervalTime": 100,
                "traderId": MT5vps_addslave_id,
                "account": MT5vps_user_accounts_1
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

        @allure.title("数据库校验-策略平仓-主指令及订单详情数据检查")
        def test_dbquery_orderSendclose(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                new_user = var_manager.get_variable("new_user")
                sql = f"""
                    SELECT 
                        fod.size,
                        fod.comment,
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

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(0.3),
                        op=CompareOp.EQ,
                        abs_tol=0.001,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-策略平仓-跟单指令及订单详情数据检查")
        def test_dbquery_addsalve_orderSendclose(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
                MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
                sql = f"""
                    SELECT 
                        fod.size,
                        fod.comment,
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
                        AND fod.comment = %s
                        """
                params = (
                    '1',
                    MT5vps_user_accounts_1,
                    MT5vps_addslave_id,
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

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(0.03),
                        op=CompareOp.EQ,
                        abs_tol=0.001,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

                with allure.step("验证详情手数和指令手数一致"):
                    size = [record["size"] for record in db_data]
                    true_total_lots = [record["true_total_lots"] for record in db_data]
                    self.assert_list_equal_ignore_order(
                        size,
                        true_total_lots,
                        f"手数不一致: 详情{size}, 指令{true_total_lots}"
                    )
                    logger.info(f"手数一致: 详情{size}, 指令{true_total_lots}")

    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    @allure.story("场景11：复制下单-手数范围0.01-1，总手数0.3")
    @allure.description("""
    ### 测试说明
    - 前置条件：有vps策略和vps跟单
      1. 修改跟单账号下单比例0.25，手数取余-四舍五入，合约比例0.5
      2. 进行开仓，手数范围0.01-1，总手数0.3
      3. 校验账号的数据是否正确-下单手数是0.3*0.25*0.5=0.0375，四舍五入是0.04
      4. 进行平仓
      5. 校验账号的数据是否正确
    - 预期结果：账号的数据正确
    """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    class TestVPSOrderSend11(APITestBase):
        @pytest.mark.url("vps")
        @allure.title("修改跟单账号-手数取余-取小数")
        def test_follow_updateSlave(self, class_random_str, var_manager, logged_session, encrypted_password):
            with allure.step("1. 修改跟单账号"):
                # remainder  0 : 四舍五入  1：取小数
                new_user = var_manager.get_variable("new_user")
                MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
                MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
                MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
                platformId = var_manager.get_variable("platformId")
                MT5vps_template_id2 = var_manager.get_variable("MT5vps_template_id2")
                data = {
                    "traderId": MT5vps_trader_id,
                    "platform": new_user["platform"],
                    "account": MT5vps_user_accounts_1,
                    "password": encrypted_password,
                    "platformType": 1,
                    "remark": "",
                    "followDirection": 0,
                    "followMode": 1,
                    "remainder": 0,
                    "followParam": "0.25",
                    "placedType": 0,
                    "templateId": MT5vps_template_id2,
                    "followStatus": 1,
                    "followOpen": 1,
                    "followClose": 1,
                    "followRep": 0,
                    "fixedComment": "",
                    "commentType": None,
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

        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-策略开仓")
        def test_trader_orderSend(self, class_random_str, var_manager, logged_session):
            # 1. 发送策略开仓请求
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
            data = {
                "symbol": trader_ordersend["symbol"],
                "placedType": 0,
                "remark": class_random_str,
                "intervalTime": 100,
                "type": 1,
                "totalNum": "",
                "totalSzie": "0.3",
                "startSize": "0.01",
                "endSize": "1.0",
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
                    WHERE foi.operation_type = %s
                        AND fod.account = %s
                        AND fod.comment = %s
                        """
                params = (
                    '0',
                    new_user["account"],
                    class_random_str
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )
            with allure.step("2. 数据校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(0.3),
                        op=CompareOp.EQ,
                        abs_tol=0.001,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-策略开仓-跟单指令及订单详情数据检查")
        def test_dbquery_addsalve_orderSend(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
                sql = f"""
                    SELECT 
                        fod.size,
                        fod.comment,
                        fod.send_no,
                        fod.magical,
                        fod.open_price,
                        fod.symbol,
                        fod.order_no,
                        foi.true_total_lots,
                        foi.order_no,
                        foi.operation_type,
                        foi.create_time,
                        foi.status,
                        foi.total_lots,
                        foi.total_orders
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
                    MT5vps_user_accounts_1,
                    class_random_str
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )

            with allure.step("2. 数据校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(0.04),
                        op=CompareOp.EQ,
                        abs_tol=0.001,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-策略平仓")
        def test_trader_orderclose(self, class_random_str, var_manager, logged_session):
            # 1. 发送全平订单平仓请求
            MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
            new_user = var_manager.get_variable("new_user")
            data = {
                "isCloseAll": 1,
                "intervalTime": 100,
                "traderId": MT5vps_trader_id,
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

        # @pytest.mark.skip(reason=SKIP_REASON)
        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-跟单平仓")
        def test_addtrader_orderclose(self, class_random_str, var_manager, logged_session):
            # 1. 发送全平订单平仓请求
            MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
            MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
            data = {
                "isCloseAll": 1,
                "intervalTime": 100,
                "traderId": MT5vps_addslave_id,
                "account": MT5vps_user_accounts_1
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

        @allure.title("数据库校验-策略平仓-主指令及订单详情数据检查")
        def test_dbquery_orderSendclose(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                new_user = var_manager.get_variable("new_user")
                sql = f"""
                    SELECT 
                        fod.size,
                        fod.comment,
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

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(0.3),
                        op=CompareOp.EQ,
                        abs_tol=0.001,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-策略平仓-跟单指令及订单详情数据检查")
        def test_dbquery_addsalve_orderSendclose(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
                MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
                sql = f"""
                    SELECT 
                        fod.size,
                        fod.comment,
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
                        AND fod.comment = %s
                        """
                params = (
                    '1',
                    MT5vps_user_accounts_1,
                    MT5vps_addslave_id,
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

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(0.04),
                        op=CompareOp.EQ,
                        abs_tol=0.001,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

                with allure.step("验证详情手数和指令手数一致"):
                    size = [record["size"] for record in db_data]
                    true_total_lots = [record["true_total_lots"] for record in db_data]
                    self.assert_list_equal_ignore_order(
                        size,
                        true_total_lots,
                        f"手数不一致: 详情{size}, 指令{true_total_lots}"
                    )
                    logger.info(f"手数一致: 详情{size}, 指令{true_total_lots}")

    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    @allure.story("场景12：复制下单-手数范围0.01-1，总手数0.01")
    @allure.description("""
    ### 测试说明
    - 前置条件：有vps策略和vps跟单
      1. 修改跟单账号下单比例0.25，手数取余-四舍五入，合约比例0.5
      2. 进行开仓，手数范围0.01-1，总手数0.01
      3. 校验账号的数据是否正确-下单手数是0.01*0.25*0.5=0.00125，最低下单手数是0.01
      4. 进行平仓
      5. 校验账号的数据是否正确
    - 预期结果：账号的数据正确
    """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    class TestVPSOrderSend12(APITestBase):
        @pytest.mark.url("vps")
        @allure.title("修改跟单账号-手数取余-取小数")
        def test_follow_updateSlave(self, class_random_str, var_manager, logged_session, encrypted_password):
            with allure.step("1. 修改跟单账号"):
                # remainder  0 : 四舍五入  1：取小数
                new_user = var_manager.get_variable("new_user")
                MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
                MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
                MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
                platformId = var_manager.get_variable("platformId")
                MT5vps_template_id2 = var_manager.get_variable("MT5vps_template_id2")
                data = {
                    "traderId": MT5vps_trader_id,
                    "platform": new_user["platform"],
                    "account": MT5vps_user_accounts_1,
                    "password": encrypted_password,
                    "platformType": 1,
                    "remark": "",
                    "followDirection": 0,
                    "followMode": 1,
                    "remainder": 0,
                    "followParam": "0.25",
                    "placedType": 0,
                    "templateId": MT5vps_template_id2,
                    "followStatus": 1,
                    "followOpen": 1,
                    "followClose": 1,
                    "followRep": 0,
                    "fixedComment": "",
                    "commentType": None,
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

        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-策略开仓")
        def test_trader_orderSend(self, class_random_str, var_manager, logged_session):
            # 1. 发送策略开仓请求
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
            data = {
                "symbol": trader_ordersend["symbol"],
                "placedType": 0,
                "remark": class_random_str,
                "intervalTime": 100,
                "type": 1,
                "totalNum": "",
                "totalSzie": "0.01",
                "startSize": "0.01",
                "endSize": "1.0",
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
                    WHERE foi.operation_type = %s
                        AND fod.account = %s
                        AND fod.comment = %s
                        """
                params = (
                    '0',
                    new_user["account"],
                    class_random_str
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )
            with allure.step("2. 数据校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(0.01),
                        op=CompareOp.EQ,
                        abs_tol=0.001,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-策略开仓-跟单指令及订单详情数据检查")
        def test_dbquery_addsalve_orderSend(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
                sql = f"""
                    SELECT 
                        fod.size,
                        fod.comment,
                        fod.send_no,
                        fod.magical,
                        fod.open_price,
                        fod.symbol,
                        fod.order_no,
                        foi.true_total_lots,
                        foi.order_no,
                        foi.operation_type,
                        foi.create_time,
                        foi.status,
                        foi.total_lots,
                        foi.total_orders
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
                    MT5vps_user_accounts_1,
                    class_random_str
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.open_time"
                )

            with allure.step("2. 数据校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(0.01),
                        op=CompareOp.EQ,
                        abs_tol=0.001,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-策略平仓")
        def test_trader_orderclose(self, class_random_str, var_manager, logged_session):
            # 1. 发送全平订单平仓请求
            MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
            new_user = var_manager.get_variable("new_user")
            data = {
                "isCloseAll": 1,
                "intervalTime": 100,
                "traderId": MT5vps_trader_id,
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

        # @pytest.mark.skip(reason=SKIP_REASON)
        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-跟单平仓")
        def test_addtrader_orderclose(self, class_random_str, var_manager, logged_session):
            # 1. 发送全平订单平仓请求
            MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
            MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
            data = {
                "isCloseAll": 1,
                "intervalTime": 100,
                "traderId": MT5vps_addslave_id,
                "account": MT5vps_user_accounts_1
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

        @allure.title("数据库校验-策略平仓-主指令及订单详情数据检查")
        def test_dbquery_orderSendclose(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                new_user = var_manager.get_variable("new_user")
                sql = f"""
                    SELECT 
                        fod.size,
                        fod.comment,
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

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(0.01),
                        op=CompareOp.EQ,
                        abs_tol=0.001,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

        @allure.title("数据库校验-策略平仓-跟单指令及订单详情数据检查")
        def test_dbquery_addsalve_orderSendclose(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
                MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
                sql = f"""
                    SELECT 
                        fod.size,
                        fod.comment,
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
                        AND fod.comment = %s
                        """
                params = (
                    '1',
                    MT5vps_user_accounts_1,
                    MT5vps_addslave_id,
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

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1, 3),
                        op=CompareOp.IN,
                        message="订单状态应为0或1或3",
                        attachment_name="订单状态详情"
                    )
                    logging.info(f"订单状态验证通过: {status}")

                with allure.step("验证详情总手数"):
                    size = [record["size"] for record in db_data]
                    total = sum(size)
                    # 关键优化：四舍五入保留两位小数
                    total = round(float(total), 2)
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(0.01),
                        op=CompareOp.EQ,
                        abs_tol=0.001,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

                with allure.step("验证详情手数和指令手数一致"):
                    size = [record["size"] for record in db_data]
                    true_total_lots = [record["true_total_lots"] for record in db_data]
                    self.assert_list_equal_ignore_order(
                        size,
                        true_total_lots,
                        f"手数不一致: 详情{size}, 指令{true_total_lots}"
                    )
                    logger.info(f"手数一致: 详情{size}, 指令{true_total_lots}")
