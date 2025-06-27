import allure
import logging
import time


@allure.feature("账号管理")
class TestUser:

    @allure.story("账号管理-新增单个用户")
    def test_create_user(self, api_session, var_manager, logged_session, db_transaction):
        """测试新增用户接口并验证数据库"""
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

        with allure.step("4. 查询数据库验证"):
            db_query = var_manager.get_variable("db_query")
            with db_transaction.cursor() as cursor:
                sql = f'SELECT * FROM {db_query["table"]} WHERE account = %s'
                cursor.execute(sql, (db_query["account"],))
                db_data = cursor.fetchall()

                # 验证数据库结果
                assert db_data, "数据库查询结果为空"

                # 提取并保存用户ID到动态变量
                user_id = db_data[0]["id"]
                var_manager.set_variable("user_id", user_id)
                # 后续用例可通过var_manager.get_variable("user_id")获取
                logging.info(f"新增用户ID: {user_id}")
