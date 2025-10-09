import time
import statistics
from typing import List, Union
import allure
import logging
import json
import pytest
from template.VAR.VAR import *
from template.commons.jsonpath_utils import *
from template.commons.random_generator import *
import re
import datetime
import requests
from template.commons.api_base import APITestBase, CompareOp, logger
from template.public_function.proportion_public import PublicUtils


@allure.feature("账号管理-删除账号")
class Test_delete(APITestBase):
    # 实例化JsonPath工具类（全局复用）
    json_utils = JsonPathUtils()

    @allure.title("公共方法-校验前操作")
    def test_run_public(self, var_manager, logged_session, db_transaction):
        # 实例化类
        public_front = PublicUtils()

        # 登录MT4账号获取token
        public_front.test_mt4_login(var_manager)
        # MT4平台开仓操作
        public_front.test_mt4_open(var_manager)
        # 提跟单订单号
        public_front.test_dbquery_openorder(var_manager, db_transaction)

        public_front.test_mt4_close(var_manager, db_transaction)

    # @allure.title("账号管理-交易员账号-绑定账户")
    # def test_account_bind(self, var_manager, logged_session):
    #     trader_account = var_manager.get_variable("trader_account")
    #     trader_password = var_manager.get_variable("trader_password")
    #     trader_user_id = var_manager.get_variable("trader_user_id")
    #     trader_broker_id = var_manager.get_variable("trader_broker_id")
    #     trader_server_id = var_manager.get_variable("trader_server_id")
    #     data = {
    #         "userId": trader_user_id,
    #         "brokerId": trader_broker_id,
    #         "serverId": trader_server_id,
    #         "account": trader_account,
    #         "password": trader_password,
    #         "display": "PUBLIC",
    #         "passwordType": "0",
    #         "subscribeFee": "0",
    #         "type": "MASTER_REAL",
    #         "strategy": "",
    #         "platform": "4"
    #     }
    #     response = self.send_post_request(
    #         logged_session,
    #         '/blockchain/account/bind',
    #         json_data=data
    #     )
    #
    #     self.assert_json_value(
    #         response,
    #         "$.success",
    #         True,
    #         "响应success字段应为true"
    #     )
    #
    # @allure.title("账号管理-交易员账号-绑定交易员-提取服务器ID")
    # def test_api_getData1(self, var_manager, logged_session):
    #     target_server = "CPTMarkets-Demo"
    #     trader_broker_id = var_manager.get_variable("trader_broker_id")
    #     with allure.step("1. 发送请求"):
    #         params = {
    #             "_t": current_timestamp_seconds,
    #             "broker_id": trader_broker_id,
    #             "pageSize": "50"
    #         }
    #         response = self.send_get_request(
    #             logged_session,
    #             '/online/cgform/api/getData/402883917b2f2594017b335d3ddb0001',
    #             params=params
    #         )
    #
    #     with allure.step("2. 返回校验"):
    #         self.assert_json_value(
    #             response,
    #             "$.success",
    #             True,
    #             "响应success字段应为true"
    #         )
    #
    #     with allure.step("3. 提取服务器的ID"):
    #         all_servers = self.json_utils.extract(
    #             data=response.json(),
    #             expression="$.result.records[*]",
    #             multi_match=True,
    #             default=[]
    #         )
    #
    #         server_id = None
    #         existing_servers = [server.get("server") for server in all_servers if server.get("server")]
    #
    #         for server in all_servers:
    #             current_server = server.get("server")
    #             if current_server == target_server:
    #                 server_id = server.get("id")
    #                 break
    #
    #         assert server_id is not None, (
    #             f"未找到服务器[{target_server}]的ID！"
    #             f"\n当前返回的服务器列表：{existing_servers}"
    #             f"\n请检查：1. 服务器名称是否正确 2. 是否在当前分页（pageSize=50）"
    #         )
    #         logging.info(f"提取成功 | 服务器名称: {target_server} | server_id: {server_id}")
    #         var_manager.set_runtime_variable("trader_server_id", server_id)
    #         allure.attach(
    #             name="服务器id",
    #             body=str(server_id),
    #             attachment_type=allure.attachment_type.TEXT
    #         )
