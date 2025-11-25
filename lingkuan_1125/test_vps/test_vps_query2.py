import time
import math
import allure
import logging
import pytest
import re
from lingkuan_1120.VAR.VAR import *
from lingkuan_1120.conftest import var_manager
from lingkuan_1120.commons.api_base import *
from template.commons.jsonpath_utils import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("运营监控-历史指令-查询校验")
class TestVPShistoryCommands(APITestBase):
    # 实例化JsonPath工具类（全局复用）
    json_utils = JsonPathUtils()

    @allure.title("品种查询校验")
    def test_query_symbol(self, var_manager, logged_session):
        with allure.step(f"1. 发送查询请求"):
            new_user = var_manager.get_variable("new_user")
            symbol = new_user["symbol"]
            data = {
                "page": 1,
                "limit": 50,
                "asc": "",
            }

            response = self.send_post_request(
                logged_session,
                '/bargain/historyCommands',
                json_data=data
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

        with allure.step(f"3. 品种查询校验"):
            # 修复：正确的 JsonPath 表达式（提取所有记录的 symbol）
            symbol_list = self.json_utils.extract(
                response.json(),
                "$.data.list[*].followBaiginInstructSubVOList[*].symbol",
                default=[],
                multi_match=True
            )

            # 日志和 Allure 附件优化
            if not symbol_list:
                attach_body = f"品种查询校验[{symbol}]，返回的symbol列表为空（暂无数据）"
                logger.info(attach_body)
                allure.attach(
                    body=attach_body,
                    name=f"品种:{symbol}查询结果",
                    attachment_type="text/plain"
                )
                # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                pytest.skip(f"品种查询[{symbol}]暂无数据，跳过校验")
            else:
                attach_body = f"品种查询[{symbol}]，返回 {len(symbol_list)} 条记录"
                logger.info(attach_body)
                allure.attach(
                    body=attach_body,
                    name=f"品种:{symbol}查询结果",
                    attachment_type="text/plain"
                )

            # 修复：去掉 int() 强制转换（status 是字符串，symbol 也是字符串）
            for idx, actual_status in enumerate(symbol_list):
                self.verify_data(
                    actual_value=symbol,
                    expected_value=actual_status,
                    op=CompareOp.IN,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的symbol应为{symbol}，实际为{actual_status}",
                    attachment_name=f"品种:{symbol}第 {idx + 1} 条记录校验"
                )

    @allure.title("品种查询校验-查询结果为空")
    def test_query_symbolNO(self, var_manager, logged_session):
        with allure.step(f"1. 发送查询请求"):
            data = {
                "page": 1,
                "limit": 50,
                "instructionType": "",
                "symbol": "测试品种",
                "type": "",
                "creatorName": "",
                "startTime": "",
                "endTime": "",
                "cloudType": [],
                "cloud": [],
                "operationType": "",
                "ifFollows": [],
                "detailStatus": "",
                "detailAccount": "",
                "orderNo": "",
                "magical": "",
                "status": [],
                "isClosed": True,
                "platformType": ""
            }

            response = self.send_post_request(
                logged_session,
                '/bargain/historyCommands',
                json_data=data
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

        with allure.step("3. 查询校验"):
            self.json_utils.assert_empty_list(
                data=response.json(),
                expression="$.data.list",
            )
            logging.info("查询结果符合预期：list为空列表")
            allure.attach("查询结果为空，符合预期", 'text/plain')
