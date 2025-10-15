import time
import statistics
from typing import List, Union
import allure
import logging
import json
import pytest
from template_model.VAR.VAR import *
from template_model.commons.jsonpath_utils import *
from template_model.commons.random_generator import *
import re
import datetime
import requests
from template_model.commons.api_base import APITestBase, CompareOp, logger
from template_model.public_function.proportion_public import PublicUtils


@allure.feature("账号管理-删除账号")
class Test_delete(APITestBase):
    # 实例化JsonPath工具类（全局复用）
    json_utils = JsonPathUtils()

    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-新增策略账号")
    def test_add_trader(self, var_manager, logged_vps, encrypted_password):
        # 1. 发送新增策略账号请求
        new_user = var_manager.get_variable("new_user")
        vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
        data = {
            "type": 0,
            "account": vps_user_accounts_1,
            "password": encrypted_password,
            "platform": new_user["platform"],
            "remark": "",
            "platformId": "",
            "template_modelId": 1,
            "followStatus": 1,
            "cfd": "",
            "forex": "",
            "followOrderRemark": 1,
            "fixedComment": "",
            "commentType": "",
            "digits": "",
            "platformType": 0
        }
        response = self.send_post_request(
            logged_vps,
            '/subcontrol/trader',
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "新增策略账号失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )
    # @allure.title("公共方法-校验前操作")
    # def test_run_public(self, var_manager, logged_session, db_transaction):
    #     # 实例化类
    #     public_front = PublicUtils()
    #
    #     public_front.test_login(var_manager)

    # # 登录MT4账号获取token
    # public_front.test_mt4_login(var_manager)
    # # MT4平台开仓操作
    # public_front.test_mt4_open(var_manager)
    # # 提跟单订单号
    # public_front.test_dbquery_openorder(var_manager, db_transaction)
    #
    # public_front.test_mt4_close(var_manager, db_transaction)

    # @allure.title("数据库查询-提取数据")
    # def test_dbbchain_trader(self, var_manager, db_transaction):
    #     with allure.step("1. 查询数据库"):
    #         sql = f"SELECT id,name FROM bchain_trader_broker WHERE name = %s"
    #         params = ("CPT Markets",)
    #         db_data = self.query_database(
    #             db_transaction=db_transaction,
    #             sql=sql,
    #             params=params
    #         )
    #     with allure.step("2. 提取数据"):
    #         brokerId = db_data[0]["id"]
    #         var_manager.set_runtime_variable("trader_broker_id", brokerId)
    #
    # @allure.title("账号管理-交易员账号-绑定交易员-用户列表-提取用户id")
    # def test_user_list(self, var_manager, logged_session):
    #     login_config = var_manager.get_variable("login_config")
    #     target_email = login_config["username"]
    #
    #     with allure.step("1. 发送GET请求"):
    #         params = {
    #             "_t": current_timestamp_seconds,
    #             "username": target_email,
    #             "column": "createTime",
    #             "field": "id,,id,createTime,username,nickname,email,countryName,phone,avatar,realname,post_dictText,whiteLabelNameEn,invitationCode,agentLevel,agentLeader,isMfaVerified,orgCodeTxt,introduce,status_dictText,country,lang,trialPeriod,bufferDay,action",
    #             "pageNo": "1",
    #             "pageSize": "20",
    #             "order": "desc"
    #         }
    #
    #         response = self.send_get_request(
    #             logged_session,
    #             '/sys/user/list',
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
    #     with allure.step(f"3. 提取用户ID"):
    #         user_id = self.json_utils.extract(response.json(), "$.result.records[0].id")
    #         var_manager.set_runtime_variable("trader_user_id", user_id)
    #         allure.attach(
    #             name="用户ID",
    #             body=str(user_id),
    #             attachment_type=allure.attachment_type.TEXT
    #         )
