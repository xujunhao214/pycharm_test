import allure
import logging
import pytest
import time
import math
from lingkuan_814.VAR.VAR import *
from lingkuan_814.conftest import var_manager
from lingkuan_814.commons.api_base import APITestBase  # 导入基础类
from lingkuan_814.commons.redis_utils import *

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("VPS策略下单-漏开")
class TestLeakageopen(APITestBase):
    # ---------------------------
    # 跟单软件看板-VPS数据-修改跟单账号
    # ---------------------------
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-修改跟单账号（漏开）")
    def test_update_slave(self, var_manager, logged_session, encrypted_password):
        # 1. 发送修改策略账号请求
        add_Slave = var_manager.get_variable("add_Slave")
        vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
        vps_addslave_id = var_manager.get_variable("vps_addslave_id")
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        # 开仓给关闭followOpen：0
        data = {
            "traderId": vps_trader_id,
            "platform": add_Slave["platform"],
            "account": vps_user_accounts_1,
            "password": encrypted_password,
            "remark": add_Slave["remark"],
            "followDirection": 0,
            "followMode": 1,
            "remainder": 0,
            "followParam": 1,
            "placedType": 0,
            "templateId": 1,
            "followStatus": 1,
            "followOpen": 0,
            "followClose": 1,
            "followRep": 0,
            "fixedComment": add_Slave["fixedComment"],
            "commentType": 2,
            "digits": 0,
            "cfd": "@",
            "forex": "",
            "abRemark": "",
            "id": vps_addslave_id
        }
        response = self.send_post_request(
            logged_session,
            '/subcontrol/follow/updateSlave',
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "修改跟单账号失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    @allure.title("数据库校验-VPS数据-修改跟单账号是否成功")
    def test_dbquery_updateslave(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否修改成功"):
            vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
            sql = f"SELECT * FROM follow_trader_subscribe WHERE slave_account = %s"
            params = (vps_user_accounts_1,)

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
            )
        with allure.step("2. 对数据进行校验"):
            follow_open = db_data[0]["follow_open"]
            assert follow_open == 0, f"follow_open的状态应该是0，实际是：{follow_open}"

    # ---------------------------
    # 跟单软件看板-VPS数据-策略开仓-出现漏单
    # ---------------------------
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-策略开仓-出现漏单")
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

    # ---------------------------
    # 数据库校验-策略开仓-主指令及订单详情数据检查
    # ---------------------------
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
            db_data = self.wait_for_database_record_with_timezone(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="fod.open_time"
            )
        with allure.step("2. 数据校验"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            status = db_data[0]["status"]
            assert status in (0, 1), f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}"
            logging.info(f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}")

            min_lot_size = db_data[0]["min_lot_size"]
            endsize = trader_ordersend["endSize"]
            assert math.isclose(float(endsize), float(min_lot_size), rel_tol=1e-9), \
                f'手数范围：结束手数是：{endsize}，实际是：{min_lot_size}'
            logging.info(f'手数范围：结束手数是：{endsize}，实际是：{min_lot_size}')

            max_lot_size = db_data[0]["max_lot_size"]
            startSize = trader_ordersend["startSize"]
            assert math.isclose(float(startSize), float(max_lot_size), rel_tol=1e-9), \
                f'手数范围：开始手数是：{startSize}，实际是：{max_lot_size}'
            logging.info(f'手数范围：开始手数是：{startSize}，实际是：{max_lot_size}')

            total_orders = db_data[0]["total_orders"]
            totalNum = trader_ordersend["totalNum"]
            assert math.isclose(float(totalNum), float(total_orders), rel_tol=1e-9), \
                f'总订单数量是：{totalNum}，实际是：{total_orders}'
            logging.info(f'总订单数量是：{totalNum}，实际是：{total_orders}')

            total_lots = db_data[0]["total_lots"]
            totalSzie = trader_ordersend["totalSzie"]
            assert math.isclose(float(totalSzie), float(total_lots), rel_tol=1e-9), \
                f'下单总手数是：{totalSzie}，实际是：{total_lots}'
            logging.info(f'下单总手数是：{totalSzie}，实际是：{total_lots}')

            totalSzie = trader_ordersend["totalSzie"]
            size = [record["size"] for record in db_data]
            total = sum(size)
            assert math.isclose(float(totalSzie), float(total), rel_tol=1e-9), \
                f'下单总手数是：{totalSzie},订单详情总手数是：{total}'
            logging.info(f'下单总手数是：{totalSzie},订单详情总手数是：{total}')

    # ---------------------------
    # 数据库校验-策略开仓-跟单开仓指令
    # ---------------------------
    @allure.title("数据库校验-策略开仓-跟单开仓指令-根据status状态发现有漏单")
    def test_dbquery_orderSend_addsalve(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否有跟单开仓指令"):
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            symbol = trader_ordersend["symbol"]

            sql = f"""
                SELECT * 
                FROM follow_order_instruct 
                WHERE symbol LIKE %s 
                  AND instruction_type = %s 
                  AND master_order_status = %s 
                  AND type = %s 
                  AND trader_id = %s
                """
            params = (
                f"%{symbol}%",
                "2",
                "0",
                trader_ordersend["type"],
                vps_trader_id
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params
            )
        with allure.step("2. 对订单状态进行校验"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")
            status = db_data[0]["status"]
            assert status == 2, f"跟单失败，跟单状态status应该是2，实际是：{status}"

    # ---------------------------
    # 出现漏开-redis数据和数据库的数据做比对
    # ---------------------------
    @allure.title("出现漏开-redis数据和数据库的数据做比对")
    def test_dbquery_redis(self, var_manager, db_transaction, redis_order_data_send):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            new_user = var_manager.get_variable("new_user")
            symbol = trader_ordersend["symbol"]

            sql = f"""
                       SELECT * 
                       FROM follow_order_detail 
                       WHERE symbol LIKE %s 
                         AND source_user = %s
                         AND account = %s
                       """
            params = (
                f"%{symbol}%",
                new_user["account"],
                new_user["account"],
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="create_time"
            )

        with allure.step("2. 转换Redis数据为可比较格式"):
            if not redis_order_data_send:
                pytest.fail("Redis中未查询到订单数据")

            # 转换Redis数据为与数据库一致的格式
            vps_redis_comparable_list_open = convert_redis_orders_to_comparable_list(redis_order_data_send)
            logging.info(f"转换后的Redis数据: {vps_redis_comparable_list_open}")

            # 将转换后的数据存入变量管理器
            var_manager.set_runtime_variable("vps_redis_comparable_list_open", vps_redis_comparable_list_open)

        with allure.step("3. 比较Redis与数据库数据"):
            # 假设db_data是之前从数据库查询的结果
            if not db_data:
                pytest.fail("数据库中未查询到订单数据")

            # 提取数据库中的关键字段（根据实际数据库表结构调整）
            db_comparable_list = [
                {
                    "order_no": record["order_no"],  # 数据库order_no → 统一字段order_no
                    "magical": record["magical"],  # 数据库magical → 统一字段magical
                    "size": float(record["size"]),  # 数据库size → 统一字段size
                    "open_price": float(record["open_price"]),
                    "symbol": record["symbol"]
                }
                for record in db_data
            ]
            logging.info(f"数据库转换后: {db_comparable_list}")
            # 比较两个列表（可根据需要调整比较逻辑）
            self.assert_data_lists_equal(
                actual=vps_redis_comparable_list_open,
                expected=db_comparable_list,
                fields_to_compare=["order_no", "magical", "size", "open_price", "symbol"],
                tolerance=1e-6  # 浮点数比较容差
            )

    # ---------------------------
    # 跟单软件看板-VPS数据-策略开仓-一键补全
    # ---------------------------
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-开仓补全")
    def test_follow_repairSend(self, var_manager, logged_session):
        with allure.step("1. 发送开仓补全请求"):
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            data = {
                "type": 2,
                "masterId": vps_trader_id,
                "slaveId": vps_addslave_id
            }
            response = self.send_post_request(
                logged_session,
                '/subcontrol/follow/repairSend',
                json_data=data
            )

        with allure.step("2. 没有开仓，需要提前开仓才可以补全"):
            self.assert_json_value(
                response,
                "$.msg",
                "请开启补仓开关",
                "响应msg字段应为'请开启补仓开关'"
            )

    # ---------------------------
    # 跟单软件看板-VPS数据-修改跟单账号
    # ---------------------------
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-修改跟单账号")
    def test_update_slave2(self, var_manager, logged_session, encrypted_password):
        # 1. 发送修改策略账号请求
        add_Slave = var_manager.get_variable("add_Slave")
        vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        vps_addslave_id = var_manager.get_variable("vps_addslave_id")
        # 开仓给开启followOpen：1
        data = {
            "traderId": vps_trader_id,
            "platform": add_Slave["platform"],
            "account": vps_user_accounts_1,
            "password": encrypted_password,
            "remark": add_Slave["remark"],
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
            "fixedComment": add_Slave["fixedComment"],
            "commentType": 2,
            "digits": 0,
            "cfd": "@",
            "forex": "",
            "abRemark": "",
            "id": vps_addslave_id
        }
        response = self.send_post_request(
            logged_session,
            '/subcontrol/follow/updateSlave',
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "修改跟单账号失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    @allure.title("数据库校验-VPS数据-修改跟单账号是否成功")
    def test_dbquery_updateslave2(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否修改成功"):
            vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
            sql = f"SELECT * FROM follow_trader_subscribe WHERE slave_account = %s"
            params = (vps_user_accounts_1,)

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params
            )

        with allure.step("2. 对数据进行校验"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")
            follow_open = db_data[0]["follow_open"]
            assert follow_open == 1, f"数据修改失败，数据follow_openy应该是1，实际是：{follow_open}"

    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-修改完之后进行开仓补全")
    def test_follow_repairSend2(self, var_manager, logged_session):
        with allure.step("1. 发送开仓补全请求"):
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            data = {
                "type": 2,
                "masterId": vps_trader_id,
                "slaveId": vps_addslave_id
            }
            response = self.send_post_request(
                logged_session,
                '/subcontrol/follow/repairSend',
                json_data=data
            )

        with allure.step("2. 补仓成功"):
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

    # ---------------------------
    # 数据库校验-策略开仓-跟单指令及订单详情数据检查
    # ---------------------------
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
            db_data = self.wait_for_database_record_with_timezone(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="fod.open_time"
            )
        with allure.step("2. 数据校验"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            status = db_data[0]["status"]
            assert status in (0, 1), f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}"
            logging.info(f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}")

            total_lots = [record["total_lots"] for record in db_data]
            total_sumlots = sum(total_lots)
            totalSzie = trader_ordersend["totalSzie"]
            size = [record["size"] for record in db_data]
            total = sum(size)
            assert math.isclose(float(totalSzie), float(total_sumlots), rel_tol=1e-9) and \
                   math.isclose(float(totalSzie), float(total), rel_tol=1e-9), \
                f'下单总手数是：{totalSzie}，指令表总手数是：{total_sumlots},订单详情总手数是：{total}'
            logging.info(f'下单总手数是：{totalSzie}，指令表总手数是：{total_sumlots},订单详情总手数是：{total}')

            self.assert_list_equal_ignore_order(
                size,
                total_lots,
                f"订单详情列表的手数：{size}和指令列表的手数：{total_lots}不一致"
            )

    # ---------------------------
    # 跟单软件看板-VPS数据-策略平仓
    # ---------------------------
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-策略平仓")
    def test_trader_orderclose(self, var_manager, logged_session, db_transaction):
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

    # ---------------------------
    # 数据库校验-策略平仓-主指令及订单详情数据检查
    # ---------------------------
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
            db_data = self.wait_for_database_record_with_timezone(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="fod.close_time"
            )
        with allure.step("2. 数据校验"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            status = db_data[0]["status"]
            assert status in (0, 1), f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}"
            logging.info(f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}")

            totalSzie = trader_ordersend["totalSzie"]
            size = [record["size"] for record in db_data]
            total = sum(size)
            assert math.isclose(float(totalSzie), float(total), rel_tol=1e-9), \
                f'下单总手数是：{totalSzie}，订单详情总手数是：{total}'
            logging.info(f'下单总手数是：{totalSzie}，订单详情总手数是：{total}')

    # ---------------------------
    # 数据库校验-策略平仓-跟单指令及订单详情数据检查
    # ---------------------------
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
            db_data = self.wait_for_database_record_with_timezone(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="fod.close_time"
            )
        with allure.step("2. 数据校验"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            status = db_data[0]["status"]
            assert status in (0, 1), f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}"
            logging.info(f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}")

            totalSzie = trader_ordersend["totalSzie"]
            size = [record["size"] for record in db_data]
            total = sum(size)
            assert math.isclose(float(totalSzie), float(total), rel_tol=1e-9), \
                f'下单总手数是：{totalSzie}，订单详情总手数是：{total}'
            logging.info(f'下单总手数是：{totalSzie}，订单详情总手数是：{total}')
            total_lots = [record["total_lots"] for record in db_data]
            self.assert_list_equal_ignore_order(
                size,
                total_lots,
                f"订单详情列表的手数：{size}和指令列表的手数：{total_lots}不一致"
            )
            logging.info(f"订单详情列表的手数：{size}和指令列表的手数：{total_lots}")

        time.sleep(25)
