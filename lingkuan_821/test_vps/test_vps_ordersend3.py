import time
import math
import allure
import logging
import pytest
from lingkuan_821.VAR.VAR import *
from lingkuan_821.conftest import var_manager
from lingkuan_821.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"


@allure.feature("VPS策略下单-开仓的场景校验")
class TestVPSOrderSend_newScenarios:
    @allure.story("场景1：VPS策略下单-下单的场景校验")
    @allure.description("""
    ### 测试说明
    - 场景校验：手数范围>总手数>订单数量
    - 前置条件：有vps策略和vps跟单
      1. 进行开仓，手数范围0.6-1，总手数1
      2. 校验手数范围限制是否生效，只有一个订单，订单手数大于0.6
      3. 进行平仓
      4. 校验账号的数据是否正确
    - 预期结果：账号的数据正确，权重正确
    """)
    class TestVPSOrderSend1(APITestBase):
        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-策略开仓")
        def test_trader_orderSend(self, var_manager, logged_session):
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
                "startSize": "0.60",
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

        @allure.title("数据库校验-策略开仓-主指令及订单详情数据检查")
        def test_dbquery_orderSend(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情界面跟单账号数据"):
                new_user = var_manager.get_variable("new_user")
                sql = f"""
                    SELECT 
                        fod.size,
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
                        """
                params = (
                    '0',
                    new_user["account"],
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
                    pytest.fail("数据库查询结果为空，无法提取数据")

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1),
                        op=CompareOp.IN,
                        message="订单状态应为0或1",
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
                        op=CompareOp.GT,
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
        def test_dbquery_addsalve_orderSend(self, var_manager, db_transaction):
            with allure.step("1. 获取订单详情界面跟单账号数据"):
                vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
                sql = f"""
                    SELECT 
                        fod.size,
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
            with allure.step("2. 数据校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1),
                        op=CompareOp.IN,
                        message="订单状态应为0或1",
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
                        op=CompareOp.GT,
                        message="实际手数符合预期",
                        attachment_name="实际手数"
                    )
                    logging.info(f"实际手数: {size}")

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
        def test_addtrader_orderclose(self, var_manager, logged_session):
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

        @allure.title("数据库校验-策略平仓-主指令及订单详情数据检查")
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
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )
            with allure.step("2. 数据校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1),
                        op=CompareOp.IN,
                        message="订单状态应为0或1",
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
                        op=CompareOp.GT,
                        message="实际手数符合预期",
                        attachment_name="实际手数"
                    )
                    logging.info(f"实际手数: {size}")

        @allure.title("数据库校验-策略平仓-跟单指令及订单详情数据检查")
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
                db_data = self.query_database_with_time_with_timezone(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="fod.close_time"
                )
            with allure.step("2. 验证主指令开仓数据"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

                with allure.step("验证订单状态"):
                    status = db_data[0]["status"]
                    self.verify_data(
                        actual_value=status,
                        expected_value=(0, 1),
                        op=CompareOp.IN,
                        message="订单状态应为0或1",
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
                        op=CompareOp.GT,
                        message="实际手数符合预期",
                        attachment_name="实际手数"
                    )
                    logging.info(f"实际手数: {size}")

            time.sleep(25)