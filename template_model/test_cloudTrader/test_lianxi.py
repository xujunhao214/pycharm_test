import time
import statistics
from typing import List, Union
from template_model.commons.api_base import APITestBase, CompareOp
import allure
import logging
import json
import pytest
from template_model.VAR.VAR import *
from template_model.commons.jsonpath_utils import *
from template_model.commons.random_generator import *

# 配置日志（确保输出格式清晰）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@allure.story("开仓/平仓时间差数据统计")
class Test_trader(APITestBase):
    # 实例化JsonPath工具类（全局复用）
    json_utils = JsonPathUtils()

    # @pytest.mark.skipif(True, reason="该用例暂时跳过")
    @allure.title("MT4账号查询")
    def test_query_trader_id(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            trader_pass_id = var_manager.get_variable("trader_pass_id")
            trader_account = var_manager.get_variable("trader_account")
            params = {
                "_t": current_timestamp_seconds,
                "trader_id": trader_pass_id,
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "superQueryMatchType": "and"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/402883977b38c9ca017b38c9d0960001',
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
            trader_id_list = self.json_utils.extract(
                response.json(),
                "$.result.records[*].trader_id",
                default=[],
                multi_match=True
            )

            if not trader_id_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"MT4账号查询-{trader_pass_id}，返回 {len(trader_id_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"MT4账号-{trader_pass_id}查询结果",
                attachment_type="text/plain"
            )

            for idx, trader_idlt in enumerate(trader_id_list):
                self.verify_data(
                    actual_value=trader_idlt,
                    expected_value=trader_pass_id,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的MT4账号查询符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的MT4账号校验,MT4账号是{trader_account}"
                )
