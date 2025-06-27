# lingkuan_youhua10/tests/test_create.py
import allure
import logging
import time
import pytest
from lingkuan_youhua10.VAR.VAR import *
from lingkuan_youhua10.conftest import var_manager
from lingkuan_youhua10.commons.wait_utils import wait_for_condition

logger = logging.getLogger(__name__)


@allure.feature("账号管理-创建")
class TestCreate:
    # ---------------------------
    # 账号管理-账号列表-新增单个用户
    # ---------------------------
    @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("账号管理-账号列表-新增单个用户")
    def test_create_user(self, api_session, var_manager, logged_session, db_transaction):
        with allure.step("1. 发送创建用户请求"):
            new_user = var_manager.get_variable("new_user")
            response = api_session.post("/mascontrol/user", json=new_user)
            time.sleep(3)

        with allure.step("2. 验证响应状态码"):
            assert response.status_code == 200, f"新增单个用户失败: {response.text}"

        with allure.step("3. 验证JSON返回内容"):
            # 使用JSONPath提取并断言
            msg = response.extract_jsonpath("$.msg")
            assert msg == "success", "响应msg字段应为success"

    @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("账号管理-账号列表-批量新增用户")
    def test_create_importuser(self, api_session, var_manager, logged_session, db_transaction):
        """验证数据库"""
        adduser = var_manager.get_variable("adduser")
        with open(adduser["csv_user_path"], 'rb') as f:
            csv_file = f.read()

        # 2. 构造请求参数（文件上传使用files参数）
        files = {
            "file": ("品种数据100.csv", csv_file, "text/csv")
        }
        with allure.step("1. 发送创建用户请求"):
            new_user = var_manager.get_variable("new_user")
            response = api_session.post("/mascontrol/user/import", files=files, json=new_user)
            time.sleep(3)

        with allure.step("2. 验证响应状态码"):
            assert response.status_code == 200, f"批量新增用户失败: {response.text}"

        with allure.step("3. 验证JSON返回内容"):
            # 使用JSONPath提取并断言
            msg = response.extract_jsonpath("$.msg")
            assert msg == "success", "响应msg字段应为success"

    @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("数据库校验-账号列表-新增用户")
    def test_dbquery_user(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            db_query = var_manager.get_variable("db_query")
            with db_transaction.cursor() as cursor:
                sql = f'SELECT * FROM {db_query["table"]} WHERE account = %s'
                cursor.execute(sql, (db_query["account"],))
                db_data = cursor.fetchall()
                # 调试日志 - 查看查询结果
                logging.info(f"数据库查询结果: {db_data}")

                # 提取数据库中的值
                if db_data:
                    user_id = db_data[0]["id"]
                    print(f"输出：{user_id}")
                    logging.info(f"新增用户ID: {user_id}")
                    var_manager.set_runtime_variable("user_id", user_id)
                else:
                    pytest.fail("数据库查询结果为空，无法提取数据")

    # ---------------------------
    # 账号管理-组别列表-新增VPS组别
    # ---------------------------

    @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("账号管理-组别列表-新增VPS组别")
    def test_create_vpsgroup(self, api_session, var_manager, logged_session):
        """验证数据库"""
        add_vpsgroup = var_manager.get_variable("add_vpsgroup")
        with allure.step("1. 发送新增VPS组别请求"):
            new_user = var_manager.get_variable("new_user")
            response = api_session.post("/mascontrol/group", json=add_vpsgroup)
            time.sleep(3)

        with allure.step("2. 验证响应状态码"):
            assert response.status_code == 200, f"新增VPS组别失败: {response.text}"

        with allure.step("3. 验证JSON返回内容"):
            # 使用JSONPath提取并断言
            msg = response.extract_jsonpath("$.msg")
            assert msg == "success", "响应msg字段应为success"

    @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("数据库校验-组别列表-新增VPS组别")
    def test_dbquery_vpsgroup(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            db_group = var_manager.get_variable("db_group")
            with db_transaction.cursor() as cursor:
                sql = f'SELECT * FROM {db_group["table"]} WHERE name = %s'
                cursor.execute(sql, (db_group["name"],))
                db_data = cursor.fetchall()
                # 调试日志 - 查看查询结果
                logging.info(f"数据库查询结果: {db_data}")

                # 提取数据库中的值
                if db_data:
                    group_id = db_data[0]["id"]
                    print(f"输出：{group_id}")
                    logging.info(f"新增VPS组别ID: {group_id}")
                    var_manager.set_runtime_variable("group_id", group_id)
                else:
                    pytest.fail("数据库查询结果为空，无法提取数据")

    # ---------------------------
    # 平台管理-品种管理-添加品种
    # ---------------------------

    @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("平台管理-品种管理-添加品种")
    def test_create_variety(self, api_session, var_manager, logged_session):
        # 1. 读取CSV文件
        addvariety = var_manager.get_variable("addvariety")
        with open(addvariety["csv_variety_path"], 'rb') as f:
            csv_file = f.read()

        # 2. 构造请求参数（文件上传使用files参数）
        files = {
            "file": ("品种数据100.csv", csv_file, "text/csv")
        }
        data = {
            "templateName": addvariety["templateName"]
        }
        with allure.step("1. 添加品种"):
            response = api_session.post('/mascontrol/variety/addTemplate', files=files, data=data)
        with allure.step("2. 判断是否添加成功"):
            msg = response.extract_jsonpath("$.msg")
            logging.info(f"断言：预期：success 实际：{msg}")
            assert "success" == msg
            time.sleep(3)

    @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("数据库校验-品种管理-添加品种")
    def test_dbquery_variety(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            addvariety = var_manager.get_variable("addvariety")
            # 查询数据库获取数据
            with db_transaction.cursor() as cursor:
                sql = 'SELECT * FROM follow_variety WHERE template_name=%s'
                cursor.execute(sql, (addvariety["template_name"],))
                # 获取数据库查询结果

                db_data = cursor.fetchall()

                # 调试日志 - 查看查询结果
                logging.info(f"数据库查询结果: {db_data}")
                time.sleep(10)

            # 提取数据库中的值
            if db_data:
                template_id = db_data[0]["template_id"]
                logging.info(f"新增品种id: {template_id}")
                var_manager.set_runtime_variable("template_id", template_id)
            else:
                pytest.fail("数据库查询结果为空，无法提取数据")

    # ---------------------------
    # VPS管理-VPS列表-添加VPS
    # ---------------------------
    @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("VPS管理-VPS列表-校验服务器IP是否可用")
    def test_get_connect(self, api_session, var_manager, logged_session):
        with allure.step("1. 校验服务器IP是否可用"):
            add_VPS = var_manager.get_variable("add_VPS")
            response = api_session.get('/mascontrol/vps/connect', params={'ipAddress': add_VPS["ipAddress"]})

        with allure.step("2. 验证响应状态码"):
            assert response.status_code == 200, f"服务器IP不可用: {response.text}"

        with allure.step("3. 验证JSON返回内容"):
            # 使用JSONPath提取并断言
            msg = response.extract_jsonpath("$.msg")
            assert msg == "success", "响应msg字段应为success"

    # 获取可见用户列表
    @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("VPS管理-VPS列表-获取可见用户信息")
    def test_get_user(self, api_session, var_manager, logged_session):
        with allure.step("1. 请求可见用户列表接口"):
            response = api_session.get('/sys/user/user')

        with allure.step("2. 获取可见用户信息"):
            user_data = response.extract_jsonpath("$.data[1]")
            logging.info(f"获取的可见用户信息：{user_data}")
            var_manager.set_runtime_variable("user_data", user_data)

    @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("VPS管理-VPS列表-新增vps")
    def test_create_vps(self, api_session, var_manager, logged_session):
        with allure.step("1. 发送新增vps请求"):
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
            response = api_session.post('/mascontrol/vps', json=data)
        with allure.step("2. 判断是否添加成功"):
            msg = response.extract_jsonpath("$.msg")
            logging.info(f"断言：预期：success 实际：{msg}")
            assert "success" == msg

    @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("数据库校验-VPS列表-新增vps")
    def test_dbquery_vps(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            add_VPS = var_manager.get_variable("add_VPS")

            # 定义数据库查询条件函数
            def check_db():
                with db_transaction.cursor() as cursor:
                    sql = f'select * from {add_VPS["table"]} where ip_address=%s and deleted=%s'
                    cursor.execute(sql, (add_VPS["ipAddress"], add_VPS["deleted"]))
                    # 获取数据库查询结果
                    db_data = cursor.fetchall()
                    # 调试日志 - 查看查询结果
                    logging.info(f"数据库查询结果: {db_data}")
                    return db_data

            # 使用智能等待并记录Allure步骤
            db_data = wait_for_condition(
                condition=check_db,
                timeout=30,
                poll_interval=2,
                error_message=f"数据库查询超时: {add_VPS['ipAddress']} 未找到",
                step_title=f"等待数据 {add_VPS['ipAddress']} 出现在数据库中。"
            )
            # 提取数据库中的值
            if db_data:
                vps_list_id = db_data[0]["id"]
                logging.info(f"新增vps的id: {vps_list_id}")
                var_manager.set_runtime_variable("vps_list_id", vps_list_id)
            else:
                pytest.fail("数据库查询结果为空，无法提取数据")

    # 获取要复制的VPS的ID
    @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("VPS管理-VPS列表-获取要复制的VPS的ID")
    def test_get_vps_pageid(self, api_session, var_manager, logged_session):
        with allure.step("1. 请求VPS列表接口"):
            list_query = var_manager.get_variable("list_query")
            response = api_session.get('mascontrol/vps/page', params=list_query)

        with allure.step("2. 获取要复制的VPS的ID"):
            vps_page_id = response.extract_jsonpath("$.data.list[1].id")
            logging.info(f"获取vps的id：{vps_page_id}")
            var_manager.set_runtime_variable("vps_page_id", vps_page_id)

    # 复制默认节点
    @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("VPS管理-VPS列表-复制默认节点")
    def test_vps_copyDefaultNode(self, api_session, var_manager, logged_session):
        with allure.step("1. 请求VPS复制默认节点接口"):
            vps_page_id = var_manager.get_variable("vps_page_id")
            vps_list_id = var_manager.get_variable("vps_list_id")
            data = {"oldVpsId": vps_list_id, "newVpsId": [vps_page_id]}
            response = api_session.put('/mascontrol/vps/copyDefaultNode', json=data)

        with allure.step("2. 验证响应状态码"):
            assert response.status_code == 200, f"服务器IP不可用: {response.text}"

        with allure.step("3. 验证JSON返回内容"):
            # 使用JSONPath提取并断言
            msg = response.extract_jsonpath("$.msg")
            assert msg == "success", "响应msg字段应为success"
