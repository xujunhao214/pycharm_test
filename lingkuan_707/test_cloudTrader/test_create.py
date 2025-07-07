# lingkuan_707/tests/test_create.py
import time

import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuan_707.VAR.VAR import *
from lingkuan_707.commons.jsonpath_utils import *
from lingkuan_707.conftest import var_manager
from lingkuan_707.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("账号管理-创建账号-为云策略准备")
class TestCreate_cloudTrader(APITestBase):
    # ---------------------------
    # 账号管理-账号列表-批量新增用户-为云策略准备
    # ---------------------------
    @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-账号列表-批量新增用户")
    def test_create_importuser(self, api_session, var_manager, logged_session, db_transaction):
        """验证数据库"""
        add_cloudTrader = var_manager.get_variable("add_cloudTrader")
        with open(add_cloudTrader["csv_user_path"], 'rb') as f:
            csv_file = f.read()

        # 构造请求参数（文件上传使用files参数）
        files = {
            "file": ("云策略账号数据.csv", csv_file, "text/csv")
        }

        # 1. 发送创建用户请求
        response = self.send_post_request(
            api_session,
            "/mascontrol/user/import",
            files=files
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "批量新增用户失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # ---------------------------
    # 数据库校验-账号列表-批量新增用户
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-账号列表-批量新增用户")
    def test_dbquery__importuser(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            add_cloudTrader = var_manager.get_variable("add_cloudTrader")
            follow_trader_user = var_manager.get_variable("follow_trader_user")

            # 执行数据库查询
            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM {follow_trader_user} WHERE remark = %s",
                (add_cloudTrader["remarkimport"],),
            )

            # 验证查询结果
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            # 提取user_ids和user_accounts（保持原有列表形式，用于后续判断）
            user_ids_cloudTrader = [item["id"] for item in db_data]
            user_accounts_cloudTrader = [item["account"] for item in db_data]

            print(f"提取到用户ID列表: {user_ids_cloudTrader}")
            print(f"提取到用户账号列表: {user_accounts_cloudTrader}")

            # 将列表拆分为单独的变量
            for i, (user_id_cloudTrader, account_cloudTrader) in enumerate(
                    zip(user_ids_cloudTrader, user_accounts_cloudTrader), 1):
                var_manager.set_runtime_variable(f"user_ids_cloudTrader_{i}", user_id_cloudTrader)
                var_manager.set_runtime_variable(f"user_accounts_cloudTrader_{i}", account_cloudTrader)
                print(
                    f"已设置变量: user_ids_cloudTrader_{i}={user_id_cloudTrader}, user_accounts_cloudTrader_{i}={account_cloudTrader}")

            # 保存总数，便于后续参数化使用
            var_manager.set_runtime_variable("user_count_cloudTrader", len(user_ids_cloudTrader))
            print(f"共提取{len(user_ids_cloudTrader)}个用户数据")

    # ---------------------------
    # 跟单软件看板-VPS数据-新增策略账号-为云策略准备
    # ---------------------------
    @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-新增策略账号")
    def test_add_trader(self, var_manager, logged_session, db_transaction):
        # 1. 发送新增策略账号请求
        vps_cloudTrade = var_manager.get_variable("vps_cloudTrade")
        user_accounts_cloudTrader_1 = var_manager.get_variable("user_accounts_cloudTrader_1")
        data = {
            "account": user_accounts_cloudTrader_1,
            "password": vps_cloudTrade["password"],
            "remark": vps_cloudTrade["remark"],
            "followStatus": 1,
            "templateId": 1,
            "type": 0,
            "platform": vps_cloudTrade["platform"]
        }
        response = self.send_post_request(
            logged_session,
            '/subcontrol/trader',
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "新增策略账号失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-VPS数据-新增策略账号")
    def test_dbquery_trader(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            user_accounts_cloudTrader_1 = var_manager.get_variable("user_accounts_cloudTrader_1")
            follow_trader = var_manager.get_variable("follow_trader")

            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM {follow_trader} WHERE account = %s",
                (user_accounts_cloudTrader_1,),
            )

            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            vps_id_cloudTrader = db_data[0]["id"]
            logging.info(f"新增策略账号ID: {vps_id_cloudTrader}")
            var_manager.set_runtime_variable("vps_id_cloudTrader", vps_id_cloudTrader)

            # 定义验证函数
            def verify_order_status():
                status = db_data[0]["status"]
                if status != 0:
                    pytest.fail(f"新增跟单账号状态status应为0（正常），实际状态为: {status}")
                euqit = db_data[0]["euqit"]
                if euqit == 0:
                    pytest.fail(f"账号净值euqit有钱，实际金额为: {euqit}")

            # 执行验证
            try:
                verify_order_status()
                allure.attach("账号基础信息校验通过", "成功详情", allure.attachment_type.TEXT)
            except AssertionError as e:
                allure.attach(str(e.args[0]), "账号基础信息校验失败", allure.attachment_type.TEXT)
                raise

    # ---------------------------
    # 云策略-云策略列表-获取云策略ID
    # ---------------------------
    @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("云策略-云策略列表-获取云策略ID")
    def test_cloudMaster_list(self, var_manager, logged_session):
        # 1. 发送获取云策略ID请求
        params = {
            "name": "565555",
            "groupId": "",
        }
        response = self.send_get_request(
            logged_session,
            '/mascontrol/cloudMaster/list',
            params=params
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "获取云策略ID失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )
        cloudMaster_id = response.extract_jsonpath("$.data.masterVOS[0].id")
        var_manager.set_runtime_variable("cloudMaster_id", cloudMaster_id)

    # ---------------------------
    # 账号管理-账号列表-批量挂靠VPS
    # ---------------------------
    @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-账号列表-批量挂靠VPS")
    def test_user_hangVps(self, var_manager, logged_session, db_transaction):
        # 1. 发送新增策略账号请求
        user_ids_cloudTrader_2 = var_manager.get_variable("user_ids_cloudTrader_2")
        user_ids_cloudTrader_3 = var_manager.get_variable("user_ids_cloudTrader_3")
        user_ids_cloudTrader_4 = var_manager.get_variable("user_ids_cloudTrader_4")
        vps_id_cloudTrader = var_manager.get_variable("vps_id_cloudTrader")
        vpsId = var_manager.get_variable("vpsId")
        data = {
            "accountType": 1,
            "vpsId": vpsId,
            "traderId": vps_id_cloudTrader,
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
            "commentType": "",
            "digits": 0,
            "traderUserIds": [
                user_ids_cloudTrader_2,
                user_ids_cloudTrader_3,
                user_ids_cloudTrader_4
            ]
        }
        response = self.send_post_request(
            logged_session,
            '/mascontrol/user/hangVps',
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "批量挂靠VPS失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

        # @pytest.mark.skip(reason=SKIP_REASON)

    @allure.title("数据库校验-VPS数据-批量新增跟单账号")
    def test_dbimport_addSlave(self, var_manager, db_transaction):
        # 1. 校验总用户数（需至少7个，才能取后6个）
        user_count = var_manager.get_variable("user_count", 0)
        if user_count < 7:
            pytest.fail(f"用户总数需至少为7，当前为{user_count}，无法提取后6个数据进行校验")

        # 2. 提取后6个账号（对应user_accounts_2到user_accounts_7）
        all_accounts = []
        for i in range(2, 8):  # 直接指定取第2到第7个账号（共6个）
            account = var_manager.get_variable(f"user_accounts_{i}")
            if not account:
                pytest.fail(f"未找到第{i}个账号（变量：user_accounts_{i}）")
            all_accounts.append(account)
        print(f"将校验的后6个账号：{all_accounts}")

        # 3. 初始化ID列表和计数器
        all_ids = []
        addslave_count = 0

        # 4. 逐个校验后6个账号的数据库记录
        for idx, account in enumerate(all_accounts, 1):  # idx从1开始（1-6，对应6个账号）
            with allure.step(f"验证第{idx}个账号（{account}）的数据库记录"):
                db_addslave_query = var_manager.get_variable("db_addslave_query")
                if not db_addslave_query or "table" not in db_addslave_query:
                    pytest.fail("数据库查询配置不完整（缺少table信息）")
                sql = f"SELECT * FROM {db_addslave_query['table']} WHERE account = %s"
                params = (account,)

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.wait_for_database_record(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    timeout=WAIT_TIMEOUT,  # 最多等30秒
                    poll_interval=POLL_INTERVAL,  # 每2秒查一次
                    order_by="create_time DESC"  # 按创建时间倒序
                )

                if not db_data:
                    pytest.fail(f"账号 {account} 在主表中未找到记录，请检查新增是否成功")

                # 提取当前账号的ID并保存到变量管理器
                vps_addslave_id = db_data[0]["id"]
                all_ids.append(vps_addslave_id)
                var_manager.set_runtime_variable(f"vps_addslave_ids_{idx}", vps_addslave_id)
                print(f"账号 {account} 的ID为：{vps_addslave_id}，已保存到变量 vps_addslave_ids_{idx}")

                # 校验账号状态和净值（核心业务规则）
                def verify_core_fields():
                    # 校验状态（0为正常）
                    status = db_data[0]["status"]
                    if status != 0:
                        pytest.fail(f"账号 {account} 状态异常：预期status=0（正常），实际={status}")
                    # 校验净值（非零）
                    euqit = db_data[0]["euqit"]
                    if euqit == 0:
                        pytest.fail(f"账号 {account} 净值异常：预期euqit≠0，实际={euqit}")

                # 执行核心校验并记录结果
                try:
                    verify_core_fields()
                    allure.attach(f"账号 {account} 主表字段校验通过", "校验结果", allure.attachment_type.TEXT)
                except AssertionError as e:
                    allure.attach(str(e), f"账号 {account} 主表字段校验失败", allure.attachment_type.TEXT)
                    raise

                # 校验订阅表记录（从表关联）
                if "table_subscribe" in db_addslave_query:
                    sql = f"SELECT * FROM {db_addslave_query['table_subscribe']} WHERE slave_account = %s"
                    params = (account,)
                    # 调用轮询等待方法（带时间范围过滤）
                    db_sub_data = self.wait_for_database_record(
                        db_transaction=db_transaction,
                        sql=sql,
                        params=params,
                        timeout=WAIT_TIMEOUT,  # 最多等30秒
                        poll_interval=POLL_INTERVAL,  # 每2秒查一次
                        order_by="create_time DESC"  # 按创建时间倒序
                    )

                    if not db_sub_data:
                        pytest.fail(f"账号 {account} 在订阅表中未找到关联记录")
                    # 校验订阅表中的账号与当前账号一致
                    slave_account = db_sub_data[0]["slave_account"]
                    if slave_account != account:
                        pytest.fail(f"订阅表账号不匹配：预期={account}，实际={slave_account}")
                    allure.attach(f"账号 {account} 订阅表关联校验通过", "校验结果", allure.attachment_type.TEXT)

        # 5. 保存总数量（供后续步骤使用）
        addslave_count = len(all_ids)
        var_manager.set_runtime_variable("addslave_count", addslave_count)
        print(f"后6个账号数据库校验完成，共提取{addslave_count}个ID，已保存到变量 addslave_count")

    # ---------------------------
    # 云策略-云策略列表-新增策略账号
    # ---------------------------
    @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("云策略-云策略列表-新增策略账号")
    def test_mascontrol_cloudTrader(self, var_manager, logged_session, db_transaction):
        # 1. 发送新增策略账号请求
        cloudMaster_id = var_manager.get_variable("cloudMaster_id")
        user_ids_cloudTrader_2 = var_manager.get_variable("user_ids_cloudTrader_2")
        data = {
            "cloudId": cloudMaster_id,
            "sourceType": 0,
            "remark": "新增云策略账号",
            "runningStatus": 0,
            "traderId": user_ids_cloudTrader_2,
            "managerIp": "",
            "managerAccount": "",
            "managerPassword": "",
            "account": "",
            "platform": "",
            "templateId": ""
        }
        response = self.send_post_request(
            logged_session,
            '/mascontrol/cloudTrader',
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "新增策略账号失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-VPS数据-新增策略账号")
    def test_dbquery_trader(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            user_ids_cloudTrader_2 = var_manager.get_variable("user_ids_cloudTrader_2")
            follow_trader = var_manager.get_variable("follow_trader")

            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM {follow_trader} WHERE account = %s",
                (user_ids_cloudTrader_2,),
            )

            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            vpsid_cloudTrader_2 = db_data[0]["id"]
            logging.info(f"新增策略账号ID: {vpsid_cloudTrader_2}")
            var_manager.set_runtime_variable("vpsid_cloudTrader_2", vpsid_cloudTrader_2)

            # 定义验证函数
            def verify_order_status():
                status = db_data[0]["status"]
                if status != 0:
                    pytest.fail(f"新增策略账号状态status应为0（正常），实际状态为: {status}")
                euqit = db_data[0]["euqit"]
                if euqit == 0:
                    pytest.fail(f"账号净值euqit有钱，实际金额为: {euqit}")

            # 执行验证
            try:
                verify_order_status()
                allure.attach("账号基础信息校验通过", "成功详情", allure.attachment_type.TEXT)
            except AssertionError as e:
                allure.attach(str(e.args[0]), "账号基础信息校验失败", allure.attachment_type.TEXT)
                raise
