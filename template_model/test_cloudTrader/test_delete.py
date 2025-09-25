from template_model.commons.api_base import APITestBase
import allure
import logging
import pytest
import json
import requests
from template_model.VAR.VAR import *
from template_model.commons.jsonpath_utils import *
from template_model.public_function.proportion_public import PublicUtils


@allure.feature("账号管理-删除账号")
class Test_delete(APITestBase):
    # 实例化JsonPath工具类（全局复用）
    json_utils = JsonPathUtils()

    @allure.title("跟单社区前端-登录")
    def test_run_public(self, var_manager, logged_session):
        # 实例化类
        public_front = PublicUtils()

        # 登录获取 token
        public_front.test_login(var_manager)

    @allure.title("跟单社区前端-我的账户-喊单账号解绑-未取消订阅")
    def test_account_unbindtraderNO(self, var_manager):
        with allure.step("1. 发送解绑请求"):
            token_top = var_manager.get_variable("token_top")
            trader_pass_id = var_manager.get_variable("trader_pass_id")
            url = f"{URL_TOP}/blockchain/account/unbind?traderId={trader_pass_id}"

            payload = json.dumps({})
            headers = {
                'priority': 'u=1, i',
                'x-access-token': token_top,
                'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
                'content-type': 'application/json',
                'Accept': '*/*',
                'Host': 'dev.lgcopytrade.top',
                'Connection': 'keep-alive'
            }

            response = requests.request("POST", url, headers=headers, data=payload)
            allure.attach(url, "请求URL", allure.attachment_type.TEXT)
            headers_json = json.dumps(headers, ensure_ascii=False, indent=2)
            allure.attach(headers_json, "请求头", allure.attachment_type.JSON)
            print(response.text)
            logging.info(f"登录返回信息：{response.text}")
            allure.attach(response.text, "响应信息", allure.attachment_type.JSON)

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.message",
                "解绑账户失败：请先取消订阅关系",
                "响应message字段应为:解绑账户失败：请先取消订阅关系"
            )

    @allure.title("跟单社区前端-我的账户-跟单账号解绑-未取消订阅")
    def test_account_unbindfollowNO(self, var_manager):
        with allure.step("1. 发送解绑请求"):
            token_top = var_manager.get_variable("token_top")
            follow_pass_id = var_manager.get_variable("follow_pass_id")
            url = f"{URL_TOP}/blockchain/account/unbind?traderId={follow_pass_id}"

            payload = json.dumps({})
            headers = {
                'priority': 'u=1, i',
                'x-access-token': token_top,
                'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
                'content-type': 'application/json',
                'Accept': '*/*',
                'Host': 'dev.lgcopytrade.top',
                'Connection': 'keep-alive'
            }

            response = requests.request("POST", url, headers=headers, data=payload)
            allure.attach(url, "请求URL", allure.attachment_type.TEXT)
            headers_json = json.dumps(headers, ensure_ascii=False, indent=2)
            allure.attach(headers_json, "请求头", allure.attachment_type.JSON)
            print(response.text)
            logging.info(f"登录返回信息：{response.text}")
            allure.attach(response.text, "响应信息", allure.attachment_type.JSON)

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.message",
                "解绑账户失败：请先取消订阅关系",
                "响应message字段应为:解绑账户失败：请先取消订阅关系"
            )

    @allure.title("跟单社区后台-跟单管理-实时跟单-取消订阅")
    def test_api_deletePa(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            follow_jeecg_rowkey = var_manager.get_variable("follow_jeecg_rowkey")
            params = {
                "id": follow_jeecg_rowkey
            }
            response = self.send_delete_request(
                logged_session,
                f'/blockchain/master-slave/deletePa',
                params=params
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

    # @allure.title("跟单社区前端-登录")
    # def test_run_public(self, var_manager, logged_session):
    #     # 实例化类
    #     public_front = PublicUtils()
    #
    #     # 登录获取 token
    #     public_front.test_login(var_manager)

    @allure.title("跟单社区前端-我的账户-喊单账号解绑")
    def test_account_unbindtrader(self, var_manager):
        with allure.step("1. 发送解绑请求"):
            token_top = var_manager.get_variable("token_top")
            trader_pass_id = var_manager.get_variable("trader_pass_id")
            url = f"{URL_TOP}/blockchain/account/unbind?traderId={trader_pass_id}"

            payload = json.dumps({})
            headers = {
                'priority': 'u=1, i',
                'x-access-token': token_top,
                'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
                'content-type': 'application/json',
                'Accept': '*/*',
                'Host': 'dev.lgcopytrade.top',
                'Connection': 'keep-alive'
            }

            response = requests.request("POST", url, headers=headers, data=payload)
            allure.attach(url, "请求URL", allure.attachment_type.TEXT)
            headers_json = json.dumps(headers, ensure_ascii=False, indent=2)
            allure.attach(headers_json, "请求头", allure.attachment_type.JSON)
            print(response.text)
            logging.info(f"登录返回信息：{response.text}")
            allure.attach(response.text, "响应信息", allure.attachment_type.JSON)

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

    @allure.title("跟单社区前端-我的账户-跟单账号解绑")
    def test_account_unbindfollow(self, var_manager):
        with allure.step("1. 发送解绑请求"):
            token_top = var_manager.get_variable("token_top")
            follow_pass_id = var_manager.get_variable("follow_pass_id")
            url = f"{URL_TOP}/blockchain/account/unbind?traderId={follow_pass_id}"

            payload = json.dumps({})
            headers = {
                'priority': 'u=1, i',
                'x-access-token': token_top,
                'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
                'content-type': 'application/json',
                'Accept': '*/*',
                'Host': 'dev.lgcopytrade.top',
                'Connection': 'keep-alive'
            }

            response = requests.request("POST", url, headers=headers, data=payload)
            allure.attach(url, "请求URL", allure.attachment_type.TEXT)
            headers_json = json.dumps(headers, ensure_ascii=False, indent=2)
            allure.attach(headers_json, "请求头", allure.attachment_type.JSON)
            print(response.text)
            logging.info(f"登录返回信息：{response.text}")
            allure.attach(response.text, "响应信息", allure.attachment_type.JSON)

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

    @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("跟单社区后台-账号管理-跟随者账号-解绑账户")
    def test_account_unbindPa_follow(self, var_manager, logged_session):
        follow_pass_id = var_manager.get_variable("follow_pass_id")
        params = {
            "traderId": follow_pass_id
        }
        response = self.send_post_request(
            logged_session,
            '/blockchain/account/unbindPa',
            params=params
        )

        self.assert_json_value(
            response,
            "$.success",
            True,
            "响应success字段应为true"
        )

    # @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("数据库查询-校验跟随者账号是否解绑成功")
    def test_dbbchain_follow(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库"):
            follow_account = var_manager.get_variable("follow_account")
            sql = f"SELECT id,server_id,broker_id,user_id,account,type,password,display,meta_trader_platform_id,password_type,subscribe_fee,status FROM bchain_trader WHERE account = %s"
            params = (follow_account,)

            db_data = self.query_database(
                db_transaction=db_transaction,
                sql=sql,
                params=params
            )

        with allure.step("2. 校验跟随者账号是否解绑成功"):
            status_list = [record["status"] for record in db_data]
            for i in status_list:
                assert i == "UNBIND", f"跟随者账号解绑失败，实际状态为: {i}"
            logging.info(f"跟随者账号解绑成功")

    @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("跟单社区后台-账号管理-交易员账号-解绑账户")
    def test_account_unbindPa_trader(self, var_manager, logged_session):
        trader_pass_id = var_manager.get_variable("trader_pass_id")
        params = {
            "traderId": trader_pass_id
        }
        response = self.send_post_request(
            logged_session,
            '/blockchain/account/unbindPa',
            params=params
        )

        self.assert_json_value(
            response,
            "$.success",
            True,
            "响应success字段应为true"
        )

    @allure.title("数据库查询-校验交易员账号是否解绑成功")
    def test_dbbchain_trader(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库"):
            trader_account = var_manager.get_variable("trader_account")
            sql = f"SELECT id,server_id,broker_id,user_id,account,type,password,display,meta_trader_platform_id,password_type,subscribe_fee,status FROM bchain_trader WHERE account = %s"
            params = (trader_account,)

            db_data = self.query_database(
                db_transaction=db_transaction,
                sql=sql,
                params=params
            )

        with allure.step("2. 校验交易员账号是否解绑成功"):
            status_list = [record["status"] for record in db_data]
            for i in status_list:
                assert i == "UNBIND", f"交易员账号解绑失败，实际状态为: {i}"
            logging.info(f"交易员账号解绑成功")
