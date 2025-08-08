# lingkuan_801UAT/tests/test_create.py
import time

import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuan_801UAT.VAR.VAR import *
from lingkuan_801UAT.commons.jsonpath_utils import *
from lingkuan_801UAT.conftest import var_manager
from lingkuan_801UAT.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("账号管理-创建账号-为云策略准备")
class TestCreate_cloudTrader(APITestBase):
    # ---------------------------
    # 账号管理-账号列表-批量新增用户-为云策略准备
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-账号列表-批量新增用户")
    def test_create_importuser(self, api_session, var_manager, logged_session):
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

            # 执行数据库查询
            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_trader_user WHERE remark = %s",
                (add_cloudTrader["remarkimport"],),
            )

            # 验证查询结果
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            # 提取user_ids_cloudTrader和user_accounts_cloudTrader（保持原有列表形式，用于后续判断）
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
    # 跟单软件看板-VPS数据-获取VPSID
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("跟单软件看板-VPS数据-获取VPSID")
    def test_get_vpsID(self, var_manager, logged_session):
        # 初始化 JSONPath 工具类
        json_utils = JsonPathUtils()

        with allure.step("1. 发送获取VPSID的请求接口"):
            params = {
                "name": "",
                "ip": "",
                "groupIds": "",
                "account": "",
                "type": "0",
            }
            response = self.send_get_request(
                logged_session,
                '/mascontrol/vps/listVps',
                params=params
            )
            # 将响应转换为字典
            response_json = response.json()

        with allure.step("2. 校验接口请求是否正确"):
            # 使用工具类的 assert_value 方法验证响应状态
            json_utils.assert_value(
                response_json,
                "$.msg",
                "success",
            )

        with allure.step("3. 提取数据"):
            # 先提取所有 VPS 列表（避开过滤语法）
            vps_list = json_utils.extract(
                response_json,
                "$.data.list"  # 只提取列表，不做过滤
            )

            # 手动过滤出 name 为 ^主VPS 的对象
            target_vps = None
            for vps in vps_list:
                if vps.get("name") == "39.99.145.155-Allon专用张家口3":
                    target_vps = vps
                    break

            # 校验是否找到目标 VPS
            assert target_vps is not None, "未找到 name 为 '39.99.145.155-Allon专用张家口3' 的 VPS 数据"

            # 提取 id
            vpsId = target_vps.get("id")
            assert vpsId is not None, "找到的 VPS 数据中没有 id 字段"

            # 存入变量管理器
            var_manager.set_runtime_variable("vpsId", vpsId)
            print(f"成功提取 VPS ID: {vpsId}")

    # ---------------------------
    # 跟单软件看板-VPS数据-新增策略账号-为云策略准备
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-新增策略账号")
    def test_add_trader(self, var_manager, logged_session, db_transaction, encrypted_password):
        # 1. 发送新增策略账号请求
        new_user = var_manager.get_variable("new_user")
        user_accounts_cloudTrader_1 = var_manager.get_variable("user_accounts_cloudTrader_1")
        data = {
            "account": user_accounts_cloudTrader_1,
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
            user_accounts_cloudTrader_1 = var_manager.get_variable("user_accounts_cloudTrader_1")

            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_trader WHERE account = %s",
                (user_accounts_cloudTrader_1,),
            )

            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            vps_id_cloudTrader = db_data[0]["id"]
            logging.info(f"新增策略账号ID: {vps_id_cloudTrader}")
            print(f"新增策略账号ID: {vps_id_cloudTrader}")
            var_manager.set_runtime_variable("vps_id_cloudTrader", vps_id_cloudTrader)

        # 定义验证函数
        with allure.step("2. 数据校验"):
            status = db_data[0]["status"]
            assert status == 0, f"新增策略账号状态status应为0（正常），实际状态为: {status}"
            logging.info(f"新增策略账号状态status应为0（正常），实际状态为: {status}")

            euqit = db_data[0]["euqit"]
            assert euqit > 0, f"账号净值euqit有钱，实际金额为: {euqit}"
            logging.info(f"账号净值euqit有钱，实际金额为: {euqit}")

    # ---------------------------
    # 账号管理-账号列表-批量挂靠VPS
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-账号列表-批量挂靠VPS跟单（后9个账号）")
    def test_user_hangVps(self, var_manager, logged_session, db_transaction):
        # 1. 获取后9个账号的ID（使用range直接循环索引1-9，对应第2到第10个账号）
        user_count_cloudTrader = var_manager.get_variable("user_count_cloudTrader")
        user_ids_later9 = []
        for i in range(2, user_count_cloudTrader + 1):  # 循环索引1-9（共9次）
            user_id_var_name = f"user_ids_cloudTrader_{i}"
            user_id = var_manager.get_variable(user_id_var_name)
            if not user_id:
                pytest.fail(f"未找到第{i}个账号ID（变量：{user_id_var_name}）")
            user_ids_later9.append(user_id)

        var_manager.set_runtime_variable("user_ids_later9", user_ids_later9)  # 保存后9个账号ID
        print(f"将批量挂靠的后9个账号ID：{user_ids_later9}")

        # 2. 发送批量挂靠VPS跟单请求（后续代码与之前一致）
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
            "traderUserIds": user_ids_later9  # 传入后9个账号ID
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

    # ---------------------------
    # 数据库校验-批量挂靠VPS跟单（后9个账号）
    # ---------------------------
    @allure.title("数据库校验-批量挂靠VPS跟单（后9个账号）")
    def test_dbimport_addSlave(self, var_manager, db_transaction):
        # 1. 获取后9个账号的账号名（使用range直接循环索引1-9）
        all_accounts_cloudTrader = []
        user_count_cloudTrader = var_manager.get_variable("user_count_cloudTrader")
        for i in range(2, user_count_cloudTrader + 1):  # 循环索引1-9（共9次）
            account_var_name = f"user_accounts_cloudTrader_{i}"
            account_cloudTrader = var_manager.get_variable(account_var_name)
            if not account_cloudTrader:
                pytest.fail(f"未找到第{i}个账号（变量：{account_var_name}）")
            all_accounts_cloudTrader.append(account_cloudTrader)
        print(f"将校验的后9个账号：{all_accounts_cloudTrader}")

        # 2. 逐个校验后9个账号的数据库记录（后续代码与之前一致）
        all_ids_cloudTrader = []
        for idx, account_cloudTrader in enumerate(all_accounts_cloudTrader, 1):  # idx从1到9
            with allure.step(f"验证第{idx}个账号（{account_cloudTrader}）的数据库记录"):
                # 数据库查询和校验逻辑与之前一致
                sql = f"SELECT * FROM follow_trader WHERE account = %s"
                params = (account_cloudTrader,)

                db_data = self.wait_for_database_record(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )
                print(f"验证第{idx}个账号（{account_cloudTrader}）的数据库记录")

                if not db_data:
                    pytest.fail(f"账号 {account_cloudTrader} 在主表中未找到记录")

                # 保存账号ID并校验状态/净值/订阅表（代码与之前一致）
                vps_cloudTrader_id = db_data[0]["id"]
                all_ids_cloudTrader.append(vps_cloudTrader_id)
                var_manager.set_runtime_variable(f"vps_cloudTrader_ids_{idx}", vps_cloudTrader_id)
                print(
                    f"账号 {account_cloudTrader} 的ID为：{vps_cloudTrader_id}，已保存到变量 vps_cloudTrader_ids_{idx}")

                # 校验账号状态和净值
                def verify_core_fields():
                    status = db_data[0]["status"]
                    if status != 0:
                        pytest.fail(f"账号 {account_cloudTrader} 状态异常：预期status=0，实际={status}")
                    euqit = db_data[0]["euqit"]
                    if euqit == 0:
                        pytest.fail(f"账号 {account_cloudTrader} 净值异常：预期euqit≠0，实际={euqit}")

                # 执行校验（代码与之前一致）
                try:
                    verify_core_fields()
                    allure.attach(f"账号 {account_cloudTrader} 主表字段校验通过", "校验结果",
                                  allure.attachment_type.TEXT)
                except AssertionError as e:
                    allure.attach(str(e), f"账号 {account_cloudTrader} 主表字段校验失败",
                                  allure.attachment_type.TEXT)
                    raise

                # 校验订阅表记录（代码与之前一致）
                sql = f"SELECT * FROM follow_trader_subscribe WHERE slave_account = %s"
                params = (account_cloudTrader,)
                db_sub_data = self.wait_for_database_record(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )

                if not db_sub_data:
                    pytest.fail(f"账号 {account_cloudTrader} 在订阅表中未找到关联记录")
                slave_account_cloudTrader = db_sub_data[0]["slave_account"]
                if slave_account_cloudTrader != account_cloudTrader:
                    pytest.fail(f"订阅表账号不匹配：预期={account_cloudTrader}，实际={slave_account_cloudTrader}")
                allure.attach(f"账号 {account_cloudTrader} 订阅表关联校验通过", "校验结果",
                              allure.attachment_type.TEXT)

        # 3. 保存总数量和ID列表（代码与之前一致）
        account_count = len(all_ids_cloudTrader)
        var_manager.set_runtime_variable("account_cloudTrader", account_count)
        var_manager.set_runtime_variable("all_vps_cloudTrader_ids", all_ids_cloudTrader)
        print(f"后9个账号数据库校验完成，共提取{account_count}个ID")

    # ---------------------------
    # 账号管理-组别列表-新增云策略组别
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-组别列表-新增云策略组别")
    def test_create_cloudgroup(self, api_session, var_manager, logged_session):
        add_cloudgroup = var_manager.get_variable("add_cloudgroup")
        data = {
            "name": add_cloudgroup["name"],
            "color": add_cloudgroup["color"],
            "sort": add_cloudgroup["sort"],
            "type": add_cloudgroup["type"]
        }

        # 1. 发送新增VPS组别请求
        response = self.send_post_request(
            api_session,
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

    # ---------------------------
    # 数据库校验-组别列表-新增云策略组别
    # ---------------------------
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

            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            cloudgroup_id = db_data[0]["id"]
            print(f"输出：{cloudgroup_id}")
            logging.info(f"新增云策略组别ID: {cloudgroup_id}")
            var_manager.set_runtime_variable("cloudgroup_id", cloudgroup_id)

    # ---------------------------
    # 云策略-云策略列表-新增云策略
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云策略列表-新增云策略")
    def test_create_cloudMaster(self, var_manager, logged_session):
        cloudgroup_id = var_manager.get_variable("cloudgroup_id")
        with allure.step("1. 发送新增云策略的请求接口"):
            data = {
                "name": "自动化测试",
                "type": 0,
                "remark": "",
                "status": 0,
                "groupId": cloudgroup_id,
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
        with allure.step("2. 校验数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，新增云策略账号失败")

        with allure.step("3. 提取数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，新增云策略账号失败")

            cloudMaster_id = db_data[0]['id']
            var_manager.set_runtime_variable("cloudMaster_id", cloudMaster_id)
            logging.info(f"新增云策略账号id是：{cloudMaster_id}")

    # ---------------------------
    # 云策略-云策略列表-新增策略账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云策略列表-新增策略账号")
    def test_mascontrol_cloudTrader(self, var_manager, logged_session):
        # 1. 发送新增策略账号请求
        cloudMaster_id = var_manager.get_variable("cloudMaster_id")
        vps_cloudTrader_ids_1 = var_manager.get_variable("vps_cloudTrader_ids_1")
        data = {
            "cloudId": cloudMaster_id,
            "sourceType": 0,
            "remark": "新增云策略账号",
            "runningStatus": 0,
            "followOrderRemark": 1,
            "traderId": vps_cloudTrader_ids_1,
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
            user_accounts_cloudTrader_2 = var_manager.get_variable("user_accounts_cloudTrader_2")

            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_cloud_trader WHERE account = %s",
                (user_accounts_cloudTrader_2,),
            )
        with allure.step("2. 校验数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，新增云策略账号失败")

        with allure.step("3. 提取数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，新增云策略账号失败")

            traderList_cloudTrader_2 = db_data[0]['id']
            var_manager.set_runtime_variable("traderList_cloudTrader_2", traderList_cloudTrader_2)
            logging.info(f"新增策略账号id是：{traderList_cloudTrader_2}")

    # ---------------------------
    # 云策略-云策略列表-新增manager策略账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云策略列表-新增manager策略账号")
    def test_manager_cloudTrader(self, var_manager, logged_session):
        # 1. 发送新增策略账号请求
        cloudMaster_id = var_manager.get_variable("cloudMaster_id")
        user_accounts_cloudTrader_3 = var_manager.get_variable("user_accounts_cloudTrader_3")
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
            "account": user_accounts_cloudTrader_3,
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
            user_accounts_cloudTrader_3 = var_manager.get_variable("user_accounts_cloudTrader_3")

            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_cloud_trader WHERE account = %s",
                (user_accounts_cloudTrader_3,)
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
            traderList_cloudTrader_3 = db_data[0]['id']
            var_manager.set_runtime_variable("traderList_cloudTrader_3", traderList_cloudTrader_3)
            logging.info(f"新增manager账号id是：{traderList_cloudTrader_3}")

    # ---------------------------
    # 云策略-云策略列表-新增云策略跟单账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云策略列表-新增云策略跟单账号")
    def test_cloudTrader_cloudBatchAdd(self, var_manager, logged_session):
        # 1. 发送新增策略账号请求
        cloudMaster_id = var_manager.get_variable("cloudMaster_id")
        vps_cloudTrader_ids_3 = var_manager.get_variable("vps_cloudTrader_ids_3")
        traderList_cloudTrader_3 = var_manager.get_variable("traderList_cloudTrader_3")
        user_accounts_cloudTrader_3 = var_manager.get_variable("user_accounts_cloudTrader_3")
        data = [
            {
                "traderList": [
                    vps_cloudTrader_ids_3
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
            '/mascontrol/cloudTrader/cloudBatchAdd',
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "新增云策略跟单账号失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-云策略列表-新增云策略跟单账号")
    def test_dbcloudTrader_cloudBatchAdd(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            user_accounts_cloudTrader_4 = var_manager.get_variable("user_accounts_cloudTrader_4")

            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_cloud_trader WHERE account = %s",
                (user_accounts_cloudTrader_4,)
            )

        with allure.step("2. 提取数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空，新增云策略账号失败")

            traderList_cloudTrader_4 = db_data[0]['id']
            var_manager.set_runtime_variable("traderList_cloudTrader_4", traderList_cloudTrader_4)
            logging.info(f"新增云策略跟单账号id是：{traderList_cloudTrader_4}")

    # ---------------------------
    # 平台管理-品种管理-添加品种
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("平台管理-品种管理-添加品种")
    def test_create_variety(self, api_session, var_manager, logged_session):
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
            api_session,
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

    # ---------------------------
    # 数据库校验-品种管理-添加品种
    # ---------------------------
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

            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            template_id2 = db_data[0]["template_id"]
            logging.info(f"新增品种id: {template_id2}")
            var_manager.set_runtime_variable("template_id2", template_id2)
