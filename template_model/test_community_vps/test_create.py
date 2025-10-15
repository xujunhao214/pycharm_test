import time
import pytest
import logging
import allure
from typing import Dict, Any, List
from template_model.VAR.VAR import *
from template_model.conftest import var_manager
from template_model.commons.api_vpsbase import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("数据管理-创建数据-为VPS测试准备")
class TestCreate(APIVPSBase):
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库查询-提取数据库平台ID数据")
    def test_dbquery_platform(self, var_manager, dbvps_transaction):
        with allure.step("1. 提取数据库平台ID数据"):
            new_user = var_manager.get_variable("new_user")
            # 执行数据库查询
            db_data = self.query_database(
                dbvps_transaction,
                f"SELECT * FROM follow_platform WHERE server = %s",
                (new_user["platform"],)
            )

            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            platformId = db_data[0]["id"]
            logging.info(f"平台ID: {platformId}")
            var_manager.set_runtime_variable("platformId", platformId)

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-账号列表-批量新增用户")
    def test_create_importuser(self, logged_vps, var_manager):
        adduser = var_manager.get_variable("adduser")
        with open(adduser["csv_user_path"], 'rb') as f:
            csv_file = f.read()

        # 构造请求参数（文件上传使用files参数）
        files = {
            "file": ("账号列表数据.csv", csv_file, "text/csv")
        }

        # 1. 发送创建用户请求
        response = self.send_post_request(
            logged_vps,
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

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-账号列表-批量新增用户")
    def test_dbquery_importuser(self, var_manager, dbvps_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            new_user = var_manager.get_variable("new_user")

            # 执行数据库查询
            db_data = self.query_database(
                dbvps_transaction,
                f"SELECT * FROM FOLLOW_TRADER_USER WHERE remark = %s",
                (new_user["remarkimport"],),
                order_by="account ASC"
            )

            # 验证查询结果
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            # 提取vps_user_ids和vps_user_accounts（保持原有列表形式，用于后续判断）
            vps_user_ids = [item["id"] for item in db_data]
            vps_user_accounts = [item["account"] for item in db_data]

            print(f"提取到用户ID列表: {vps_user_ids}")
            print(f"提取到用户账号列表: {vps_user_accounts}")

            # 将列表拆分为单独的变量
            for i, (user_id, account) in enumerate(zip(vps_user_ids, vps_user_accounts), 1):
                var_manager.set_runtime_variable(f"vps_user_ids_{i}", user_id)
                var_manager.set_runtime_variable(f"vps_user_accounts_{i}", account)
                print(f"已设置变量: vps_user_ids_{i}={user_id}, vps_user_accounts_{i}={account}")

            # 保存总数，便于后续参数化使用
            var_manager.set_runtime_variable("vps_user_count", len(vps_user_ids))
            print(f"共提取{len(vps_user_ids)}个用户数据")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-组别列表-新增VPS组别")
    def test_create_vpsgroup(self, logged_vps, var_manager):
        add_vpsgroup = var_manager.get_variable("add_vpsgroup")
        data = {
            "name": add_vpsgroup["name"],
            "color": add_vpsgroup["color"],
            "sort": add_vpsgroup["sort"],
            "type": add_vpsgroup["type"]
        }

        # 1. 发送新增VPS组别请求
        response = self.send_post_request(
            logged_vps,
            "/mascontrol/group",
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "新增VPS组别失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-组别列表-新增VPS组别")
    def test_dbquery_vpsgroup(self, var_manager, dbvps_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            add_vpsgroup = var_manager.get_variable("add_vpsgroup")
            # 执行数据库查询
            db_data = self.query_database(
                dbvps_transaction,
                f"SELECT * FROM follow_group WHERE name = %s",
                (add_vpsgroup["name"],),
            )

            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            vps_group_id = db_data[0]["id"]
            print(f"输出：{vps_group_id}")
            logging.info(f"新增VPS组别ID: {vps_group_id}")
            var_manager.set_runtime_variable("vps_group_id", vps_group_id)

    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-新增策略账号")
    def test_add_trader(self, var_manager, logged_vps, encrypted_password):
        # 1. 发送新增策略账号请求
        new_user = var_manager.get_variable("new_user")
        vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
        data = {
            "type": 0,
            "account": vps_user_accounts_1,
            "password": encrypted_password,
            "platform": new_user["platform"],
            "remark": "",
            "platformId": "",
            "template_modelId": 1,
            "followStatus": 1,
            "cfd": "",
            "forex": "",
            "followOrderRemark": 1,
            "fixedComment": "",
            "commentType": "",
            "digits": "",
            "platformType": 0
        }
        response = self.send_post_request(
            logged_vps,
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
    def test_dbquery_trader(self, var_manager, dbvps_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
            # 执行数据库查询
            db_data = self.query_database(
                dbvps_transaction,
                f"SELECT * FROM follow_trader WHERE account = %s",
                (vps_user_accounts_1,)
            )

            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            vps_trader_id = db_data[0]["id"]
            logging.info(f"新增策略账号ID: {vps_trader_id}")
            var_manager.set_runtime_variable("vps_trader_id", vps_trader_id)

        with allure.step("2. 数据校验"):
            status = db_data[0]["status"]
            assert status == 0, f"新增策略账号状态status应为0（正常），实际状态为: {status}"
            logging.info(f"新增策略账号状态status应为0（正常），实际状态为: {status}")

            euqit = db_data[0]["euqit"]
            assert euqit > 0, f"账号净值euqit有钱，实际金额为: {euqit}"
            logging.info(f"账号净值euqit有钱，实际金额为: {euqit}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-新增跟单账号")
    def test_create_addSlave(self, var_manager, logged_vps, encrypted_password):
        # 1. 发送新增策略账号请求
        new_user = var_manager.get_variable("new_user")
        vps_user_accounts_2 = var_manager.get_variable("vps_user_accounts_2")
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        data = {
            "traderId": vps_trader_id,
            "platform": new_user["platform"],
            "account": vps_user_accounts_2,
            "password": encrypted_password,
            "remark": "",
            "followDirection": 0,
            "followMode": 1,
            "remainder": 0,
            "followParam": 1,
            "placedType": 0,
            "template_modelId": 1,
            "followStatus": 1,
            "followOpen": 1,
            "followClose": 1,
            "followRep": 0,
            "fixedComment": "",
            "commentType": "",
            "digits": 0,
            "cfd": "",
            "forex": "",
            "abRemark": "",
            "platformType": 0
        }
        response = self.send_post_request(
            logged_vps,
            '/subcontrol/follow/addSlave',
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "创建用户失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-VPS数据-新增跟单账号")
    def test_dbquery_addslave(self, var_manager, dbvps_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            vps_user_accounts_2 = var_manager.get_variable("vps_user_accounts_2")
            # 执行数据库查询
            db_data = self.query_database(
                dbvps_transaction,
                f"SELECT * FROM follow_trader WHERE account = %s",
                (vps_user_accounts_2,)
            )

            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            vps_addslave_id = db_data[0]["id"]
            logging.info(f"新增跟单账号ID: {vps_addslave_id}")
            var_manager.set_runtime_variable("vps_addslave_id", vps_addslave_id)

        with allure.step("2. 校验账号状态和净值"):
            status = db_data[0]["status"]
            assert status == 0, f"账号 {vps_user_accounts_2} 状态异常：预期status=0，实际={status}"
            logging.info(f"账号 {vps_user_accounts_2} 状态异常：预期status=0，实际={status}")

            euqit = db_data[0]["euqit"]
            assert euqit > 0, f"账号 {vps_user_accounts_2} 净值异常：预期euqit≠0，实际={euqit}"
            logging.info(f"账号 {vps_user_accounts_2} 净值异常：预期euqit≠0，实际={euqit}")

            db_data2 = self.query_database(
                dbvps_transaction,
                f"SELECT * FROM follow_trader_subscribe WHERE slave_account = %s",
                (vps_user_accounts_2,)
            )

            if not db_data2:
                pytest.fail("数据库查询结果为空，无法提取数据")

            slave_account = db_data2[0]["slave_account"]
            assert slave_account == vps_user_accounts_2, f"账号新增失败，新增账号：{vps_user_accounts_2}  数据库账号:{slave_account}"
            logging.info(f"账号新增成功，新增账号：{vps_user_accounts_2}  数据库账号:{slave_account}")
