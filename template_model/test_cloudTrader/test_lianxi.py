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


class Test_delete(APITestBase):
    # 实例化JsonPath工具类（全局复用）
    json_utils = JsonPathUtils()

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

    # @allure.title("任务中心-MT4绑定审核-提取vpsID")
    # def test_getRecordList(self, var_manager, logged_session):
    #     with allure.step("1. 发送请求"):
    #         params = {
    #             "_t": current_timestamp_seconds,
    #             "column": "name",
    #             "order": "asc"
    #         }
    #         response = self.send_get_request(
    #             logged_session,
    #             '/blockchain/followVps/getRecordList',
    #             params=params
    #         )
    #
    #     with allure.step("2. 返回校验"):
    #         self.assert_json_value(
    #             response,
    #             "$.optimizeCountSql",
    #             True,
    #             "响应optimizeCountSql字段应为true"
    #         )
    #
    #     with allure.step("3. 提取数据"):
    #         ipAddress = self.json_utils.extract(response.json(), "$.records[1].ipAddress")
    #         var_manager.set_runtime_variable("vpsrunIpAddr", ipAddress)
