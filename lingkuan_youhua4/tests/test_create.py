import allure
import logging
import time
import pytest

from lingkuan_youhua4.conftest import var_manager

logger = logging.getLogger(__name__)


@allure.feature("账号管理-创建")
class TestCreate:
    @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("账号管理-账号列表-新增单个用户")
    def test_create_user(self, api_session, var_manager, logged_session, db_transaction):
        with allure.step("1. 发送创建用户请求"):
            new_user = var_manager.get_variable("new_user")
            response = api_session.post("/mascontrol/user", json=new_user)
            time.sleep(3)

        with allure.step("2. 验证响应状态码"):
            assert response.status_code == 200, f"创建用户失败: {response.text}"

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
            assert response.status_code == 200, f"创建用户失败: {response.text}"

        with allure.step("3. 验证JSON返回内容"):
            # 使用JSONPath提取并断言
            msg = response.extract_jsonpath("$.msg")
            assert msg == "success", "响应msg字段应为success"

    # @pytest.mark.skip(reason="该功能暂不需要")
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

    @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("账号管理-组别列表-新增VPS组别")
    def test_create_vpsgroup(self, api_session, var_manager, logged_session, db_transaction):
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

    @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("平台管理-品种管理-添加品种")
    def test_create_variety(self, api_session, var_manager, logged_session, db_transaction):
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
                cursor.execute(sql, (addvariety["templateName"],))
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
