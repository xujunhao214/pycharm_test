import time
import math
import allure
import logging
import pytest
from lingkuan_821.VAR.VAR import *
from lingkuan_821.conftest import var_manager
from lingkuan_821.commons.api_base import APITestBase

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"


@allure.story("VPS策略下单-下单的场景校验")
@allure.description("""
### 测试说明
- 场景校验：手数范围>总手数>订单数量
- 前置条件：有vps策略和vps跟单
  1. 进行开仓，手数范围0.3-1，总订单数量5，总手数1
  2. 校验手数范围限制是否生效，只有一个订单，订单手数大于0.6
  3. 进行平仓
  4. 校验账号的数据是否正确
- 预期结果：账号的数据正确
""")
class TestVPSOrderSend2(APITestBase):
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
            "totalNum": "5",
            "totalSzie": "1.00",
            "startSize": "0.30",
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
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            status = db_data[0]["status"]
            with allure.step("验证订单状态"):
                assert status in (0, 1), f"订单状态应为0(处理中)或1(全部成功)，实际为: {status}"
                allure.attach(f"实际状态: {status}", "订单状态详情", allure.attachment_type.TEXT)
                logging.info(f"订单状态验证通过: {status}")

            with allure.step("验证订单数量"):
                assert len(db_data) != 5, f"开仓订单没有5个，实际有{len(db_data)}个"
                allure.attach(f"实际订单数量: {len(db_data)}", "订单数量详情", allure.attachment_type.TEXT)

            with allure.step("验证下单手数"):
                size = db_data[0]["size"]
                assert size > 0.3, f"下单手数应大于0.3，实际为：{size}"
                allure.attach(f"实际手数: {size}", "下单手数详情", allure.attachment_type.TEXT)
                logging.info(f"下单手数验证通过: {size}")

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

            status = db_data[0]["status"]
            with allure.step("验证订单状态"):
                assert status in (0, 1), f"订单状态应为0(处理中)或1(全部成功)，实际为: {status}"
                allure.attach(f"实际状态: {status}", "订单状态详情", allure.attachment_type.TEXT)
                logging.info(f"订单状态验证通过: {status}")

            with allure.step("验证订单数量"):
                assert len(db_data) != 5, f"开仓订单没有5个，实际有{len(db_data)}个"
                allure.attach(f"实际订单数量: {len(db_data)}", "订单数量详情", allure.attachment_type.TEXT)

            with allure.step("验证下单手数"):
                size = db_data[0]["size"]
                assert size > 0.3, f"下单手数应大于0.3，实际为：{size}"
                allure.attach(f"实际手数: {size}", "下单手数详情", allure.attachment_type.TEXT)
                logging.info(f"下单手数验证通过: {size}")

            with allure.step("验证下单总手数"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                totalSzie = trader_ordersend["totalSzie"]
                size = [record["size"] for record in db_data]
                total = sum(size)
                assert math.isclose(float(totalSzie), float(total), rel_tol=1e-9), \
                    f'下单总手数是：{totalSzie},订单详情总手数是：{total}'
                allure.attach(f'下单总手数是：{totalSzie},订单详情总手数是：{total}', allure.attachment_type.TEXT)
                logging.info(f'下单总手数是：{totalSzie},订单详情总手数是：{total}')

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

            with allure.step("验证订单数量"):
                assert len(db_data) != 5, f"开仓订单没有5个，实际有{len(db_data)}个"
                allure.attach(f"实际订单数量: {len(db_data)}", "订单数量详情", allure.attachment_type.TEXT)

            with allure.step("验证下单手数"):
                size = db_data[0]["size"]
                assert size > 0.3, f"下单手数应大于0.3，实际为：{size}"
                allure.attach(f"实际手数: {size}", "下单手数详情", allure.attachment_type.TEXT)
                logging.info(f"下单手数验证通过: {size}")

            with allure.step("验证下单总手数"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                totalSzie = trader_ordersend["totalSzie"]
                size = [record["size"] for record in db_data]
                total = sum(size)
                assert math.isclose(float(totalSzie), float(total), rel_tol=1e-9), \
                    f'下单总手数是：{totalSzie},订单详情总手数是：{total}'
                allure.attach(f'下单总手数是：{totalSzie},订单详情总手数是：{total}', allure.attachment_type.TEXT)
                logging.info(f'下单总手数是：{totalSzie},订单详情总手数是：{total}')

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
        with allure.step("2. 数据校验"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            status = db_data[0]["status"]
            with allure.step("验证订单状态"):
                assert status in (0, 1), f"订单状态应为0(处理中)或1(全部成功)，实际为: {status}"
                allure.attach(f"实际状态: {status}", "订单状态详情", allure.attachment_type.TEXT)
                logging.info(f"订单状态验证通过: {status}")

            with allure.step("验证订单数量"):
                assert len(db_data) != 5, f"开仓订单没有5个，实际有{len(db_data)}个"
                allure.attach(f"实际订单数量: {len(db_data)}", "订单数量详情", allure.attachment_type.TEXT)

            with allure.step("验证下单手数"):
                size = db_data[0]["size"]
                assert size > 0.3, f"下单手数应大于0.3，实际为：{size}"
                allure.attach(f"实际手数: {size}", "下单手数详情", allure.attachment_type.TEXT)
                logging.info(f"下单手数验证通过: {size}")

        # time.sleep(25)
