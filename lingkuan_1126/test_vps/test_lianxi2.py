import time
import math
import allure
import logging
import pytest
import re
from lingkuan_1126.VAR.VAR import *
from lingkuan_1126.conftest import var_manager
from lingkuan_1126.commons.api_base import *
from template.commons.jsonpath_utils import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("查询校验")
class TestVPSquery(APITestBase):
    @allure.story("运营监控-订单列表")
    class TestVPSquerylog(APITestBase):
        # 实例化JsonPath工具类（全局复用）
        json_utils = JsonPathUtils()

        @pytest.mark.url("vps")
        @allure.title("喊单账号查询校验")
        def test_query_sourceUser(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                new_user = var_manager.get_variable("new_user")
                sourceUser = new_user["account"]
                params = {
                    "page": 1,
                    "limit": 50,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "brokeName": "",
                    "platform": "",
                    "symbol": "",
                    "orderNo": "",
                    "sourceUser": sourceUser,
                    "magicals": "",
                    "serverName": "",
                    "closeServerName": "",
                    "orderingSystem": "",
                    "startTime": DATETIME_INIT,
                    "endTime": DATETIME_NOW,
                    "closeStartTime": "",
                    "closeEndTime": "",
                    "requestOpenTimeStart": "",
                    "requestOpenTimeEnd": "",
                    "requestCloseTimeStart": "",
                    "requestCloseTimeEnd": "",
                    "platformType": "",
                }

                response = self.send_get_request(
                    logged_session,
                    '/subcontrol/trader/orderSlipDetail',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

            with allure.step(f"3. 喊单账号查询校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 sourceUser）
                sourceUser_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].sourceUser",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not sourceUser_list:
                    attach_body = f"喊单账号查询校验[{sourceUser}]，返回的sourceUser列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"喊单账号:{sourceUser}查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"喊单账号查询[{sourceUser}]暂无数据，跳过校验")
                else:
                    attach_body = f"喊单账号查询[{sourceUser}]，返回 {len(sourceUser_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"喊单账号:{sourceUser}查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，sourceUser 也是字符串）
                for idx, actual_status in enumerate(sourceUser_list):
                    self.verify_data(
                        actual_value=sourceUser,
                        expected_value=actual_status,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的sourceUser应为{sourceUser}，实际为{actual_status}",
                        attachment_name=f"喊单账号:{sourceUser}第 {idx + 1} 条记录校验"
                    )

        @pytest.mark.url("vps")
        @allure.title("喊单账号查询校验-查询结果为空")
        def test_query_sourceUserNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 50,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "brokeName": "",
                    "platform": "",
                    "sourceUser": "9999999999",
                    "symbol": "",
                    "orderNo": "",
                    "magicals": "",
                    "serverName": "",
                    "closeServerName": "",
                    "orderingSystem": "",
                    "startTime": DATETIME_INIT,
                    "endTime": DATETIME_NOW,
                    "closeStartTime": "",
                    "closeEndTime": "",
                    "requestOpenTimeStart": "",
                    "requestOpenTimeEnd": "",
                    "requestCloseTimeStart": "",
                    "requestCloseTimeEnd": "",
                    "platformType": "",
                }

                response = self.send_get_request(
                    logged_session,
                    '/subcontrol/trader/orderSlipDetail',
                    params=params
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
