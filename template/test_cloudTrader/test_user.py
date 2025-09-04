from template.commons.api_base import APITestBase
import allure
import logging
from template.VAR.VAR import *
from template.commons.jsonpath_utils import *


class Test_usr(APITestBase):
    @allure.title("数据库查询-提取数据")
    def test_dbbchain_trader(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库"):
            global server_id, broker_id, user_id, account, type, password, display_upper, meta_trader_platform_id, password_type, subscribe_fee, trader_id

            sql = f"SELECT id,server_id,broker_id,user_id,account,type,password,display,meta_trader_platform_id,password_type,subscribe_fee FROM bchain_trader WHERE account = %s"
            params = ("301387254",)
            db_data = self.query_database(
                db_transaction=db_transaction,
                sql=sql,
                params=params
            )
        with allure.step("2. 提取数据"):
            server_id = db_data[0]["server_id"]
            broker_id = db_data[0]["broker_id"]
            user_id = db_data[0]["user_id"]
            type = db_data[0]["type"]
            password = db_data[0]["password"]
            display = db_data[0]["display"]
            display_upper = display.upper()
            meta_trader_platform_id = db_data[0]["meta_trader_platform_id"]
            password_type = db_data[0]["password_type"]
            subscribe_fee = db_data[0]["subscribe_fee"]
            trader_id = db_data[0]["id"]

    @allure.title("账号管理-交易员账号-绑定账户")
    def test_account_bind(self, logged_session):
        data = {
            "userId": user_id,
            "brokerId": broker_id,
            "serverId": server_id,
            "account": "301387254",
            "password": password,
            "display": display_upper,
            "passwordType": password_type,
            "subscribeFee": subscribe_fee,
            "type": type,
            "strategy": "",
            "platform": meta_trader_platform_id
        }
        response = self.send_post_request(
            logged_session,
            '/blockchain/account/bind',
            json_data=data
        )

        self.assert_json_value(
            response,
            "$.success",
            True,
            "响应success字段应为true"
        )

        # self.assert_json_value(
        #     response,
        #     "$.message",
        #     "该账号在系统中已经被绑定了",
        #     "响应message字段应为:该账号在系统中已经被绑定了"
        # )

    @allure.title("任务中心-MT4绑定审核-提取数据")
    def test_api_getData(self, logged_session):
        global jeecg_row_key
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "column": "name",
                "order": "asc"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/4028839781b865e40181b87163350007',
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
            json_unit = JsonPathUtils()
            jeecg_row_key = json_unit.extract(response.json(), "$.result.records[4].jeecg_row_key")

    @allure.title("任务中心-MT4绑定审核-通过")
    def test_account_pass(self, logged_session):
        with allure.step("1. 发送请求"):
            data = {
                "pass": True,
                "commission": False,
                "planId": jeecg_row_key,
                "toSynDate": DATETIME_NOW,
                "bindIpAddr": None
            }
            response = self.send_post_request(
                logged_session,
                '/blockchain/account/pass/1963509294228770818',
                json_data=data
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

    @allure.title("账号管理-交易员账号-解绑账户")
    def test_account_unbindPa(self, logged_session):
        params = {
            "traderId": trader_id
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
