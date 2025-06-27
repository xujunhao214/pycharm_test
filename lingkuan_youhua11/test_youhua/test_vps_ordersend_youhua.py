import allure
import logging
import pytest
from lingkuan_youhua11.VAR.VAR import *
from lingkuan_youhua11.conftest import var_manager
from lingkuan_youhua11.commons.api_base import APITestBase

logger = logging.getLogger(__name__)


@allure.feature("VPS策略下单-正常开仓平仓")
class TestVPSOrderSend(APITestBase):
    # ---------------------------
    # 跟单软件看板-VPS数据-策略开仓
    # ---------------------------
    @allure.title("跟单软件看板-VPS数据-策略开仓")
    def test_trader_orderSend(self, vps_api_session, var_manager, logged_session):
        # 1. 发送策略开仓请求
        trader_ordersend = var_manager.get_variable("trader_ordersend")
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        data = {
            "symbol": trader_ordersend["symbol"],
            "placedType": 0,
            "remark": trader_ordersend["remark"],
            "intervalTime": 100,
            "type": 0,
            "totalNum": trader_ordersend["totalNum"],
            "totalSzie": trader_ordersend["totalSzie"],
            "startSize": trader_ordersend["startSize"],
            "endSize": trader_ordersend["endSize"],
            "traderId": vps_trader_id
        }
        response = self.send_post_request(
            vps_api_session,
            '/subcontrol/trader/orderSend',
            json_data=data,
            sleep_seconds=0
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

    @allure.title("数据库校验-策略开仓-策略开仓指令")
    def test_dbquery_orderSend(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否有策略开仓指令"):
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            trader_ordersend = var_manager.get_variable("trader_ordersend")

            # 使用正确格式的条件字典
            conditions = {
                "like": {"field": "symbol", "value": trader_ordersend["symbol"]},
                "type": trader_ordersend["type"],
                "min_lot_size": trader_ordersend["endSize"],
                "max_lot_size": trader_ordersend["startSize"],
                "remark": trader_ordersend["remark"],
                "total_lots": trader_ordersend["totalSzie"],
                "total_orders": trader_ordersend["totalNum"],
                "trader_id": vps_trader_id
            }

            # 使用基类的wait_for_db_record方法
            db_data = self.wait_for_db_record(
                db_transaction,
                trader_ordersend["table"],
                conditions,
                time_field="create_time",
                time_range=MYSQL_TIME,
                timeout=WAIT_TIMEOUT,
                poll_interval=POLL_INTERVAL
            )

        with allure.step("2. 提取数据"):
            self.log_and_assert(db_data, "数据库查询结果为空，无法提取数据")

            order_no = db_data[0]["order_no"]
            logging.info(f"获取策略账号下单的订单号: {order_no}")
            var_manager.set_runtime_variable("order_no", order_no)

        with allure.step("3. 验证订单状态"):
            self.verify_db_status(
                db_data,
                "master_order_status",
                0,
                "下单后平仓状态master_order_status应为0（未平仓）"
            )

            operation_type = db_data[0]["operation_type"]
            self.log_and_assert(
                operation_type == 0,
                f"操作类型operation_type应为0(下单)，实际状态为: {operation_type}"
            )

            status = db_data[0]["status"]
            self.log_and_assert(
                status in (0, 1),
                f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}"
            )

            allure.attach("订单状态验证通过", "成功详情", allure.attachment_type.TEXT)

    @allure.title("数据库校验-策略开仓-跟单开仓指令")
    def test_dbquery_orderSend_addsalve(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否有跟单开仓指令"):
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            add_Slave = var_manager.get_variable("add_Slave")

            # 使用正确格式的条件字典
            conditions = {
                "like": {"field": "symbol", "value": trader_ordersend["symbol"]},
                "status": "1",
                "if_follow": "1",
                "master_order_status": "0",
                "type": trader_ordersend["type"],
                "trader_id": vps_trader_id
            }

            # 使用基类的wait_for_db_record方法
            db_data = self.wait_for_db_record(
                db_transaction,
                trader_ordersend["table"],
                conditions,
                time_field="create_time",
                time_range=MYSQL_TIME,
                timeout=WAIT_TIMEOUT,
                poll_interval=POLL_INTERVAL
            )

        with allure.step("2. 验证订单状态和手数"):
            self.log_and_assert(db_data, "数据库查询结果为空，无法提取数据")

            total_lots = [item["total_lots"] for item in db_data]
            true_total_lots = [item["true_total_lots"] for item in db_data]
            logging.info(f"总手数: {total_lots}, 实际总手数: {true_total_lots}")

            self.log_and_assert(
                total_lots == true_total_lots,
                f"总手数不一致: {total_lots} vs {true_total_lots}"
            )

            traded_lots = [item["traded_lots"] for item in db_data]
            traded_lots_sum = sum(traded_lots)
            followParam = add_Slave["followParam"]
            logging.info(f"实际下单手数: {traded_lots}, 下单参数: {followParam}")

            self.log_and_assert(
                float(traded_lots_sum) == float(followParam),
                f"手数总和不一致: {traded_lots_sum} vs {followParam}"
            )

            allure.attach("手数验证通过", "成功详情", allure.attachment_type.TEXT)

    @allure.title("数据库校验-策略开仓-持仓检查")
    def test_dbquery_order_detail(self, var_manager, db_transaction):
        with allure.step("1. 根据下单指令获取跟单账号订单数据"):
            order_no = var_manager.get_variable("order_no")
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            trader_ordersend = var_manager.get_variable("trader_ordersend")

            # 使用正确格式的条件字典
            conditions = {
                "like": {"field": "symbol", "value": trader_ordersend["symbol"]},
                "send_no": order_no,
                "type": trader_ordersend["type"],
                "trader_id": vps_trader_id
            }

            # 使用基类的wait_for_db_record方法
            db_data = self.wait_for_db_record(
                db_transaction,
                trader_ordersend["table_detail"],
                conditions,
                time_field="create_time",
                time_range=MYSQL_TIME,
                timeout=WAIT_TIMEOUT,
                poll_interval=POLL_INTERVAL
            )

            self.log_and_assert(db_data, "数据库查询结果为空，无法提取数据")

            order_nos = [item["order_no"] for item in db_data]
            logging.info(f"持仓订单的订单号: {order_nos}")
            var_manager.set_runtime_variable("order_nos", order_nos)

            addsalve_size = [item["size"] for item in db_data]
            total = sum(addsalve_size)
            logging.info(f"手数: {addsalve_size}, 手数总和: {total}")

            # 验证手数一致性
            expected_total = float(trader_ordersend["totalSzie"])
            self.log_and_assert(
                total == expected_total,
                f"跟单总手数和下单的手数不相等 (实际: {total}, 预期: {expected_total})"
            )

            allure.attach("手数总和验证通过", "成功详情", allure.attachment_type.TEXT)

    @allure.title("跟单软件看板-VPS数据-策略平仓")
    def test_trader_orderclose(self, vps_api_session, var_manager, logged_session, db_transaction):
        # 1. 发送全平订单平仓请求
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        vps_trader_isCloseAll = var_manager.get_variable("vps_trader_isCloseAll")
        data = {
            "isCloseAll": 1,
            "intervalTime": 100,
            "traderId": vps_trader_id,
            "account": vps_trader_isCloseAll["account"]
        }
        response = self.send_post_request(
            vps_api_session,
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

    @allure.title("数据库校验-策略平仓-策略平仓指令")
    def test_dbquery_traderclose(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否有策略平仓指令"):
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            vps_trader_isCloseAll = var_manager.get_variable("vps_trader_isCloseAll")

            # 使用正确格式的条件字典
            conditions = {
                "like": {"field": "symbol", "value": vps_trader_isCloseAll["symbol"]},
                "master_order_status": "1",
                "trader_id": vps_trader_id
            }

            # 使用基类的wait_for_db_record方法
            db_data = self.wait_for_db_record(
                db_transaction,
                vps_trader_isCloseAll["table"],
                conditions,
                time_field="create_time",
                time_range=MYSQL_TIME,
                timeout=WAIT_TIMEOUT,
                poll_interval=POLL_INTERVAL
            )

        with allure.step("2. 提取并验证数据"):
            self.log_and_assert(db_data, "数据库查询结果为空，无法提取数据")

            master_order_status = db_data[0]["master_order_status"]
            logging.info(f"订单状态master_order_status由0未平仓变为1已平仓: {master_order_status}")
            var_manager.set_runtime_variable("master_order_status", master_order_status)

            self.verify_db_status(
                db_data,
                "master_order_status",
                1,
                "平仓后订单状态master_order_status应为1"
            )

            allure.attach("平仓状态验证通过", "成功详情", allure.attachment_type.TEXT)