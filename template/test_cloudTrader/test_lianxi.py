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

        @allure.title("获取用户钱包信息-余额校验")
        def test_api_getData_no(self, var_manager):
            with allure.step("1. 发送请求"):
                trader_user_id = var_manager.get_variable("trader_user_id")
                url = f"https://dev.lgcopytrade.top/api/online/cgform/api/getData/4028839781b865e40181b8784023000b?to_uid={trader_user_id}&pageSize=10&pageNo=1&type=1,8&column=create_time&order=desc"

                response = requests.request("GET", url, headers=headers, data={})
                print(response.text)
                logging.info(f"response返回信息：{response.text}")

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step("3. 余额校验"):
                actual_money = var_manager.get_variable("actual_money")
                actual_money_now = self.json_utils.extract(response.json(), "$.result.records[0].actual_money")
                actual_money_top = actual_money + 100
                self.verify_data(
                    actual_value=actual_money_now,
                    expected_value=actual_money_top,
                    op=CompareOp.EQ,
                    message="余额符合预期",
                    attachment_name="余额信息"
                )
                logging.info(f"余额验证通过: {actual_money_now}")
