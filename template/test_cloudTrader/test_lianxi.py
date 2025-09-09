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

        @allure.title("任务中心-MT4绑定审核-提取数据2")
        def test_api_getData0(self, var_manager, logged_session):
            account = var_manager.get_variable("trader_account")
            with allure.step("1. 发送请求"):
                params = {
                    "_t": current_timestamp_seconds,
                    "column": "id",
                    "order": "desc",
                    "pageNo": 1,
                    "pageSize": 20,
                    "superQueryMatchType": "and",
                    "status": "PENDING,VERIFICATION"
                }
                response = self.send_get_request(
                    logged_session,
                    '/online/cgform/api/getData/2c9a814a81d3a91b0181d3a91b250000',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step("3. 提取数据"):
                all_pass_account = self.json_utils.extract(
                    data=response.json(),
                    expression="$.result.records[*]",
                    multi_match=True,
                    default=[]
                )
                trader_pass_id = None
                existing_account = [account.get("account") for account in all_pass_account if account.get("account")]

                for trader_pass in all_pass_account:
                    current_server = trader_pass.get("account")
                    if current_server == account:
                        trader_pass_id = trader_pass.get("id")
                        break

                assert trader_pass_id is not None, (
                    f"未找MT4审核[{account}]的ID！"
                    f"\n当前返回的MT4审核列表：{existing_account}"
                    f"\n请检查：1. 账号是否正确； 2. 是否在当前分页（pageSize=50）"
                )
                logging.info(f"提取成功 | 账号的id: {account} | trader_pass_id: {trader_pass_id}")
                var_manager.set_runtime_variable("trader_pass_id", trader_pass_id)
                allure.attach(
                    name="账号id",
                    body=str(trader_pass_id),
                    attachment_type=allure.attachment_type.TEXT
                )
