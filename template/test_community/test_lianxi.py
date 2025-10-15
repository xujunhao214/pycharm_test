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
from template.commons.vps_session import *
from template.public_function.proportion_public import PublicUtils
from template.public_function.proportion_public_vps import PublicVpsUtils


@allure.feature("跟随方式-按比例")
class Test_proportionall(APITestBase):
    @allure.title("公共方法-策略开仓操作")
    def test_run_open(self, var_manager, logged_vps, dbvps_transaction):
        # 实例化类
        public_front = PublicVpsUtils()

        # 发送策略开仓请求
        public_front.test_trader_openorderSend(var_manager, logged_vps)
        # 提跟单订单号
        public_front.test_dbquery_orderSend(var_manager, dbvps_transaction)
