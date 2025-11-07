import allure
import logging
import pytest
import time
from lingkuan_1029.conftest import var_manager
from lingkuan_1029.commons.api_base import *
from lingkuan_1029.commons.redis_utils import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("云策略-策略账号交易下单-漏单场景")
class TestcloudTrader_openandlevel:
    @allure.story("场景5：云策略列表-云策略复制下单-漏开")
    @allure.description("""
    ### 用例说明
    - 前置条件：有云策略和云跟单
    - 操作步骤：
      1. 修改云跟单账号开仓-关闭
      2. 进行开仓
      3. 跟单账号开仓失败，有漏单数据，把redis数据和MySQL数据进行校验
      4. 修改云跟单账号开仓-开启
      5. 进行补单操作，然后平仓
    - 预期结果：云跟单账号开仓-关闭，有漏单数据
    """)
    @pytest.mark.flaky(reruns=3, reruns_delay=3)
    @pytest.mark.usefixtures("class_random_str")
    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    class TestcloudTrader_open5(APITestBase):
        @allure.title("云策略-云策略列表-修改云跟单")
        @pytest.mark.flaky(reruns=3, reruns_delay=3)
        def test_cloudTrader_cloudBatchUpdate(self, class_random_str, var_manager, logged_session):
            with allure.step("1. 发送修改跟单策略账号请求，将followOpen改为0，关闭开仓"):
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
                data = [
                    {
                        "traderList": [
                            cloudTrader_traderList_4
                        ],
                        "cloudId": cloudMaster_id,
                        "masterId": cloudTrader_traderList_2,
                        "masterAccount": cloudTrader_user_accounts_2,
                        "platformType": 0,
                        "followDirection": 0,
                        "followMode": 1,
                        "followParam": 1,
                        "remainder": 0,
                        "placedType": 0,
                        "templateId": 1,
                        "followStatus": 1,
                        "followOpen": 0,
                        "followClose": 1,
                        "fixedComment": "",
                        "commentType": None,
                        "digits": 0,
                        "followTraderIds": [],
                        "sort": 100,
                        "remark": "",
                        "cfd": "",
                        "forex": ""
                    }
                ]

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudBatchUpdate',
                    json_data=data
                )

            with allure.step("2. 验证JSON返回内容"):
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

        @allure.title("数据库校验-云策略列表-修改云跟单账号是否成功")
        def test_dbcloudTrader_cloudBatchUpdate(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 查询数据库验证是否修改成功"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                sql = f"SELECT * FROM follow_cloud_trader WHERE account = %s and cloud_id = %s"
                params = (cloudTrader_user_accounts_4, cloudMaster_id,)

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )
            with allure.step("2. 对数据进行校验"):
                follow_open = db_data[0]["follow_open"]
                assert follow_open == 0, f"follow_open的状态应该是0，实际是：{follow_open}"

        @allure.title("云策略列表-云策略账号复制下单-出现漏开")
        def test_bargain_masOrderSend(self, class_random_str, logged_session, var_manager):
            """执行云策略复制下单操作并验证请求结果"""
            with allure.step("1.发送复制下单请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")

                request_data = {
                    "id": cloudMaster_id,
                    "type": 0,
                    "tradeType": 1,
                    "intervalTime": 100,
                    "cloudTraderId": [cloudTrader_traderList_2],
                    "symbol": "XAUUSD",
                    "placedType": 0,
                    "startSize": "0.10",
                    "endSize": "1.00",
                    "totalNum": "3",
                    "totalSzie": "1.00",
                    "remark": class_random_str
                }

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudOrderSend',
                    json_data=request_data
                )

            with allure.step("2.验证响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

        @allure.title("数据库校验-云策略列表-根据remark发现有漏单")
        def test_dbquery_orderSend_addsalve(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 查询数据库验证是否有跟单开仓指令"):
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")

                sql = f"""
                    SELECT 
                        fod.send_no,
                        fod.comment,
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
                    time_field="foi.create_time",
                    time_range=1
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
        def test_dbquery_redis(self, class_random_str, var_manager, db_transaction, redis_cloudTrader_data_send):
            with allure.step("1. 获取订单详情表账号数据"):
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
                cloudOrderSend = var_manager.get_variable("cloudOrderSend")
                symbol = cloudOrderSend["symbol"]

                sql = f"""
                       SELECT * 
                       FROM follow_order_detail 
                       WHERE symbol LIKE %s 
                         AND account = %s
                         AND comment = %s
                       """
                params = (
                    f"%{symbol}%",
                    cloudTrader_user_accounts_2,
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
                if not redis_cloudTrader_data_send:
                    pytest.fail("Redis中未查询到订单数据")

                # 转换Redis数据为与数据库一致的格式
                cloudtrader_redis_comparable_openlist = convert_redis_orders_to_comparable_list(
                    redis_cloudTrader_data_send)
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
                    tolerance=1e-6
                )

        @allure.title("云策略-云策略列表-修改云跟单")
        def test_cloudTrader_cloudBatchUpdate2(self, class_random_str, var_manager, logged_session):
            with allure.step("1. 发送修改跟单策略账号请求，将followOpen改为1，开启开仓"):
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
                data = [
                    {
                        "traderList": [
                            cloudTrader_traderList_4
                        ],
                        "cloudId": cloudMaster_id,
                        "masterId": cloudTrader_traderList_2,
                        "masterAccount": cloudTrader_user_accounts_2,
                        "platformType": 0,
                        "followDirection": 0,
                        "followMode": 1,
                        "followParam": 1,
                        "remainder": 0,
                        "placedType": 0,
                        "templateId": 1,
                        "followStatus": 1,
                        "followOpen": 1,
                        "followClose": 1,
                        "fixedComment": "",
                        "commentType": None,
                        "digits": 0,
                        "followTraderIds": [],
                        "sort": 100,
                        "remark": "",
                        "cfd": "",
                        "forex": ""
                    }
                ]

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudBatchUpdate',
                    json_data=data
                )

            with allure.step("2. 验证JSON返回内容"):
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

        @allure.title("数据库校验-云策略列表-修改云跟单账号是否成功")
        def test_dbcloudTrader_cloudBatchUpdate2(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 查询数据库验证是否修改成功"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                sql = f"SELECT * FROM follow_cloud_trader WHERE account = %s and cloud_id = %s"
                params = (cloudTrader_user_accounts_4, cloudMaster_id,)

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )
            with allure.step("2. 对数据进行校验"):
                follow_open = db_data[0]["follow_open"]
                assert follow_open == 1, f"follow_open的状态应该是1，实际是：{follow_open}"

        @allure.title("云策略-云策略列表-修改完之后进行开仓补全")
        def test_follow_repairSend(self, class_random_str, var_manager, logged_session):
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

        @allure.title("数据库校验-云策略列表-指令及订单详情数据检查")
        def test_dbcloudTrader_cloudOrderSend(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
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
                    time_range=1
                )
            with allure.step("2. 数据校验"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

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

        @allure.title("云策略列表-平仓")
        def test_cloudTrader_cloudOrderClose(self, class_random_str, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("1.发送复制下单平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")

                request_data = {
                    "isCloseAll": 1,
                    "intervalTime": 100,
                    "id": f"{cloudMaster_id}",
                    "cloudTraderId": [cloudTrader_traderList_2]
                }

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudOrderClose',
                    json_data=request_data
                )

            with allure.step("2.验证复制平仓响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制平仓响应msg字段应为success"
                )

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库校验-交易平仓-指令及订单详情数据检查")
        def test_dbcloudTrader_cloudOrderClose(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
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
                               AND fod.comment = %s
                               """
                params = (
                    '1',
                    cloudTrader_user_accounts_4,
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
                    pytest.fail("数据库查询结果为空，无法提取数据")

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

    @allure.story("场景6：云策略列表-云策略复制下单-漏平")
    @allure.description("""
    ### 用例说明
    - 前置条件：有云策略和云跟单
    - 操作步骤：
      1. 修改云跟单账号平仓-关闭
      2. 进行开仓
      3. 进行平仓
      4. 跟单账号平仓失败，有漏单数据，把redis数据和MySQL数据进行校验
      5. 修改云跟单账号平仓-开启
    - 预期结果：云跟单账号平仓-关闭，有漏单数据
    """)
    @pytest.mark.flaky(reruns=3, reruns_delay=3)
    @pytest.mark.usefixtures("class_random_str")
    # @pytest.mark.skipif(True, reason=SKIP_REASON)
    class TestcloudTrader_level6(APITestBase):
        @allure.title("云策略-云策略列表-修改云跟单")
        def test_cloudTrader_cloudBatchUpdate(self, class_random_str, var_manager, logged_session):
            with allure.step("1. 发送修改跟单策略账号请求，将followClose改为0，关闭平仓"):
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
                data = [
                    {
                        "traderList": [
                            cloudTrader_traderList_4
                        ],
                        "cloudId": cloudMaster_id,
                        "masterId": cloudTrader_traderList_2,
                        "masterAccount": cloudTrader_user_accounts_2,
                        "platformType": 0,
                        "followDirection": 0,
                        "followMode": 1,
                        "followParam": 1,
                        "remainder": 0,
                        "placedType": 0,
                        "templateId": 1,
                        "followStatus": 1,
                        "followOpen": 1,
                        "followClose": 0,
                        "fixedComment": "",
                        "commentType": None,
                        "digits": 0,
                        "followTraderIds": [],
                        "sort": 100,
                        "remark": "",
                        "cfd": "",
                        "forex": ""
                    }
                ]

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudBatchUpdate',
                    json_data=data
                )

            with allure.step("2. 验证JSON返回内容"):
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

        @allure.title("数据库校验-云策略列表-修改云跟单账号是否成功")
        def test_dbcloudTrader_cloudBatchUpdate(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 查询数据库验证是否修改成功"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                sql = f"SELECT * FROM follow_cloud_trader WHERE account = %s and cloud_id = %s"
                params = (cloudTrader_user_accounts_4, cloudMaster_id,)

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )
            with allure.step("2. 对数据进行校验"):
                follow_close = db_data[0]["follow_close"]
                assert follow_close == 0, f"follow_close的状态应该是0，实际是：{follow_close}"

        @allure.title("云策略列表-云策略账号复制下单")
        def test_bargain_masOrderSend(self, class_random_str, logged_session, var_manager):
            """执行云策略复制下单操作并验证请求结果"""
            with allure.step("1.发送复制下单请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")

                request_data = {
                    "id": cloudMaster_id,
                    "type": 0,
                    "tradeType": 1,
                    "intervalTime": 100,
                    "cloudTraderId": [cloudTrader_traderList_2],
                    "symbol": "XAUUSD",
                    "placedType": 0,
                    "startSize": "0.10",
                    "endSize": "1.00",
                    "totalNum": "3",
                    "totalSzie": "1.00",
                    "remark": class_random_str
                }

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudOrderSend',
                    json_data=request_data
                )

            with allure.step("2.验证响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

        @allure.title("数据库校验-云策略列表-指令及订单详情数据检查")
        def test_dbcloudTrader_cloudOrderSend(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
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
                    cloudTrader_user_accounts_4,
                    class_random_str
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="foi.create_time",
                )
            with allure.step("2. 数据校验"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

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

        @allure.title("云策略列表-平仓-出现漏平")
        def test_cloudTrader_cloudOrderClose(self, class_random_str, logged_session, var_manager):
            """执行复制下单的平仓操作并验证结果"""
            with allure.step("1.发送复制下单平仓请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")

                request_data = {
                    "isCloseAll": 1,
                    "intervalTime": 100,
                    "id": f"{cloudMaster_id}",
                    "cloudTraderId": [cloudTrader_traderList_2]
                }

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudOrderClose',
                    json_data=request_data
                )

            with allure.step("2.验证复制平仓响应结果"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "复制平仓响应msg字段应为success"
                )

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库校验-策略平仓-检查平仓订单是否出现漏平")
        def test_dbquery_addsalve_clsesdetail(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")

                sql = f"""
                       SELECT 
                           fod.send_no,
                           fod.comment,
                           fod.magical,
                           fod.remark,
                           fod.symbol,
                           fod.close_no,
                           fod.close_time,
                           fod.close_status,
                           fod.close_remark,
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
                           foi.order_no = fod.close_no COLLATE utf8mb4_0900_ai_ci
                       WHERE foi.operation_type = %s
                           AND foi.cloud_account = %s
                           AND fod.comment = %s
                                               """
                params = (
                    '1',
                    cloudTrader_user_accounts_2,
                    class_random_str
                )

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    time_field="foi.create_time"
                )
            with allure.step("2. 校验数据"):
                # close_status = db_data[0]["close_status"]
                # logging.info(f"出现漏平，平仓状态应该是0，实际是：{close_status}")
                # assert close_status == 0, f"出现漏平，平仓状态应该是0，实际是：{close_status}"

                close_remark = db_data[0]["close_remark"]
                logging.info(
                    f"出现漏平，平仓异常信息应该是:平仓异常: 未开通平仓状态/未开通平仓状态，实际是：{close_remark}")
                assert close_remark == "平仓异常: 未开通平仓状态" or close_remark == "未开通平仓状态", f"出现漏平，平仓异常信息应该是:平仓异常: 未开通平仓状态/未开通平仓状态，实际是：{close_remark}"

            with allure.step("3. 提取数据"):
                cloudTrader_master_order_level = [record["master_order"] for record in db_data]
                var_manager.set_runtime_variable("cloudTrader_master_order_level", cloudTrader_master_order_level)

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("出现漏平-redis数据和数据库的数据做比对")
        def test_dbquery_redis(self, class_random_str, var_manager, db_transaction, redis_cloudTrader_data_close):
            with allure.step("1. 获取订单详情表账号数据"):
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
                cloudOrderSend = var_manager.get_variable("cloudOrderSend")
                symbol = cloudOrderSend["symbol"]

                sql = f"""
                          SELECT * 
                          FROM follow_order_detail 
                          WHERE symbol LIKE %s 
                            AND account = %s
                            AND comment = %s
                          """
                params = (
                    f"%{symbol}%",
                    cloudTrader_user_accounts_2,
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
                if not redis_cloudTrader_data_close:
                    pytest.fail("Redis中未查询到订单数据")

                # 转换Redis数据为与数据库一致的格式
                cloudtrader_redis_comparable_levellist = convert_redis_orders_to_comparable_list(
                    redis_cloudTrader_data_close)
                logging.info(f"转换后的Redis数据: {cloudtrader_redis_comparable_levellist}")

                # 将转换后的数据存入变量管理器
                var_manager.set_runtime_variable("cloudtrader_redis_comparable_levellist",
                                                 cloudtrader_redis_comparable_levellist)

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
                    actual=cloudtrader_redis_comparable_levellist,
                    expected=db_comparable_list,
                    fields_to_compare=["order_no", "magical", "size", "open_price", "symbol"],
                    tolerance=1e-6
                )

        @allure.title("云策略-云策略列表-修改云跟单")
        def test_cloudTrader_cloudBatchUpdate2(self, class_random_str, var_manager, logged_session):
            with allure.step("1. 发送修改跟单策略账号请求，将followClose改为1，开启平仓"):
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
                data = [
                    {
                        "traderList": [
                            cloudTrader_traderList_4
                        ],
                        "cloudId": cloudMaster_id,
                        "masterId": cloudTrader_traderList_2,
                        "masterAccount": cloudTrader_user_accounts_2,
                        "platformType": 0,
                        "followDirection": 0,
                        "followMode": 1,
                        "followParam": 1,
                        "remainder": 0,
                        "placedType": 0,
                        "templateId": 1,
                        "followStatus": 1,
                        "followOpen": 1,
                        "followClose": 1,
                        "fixedComment": "",
                        "commentType": None,
                        "digits": 0,
                        "followTraderIds": [],
                        "sort": 100,
                        "remark": "",
                        "cfd": "",
                        "forex": ""
                    }
                ]

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/cloudTrader/cloudBatchUpdate',
                    json_data=data
                )

            with allure.step("2. 验证JSON返回内容"):
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

        @allure.title("数据库校验-云策略列表-修改云跟单账号是否成功")
        def test_dbcloudTrader_cloudBatchUpdate2(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 查询数据库验证是否修改成功"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                sql = f"SELECT * FROM follow_cloud_trader WHERE account = %s and cloud_id = %s"
                params = (cloudTrader_user_accounts_4, cloudMaster_id,)

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )
            with allure.step("2. 对数据进行校验"):
                follow_close = db_data[0]["follow_close"]
                assert follow_close == 1, f"follow_close的状态应该是1，实际是：{follow_close}"

        @allure.title("云策略-云策略列表-修改完之后进行平仓补全")
        def test_follow_repairSend(self, class_random_str, var_manager, logged_session):
            with allure.step("1. 发送平仓补全请求"):
                cloudMaster_id = var_manager.get_variable("cloudMaster_id")
                cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")
                cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
                cloudTrader_master_order_level = var_manager.get_variable("cloudTrader_master_order_level")
                for cloudTrader_master_order_level in cloudTrader_master_order_level:
                    data = [
                        {
                            "cloudId": cloudMaster_id,
                            "repairType": 1,
                            "masterId": cloudTrader_traderList_2,
                            "slaveId": cloudTrader_traderList_4,
                            "masterOrder": cloudTrader_master_order_level
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

        @allure.title("云策略-云策略列表-云跟单账号自己平仓")
        def test_cloudTrader_cloudOrderClose2(self, class_random_str, logged_session, var_manager):
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
        def test_dbcloudTrader_cloudOrderClose(self, class_random_str, var_manager, db_transaction):
            with allure.step("1. 获取订单详情表账号数据"):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
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
                               foi.master_order = fod.magical COLLATE utf8mb4_0900_ai_ci
                           WHERE foi.operation_type = %s
                               AND fod.account = %s
                               AND fod.comment = %s
                               """
                params = (
                    '1',
                    cloudTrader_user_accounts_4,
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
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

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
