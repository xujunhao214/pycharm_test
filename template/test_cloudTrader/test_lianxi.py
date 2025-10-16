import time
from template.commons.api_base import APITestBase
import allure
import logging
import pytest
from template.VAR.VAR import *
from template.commons.jsonpath_utils import *
from template.commons.random_generator import *


@allure.feature("账号管理")
class Test_create:
    @allure.story("绑定交易员账号")
    class Test_trader(APITestBase):
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
                var_manager.set_runtime_variable("trader_broker_id", brokerId)