from template.commons.api_base import APITestBase
import allure
import logging
import pytest
import json
import requests
from template.VAR.VAR import *
from template.commons.jsonpath_utils import *
from template.public_function.proportion_public import PublicUtils


@allure.feature("账号管理-删除账号")
class Test_delete(APITestBase):
    # 实例化JsonPath工具类（全局复用）
    json_utils = JsonPathUtils()

    @allure.title("公共方法-校验前操作")
    def test_run_public(self, var_manager, logged_session):
        # 实例化类
        public_front = PublicUtils()

        # 按顺序调用
        # 登录获取 token
        public_front.test_login(var_manager)
        # 平仓喊单账号
        public_front.test_close_trader(var_manager)
        # 平仓跟单账号
        public_front.test_close_follow(var_manager)
