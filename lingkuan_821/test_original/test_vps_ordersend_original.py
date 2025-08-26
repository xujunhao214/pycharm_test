import time
import math
import allure
import logging
import pytest
from lingkuan_821.VAR.VAR import *
from lingkuan_821.conftest import var_manager
from lingkuan_821.commons.api_base import APITestBase

logger = logging.getLogger(__name__)
SKIP_REASON = "该用例暂时跳过"


class VPSOrderTestBase(APITestBase):
    """VPS策略下单测试基类，封装公共测试逻辑"""

    # 子类需定义测试参数
    test_params = {
        "totalNum": "",
        "totalSzie": "",
        "startSize": "",
        "endSize": "",
        "intervalTime": ""
    }

    def _send_open_order(self, var_manager, logged_session):
        """发送开仓请求（公共方法）"""
        trader_ordersend = var_manager.get_variable("trader_ordersend")
        vps_trader_id = var_manager.get_variable("vps_trader_id")

        data = {
            "symbol": trader_ordersend["symbol"],
            "placedType": 0,
            "remark": trader_ordersend["remark"],
            "intervalTime": self.test_params["intervalTime"],
            "type": 0,
            "totalNum": self.test_params["totalNum"],
            "totalSzie": self.test_params["totalSzie"],
            "startSize": self.test_params["startSize"],
            "endSize": self.test_params["endSize"],
            "traderId": vps_trader_id
        }

        with allure.step(f"发送开仓请求"):
            response = self.send_post_request(
                logged_session,
                '/subcontrol/trader/orderSend',
                json_data=data,
            )

            # 验证响应
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
            return response

    def _send_close_order(self, var_manager, logged_session, trader_id, account):
        """发送平仓请求（公共方法）"""
        data = {
            "isCloseAll": 1,
            "intervalTime": 100,
            "traderId": trader_id,
            "account": account
        }

        with allure.step(f"发送平仓请求"):
            response = self.send_post_request(
                logged_session,
                '/subcontrol/trader/orderClose',
                json_data=data,
            )

            # 验证响应
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
            return response

    def _verify_open_order_master(self, var_manager, db_transaction):
        """验证主指令开仓数据（公共方法）"""
        new_user = var_manager.get_variable("new_user")

        # 1. 获取订单数据
        with allure.step("1. 获取主指令开仓数据"):
            sql = """
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
            params = ('0', new_user["account"])

            db_data = self.query_database_with_time_with_timezone(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="fod.open_time"
            )

        # 2. 数据校验
        with allure.step("2. 验证主指令开仓数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            # 验证订单状态
            status = db_data[0]["status"]
            assert status in (0, 1), f"订单状态应为0或1，实际为: {status}"
            logger.info(f"订单状态验证通过: {status}")

            # 验证手数范围
            if self.test_params["startSize"]:
                max_lot_size = db_data[0]["max_lot_size"]
                assert math.isclose(
                    float(self.test_params["startSize"]),
                    float(max_lot_size),
                    rel_tol=1e-9
                ), f'开始手数不符: 预期{self.test_params["startSize"]}, 实际{max_lot_size}'
                logger.info(f"开始手数验证通过: {self.test_params['startSize']}")

            if self.test_params["endSize"]:
                min_lot_size = db_data[0]["min_lot_size"]
                assert math.isclose(
                    float(self.test_params["endSize"]),
                    float(min_lot_size),
                    rel_tol=1e-9
                ), f'结束手数不符: 预期{self.test_params["endSize"]}, 实际{min_lot_size}'
                logger.info(f"结束手数验证通过: {self.test_params['endSize']}")

            # 验证总订单数
            if self.test_params["totalNum"]:
                total_orders = db_data[0]["total_orders"]
                assert math.isclose(
                    float(self.test_params["totalNum"]),
                    float(total_orders),
                    rel_tol=1e-9
                ), f'总订单数不符: 预期{self.test_params["totalNum"]}, 实际{total_orders}'
                logger.info(f"总订单数验证通过: {self.test_params['totalNum']}")

            # 验证总手数
            if self.test_params["totalSzie"]:
                total_lots = db_data[0]["total_lots"]
                assert math.isclose(
                    float(self.test_params["totalSzie"]),
                    float(total_lots),
                    rel_tol=1e-9
                ), f'总手数不符: 预期{self.test_params["totalSzie"]}, 实际{total_lots}'
                logger.info(f"总手数验证通过: {self.test_params['totalSzie']}")

                # 验证详情总手数
                size = [record["size"] for record in db_data]
                total = sum(size)
                assert math.isclose(
                    float(self.test_params["totalSzie"]),
                    float(total),
                    rel_tol=1e-9
                ), f'详情总手数不符: 预期{self.test_params["totalSzie"]}, 实际{total}'
                logger.info(f"详情总手数验证通过: {total}")

        return db_data

    def _verify_open_order_slave(self, var_manager, db_transaction):
        """验证跟单指令开仓数据（公共方法）"""
        vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")

        # 1. 获取订单数据
        with allure.step("1. 获取跟单指令开仓数据"):
            sql = """
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
            params = ('0', vps_user_accounts_1)

            db_data = self.query_database_with_time_with_timezone(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="fod.open_time"
            )

        # 2. 数据校验
        with allure.step("2. 验证跟单指令开仓数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            # 验证订单状态
            status = db_data[0]["status"]
            assert status in (0, 1), f"订单状态应为0或1，实际为: {status}"
            logger.info(f"订单状态验证通过: {status}")

            # 验证手数一致性
            size = [record["size"] for record in db_data]
            total_lots = [record["total_lots"] for record in db_data]
            self.assert_list_equal_ignore_order(
                size,
                total_lots,
                f"手数不一致: 详情{size}, 指令{total_lots}"
            )
            logger.info("手数一致性验证通过")

            # 验证总手数
            if self.test_params["totalSzie"]:
                total_sumlots = sum(total_lots)
                total = sum(size)
                assert math.isclose(
                    float(self.test_params["totalSzie"]),
                    float(total_sumlots),
                    rel_tol=1e-9
                ) and math.isclose(
                    float(self.test_params["totalSzie"]),
                    float(total),
                    rel_tol=1e-9
                ), f'总手数不符: 预期{self.test_params["totalSzie"]}, 指令{total_sumlots}, 详情{total}'
                logger.info(f"总手数验证通过: {self.test_params['totalSzie']}")

        return db_data

    def _verify_close_order_master(self, var_manager, db_transaction):
        """验证主指令平仓数据（公共方法）"""
        new_user = var_manager.get_variable("new_user")

        # 1. 获取订单数据
        with allure.step("1. 获取主指令平仓数据"):
            sql = """
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
            params = ('1', new_user["account"])

            db_data = self.query_database_with_time_with_timezone(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="fod.close_time"
            )

        # 2. 数据校验
        with allure.step("2. 验证主指令平仓数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            # 验证订单状态
            status = db_data[0]["status"]
            assert status in (0, 1), f"订单状态应为0或1，实际为: {status}"
            logger.info(f"平仓状态验证通过: {status}")

            # 验证总手数
            if self.test_params["totalSzie"]:
                size = [record["size"] for record in db_data]
                total = sum(size)
                assert math.isclose(
                    float(self.test_params["totalSzie"]),
                    float(total),
                    rel_tol=1e-9
                ), f'平仓总手数不符: 预期{self.test_params["totalSzie"]}, 实际{total}'
                logger.info(f"平仓总手数验证通过: {total}")

        return db_data

    def _verify_close_order_slave(self, var_manager, db_transaction):
        """验证跟单指令平仓数据（公共方法）"""
        vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
        vps_addslave_id = var_manager.get_variable("vps_addslave_id")

        # 1. 获取订单数据
        with allure.step("1. 获取跟单指令平仓数据"):
            sql = """
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
            params = ('1', vps_user_accounts_1, vps_addslave_id)

            db_data = self.query_database_with_time_with_timezone(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="fod.close_time"
            )

        # 2. 数据校验
        with allure.step("2. 验证跟单指令平仓数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            # 验证订单状态
            status = db_data[0]["status"]
            assert status in (0, 1), f"订单状态应为0或1，实际为: {status}"
            logger.info(f"平仓状态验证通过: {status}")

            # 验证手数一致性
            size = [record["size"] for record in db_data]
            total_lots = [record["total_lots"] for record in db_data]
            self.assert_list_equal_ignore_order(
                size,
                total_lots,
                f"手数不一致: 详情{size}, 指令{total_lots}"
            )
            logger.info("平仓手数一致性验证通过")

            # 验证总手数
            if self.test_params["totalSzie"]:
                total = sum(size)
                assert math.isclose(
                    float(self.test_params["totalSzie"]),
                    float(total),
                    rel_tol=1e-9
                ), f'平仓总手数不符: 预期{self.test_params["totalSzie"]}, 实际{total}'
                logger.info(f"平仓总手数验证通过: {total}")

        time.sleep(25)
        return db_data


# @pytest.mark.skip(reason=SKIP_REASON)
@allure.feature("VPS策略下单-正常开仓平仓")
@allure.description("""
### 用例说明
- 前置条件：有vps策略和vps跟单
- 操作步骤：
  1. 进行开仓
    手数范围：0.1-1
    总订单数量：3
    总手数：1
  2. 检验喊单账号和跟单账号的数据是否正确
  3. 进行平仓
  4. 检验喊单账号和跟单账号的数据是否正确
- 预期结果：检验喊单账号和跟单账号的数据正确
""")
class TestVPSOrderSend1(VPSOrderTestBase):
    """测试用例1：手数范围0.1-1，总订单3，总手数1"""
    test_params = {
        "totalNum": "3",
        "totalSzie": "1",
        "startSize": "0.1",
        "endSize": "1",
        "intervalTime": "100"
    }

    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-策略开仓")
    def test_trader_orderSend(self, var_manager, logged_session):
        self._send_open_order(var_manager, logged_session)

    @allure.title("数据库校验-策略开仓-主指令及订单详情数据检查")
    def test_dbquery_orderSend(self, var_manager, db_transaction):
        self._verify_open_order_master(var_manager, db_transaction)

    @allure.title("数据库校验-策略开仓-跟单指令及订单详情数据检查")
    def test_dbquery_addsalve_orderSend(self, var_manager, db_transaction):
        self._verify_open_order_slave(var_manager, db_transaction)

    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-策略平仓")
    def test_trader_orderclose(self, var_manager, logged_session):
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        new_user = var_manager.get_variable("new_user")
        self._send_close_order(var_manager, logged_session, vps_trader_id, new_user["account"])

    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-跟单平仓")
    def test_addtrader_orderclose(self, var_manager, logged_session):
        vps_addslave_id = var_manager.get_variable("vps_addslave_id")
        vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
        self._send_close_order(var_manager, logged_session, vps_addslave_id, vps_user_accounts_1)

    @allure.title("数据库校验-策略平仓-主指令及订单详情数据检查")
    def test_dbquery_orderSendclose(self, var_manager, db_transaction):
        self._verify_close_order_master(var_manager, db_transaction)

    @allure.title("数据库校验-策略平仓-跟单指令及订单详情数据检查")
    def test_dbquery_addsalve_orderSendclose(self, var_manager, db_transaction):
        self._verify_close_order_slave(var_manager, db_transaction)


# @pytest.mark.skip(reason=SKIP_REASON)
@allure.feature("VPS策略下单-正常开仓平仓")
@allure.description("""
### 用例说明
- 前置条件：有vps策略和vps跟单
- 操作步骤：
  1. 进行开仓
    手数范围：0.01-0.01
    总订单数量：无
    总手数：0.01
  2. 检验喊单账号和跟单账号的数据是否正确
  3. 进行平仓
  4. 检验喊单账号和跟单账号的数据是否正确
- 预期结果：检验喊单账号和跟单账号的数据正确
""")
class TestVPSOrderSend2(VPSOrderTestBase):
    """测试用例2：手数范围0.01-0.01，总手数0.01"""
    test_params = {
        "totalNum": "",
        "totalSzie": "0.01",
        "startSize": "0.01",
        "endSize": "0.01",
        "intervalTime": "100"
    }

    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-策略开仓")
    def test_trader_orderSend(self, var_manager, logged_session):
        self._send_open_order(var_manager, logged_session)

    @allure.title("数据库校验-策略开仓-主指令及订单详情数据检查")
    def test_dbquery_orderSend(self, var_manager, db_transaction):
        self._verify_open_order_master(var_manager, db_transaction)

    @allure.title("数据库校验-策略开仓-跟单指令及订单详情数据检查")
    def test_dbquery_addsalve_orderSend(self, var_manager, db_transaction):
        self._verify_open_order_slave(var_manager, db_transaction)

    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-策略平仓")
    def test_trader_orderclose(self, var_manager, logged_session):
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        new_user = var_manager.get_variable("new_user")
        self._send_close_order(var_manager, logged_session, vps_trader_id, new_user["account"])

    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-跟单平仓")
    def test_addtrader_orderclose(self, var_manager, logged_session):
        vps_addslave_id = var_manager.get_variable("vps_addslave_id")
        vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
        self._send_close_order(var_manager, logged_session, vps_addslave_id, vps_user_accounts_1)

    @allure.title("数据库校验-策略平仓-主指令及订单详情数据检查")
    def test_dbquery_orderSendclose(self, var_manager, db_transaction):
        self._verify_close_order_master(var_manager, db_transaction)

    @allure.title("数据库校验-策略平仓-跟单指令及订单详情数据检查")
    def test_dbquery_addsalve_orderSendclose(self, var_manager, db_transaction):
        self._verify_close_order_slave(var_manager, db_transaction)


# @pytest.mark.skip(reason=SKIP_REASON)
@allure.feature("VPS策略下单-正常开仓平仓")
@allure.description("""
### 用例说明
- 前置条件：有vps策略和vps跟单
- 操作步骤：
  1. 进行开仓
    手数范围：0.1-1
    总订单数量：无
    总手数：5
  2. 检验喊单账号和跟单账号的数据是否正确
  3. 进行平仓
  4. 检验喊单账号和跟单账号的数据是否正确
- 预期结果：检验喊单账号和跟单账号的数据正确
""")
class TestVPSOrderSend3(VPSOrderTestBase):
    """测试用例3：手数范围0.1-1，总手数5"""
    test_params = {
        "totalNum": "",
        "totalSzie": "5",
        "startSize": "0.1",
        "endSize": "1",
        "intervalTime": "100"
    }

    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-策略开仓")
    def test_trader_orderSend(self, var_manager, logged_session):
        self._send_open_order(var_manager, logged_session)

    @allure.title("数据库校验-策略开仓-主指令及订单详情数据检查")
    def test_dbquery_orderSend(self, var_manager, db_transaction):
        self._verify_open_order_master(var_manager, db_transaction)

    @allure.title("数据库校验-策略开仓-跟单指令及订单详情数据检查")
    def test_dbquery_addsalve_orderSend(self, var_manager, db_transaction):
        self._verify_open_order_slave(var_manager, db_transaction)

    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-策略平仓")
    def test_trader_orderclose(self, var_manager, logged_session):
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        new_user = var_manager.get_variable("new_user")
        self._send_close_order(var_manager, logged_session, vps_trader_id, new_user["account"])

    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-跟单平仓")
    def test_addtrader_orderclose(self, var_manager, logged_session):
        vps_addslave_id = var_manager.get_variable("vps_addslave_id")
        vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
        self._send_close_order(var_manager, logged_session, vps_addslave_id, vps_user_accounts_1)

    @allure.title("数据库校验-策略平仓-主指令及订单详情数据检查")
    def test_dbquery_orderSendclose(self, var_manager, db_transaction):
        self._verify_close_order_master(var_manager, db_transaction)

    @allure.title("数据库校验-策略平仓-跟单指令及订单详情数据检查")
    def test_dbquery_addsalve_orderSendclose(self, var_manager, db_transaction):
        self._verify_close_order_slave(var_manager, db_transaction)


# @pytest.mark.skip(reason=SKIP_REASON)
@allure.feature("VPS策略下单-正常开仓平仓")
@allure.description("""
### 用例说明
- 前置条件：有vps策略和vps跟单
- 操作步骤：
  1. 进行开仓
    手数范围：0.01-1
    总订单数量：10
    总手数：无
  2. 检验喊单账号和跟单账号的数据是否正确
  3. 进行平仓
  4. 检验喊单账号和跟单账号的数据正确
- 预期结果：检验喊单账号和跟单账号的数据正确
""")
class TestVPSOrderSend4(VPSOrderTestBase):
    """测试用例4：手数范围0.01-1，总订单10"""
    test_params = {
        "totalNum": "10",
        "totalSzie": "",
        "startSize": "0.01",
        "endSize": "1",
        "intervalTime": "100"
    }

    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-策略开仓")
    def test_trader_orderSend(self, var_manager, logged_session):
        self._send_open_order(var_manager, logged_session)

    @allure.title("数据库校验-策略开仓-主指令及订单详情数据检查")
    def test_dbquery_orderSend(self, var_manager, db_transaction):
        self._verify_open_order_master(var_manager, db_transaction)

    @allure.title("数据库校验-策略开仓-跟单指令及订单详情数据检查")
    def test_dbquery_addsalve_orderSend(self, var_manager, db_transaction):
        self._verify_open_order_slave(var_manager, db_transaction)

    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-策略平仓")
    def test_trader_orderclose(self, var_manager, logged_session):
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        new_user = var_manager.get_variable("new_user")
        self._send_close_order(var_manager, logged_session, vps_trader_id, new_user["account"])

    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-跟单平仓")
    def test_addtrader_orderclose(self, var_manager, logged_session):
        vps_addslave_id = var_manager.get_variable("vps_addslave_id")
        vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
        self._send_close_order(var_manager, logged_session, vps_addslave_id, vps_user_accounts_1)

    @allure.title("数据库校验-策略平仓-主指令及订单详情数据检查")
    def test_dbquery_orderSendclose(self, var_manager, db_transaction):
        self._verify_close_order_master(var_manager, db_transaction)

    @allure.title("数据库校验-策略平仓-跟单指令及订单详情数据检查")
    def test_dbquery_addsalve_orderSendclose(self, var_manager, db_transaction):
        self._verify_close_order_slave(var_manager, db_transaction)


# @pytest.mark.skip(reason=SKIP_REASON)
@allure.feature("VPS策略下单-正常开仓平仓")
@allure.description("""
### 用例说明
- 前置条件：有vps策略和vps跟单
- 操作步骤：
  1. 进行开仓
    手数范围：0.1-1
    总订单数量：无
    总手数：1
  2. 校验订单数量，数据库的订单手数和开仓手数不相等
  3. 发送停止请求
  4. 进行平仓
- 预期结果：平仓停止功能正确，数据库的订单手数和开仓手数不相等
""")
class TestVPSOrderSend5(VPSOrderTestBase):
    """测试用例5：手数范围0.1-1，总订单无，总手数1"""
    test_params = {
        "totalNum": "",
        "totalSzie": "1",
        "startSize": "0.1",
        "endSize": "1",
        "intervalTime": "40000"

    }

    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-策略开仓")
    def test_trader_orderSend(self, var_manager, logged_session):
        self._send_open_order(var_manager, logged_session)

    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-停止功能校验")
    def test_trader_stopOrder(self, var_manager, logged_session):
        # 1. 发送策略开仓停止请求
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        params = {
            "type": "0",
            "traderId": vps_trader_id
        }
        response = self.send_get_request(
            logged_session,
            '/subcontrol/trader/stopOrder',
            params=params
        )

        # 2. 验证响应状态码和内容
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
            assert status in (0, 1), f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}"
            logging.info(f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}")

            total_lots = [record["total_lots"] for record in db_data]
            total_sumlots = sum(total_lots)
            assert not math.isclose(float(1), float(total_sumlots), rel_tol=1e-9), \
                f'下单总手数是：1，指令表总手数是：{total_sumlots}'
            logging.info(f'下单总手数是：1，指令表总手数是：{total_sumlots} 不相等')

    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-策略平仓")
    def test_trader_orderclose(self, var_manager, logged_session):
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        new_user = var_manager.get_variable("new_user")
        self._send_close_order(var_manager, logged_session, vps_trader_id, new_user["account"])

    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-跟单平仓")
    def test_addtrader_orderclose(self, var_manager, logged_session):
        vps_addslave_id = var_manager.get_variable("vps_addslave_id")
        vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
        self._send_close_order(var_manager, logged_session, vps_addslave_id, vps_user_accounts_1)
