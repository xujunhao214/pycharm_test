# lingkuan_801UAT/tests/test_云策略_ordersend.py
import allure
import logging
import pytest
import time
import math
from lingkuan_801UAT.VAR.VAR import *
from lingkuan_801UAT.conftest import var_manager
from lingkuan_801UAT.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("交易下单-manager账号云策略复制下单-漏平")
class TestcloudTrader_managerlevel(APITestBase):
    # ---------------------------
    # 云策略-云策略列表-修改云策略跟单
    # ---------------------------
    @allure.title("云策略-云策略列表-修改云策略跟单")
    def test_cloudTrader_cloudBatchUpdate(self, var_manager, logged_session, db_transaction):
        with allure.step("1. 发送修改跟单策略账号请求，将followClose改为0，关闭平仓"):
            cloudMaster_id = var_manager.get_variable("cloudMaster_id")
            traderList_cloudTrader_4 = var_manager.get_variable("traderList_cloudTrader_4")
            traderList_cloudTrader_3 = var_manager.get_variable("traderList_cloudTrader_3")
            user_accounts_cloudTrader_3 = var_manager.get_variable("user_accounts_cloudTrader_3")
            data = [
                {
                    "traderList": [
                        traderList_cloudTrader_4
                    ],
                    "cloudId": cloudMaster_id,
                    "masterId": traderList_cloudTrader_3,
                    "masterAccount": user_accounts_cloudTrader_3,
                    "followDirection": 0,
                    "followMode": 1,
                    "followParam": 1,
                    "remainder": 0,
                    "placedType": 0,
                    "templateId": 1,
                    "followStatus": 1,
                    "followOpen": 1,
                    "followClose": 0,
                    "fixedComment": "ceshi",
                    "commentType": "",
                    "digits": 0,
                    "followTraderIds": [],
                    "sort": "100"
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
                "修改云跟单账号失败"
            )

            # 3. 验证JSON返回内容
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

    @allure.title("数据库校验-云策略列表-修改云策略跟单账号是否成功")
    def test_dbcloudTrader_cloudBatchUpdate(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否修改成功"):
            user_accounts_cloudTrader_3 = var_manager.get_variable("user_accounts_cloudTrader_3")
            sql = f"SELECT * FROM follow_cloud_trader WHERE account = %s"
            params = (user_accounts_cloudTrader_3,)

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params
            )
        with allure.step("2. 对数据进行校验"):
            follow_close = db_data[0]["follow_close"]
            assert follow_close == 0, f"follow_close的状态应该是0，实际是：{follow_close}"

    # ---------------------------
    # 账号管理-交易下单-云策略账号复制下单
    # ---------------------------
    @allure.title("账号管理-交易下单-云策略manager策略账号复制下单")
    def test_bargain_masOrderSend(self, api_session, var_manager, logged_session):
        # 1. 发送云策略复制下单请求
        global user_ids_cloudTrader_3
        cloudOrderSend = var_manager.get_variable("cloudOrderSend")
        user_ids_cloudTrader_3 = var_manager.get_variable("user_ids_cloudTrader_3")
        data = {
            "traderList": [user_ids_cloudTrader_3],
            "type": 0,
            "tradeType": 1,
            "intervalTime": 100,
            "symbol": cloudOrderSend["symbol"],
            "placedType": 0,
            "startSize": "0.10",
            "endSize": "1.00",
            "totalNum": "3",
            "totalSzie": "1.00",
            "remark": "测试数据"
        }
        response = self.send_post_request(
            api_session,
            '/bargain/masOrderSend',
            json_data=data,
            sleep_seconds=0
        )

        # 2. 判断云策略复制下单是否成功
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # ---------------------------
    # 数据库校验-交易开仓-指令及订单详情数据检查
    # ---------------------------
    @allure.title("数据库校验-交易开仓-主指令及订单详情数据检查")
    def test_dbquery_orderSend(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            user_accounts_cloudTrader_3 = var_manager.get_variable("user_accounts_cloudTrader_3")
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
                user_accounts_cloudTrader_3,
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

            # 手数范围：结束手数校验
            min_lot_size = db_data[0]["min_lot_size"]
            endsize = trader_ordersend["endSize"]
            assert math.isclose(float(endsize), float(min_lot_size), rel_tol=1e-9, abs_tol=1e-9), \
                f'手数范围：结束手数是：{endsize}，实际是：{min_lot_size}'
            logging.info(f'手数范围：结束手数是：{endsize}，实际是：{min_lot_size}')

            # 手数范围：开始手数校验
            max_lot_size = db_data[0]["max_lot_size"]
            startSize = trader_ordersend["startSize"]
            assert math.isclose(float(startSize), float(max_lot_size), rel_tol=1e-9, abs_tol=1e-9), \
                f'手数范围：开始手数是：{startSize}，实际是：{max_lot_size}'
            logging.info(f'手数范围：开始手数是：{startSize}，实际是：{max_lot_size}')

            total_orders = db_data[0]["total_orders"]
            totalNum = trader_ordersend["totalNum"]
            assert math.isclose(float(totalNum), float(total_orders), rel_tol=1e-9), \
                f'总订单数量是：{totalNum}，实际是：{total_orders}'
            logging.info(f'总订单数量是：{totalNum}，实际是：{total_orders}')

            # 下单总手数与指令表总手数校验
            total_lots = db_data[0]["total_lots"]
            totalSzie = trader_ordersend["totalSzie"]
            assert math.isclose(float(totalSzie), float(total_lots), rel_tol=1e-9, abs_tol=1e-9), \
                f'下单总手数是：{totalSzie}，实际是：{total_lots}'
            logging.info(f'下单总手数是：{totalSzie}，实际是：{total_lots}')

            # 下单总手数与订单详情总手数校验
            totalSzie = trader_ordersend["totalSzie"]
            size = [record["size"] for record in db_data]
            total = sum(size)
            assert math.isclose(float(totalSzie), float(total), rel_tol=1e-9, abs_tol=1e-9), \
                f'下单总手数是：{totalSzie},订单详情总手数是：{total}'
            logging.info(f'下单总手数是：{totalSzie},订单详情总手数是：{total}')

    @allure.title("数据库校验-交易开仓-跟单指令及订单详情数据检查")
    def test_dbcloudTrader_cloudOrderSend(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            user_accounts_cloudTrader_4 = var_manager.get_variable("user_accounts_cloudTrader_4")
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
                user_accounts_cloudTrader_4,
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

            # 手数范围：结束手数校验（使用math.isclose替换直接比较）
            min_lot_size = db_data[0]["min_lot_size"]
            endsize = trader_ordersend["endSize"]
            assert math.isclose(float(endsize), float(min_lot_size), rel_tol=1e-9, abs_tol=1e-9), \
                f'手数范围：结束手数是：{endsize}，实际是：{min_lot_size}'
            logging.info(f'手数范围：结束手数是：{endsize}，实际是：{min_lot_size}')

            # 手数范围：开始手数校验
            max_lot_size = db_data[0]["max_lot_size"]
            startSize = trader_ordersend["startSize"]
            assert math.isclose(float(startSize), float(max_lot_size), rel_tol=1e-9, abs_tol=1e-9), \
                f'手数范围：开始手数是：{startSize}，实际是：{max_lot_size}'
            logging.info(f'手数范围：开始手数是：{startSize}，实际是：{max_lot_size}')

            # 总订单数量校验
            total_orders = db_data[0]["total_orders"]
            totalNum = trader_ordersend["totalNum"]
            assert math.isclose(float(totalNum), float(total_orders), rel_tol=1e-9, abs_tol=1e-9), \
                f'总订单数量是：{totalNum}，实际是：{total_orders}'
            logging.info(f'总订单数量是：{totalNum}，实际是：{total_orders}')

            # 下单总手数与指令表总手数校验
            total_lots = db_data[0]["total_lots"]
            totalSzie = trader_ordersend["totalSzie"]
            assert math.isclose(float(totalSzie), float(total_lots), rel_tol=1e-9, abs_tol=1e-9), \
                f'下单总手数是：{totalSzie}，实际是：{total_lots}'
            logging.info(f'下单总手数是：{totalSzie}，实际是：{total_lots}')

            # 下单总手数与订单详情总手数校验
            totalSzie = trader_ordersend["totalSzie"]
            size = [record["size"] for record in db_data]
            total = sum(size)
            assert math.isclose(float(totalSzie), float(total), rel_tol=1e-9, abs_tol=1e-9), \
                f'下单总手数是：{totalSzie},订单详情总手数是：{total}'
            logging.info(f'下单总手数是：{totalSzie},订单详情总手数是：{total}')

    # ---------------------------
    # 账号管理-交易下单-云策略平仓
    # ---------------------------
    @allure.title("账号管理-交易下单-云平仓")
    def test_bargain_masOrderClose(self, api_session, var_manager, logged_session):
        # 1. 发送平仓请求
        data = {
            "isCloseAll": 1,
            "intervalTime": 100,
            "traderList": [user_ids_cloudTrader_3]
        }
        response = self.send_post_request(
            api_session,
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

    # ---------------------------
    # 数据库校验-交易平仓-指令及订单详情数据检查
    # ---------------------------
    @allure.title("数据库校验-交易平仓-指令及订单详情数据检查")
    def test_dbquery_addsalve_orderSendclose(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            user_accounts_cloudTrader_3 = var_manager.get_variable("user_accounts_cloudTrader_3")
            vps_cloudTrader_ids_2 = var_manager.get_variable("vps_cloudTrader_ids_2")
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
                user_accounts_cloudTrader_3,
                vps_cloudTrader_ids_2,
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

            # 平仓总手数校验
            totalSzie = trader_ordersend["totalSzie"]
            size = [record["size"] for record in db_data]
            total = sum(size)
            assert math.isclose(float(totalSzie), float(total), rel_tol=1e-9, abs_tol=1e-9), \
                f'下单总手数是：{totalSzie}，订单详情总手数是：{total}'
            logging.info(f'下单总手数是：{totalSzie}，订单详情总手数是：{total}')

    # ---------------------------
    # 数据库校验-交易平仓-跟单账号出现漏平
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-交易平仓-跟单账号出现漏平")
    def test_dbquery_level(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            user_accounts_cloudTrader_4 = var_manager.get_variable("user_accounts_cloudTrader_4")
            traderList_cloudTrader_4 = var_manager.get_variable("traderList_cloudTrader_4")
            cloudMaster_id = var_manager.get_variable("cloudMaster_id")

            sql = f"""
                       SELECT * 
                       FROM follow_order_detail 
                       WHERE account = %s
                         AND cloud_trader_id = %s
                         AND cloud_id = %s
                       """
            params = (
                user_accounts_cloudTrader_4,
                traderList_cloudTrader_4,
                cloudMaster_id,
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="create_time"
            )
        with allure.step("2. 校验数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")
            close_remark = db_data[0]["close_remark"]
            assert close_remark == "未开通平仓状态", f"云策略跟单账号未开启开仓，备注信息是：未开通平仓状态，实际是{close_remark}"

            close_status = db_data[0]["close_status"]
            assert close_status == 0, f"云策略跟单账号平仓失败，状态是：0，实际是{close_status}"

    # ---------------------------
    # 云策略-云策略列表-修改云策略跟单
    # ---------------------------
    @allure.title("云策略-云策略列表-修改云策略跟单")
    def test_cloudTrader_cloudBatchUpdate2(self, var_manager, logged_session, db_transaction):
        with allure.step("1. 发送修改跟单策略账号请求，将followClose改为1，开启开仓"):
            cloudMaster_id = var_manager.get_variable("cloudMaster_id")
            traderList_cloudTrader_4 = var_manager.get_variable("traderList_cloudTrader_4")
            traderList_cloudTrader_3 = var_manager.get_variable("traderList_cloudTrader_3")
            user_accounts_cloudTrader_3 = var_manager.get_variable("user_accounts_cloudTrader_3")
            data = [
                {
                    "traderList": [
                        traderList_cloudTrader_4
                    ],
                    "cloudId": cloudMaster_id,
                    "masterId": traderList_cloudTrader_3,
                    "masterAccount": user_accounts_cloudTrader_3,
                    "followDirection": 0,
                    "followMode": 1,
                    "followParam": 1,
                    "remainder": 0,
                    "placedType": 0,
                    "templateId": 1,
                    "followStatus": 1,
                    "followOpen": 1,
                    "followClose": 1,
                    "fixedComment": "ceshi",
                    "commentType": "",
                    "digits": 0,
                    "followTraderIds": [],
                    "sort": "100"
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
                "修改云跟单账号失败"
            )

            # 3. 验证JSON返回内容
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

    @allure.title("数据库校验-云策略列表-修改云跟单账号是否成功")
    def test_dbcloudTrader_cloudBatchUpdate2(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否修改成功"):
            user_accounts_cloudTrader_4 = var_manager.get_variable("user_accounts_cloudTrader_4")
            sql = f"SELECT * FROM follow_cloud_trader WHERE account = %s"
            params = (user_accounts_cloudTrader_4,)

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params
            )
        with allure.step("2. 对数据进行校验"):
            follow_close = db_data[0]["follow_close"]
            assert follow_close == 1, f"follow_close的状态应该是1，实际是：{follow_close}"

    @allure.title("数据库校验-云策略下单-获取云策略跟单指令ID")
    def test_dbbargain_masOrderSend2(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否有下单"):
            cloudOrderSend = var_manager.get_variable("cloudOrderSend")
            cloudMaster_id = var_manager.get_variable("cloudMaster_id")
            user_accounts_cloudTrader_3 = var_manager.get_variable("user_accounts_cloudTrader_3")
            symbol = cloudOrderSend["symbol"]

            sql = f"""
                       SELECT * 
                       FROM follow_order_instruct
                       WHERE symbol LIKE %s 
                         AND cloud_account = %s 
                         AND cloud_id = %s 
                       """
            params = (
                f"%{symbol}%",
                user_accounts_cloudTrader_3,
                cloudMaster_id,
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="create_time",  # 按创建时间过滤
                time_range=50,  # 只查前后2分钟的数据
                timeout=WAIT_TIMEOUT,  # 最多等30秒
                poll_interval=POLL_INTERVAL,  # 每2秒查一次
                stable_period=STBLE_PERIOD,  # 新增：数据连续3秒不变则认为加载完成
                order_by="create_time DESC"  # 按创建时间倒序
            )

        with allure.step("2. 提取数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            order_instruct_id = [record["id"] for record in db_data]
            logging.info(f"下单指令的ID: {order_instruct_id}")
            var_manager.set_runtime_variable("order_instruct_id", order_instruct_id)

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云策略列表-批量重试-漏平")
    def test_bargain_masRetryAllBatch(self, api_session, var_manager, logged_session):
        # 1. 发送批量重试请求
        order_instruct_id = var_manager.get_variable("order_instruct_id")
        data = {
            "ids": order_instruct_id
        }
        response = self.send_post_request(
            api_session,
            '/bargain/masRetryAllBatch',
            json_data=data,
        )

        # 2. 判断云策略复制下单是否成功
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    @allure.title("数据库校验-云策略平仓-云策略跟单账号数据校验")
    def test_dbbargain_masOrderSend4(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否有下单"):
            user_accounts_cloudTrader_4 = var_manager.get_variable("user_accounts_cloudTrader_4")

            sql = f"""
                   SELECT 
                        fod.size,
                        fod.close_no,
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
                "1",
                user_accounts_cloudTrader_4
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="foi.create_time",  # 按创建时间过滤
                time_range=MYSQL_TIME,  # 只查前后2分钟的数据
                timeout=WAIT_TIMEOUT,  # 最多等30秒
                poll_interval=POLL_INTERVAL,  # 每2秒查一次
                stable_period=STBLE_PERIOD,  # 新增：数据连续3秒不变则认为加载完成
                order_by="foi.create_time DESC"  # 按创建时间倒序
            )
        with allure.step("2. 对数据进行校验"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            size = [record["size"] for record in db_data]
            cloudOrderSend = var_manager.get_variable("cloudOrderSend")
            total = sum(size)
            totalSzie = cloudOrderSend["totalSzie"]
            assert math.isclose(float(total), float(totalSzie), rel_tol=1e-9,
                                abs_tol=1e-9), f"跟单总手数和下单的手数不相等 (实际: {total}, 预期: {totalSzie})"
            logging.info(f"跟单总手数和下单的手数相等(实际: {total}, 预期: {totalSzie})")

        time.sleep(25)
