import allure
import logging
import pytest
import time
from lingkuanMT5_1029copy.conftest import var_manager
from lingkuanMT5_1029copy.commons.api_base import *
from lingkuanMT5_1029copy.commons.redis_utils import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("VPS策略下单-漏单场景")
class TestLeakageopen_level:
    @allure.story("场景1：VPS策略下单-漏开")
    @allure.description("""
    ### 用例说明
    - 前置条件：有vps策略和vps跟单
    - 操作步骤：
      1. 修改vps跟单账号开仓-关闭
      2. 进行开仓
      3. 跟单账号开仓失败，有漏单数据，把redis数据和MySQL数据进行校验
      4. 修改vps跟单账号开仓-开启
      5. 进行补单操作，然后平仓
    - 预期结果：vps跟单账号开仓-关闭，有漏单数据
    """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    class TestLeakageopen(APITestBase):
        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-修改跟单账号（漏开）")
        def test_update_slave(self, class_random_str, var_manager, logged_session, encrypted_password):
            # 1. 发送修改vps跟单账号请求,修改followOpen：0关闭  1开启
            add_Slave = var_manager.get_variable("add_Slave")
            MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
            MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
            MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
            platformId = var_manager.get_variable("platformId")
            data = {
                "traderId": MT5vps_trader_id,
                "platform": add_Slave["platform"],
                "account": MT5vps_user_accounts_1,
                "password": encrypted_password,
                "remark": "",
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
                "fixedComment": "",
                "commentType": 2,
                "digits": 0,
                "cfd": "",
                "forex": "",
                "abRemark": "",
                "id": MT5vps_addslave_id,
                "platformType": 1,
                "platformId": platformId
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
        def test_dbquery_updateslave(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 查询数据库验证是否修改成功"):
                MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
                sql = f"SELECT * FROM follow_trader_subscribe WHERE slave_account = %s"
                params = (MT5vps_user_accounts_1,)

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                )
            with allure.step("2. 对数据进行校验"):
                follow_open = db_data[0]["follow_open"]
                assert follow_open == 0, f"follow_open的状态应该是0，实际是：{follow_open}"

        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-策略开仓-出现漏单")
        def test_trader_orderSend(self, class_random_str, var_manager, logged_session):
            # 1. 发送策略开仓请求
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
            data = {
                "symbol": trader_ordersend["symbol"],
                "placedType": 0,
                "remark": class_random_str,
                "intervalTime": 0,
                "type": 0,
                "totalNum": trader_ordersend["totalNum"],
                "totalSzie": trader_ordersend["totalSzie"],
                "startSize": trader_ordersend["startSize"],
                "endSize": trader_ordersend["endSize"],
                "traderId": MT5vps_trader_id
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
                    time_field="fod.open_time",
                    time_range=1
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
                        expected_value=float(0.1),
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
                    self.verify_data(
                        actual_value=float(total),
                        expected_value=float(totalSzie),
                        op=CompareOp.EQ,
                        message="详情总手数应符合预期",
                        attachment_name="详情总手数"
                    )
                    logging.info(f"详情总手数验证通过: {total}")

                with allure.step("验证详情手数和指令手数一致"):
                    size = [record["size"] for record in db_data]
                    true_total_lots = [record["true_total_lots"] for record in db_data]
                    total_lots = [record["total_lots"] for record in db_data]
                    self.assert_list_equal_ignore_order(
                        total_lots,
                        size,
                        true_total_lots,
                        f"手数不一致: 详情手数{size}, 总手数{total_lots}, 实际总手数{true_total_lots}"
                    )
                    logger.info(f"手数一致: 详情手数{size}, 总手数{total_lots}, 实际总手数{true_total_lots}")

        @allure.title("数据库校验-策略开仓-跟单开仓指令-根据status状态发现有漏单")
        def test_dbquery_orderSend_addsalve(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 查询数据库验证是否有跟单开仓指令"):
                MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
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
                    MT5vps_trader_id
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )
            with allure.step("2. 对订单状态进行校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")
                status = db_data[0]["status"]
                assert status == 2, f"跟单失败，跟单状态status应该是2，实际是：{status}"

        @allure.title("出现漏开-redis数据和数据库的数据做比对")
        def test_dbquery_redis(self, class_random_str, var_manager, db_transaction, redis_order_data_send):
            with allure.step("1. 获取订单详情表账号数据"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                new_user = var_manager.get_variable("new_user")
                symbol = trader_ordersend["symbol"]

                sql = f"""
                           SELECT * 
                           FROM follow_order_detail 
                           WHERE symbol LIKE %s 
                             AND account = %s
                             AND comment = %s
                           """
                params = (
                    f"%{symbol}%",
                    new_user["account"],
                    class_random_str
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="create_time"
                )

            with allure.step("2. 转换Redis数据为可比较格式"):
                if not redis_order_data_send:
                    pytest.fail("Redis中未查询到订单数据")

                # 转换Redis数据为与数据库一致的格式
                MT5vps_redis_comparable_list_open = convert_redis_orders_to_comparable_list(redis_order_data_send)
                logging.info(f"转换后的Redis数据: {MT5vps_redis_comparable_list_open}")

                # 将转换后的数据存入变量管理器
                var_manager.set_runtime_variable("MT5vps_redis_comparable_list_open", MT5vps_redis_comparable_list_open)

            with allure.step("3. 比较Redis与数据库数据"):
                # 假设db_data是之前从数据库查询的结果
                if not db_data:
                    pytest.fail("数据库中未查询到订单数据")

                # 提取数据库中的关键字段（根据实际数据库表结构调整）
                db_comparable_list = [
                    {
                        "order_no": record["order_no"],  # 数据库order_no → 统一字段order_no
                        "magical": record["magical"],  # 数据库magical → 统一字段magical
                        # "size": float(record["size"]),  # 数据库size → 统一字段size
                        "open_price": float(record["open_price"]),
                        "symbol": record["symbol"]
                    }
                    for record in db_data
                ]
                logging.info(f"数据库转换后: {db_comparable_list}")
                # 比较两个列表（可根据需要调整比较逻辑）
                self.assert_expected_in_actual(
                    actual=MT5vps_redis_comparable_list_open,
                    expected=db_comparable_list,
                    # fields_to_compare=["order_no", "magical", "size", "open_price", "symbol"],
                    fields_to_compare=["order_no", "magical", "open_price", "symbol"],
                    tolerance=1e-6
                )

        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-开仓补全")
        def test_follow_repairSend(self, class_random_str, var_manager, logged_session):
            with allure.step("1. 发送开仓补全请求"):
                MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
                MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
                data = {
                    "type": 2,
                    "masterId": MT5vps_trader_id,
                    "slaveId": MT5vps_addslave_id
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

        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-修改跟单账号")
        def test_update_slave2(self, class_random_str, var_manager, logged_session, encrypted_password):
            # 1. 发送修改vps跟单账号请求,修改followOpen：0关闭  1开启
            add_Slave = var_manager.get_variable("add_Slave")
            MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
            MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
            MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
            platformId = var_manager.get_variable("platformId")
            data = {
                "traderId": MT5vps_trader_id,
                "platform": add_Slave["platform"],
                "account": MT5vps_user_accounts_1,
                "password": encrypted_password,
                "remark": "",
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
                "fixedComment": "",
                "commentType": 2,
                "digits": 0,
                "cfd": "@",
                "forex": "",
                "abRemark": "",
                "id": MT5vps_addslave_id,
                "platformType": 1,
                "platformId": platformId
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
        def test_dbquery_updateslave2(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 查询数据库验证是否修改成功"):
                MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
                sql = f"SELECT * FROM follow_trader_subscribe WHERE slave_account = %s"
                params = (MT5vps_user_accounts_1,)

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )

            with allure.step("2. 对数据进行校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")
                follow_open = db_data[0]["follow_open"]
                assert follow_open == 1, f"数据修改失败，数据follow_openy应该是1，实际是：{follow_open}"

        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-修改完之后进行开仓补全")
        def test_follow_repairSend2(self, class_random_str, var_manager, logged_session):
            with allure.step("1. 发送开仓补全请求"):
                MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
                MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
                data = {
                    "type": 2,
                    "masterId": MT5vps_trader_id,
                    "slaveId": MT5vps_addslave_id
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

                with allure.step("验证详情总手数"):
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

                with allure.step("验证详情手数和指令手数一致"):
                    size = [record["size"] for record in db_data]
                    true_total_lots = [record["true_total_lots"] for record in db_data]
                    total_lots = [record["total_lots"] for record in db_data]
                    self.assert_list_equal_ignore_order(
                        total_lots,
                        size,
                        true_total_lots,
                        f"手数不一致: 详情手数{size}, 总手数{total_lots}, 实际总手数{true_total_lots}"
                    )
                    logger.info(f"手数一致: 详情手数{size}, 总手数{total_lots}, 实际总手数{true_total_lots}")

        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-策略平仓")
        def test_trader_orderclose(self, class_random_str, var_manager, logged_session, db_transaction):
            # 1. 发送全平订单平仓请求
            MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
            new_user = var_manager.get_variable("new_user")
            data = {
                "isCloseAll": 1,
                "intervalTime": 0,
                "traderId": MT5vps_trader_id,
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

    @allure.story("场景2：VPS策略下单-漏平")
    @allure.description("""
    ### 用例说明
    - 前置条件：有vps策略和vps跟单
    - 操作步骤：
      1. 修改vps跟单账号平仓-关闭
      2. 进行开仓
      3. 进行平仓
      4. 跟单账号平仓失败，有漏单数据，把redis数据和MySQL数据进行校验
      5. 修改vps跟单账号平仓-开启
    - 预期结果：vps跟单账号平仓-关闭，有漏单数据
    """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    class TestLeakagelevel(APITestBase):
        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-修改跟单账号（漏平）")
        def test_update_slave(self, class_random_str, var_manager, logged_session, encrypted_password):
            # 1. 发送修改vps跟单账号请求,修改followClose：0关闭  1开启
            add_Slave = var_manager.get_variable("add_Slave")
            MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
            MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
            platformId = var_manager.get_variable("platformId")
            MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
            data = {
                "traderId": MT5vps_trader_id,
                "platform": add_Slave["platform"],
                "account": MT5vps_user_accounts_1,
                "password": encrypted_password,
                "remark": "",
                "followDirection": 0,
                "followMode": 1,
                "remainder": 0,
                "followParam": 1,
                "placedType": 0,
                "templateId": 1,
                "followStatus": 1,
                "followOpen": 1,
                "followClose": 0,
                "followRep": 0,
                "fixedComment": "",
                "commentType": 2,
                "digits": 0,
                "cfd": "",
                "forex": "",
                "abRemark": "",
                "platformType": 1,
                "id": MT5vps_addslave_id,
                "platformId": platformId
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
        def test_dbquery_updateslave(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 查询数据库验证是否修改成功"):
                MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
                sql = f"SELECT * FROM follow_trader_subscribe WHERE slave_account = %s"
                params = (MT5vps_user_accounts_1,)

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                )

            with allure.step("2. 对数据进行校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                follow_close = db_data[0]["follow_close"]
                assert follow_close == 0, f"数据修改失败follow_close数据应该是0，实际是：{follow_close}"

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
                "intervalTime": 0,
                "type": 0,
                "totalNum": trader_ordersend["totalNum"],
                "totalSzie": trader_ordersend["totalSzie"],
                "startSize": trader_ordersend["startSize"],
                "endSize": trader_ordersend["endSize"],
                "traderId": MT5vps_trader_id
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

        # @pytest.mark.skipif(True, reason=SKIP_REASON)
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
                        fod.open_time,
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
                        expected_value=float(0.1),
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

                with allure.step("验证指令总手数"):
                    true_total_lots = db_data[0]["true_total_lots"]
                    totalSzie = trader_ordersend["totalSzie"]
                    self.verify_data(
                        actual_value=float(true_total_lots),
                        expected_value=float(totalSzie),
                        op=CompareOp.EQ,
                        message="指令总手数应符合预期",
                        attachment_name="指令总手数详情"
                    )
                    logging.info(f"指令总手数验证通过: {true_total_lots}")

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

        # @pytest.mark.skipif(True, reason=SKIP_REASON)
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
                        fod.open_time,
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

                with allure.step("验证详情手数和指令手数一致"):
                    size = [record["size"] for record in db_data]
                    true_total_lots = [record["true_total_lots"] for record in db_data]
                    total_lots = [record["total_lots"] for record in db_data]
                    self.assert_list_equal_ignore_order(
                        total_lots,
                        size,
                        true_total_lots,
                        f"手数不一致: 详情手数{size}, 总手数{total_lots}, 实际总手数{true_total_lots}"
                    )
                    logger.info(f"手数一致: 详情手数{size}, 总手数{total_lots}, 实际总手数{true_total_lots}")

        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-策略平仓-出现漏平")
        def test_trader_orderclose(self, class_random_str, var_manager, logged_session):
            # 1. 发送全平订单平仓请求
            MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
            new_user = var_manager.get_variable("new_user")
            data = {
                "isCloseAll": 1,
                "intervalTime": 0,
                "traderId": MT5vps_trader_id,
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
                        fod.close_time,
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

        @allure.title("数据库校验-策略平仓-检查平仓订单是否出现漏平")
        def test_dbquery_addsalve_clsesdetail(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
                symbol = trader_ordersend["symbol"]

                sql = f"""
                        SELECT * 
                        FROM follow_order_detail 
                        WHERE symbol LIKE %s 
                          AND account = %s
                          AND comment = %s
                        """
                params = (
                    f"%{symbol}%",
                    MT5vps_user_accounts_1,
                    class_random_str
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="create_time"
                )
            with allure.step("2. 校验数据"):
                # close_status = db_data[0]["close_status"]
                # logging.info(f"出现漏平，平仓状态应该是0，实际是：{close_status}")
                # assert close_status == 0, f"出现漏平，平仓状态应该是0，实际是：{close_status}"

                close_remark = db_data[0]["close_remark"]
                logging.info(f"出现漏平，平仓异常信息应该是:未开通平仓状态，实际是：{close_remark}")
                assert close_remark == "未开通平仓状态", f"出现漏平，平仓异常信息应该是未开通平仓状态，实际是：{close_remark}"

        @allure.title("出现漏平-redis数据和数据库的数据做比对")
        def test_dbquery_redis(self, class_random_str, var_manager, db_transaction, redis_order_data_close):
            with allure.step("1. 获取订单详情表账号数据"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                new_user = var_manager.get_variable("new_user")
                symbol = trader_ordersend["symbol"]

                sql = f"""
                           SELECT * 
                           FROM follow_order_detail 
                           WHERE symbol LIKE %s 
                             AND account = %s
                             AND comment = %s
                           """
                params = (
                    f"%{symbol}%",
                    new_user["account"],
                    class_random_str
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="create_time",
                    time_range=1
                )

            with allure.step("2. 转换Redis数据为可比较格式"):
                if not redis_order_data_close:
                    pytest.fail("Redis中未查询到订单数据")

                # 转换Redis数据为与数据库一致的格式
                MT5vps_redis_comparable_list_level = convert_redis_orders_to_comparable_list(redis_order_data_close)
                logging.info(f"转换后的Redis数据: {MT5vps_redis_comparable_list_level}")

                # 将转换后的数据存入变量管理器
                var_manager.set_runtime_variable("MT5vps_redis_comparable_list_level",
                                                 MT5vps_redis_comparable_list_level)

            with allure.step("3. 比较Redis与数据库数据"):
                # 假设db_data是之前从数据库查询的结果
                if not db_data:
                    pytest.fail("数据库中未查询到订单数据")

                # 提取数据库中的关键字段（根据实际数据库表结构调整）
                db_comparable_list = [
                    {
                        "order_no": record["order_no"],  # 数据库order_no → 统一字段order_no
                        "magical": record["magical"],  # 数据库magical → 统一字段magical
                        # "size": float(record["size"]),  # 数据库size → 统一字段size
                        "open_price": float(record["open_price"]),
                        "symbol": record["symbol"]
                    }
                    for record in db_data
                ]
                logging.info(f"数据库转换后: {db_comparable_list}")
                # 比较两个列表（可根据需要调整比较逻辑）
                self.assert_expected_in_actual(
                    actual=MT5vps_redis_comparable_list_level,
                    expected=db_comparable_list,
                    # fields_to_compare=["order_no", "magical", "size", "open_price", "symbol"],
                    fields_to_compare=["order_no", "magical", "open_price", "symbol"],
                    tolerance=1e-6
                )

        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-修改跟单账号（漏平）")
        def test_update_slave2(self, class_random_str, var_manager, logged_session, encrypted_password):
            # 1. 发送修改vps跟单账号请求,修改followClose：0关闭  1开启
            add_Slave = var_manager.get_variable("add_Slave")
            MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
            MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
            MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
            platformId = var_manager.get_variable("platformId")
            data = {
                "traderId": MT5vps_trader_id,
                "platform": add_Slave["platform"],
                "account": MT5vps_user_accounts_1,
                "password": encrypted_password,
                "remark": "",
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
                "fixedComment": "",
                "commentType": 2,
                "digits": 0,
                "cfd": "",
                "forex": "",
                "abRemark": "",
                "platformType": 1,
                "id": MT5vps_addslave_id,
                "platformId": platformId
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
        def test_dbquery_updateslave2(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 查询数据库验证是否修改成功"):
                MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
                sql = f"SELECT * FROM follow_trader_subscribe WHERE slave_account = %s"
                params = (MT5vps_user_accounts_1,)

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )

            with allure.step("2. 对数据进行校验"):
                if not db_data:
                    pytest.fail("数据库查询结果为空，订单可能没有入库")

                follow_close = db_data[0]["follow_close"]
                assert follow_close == 1, f"数据修改失败follow_close数据应该是1，实际是：{follow_close}"

        @allure.title("跟单软件看板-VPS数据-修改完之后进行平仓补全")
        @pytest.mark.url("vps")
        def test_follow_repairSend(self, class_random_str, var_manager, logged_session):
            with allure.step("1. 发送平仓补全请求"):
                MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
                MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
                data = {
                    "type": 2,
                    "masterId": MT5vps_trader_id,
                    "slaveId": MT5vps_addslave_id
                }
                response = self.send_post_request(
                    logged_session,
                    '/subcontrol/follow/repairSend',
                    json_data=data
                )

            with allure.step("2. 关仓成功"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

        @allure.title("跟单软件看板-VPS数据-跟单账号自己平仓")
        @pytest.mark.url("vps")
        def test_follow_orderClose(self, class_random_str, var_manager, logged_session):
            with allure.step("1. 发送平仓请求"):
                MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
                MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
                data = {
                    "traderId": MT5vps_addslave_id,
                    "account": MT5vps_user_accounts_1,
                    "ifAccount": "true",
                    "isCloseAll": 1
                }
                response = self.send_post_request(
                    logged_session,
                    '/subcontrol/trader/orderClose',
                    json_data=data
                )

            with allure.step("2. 平仓成功"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

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
                        fod.close_time,
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

    @allure.story("场景3：VPS策略下单-关闭策略跟单状态")
    @allure.description("""
    ### 用例说明
    - 前置条件：有vps策略和vps跟单
    - 操作步骤：
      1. 修改vps策略跟单状态为关闭
      2. 进行开仓
      3. 跟单账号跟单失败，有漏单数据，把redis数据和MySQL数据进行校验
      4. 修改vps策略跟单状态为开启
      5. 进行补单操作，然后平仓
    - 预期结果：vps策略跟单状态为关闭，有漏单数据
    """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    class TestLeakageopen_addstatus(APITestBase):
        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-修改策略账号信息")
        def test_subcontrol_trader(self, class_random_str, var_manager, logged_session, encrypted_password):
            # 1. 发送修改vps策略的请求，修改followStatus：0关闭 1开启
            with allure.step("1.发送修改vps策略的请求"):
                new_user = var_manager.get_variable("new_user")
                MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
                platformId = var_manager.get_variable("platformId")
                json_data = {
                    "id": MT5vps_trader_id,
                    "type": 0,
                    "account": new_user["account"],
                    "password": encrypted_password,
                    "platform": new_user["platform"],
                    "platformType": 1,
                    "remark": "",
                    "platformId": platformId,
                    "templateId": 1,
                    "followStatus": 0,
                    "cfd": "",
                    "forex": "",
                    "followOrderRemark": 1,
                    "fixedComment": "",
                    "commentType": "",
                    "digits": 0
                }
                response = self.send_put_request(
                    logged_session,
                    '/subcontrol/trader',
                    json_data=json_data,
                )

            with allure.step("2. 验证响应状态码和内容"):
                # 2. 验证响应状态码和内容
                self.assert_response_status(
                    response,
                    200,
                    "发送修改vps策略的请求失败"
                )
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

        @allure.title("数据库校验-VPS数据-修改策略账号是否成功")
        def test_dbquery_updateslave(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 查询数据库验证是否修改成功"):
                new_user = var_manager.get_variable("new_user")
                sql = f"SELECT * FROM follow_trader WHERE account = %s"
                params = (new_user["account"],)

                db_data = self.query_database(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )
            with allure.step("2. 对数据进行校验"):
                follow_status = db_data[0]["follow_status"]
                assert follow_status == 0, f"follow_status的状态应该是0，实际是：{follow_status}"

        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-策略开仓-出现漏单")
        def test_trader_orderSend(self, class_random_str, var_manager, logged_session):
            # 1. 发送策略开仓请求
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
            data = {
                "symbol": trader_ordersend["symbol"],
                "placedType": 0,
                "remark": class_random_str,
                "intervalTime": 0,
                "type": 0,
                "totalNum": trader_ordersend["totalNum"],
                "totalSzie": trader_ordersend["totalSzie"],
                "startSize": trader_ordersend["startSize"],
                "endSize": trader_ordersend["endSize"],
                "traderId": MT5vps_trader_id
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

        @allure.title("出现漏开-redis数据和数据库的数据做比对")
        def test_dbquery_redis(self, class_random_str, var_manager, db_transaction, redis_order_data_send):
            with allure.step("1. 获取订单详情表账号数据"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                new_user = var_manager.get_variable("new_user")
                symbol = trader_ordersend["symbol"]

                sql = f"""
                           SELECT * 
                           FROM follow_order_detail 
                           WHERE symbol LIKE %s 
                             AND account = %s
                             AND comment = %s
                           """
                params = (
                    f"%{symbol}%",
                    new_user["account"],
                    class_random_str
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="create_time"
                )

            with allure.step("2. 转换Redis数据为可比较格式"):
                if not redis_order_data_send:
                    pytest.fail("Redis中未查询到订单数据")

                # 转换Redis数据为与数据库一致的格式
                MT5vps_redis_comparable_list_open = convert_redis_orders_to_comparable_list(redis_order_data_send)
                logging.info(f"转换后的Redis数据: {MT5vps_redis_comparable_list_open}")

                # 将转换后的数据存入变量管理器
                var_manager.set_runtime_variable("MT5vps_redis_comparable_list_open", MT5vps_redis_comparable_list_open)

            with allure.step("3. 比较Redis与数据库数据"):
                # 假设db_data是之前从数据库查询的结果
                if not db_data:
                    pytest.fail("数据库中未查询到订单数据")

                # 提取数据库中的关键字段（根据实际数据库表结构调整）
                db_comparable_list = [
                    {
                        "order_no": record["order_no"],  # 数据库order_no → 统一字段order_no
                        "magical": record["magical"],  # 数据库magical → 统一字段magical
                        # "size": float(record["size"]),  # 数据库size → 统一字段size
                        "open_price": float(record["open_price"]),
                        "symbol": record["symbol"]
                    }
                    for record in db_data
                ]
                logging.info(f"数据库转换后: {db_comparable_list}")
                # 比较两个列表（可根据需要调整比较逻辑）
                self.assert_expected_in_actual(
                    actual=MT5vps_redis_comparable_list_open,
                    expected=db_comparable_list,
                    # fields_to_compare=["order_no", "magical", "size", "open_price", "symbol"],
                    fields_to_compare=["order_no", "magical", "open_price", "symbol"],
                    tolerance=1e-6
                )

        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-开仓补全")
        def test_follow_repairSend(self, class_random_str, var_manager, logged_session):
            with allure.step("1. 发送开仓补全请求"):
                MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
                MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
                data = {
                    "type": 2,
                    "masterId": MT5vps_trader_id,
                    "slaveId": MT5vps_addslave_id
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

        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-修改策略账号信息")
        def test_subcontrol_trader2(self, class_random_str, var_manager, logged_session, encrypted_password):
            # 1. 发送修改vps策略的请求，修改followStatus：0关闭 1开启
            with allure.step("1.发送修改vps策略的请求"):
                new_user = var_manager.get_variable("new_user")
                MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
                platformId = var_manager.get_variable("platformId")
                json_data = {
                    "id": MT5vps_trader_id,
                    "type": 0,
                    "account": new_user["account"],
                    "password": encrypted_password,
                    "platform": new_user["platform"],
                    "remark": "",
                    "platformId": platformId,
                    "templateId": 1,
                    "followStatus": 1,
                    "cfd": "",
                    "forex": "",
                    "followOrderRemark": 1,
                    "fixedComment": "",
                    "commentType": "",
                    "digits": 0,
                    "platformType": 1
                }

                response = self.send_put_request(
                    logged_session,
                    '/subcontrol/trader',
                    json_data=json_data,
                )

            with allure.step("2. 验证响应状态码和内容"):
                # 2. 验证响应状态码和内容
                self.assert_response_status(
                    response,
                    200,
                    "发送修改vps策略的请求失败"
                )
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

        @allure.title("数据库校验-VPS数据-修改策略账号是否成功")
        def test_dbquery_updateslave2(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 查询数据库验证是否修改成功"):
                new_user = var_manager.get_variable("new_user")
                sql = f"SELECT * FROM follow_trader WHERE account = %s"
                params = (new_user["account"],)

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )
            with allure.step("2. 对数据进行校验"):
                follow_status = db_data[0]["follow_status"]
                assert follow_status == 1, f"follow_status的状态应该是1，实际是：{follow_status}"

        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-修改完之后进行开仓补全")
        def test_follow_repairSend2(self, class_random_str, var_manager, logged_session):
            with allure.step("1. 发送开仓补全请求"):
                MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
                MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
                data = {
                    "type": 2,
                    "masterId": MT5vps_trader_id,
                    "slaveId": MT5vps_addslave_id
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

        @allure.title("数据库校验-策略开仓-跟单指令及订单详情数据检查")
        def test_dbquery_addsalve_orderSend(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
                MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
                sql = f"""
                    SELECT * FROM follow_order_detail
                    WHERE account = %s
                        AND trader_id = %s
                        AND comment = %s
                        """
                params = (
                    MT5vps_user_accounts_1,
                    MT5vps_addslave_id,
                    class_random_str
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="create_time"
                )
            with allure.step("2. 数据校验"):
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

        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-策略平仓")
        def test_trader_orderclose(self, class_random_str, var_manager, logged_session, db_transaction):
            # 1. 发送全平订单平仓请求
            MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
            new_user = var_manager.get_variable("new_user")
            data = {
                "isCloseAll": 1,
                "intervalTime": 0,
                "traderId": MT5vps_trader_id,
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
