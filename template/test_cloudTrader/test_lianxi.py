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

    # @allure.title("公共方法-校验前操作")
    # def test_run_public(self, var_manager, logged_session, db_transaction):
    #     # 实例化类
    #     public_front = PublicUtils()
    #
    #     # 按顺序调用
    #     # 登录获取 token
    #     # public_front.test_login(var_manager)
    #     # 平仓喊单账号
    #     # public_front.test_close_trader(var_manager)
    #     # 平仓跟单账号
    #     # public_front.test_close_follow(var_manager)
    #     public_front.test_mt4_login(var_manager)
    #     public_front.test_mt4_open(var_manager)
    #     # 提跟单订单号
    #     # public_front.test_dbquery_openorder(var_manager, db_transaction)
    #     public_front.test_mt4_close(var_manager, db_transaction)

    @allure.title("数据库查询-校验交易员账号是否解绑成功")
    def test_dbbchain_trader(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库"):
            trader_pass_id = var_manager.get_variable("trader_pass_id")
            sql = f"SELECT id,server_id,broker_id,user_id,account,type,password,display,meta_trader_platform_id,password_type,subscribe_fee,status FROM bchain_trader WHERE id = %s"
            params = (trader_pass_id,)

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
                allure.attach(str(status_list), "交易员账号解绑成功", allure.attachment_type.TEXT)
