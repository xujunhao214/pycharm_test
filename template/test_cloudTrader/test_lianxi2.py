import time
from template.commons.api_base import APITestBase, CompareOp, logger
import allure
import logging
import logging
import datetime
import re
import pytest
import requests
from template.VAR.VAR import *
from template.commons.jsonpath_utils import *
from template.commons.random_generator import *
from template.commons.session import percentage_to_decimal


@allure.feature("跟随方式-按手数")
class Test_openandclouseall:
    @allure.story("场景3：跟随方式-按手数-0.01,跟单方向反向")
    @allure.description("""
    ### 测试说明
    - 前置条件：有喊单账号、跟单账号，跟单已经和喊单有订阅关系
      1. MT4进行登录，然后进行开仓，总手数0.01
      2. 账号管理-持仓订单-喊单和跟单数据校验
      3. 跟单管理-开仓日志-喊单和跟单数据校验
      4. 跟单管理-VPS管理-喊单和跟单数据校验
      5. MT4进行平仓
      6.账号管理-持仓订单-喊单和跟单数据校验
      7.跟单管理-开仓日志-喊单和跟单数据校验
      8.跟单管理-VPS管理-喊单和跟单数据校验
    - 预期结果：喊单和跟单数据校验正确
    """)
    # @pytest.mark.skipif(True, reason="跳过此用例")
    class Test_orderseng3(APITestBase):
        # 实例化JsonPath工具类（全局复用）
        json_utils = JsonPathUtils()

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("跟单管理-实时跟单-修改订阅数据")
        def test_query_updata_editPa(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                follow_jeecg_rowkey = var_manager.get_variable("follow_jeecg_rowkey")
                data = {
                    "id": follow_jeecg_rowkey,
                    "direction": "REVERSE",
                    "followingMode": 3,
                    "fixedProportion": None,
                    "fixedLots": 0.01
                }
                response = self.send_put_request(
                    logged_session,
                    '/blockchain/master-slave/editPa',
                    json_data=data
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )