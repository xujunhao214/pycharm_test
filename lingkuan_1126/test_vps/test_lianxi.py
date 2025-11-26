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
        @allure.title("券商查询校验")
        def test_query_brokeName(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                brokeName = var_manager.get_variable("broker_name")
                # 统一转为小写，用于后续不区分大小写校验（避免硬编码大小写问题）
                brokeName_lower = brokeName.lower()
                params = {
                    "page": 1,
                    "limit": 50,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "brokeName": brokeName_lower,
                    "platform": "",
                    "account": "",
                    "symbol": "",
                    "orderNo": "",
                    "sourceUser": "",
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

            with allure.step(f"3. 券商查询校验（不区分大小写，包含{brokeName}）"):
                # 提取所有记录的 brokerName
                brokeName_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].brokeName",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not brokeName_list:
                    attach_body = f"券商查询校验[{brokeName}]，返回的brokerName列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"券商:{brokeName}查询结果",
                        attachment_type="text/plain"
                    )
                    pytest.skip(f"券商查询[{brokeName}]暂无数据，跳过校验")
                else:
                    attach_body = f"券商查询[{brokeName}]，返回 {len(brokeName_list)} 条记录：{brokeName_list}"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"券商:{brokeName}查询结果",
                        attachment_type="text/plain"
                    )

                # 核心修复：不区分大小写的模糊匹配校验
                for idx, actual_name in enumerate(brokeName_list):
                    # 实际值转为小写，与预期值（小写）进行包含匹配
                    actual_name_lower = actual_name.lower()

                    # 思路：将「实际值包含预期值」转为「预期值 in 实际值」，并统一大小写
                    self.verify_data(
                        actual_value=brokeName_lower,
                        expected_value=actual_name_lower,
                        op=CompareOp.IN,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的brokerName[{actual_name}]应包含{brokeName}",
                        attachment_name=f"券商:{brokeName}第 {idx + 1} 条记录校验"
                    )