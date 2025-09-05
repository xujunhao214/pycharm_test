from template.commons.api_base import APITestBase
import allure
import logging
import pytest
from template.VAR.VAR import *
from template.commons.jsonpath_utils import *

json_unit = JsonPathUtils()


class Test_usr(APITestBase):
    @allure.title("数据库查询-提取数据")
    def test_dbbchain_trader(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库"):
            global brokerId

            sql = f"SELECT id,name FROM bchain_trader_broker WHERE name = %s"
            params = ("CPT Markets",)
            db_data = self.query_database(
                db_transaction=db_transaction,
                sql=sql,
                params=params
            )
        with allure.step("2. 提取数据"):
            brokerId = db_data[0]["id"]

    @allure.title("账号管理-交易员账号-绑定交易员-用户列表")
    def test_user_list(self, logged_session):
        global user_id
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "column": "createTime",
                "field": "id,,username,nickname,email,phone",
                "pageNo": "1",
                "pageSize": "5",
                "order": "asc"
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

        with allure.step("3. 提取数据"):
            user_id = json_unit.extract(response.json(), "$.result.records[?(@.email == 'xujunhao@163.com')].id")

    @allure.title("账号管理-交易员账号-绑定交易员-用户列表")
    def test_user_list(self, logged_session):
        global server_id
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "broker_id": brokerId,
                "pageSize": "50"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/402883917b2f2594017b335d3ddb0001',
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
            server_id = json_unit.extract(response.json(), "$.result.records[?(@.server == 'CPTMarkets-Demo')].id")

    @allure.title("账号管理-交易员账号-绑定交易员-用户列表")
    def test_user_list(self, logged_session):
        global user_id
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "column": "createTime",
                "field": "id,,username,nickname,email,phone",
                "pageNo": "1",
                "pageSize": "5",
                "order": "asc"
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

        with allure.step("3. 提取数据"):
            json_unit = JsonPathUtils()
            user_id = json_unit.extract(response.json(), "$.result.records[?(@.email == 'xujunhao@163.com')].id")

    @allure.title("账号管理-交易员账号-绑定账户")
    def test_account_bind(self, var_manager, logged_session):
        global trader, password
        trader = var_manager.get_variable("trader")
        password = var_manager.get_variable("password")
        data = {
            "userId": user_id,
            "brokerId": brokerId,
            "serverId": server_id,
            "account": trader,
            "password": password,
            "display": "PUBLIC",
            "passwordType": "0",
            "subscribeFee": "0",
            "type": type,
            "strategy": "",
            "platform": "4"
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

    @allure.title("账号管理-交易员账号-绑定账户-已经绑定过")
    def test_account_bind2(self, var_manager, logged_session):
        data = {
            "userId": user_id,
            "brokerId": brokerId,
            "serverId": server_id,
            "account": trader,
            "password": password,
            "display": "PUBLIC",
            "passwordType": "0",
            "subscribeFee": "0",
            "type": type,
            "strategy": "",
            "platform": "4"
        }
        response = self.send_post_request(
            logged_session,
            '/blockchain/account/bind',
            json_data=data
        )

        self.assert_json_value(
            response,
            "$.success",
            False,
            "响应success字段应为false"
        )

        self.assert_json_value(
            response,
            "$.message",
            "该账号在系统中已经被绑定了",
            "响应message字段应为:该账号在系统中已经被绑定了"
        )

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

    @allure.title("任务中心-MT4绑定审核-提取数据2")
    def test_api_getData2(self, logged_session):
        global pass_id
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
            pass_id = json_unit.extract(response.json(), "$.result.records[0].id")

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
                f'/blockchain/account/pass/{pass_id}',
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
            "traderId": pass_id
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
    def test_dbbchain_trader2(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库"):
            trader = var_manager.get_variable("trader")
            sql = f"SELECT id,server_id,broker_id,user_id,account,type,password,display,meta_trader_platform_id,password_type,subscribe_fee,status FROM bchain_trader WHERE account = %s"
            params = (trader,)

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
