import time
from template.commons.api_base import APITestBase, CompareOp
import allure
import logging
import pytest
import requests
from template.VAR.VAR import *
from template.commons.jsonpath_utils import *
from template.commons.random_generator import *


@allure.feature("账号管理")
class Test_create:
    @allure.story("创建交易员账号")
    class Test_trader(APITestBase):
        # 实例化JsonPath工具类（全局复用）
        json_utils = JsonPathUtils()

        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
        @allure.title("服务器查询")
        def test_query_server_id(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                trader_server_id = var_manager.get_variable("trader_server_id")
                params = {
                    "_t": current_timestamp_seconds,
                    "server_id": trader_server_id,
                    "column": "id",
                    "order": "desc",
                    "pageNo": 1,
                    "pageSize": 20,
                    "status": "VERIFICATION,PASS,PENDING,ERROR",
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
                server_id_list = self.json_utils.extract(
                    response.json(),
                    "$.result.records[*].server_id",
                    default=[],
                    multi_match=True
                )

                if not server_id_list:
                    attach_body = f"查询{trader_server_id}服务器，返回的server_id列表为空（暂无数据）"
                else:
                    attach_body = f"查询{trader_server_id}服务器：返回 {len(server_id_list)} 条记录，server_id值如下：\n" + \
                                  "\n".join([f"第 {idx + 1} 条：{s}" for idx, s in enumerate(server_id_list)])

                allure.attach(
                    body=attach_body,
                    name=f"{trader_server_id}查询结果",
                    attachment_type="text/plain"
                )

                for idx, server_id in enumerate(server_id_list):
                    self.verify_data(
                        actual_value=server_id,
                        expected_value=trader_server_id,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的server_id符合预期",
                        attachment_name=f"第 {idx + 1} 条记录的server_id校验"
                    )
