# lingkuan_825/tests/test_create.py
import time
import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuan_825.VAR.VAR import *
from lingkuan_825.commons.jsonpath_utils import *
from lingkuan_825.conftest import var_manager
from lingkuan_825.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("数据管理-创建数据-为云策略准备")
class TestCreate_cloudTrader(APITestBase):
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-账号列表-批量新增用户")
    def test_create_importuser(self, logged_session, var_manager):
        add_cloudTrader = var_manager.get_variable("add_cloudTrader")
        with open(add_cloudTrader["csv_user_path"], 'rb') as f:
            csv_file = f.read()

        # 构造请求参数（文件上传使用files参数）
        files = {
            "file": ("云策略账号数据.csv", csv_file, "text/csv")
        }

        # 1. 发送创建用户请求
        response = self.send_post_request(
            logged_session,
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
    def test_dbquery_importuser(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            add_cloudTrader = var_manager.get_variable("add_cloudTrader")

            # 执行数据库查询
            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_trader_user WHERE remark = %s",
                (add_cloudTrader["remarkimport"],),
                order_by="account ASC"
            )

        with allure.step("2. 提取数据库数据"):
            # 验证查询结果
            if not db_data:
                pytest.fail("数据库查询结果为空，订单可能没有入库")

            # 提取cloudTrader_user_ids和cloudTrader_user_accounts（保持原有列表形式，用于后续判断）
            cloudTrader_user_ids = [item["id"] for item in db_data]
            cloudTrader_user_accounts = [item["account"] for item in db_data]

            print(f"\n提取到用户ID列表: {cloudTrader_user_ids}")
            print(f"提取到用户账号列表: {cloudTrader_user_accounts}")

            # 将列表拆分为单独的变量
            for i, (user_id_cloudTrader, cloudTrader_account) in enumerate(
                    zip(cloudTrader_user_ids, cloudTrader_user_accounts), 1):
                var_manager.set_runtime_variable(f"cloudTrader_user_ids_{i}", user_id_cloudTrader)
                var_manager.set_runtime_variable(f"cloudTrader_user_accounts_{i}", cloudTrader_account)
                print(
                    f"已设置变量: cloudTrader_user_ids_{i}={user_id_cloudTrader}, cloudTrader_user_accounts_{i}={cloudTrader_account}")

            # 保存总数，便于后续参数化使用
            var_manager.set_runtime_variable("cloudTrader_user_count", len(cloudTrader_user_ids))
            print(f"共提取{len(cloudTrader_user_ids)}个用户数据")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库查询-获取VPSID")
    def test_get_vpsID(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库数据"):
            ip_address = var_manager.get_variable("IP_ADDRESS")

            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_vps WHERE ip_address = %s",
                (ip_address,)
            )

        with allure.step("2. 提取数据库数据"):
            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空，订单可能没有入库")

            vpsId = db_data[0]["id"]
            # 存入变量管理器
            var_manager.set_runtime_variable("vpsId", vpsId)
            print(f"成功提取 VPS ID: {vpsId}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-新增策略账号")
    def test_add_trader(self, var_manager, logged_session, encrypted_password):
        # 1. 发送新增策略账号请求
        new_user = var_manager.get_variable("new_user")
        cloudTrader_user_accounts_1 = var_manager.get_variable("cloudTrader_user_accounts_1")
        data = {
            "account": cloudTrader_user_accounts_1,
            "password": encrypted_password,
            "remark": new_user["remark"],
            "followStatus": 1,
            "templateId": 1,
            "type": 0,
            "cfd": "",
            "forex": "",
            "followOrderRemark": 1,
            "fixedComment": new_user["fixedComment"],
            "commentType": new_user["commentType"],
            "digits": new_user["digits"],
            "platformId": new_user["platformId"],
            "platform": new_user["platform"]
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
            cloudTrader_user_accounts_1 = var_manager.get_variable("cloudTrader_user_accounts_1")

            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_trader WHERE account = %s",
                (cloudTrader_user_accounts_1,),
            )

        with allure.step("2. 提取数据库数据"):
            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空，订单可能没有入库")

            cloudTrader_vps_id = db_data[0]["id"]
            logging.info(f"新增策略账号ID: {cloudTrader_vps_id}")
            print(f"新增策略账号ID: {cloudTrader_vps_id}")
            var_manager.set_runtime_variable("cloudTrader_vps_id", cloudTrader_vps_id)

        # 定义验证函数
        with allure.step("2. 数据校验"):
            status = db_data[0]["status"]
            assert status == 0, f"新增策略账号状态status应为0（正常），实际状态为: {status}"
            logging.info(f"新增策略账号状态status应为0（正常），实际状态为: {status}")

            euqit = db_data[0]["euqit"]
            assert euqit > 0, f"账号净值euqit有钱，实际金额为: {euqit}"
            logging.info(f"账号净值euqit有钱，实际金额为: {euqit}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-账号列表-批量挂靠VPS跟单（后9个账号）")
    def test_user_hangVps(self, var_manager, logged_session):
        # 1. 获取后9个账号的ID（使用range直接循环索引1-9，对应第2到第10个账号）
        cloudTrader_user_count = var_manager.get_variable("cloudTrader_user_count")
        cloudTrader_user_ids_later9 = []
        for i in range(2, cloudTrader_user_count + 1):  # 循环索引1-9（共9次）
            user_id_var_name = f"cloudTrader_user_ids_{i}"
            user_id = var_manager.get_variable(user_id_var_name)
            if not user_id:
                pytest.fail(f"未找到第{i}个账号ID（变量：{user_id_var_name}）")
            cloudTrader_user_ids_later9.append(user_id)

        var_manager.set_runtime_variable("cloudTrader_user_ids_later9", cloudTrader_user_ids_later9)  # 保存后9个账号ID
        print(f"将批量挂靠的后9个账号ID：{cloudTrader_user_ids_later9}")

        # 2. 发送批量挂靠VPS跟单请求（后续代码与之前一致）
        cloudTrader_vps_id = var_manager.get_variable("cloudTrader_vps_id")
        vpsId = var_manager.get_variable("vpsId")
        data = {
            "accountType": 1,
            "vpsId": vpsId,
            "traderId": cloudTrader_vps_id,
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
            "traderUserIds": cloudTrader_user_ids_later9  # 传入后9个账号ID
        }

        response = self.send_post_request(
            logged_session,
            '/mascontrol/user/hangVps',
            json_data=data
        )

        # 3. 验证响应（后续代码与之前一致）
        self.assert_response_status(
            response,
            200,
            "批量挂靠VPS（后9个账号）失败")
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success")

    @allure.title("数据库校验-批量挂靠VPS跟单（后9个账号）")
    def test_dbimport_addSlave(self, var_manager, db_transaction):
        # 1. 获取后9个账号的账号名（使用range直接循环索引1-9）
        all_accounts_cloudTrader = []
        cloudTrader_user_count = var_manager.get_variable("cloudTrader_user_count")
        for i in range(2, cloudTrader_user_count + 1):  # 循环索引1-9（共9次）
            cloudTrader_account_var_name = f"cloudTrader_user_accounts_{i}"
            cloudTrader_account = var_manager.get_variable(cloudTrader_account_var_name)
            if not cloudTrader_account:
                pytest.fail(f"未找到第{i}个账号（变量：{cloudTrader_account_var_name}）")
            all_accounts_cloudTrader.append(cloudTrader_account)
        print(f"\n将校验的后9个账号：{all_accounts_cloudTrader}")

        # 2. 逐个校验后9个账号的数据库记录（后续代码与之前一致）
        all_ids_cloudTrader = []
        for idx, cloudTrader_account in enumerate(all_accounts_cloudTrader, 1):  # idx从1到9
            with allure.step(f"验证第{idx}个账号（{cloudTrader_account}）的数据库记录"):
                # 数据库查询和校验逻辑与之前一致
                sql = f"SELECT * FROM follow_trader WHERE account = %s"
                params = (cloudTrader_account,)

                db_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    order_by="account ASC"

                )
                print(f"验证第{idx}个账号（{cloudTrader_account}）的数据库记录")

                if not db_data:
                    pytest.fail(f"账号 {cloudTrader_account} 在主表中未找到记录")

                # 保存账号ID并校验状态/净值/订阅表（代码与之前一致）
                cloudTrader_vps_id = db_data[0]["id"]
                all_ids_cloudTrader.append(cloudTrader_vps_id)
                var_manager.set_runtime_variable(f"cloudTrader_vps_ids_{idx}", cloudTrader_vps_id)
                print(
                    f"账号 {cloudTrader_account} 的ID为：{cloudTrader_vps_id}，已保存到变量 cloudTrader_vps_ids_{idx}")

            with allure.step("校验账号状态和净值"):
                status = db_data[0]["status"]
                assert status == 0, f"账号 {cloudTrader_account} 状态异常：预期status=0，实际={status}"
                logging.info(f"账号 {cloudTrader_account} 状态异常：预期status=0，实际={status}")

                euqit = db_data[0]["euqit"]
                assert euqit > 0, f"账号 {cloudTrader_account} 净值异常：预期euqit≠0，实际={euqit}"
                logging.info(f"账号 {cloudTrader_account} 净值异常：预期euqit≠0，实际={euqit}")

                # 校验订阅表记录（代码与之前一致）
                sql = f"SELECT * FROM follow_trader_subscribe WHERE slave_account = %s"
                params = (cloudTrader_account,)
                db_sub_data = self.query_database_with_time(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    order_by="slave_account ASC"
                )

                if not db_sub_data:
                    pytest.fail(f"账号 {cloudTrader_account} 在订阅表中未找到关联记录")
                slave_cloudTrader_account = db_sub_data[0]["slave_account"]
                assert slave_cloudTrader_account == cloudTrader_account, f"账号 {cloudTrader_account} 在订阅表中的关联账号异常"
                logging.info(f"账号 {cloudTrader_account} 订阅表关联校验通过")

        # 3. 保存总数量和ID列表（代码与之前一致）
        account_count = len(all_ids_cloudTrader)
        var_manager.set_runtime_variable("cloudTrader_account", account_count)
        var_manager.set_runtime_variable("cloudTrader_all_vps_ids", all_ids_cloudTrader)
        print(f"后9个账号数据库校验完成，共提取{account_count}个ID")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-组别列表-新增云策略组别")
    def test_create_cloudgroup(self, logged_session, var_manager):
        add_cloudgroup = var_manager.get_variable("add_cloudgroup")
        data = {
            "name": add_cloudgroup["name"],
            "color": add_cloudgroup["color"],
            "sort": add_cloudgroup["sort"],
            "type": add_cloudgroup["type"]
        }

        # 1. 发送新增VPS组别请求
        response = self.send_post_request(
            logged_session,
            "/mascontrol/group",
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "新增云策略组别失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-组别列表-新增云策略组别")
    def test_dbquery_cloudgroup(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            add_cloudgroup = var_manager.get_variable("add_cloudgroup")

            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_group WHERE name = %s",
                (add_cloudgroup["name"],),
            )

        with allure.step("2. 提取数据库中的值"):
            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空，订单可能没有入库")

            cloudTrader_group_id = db_data[0]["id"]
            print(f"输出：{cloudTrader_group_id}")
            logging.info(f"新增云策略组别ID: {cloudTrader_group_id}")
            var_manager.set_runtime_variable("cloudTrader_group_id", cloudTrader_group_id)

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云策略列表-新增云策略")
    def test_create_cloudMaster(self, var_manager, logged_session):
        cloudTrader_group_id = var_manager.get_variable("cloudTrader_group_id")
        with allure.step("1. 发送新增云策略的请求接口"):
            data = {
                "name": "自动化测试",
                "type": 0,
                "remark": "",
                "status": 0,
                "groupId": cloudTrader_group_id,
                "sort": 100,
                "isMonitorRepair": 1
            }
            response = self.send_post_request(
                logged_session,
                '/mascontrol/cloudMaster',
                json_data=data
            )

        with allure.step("2. 校验接口请求是否正确"):
            # 使用工具类的 assert_value 方法验证响应状态
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-云策略列表-新增云策略")
    def test_dbcreate_cloudTrader(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_cloud_master WHERE name = %s",
                ("自动化测试",),
            )

        with allure.step("2. 提取数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，新增云策略账号失败")

            cloudMaster_id = db_data[0]['id']
            var_manager.set_runtime_variable("cloudMaster_id", cloudMaster_id)
            logging.info(f"新增云策略账号id是：{cloudMaster_id}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云策略列表-新增策略账号")
    def test_mascontrol_cloudTrader(self, var_manager, logged_session):
        # 1. 发送新增策略账号请求
        cloudMaster_id = var_manager.get_variable("cloudMaster_id")
        cloudTrader_vps_ids_1 = var_manager.get_variable("cloudTrader_vps_ids_1")
        data = {
            "cloudId": cloudMaster_id,
            "sourceType": 0,
            "remark": "新增云策略账号",
            "runningStatus": 0,
            "followOrderRemark": 1,
            "traderId": cloudTrader_vps_ids_1,
            "managerIp": "",
            "managerAccount": "",
            "managerPassword": "",
            "account": "",
            "platform": "",
            "templateId": "",
            "fixedComment": "ceshi",
            "commentType": "",
            "digits": ""
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
    @allure.title("数据库校验-云策略列表-新增策略账号")
    def test_dbmascontrol_cloudTrader(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")

            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_cloud_trader WHERE account = %s",
                (cloudTrader_user_accounts_2,),
            )

        with allure.step("2. 提取数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，新增云策略账号失败")

            cloudTrader_traderList_2 = db_data[0]['id']
            var_manager.set_runtime_variable("cloudTrader_traderList_2", cloudTrader_traderList_2)
            logging.info(f"新增策略账号id是：{cloudTrader_traderList_2}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.retry(n=3, delay=5)
    @allure.title("云策略-云策略列表-新增manager策略账号")
    def test_manager_cloudTrader(self, var_manager, logged_session):
        # 1. 发送新增策略账号请求
        cloudMaster_id = var_manager.get_variable("cloudMaster_id")
        cloudTrader_user_accounts_3 = var_manager.get_variable("cloudTrader_user_accounts_3")
        new_user = var_manager.get_variable("new_user")
        manager = var_manager.get_variable("manager")
        data = {
            "cloudId": cloudMaster_id,
            "sourceType": 1,
            "remark": "新增manager账号",
            "runningStatus": 0,
            "followOrderRemark": 1,
            "traderId": "",
            "managerIp": manager["managerIp"],
            "managerAccount": manager["managerAccount"],
            "managerPassword": manager["managerPassword"],
            "account": cloudTrader_user_accounts_3,
            "platform": new_user["platform"],
            "templateId": 1,
            "fixedComment": new_user["fixedComment"],
            "commentType": "",
            "digits": ""
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
            "新增manager策略账号失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-云策略列表-新增manager账号")
    def test_dbmanager_trader(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            cloudTrader_user_accounts_3 = var_manager.get_variable("cloudTrader_user_accounts_3")

            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_cloud_trader WHERE account = %s",
                (cloudTrader_user_accounts_3,)
            )

        with allure.step("2. 验证数据库数据"):
            manager = var_manager.get_variable("manager")
            managerdb = db_data[0]['manager_ip']
            self.assert_values_equal(
                manager['managerIp'],
                managerdb,
                f"新增manager账号服务器是：{managerdb} 应该是：{manager['managerIp']}"
            )
            logging.info(f"新增manager账号服务器是：{managerdb} 应该是：{manager['managerIp']}")

        with allure.step("3. 提取数据"):
            cloudTrader_traderList_3 = db_data[0]['id']
            var_manager.set_runtime_variable("cloudTrader_traderList_3", cloudTrader_traderList_3)
            logging.info(f"新增manager账号id是：{cloudTrader_traderList_3}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云策略列表-新增云跟单账号")
    def test_cloudTrader_BatchAdd(self, var_manager, logged_session):
        # 1. 发送新增策略账号请求
        cloudMaster_id = var_manager.get_variable("cloudMaster_id")
        cloudTrader_vps_ids_3 = var_manager.get_variable("cloudTrader_vps_ids_3")
        cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")
        cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
        data = [
            {
                "traderList": [
                    cloudTrader_vps_ids_3
                ],
                "cloudId": cloudMaster_id,
                "masterId": cloudTrader_traderList_2,
                "masterAccount": cloudTrader_user_accounts_2,
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
            '/mascontrol/cloudTrader/cloudBatchAdd',
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "新增云跟单账号失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-云策略列表-新增云跟单账号")
    def test_dbcloudTrader_BatchAdd(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
            cloudMaster_id = var_manager.get_variable("cloudMaster_id")

            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_cloud_trader WHERE account = %s and cloud_id = %s",
                (cloudTrader_user_accounts_4, cloudMaster_id,)
            )

        with allure.step("2. 提取数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，新增跟单账号失败")

            cloudTrader_traderList_4 = db_data[0]['id']
            var_manager.set_runtime_variable("cloudTrader_traderList_4", cloudTrader_traderList_4)
            logging.info(f"新增云跟单账号id是：{cloudTrader_traderList_4}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("平台管理-品种管理-添加品种")
    def test_create_variety(self, logged_session, var_manager):
        # 1. 读取CSV文件
        add_variety = var_manager.get_variable("add_variety")
        with open(add_variety["csv_variety_path"], 'rb') as f:
            # print(f'打印输出文件：{add_variety["csv_variety_path"]}')
            csv_file = f.read()

        # 2. 构造请求参数
        files = {
            "file": ("品种数据300.csv", csv_file, "text/csv")
        }
        data = {
            "templateName": add_variety["templateName2"]
        }

        # 1. 添加品种
        response = self.send_post_request(
            logged_session,
            '/mascontrol/variety/addTemplate',
            data=data,
            files=files
        )

        # 2. 判断是否添加成功
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-品种管理-添加品种")
    def test_dbquery_variety(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            add_variety = var_manager.get_variable("add_variety")
            # 从变量中获取表名和模板名
            template_name = add_variety["templateName2"]
            # 使用f-string正确格式化SQL语句
            sql = f"SELECT * FROM follow_variety WHERE template_name = %s"
            params = (template_name,)
            # 执行带时间范围的查询
            db_data = self.query_database(db_transaction, sql, params)

        with allure.step("2. 提取数据"):
            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空，订单可能没有入库")

            cloudTrader_template_id1 = db_data[0]["template_id"]
            logging.info(f"新增品种id: {cloudTrader_template_id1}")
            var_manager.set_runtime_variable("cloudTrader_template_id1", cloudTrader_template_id1)

    @allure.title("云策略-云策略列表-新增云策略-手动下单")
    def test_create_handcloudMaster(self, var_manager, logged_session):
        cloudTrader_group_id = var_manager.get_variable("cloudTrader_group_id")
        with allure.step("1. 发送新增云策略的请求接口"):
            data = {
                "name": "自动化测试_手动下单",
                "type": 1,
                "remark": "",
                "status": 0,
                "groupId": cloudTrader_group_id,
                "sort": 100,
                "isMonitorRepair": 1,
                "isAutoRepair": 1
            }
            response = self.send_post_request(
                logged_session,
                '/mascontrol/cloudMaster',
                json_data=data
            )

        with allure.step("2. 校验接口请求是否正确"):
            # 使用工具类的 assert_value 方法验证响应状态
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-云策略列表-新增云策略-手动下单")
    def test_dbcreate_handcloudMaster(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_cloud_master WHERE name = %s",
                ("自动化测试_手动下单",),
            )

        with allure.step("2. 提取数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，新增云策略账号失败")

            cloudMaster_id_hand = db_data[0]['id']
            var_manager.set_runtime_variable("cloudMaster_id_hand", cloudMaster_id_hand)
            logging.info(f"新增云策略账号id是：{cloudMaster_id_hand}")

    @allure.title("云策略-云策略列表-新增云跟单-手动下单")
    def test_create_handcloudBatchAdd(self, var_manager, logged_session):
        cloudTrader_vps_ids_3 = var_manager.get_variable("cloudTrader_vps_ids_3")
        cloudMaster_id_hand = var_manager.get_variable("cloudMaster_id_hand")
        with allure.step("1. 发送新增云跟单的请求接口"):
            data = [
                {
                    "traderList": [
                        cloudTrader_vps_ids_3
                    ],
                    "cloudId": cloudMaster_id_hand,
                    "masterId": "",
                    "masterAccount": "",
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
                    "followTraderIds": [],
                    "sort": "100",
                    "remark": "测试手动下单"
                }
            ]
            response = self.send_post_request(
                logged_session,
                '/mascontrol/cloudTrader/cloudBatchAdd',
                json_data=data
            )

        with allure.step("2. 校验接口请求是否正确"):
            # 使用工具类的 assert_value 方法验证响应状态
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-云策略列表-新增云跟单-手动下单")
    def test_dbcreate_handcloudBatchAdd(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
            cloudMaster_id_hand = var_manager.get_variable("cloudMaster_id_hand")
            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_cloud_trader WHERE account = %s and cloud_id = %s",
                (cloudTrader_user_accounts_4, cloudMaster_id_hand,),
            )
        with allure.step("2. 校验数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，新增云跟单账号失败")

            cloudTrader_traderList_handid = db_data[0]['id']
            var_manager.set_runtime_variable("cloudTrader_traderList_handid", cloudTrader_traderList_handid)
            logging.info(f"新增云跟单账号id是：{cloudTrader_traderList_handid}")
