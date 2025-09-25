import time
from template.commons.api_base import APITestBase, CompareOp, logger
import allure
import logging
import json
import logging
import datetime
import re
import pytest
import requests
from template.VAR.VAR import *
from template.commons.jsonpath_utils import *
from template.commons.random_generator import *


@allure.story("绑定跟随者账号")
class Test_follow(APITestBase):
    # 实例化JsonPath工具类（全局复用）
    json_utils = JsonPathUtils()

    @allure.title("数据库查询-提取数据")
    def test_dbbchain_trader(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库"):
            sql = f"SELECT id,name FROM bchain_trader_broker WHERE name = %s"
            params = ("CPT Markets",)
            db_data = self.query_database(
                db_transaction=db_transaction,
                sql=sql,
                params=params
            )
        with allure.step("2. 提取数据"):
            brokerId = db_data[0]["id"]
            var_manager.set_runtime_variable("follow_broker_id", brokerId)

    @allure.title("账号管理-跟随者账号-绑定跟随者-用户列表-提取用户id")
    def test_user_list(self, var_manager, logged_session):
        target_email = "xujunhao@163.com"
        with allure.step("1. 构造参数并发送GET请求"):
            params = {
                "_t": current_timestamp_seconds,
                "column": "createTime",
                "field": "id,,username,nickname,email,phone",
                "pageNo": "1",
                "pageSize": "20",
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
            var_manager.set_runtime_variable("follow_user_id", user_id)
            allure.attach(
                name="用户ID",
                body=str(user_id),
                attachment_type=allure.attachment_type.TEXT
            )

    @allure.title("账号管理-跟随者账号-绑定跟随者-提取服务器ID")
    def test_api_getData1(self, var_manager, logged_session):
        target_server = "CPTMarkets-Demo"
        follow_broker_id = var_manager.get_variable("follow_broker_id")
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "broker_id": follow_broker_id,
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
            var_manager.set_runtime_variable("follow_server_id", server_id)
            allure.attach(
                name="服务器id",
                body=str(server_id),
                attachment_type=allure.attachment_type.TEXT
            )

    @allure.title("账号管理-跟随者账户-绑定账户")
    def test_account_bind(self, var_manager, logged_session):
        follow_account = var_manager.get_variable("follow_account")
        follow_password = var_manager.get_variable("follow_password")
        follow_user_id = var_manager.get_variable("follow_user_id")
        follow_broker_id = var_manager.get_variable("follow_broker_id")
        follow_server_id = var_manager.get_variable("follow_server_id")
        data = {
            "userId": follow_user_id,
            "brokerId": follow_broker_id,
            "serverId": follow_server_id,
            "account": follow_account,
            "password": follow_password,
            "display": "PRIVATE",
            "passwordType": "0",
            "subscribeFee": "0",
            "type": "SLAVE_REAL",
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

    @allure.title("任务中心-MT4绑定审核-提取数据")
    def test_api_getData7(self, var_manager, logged_session):
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
            var_manager.set_runtime_variable("follow_jeecgrow_key", jeecg_row_key)

    @allure.title("任务中心-MT4绑定审核-提取数据2")
    def test_api_getData0(self, var_manager, logged_session):
        account = var_manager.get_variable("follow_account")
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
            follow_pass_id = None
            existing_account = [account.get("account") for account in all_pass_account if account.get("account")]

            for trader_pass in all_pass_account:
                current_server = trader_pass.get("account")
                if current_server == account:
                    follow_pass_id = trader_pass.get("id")
                    break

            assert follow_pass_id is not None, (
                f"未找MT4审核[{account}]的ID！"
                f"\n当前返回的MT4审核列表：{existing_account}"
                f"\n请检查：1. 账号是否正确； 2. 是否在当前分页（pageSize=50）"
            )
            logging.info(f"提取成功 | 账号的id: {account} | trader_pass_id: {follow_pass_id}")
            var_manager.set_runtime_variable("follow_pass_id", follow_pass_id)
            allure.attach(
                name="账号id",
                body=str(follow_pass_id),
                attachment_type=allure.attachment_type.TEXT
            )

    @allure.title("任务中心-MT4绑定审核-通过")
    def test_account_pass(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            follow_pass_id = var_manager.get_variable("follow_pass_id")
            follow_jeecgrow_key = var_manager.get_variable("follow_jeecgrow_key")
            vpsrunIpAddr = var_manager.get_variable("vpsrunIpAddr")
            data = {
                "pass": True,
                "commission": False,
                "planId": follow_jeecgrow_key,
                "toSynDate": DATETIME_NOW,
                "bindIpAddr": vpsrunIpAddr
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

    @allure.title("跟单管理-实时跟单-检查是否有订阅记录")
    def test_api_getColumnsAndData(self, var_manager, logged_session):
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
            deletePa_id = self.json_utils.extract(response.json(), "$.result.data.records[0].id")
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
                with allure.step("4. 删除订阅信息"):
                    data = {
                        "id": deletePa_id
                    }
                    self.send_delete_request(
                        logged_session,
                        f'/blockchain/master-slave/deletePa',
                        json_data=data
                    )

    # @pytest.mark.skip(reason="跳过此用例")
    @allure.title("账号管理-跟单者账号-订阅")
    def test_admin_add(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            trader_pass_id = var_manager.get_variable("trader_pass_id")
            follow_pass_id = var_manager.get_variable("follow_pass_id")
            data = {
                "masterId": trader_pass_id,
                "slaveId": follow_pass_id,
                "direction": "FORWARD",
                "followingMode": "2",
                "fixedProportion": "100",
                "fixedLots": None,
                "order": {"paymentAccount": "", "paymentMethod": ""},
            }
            response = self.send_post_request(
                logged_session,
                f'/blockchain/master-slave/admin/add',
                json_data=data
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

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
            follow_jeecg_rowkey = self.json_utils.extract(response.json(), "$.result.data.records[0].jeecg_row_key")
            var_manager.set_runtime_variable("follow_jeecg_rowkey", follow_jeecg_rowkey)
            if not result:
                pytest.fail("无订阅信息")
            else:
                logging.info(f"有订阅信息")
                allure.attach(
                    "有订阅信息",
                    name="订阅信息"
                )
