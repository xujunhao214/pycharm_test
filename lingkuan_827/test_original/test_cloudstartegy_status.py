# lingkuan_827/tests/test_云策略_ordersend.py
import allure
import logging
import pytest
import time
import math
from lingkuan_827.VAR.VAR import *
from lingkuan_827.conftest import var_manager
from lingkuan_827.commons.api_base import *
from lingkuan_827.commons.redis_utils import *

logger = logging.getLogger(__name__)
SKIP_REASON = "该用例暂时跳过"


@allure.feature("交易下单-云策略复制下单-云策略-策略状态关闭")
@allure.description("""
### 用例说明
- 前置条件：有云策略和云跟单
- 操作步骤：
  1. 修改云策略 策略状态为关闭
  2. 进行开仓
  3. 跟单账号跟单失败，有漏单数据，把redis数据和MySQL数据进行校验
  4. 修改云策略 策略状态为开启
  5. 进行补单操作，然后平仓
- 预期结果：云策略 策略状态为关闭，有漏单数据
""")
class Testcloudstargy_status(APITestBase):
    @allure.title("云策略-云策略列表-修改策略账号信息")
    def test_mascontrol_cloudMaster(self, var_manager, logged_session, encrypted_password):
        # 1. 修改云策略状态status为1，关闭策略状态
        with allure.step("发送修改云策略的请求"):
            cloudTrader_group_id = var_manager.get_variable("cloudTrader_group_id")
            cloudMaster_id = var_manager.get_variable("cloudMaster_id")
            json_data = {
                "id": cloudMaster_id,
                "name": "自动化测试",
                "type": 0,
                "remark": None,
                "status": 1,
                "groupId": cloudTrader_group_id,
                "sort": None,
                "isMonitorRepair": 1,
                "isAutoRepair": 1
            }
            response = self.send_put_request(
                logged_session,
                '/mascontrol/cloudMaster',
                json_data=json_data,
            )

        with allure.step("2. 验证响应状态码和内容"):
            # 2. 验证响应状态码和内容
            self.assert_response_status(
                response,
                200,
                "发送修改云策略的请求失败"
            )
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

    @allure.title("数据库校验-云策略列表-修改云策略是否成功")
    def test_dbcloudTrader_cloudBatchUpdate(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否修改成功"):
            sql = f"SELECT * FROM follow_cloud_master WHERE name = %s"
            params = ("自动化测试",)

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.query_database_with_time(
                db_transaction=db_transaction,
                sql=sql,
                params=params
            )
        with allure.step("2. 对数据进行校验"):
            status = db_data[0]["status"]
            assert status == 1, f"status的状态应该是1，实际是：{status}"

    @allure.title("账号管理-交易下单-云策略账号复制下单-出现漏开")
    def test_bargain_masOrderSend(self, logged_session, var_manager):
        # 1. 发送云策略复制下单请求
        global cloudTrader_user_ids_2
        cloudTrader_user_ids_2 = var_manager.get_variable("cloudTrader_user_ids_2")
        data = {
            "traderList": [
                cloudTrader_user_ids_2
            ],
            "type": 0,
            "tradeType": 1,
            "intervalTime": 100,
            "symbol": "XAUUSD",
            "placedType": 0,
            "startSize": "0.10",
            "endSize": "1.00",
            "totalNum": "3",
            "totalSzie": "1.00",
            "remark": "测试交易下单数据"
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

    @allure.title("数据库校验-账号管理-交易下单-根据remark发现有漏单")
    def test_dbquery_orderSend_addsalve(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否有跟单开仓指令"):
            cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")

            sql = f"""
                SELECT 
                    fod.send_no,
                    fod.magical,
                    fod.remark,
                    fod.symbol,
                    fod.order_no,
                    foi.true_total_lots,
                    foi.order_no,
                    foi.operation_type,
                    foi.create_time,
                    foi.status,
                    foi.master_order,
                    foi.cloud_account,
                    foi.total_orders
                FROM 
                    follow_order_detail fod
                INNER JOIN 
                    follow_order_instruct foi 
                ON 
                    foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
                WHERE foi.operation_type = %s
                    AND foi.cloud_account = %s
                                        """
            params = (
                '0',
                cloudTrader_user_accounts_2,
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.query_database_with_time(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="foi.create_time"
            )
        with allure.step("2. 对订单状态进行校验"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")
            remark = db_data[0]["remark"]
            assert remark == "未开通下单状态", f"跟单失败，异常提示信息是：未开通下单状态，实际是：{remark}"

        with allure.step("3. 提取数据"):
            cloudTrader_master_order_open = [record["master_order"] for record in db_data]
            var_manager.set_runtime_variable("cloudTrader_master_order_open", cloudTrader_master_order_open)
            # print(f"master_order的数据是：{cloudTrader_master_order_open}")

    @allure.title("出现漏开-redis数据和数据库的数据做比对")
    def test_dbquery_redis(self, var_manager, db_transaction, redis_cloudTrader_data_send):
        with allure.step("1. 获取订单详情表账号数据"):
            cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
            cloudOrderSend = var_manager.get_variable("cloudOrderSend")
            symbol = cloudOrderSend["symbol"]

            sql = f"""
                           SELECT * 
                           FROM follow_order_detail 
                           WHERE symbol LIKE %s 
                             AND source_user = %s
                             AND account = %s
                           """
            params = (
                f"%{symbol}%",
                cloudTrader_user_accounts_2,
                cloudTrader_user_accounts_2,
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.query_database_with_time(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="create_time"
            )

        with allure.step("2. 转换Redis数据为可比较格式"):
            if not redis_cloudTrader_data_send:
                pytest.fail("Redis中未查询到订单数据")

            # 转换Redis数据为与数据库一致的格式
            cloudtrader_redis_comparable_openlist = convert_redis_orders_to_comparable_list(redis_cloudTrader_data_send)
            logging.info(f"转换后的Redis数据: {cloudtrader_redis_comparable_openlist}")

            # 将转换后的数据存入变量管理器
            var_manager.set_runtime_variable("cloudtrader_redis_comparable_openlist",
                                             cloudtrader_redis_comparable_openlist)

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
                actual=cloudtrader_redis_comparable_openlist,
                expected=db_comparable_list,
                fields_to_compare=["order_no", "magical", "size", "open_price", "symbol"],
                tolerance=1e-6  # 浮点数比较容差
            )

    @allure.title("云策略-云策略列表-修改策略账号信息")
    def test_mascontrol_cloudMaster2(self, var_manager, logged_session, encrypted_password):
        # 1. 修改云策略状态status为0，开启云策略状态
        with allure.step("发送修改云策略的请求"):
            cloudTrader_group_id = var_manager.get_variable("cloudTrader_group_id")
            cloudMaster_id = var_manager.get_variable("cloudMaster_id")
            json_data = {
                "id": cloudMaster_id,
                "name": "自动化测试",
                "type": 0,
                "remark": None,
                "status": 0,
                "groupId": cloudTrader_group_id,
                "sort": None,
                "isMonitorRepair": 1,
                "isAutoRepair": 1
            }
            response = self.send_put_request(
                logged_session,
                '/mascontrol/cloudMaster',
                json_data=json_data,
            )

        with allure.step("2. 验证响应状态码和内容"):
            # 2. 验证响应状态码和内容
            self.assert_response_status(
                response,
                200,
                "发送修改云策略的请求失败"
            )
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

    @allure.title("数据库校验-云策略列表-修改云策略是否成功")
    def test_dbcloudTrader_cloudBatchUpdate2(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否修改成功"):
            sql = f"SELECT * FROM follow_cloud_master WHERE name = %s"
            params = ("自动化测试",)

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.query_database_with_time(
                db_transaction=db_transaction,
                sql=sql,
                params=params
            )
        with allure.step("2. 对数据进行校验"):
            status = db_data[0]["status"]
            assert status == 0, f"status的状态应该是0，实际是：{status}"

    @allure.title("云策略-云策略列表-修改完之后进行开仓补全")
    def test_follow_repairSend(self, var_manager, logged_session):
        with allure.step("1. 发送开仓补全请求"):
            cloudMaster_id = var_manager.get_variable("cloudMaster_id")
            cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")
            cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
            cloudTrader_master_order_open = var_manager.get_variable("cloudTrader_master_order_open")
            for cloudTrader_master_order_open in cloudTrader_master_order_open:
                data = [
                    {
                        "cloudId": cloudMaster_id,
                        "repairType": 0,
                        "masterId": cloudTrader_traderList_2,
                        "slaveId": cloudTrader_traderList_4,
                        "masterOrder": cloudTrader_master_order_open
                    }
                ]
                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/batchRepairSend',
                    json_data=data
                )

            with allure.step("2. 补仓成功"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

    @allure.title("数据库校验-账号管理-交易下单-指令及订单详情数据检查")
    def test_dbcloudTrader_cloudOrderSend(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情表账号数据"):
            cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
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
                cloudTrader_user_accounts_4,
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.query_database_with_time(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="foi.create_time",
            )
        with allure.step("2. 数据校验"):
            cloudOrderSend = var_manager.get_variable("cloudOrderSend")
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            # 下单总手数与订单详情总手数校验
            totalSzie = cloudOrderSend["totalSzie"]
            size = [record["size"] for record in db_data]
            total = sum(size)
            assert math.isclose(float(totalSzie), float(total), rel_tol=1e-9, abs_tol=1e-9), \
                f'下单总手数是：{totalSzie},订单详情总手数是：{total}'
            logging.info(f'下单总手数是：{totalSzie},订单详情总手数是：{total}')

            # 下单手数与指令表手数校验
            total_lots = [record["total_lots"] for record in db_data]
            self.assert_list_equal_ignore_order(total_lots, size), f'下单手数是：{totalSzie},指令表手数是：{total_lots}'
            logging.info(f'下单手数是：{totalSzie},指令表手数是：{total_lots}')

    @allure.title("账号管理-交易下单-平仓")
    def test_cloudTrader_cloudOrderClose(self, logged_session, var_manager):
        cloudTrader_user_ids_2 = var_manager.get_variable("cloudTrader_user_ids_2")
        # 1. 发送平仓请求
        data = {
            "isCloseAll": 1,
            "intervalTime": 100,
            "traderList": [
                cloudTrader_user_ids_2
            ]
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

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-交易平仓-指令及订单详情数据检查")
    def test_dbcloudTrader_cloudOrderClose(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情表账号数据"):
            cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
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
                           """
            params = (
                '1',
                cloudTrader_user_accounts_4
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.query_database_with_time_with_timezone(
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

            # 平仓总手数校验
            totalSzie = trader_ordersend["totalSzie"]
            size = [record["size"] for record in db_data]
            total = sum(size)
            assert math.isclose(float(totalSzie), float(total), rel_tol=1e-9, abs_tol=1e-9), \
                f'下单总手数是：{totalSzie}，订单详情总手数是：{total}'
            logging.info(f'订单详情总手数是：{total}')

            time.sleep(25)
