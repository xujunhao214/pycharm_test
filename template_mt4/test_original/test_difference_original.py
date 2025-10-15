import time
from template_mt4.commons.api_base import APITestBase, CompareOp
import allure
import logging
import json
import pytest
from template_mt4.VAR.VAR import *
from template_mt4.commons.jsonpath_utils import *
from template_mt4.commons.random_generator import *


@allure.feature("账号管理-历史订单")
class Test_create:
    @allure.story("历史订单的订单查询校验")
    class Test_trader(APITestBase):
        # 实例化JsonPath工具类（全局复用）
        json_utils = JsonPathUtils()

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库提取数据-喊单账户开仓时间差")
        def test_dbquery_trader_openorder(self, var_manager, db_transaction):
            with allure.step("1. 查询数据库验证是否新增成功"):
                trader_pass_id = var_manager.get_variable("trader_pass_id")

                db_data = self.query_database(
                    db_transaction,
                    f"SELECT * FROM bchain_trader_subscribe_order WHERE master_id = %s",
                    (trader_pass_id,),
                )

                # 提取数据库中的值
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

            with allure.step("2. 提取数据库中的值"):
                trader_open_time_difference = [record["open_time_difference"] for record in db_data]
                logging.info(f"喊单账户开仓时间差（毫秒）: {trader_open_time_difference}")
                var_manager.set_runtime_variable("trader_open_time_difference", trader_open_time_difference)
                allure.attach(f"喊单账户开仓时间差（毫秒）: {trader_open_time_difference}", "喊单账户开仓时间差")

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库提取数据-跟单账户开仓时间差")
        def test_dbquery_follow_openorder(self, var_manager, db_transaction):
            with allure.step("1. 查询数据库验证是否新增成功"):
                follow_pass_id = var_manager.get_variable("follow_pass_id")

                # 优化后的数据库查询
                db_data = self.query_database(
                    db_transaction,
                    f"SELECT * FROM bchain_trader_subscribe_order WHERE slave_id = %s",
                    (follow_pass_id,),
                )

                # 提取数据库中的值
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

            with allure.step("2. 提取数据库中的值"):
                follow_open_time_difference = [record["open_time_difference"] for record in db_data]
                logging.info(f"跟单账户开仓时间差（毫秒）: {follow_open_time_difference}")
                var_manager.set_runtime_variable("follow_open_time_difference", follow_open_time_difference)
                allure.attach(f"跟单账户开仓时间差（毫秒）: {follow_open_time_difference}", "跟单账户开仓时间差")

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库提取数据-喊单账户平仓时间差")
        def test_dbquery_trader_closeorder(self, var_manager, db_transaction):
            with allure.step("1. 查询数据库验证是否新增成功"):
                trader_pass_id = var_manager.get_variable("trader_pass_id")

                db_data = self.query_database(
                    db_transaction,
                    f"SELECT * FROM bchain_trader_subscribe_order WHERE master_id = %s",
                    (trader_pass_id,),
                )

                # 提取数据库中的值
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

            with allure.step("2. 提取数据库中的值"):
                trader_close_time_difference = [record["close_time_difference"] for record in db_data]
                logging.info(f"喊单账户平仓时间差（毫秒）: {trader_close_time_difference}")
                var_manager.set_runtime_variable("trader_open_time_difference", trader_close_time_difference)
                allure.attach(f"喊单账户平仓时间差（毫秒）: {trader_close_time_difference}", "喊单账户平仓时间差")

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库提取数据-跟单账户平仓时间差")
        def test_dbquery_follow_closeorder(self, var_manager, db_transaction):
            with allure.step("1. 查询数据库验证是否新增成功"):
                follow_pass_id = var_manager.get_variable("follow_pass_id")

                # 优化后的数据库查询
                db_data = self.query_database(
                    db_transaction,
                    f"SELECT * FROM bchain_trader_subscribe_order WHERE slave_id = %s",
                    (follow_pass_id,),
                )

                # 提取数据库中的值
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

            with allure.step("2. 提取数据库中的值"):
                follow_close_time_difference = [record["close_time_difference"] for record in db_data]
                logging.info(f"跟单账户平仓时间差（毫秒）: {follow_close_time_difference}")
                var_manager.set_runtime_variable("follow_close_time_difference", follow_close_time_difference)
                allure.attach(f"跟单账户平仓时间差（毫秒）: {follow_close_time_difference}", "跟单账户平仓时间差")
