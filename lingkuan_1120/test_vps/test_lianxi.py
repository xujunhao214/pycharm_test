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


@allure.feature("运营监控-订单列表-查询校验")
class TestVPShistoryCommands(APITestBase):
    # 实例化JsonPath工具类（全局复用）
    json_utils = JsonPathUtils()

    @pytest.mark.url("vps")
    @allure.title("组合查询")
    def test_query_combination(self, var_manager, logged_session):
        with allure.step(f"1. 发送查询请求"):
            brokeName = var_manager.get_variable("broker_name")
            new_user = var_manager.get_variable("new_user")
            account = new_user["account"]
            params = {
                "page": 1,
                "limit": 100,
                "flag": 1,
                "asc": "false",
                "order": "close_time",
                "isRepeat": "false",
                "brokeName": brokeName,
                "account": account,
                "platform": "",
                "sourceUser": "",
                "orderingSystem": "",
                "startTime": five_time,
                "endTime": DATETIME_NOW,
                "closeStartTime": five_time,
                "closeEndTime": DATETIME_NOW,
                "requestOpenTimeStart": five_time,
                "requestOpenTimeEnd": DATETIME_NOW,
                "requestCloseTimeStart": five_time,
                "requestCloseTimeEnd": DATETIME_NOW,
                "platformType": ""
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

        with allure.step(f"3. 平仓请求时间查询校验"):
            # 修复：正确的 JsonPath 表达式（提取所有记录的 requestCloseTime）
            requestCloseTime_list = self.json_utils.extract(
                response.json(),
                "$.data.list[*].requestCloseTime",
                default=[],
                multi_match=True
            )

            # 日志和 Allure 附件优化
            if not requestCloseTime_list:
                attach_body = f"平仓请求时间查询校验，返回的requestCloseTime列表为空（暂无数据）"
                logger.info(attach_body)
                allure.attach(
                    body=attach_body,
                    name=f"平仓请求时间查询结果",
                    attachment_type="text/plain"
                )
                # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                pytest.skip(f"平仓请求时间查询暂无数据，跳过校验")
            else:
                attach_body = f"平仓请求时间查询，返回 {len(requestCloseTime_list)} 条记录"
                logger.info(attach_body)
                allure.attach(
                    body=attach_body,
                    name=f"平仓请求时间查询结果",
                    attachment_type="text/plain"
                )

            # 修复：去掉 int() 强制转换（status 是字符串，requestCloseTime 也是字符串）
            for idx, actual_status in enumerate(requestCloseTime_list):
                self.verify_data(
                    actual_value=actual_status,
                    expected_value=five_time,
                    op=CompareOp.GE,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的requestCloseTime应大于{five_time}",
                    attachment_name=f"平仓请求时间:{actual_status}第 {idx + 1} 条记录校验"
                )

                self.verify_data(
                    actual_value=actual_status,
                    expected_value=DATETIME_NOW,
                    op=CompareOp.LE,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的requestCloseTime应小于{DATETIME_NOW}",
                    attachment_name=f"平仓请求时间:{actual_status}第 {idx + 1} 条记录校验"
                )

        with allure.step(f"4. 账号查询校验"):
            # 修复：正确的 JsonPath 表达式（提取所有记录的 account）
            account_list = self.json_utils.extract(
                response.json(),
                "$.data.list[*].account",
                default=[],
                multi_match=True
            )

            # 日志和 Allure 附件优化
            if not account_list:
                attach_body = f"账号查询校验[{account}]，返回的account列表为空（暂无数据）"
                logger.info(attach_body)
                allure.attach(
                    body=attach_body,
                    name=f"账号:{account}查询结果",
                    attachment_type="text/plain"
                )
                # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                pytest.skip(f"账号查询[{account}]暂无数据，跳过校验")
            else:
                attach_body = f"账号查询[{account}]，返回 {len(account_list)} 条记录"
                logger.info(attach_body)
                allure.attach(
                    body=attach_body,
                    name=f"账号:{account}查询结果",
                    attachment_type="text/plain"
                )

            # 修复：去掉 int() 强制转换（status 是字符串，account 也是字符串）
            for idx, actual_status in enumerate(account_list):
                self.verify_data(
                    actual_value=account,
                    expected_value=actual_status,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的account应为{account}，实际为{actual_status}",
                    attachment_name=f"账号:{account}第 {idx + 1} 条记录校验"
                )

        with allure.step(f"5. 券商查询校验"):
            # 修复：正确的 JsonPath 表达式（提取所有记录的 brokeName）
            brokeName_list = self.json_utils.extract(
                response.json(),
                "$.data.list[*].brokeName",
                default=[],
                multi_match=True
            )

            # 日志和 Allure 附件优化
            if not brokeName_list:
                attach_body = f"券商查询校验[{brokeName}]，返回的brokeName列表为空（暂无数据）"
                logger.info(attach_body)
                allure.attach(
                    body=attach_body,
                    name=f"券商:{brokeName}查询结果",
                    attachment_type="text/plain"
                )
                # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                pytest.skip(f"券商查询[{brokeName}]暂无数据，跳过校验")
            else:
                attach_body = f"券商查询[{brokeName}]，返回 {len(brokeName_list)} 条记录"
                logger.info(attach_body)
                allure.attach(
                    body=attach_body,
                    name=f"券商:{brokeName}查询结果",
                    attachment_type="text/plain"
                )

            # 修复：去掉 int() 强制转换（status 是字符串，brokeName 也是字符串）
            for idx, actual_status in enumerate(brokeName_list):
                self.verify_data(
                    actual_value=brokeName,
                    expected_value=actual_status,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的brokeName应为{brokeName}，实际为{actual_status}",
                    attachment_name=f"券商:{brokeName}第 {idx + 1} 条记录校验"
                )
