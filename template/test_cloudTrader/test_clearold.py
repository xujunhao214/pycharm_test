import time
from template.commons.api_base import APITestBase, CompareOp, logger
import allure
import logging
import logging
import datetime
import re
import json
import pytest
import requests
from template.VAR.VAR import *
from template.commons.jsonpath_utils import *
from template.commons.random_generator import *
from template.commons.session import percentage_to_decimal


@allure.title("数据校验开始前操作")
class Test_clear_old(APITestBase):
    # 实例化JsonPath工具类（全局复用）
    json_utils = JsonPathUtils()

    @allure.title("跟单社区前端-登录")
    def test_login(self, var_manager):
        with allure.step("1. 发送登录请求"):
            url = f"{URL_TOP}/sys/mLogin"

            payload = json.dumps({
                "username": "xujunhao@163.com",
                "password": "123456",
                "lang": 0,
                "orgCode": "A01"
            })
            header = {
                'priority': 'u=1, i',
                'x-access-token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3NTgyNDY3ODIsInVzZXJuYW1lIjoiYW5vbnltb3VzIn0.lvI66l-hA0VqHCsfgODrPoH4KylpOpzVuSOOycls5gE',
                'X-Access-Token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3NTc0OTMyMDMsInVzZXJuYW1lIjoiYWRtaW4ifQ.PkFLjsBa0NbCUF8ROtmIGABzYmUH2ldQfqz_ERvaKsY',
                'content-type': 'application/json',
                'Accept': '*/*',
                'Host': 'dev.lgcopytrade.top',
                'Connection': 'keep-alive'
            }

            response = requests.request("POST", url, headers=header, data=payload)
            print(response.text)
            logging.info(f"登录返回信息：{response.text}")

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

        with allure.step("3. 提取token"):
            token_top = self.json_utils.extract(response.json(), "$.result.token")
            var_manager.set_runtime_variable("token_top", token_top)

    @allure.title("跟单社区前端-喊单账号平仓")
    def test_close_trader(self, var_manager):
        with allure.step("1. 发送喊单账号平仓请求"):
            global headers
            trader_pass_id = var_manager.get_variable("trader_pass_id")
            token_top = var_manager.get_variable("token_top")
            url = f"{URL_TOP}/blockchain/account/closeAllOrder?traderId={trader_pass_id}&including=true"

            headers = {
                'priority': 'u=1, i',
                'X-Access-Token': token_top,
                'Accept': '*/*',
                'Host': 'dev.lgcopytrade.top',
                'Connection': 'keep-alive'
            }

            response = requests.request("GET", url, headers=headers, data={})

            print(response.text)
            logging.info(f"平仓返回信息：{response.text}")

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

    @allure.title("跟单社区前端-跟单账号平仓")
    def test_close_follow(self, var_manager):
        with allure.step("1. 发送跟单账号平仓请求"):
            follow_pass_id = var_manager.get_variable("follow_pass_id")
            url = f"{URL_TOP}/blockchain/account/closeAllOrder?traderId={follow_pass_id}&including=true"

            response = requests.request("GET", url, headers=headers, data={})

            print(response.text)
            logging.info(f"平仓返回信息：{response.text}")

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

    # @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("账号管理-持仓订单-魔术号查询-开仓前")
    def test_query_magic(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            trader_account = var_manager.get_variable("trader_account")
            params = {
                "_t": current_timestamp_seconds,
                "magic": trader_account,
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

        with allure.step("3. 查询校验"):
            jeecg_row_key_list = self.json_utils.extract(
                response.json(),
                "$.result.records[*].jeecg_row_key",
                default=[],
                multi_match=True
            )

            if jeecg_row_key_list is None:
                allure.attach("魔术号查询结果为空", "查询结果", allure.attachment_type.TEXT)
            else:
                for jeecg_row_key in jeecg_row_key_list:
                    self.send_delete_request(
                        logged_session,
                        f'/online/cgform/api/form/402883977b38c9ca017b38c9caff0000/{jeecg_row_key}'
                    )
                    allure.attach(f"删除数据成功：{jeecg_row_key}", "删除结果", allure.attachment_type.TEXT)

    # @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("账号管理-持仓订单-账号ID查询-开仓前")
    def test_query_follow_passid(self, var_manager, logged_session):
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
            trader_id_list = self.json_utils.extract(
                response.json(),
                "$.result.records[*].trader_id",
                default=[],
                multi_match=True
            )

            if trader_id_list is None:
                allure.attach("账号ID查询结果为空", "查询结果", allure.attachment_type.TEXT)
            else:
                for trader_id in trader_id_list:
                    self.send_delete_request(
                        logged_session,
                        f'/online/cgform/api/form/402883977b38c9ca017b38c9caff0000/{trader_id}'
                    )
                    allure.attach(f"删除数据成功：{trader_id}", "删除结果", allure.attachment_type.TEXT)
