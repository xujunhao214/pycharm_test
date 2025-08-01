# lingkuan_729/tests/test_vps_ordersend.py
import time

import allure
import logging
import pytest
from lingkuan_729.VAR.VAR import *
from lingkuan_729.conftest import var_manager
from lingkuan_729.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


# ---------------------------
# 云策略-云策略列表-云策略跟单账号修改模式、品种
# ---------------------------
@allure.feature("云策略策略下单-跟单修改模式、品种")
class Testcloudtrader_Scence(APITestBase):
    # ---------------------------
    # 账号管理-交易下单-云策略账号复制下单
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-交易下单-云策略账号复制下单")
    def test_bargain_masOrderSend(self, api_session, var_manager, logged_session):
        # 1. 发送云策略复制下单请求
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
    # 数据库校验-云策略跟单账号策略开仓-持仓检查跟单账号数据-固定手数5
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-云策略跟单账号策略开仓-跟单账号固定手数")
    def test_dbdetail_followParam5(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            user_accounts_cloudTrader_5 = var_manager.get_variable("user_accounts_cloudTrader_5")
            sql = f"""
                    SELECT 
                        fod.size,
                        fod.send_no,
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
                        foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
                    WHERE foi.operation_type=%s
                        AND fod.account = %s
                """
            params = (
                '0',
                user_accounts_cloudTrader_5,
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

            addsalve_size_followParam = db_data[0]["size"]
            assert addsalve_size_followParam == 5, f"跟单账号实际下单手数 (实际: {addsalve_size_followParam}, 预期: 5)"
            logging.info(f"跟单账号实际下单手数 (实际: {addsalve_size_followParam}, 预期: 5)")

    # ---------------------------
    # 数据库校验-云策略跟单账号策略开仓-跟单账号修改品种
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-云策略跟单账号策略开仓-跟单账号修改品种")
    def test_dbdetail_templateId3(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            user_accounts_cloudTrader_6 = var_manager.get_variable("user_accounts_cloudTrader_6")

            sql = f"""
                    SELECT 
                        fod.size,
                        fod.send_no,
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
                        foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
                    WHERE foi.operation_type=%s
                        AND fod.account = %s
                """
            params = (
                '0',
                user_accounts_cloudTrader_6,
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

            addsalve_size_templateId3 = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("addsalve_size_templateId3", addsalve_size_templateId3)
            total = sum(addsalve_size_templateId3)
            assert float(total) == 3, f"修改下单品种之后下单手数之和应该是3，实际是：{total}"
            logging.info(f"修改下单品种之后下单手数之和应该是3，实际是：{total}")

    # ---------------------------
    # 数据库-获取主账号净值
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库-获取主账号净值")
    def test_dbtrader_euqit(self, var_manager, db_transaction):
        with allure.step("1. 获取主账号净值"):
            vps_cloudTrader_ids_2 = var_manager.get_variable("vps_cloudTrader_ids_2")

            sql = f"""
                        SELECT * FROM follow_trader WHERE id = %s
                        """
            params = (
                vps_cloudTrader_ids_2
            )

            # 使用智能等待查询
            db_data = self.query_database(
                db_transaction,
                sql,
                params,
            )

        with allure.step("2. 提取数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            cloud_euqit = db_data[0]["euqit"]
            var_manager.set_runtime_variable("cloud_euqit", cloud_euqit)
            logging.info(f"主账号净值：{cloud_euqit}")

    # ---------------------------
    # 数据库-获取跟单账号净值
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库-获取跟单账号净值")
    def test_dbaddsalve_euqit(self, var_manager, db_transaction):
        with allure.step("1. 获取跟单账号净值"):
            vps_cloudTrader_ids_6 = var_manager.get_variable("vps_cloudTrader_ids_6")

            sql = f"""
                    SELECT * FROM follow_trader WHERE id = %s
                    """
            params = (
                vps_cloudTrader_ids_6
            )

            # 使用智能等待查询
            db_data = self.query_database(
                db_transaction,
                sql,
                params,
            )

        with allure.step("2. 提取数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            addcloud_euqit = db_data[0]["euqit"]
            var_manager.set_runtime_variable("addcloud_euqit", addcloud_euqit)
            logging.info(f"跟单账号净值：{addcloud_euqit}")

    # 数据库校验-云策略跟单账号策略开仓-修改净值
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-云策略跟单账号策略开仓-修改净值")
    def test_dbtrader_euqit2(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            user_accounts_cloudTrader_7 = var_manager.get_variable("user_accounts_cloudTrader_7")

            sql = f"""
                    SELECT 
                        fod.size,
                        fod.send_no,
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
                        foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
                    WHERE foi.operation_type=%s
                        AND fod.account = %s
                """
            params = (
                '0',
                user_accounts_cloudTrader_7,
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

            addsalve_size_euqit = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("addsalve_size_euqit", addsalve_size_euqit)
            total = sum(addsalve_size_euqit)
            cloud_euqit = var_manager.get_variable("cloud_euqit")
            addcloud_euqit = var_manager.get_variable("addcloud_euqit")
            # 校验除数非零
            if cloud_euqit == 0:
                pytest.fail("cloud_euqit为0，无法计算预期比例（避免除零）")

            true_size = addcloud_euqit / cloud_euqit * 1
            # 断言（调整误差范围为合理值，如±0.1）
            assert abs(total - true_size) < 3, f"size总和与预期比例偏差过大：预期{true_size}，实际{total}，误差超过3"
            logging.info(f"预期: {true_size} 实际: {total}")

    # ---------------------------
    # 账号管理-交易下单-云策略平仓
    # ---------------------------
    @allure.title("账号管理-交易下单-云策略平仓")
    def test_bargain_masOrderClose(self, api_session, var_manager, logged_session):
        user_ids_cloudTrader_3 = var_manager.get_variable("user_ids_cloudTrader_3")
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
    # 云策略-云策略列表-平仓
    # ---------------------------
    @allure.title("云策略-云策略列表-平仓")
    def test_cloudTrader_cloudOrderClose(self, api_session, var_manager, logged_session):
        cloudMaster_id = var_manager.get_variable("cloudMaster_id")
        # 1. 发送平仓请求
        data = {
            "isCloseAll": 1,
            "intervalTime": 100,
            "id": f"{cloudMaster_id}"
        }
        response = self.send_post_request(
            api_session,
            '/mascontrol/cloudTrader/cloudOrderClose',
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
    # 数据库校验-云策略跟单账号策略开仓-持仓检查跟单账号数据-固定手数5
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-云策略跟单账号策略平仓-跟单账号固定手数")
    def test_dbclose_followParam5(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            user_accounts_cloudTrader_5 = var_manager.get_variable("user_accounts_cloudTrader_5")
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
                user_accounts_cloudTrader_5,
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

            addsalve_size_followParam = db_data[0]["size"]
            assert addsalve_size_followParam == 5, f"跟单账号实际平仓手数 (实际: {addsalve_size_followParam}, 预期: 5)"
            logging.info(f"跟单账号实际平仓手数 (实际: {addsalve_size_followParam}, 预期: 5)")

    # ---------------------------
    # 数据库校验-云策略跟单账号策略平仓-跟单账号修改品种
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-云策略跟单账号策略平仓-跟单账号修改品种")
    def test_dbclose_templateId3(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            user_accounts_cloudTrader_6 = var_manager.get_variable("user_accounts_cloudTrader_6")

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
                user_accounts_cloudTrader_6,
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

            addsalve_size_templateId3 = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("addsalve_size_templateId3", addsalve_size_templateId3)
            total = sum(addsalve_size_templateId3)
            assert float(total) == 3, f"修改下单品种之后平仓手数之和应该是3，实际是：{total}"
            logging.info(f"修改下单品种之后平仓手数之和应该是3，实际是：{total}")

    # ---------------------------
    # 数据库校验-云策略跟单账号策略平仓-修改净值
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-云策略跟单账号策略平仓-修改净值")
    def test_dbclose_euqit(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            user_accounts_cloudTrader_7 = var_manager.get_variable("user_accounts_cloudTrader_7")

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
                user_accounts_cloudTrader_7,
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

            addsalve_size_euqit = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("addsalve_size_euqit", addsalve_size_euqit)
            total = sum(addsalve_size_euqit)
            cloud_euqit = var_manager.get_variable("cloud_euqit")
            addcloud_euqit = var_manager.get_variable("addcloud_euqit")
            # 校验除数非零
            if cloud_euqit == 0:
                pytest.fail("cloud_euqit为0，无法计算预期比例（避免除零）")

            true_size = addcloud_euqit / cloud_euqit * 1
            # 断言（调整误差范围为合理值，如±0.1）
            assert abs(total - true_size) < 3, f"size总和与预期比例偏差过大：预期{true_size}，实际{total}，误差超过3"
            logging.info(f"预期: {true_size} 实际: {total}")

        time.sleep(25)
