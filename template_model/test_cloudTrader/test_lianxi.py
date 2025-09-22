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
        def test_query_combination(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                follow_user_id = var_manager.get_variable("follow_user_id")
                follow_account = var_manager.get_variable("follow_account")
                follow_broker_id = var_manager.get_variable("follow_broker_id")
                follow_server_id = var_manager.get_variable("follow_server_id")
                params = {
                    "_t": current_timestamp_seconds,
                    "user_id": follow_user_id,
                    "status": "PASS",
                    "account": follow_account,
                    "broker_id": follow_broker_id,
                    "server_id": follow_server_id,
                    "subscribe_fee": 0,
                    # "level_id": 3,
                    "connected": 1,
                    "column": "id",
                    "order": "desc",
                    "pageNo": 1,
                    "pageSize": 20,
                    "type": "SLAVE_REAL"
                }
                response = self.send_get_request(
                    logged_session,
                    '/online/cgform/api/getData/2c9a814a81d3a91b0181e04a36e00001',
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
                recommenders_user_id_list = self.json_utils.extract(
                    response.json(),
                    "$.result.records[*].recommenders_user_id",
                    default=[],
                    multi_match=True
                )

                if not recommenders_user_id_list:
                    pytest.fail("查询结果为空，不符合预期")
                else:
                    attach_body = f"推荐人ID查询：{follow_user_id}，返回 {len(recommenders_user_id_list)} 条记录，recommenders_user_id值如下：\n" + \
                                  "\n".join([f"第 {idx + 1} 条：{s}" for idx, s in enumerate(recommenders_user_id_list)])

                allure.attach(
                    body=attach_body,
                    name=f"{follow_user_id}查询结果",
                    attachment_type="text/plain"
                )

                for idx, recommenders_user_id in enumerate(recommenders_user_id_list):
                    self.verify_data(
                        actual_value=follow_user_id,
                        expected_value=recommenders_user_id,
                        op=CompareOp.IN,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的推荐人ID符合预期",
                        attachment_name=f"第 {idx + 1} 条记录的推荐人ID校验"
                    )