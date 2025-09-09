from template.commons.api_base import APITestBase
import allure
import logging
import pytest
from template.VAR.VAR import *
from template.commons.jsonpath_utils import *


@allure.feature("账号管理-删除账号")
class Test_delete(APITestBase):
    # @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("账号管理-跟随者账号-解绑账户")
    def test_account_unbindPa_follow(self, var_manager, logged_session):
        follow_pass_id = var_manager.get_variable("follow_pass_id")
        params = {
            "traderId": follow_pass_id
        }
        response = self.send_post_request(
            logged_session,
            '/blockchain/account/unbindPa',
            params=params
        )

        self.assert_json_value(
            response,
            "$.success",
            True,
            "响应success字段应为true"
        )

    # @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("数据库查询-校验跟随者账号是否解绑成功")
    def test_dbbchain_follow(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库"):
            follow_account = var_manager.get_variable("follow_account")
            sql = f"SELECT id,server_id,broker_id,user_id,account,type,password,display,meta_trader_platform_id,password_type,subscribe_fee,status FROM bchain_trader WHERE account = %s"
            params = (follow_account,)

            db_data = self.query_database(
                db_transaction=db_transaction,
                sql=sql,
                params=params
            )

        with allure.step("2. 校验跟随者账号是否解绑成功"):
            status_list = [record["status"] for record in db_data]
            for i in status_list:
                assert i == "UNBIND", f"跟随者账号解绑失败，实际状态为: {i}"
            logging.info(f"跟随者账号解绑成功")

    @allure.title("账号管理-交易员账号-解绑账户")
    def test_account_unbindPa_trader(self, var_manager, logged_session):
        trader_pass_id = var_manager.get_variable("trader_pass_id")
        params = {
            "traderId": trader_pass_id
        }
        response = self.send_post_request(
            logged_session,
            '/blockchain/account/unbindPa',
            params=params
        )

        self.assert_json_value(
            response,
            "$.success",
            True,
            "响应success字段应为true"
        )

    @allure.title("数据库查询-校验交易员账号是否解绑成功")
    def test_dbbchain_trader(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库"):
            trader_account = var_manager.get_variable("trader_account")
            sql = f"SELECT id,server_id,broker_id,user_id,account,type,password,display,meta_trader_platform_id,password_type,subscribe_fee,status FROM bchain_trader WHERE account = %s"
            params = (trader_account,)

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
