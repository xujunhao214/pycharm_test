import time
from template.commons.api_base import APITestBase
import allure
import logging
import pytest
from template.VAR.VAR import *
from template.commons.jsonpath_utils import *
from template.commons.random_generator import *


@allure.feature("账号管理")
class Test_create:
    @allure.story("创建交易员账号")
    class Test_trader(APITestBase):
        # 实例化JsonPath工具类（全局复用）
        json_utils = JsonPathUtils()

        @allure.title("账号管理-交易员账号-绑定交易员-用户列表-提取用户id")
        def test_user_list(self, var_manager, logged_session):
            target_email = "xujunhao@163.com"

            with allure.step("1. 构造参数并发送GET请求"):
                params = {
                    "_t": current_timestamp_seconds,
                    "column": "createTime",
                    "field": "id,,username,nickname,email,phone",
                    "pageNo": "1",
                    "pageSize": "20",
                    "order": "desc"
                }

                response = self.send_get_request(
                    logged_session,
                    '/sys/user/list',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step(f"3. 提取用户ID"):
                all_users = self.json_utils.extract(
                    data=response.json(),
                    expression="$.result.records[*]",
                    multi_match=True,
                    default=[]
                )

                user_id = None
                if not all_users:
                    assert False, f"提取用户列表失败：$.result.records为空，接口返回异常"

                for user in all_users:
                    user_email = user.get("email")
                    if user_email and user_email.lower() == target_email.lower():
                        user_id = user.get("id")
                        break

                assert user_id is not None, f"未找到email={target_email}的用户，请检查用户是否存在或分页参数"
                logging.info(f"提取用户ID成功 | email={target_email} | user_id={user_id}")
                var_manager.set_runtime_variable("trader_user_id", user_id)
                allure.attach(
                    name="用户ID",
                    body=str(user_id),
                    attachment_type=allure.attachment_type.TEXT
                )