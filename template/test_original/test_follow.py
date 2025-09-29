from template.commons.api_base import APITestBase
import allure
import logging
import pytest
from template.VAR.VAR import *
from template.commons.jsonpath_utils import *


class Test_follow(APITestBase):
    # 实例化JsonPath工具类（全局复用）
    json_utils = JsonPathUtils()

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

    @allure.title("账号管理-跟随者账号-绑定跟随者-用户列表-提取用户id")
    def test_user_list(self, logged_session):
        global user_id
        target_email = "xujunhao@163.com"

        with allure.step("1. 发送GET请求"):
            params = {
                "_t": current_timestamp_seconds,
                "column": "createTime",
                "field": "id,,username,nickname,email,phone",
                "pageNo": "1",
                "pageSize": "5",
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
            allure.attach(
                name="用户ID",
                body=str(user_id),
                attachment_type=allure.attachment_type.TEXT
            )

    @allure.title("账号管理-跟随者账号-绑定跟随者-提取服务器ID")
    def test_api_getData1(self, logged_session):
        global server_id
        target_server = "CPTMarkets-Demo"

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

        with allure.step("3. 提取服务器的ID"):
            all_servers = self.json_utils.extract(
                data=response.json(),
                expression="$.result.records[*]",
                multi_match=True,
                default=[]
            )

            server_id = None
            existing_servers = [server.get("server") for server in all_servers if server.get("server")]

            for server in all_servers:
                current_server = server.get("server")
                if current_server == target_server:
                    server_id = server.get("id")
                    break

            assert server_id is not None, (
                f"未找到服务器[{target_server}]的ID！"
                f"\n当前返回的服务器列表：{existing_servers}"
                f"\n请检查：1. 服务器名称是否正确 2. 是否在当前分页（pageSize=50）"
            )
            logging.info(f"提取成功 | 服务器名称: {target_server} | server_id: {server_id}")
            allure.attach(
                name="服务器id",
                body=str(server_id),
                attachment_type=allure.attachment_type.TEXT
            )

    @allure.title("账号管理-跟随者账户-绑定账户")
    def test_account_bind(self, var_manager, logged_session):
        global follow_account, follow_password
        follow_account = var_manager.get_variable("follow_account")
        follow_password = var_manager.get_variable("follow_password")
        data = {
            "userId": user_id,
            "brokerId": brokerId,
            "serverId": server_id,
            "account": follow_account,
            "password": follow_password,
            "display": "PRIVATE",
            "passwordType": "0",
            "subscribeFee": "0",
            "type": "SLAVE_REAL",
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

    @allure.title("账号管理-跟随者账号-绑定账户-已经绑定过")
    def test_account_bind2(self, var_manager, logged_session):
        data = {
            "userId": user_id,
            "brokerId": brokerId,
            "serverId": server_id,
            "account": follow_account,
            "password": follow_password,
            "display": "PRIVATE",
            "passwordType": "0",
            "subscribeFee": "0",
            "type": "SLAVE_REAL",
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
    def test_api_getData7(self, logged_session):
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
            jeecg_row_key = self.json_utils.extract(response.json(), "$.result.records[4].jeecg_row_key")

    @allure.title("任务中心-MT4绑定审核-提取数据2")
    def test_api_getData0(self, logged_session):
        global follow_pass_id
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
            follow_pass_id = self.json_utils.extract(response.json(), "$.result.records[0].id")

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
                f'/blockchain/account/pass/{follow_pass_id}',
                json_data=data
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

    # @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("账号管理-跟随者账号-解绑账户")
    def test_account_unbindPa(self, logged_session):
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
    def test_dbbchain_trader2(self, var_manager, db_transaction):
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
