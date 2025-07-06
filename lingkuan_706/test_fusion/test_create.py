# lingkuan_706/tests/test_create.py
import time

import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuan_706.VAR.VAR import *
from lingkuan_706.conftest import var_manager
from lingkuan_706.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("账号管理-创建基本信息")
class TestCreate(APITestBase):
    # ---------------------------
    # 账号管理-账号列表-新增单个用户
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-账号列表-新增单个用户")
    def test_create_user(self, api_session, var_manager, logged_session, db_transaction):
        # 1. 发送创建用户请求
        new_user = var_manager.get_variable("new_user")
        data = {
            "account": new_user["account"],
            "password": new_user["password"],
            "platform": new_user["platform"],
            "accountType": "0",
            "serverNode": new_user["serverNode"],
            "remark": new_user["remark"],
            "sort": "12",
            "vpsDescs": []
        }
        response = self.send_post_request(
            api_session,
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

    # ---------------------------
    # 数据库校验-账号列表-新增用户
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-账号列表-新增用户")
    def test_dbquery_user(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            db_query = var_manager.get_variable("db_query")
            sql = f"SELECT * FROM {db_query['table']} WHERE account = %s"
            params = (db_query["account"],)

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="create_time",  # 按创建时间过滤
                time_range=MYSQL_TIME,  # 只查前后1分钟的数据
                timeout=WAIT_TIMEOUT,  # 最多等60秒
                poll_interval=POLL_INTERVAL,  # 每2秒查一次
                order_by="create_time DESC"  # 按创建时间倒序
            )

            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            trader_user_id = db_data[0]["id"]
            print(f"输出：{trader_user_id}")
            logging.info(f"新增用户ID: {trader_user_id}")
            var_manager.set_runtime_variable("trader_user_id", trader_user_id)
            time.sleep(90)

    # ---------------------------
    # 账号管理-账号列表-批量新增用户
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-账号列表-批量新增用户")
    def test_create_importuser(self, api_session, var_manager, logged_session, db_transaction):
        """验证数据库"""
        adduser = var_manager.get_variable("adduser")
        with open(adduser["csv_user_path"], 'rb') as f:
            csv_file = f.read()

        # 构造请求参数（文件上传使用files参数）
        files = {
            "file": ("账号列表数据.csv", csv_file, "text/csv")
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
            db_query = var_manager.get_variable("db_query")
            sql = f"SELECT * FROM {db_query['table']} WHERE remark = %s"
            params = (db_query["remark"],)
            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="create_time",  # 按创建时间过滤
                time_range=MYSQL_TIME,  # 只查前后1分钟的数据
                timeout=WAIT_TIMEOUT,  # 最多等60秒
                poll_interval=POLL_INTERVAL,  # 每2秒查一次
                order_by="create_time DESC"  # 按创建时间倒序
            )

            # 验证查询结果
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            # 提取user_ids和user_accounts（保持原有列表形式，用于后续判断）
            user_ids = [item["id"] for item in db_data]
            user_accounts = [item["account"] for item in db_data]

            print(f"提取到用户ID列表: {user_ids}")
            print(f"提取到用户账号列表: {user_accounts}")

            # 将列表拆分为单独的变量
            for i, (user_id, account) in enumerate(zip(user_ids, user_accounts), 1):
                var_manager.set_runtime_variable(f"user_ids_{i}", user_id)
                var_manager.set_runtime_variable(f"user_accounts_{i}", account)
                print(f"已设置变量: user_ids_{i}={user_id}, user_accounts_{i}={account}")

            # 保存总数，便于后续参数化使用
            var_manager.set_runtime_variable("user_count", len(user_ids))
            print(f"共提取{len(user_ids)}个用户数据")

    # ---------------------------
    # 账号管理-组别列表-新增VPS组别
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-组别列表-新增VPS组别")
    def test_create_vpsgroup(self, api_session, var_manager, logged_session):
        """验证数据库"""
        add_vpsgroup = var_manager.get_variable("add_vpsgroup")
        data = {
            "name": add_vpsgroup["name"],
            "color": add_vpsgroup["color"],
            "sort": add_vpsgroup["sort"],
            "type": 1
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
            "新增VPS组别失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # ---------------------------
    # 数据库校验-组别列表-新增VPS组别
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-组别列表-新增VPS组别")
    def test_dbquery_vpsgroup(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            db_group = var_manager.get_variable("db_group")
            sql = f"SELECT * FROM {db_group['table']} WHERE name = %s"
            params = (db_group["name"],)

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="create_time",  # 按创建时间过滤
                time_range=MYSQL_TIME,  # 只查前后1分钟的数据
                timeout=WAIT_TIMEOUT,  # 最多等60秒
                poll_interval=POLL_INTERVAL,  # 每2秒查一次
                order_by="create_time DESC"  # 按创建时间倒序
            )

            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            group_id = db_data[0]["id"]
            print(f"输出：{group_id}")
            logging.info(f"新增VPS组别ID: {group_id}")
            var_manager.set_runtime_variable("group_id", group_id)

    # ---------------------------
    # 平台管理-品种管理-添加品种
    # ---------------------------
    @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("平台管理-品种管理-添加品种")
    def test_create_variety(self, api_session, var_manager, logged_session):
        # 1. 读取CSV文件
        add_variety = var_manager.get_variable("add_variety")
        with open(add_variety["csv_variety_path"], 'rb') as f:
            # print(f'打印输出文件：{add_variety["csv_variety_path"]}')
            csv_file = f.read()

        # 2. 构造请求参数
        files = {
            "file": ("品种数据100.csv", csv_file, "text/csv")
        }
        data = {
            "templateName": add_variety["templateName"]
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
    @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-品种管理-添加品种")
    def test_dbquery_variety(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            add_variety = var_manager.get_variable("add_variety")
            # 从变量中获取表名和模板名
            table_name = add_variety["table"]
            template_name = add_variety["templateName"]
            # 使用f-string正确格式化SQL语句
            sql = f"SELECT * FROM {table_name} WHERE template_name = %s"
            params = (template_name,)
            # 执行带时间范围的查询
            db_data = self.query_database(
                db_transaction,
                sql,
                params,
                time_field="create_time",
                time_range_minutes=MYSQL_TIME
            )

            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            template_id = db_data[0]["template_id"]
            logging.info(f"新增品种id: {template_id}")
            var_manager.set_runtime_variable("template_id", template_id)

    # ---------------------------
    # 平台管理-品种管理-添加品种2
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("平台管理-品种管理-添加品种2")
    def test_create_variety2(self, api_session, var_manager, logged_session):
        # 1. 读取CSV文件
        add_variety = var_manager.get_variable("add_variety")
        with open(add_variety["csv_variety_path2"], 'rb') as f:
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
    # 数据库校验-品种管理-添加品种2
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-品种管理-添加品种2")
    def test_dbquery_variety2(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            add_variety = var_manager.get_variable("add_variety")
            # 从变量中获取表名和模板名
            table_name = add_variety["table"]
            template_name2 = add_variety["templateName2"]
            # 使用f-string正确格式化SQL语句
            sql = f"SELECT * FROM {table_name} WHERE template_name = %s"
            params = (template_name2,)
            # 执行带时间范围的查询
            db_data = self.query_database(
                db_transaction,
                sql,
                params,
                time_field="create_time",
                time_range_minutes=MYSQL_TIME
            )

            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            template_id2 = db_data[0]["template_id"]
            logging.info(f"新增品种id2: {template_id2}")
            var_manager.set_runtime_variable("template_id2", template_id2)

    # ---------------------------
    # VPS管理-VPS列表-校验服务器IP是否可用
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("VPS管理-VPS列表-校验服务器IP是否可用")
    def test_get_connect(self, api_session, var_manager, logged_session):
        # 1. 校验服务器IP是否可用
        add_VPS = var_manager.get_variable("add_VPS")
        response = self.send_get_request(
            api_session,
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

    # ---------------------------
    # VPS管理-VPS列表-获取可见用户信息
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("VPS管理-VPS列表-获取可见用户信息")
    def test_get_user(self, api_session, var_manager, logged_session):
        # 1. 请求可见用户列表接口
        response = self.send_get_request(
            api_session,
            '/sys/user/user'
        )

        # 2. 获取可见用户信息
        user_data = response.extract_jsonpath("$.data[1]")
        logging.info(f"获取的可见用户信息：{user_data}")
        var_manager.set_runtime_variable("user_data", user_data)

    # ---------------------------
    # VPS管理-VPS列表-新增vps
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("VPS管理-VPS列表-新增vps")
    def test_create_vps(self, api_session, var_manager, logged_session):
        # 1. 发送新增vps请求
        add_VPS = var_manager.get_variable("add_VPS")
        user_data = var_manager.get_variable("user_data")
        group_id = var_manager.get_variable("group_id")
        data = {
            "ipAddress": add_VPS["ipAddress"],
            "name": "测试",
            "expiryDate": DATETIME_ENDTIME,
            "remark": "测试",
            "isOpen": 1,
            "isActive": 1,
            "userList": [user_data],
            "isSelectAccount": 1,
            "isMonitorRepair": 1,
            "isSpecializedRepair": 1,
            "isAutoRepair": 1,
            "groupId": f"{group_id}",
            "sort": 120
        }
        response = self.send_post_request(
            api_session,
            '/mascontrol/vps',
            json_data=data
        )

        # 2. 判断是否添加成功
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # ---------------------------
    # 数据库校验-VPS列表-新增vps
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-VPS列表-新增vps")
    def test_dbquery_vps(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            add_VPS = var_manager.get_variable("add_VPS")

            # 定义数据库查询条件
            sql = f"SELECT * FROM {add_VPS['table']} WHERE ip_address=%s AND deleted=%s"
            params = (add_VPS["ipAddress"], add_VPS["deleted"])

            # 使用智能等待
            db_data = self.wait_for_database_record(
                db_transaction,
                sql,
                params
            )

            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            vps_list_id = db_data[0]["id"]
            logging.info(f"新增vps的id: {vps_list_id}")
            var_manager.set_runtime_variable("vps_list_id", vps_list_id)

    # ---------------------------
    # VPS管理-VPS列表-获取要复制的VPS的ID
    # ---------------------------
    @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("VPS管理-VPS列表-获取要复制的VPS的ID")
    def test_get_vps_pageid(self, api_session, var_manager, logged_session):
        # 1. 请求VPS列表接口
        list_query = var_manager.get_variable("list_query")
        response = self.send_get_request(
            api_session,
            'mascontrol/vps/page',
            params=list_query
        )

        # 2. 获取要复制的VPS的ID
        vps_page_id = response.extract_jsonpath("$.data.list[1].id")
        logging.info(f"获取vps的id：{vps_page_id}")
        var_manager.set_runtime_variable("vps_page_id", vps_page_id)

    # ---------------------------
    # VPS管理-VPS列表-复制默认节点
    # ---------------------------
    @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("VPS管理-VPS列表-复制默认节点")
    def test_vps_copyDefaultNode(self, api_session, var_manager, logged_session):
        # 1. 请求VPS复制默认节点接口
        vps_page_id = var_manager.get_variable("vps_page_id")
        vps_list_id = var_manager.get_variable("vps_list_id")
        data = {"oldVpsId": vps_list_id, "newVpsId": [vps_page_id]}
        response = self.send_put_request(
            api_session,
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

    # ---------------------------
    # 跟单软件看板-VPS数据-新增策略账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-新增策略账号")
    def test_add_trader(self, var_manager, logged_session, db_transaction):
        # 1. 发送新增策略账号请求
        vps_trader = var_manager.get_variable("vps_trader")
        data = {
            "account": vps_trader["account"],
            "password": vps_trader["password"],
            "remark": vps_trader["remark"],
            "followStatus": 1,
            "templateId": 1,
            "type": 0,
            "platform": vps_trader["platform"]
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
            db_trader_query = var_manager.get_variable("db_trader_query")

            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM {db_trader_query['table']} WHERE account = %s",
                (db_trader_query["account"],),
                time_field="create_time",
                time_range_minutes=MYSQL_TIME
            )

            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            vps_trader_id = db_data[0]["id"]
            logging.info(f"新增策略账号ID: {vps_trader_id}")
            var_manager.set_runtime_variable("vps_trader_id", vps_trader_id)

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
    # 跟单软件看板-VPS数据-新增跟单账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-新增跟单账号")
    def test_create_addSlave(self, var_manager, logged_session, db_transaction):
        # 1. 发送新增策略账号请求
        add_Slave = var_manager.get_variable("add_Slave")
        user_accounts_1 = var_manager.get_variable("user_accounts_1")
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        password = var_manager.get_variable("password")
        data = {
            "traderId": vps_trader_id,
            "platform": add_Slave["platform"],
            "account": user_accounts_1,
            "password": password,
            "remark": add_Slave["remark"],
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
            "fixedComment": add_Slave["fixedComment"],
            "commentType": 2,
            "digits": 0,
            "cfd": "",
            "forex": "",
            "abRemark": ""
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
    def test_dbquery_addslave(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            db_addslave_query = var_manager.get_variable("db_addslave_query")
            user_accounts_1 = var_manager.get_variable("user_accounts_1")

            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM {db_addslave_query['table']} WHERE account = %s",
                (user_accounts_1,),
                time_field="create_time",
                time_range_minutes=MYSQL_TIME
            )

            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            vps_addslave_id = db_data[0]["id"]
            logging.info(f"新增跟单账号ID: {vps_addslave_id}")
            var_manager.set_runtime_variable("vps_addslave_id", vps_addslave_id)

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

            db_data2 = self.query_database(
                db_transaction,
                f"SELECT * FROM {db_addslave_query['table_subscribe']} WHERE slave_account = %s",
                (user_accounts_1,),
                time_field="create_time",
                time_range_minutes=MYSQL_TIME
            )

            if not db_data2:
                pytest.fail("数据库查询结果为空，无法提取数据")

            slave_account = db_data2[0]["slave_account"]
            if slave_account != user_accounts_1:
                pytest.fail(f"账号新增失败，新增账号：{user_accounts_1}  数据库账号:{slave_account}")
