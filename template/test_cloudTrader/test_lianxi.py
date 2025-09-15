import time
from template.commons.api_base import APITestBase, CompareOp
import allure
import logging
import pytest
import json
from template.VAR.VAR import *
from template.commons.jsonpath_utils import *
from template.commons.random_generator import *


@allure.feature("账号管理")
class Test_create:
    @allure.story("跟随者账户查询校验")
    class Test_trader(APITestBase):
        # 实例化JsonPath工具类（全局复用）
        json_utils = JsonPathUtils()

        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
        @allure.title("分红用户查询")
        def test_query_followerTa(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                login_config = var_manager.get_variable("login_config")
                dividendUser = login_config.get("username")
                params = {
                    "_t": current_timestamp_seconds,
                    "page": 1,
                    "limit": 100,
                    "type": "",
                    "status": "",
                    "dividendTimeBegin": "",
                    "dividendTimeEnd": "",
                    "followerUser": "",
                    "followerTa": "",
                    "dividendUser": dividendUser
                }
                response = self.send_get_request(
                    logged_session,
                    '/agent/agentLevelDividend/page',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step(f"3. 查询结果校验"):
                dividendUser_list = self.json_utils.extract(
                    response.json(),
                    "$.result.list[*].slaveRecords[*].dividendUser",
                    default=[],
                    multi_match=True
                )

                if not dividendUser_list:
                    attach_body = f"分红用户查询：{dividendUser}，返回的dividendUser列表为空（暂无数据）"
                else:
                    attach_body = f"分红用户查询：{dividendUser}，返回 {len(dividendUser_list)} 条记录，dividendUser值如下：\n" + \
                                  "\n".join([f"第 {idx + 1} 条：{s}" for idx, s in enumerate(dividendUser_list)])

                allure.attach(
                    body=attach_body,
                    name=f"分红用户:{dividendUser}查询结果",
                    attachment_type="text/plain"
                )

                for idx, followerUserlist in enumerate(dividendUser_list):
                    self.verify_data(
                        actual_value=followerUserlist,
                        expected_value=dividendUser,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的dividendUser应为{followerUserlist}",
                        attachment_name=f"分红用户:{dividendUser}第 {idx + 1} 条记录校验"
                    )
