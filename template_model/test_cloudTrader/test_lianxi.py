import time
from template_model.commons.api_base import APITestBase, CompareOp
import allure
import logging
import json
import pytest
from template_model.VAR.VAR import *
from template_model.commons.jsonpath_utils import *
from template_model.commons.random_generator import *


@allure.feature("账号管理-跟随者账户")
class Test_create:
    @allure.story("跟随者账户查询校验")
    class Test_trader(APITestBase):
        # 实例化JsonPath工具类（全局复用）
        json_utils = JsonPathUtils()

        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
        @allure.title("组合查询")
        def test_query_all(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                follow_account = var_manager.get_variable("follow_account")
                trader_account = var_manager.get_variable("trader_account")
                trader_master_nickname = var_manager.get_variable("trader_master_nickname")
                follow_nickname = var_manager.get_variable("follow_nickname")
                trader_master_server = var_manager.get_variable("trader_master_server")
                follow_slave_server = var_manager.get_variable("follow_slave_server")
                trader_pass_id = var_manager.get_variable("trader_pass_id")
                follow_pass_id = var_manager.get_variable("follow_pass_id")
                login_config = var_manager.get_variable("login_config")
                username_log = login_config["username"]
                params = {
                    "_t": current_timestamp_seconds,
                    "account": follow_account,
                    "following_mode": 2,
                    "master_account": trader_account,
                    "master_nickname": trader_master_nickname,
                    "nickname": follow_nickname,
                    "master_server": trader_master_server,
                    "slave_server": follow_slave_server,
                    "master_id": trader_pass_id,
                    "slave_id": follow_pass_id,
                    "username": username_log,
                    "pause": 0,
                    "pageNo": 1,
                    "pageSize": 20,
                    "status": "NORMAL,AUDIT"
                }
                response = self.send_get_request(
                    logged_session,
                    '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step("3. 查询校验"):
                account_list = self.json_utils.extract(
                    response.json(),
                    "$.result.data.records[*].account",
                    default=[],
                    multi_match=True
                )

                if not account_list:
                    pytest.fail("查询结果为空，不符合预期")
                else:
                    attach_body = f"跟随者账户查询：{follow_account}，返回 {len(account_list)} 条记录，account值如下：\n" + \
                                  "\n".join([f"第 {idx + 1} 条：{s}" for idx, s in enumerate(account_list)])

                allure.attach(
                    body=attach_body,
                    name=f"{follow_account}查询结果",
                    attachment_type="text/plain"
                )

                for idx, account in enumerate(account_list):
                    self.verify_data(
                        actual_value=account,
                        expected_value=follow_account,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的跟随者账户符合预期",
                        attachment_name=f"第 {idx + 1} 条记录的跟随者账户校验"
                    )
