import time
from template.commons.api_base import APITestBase, CompareOp
import allure
import logging
import pytest
import requests
from template.VAR.VAR import *
from template.commons.jsonpath_utils import *
from template.commons.random_generator import *


@allure.feature("账号管理")
class Test_create:
    @allure.story("创建交易员账号")
    class Test_trader(APITestBase):
        # 实例化JsonPath工具类（全局复用）
        json_utils = JsonPathUtils()

        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
        @allure.title("喊单者账号ID查询-开仓前")
        def test_query_trader_passid(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                trader_pass_id = var_manager.get_variable("trader_pass_id")
                params = {
                    "_t": current_timestamp_seconds,
                    "trader_id": trader_pass_id,
                    "column": "id",
                    "order": "desc",
                    "pageNo": 1,
                    "pageSize": 50,
                    "superQueryMatchType": "and"
                }
                response = self.send_get_request(
                    logged_session,
                    '/online/cgform/api/getData/402883977b38c9ca017b38c9caff0000',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step(f"3. 查询校验"):
                self.json_utils.assert_empty_list(
                    data=response.json(),
                    expression="$.result.records"
                )
                logging.info("查询结果符合预期：records为空列表")
                allure.attach("查询结果为空，符合预期", 'text/plain')

        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
        @allure.title("跟单账号ID查询-开仓前")
        def test_query_follow_passid(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                follow_pass_id = var_manager.get_variable("follow_pass_id")
                params = {
                    "_t": current_timestamp_seconds,
                    "trader_id": follow_pass_id,
                    "column": "id",
                    "order": "desc",
                    "pageNo": 1,
                    "pageSize": 50,
                    "superQueryMatchType": "and"
                }
                response = self.send_get_request(
                    logged_session,
                    '/online/cgform/api/getData/402883977b38c9ca017b38c9caff0000',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step(f"3. 查询校验"):
                self.json_utils.assert_empty_list(
                    data=response.json(),
                    expression="$.result.records"
                )
                logging.info("查询结果符合预期：records为空列表")
                allure.attach("查询结果为空，符合预期", 'text/plain')