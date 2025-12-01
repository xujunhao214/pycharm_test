import time
import math
import allure
import logging
import pytest
import re
from lingkuan_1029.VAR.VAR import *
from lingkuan_1029.conftest import var_manager
from lingkuan_1029.commons.api_base import *
from template.commons.jsonpath_utils import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("VPS看板-查询校验")
class TestVPSquery(APITestBase):
    @allure.story("VPS看板-日志查询")
    class TestVPSquerylog(APITestBase):
        # 实例化JsonPath工具类（全局复用）
        json_utils = JsonPathUtils()

        # 定义所有需要测试的状态（作为参数化数据源）
        STATUS_logType = [
            ("连接日志", "日志类型"),
            ("交易日志", "日志类型")
        ]

        @pytest.mark.url("vps")
        @pytest.mark.parametrize("status, status_desc", STATUS_logType)
        @allure.title("查询：{status_desc}（{status}）")
        def test_query_logType(self, var_manager, logged_session, status, status_desc):
            with allure.step(f"1. 发送请求：查询{status_desc}（{status}）"):
                json_data = {
                    "page": 1,
                    "limit": 100,
                    "platformType": [],
                    "startDate": DATETIME_INIT,
                    "endDate": DATETIME_NOW,
                    "keywords": [],
                    "logInfo": [],
                    "cloudId": [],
                    "vpsId": [],
                    "source": [],
                    "logType": [status]
                }

                response = self.send_post_request(
                    logged_session,
                    '/subcontrol/eslog/queryLogsPage',
                    json_data=json_data
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

            with allure.step(f"3. 查询结果校验：返回记录的typeDec应为{status}"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 typeDec）
                typeDec_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].typeDec",
                    default=[],
                    multi_match=True
                )
                # var_manager.set_runtime_variable("query_typeDec_list", typeDec_list)

                # 日志和 Allure 附件优化
                if not typeDec_list:
                    attach_body = f"查询[{status}]，返回的typeDec列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"日志类型:{status}查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"查询[{status}]暂无数据，跳过校验")
                else:
                    attach_body = f"查询[{status}]，返回 {len(typeDec_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"日志类型:{status}查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，typeDec 也是字符串）
                for idx, actual_status in enumerate(typeDec_list):
                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=status,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的typeDec应为{status}，实际为{actual_status}",
                        attachment_name=f"日志类型:{status}第 {idx + 1} 条记录校验"
                    )