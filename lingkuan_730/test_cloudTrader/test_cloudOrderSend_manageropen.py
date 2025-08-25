# lingkuan_730/tests/test_云策略_ordersend.py
import allure
import logging
import pytest
import time
import math
from lingkuan_730.VAR.VAR import *
from lingkuan_730.conftest import var_manager
from lingkuan_730.commons.api_base import APITestBase

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("交易下单-manager账号云策略复制下单-漏开")
class TestcloudTrader_manageropen(APITestBase):
    # ---------------------------
    # 云策略-云策略列表-修改云策略跟单
    # ---------------------------
    @allure.title("云策略-云策略列表-修改云策略跟单")
    def test_cloudTrader_cloudBatchUpdate(self, var_manager, logged_session, db_transaction):
        with allure.step("1. 发送修改跟单策略账号请求，将followOpen改为0，关闭开仓"):
            traderList_cloudTrader_4 = var_manager.get_variable("traderList_cloudTrader_4")
            cloudMaster_id = var_manager.get_variable("cloudMaster_id")
            data = {
                "traderList": [
                    traderList_cloudTrader_4
                ],
                "remark": "修改云策略跟单账号",
                "followDirection": 0,
                "followMode": 1,
                "remainder": 0,
                "followParam": 1,
                "placedType": 0,
                "templateId": 1,
                "followStatus": 1,
                "followOpen": 0,
                "followClose": 1,
                "followRep": None,
                "fixedComment": "ceshi",
                "commentType": None,
                "digits": 0,
                "cfd": "@",
                "forex": "",
                "sort": 1,
                "cloudId": cloudMaster_id
            }

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

    @allure.title("数据库校验-云策略列表-修改云策略跟单账号是否成功")
    def test_dbcloudTrader_cloudBatchUpdate(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否修改成功"):
            user_accounts_cloudTrader_4 = var_manager.get_variable("user_accounts_cloudTrader_4")
            sql = f"SELECT * FROM follow_cloud_trader WHERE account = %s"
            params = (user_accounts_cloudTrader_4,)

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                timeout=WAIT_TIMEOUT,  # 最多等30秒
                poll_interval=POLL_INTERVAL,  # 每2秒查一次
                stable_period=STBLE_PERIOD,  # 新增：数据连续3秒不变则认为加载完成
                order_by="create_time DESC"  # 按创建时间倒序
            )
        with allure.step("2. 对数据进行校验"):
            follow_open = db_data[0]["follow_open"]
            assert follow_open == 0, f"follow_open的状态应该是0，实际是：{follow_open}"

    # ---------------------------
    # 账号管理-交易下单-云策略账号复制下单
    # ---------------------------
    @allure.title("账号管理-交易下单-云策略账号复制下单")
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
            json_data=data
        )

        # 2. 判断云策略复制下单是否成功
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    @allure.title("数据库校验-云策略下单-下单指令")
    def test_dbbargain_masOrderSend(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否有下单"):
            cloudOrderSend = var_manager.get_variable("cloudOrderSend")
            vps_cloudTrader_ids_2 = var_manager.get_variable("vps_cloudTrader_ids_2")
            symbol = cloudOrderSend["symbol"]

            sql = f"""
                SELECT * 
                FROM follow_order_instruct
                WHERE symbol LIKE %s 
                  AND master_order_status = %s 
                  AND type = %s 
                  AND min_lot_size = %s 
                  AND max_lot_size = %s 
                  AND remark = %s 
                  AND total_lots = %s 
                  AND trader_id = %s
                """
            params = (
                f"%{symbol}%",
                "0",
                cloudOrderSend["type"],
                cloudOrderSend["endSize"],
                cloudOrderSend["startSize"],
                cloudOrderSend["remark"],
                cloudOrderSend["totalSzie"],
                vps_cloudTrader_ids_2
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="create_time",  # 按创建时间过滤
                time_range=MYSQL_TIME,  # 只查前后2分钟的数据
                timeout=WAIT_TIMEOUT,  # 最多等30秒
                poll_interval=POLL_INTERVAL,  # 每2秒查一次
                stable_period=STBLE_PERIOD,  # 新增：数据连续3秒不变则认为加载完成
                order_by="create_time DESC"  # 按创建时间倒序
            )

        with allure.step("2. 提取数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            order_no = db_data[0]["order_no"]
            logging.info(f"获取交易账号下单的订单号: {order_no}")
            var_manager.set_runtime_variable("order_no", order_no)

        with allure.step("3. 对数据进行校验"):
            operation_type = db_data[0]["operation_type"]
            assert operation_type == 0, f"操作类型operation_type应为0(下单)，实际状态为: {operation_type}"

            status = db_data[0]["status"]
            assert status in (0, 1), f"订单状态status应为0(处理中)或1(全部成功)，实际状态为: {status}"

    @allure.title("数据库校验-云策略分配下单-持仓检查")
    def test_dbquery_order_detail(self, var_manager, db_transaction):
        with allure.step("1. 根据下单指令仓库的order_no字段获取跟单账号订单数据"):
            order_no = var_manager.get_variable("order_no")
            cloudOrderSend = var_manager.get_variable("cloudOrderSend")
            symbol = cloudOrderSend["symbol"]

            sql = f"""
            SELECT * 
            FROM follow_order_detail
            WHERE symbol LIKE %s 
              AND send_no = %s 
              AND type = %s 
            """
            params = (
                f"%{symbol}%",
                order_no,
                cloudOrderSend["type"],
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="create_time",  # 按创建时间过滤
                time_range=MYSQL_TIME,  # 只查前后2分钟的数据
                timeout=WAIT_TIMEOUT,  # 最多等30秒
                poll_interval=POLL_INTERVAL,  # 每2秒查一次
                stable_period=STBLE_PERIOD,  # 新增：数据连续3秒不变则认为加载完成
                order_by="create_time DESC"  # 按创建时间倒序
            )

        with allure.step("2. 校验数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")
            addsalve_size = [record["size"] for record in db_data]
            total = sum(addsalve_size)
            logging.info(f"手数: {addsalve_size}   手数总和: {total}")
            totalSzie = cloudOrderSend["totalSzie"]
            assert math.isclose(float(total), float(totalSzie), rel_tol=1e-9,
                                abs_tol=1e-9), f"跟单总手数和下单的手数不相等 (实际: {total}, 预期: {totalSzie})"
            logging.info(f"跟单总手数和下单的手数相等(实际: {total}, 预期: {totalSzie})")

    # ---------------------------
    # 数据库校验-交易平仓-跟单账号出现漏开
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-交易平仓-跟单账号出现漏开")
    def test_dbquery_manageropen(self, var_manager, db_transaction):
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
                time_field="create_time",  # 按创建时间过滤
                time_range=MYSQL_TIME,  # 只查前后2分钟的数据
                timeout=WAIT_TIMEOUT,  # 最多等30秒
                poll_interval=POLL_INTERVAL,  # 每2秒查一次
                stable_period=STBLE_PERIOD,  # 新增：数据连续3秒不变则认为加载完成
                order_by="create_time DESC"  # 按创建时间倒序
            )
        with allure.step("2. 校验数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")
            remark = db_data[0]["remark"]
            assert remark == "未开通下单状态", f"云策略跟单账号未开启开仓，备注信息是：未开通下单状态，实际是{remark}"

    # ---------------------------
    # 云策略-云策略列表-修改云策略跟单
    # ---------------------------
    @allure.title("云策略-云策略列表-修改云策略跟单")
    def test_cloudTrader_cloudBatchUpdate2(self, var_manager, logged_session, db_transaction):
        with allure.step("1. 发送修改跟单策略账号请求，将followOpen改为1，开启开仓"):
            traderList_cloudTrader_4 = var_manager.get_variable("traderList_cloudTrader_4")
            cloudMaster_id = var_manager.get_variable("cloudMaster_id")
            data = {
                "traderList": [
                    traderList_cloudTrader_4
                ],
                "remark": "修改云策略跟单账号",
                "followDirection": 0,
                "followMode": 1,
                "remainder": 0,
                "followParam": 1,
                "placedType": 0,
                "templateId": 1,
                "followStatus": 1,
                "followOpen": 1,
                "followClose": 1,
                "followRep": None,
                "fixedComment": "ceshi",
                "commentType": None,
                "digits": 0,
                "cfd": "@",
                "forex": "",
                "sort": 1,
                "cloudId": cloudMaster_id
            }

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

    @allure.title("数据库校验-云策略列表-修改云策略跟单账号是否成功")
    def test_dbcloudTrader_cloudBatchUpdate2(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否修改成功"):
            user_accounts_cloudTrader_4 = var_manager.get_variable("user_accounts_cloudTrader_4")
            sql = f"SELECT * FROM follow_cloud_trader WHERE account = %s"
            params = (user_accounts_cloudTrader_4,)

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                timeout=WAIT_TIMEOUT,  # 最多等30秒
                poll_interval=POLL_INTERVAL,  # 每2秒查一次
                stable_period=STBLE_PERIOD,  # 新增：数据连续3秒不变则认为加载完成
                order_by="create_time DESC"  # 按创建时间倒序
            )
        with allure.step("2. 对数据进行校验"):
            follow_open = db_data[0]["follow_open"]
            assert follow_open == 1, f"follow_open的状态应该是1，实际是：{follow_open}"

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
    @allure.title("云策略-云策略列表-批量重试")
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

    @allure.title("数据库校验-云策略开仓-云策略跟单账号数据校验")
    def test_dbbargain_masOrderSend3(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否有下单"):
            cloudMaster_id = var_manager.get_variable("cloudMaster_id")
            user_accounts_cloudTrader_4 = var_manager.get_variable("user_accounts_cloudTrader_4")

            sql = f"""
                   SELECT 
                        fod.size,
                        fod.send_no,
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
                        foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
                    WHERE foi.cloud_id = %s
                        AND foi.operation_type = %s 
                        AND fod.account = %s
                   """
            params = (
                cloudMaster_id,
                "0",
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

    # ---------------------------
    # 账号管理-交易下单-云策略平仓
    # ---------------------------
    @allure.title("账号管理-交易下单-云策略平仓")
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

    @allure.title("数据库校验-交易平仓-云策略平仓指令")
    def test_dbquery_close_addsalve(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否有平仓指令"):
            # 从变量管理器获取参数
            vps_cloudTrader_ids_2 = var_manager.get_variable("vps_cloudTrader_ids_2")

            # 构建SQL（不含时间条件，由wait_for_database_record控制）
            sql = f"""
                   SELECT * 
                   FROM follow_order_instruct 
                   WHERE cloud_type = %s
                     AND trader_id = %s
                     AND operation_type = %s
                   """
            params = (
                "0",  # cloud_type
                vps_cloudTrader_ids_2,  # trader_id
                "1"  # operation_type（平仓指令）
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="create_time",  # 按创建时间过滤
                time_range=MYSQL_TIME,  # 只查前后2分钟的数据
                timeout=WAIT_TIMEOUT,  # 最多等30秒
                poll_interval=POLL_INTERVAL,  # 每2秒查一次
                stable_period=STBLE_PERIOD,  # 新增：数据连续3秒不变则认为加载完成
                order_by="create_time DESC"  # 按创建时间倒序
            )

        with allure.step("2. 提取并保存数据"):
            # 从查询结果中提取订单号（假设第一条是最新的）
            close_send_nos = db_data[0]["order_no"]
            logging.info(f"平仓之后的跟单账号持仓订单号: {close_send_nos}")

            # 保存到运行时变量，供其他用例使用
            var_manager.set_runtime_variable("close_send_nos", close_send_nos)

        with allure.step("3. 验证结果有效性"):
            assert close_send_nos is not None, "平仓指令订单号为空"
            assert len(db_data) >= 1, "未查询到平仓指令记录"

    # ---------------------------
    # 数据库校验-交易平仓-持仓检查跟单账号数据
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-交易平仓-云策略manager账号数据")
    def test_dbquery_addsalve_clsesdetail(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            user_accounts_cloudTrader_3 = var_manager.get_variable("user_accounts_cloudTrader_3")
            cloudOrderSend = var_manager.get_variable("cloudOrderSend")
            sql = f"""
                    SELECT 
                        fod.size,
                        fod.close_no,
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
                    WHERE foi.operation_type=%s
                        AND fod.account = %s
                        """
            params = (
                '1',
                user_accounts_cloudTrader_3,
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
        with allure.step("2. 校验数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            close_addsalve_size = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("close_addsalve_size", close_addsalve_size)
            total = sum(close_addsalve_size)
            logging.info(f"手数: {close_addsalve_size} 手数总和: {total}")
            totalSzie = cloudOrderSend["totalSzie"]
            assert math.isclose(float(total), float(totalSzie), rel_tol=1e-9,
                                abs_tol=1e-9), f"跟单总手数和下单的手数不相等 (实际: {total}, 预期: {totalSzie})"
            logging.info(f"跟单总手数和下单的手数相等(实际: {total}, 预期: {totalSzie})")

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
