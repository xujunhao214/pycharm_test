import time
import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuanMT5_1027.VAR.VAR import *
from lingkuanMT5_1027.conftest import var_manager
from lingkuanMT5_1027.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@pytest.mark.flaky(reruns=3, reruns_delay=5)
@allure.feature("数据管理-创建数据-为VPS测试准备")
class TestCreate(APITestBase):
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-账号列表-新增单个用户")
    def test_create_user(self, class_random_str, logged_session, var_manager, encrypted_password):
        # 1. 发送创建用户请求
        new_user = var_manager.get_variable("new_user")
        data = {
            "account": new_user["account"],
            "password": encrypted_password,
            "platform": new_user["platform"],
            "platformType": 1,
            "serverNode": new_user["serverNode"],
            "remark": new_user["remark"],
            "sort": "12",
            "vpsDescs": None
        }
        response = self.send_post_request(
            logged_session,
            "/mascontrol/user",
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "新增单个用户失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-账号列表-新增用户")
    def test_dbquery_user(self, class_random_str, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            new_user = var_manager.get_variable("new_user")

            # 优化后的数据库查询
            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM FOLLOW_TRADER_USER WHERE account = %s",
                (new_user["account"],),
            )

            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空")

            MT5vps_trader_user_id = db_data[0]["id"]
            print(f"输出：{MT5vps_trader_user_id}")
            logging.info(f"新增用户ID: {MT5vps_trader_user_id}")
            var_manager.set_runtime_variable("MT5vps_trader_user_id", MT5vps_trader_user_id)

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库查询-提取数据库平台ID数据")
    def test_dbquery_platform(self, class_random_str, var_manager, db_transaction):
        with allure.step("1. 提取数据库平台ID数据"):
            new_user = var_manager.get_variable("new_user")
            # 执行数据库查询
            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_platform WHERE server = %s",
                (new_user["platform"],)
            )

            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空")

            platformId = db_data[0]["id"]
            logging.info(f"平台ID: {platformId}")
            var_manager.set_runtime_variable("platformId", platformId)

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-账号列表-批量新增用户")
    def test_create_importuser(self, class_random_str, logged_session, var_manager):
        adduser = var_manager.get_variable("adduser")
        with open(adduser["csv_user_path"], 'rb') as f:
            csv_file = f.read()

        # 构造请求参数（文件上传使用files参数）
        files = {
            "file": ("账号列表数据.csv", csv_file, "text/csv")
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
    def test_dbquery_importuser(self, class_random_str, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            new_user = var_manager.get_variable("new_user")

            # 执行数据库查询
            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM FOLLOW_TRADER_USER WHERE remark = %s",
                (new_user["remarkimport"],),
                order_by="account ASC"
            )

            # 验证查询结果
            if not db_data:
                pytest.fail("数据库查询结果为空")

            # 提取MT5vps_user_ids和MT5vps_user_accounts（保持原有列表形式，用于后续判断）
            MT5vps_user_ids = [item["id"] for item in db_data]
            MT5vps_user_accounts = [item["account"] for item in db_data]

            print(f"\n提取到用户ID列表: {MT5vps_user_ids}")
            print(f"提取到用户账号列表: {MT5vps_user_accounts}")

            # 将列表拆分为单独的变量
            for i, (user_id, account) in enumerate(zip(MT5vps_user_ids, MT5vps_user_accounts), 1):
                var_manager.set_runtime_variable(f"MT5vps_user_ids_{i}", user_id)
                var_manager.set_runtime_variable(f"MT5vps_user_accounts_{i}", account)
                print(f"已设置变量: MT5vps_user_ids_{i}={user_id}, MT5vps_user_accounts_{i}={account}")

            # 保存总数，便于后续参数化使用
            var_manager.set_runtime_variable("MT5vps_user_count", len(MT5vps_user_ids))
            print(f"共提取{len(MT5vps_user_ids)}个用户数据")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-组别列表-新增VPS组别")
    def test_create_vpsgroup(self, class_random_str, logged_session, var_manager):
        add_vpsgroup = var_manager.get_variable("add_vpsgroup")
        data = {
            "name": add_vpsgroup["name"],
            "color": add_vpsgroup["color"],
            "sort": add_vpsgroup["sort"],
            "type": add_vpsgroup["type"]
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
    def test_dbquery_vpsgroup(self, class_random_str, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            add_vpsgroup = var_manager.get_variable("add_vpsgroup")
            # 执行数据库查询
            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_group WHERE name = %s",
                (add_vpsgroup["name"],),
            )

            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空")

            MT5vps_group_id = db_data[0]["id"]
            print(f"输出：{MT5vps_group_id}")
            logging.info(f"新增VPS组别ID: {MT5vps_group_id}")
            var_manager.set_runtime_variable("MT5vps_group_id", MT5vps_group_id)

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("平台管理-品种管理-添加品种")
    def test_create_variety(self, class_random_str, logged_session, var_manager):
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
            "templateName": add_variety["templateName"]
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
    def test_dbquery_variety(self, class_random_str, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            add_variety = var_manager.get_variable("add_variety")
            # 从变量中获取表名和模板名
            template_name = add_variety["templateName"]
            # 执行数据库查询
            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_variety WHERE template_name = %s",
                (template_name,)
            )

            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空")

            MT5vps_template_id = db_data[0]["template_id"]
            logging.info(f"新增品种id: {MT5vps_template_id}")
            var_manager.set_runtime_variable("MT5vps_template_id", MT5vps_template_id)

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("平台管理-品种管理-添加品种2")
    def test_create_variety2(self, class_random_str, logged_session, var_manager):
        # 1. 读取CSV文件
        add_variety = var_manager.get_variable("add_variety")
        with open(add_variety["csv_variety_path2"], 'rb') as f:
            # print(f'打印输出文件：{add_variety["csv_variety_path"]}')
            csv_file = f.read()

        # 2. 构造请求参数
        files = {
            "file": ("品种数据50.csv", csv_file, "text/csv")
        }
        data = {
            "templateName": add_variety["templateName3"]
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
    @allure.title("数据库校验-品种管理-添加品种2")
    def test_dbquery_variety2(self, class_random_str, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            add_variety = var_manager.get_variable("add_variety")
            # 从变量中获取表名和模板名
            template_name = add_variety["templateName3"]
            # 执行数据库查询
            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_variety WHERE template_name = %s",
                (template_name,)
            )

            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空")

            MT5vps_template_id2 = db_data[0]["template_id"]
            logging.info(f"新增品种id: {MT5vps_template_id2}")
            var_manager.set_runtime_variable("MT5vps_template_id2", MT5vps_template_id2)

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("VPS管理-VPS列表-校验服务器IP是否可用")
    def test_get_connect(self, class_random_str, logged_session, var_manager):
        # 1. 校验服务器IP是否可用
        add_VPS = var_manager.get_variable("add_VPS")
        response = self.send_get_request(
            logged_session,
            '/mascontrol/vps/connect',
            params={'ipAddress': add_VPS["ipAddress"]}
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "服务器IP不可用"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("VPS管理-VPS列表-获取可见用户信息")
    def test_get_user(self, class_random_str, logged_session, var_manager):
        # 1. 请求可见用户列表接口
        response = self.send_get_request(
            logged_session,
            '/sys/role/role'
        )

        # 2. 获取可见用户信息
        MT5vps_user_data = response.extract_jsonpath("$.data")
        logging.info(f"获取的可见用户信息：{MT5vps_user_data}")
        var_manager.set_runtime_variable("MT5vps_user_data", MT5vps_user_data)

    @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("VPS管理-VPS列表-新增vps")
    def test_create_vps(self, class_random_str, logged_session, var_manager):
        # 1. 发送新增vps请求
        add_VPS = var_manager.get_variable("add_VPS")
        MT5vps_user_data = var_manager.get_variable("MT5vps_user_data")
        MT5vps_group_id = var_manager.get_variable("MT5vps_group_id")
        data = {
            "ipAddress": add_VPS["ipAddress"],
            "name": "测试",
            "expiryDate": DATETIME_ENDTIME,
            "remark": "MT5测试VPS",
            "isOpen": 1,
            "isActive": 1,
            "roleList": MT5vps_user_data,
            "isSelectAccount": 1,
            "isMonitorRepair": 1,
            "isSpecializedRepair": 1,
            "isAutoRepair": 1,
            "groupId": f"{MT5vps_group_id}",
            "sort": 1000
        }
        response = self.send_post_request(
            logged_session,
            '/mascontrol/vps',
            json_data=data,

        )

        # 2. 判断是否添加成功
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-VPS列表-新增vps")
    def test_dbquery_vps(self, class_random_str, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            add_VPS = var_manager.get_variable("add_VPS")

            # 执行数据库查询
            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_vps WHERE ip_address=%s AND deleted=%s",
                (add_VPS["ipAddress"], add_VPS["deleted"],)
            )

            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空")

            MT5vps_list_id = db_data[0]["id"]
            logging.info(f"新增vps的id: {MT5vps_list_id}")
            var_manager.set_runtime_variable("MT5vps_list_id", MT5vps_list_id)

    @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("VPS管理-VPS列表-获取要复制的VPS的ID")
    def test_get_MT5vps_pageid(self, class_random_str, logged_session, var_manager):
        # 1. 请求VPS列表接口
        list_query = var_manager.get_variable("list_query")
        response = self.send_get_request(
            logged_session,
            'mascontrol/vps/page',
            params=list_query
        )

        # 2. 获取要复制的VPS的ID
        MT5vps_page_id = response.extract_jsonpath("$.data.list[1].id")
        logging.info(f"获取vps的id：{MT5vps_page_id}")
        var_manager.set_runtime_variable("MT5vps_page_id", MT5vps_page_id)

    @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("VPS管理-VPS列表-复制默认节点")
    def test_MT5vps_copyDefaultNode(self, class_random_str, logged_session, var_manager):
        # 1. 请求VPS复制默认节点接口
        MT5vps_page_id = var_manager.get_variable("MT5vps_page_id")
        MT5vps_list_id = var_manager.get_variable("MT5vps_list_id")
        data = {"oldVpsId": MT5vps_list_id, "newVpsId": [MT5vps_page_id]}
        response = self.send_put_request(
            logged_session,
            '/mascontrol/vps/copyDefaultNode',
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "服务器IP不可用"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-新增策略账号")
    def test_add_trader(self, class_random_str, var_manager, logged_session, encrypted_password):
        # 1. 发送新增策略账号请求
        new_user = var_manager.get_variable("new_user")
        data = {
            "account": new_user["account"],
            "password": encrypted_password,
            "platform": new_user["platform"],
            "remark": new_user["remark"],
            "platformId": new_user["platformId"],
            "platformType": 1,
            "type": 0,
            "templateId": 1,
            "followStatus": 1,
            "cfd": "",
            "forex": "",
            "followOrderRemark": 1,
            "fixedComment": new_user["fixedComment"],
            "commentType": new_user["commentType"],
            "digits": new_user["digits"]
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
    def test_dbquery_trader(self, class_random_str, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            new_user = var_manager.get_variable("new_user")
            # 执行数据库查询
            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_trader WHERE account = %s",
                (new_user["account"],)
            )

            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空")

            MT5vps_trader_id = db_data[0]["id"]
            logging.info(f"新增策略账号ID: {MT5vps_trader_id}")
            var_manager.set_runtime_variable("MT5vps_trader_id", MT5vps_trader_id)

        with allure.step("2. 数据校验"):
            status = db_data[0]["status"]
            assert status == 0, f"新增策略账号状态status应为0（正常），实际状态为: {status}"
            logging.info(f"新增策略账号状态status应为0（正常），实际状态为: {status}")

            euqit = db_data[0]["euqit"]
            assert euqit >= 0, f"账号净值euqit有钱，实际金额为: {euqit}"
            logging.info(f"账号净值euqit有钱，实际金额为: {euqit}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-新增跟单账号")
    def test_create_addSlave(self, class_random_str, var_manager, logged_session, encrypted_password):
        # 1. 发送新增策略账号请求
        new_user = var_manager.get_variable("new_user")
        MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
        MT5vps_trader_id = var_manager.get_variable("MT5vps_trader_id")
        data = {
            "traderId": MT5vps_trader_id,
            "platform": new_user["platform"],
            "account": MT5vps_user_accounts_1,
            "password": encrypted_password,
            "remark": new_user["remark"],
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
            "commentType": "",
            "digits": 0,
            "cfd": "",
            "forex": "",
            "abRemark": "",
            "platformType": 1
        }
        response = self.send_post_request(
            logged_session,
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
    def test_dbquery_addslave(self, class_random_str, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            MT5vps_user_accounts_1 = var_manager.get_variable("MT5vps_user_accounts_1")
            # 执行数据库查询
            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_trader WHERE account = %s",
                (MT5vps_user_accounts_1,)
            )

            if not db_data:
                pytest.fail("数据库查询结果为空")

            MT5vps_addslave_id = db_data[0]["id"]
            logging.info(f"新增跟单账号ID: {MT5vps_addslave_id}")
            var_manager.set_runtime_variable("MT5vps_addslave_id", MT5vps_addslave_id)

        with allure.step("2. 校验账号状态和净值"):
            status = db_data[0]["status"]
            assert status == 0, f"账号 {MT5vps_user_accounts_1} 状态异常：预期status=0，实际={status}"
            logging.info(f"账号 {MT5vps_user_accounts_1} 状态异常：预期status=0，实际={status}")

            euqit = db_data[0]["euqit"]
            assert euqit >= 0, f"账号 {MT5vps_user_accounts_1} 净值异常：预期euqit>=0，实际={euqit}"
            logging.info(f"账号 {MT5vps_user_accounts_1} 净值异常：预期euqit>=0，实际={euqit}")

            db_data2 = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_trader_subscribe WHERE slave_account = %s",
                (MT5vps_user_accounts_1,)
            )

            if not db_data2:
                pytest.fail("数据库查询结果为空")

            slave_account = db_data2[0]["slave_account"]
            assert slave_account == MT5vps_user_accounts_1, f"账号新增失败，新增账号：{MT5vps_user_accounts_1}  数据库账号:{slave_account}"
            logging.info(f"账号新增成功，新增账号：{MT5vps_user_accounts_1}  数据库账号:{slave_account}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库查询-获取券商名称和最大手数")
    def test_dbquery_platform(self, class_random_str, var_manager, db_transaction):
        with allure.step("1. 数据库的SQL查询"):
            new_user = var_manager.get_variable("new_user")
            sql = f""" SELECT * From follow_platform where server= %s """
            params = (
                new_user["platform"],
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.query_database(
                db_transaction=db_transaction,
                sql=sql,
                params=params
            )
        with allure.step("2. 提取数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空")

            max_lots = db_data[0]["max_lots"]
            var_manager.set_runtime_variable("max_lots", max_lots)

            broker_name = db_data[0]["broker_name"]
            var_manager.set_runtime_variable("broker_name", broker_name)

        with allure.step("3. 全局配置-数据库的SQL查询"):
            sql = f""" SELECT * From sys_params where param_name= %s """
            params = (
                "最大手数配置",
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.query_database(
                db_transaction=db_transaction,
                sql=sql,
                params=params
            )
        with allure.step("4. 提取数据"):
            if not db_data:
                pytest.fail("数据库查询结果为空")

            param_value = db_data[0]["param_value"]
            var_manager.set_runtime_variable("param_value", param_value)
