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

        @allure.title("跟单管理-实时跟单-检查是否有订阅记录")
        def test_api_getColumnsAndData2(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                follow_account = var_manager.get_variable("follow_account")
                params = {
                    "_t": current_timestamp_seconds,
                    "account": follow_account,
                    "pageNo": 1,
                    "pageSize": 100,
                    "status": "NORMAL,AUDIT"
                }
                response = self.send_get_request(
                    logged_session,
                    f'/online/cgreport/api/getColumnsAndData/1560189381093109761',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step("3. 判断是否有订阅信息"):
                result = self.json_utils.extract(response.json(), "$.result.data.records[*]")
                if not result:
                    logging.info(f"无订阅信息")
                    allure.attach(
                        "无订阅信息",
                        name="订阅信息"
                    )
                else:
                    logging.info(f"有订阅信息")
                    allure.attach(
                        "有订阅信息",
                        name="订阅信息"
                    )
