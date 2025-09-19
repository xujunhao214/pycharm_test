import time
from template.commons.api_base import APITestBase, CompareOp
import allure
import logging
import json
import pytest
from template.VAR.VAR import *
from template.commons.jsonpath_utils import *
from template.commons.random_generator import *


@allure.feature("账号管理-跟随者账户")
class Test_create:
    @allure.story("跟随者账户查询校验")
    class Test_trader(APITestBase):
        # 实例化JsonPath工具类（全局复用）
        json_utils = JsonPathUtils()

        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
        @allure.title("跟单用户查询")
        def test_query_username(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                login_config = var_manager.get_variable("login_config")
                username_log = login_config["username"]
                params = {
                    "_t": current_timestamp_seconds,
                    "username": username_log,
                    "pageNo": 1,
                    "pageSize": 20,
                    "status": "NORMAL,AUDIT"
                }
                response = self.send_get_request(
                    logged_session,
                    '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step("3. 查询校验"):
                username_list = self.json_utils.extract(
                    response.json(),
                    "$.result.data.records[*].username",
                    default=[],
                    multi_match=True
                )

                if not username_list:
                    pytest.fail("查询结果为空，不符合预期")
                else:
                    attach_body = f"跟单用户查询：{username_log}，返回 {len(username_list)} 条记录，username值如下：\n" + \
                                  "\n".join([f"第 {idx + 1} 条：{s}" for idx, s in enumerate(username_list)])

                allure.attach(
                    body=attach_body,
                    name=f"跟单用户-{username_log}:查询结果",
                    attachment_type="text/plain"
                )

                for idx, username in enumerate(username_list):
                    self.verify_data(
                        actual_value=username,
                        expected_value=username_log,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的跟单用户符合预期",
                        attachment_name=f"第 {idx + 1} 条记录的跟单用户校验"
                    )

        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
        @allure.title("跟单用户查询-查询结果为空")
        def test_query_usernameNO(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                params = {
                    "_t": current_timestamp_seconds,
                    "username": "XXXXXXXXX",
                    "pageNo": 1,
                    "pageSize": 20,
                    "status": "NORMAL,AUDIT"
                }
                response = self.send_get_request(
                    logged_session,
                    '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step("3. 查询校验"):
                self.json_utils.assert_empty_list(
                    data=response.json(),
                    expression="$.result.data.records"
                )
                logging.info("查询结果符合预期：records为空列表")
                allure.attach("查询结果为空，符合预期", 'text/plain')
