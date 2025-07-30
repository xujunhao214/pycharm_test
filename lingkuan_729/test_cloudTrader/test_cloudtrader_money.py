# lingkuan_729/tests/test_vps_ordersend.py
import time
import math

import allure
import logging
import pytest
from lingkuan_729.VAR.VAR import *
from lingkuan_729.conftest import var_manager
from lingkuan_729.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


# ---------------------------
# 云策略-云策略列表-云策略跟单账号修改币种
# ---------------------------
@allure.feature("云策略-云策略列表-云策略跟单账号修改币种")
class Testcloudtrader_money(APITestBase):
    # ---------------------------
    # 账号管理-账号列表-修改用户
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-账号列表-修改用户")
    def test_update_user(self, api_session, var_manager, logged_session):
        # 1. 发送创建用户请求
        user_ids_cloudTrader_3 = var_manager.get_variable("user_ids_cloudTrader_3")
        user_accounts_cloudTrader_3 = var_manager.get_variable("user_accounts_cloudTrader_3")
        vps_cloudTrader_ids_2 = var_manager.get_variable("vps_cloudTrader_ids_2")
        vps_id_cloudTrader = var_manager.get_variable("vps_cloudTrader_ids_2")
        user_accounts_cloudTrader_1 = var_manager.get_variable("user_accounts_cloudTrader_1")
        vpsId = var_manager.get_variable("vpsId")
        data = {
            "id": user_ids_cloudTrader_3,
            "account": user_accounts_cloudTrader_3,
            "password": "b7e9fafa953d50f0e2278cacd85a8d15",
            "platform": "FXAdamantStone-Demo",
            "accountType": "0",
            "serverNode": "47.83.21.167:443",
            "remark": "参数化新增云策略账号",
            "sort": 100,
            "vpsDescs": [
                {
                    "desc": "39.99.136.49-主VPS-跟单账号",
                    "status": 0,
                    "statusExtra": "启动成功",
                    "forex": "",
                    "cfd": "",
                    "traderId": vps_cloudTrader_ids_2,
                    "ipAddress": "39.99.136.49",
                    "sourceId": vps_id_cloudTrader,
                    "sourceAccount": user_accounts_cloudTrader_1,
                    "sourceName": "测试数据",
                    "loginNode": "47.83.21.167:443",
                    "nodeType": 0,
                    "nodeName": "账号节点",
                    "type": None,
                    "vpsId": vpsId,
                    "traderType": None,
                    "abRemark": None
                }
            ]
        }
        response = self.send_put_request(
            api_session,
            "/mascontrol/user",
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "编辑策略信息失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # ---------------------------
    # 数据库校验-账号列表-修改用户是否成功
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-账号列表-修改用户是否成功")
    def test_dbupdate_user(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否编辑成功"):
            user_accounts_cloudTrader_3 = var_manager.get_variable("user_accounts_cloudTrader_3")
            sql = f"SELECT * FROM follow_cloud_trader WHERE account = %s"
            params = (user_accounts_cloudTrader_3,)

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

            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")
            cfd_value = db_data[0]["cfd"]
            # 允许为 None 或空字符串（去除空格后）
            assert cfd_value is None or cfd_value.strip() == "", f"修改个人信息失败（cfd字段应为空，实际值：{cfd_value}）"

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
    # 数据库校验-云策略跟单账号策略开仓-修改币种@
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-云策略跟单账号策略开仓-修改币种@")
    def test_dbtrader_cfda(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            user_accounts_cloudTrader_8 = var_manager.get_variable("user_accounts_cloudTrader_8")
            sql = f"""
                    SELECT 
                        fod.size,
                        fod.send_no,
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
                        foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
                    WHERE foi.operation_type = %s
                        AND fod.account = %s
                        """
            params = (
                '0',
                user_accounts_cloudTrader_8,
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

            addsalve_size_cfda = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("addsalve_size_cfda", addsalve_size_cfda)
            addsalve_size_cfda_total = sum(addsalve_size_cfda)
            assert math.isclose(addsalve_size_cfda_total, 1.0,
                                rel_tol=1e-9), f"修改币种下单总手数应该是1，实际是：{addsalve_size_cfda_total}"
            logging.info(f"修改币种下单总手数应该是1，实际是：{addsalve_size_cfda_total}")

            symbol = db_data[0]["symbol"]
            assert symbol == "XAUUSD@" or symbol == "XAUUSD", f"下单的币种与预期的不一样，预期：XAUUSD@ 实际：{symbol}"

    # ---------------------------
    # 数据库校验-云策略跟单账号策略开仓-修改币种p
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-云策略跟单账号策略开仓-修改币种p")
    def test_dbtrader_cfdp(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            user_accounts_cloudTrader_9 = var_manager.get_variable("user_accounts_cloudTrader_9")
            sql = f"""
                    SELECT 
                        fod.size,
                        fod.send_no,
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
                        foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
                    WHERE foi.operation_type=%s
                        AND fod.account = %s
                        """
            params = (
                '0',
                user_accounts_cloudTrader_9,
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

            addsalve_size_cfdp = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("addsalve_size_cfdp", addsalve_size_cfdp)
            addsalve_size_cfdp_total = sum(addsalve_size_cfdp)
            assert (math.isclose(addsalve_size_cfdp_total, 0.02, rel_tol=1e-9) or
                    math.isclose(addsalve_size_cfdp_total, 0.03, rel_tol=1e-9) or
                    math.isclose(addsalve_size_cfdp_total, 1.0,
                                 rel_tol=1e-9)), f"修改币种下单总手数应该是0.02或者0.03，如果币种不在交易时间就是1，实际是：{addsalve_size_cfdp_total}"
            logging.info(
                f"修改币种下单总手数应该是0.02或者0.03，如果币种不在交易时间就是1，实际是：{addsalve_size_cfdp_total}")

            symbol = db_data[0]["symbol"]
            assert symbol == "XAUUSD.p" or symbol == "XAUUSD", f"下单的币种与预期的不一样，预期：XAUUSD.p，如果这个币种不在交易时间就是XAUUSD 实际：{symbol}"

    # 数据库校验-云策略跟单账号策略开仓-修改币种min
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-云策略跟单账号策略开仓-修改币种min")
    def test_dbtrader_cfdmin(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            user_accounts_cloudTrader_10 = var_manager.get_variable("user_accounts_cloudTrader_10")
            sql = f"""
                    SELECT 
                        fod.size,
                        fod.send_no,
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
                        foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
                    WHERE foi.operation_type=%s
                        AND fod.account = %s
                        """
            params = (
                '0',
                user_accounts_cloudTrader_10,
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

            addsalve_size_cfdmin = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("addsalve_size_cfdmin", addsalve_size_cfdmin)
            addsalve_size_cfdmin_total = sum(addsalve_size_cfdmin)
            assert (math.isclose(addsalve_size_cfdmin_total, 10.0, rel_tol=1e-9) or
                    math.isclose(addsalve_size_cfdmin_total, 1.0,
                                 rel_tol=1e-9)), f"修改币种下单总手数应该是10,如果这个币种不在交易时间就是1，实际是：{addsalve_size_cfdmin_total}"
            logging.info(
                f"修改币种下单总手数应该是10,如果这个币种不在交易时间就是1，实际是：{addsalve_size_cfdmin_total}")

            symbol = db_data[0]["symbol"]
            assert symbol == "XAUUSD.min" or symbol == "XAUUSD", f"下单的币种与预期的不一样，预期：XAUUSD.min，如果这个币种不在交易时间就是XAUUSD，实际：{symbol}"

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
    # 数据库校验-云策略跟单账号策略平仓-修改币种@
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-云策略跟单账号策略平仓-修改币种@")
    def test_dbclose_cfda(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            user_accounts_cloudTrader_8 = var_manager.get_variable("user_accounts_cloudTrader_8")
            sql = f"""
                    SELECT 
                        fod.size,
                        fod.close_no,
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
                    WHERE foi.operation_type=%s
                        AND fod.account = %s
                        """
            params = (
                '1',
                user_accounts_cloudTrader_8,
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

            addsalve_size_cfda_close = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("addsalve_size_cfda_close", addsalve_size_cfda_close)
            addsalve_size_cfda_total = sum(addsalve_size_cfda_close)
            assert math.isclose(addsalve_size_cfda_total, 1.0,
                                rel_tol=1e-9), f"修改币种下单总手数应该是1，实际是：{addsalve_size_cfda_total}"
            logging.info(f"修改币种下单总手数应该是1，实际是：{addsalve_size_cfda_total}")

            symbol = db_data[0]["symbol"]
            assert symbol == "XAUUSD@" or symbol == "XAUUSD", f"下单的币种与预期的不一样，预期：XAUUSD@ 实际：{symbol}"

    # ---------------------------
    # 数据库校验-云策略跟单账号策略平仓-修改币种p
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-云策略跟单账号策略平仓-修改币种p")
    def test_dbclose_cfdp(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            user_accounts_cloudTrader_9 = var_manager.get_variable("user_accounts_cloudTrader_9")
            sql = f"""
                    SELECT 
                        fod.size,
                        fod.close_no,
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
                    WHERE foi.operation_type=%s
                        AND fod.account = %s
                        """
            params = (
                '1',
                user_accounts_cloudTrader_9,
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

            addsalve_size_cfdp_close = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("addsalve_size_cfdp_close", addsalve_size_cfdp_close)
            addsalve_size_cfdp_total = sum(addsalve_size_cfdp_close)
            assert (math.isclose(addsalve_size_cfdp_total, 0.02, rel_tol=1e-9) or
                    math.isclose(addsalve_size_cfdp_total, 0.03, rel_tol=1e-9) or
                    math.isclose(addsalve_size_cfdp_total, 1.0,
                                 rel_tol=1e-9)), f"修改币种下单总手数应该是0.02或者0.03，如果币种不在交易时间就是1，实际是：{addsalve_size_cfdp_total}"
            logging.info(
                f"修改币种下单总手数应该是0.02或者0.03，如果币种不在交易时间就是1，实际是：{addsalve_size_cfdp_total}")

            symbol = db_data[0]["symbol"]
            assert symbol == "XAUUSD.p" or symbol == "XAUUSD", f"下单的币种与预期的不一样，预期：XAUUSD.p，如果这个币种不在交易时间就是XAUUSD 实际：{symbol}"

    # ---------------------------
    # 数据库校验-云策略跟单账号策略平仓-修改币种min
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-云策略跟单账号策略平仓-修改币种min")
    def test_dbclose_cfdmin(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            user_accounts_cloudTrader_10 = var_manager.get_variable("user_accounts_cloudTrader_10")
            sql = f"""
                    SELECT 
                        fod.size,
                        fod.close_no,
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
                    WHERE foi.operation_type=%s
                        AND fod.account = %s
                        """
            params = (
                '1',
                user_accounts_cloudTrader_10,
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

            addsalve_size_cfdmin_close = [record["size"] for record in db_data]
            var_manager.set_runtime_variable("addsalve_size_cfdmin_close", addsalve_size_cfdmin_close)
            addsalve_size_cfdmin_total = sum(addsalve_size_cfdmin_close)
            assert (math.isclose(addsalve_size_cfdmin_total, 10.0, rel_tol=1e-9) or
                    math.isclose(addsalve_size_cfdmin_total, 1.0,
                                 rel_tol=1e-9)), f"修改币种下单总手数应该是10,如果这个币种不在交易时间就是1，实际是：{addsalve_size_cfdmin_total}"
            logging.info(
                f"修改币种下单总手数应该是10,如果这个币种不在交易时间就是1，实际是：{addsalve_size_cfdmin_total}")

            symbol = db_data[0]["symbol"]
            assert symbol == "XAUUSD.min" or symbol == "XAUUSD", f"下单的币种与预期的不一样，预期：XAUUSD.min，如果这个币种不在交易时间就是XAUUSD，实际：{symbol}"

        time.sleep(25)
