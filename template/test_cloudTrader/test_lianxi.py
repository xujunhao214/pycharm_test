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
from template.public_function.test_proportion_public import Test_public


@allure.feature("跟随方式-按比例")
class Test_openandclouseall:
    @allure.story("场景1：跟随方式-按比例-固定比例100%")
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
    class Test_orderseng1(APITestBase):
        # 实例化JsonPath工具类（全局复用）
        json_utils = JsonPathUtils()

        @allure.title("数据校验开始前操作")
        def run_clear_old(self, var_manager, logged_session):
            # 实例化类
            public_front = Test_public()

            # 按顺序调用
            # 先登录获取 token
            public_front.test_login(var_manager)
            # 平仓喊单账号
            public_front.test_close_trader(var_manager)
            # 平仓跟单账号
            public_front.test_close_follow(var_manager)
            # 清理魔术号相关数据
            public_front.test_query_magic(var_manager, logged_session)
            # 清理账号ID相关数据
            public_front.test_query_follow_passid(var_manager, logged_session)
            # 修改订阅数据
            public_front.test_query_updata_editPa(var_manager, logged_session)
            # 订阅列表数据
            public_front.test_query_getColumnsAndData(var_manager, logged_session)
            # 登录MT4账号获取token
            public_front.test_mt4_login(var_manager)
            # MT4平台开仓操作
            public_front.test_mt4_open(var_manager)
            # MT4平台平仓操作
            public_front.test_mt4_close(var_manager)
