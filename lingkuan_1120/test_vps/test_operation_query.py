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


@allure.feature("运营监控-查询校验")
class TestVPSbargainQuery(APITestBase):
    @allure.story("运营监控-历史指令-查询校验")
    class TestVPShistoryCommands(APITestBase):
        # 实例化JsonPath工具类（全局复用）
        json_utils = JsonPathUtils()

        @allure.title("时间查询校验")
        def test_query_time(self, var_manager, logged_session):
            with allure.step(f"1. 发送时间查询请求"):
                data = {
                    "page": 1,
                    "limit": 50,
                    "instructionType": "",
                    "symbol": "",
                    "type": "",
                    "creatorName": "",
                    "startTime": DATETIME_INIT,
                    "endTime": DATETIME_NOW,
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

            with allure.step(f"3. 查询结果校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 responseOpnetime）
                responseOpnetime_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].followBaiginInstructSubVOList[*].createTime",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not responseOpnetime_list:
                    pytest.fail("查询结果为空，不符合预期")
                else:
                    attach_body = f"查询开始时间：[{five_time}]，结束时间：[{DATETIME_NOW}]，返回 {len(responseOpnetime_list)} 条记录"

                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"时间查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，dateTime 也是字符串）
                for idx, actual_status in enumerate(responseOpnetime_list):
                    self.verify_data(
                        actual_value=str(actual_status),
                        expected_value=str(DATETIME_INIT),
                        op=CompareOp.GE,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的dateTime应为{actual_status}",
                        attachment_name=f"时间:{actual_status}第 {idx + 1} 条记录校验"
                    )

                    self.verify_data(
                        actual_value=str(actual_status),
                        expected_value=str(DATETIME_NOW),
                        op=CompareOp.LE,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的dateTime应为{actual_status}",
                        attachment_name=f"时间:{actual_status}第 {idx + 1} 条记录校验"
                    )

        @allure.title("时间查询校验-查询结果为空")
        def test_query_timeNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送时间查询请求"):
                data = {
                    "page": 1,
                    "limit": 50,
                    "instructionType": "",
                    "symbol": "",
                    "type": "",
                    "creatorName": "",
                    "startTime": DATETIME_NOW,
                    "endTime": DATETIME_INIT,
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

        # 定义所有需要测试的状态（作为参数化数据源）
        STATUS_instructionType = [
            (0, "分配"),
            (1, "复制"),
            (2, "策略")
        ]

        @pytest.mark.parametrize("status, status_desc", STATUS_instructionType)
        @allure.title("指令类型查询：{status_desc}（{status}）")
        def test_query_instructionType(self, var_manager, logged_session, status, status_desc):
            with allure.step(f"1. 发送请求：指令类型查询-{status_desc}（{status}）"):
                data = {
                    "page": 1,
                    "limit": 50,
                    "instructionType": status,
                    "symbol": "",
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

            with allure.step(f"3. 指令类型查询结果校验：返回记录的instructionType应为{status}"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 instructionType）
                instructionType_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].instructionType",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not instructionType_list:
                    attach_body = f"指令类型查询[{status}]，返回的instructionType列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"指令类型:{status}查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"指令类型查询[{status}]暂无数据，跳过校验")
                else:
                    attach_body = f"指令类型查询[{status}]，返回 {len(instructionType_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"指令类型:{status}查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，instructionType 也是字符串）
                for idx, actual_status in enumerate(instructionType_list):
                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=status,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的instructionType应为{status}，实际为{actual_status}",
                        attachment_name=f"指令类型:{status}第 {idx + 1} 条记录校验"
                    )

        @allure.title("品种查询校验")
        def test_query_symbol(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                new_user = var_manager.get_variable("new_user")
                symbol = new_user["symbol"]
                data = {
                    "page": 1,
                    "limit": 50,
                    "instructionType": "",
                    "symbol": symbol,
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

        # 定义所有需要测试的状态（作为参数化数据源）
        STATUS_Type = [
            (0, "buy"),
            (1, "sell"),
            (2, "buy&sell")
        ]

        @pytest.mark.parametrize("status, status_desc", STATUS_Type)
        @allure.title("类型查询：{status_desc}（{status}）")
        def test_query_Type(self, var_manager, logged_session, status, status_desc):
            with allure.step(f"1. 发送请求：查询{status_desc}（{status}）"):
                data = {
                    "page": 1,
                    "limit": 50,
                    "instructionType": "",
                    "symbol": "",
                    "type": status,
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

            with allure.step(f"3. 查询结果校验：返回记录的type应为{status}"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 type）
                type_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].type",
                    default=[],
                    multi_match=True
                )
                # var_manager.set_runtime_variable("query_type_list", type_list)

                # 日志和 Allure 附件优化
                if not type_list:
                    attach_body = f"查询[{status}]，返回的type列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"类型:{status}查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"查询[{status}]暂无数据，跳过校验")
                else:
                    attach_body = f"查询[{status}]，返回 {len(type_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"类型:{status}查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，type 也是字符串）
                for idx, actual_status in enumerate(type_list):
                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=status,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的type应为{status}，实际为{actual_status}",
                        attachment_name=f"类型:{status}第 {idx + 1} 条记录校验"
                    )

        # 定义所有需要测试的状态（作为参数化数据源）
        STATUS_cloudType = [
            (0, "VPS"),
            (1, "交易下单"),
            (2, "云策略"),
            (3, "单账号操作")
        ]

        @pytest.mark.parametrize("status, status_desc", STATUS_cloudType)
        @allure.title("来源查询：{status_desc}（{status}）")
        def test_query_cloudType(self, var_manager, logged_session, status, status_desc):
            with allure.step(f"1. 发送请求：查询{status_desc}（{status}）"):
                data = {
                    "page": 1,
                    "limit": 50,
                    "instructionType": "",
                    "symbol": "",
                    "type": "",
                    "creatorName": "",
                    "startTime": "",
                    "endTime": "",
                    "cloudType": [status],
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

            with allure.step(f"3. 查询结果校验：返回记录的cloudType应为{status}"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 cloudType）
                sourceType_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].sourceType",
                    default=[],
                    multi_match=True
                )
                # var_manager.set_runtime_variable("query_sourceType_list", sourceType_list)

                # 日志和 Allure 附件优化
                if not sourceType_list:
                    attach_body = f"查询[{status}]，返回的sourceType列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"来源查询:{status}查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"查询[{status}]暂无数据，跳过校验")
                else:
                    attach_body = f"查询[{status}]，返回 {len(sourceType_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"来源:{status}查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，sourceType 也是字符串）
                for idx, actual_status in enumerate(sourceType_list):
                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=status,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的sourceType应为{status}，实际为{actual_status}",
                        attachment_name=f"来源:{status}第 {idx + 1} 条记录校验"
                    )

        @allure.title("云策略查询校验")
        def test_query_cloudName(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                data = {
                    "page": 1,
                    "limit": 50,
                    "instructionType": "",
                    "symbol": "",
                    "type": "",
                    "creatorName": "",
                    "startTime": "",
                    "endTime": "",
                    "cloudType": [],
                    "cloud": [
                        {
                            "cloudName": "xjh测试策略",
                            "cloudAccount": None,
                            "id": 999
                        }
                    ],
                    "operationType": "",
                    "ifFollows": [],
                    "detailStatus": "",
                    "detailAccount": "",
                    "orderNo": "",
                    "magical": "",
                    "status": [],
                    "isClosed": True,
                    "cloudName": ""
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

            with allure.step(f"3. 云策略查询校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 account）
                cloudName_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].cloudName",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not cloudName_list:
                    attach_body = f"云策略查询校验，返回的cloudName列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"云策略查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"云策略查询暂无数据，跳过校验")
                else:
                    attach_body = f"云策略查询，返回 {len(cloudName_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"云策略查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，cloudName 也是字符串）
                for idx, actual_status in enumerate(cloudName_list):
                    self.verify_data(
                        actual_value=str(actual_status),
                        expected_value=str("xjh测试策略"),
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的cloudName应为1，实际为{actual_status}",
                        attachment_name=f"云策略第 {idx + 1} 条记录校验"
                    )

        # 定义所有需要测试的状态（作为参数化数据源）
        STATUS_operationType = [
            (0, "开仓"),
            (1, "平仓")
        ]

        @pytest.mark.parametrize("status, status_desc", STATUS_operationType)
        @allure.title("开平仓查询：{status_desc}（{status}）")
        def test_query_operationType(self, var_manager, logged_session, status, status_desc):
            with allure.step(f"1. 发送请求：查询{status_desc}（{status}）"):
                data = {
                    "page": 1,
                    "limit": 50,
                    "instructionType": "",
                    "symbol": "",
                    "type": "",
                    "creatorName": "",
                    "startTime": "",
                    "endTime": "",
                    "cloudType": [],
                    "cloud": [],
                    "operationType": status,
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

            with allure.step(f"3. 查询结果校验：返回记录的operationType应为{status}"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 operationType）
                operationType_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].operationType",
                    default=[],
                    multi_match=True
                )
                # var_manager.set_runtime_variable("query_operationType_list", operationType_list)

                # 日志和 Allure 附件优化
                if not operationType_list:
                    attach_body = f"查询[{status}]，返回的operationType列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"开平仓:{status}查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"查询[{status}]暂无数据，跳过校验")
                else:
                    attach_body = f"查询[{status}]，返回 {len(operationType_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"开平仓:{status}查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，operationType 也是字符串）
                for idx, actual_status in enumerate(operationType_list):
                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=status,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的operationType应为{status}，实际为{actual_status}",
                        attachment_name=f"开平仓:{status}第 {idx + 1} 条记录校验"
                    )

        # 定义所有需要测试的状态（作为参数化数据源）
        STATUS_ifFollows = [
            (0, "手动"),
            (1, "跟单")
        ]

        @pytest.mark.parametrize("status, status_desc", STATUS_ifFollows)
        @allure.title("下单方式查询：{status_desc}（{status}）")
        def test_query_ifFollows(self, var_manager, logged_session, status, status_desc):
            with allure.step(f"1. 发送请求：查询{status_desc}（{status}）"):
                data = {
                    "page": 1,
                    "limit": 50,
                    "instructionType": "",
                    "symbol": "",
                    "type": "",
                    "creatorName": "",
                    "startTime": "",
                    "endTime": "",
                    "cloudType": [],
                    "cloud": [],
                    "operationType": "",
                    "ifFollows": [status],
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

            with allure.step(f"3. 查询结果校验：返回记录的ifFollows应为{status}"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 ifFollows）
                ifFollows_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].ifFollow",
                    default=[],
                    multi_match=True
                )
                # var_manager.set_runtime_variable("query_ifFollows_list", ifFollows_list)

                # 日志和 Allure 附件优化
                if not ifFollows_list:
                    attach_body = f"查询[{status}]，返回的ifFollows列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"下单方式:{status}查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"查询[{status}]暂无数据，跳过校验")
                else:
                    attach_body = f"查询[{status}]，返回 {len(ifFollows_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"下单方式:{status}查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，ifFollows 也是字符串）
                for idx, actual_status in enumerate(ifFollows_list):
                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=status,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的ifFollows应为{status}，实际为{actual_status}",
                        attachment_name=f"下单方式:{status}第 {idx + 1} 条记录校验"
                    )

        @allure.title("操作人查询校验")
        def test_query_creatorName(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                login = var_manager.get_variable("login")
                creatorName = login["username"]
                data = {
                    "page": 1,
                    "limit": 50,
                    "instructionType": "",
                    "symbol": "",
                    "type": "",
                    "creatorName": creatorName,
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

            with allure.step(f"3. 操作人查询校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 creatorName）
                creatorName_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].creatorName",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not creatorName_list:
                    attach_body = f"操作人查询校验[{creatorName}]，返回的creatorName列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"操作人:{creatorName}查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"操作人查询[{creatorName}]暂无数据，跳过校验")
                else:
                    attach_body = f"操作人查询[{creatorName}]，返回 {len(creatorName_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"操作人:{creatorName}查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，creatorName 也是字符串）
                for idx, actual_status in enumerate(creatorName_list):
                    self.verify_data(
                        actual_value=creatorName,
                        expected_value=actual_status,
                        op=CompareOp.IN,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的creatorName应为{creatorName}，实际为{actual_status}",
                        attachment_name=f"操作人:{creatorName}第 {idx + 1} 条记录校验"
                    )

        @allure.title("操作人查询校验-查询结果为空")
        def test_query_creatorNameNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                data = {
                    "page": 1,
                    "limit": 50,
                    "instructionType": "",
                    "symbol": "",
                    "type": "",
                    "creatorName": "测试操作人",
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

        @allure.title("子指令状态查询校验-成功")
        def test_query_statusCommentsuccess(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                new_user = var_manager.get_variable("new_user")
                detailAccount = new_user["account"]
                data = {
                    "page": 1,
                    "limit": 50,
                    "instructionType": "",
                    "symbol": "",
                    "type": "",
                    "creatorName": "",
                    "startTime": "",
                    "endTime": "",
                    "cloudType": [],
                    "cloud": [],
                    "operationType": "",
                    "ifFollows": [],
                    "detailStatus": "1",
                    "detailAccount": detailAccount,
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

            with allure.step(f"3. 子指令状态查询校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 statusComment）
                statusComment_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].followBaiginInstructSubVOList[*].statusComment",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not statusComment_list:
                    attach_body = f"子指令状态查询校验，返回的statusComment列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"子指令状态查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"子指令状态查询暂无数据，跳过校验")
                else:
                    attach_body = f"子指令状态查询，返回 {len(statusComment_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"子指令状态查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，statusComment 也是字符串）
                for idx, actual_status in enumerate(statusComment_list):
                    self.verify_data(
                        actual_value="成功",
                        expected_value=actual_status,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的statusComment应为【成功】，实际为{actual_status}",
                        attachment_name=f"子指令状态第 {idx + 1} 条记录校验"
                    )

        @allure.title("子指令状态查询校验-失败")
        def test_query_statusCommenterror(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                new_user = var_manager.get_variable("new_user")
                detailAccount = new_user["account"]
                data = {
                    "page": 1,
                    "limit": 50,
                    "instructionType": "",
                    "symbol": "",
                    "type": "",
                    "creatorName": "",
                    "startTime": "",
                    "endTime": "",
                    "cloudType": [],
                    "cloud": [],
                    "operationType": "",
                    "ifFollows": [],
                    "detailStatus": "0",
                    "detailAccount": detailAccount,
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

            with allure.step(f"3. 子指令状态查询校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 statusComment）
                statusComment_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].followBaiginInstructSubVOList[*].statusComment",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not statusComment_list:
                    attach_body = f"子指令状态查询校验，返回的statusComment列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"子指令状态查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"子指令状态查询暂无数据，跳过校验")
                else:
                    attach_body = f"子指令状态查询，返回 {len(statusComment_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"子指令状态查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，statusComment 也是字符串）
                for idx, actual_status in enumerate(statusComment_list):
                    self.verify_data(
                        actual_value=actual_status,
                        expected_value="不是成功",
                        op=CompareOp.NE,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的statusComment应为【成功】，实际为{actual_status}",
                        attachment_name=f"子指令状态第 {idx + 1} 条记录校验"
                    )

        @allure.title("子指令状态查询校验-关联校验")
        def test_query_statusCommenterabout(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                data = {
                    "page": 1,
                    "limit": 50,
                    "instructionType": "",
                    "symbol": "",
                    "type": "",
                    "creatorName": "",
                    "startTime": "",
                    "endTime": "",
                    "cloudType": [],
                    "cloud": [],
                    "operationType": "",
                    "ifFollows": [],
                    "detailStatus": "0",
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
                    "子指令状态要与子指令账号或订单号或魔术号关联查询",
                    "响应msg字段应为：子指令状态要与子指令账号或订单号或魔术号关联查询"
                )

        @allure.title("子指令账号查询校验")
        def test_query_detailAccount(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                new_user = var_manager.get_variable("new_user")
                detailAccount = new_user["account"]
                data = {
                    "page": 1,
                    "limit": 50,
                    "instructionType": "",
                    "symbol": "",
                    "type": "",
                    "creatorName": "",
                    "startTime": "",
                    "endTime": "",
                    "cloudType": [],
                    "cloud": [],
                    "operationType": "",
                    "ifFollows": [],
                    "detailStatus": "",
                    "detailAccount": detailAccount,
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

            with allure.step(f"3. 子指令账号查询校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 account）
                account_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].followBaiginInstructSubVOList[*].account",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not account_list:
                    attach_body = f"子指令账号查询校验，返回的account列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"子指令账号查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"子指令账号{detailAccount}查询暂无数据，跳过校验")
                else:
                    attach_body = f"子指令账号{detailAccount}查询，返回 {len(account_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"子指令账号查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，account 也是字符串）
                for idx, actual_status in enumerate(account_list):
                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=detailAccount,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的account应为{detailAccount}，实际为{actual_status}",
                        attachment_name=f"子指令账号第 {idx + 1} 条记录校验"
                    )

        @allure.title("子指令账号查询校验-查询结果为空")
        def test_query_detailAccountNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                data = {
                    "page": 1,
                    "limit": 50,
                    "instructionType": "",
                    "symbol": "",
                    "type": "",
                    "creatorName": "",
                    "startTime": "",
                    "endTime": "",
                    "cloudType": [],
                    "cloud": [],
                    "operationType": "",
                    "ifFollows": [],
                    "detailStatus": "",
                    "detailAccount": "测试子账号查询",
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

        @allure.title("订单号查询校验")
        def test_query_order(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                vps_redis_comparable_list_open = var_manager.get_variable("vps_redis_comparable_list_open")
                orderNo = vps_redis_comparable_list_open[0]["order_no"]
                data = {
                    "page": 1,
                    "limit": 50,
                    "instructionType": "",
                    "symbol": "",
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
                    "orderNo": orderNo,
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

            with allure.step(f"3. 订单号查询校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 account）
                orderNo_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].followBaiginInstructSubVOList[*].orderNo",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not orderNo_list:
                    attach_body = f"订单号查询校验，返回的orderNo列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"订单号查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"订单号{orderNo}查询暂无数据，跳过校验")
                else:
                    attach_body = f"订单号{orderNo}查询，返回 {len(orderNo_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"订单号查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，orderNo 也是字符串）
                for idx, actual_status in enumerate(orderNo_list):
                    self.verify_data(
                        actual_value=str(actual_status),
                        expected_value=str(orderNo),
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的orderNo应为{orderNo}，实际为{actual_status}",
                        attachment_name=f"订单号第 {idx + 1} 条记录校验"
                    )

        @allure.title("订单号查询校验-查询结果为空")
        def test_query_orderNo(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                data = {
                    "page": 1,
                    "limit": 50,
                    "instructionType": "",
                    "symbol": "",
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
                    "orderNo": "测试订单号查询",
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

        @allure.title("魔术号查询校验")
        def test_query_magical(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                vps_redis_comparable_list_open = var_manager.get_variable("vps_redis_comparable_list_open")
                magical = vps_redis_comparable_list_open[0]["magical"]
                data = {
                    "page": 1,
                    "limit": 50,
                    "instructionType": "",
                    "symbol": "",
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
                    "magical": magical,
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

            with allure.step(f"3. 魔术号查询校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 account）
                magical_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].followBaiginInstructSubVOList[*].magical",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not magical_list:
                    attach_body = f"魔术号查询校验，返回的magical列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"魔术号查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"魔术号{magical}查询暂无数据，跳过校验")
                else:
                    attach_body = f"魔术号{magical}查询，返回 {len(magical_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"魔术号查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，magical 也是字符串）
                for idx, actual_status in enumerate(magical_list):
                    self.verify_data(
                        actual_value=str(actual_status),
                        expected_value=str(magical),
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的magical应为{magical}，实际为{actual_status}",
                        attachment_name=f"魔术号第 {idx + 1} 条记录校验"
                    )

        @allure.title("魔术号查询校验-查询结果为空")
        def test_query_magicalNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                data = {
                    "page": 1,
                    "limit": 50,
                    "instructionType": "",
                    "symbol": "",
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
                    "magical": "魔术号查询校验",
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

        @allure.title("平台类型-MT4")
        def test_query_platformTypeMT4(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
                data = {
                    "page": 1,
                    "limit": 50,
                    "instructionType": "",
                    "symbol": "",
                    "type": "",
                    "creatorName": "",
                    "startTime": "",
                    "endTime": "",
                    "cloudType": [],
                    "cloud": [],
                    "operationType": "",
                    "ifFollows": [],
                    "detailStatus": "",
                    "detailAccount": vps_user_accounts_1,
                    "orderNo": "",
                    "magical": "",
                    "status": [],
                    "isClosed": True,
                    "platformType": "0"
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

            with allure.step(f"3. 平台类型查询校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 account）
                platformType_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].followBaiginInstructSubVOList[*].platformType",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not platformType_list:
                    attach_body = f"平台类型查询校验，返回的platformType列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"平台类型查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"平台类型查询暂无数据，跳过校验")
                else:
                    attach_body = f"平台类型查询，返回 {len(platformType_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"平台类型查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，platformType 也是字符串）
                for idx, actual_status in enumerate(platformType_list):
                    self.verify_data(
                        actual_value=float(actual_status),
                        expected_value=float(0),
                        op=CompareOp.EQ,
                        message=f"第 {idx + 1} 条记录的platformType应为0，实际为{actual_status}",
                        attachment_name=f"平台类型第 {idx + 1} 条记录校验"
                    )

        @allure.title("平台类型-MT5")
        def test_query_platformTypeMT5(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                addVPS_MT5Slave = var_manager.get_variable("addVPS_MT5Slave")
                account = addVPS_MT5Slave["account"]
                data = {
                    "page": 1,
                    "limit": 50,
                    "instructionType": "",
                    "symbol": "",
                    "type": "",
                    "creatorName": "",
                    "startTime": "",
                    "endTime": "",
                    "cloudType": [],
                    "cloud": [],
                    "operationType": "",
                    "ifFollows": [],
                    "detailStatus": "",
                    "detailAccount": account,
                    "orderNo": "",
                    "magical": "",
                    "status": [],
                    "isClosed": True,
                    "platformType": "1"
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

            with allure.step(f"3. 平台类型查询校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 account）
                platformType_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].followBaiginInstructSubVOList[*].platformType",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not platformType_list:
                    attach_body = f"平台类型查询校验，返回的platformType列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"平台类型查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"平台类型查询暂无数据，跳过校验")
                else:
                    attach_body = f"平台类型查询，返回 {len(platformType_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"平台类型查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，platformType 也是字符串）
                for idx, actual_status in enumerate(platformType_list):
                    self.verify_data(
                        actual_value=float(actual_status),
                        expected_value=float(1),
                        op=CompareOp.EQ,
                        message=f"第 {idx + 1} 条记录的platformType应为1，实际为{actual_status}",
                        attachment_name=f"平台类型第 {idx + 1} 条记录校验"
                    )

        @allure.title("平台类型-MT5")
        def test_query_platformTypeerror(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                data = {
                    "page": 1,
                    "limit": 50,
                    "instructionType": "",
                    "symbol": "",
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
                    "platformType": "1"
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
                    "平台类型要与子指令账号或订单号或魔术号关联查询",
                    "响应msg字段应为：平台类型要与子指令账号或订单号或魔术号关联查询"
                )

    @allure.story("运营监控-订单列表-查询校验")
    class TestVPSListQuery(APITestBase):
        # 实例化JsonPath工具类（全局复用）
        json_utils = JsonPathUtils()

        @pytest.mark.url("vps")
        @allure.title("券商查询校验")
        def test_query_brokeName(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                brokeName = var_manager.get_variable("broker_name")
                params = {
                    "page": 1,
                    "limit": 100,
                    "flag": 1,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "brokeName": brokeName,
                    "platform": "",
                    "account": "",
                    "symbol": "",
                    "orderNo": "",
                    "sourceUser": "",
                    "magicals": "",
                    "serverName": "",
                    "closeServerName": "",
                    "orderingSystem": "",
                    "startTime": five_time,
                    "endTime": DATETIME_NOW,
                    "closeStartTime": "",
                    "closeEndTime": "",
                    "requestOpenTimeStart": "",
                    "requestOpenTimeEnd": "",
                    "requestCloseTimeStart": "",
                    "requestCloseTimeEnd": "",
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

            with allure.step(f"3. 券商查询校验"):
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

        @pytest.mark.url("vps")
        @allure.title("券商查询校验-查询结果为空")
        def test_query_brokeNameNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 50,
                    "flag": 1,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "brokeName": "ceshiquanshang",
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

            with allure.step("3. 查询校验"):
                self.json_utils.assert_empty_list(
                    data=response.json(),
                    expression="$.data.list",
                )
                logging.info("查询结果符合预期：list为空列表")
                allure.attach("查询结果为空，符合预期", 'text/plain')

        # 定义参数化数据源：(查询平台类型, 描述)
        STATUS_logType = [
            (0, "MT4"),
            (1, "MT5")
        ]

        @pytest.mark.url("vps")
        @pytest.mark.parametrize("query_platform, status_desc", STATUS_logType)
        @allure.title("平台类型查询：{status_desc}（{query_platform}）")
        def test_query_platformType(self, var_manager, logged_session, query_platform, status_desc):
            with allure.step(f"1. 发送请求：平台类型查询{status_desc}（{query_platform}）"):
                params = {
                    "page": 1,
                    "limit": 100,
                    "flag": 1,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "brokeName": "",
                    "platform": "",
                    "account": "",
                    "symbol": "",
                    "orderNo": "",
                    "sourceUser": "",
                    "magicals": "",
                    "serverName": "",
                    "closeServerName": "",
                    "orderingSystem": "",
                    "startTime": five_time,
                    "endTime": DATETIME_NOW,
                    "closeStartTime": "",
                    "closeEndTime": "",
                    "requestOpenTimeStart": "",
                    "requestOpenTimeEnd": "",
                    "requestCloseTimeStart": "",
                    "requestCloseTimeEnd": "",
                    "platformType": query_platform
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

            with allure.step(f"3. 平台类型查询校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 account）
                platformType_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].platformType",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not platformType_list:
                    attach_body = f"平台类型查询校验，返回的platformType列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"平台类型查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"平台类型查询暂无数据，跳过校验")
                else:
                    attach_body = f"平台类型查询，返回 {len(platformType_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"平台类型查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，platformType 也是字符串）
                for idx, actual_status in enumerate(platformType_list):
                    self.verify_data(
                        actual_value=float(actual_status),
                        expected_value=float(query_platform),
                        op=CompareOp.EQ,
                        message=f"第 {idx + 1} 条记录的platformType应为{query_platform}，实际为{actual_status}",
                        attachment_name=f"平台类型第 {idx + 1} 条记录校验"
                    )

        @pytest.mark.url("vps")
        @allure.title("服务器查询校验")
        def test_query_platform(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                new_user = var_manager.get_variable("new_user")
                platform = new_user["platform"]
                params = {
                    "page": 1,
                    "limit": 100,
                    "flag": 1,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "brokeName": "",
                    "platform": platform,
                    "account": "",
                    "symbol": "",
                    "orderNo": "",
                    "sourceUser": "",
                    "magicals": "",
                    "serverName": "",
                    "closeServerName": "",
                    "orderingSystem": "",
                    "startTime": five_time,
                    "endTime": DATETIME_NOW,
                    "closeStartTime": "",
                    "closeEndTime": "",
                    "requestOpenTimeStart": "",
                    "requestOpenTimeEnd": "",
                    "requestCloseTimeStart": "",
                    "requestCloseTimeEnd": "",
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

            with allure.step(f"3. 服务器查询校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 platform）
                platform_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].platform",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not platform_list:
                    attach_body = f"服务器查询校验[{platform}]，返回的platform列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"服务器:{platform}查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"服务器查询[{platform}]暂无数据，跳过校验")
                else:
                    attach_body = f"服务器查询[{platform}]，返回 {len(platform_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"服务器:{platform}查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，platform 也是字符串）
                for idx, actual_status in enumerate(platform_list):
                    self.verify_data(
                        actual_value=platform,
                        expected_value=actual_status,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的platform应为{platform}，实际为{actual_status}",
                        attachment_name=f"服务器:{platform}第 {idx + 1} 条记录校验"
                    )

        @pytest.mark.url("vps")
        @allure.title("服务器查询校验-查询结果为空")
        def test_query_platformNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 50,
                    "flag": 1,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "brokeName": "",
                    "platform": "ceshiquanshang",
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

            with allure.step("3. 查询校验"):
                self.json_utils.assert_empty_list(
                    data=response.json(),
                    expression="$.data.list",
                )
                logging.info("查询结果符合预期：list为空列表")
                allure.attach("查询结果为空，符合预期", 'text/plain')

        # 定义参数化数据源：(查询下单系统, 描述)
        STATUS_orderingSystem = [
            (0, "外部系统"),
            (1, "内部-VPS跟单"),
            (2, "内部-交易下单"),
            (3, "内部云策略-跟单"),
            (4, "内部云策略-手动")
        ]

        @pytest.mark.url("vps")
        @pytest.mark.parametrize("query_orderingSystem, status_desc", STATUS_orderingSystem)
        @allure.title("下单系统查询：{status_desc}（{query_orderingSystem}）")
        def test_query_orderingSystem(self, var_manager, logged_session, query_orderingSystem, status_desc):
            with allure.step(f"1. 发送请求：下单系统查询{status_desc}（{query_orderingSystem}）"):
                params = {
                    "page": 1,
                    "limit": 100,
                    "flag": 1,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "brokeName": "",
                    "account": "",
                    "symbol": "",
                    "orderNo": "",
                    "sourceUser": "",
                    "magicals": "",
                    "serverName": "",
                    "closeServerName": "",
                    "orderingSystem": query_orderingSystem,
                    "startTime": five_time,
                    "endTime": DATETIME_NOW,
                    "closeStartTime": "",
                    "closeEndTime": "",
                    "requestOpenTimeStart": "",
                    "requestOpenTimeEnd": "",
                    "requestCloseTimeStart": "",
                    "requestCloseTimeEnd": ""
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

            with allure.step(f"3. 下单系统查询校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 account）
                orderingSystemType_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].orderingType",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not orderingSystemType_list:
                    attach_body = f"下单系统查询校验，返回的orderingType列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"下单系统查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"下单系统查询暂无数据，跳过校验")
                else:
                    attach_body = f"下单系统查询，返回 {len(orderingSystemType_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"下单系统查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，orderingSystemType 也是字符串）
                for idx, actual_status in enumerate(orderingSystemType_list):
                    self.verify_data(
                        actual_value=float(actual_status),
                        expected_value=float(query_orderingSystem),
                        op=CompareOp.EQ,
                        message=f"第 {idx + 1} 条记录的orderingType应为{query_orderingSystem}，实际为{actual_status}",
                        attachment_name=f"下单系统第 {idx + 1} 条记录校验"
                    )

        @pytest.mark.url("vps")
        @allure.title("账号查询校验")
        def test_query_account(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                new_user = var_manager.get_variable("new_user")
                account = new_user["account"]
                params = {
                    "page": 1,
                    "limit": 100,
                    "flag": 1,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "platform": "",
                    "account": account,
                    "symbol": "",
                    "orderNo": "",
                    "sourceUser": "",
                    "magicals": "",
                    "serverName": "",
                    "closeServerName": "",
                    "orderingSystem": "",
                    "startTime": five_time,
                    "endTime": DATETIME_NOW,
                    "closeStartTime": "",
                    "closeEndTime": "",
                    "requestOpenTimeStart": "",
                    "requestOpenTimeEnd": "",
                    "requestCloseTimeStart": "",
                    "requestCloseTimeEnd": "",
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

            with allure.step(f"3. 账号查询校验"):
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

        @pytest.mark.url("vps")
        @allure.title("账号查询校验-查询结果为空")
        def test_query_accountNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 50,
                    "flag": 1,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "account": "999999999",
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

            with allure.step("3. 查询校验"):
                self.json_utils.assert_empty_list(
                    data=response.json(),
                    expression="$.data.list",
                )
                logging.info("查询结果符合预期：list为空列表")
                allure.attach("查询结果为空，符合预期", 'text/plain')

        @pytest.mark.url("vps")
        @allure.title("品种查询校验")
        def test_query_symbol(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                new_user = var_manager.get_variable("new_user")
                symbol = new_user["symbol"]
                params = {
                    "page": 1,
                    "limit": 100,
                    "flag": 1,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "platform": "",
                    "symbol": symbol,
                    "orderNo": "",
                    "sourceUser": "",
                    "magicals": "",
                    "serverName": "",
                    "closeServerName": "",
                    "orderingSystem": "",
                    "startTime": five_time,
                    "endTime": DATETIME_NOW,
                    "closeStartTime": "",
                    "closeEndTime": "",
                    "requestOpenTimeStart": "",
                    "requestOpenTimeEnd": "",
                    "requestCloseTimeStart": "",
                    "requestCloseTimeEnd": "",
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

            with allure.step(f"3. 品种查询校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 symbol）
                symbol_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].symbol",
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

        @pytest.mark.url("vps")
        @allure.title("品种查询校验-查询结果为空")
        def test_query_symbolNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 50,
                    "flag": 1,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "symbol": "999999999",
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

            with allure.step("3. 查询校验"):
                self.json_utils.assert_empty_list(
                    data=response.json(),
                    expression="$.data.list",
                )
                logging.info("查询结果符合预期：list为空列表")
                allure.attach("查询结果为空，符合预期", 'text/plain')

        @pytest.mark.url("vps")
        @allure.title("订单号查询校验")
        def test_query_orderNo(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                vps_redis_comparable_list_open = var_manager.get_variable("vps_redis_comparable_list_open")
                orderNo = vps_redis_comparable_list_open[0]["order_no"]
                params = {
                    "page": 1,
                    "limit": 100,
                    "flag": 1,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "platform": "",
                    "orderNo": orderNo,
                    "sourceUser": "",
                    "magicals": "",
                    "serverName": "",
                    "closeServerName": "",
                    "orderingSystem": "",
                    "startTime": five_time,
                    "endTime": DATETIME_NOW,
                    "closeStartTime": "",
                    "closeEndTime": "",
                    "requestOpenTimeStart": "",
                    "requestOpenTimeEnd": "",
                    "requestCloseTimeStart": "",
                    "requestCloseTimeEnd": "",
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

            with allure.step(f"3. 订单号查询校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 orderNo）
                orderNo_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].orderNo",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not orderNo_list:
                    attach_body = f"订单号查询校验[{orderNo}]，返回的orderNo列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"订单号:{orderNo}查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"订单号查询[{orderNo}]暂无数据，跳过校验")
                else:
                    attach_body = f"订单号查询[{orderNo}]，返回 {len(orderNo_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"订单号:{orderNo}查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，orderNo 也是字符串）
                for idx, actual_status in enumerate(orderNo_list):
                    self.verify_data(
                        actual_value=orderNo,
                        expected_value=actual_status,
                        op=CompareOp.EQ,
                        message=f"第 {idx + 1} 条记录的orderNo应为{orderNo}，实际为{actual_status}",
                        attachment_name=f"订单号:{orderNo}第 {idx + 1} 条记录校验"
                    )

        @pytest.mark.url("vps")
        @allure.title("订单号查询校验-查询结果为空")
        def test_query_orderNoNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 50,
                    "flag": 1,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "orderNo": "999999999",
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

            with allure.step("3. 查询校验"):
                self.json_utils.assert_empty_list(
                    data=response.json(),
                    expression="$.data.list",
                )
                logging.info("查询结果符合预期：list为空列表")
                allure.attach("查询结果为空，符合预期", 'text/plain')

        @pytest.mark.url("vps")
        @allure.title("喊单账号查询校验")
        def test_query_sourceUser(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                new_user = var_manager.get_variable("new_user")
                sourceUser = new_user["account"]
                params = {
                    "page": 1,
                    "limit": 100,
                    "flag": 1,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "platform": "",
                    "account": "",
                    "symbol": "",
                    "orderNo": "",
                    "sourceUser": sourceUser,
                    "magicals": "",
                    "serverName": "",
                    "closeServerName": "",
                    "orderingSystem": "",
                    "startTime": five_time,
                    "endTime": DATETIME_NOW,
                    "closeStartTime": "",
                    "closeEndTime": "",
                    "requestOpenTimeStart": "",
                    "requestOpenTimeEnd": "",
                    "requestCloseTimeStart": "",
                    "requestCloseTimeEnd": "",
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
                    "flag": 1,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "sourceUser": "999999999",
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

            with allure.step("3. 查询校验"):
                self.json_utils.assert_empty_list(
                    data=response.json(),
                    expression="$.data.list",
                )
                logging.info("查询结果符合预期：list为空列表")
                allure.attach("查询结果为空，符合预期", 'text/plain')

        @pytest.mark.url("vps")
        @allure.title("魔术号查询校验")
        def test_query_magical(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                vps_redis_comparable_list_open = var_manager.get_variable("vps_redis_comparable_list_open")
                magical = vps_redis_comparable_list_open[0]["magical"]
                params = {
                    "page": 1,
                    "limit": 100,
                    "flag": 1,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "platform": "",
                    "sourceUser": "",
                    "magicals": magical,
                    "serverName": "",
                    "closeServerName": "",
                    "orderingSystem": "",
                    "startTime": five_time,
                    "endTime": DATETIME_NOW,
                    "closeStartTime": "",
                    "closeEndTime": "",
                    "requestOpenTimeStart": "",
                    "requestOpenTimeEnd": "",
                    "requestCloseTimeStart": "",
                    "requestCloseTimeEnd": "",
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

            with allure.step(f"3. 魔术号查询校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 magical）
                magical_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].magical",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not magical_list:
                    attach_body = f"魔术号查询校验[{magical}]，返回的magical列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"魔术号:{magical}查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"魔术号查询[{magical}]暂无数据，跳过校验")
                else:
                    attach_body = f"魔术号查询[{magical}]，返回 {len(magical_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"魔术号:{magical}查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，magical 也是字符串）
                for idx, actual_status in enumerate(magical_list):
                    self.verify_data(
                        actual_value=float(magical),
                        expected_value=float(actual_status),
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的magical应为{magical}，实际为{actual_status}",
                        attachment_name=f"魔术号:{magical}第 {idx + 1} 条记录校验"
                    )

        @pytest.mark.url("vps")
        @allure.title("魔术号查询校验-查询结果为空")
        def test_query_magicalNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 50,
                    "flag": 1,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "magical": "999999999",
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

            with allure.step("3. 查询校验"):
                self.json_utils.assert_empty_list(
                    data=response.json(),
                    expression="$.data.list",
                )
                logging.info("查询结果符合预期：list为空列表")
                allure.attach("查询结果为空，符合预期", 'text/plain')

        @pytest.mark.url("vps")
        @allure.title("开仓VPS名称查询校验")
        def test_query_serverName(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                serverName = var_manager.get_variable("IP_ADDRESS")
                params = {
                    "page": 1,
                    "limit": 100,
                    "flag": 1,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "platform": "",
                    "sourceUser": "",
                    "serverName": serverName,
                    "closeServerName": "",
                    "orderingSystem": "",
                    "startTime": five_time,
                    "endTime": DATETIME_NOW,
                    "closeStartTime": "",
                    "closeEndTime": "",
                    "requestOpenTimeStart": "",
                    "requestOpenTimeEnd": "",
                    "requestCloseTimeStart": "",
                    "requestCloseTimeEnd": "",
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

            with allure.step(f"3. 开仓VPS名称查询校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 serverName）
                serverName_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].serverName",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not serverName_list:
                    attach_body = f"开仓VPS名称查询校验[{serverName}]，返回的serverName列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"开仓VPS名称:{serverName}查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"开仓VPS名称查询[{serverName}]暂无数据，跳过校验")
                else:
                    attach_body = f"开仓VPS名称查询[{serverName}]，返回 {len(serverName_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"开仓VPS名称:{serverName}查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，serverName 也是字符串）
                for idx, actual_status in enumerate(serverName_list):
                    self.verify_data(
                        actual_value=serverName,
                        expected_value=actual_status,
                        op=CompareOp.IN,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的serverName应为{serverName}，实际为{actual_status}",
                        attachment_name=f"开仓VPS名称:{serverName}第 {idx + 1} 条记录校验"
                    )

        @pytest.mark.url("vps")
        @allure.title("开仓VPS名称查询校验-查询结果为空")
        def test_query_serverNameNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 50,
                    "flag": 1,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "serverName": "999999999",
                    "sourceUser": "",
                    "serverNames": "",
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

            with allure.step("3. 查询校验"):
                self.json_utils.assert_empty_list(
                    data=response.json(),
                    expression="$.data.list",
                )
                logging.info("查询结果符合预期：list为空列表")
                allure.attach("查询结果为空，符合预期", 'text/plain')

        @pytest.mark.url("vps")
        @allure.title("平仓VPS名称查询校验")
        def test_query_closeServerName(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                closeServerName = var_manager.get_variable("IP_ADDRESS")
                params = {
                    "page": 1,
                    "limit": 100,
                    "flag": 1,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "platform": "",
                    "sourceUser": "",
                    "closeServerName": closeServerName,
                    "orderingSystem": "",
                    "startTime": five_time,
                    "endTime": DATETIME_NOW,
                    "closeStartTime": "",
                    "closeEndTime": "",
                    "requestOpenTimeStart": "",
                    "requestOpenTimeEnd": "",
                    "requestCloseTimeStart": "",
                    "requestCloseTimeEnd": "",
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

            with allure.step(f"3. 平仓VPS名称查询校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 closeServerName）
                closeServerName_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].closeServerName",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not closeServerName_list:
                    attach_body = f"平仓VPS名称查询校验[{closeServerName}]，返回的closeServerName列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"平仓VPS名称:{closeServerName}查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"平仓VPS名称查询[{closeServerName}]暂无数据，跳过校验")
                else:
                    attach_body = f"平仓VPS名称查询[{closeServerName}]，返回 {len(closeServerName_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"平仓VPS名称:{closeServerName}查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，closeServerName 也是字符串）
                for idx, actual_status in enumerate(closeServerName_list):
                    self.verify_data(
                        actual_value=closeServerName,
                        expected_value=actual_status,
                        op=CompareOp.IN,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的closeServerName应为{closeServerName}，实际为{actual_status}",
                        attachment_name=f"平仓VPS名称:{closeServerName}第 {idx + 1} 条记录校验"
                    )

        @pytest.mark.url("vps")
        @allure.title("平仓VPS名称查询校验-查询结果为空")
        def test_query_closeServerNameNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 50,
                    "flag": 1,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "closeServerName": "999999999",
                    "sourceUser": "",
                    "closeServerNames": "",
                    "closecloseServerName": "",
                    "orderingSystem": "",
                    "startTime": DATETIME_INIT,
                    "endTime": DATETIME_NOW,
                    "closeStartTime": "",
                    "closeEndTime": "",
                    "requestOpenTimeStart": "",
                    "requestOpenTimeEnd": "",
                    "requestCloseTimeStart": "",
                    "requestCloseTimeEnd": "",
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

            with allure.step("3. 查询校验"):
                self.json_utils.assert_empty_list(
                    data=response.json(),
                    expression="$.data.list",
                )
                logging.info("查询结果符合预期：list为空列表")
                allure.attach("查询结果为空，符合预期", 'text/plain')

        @pytest.mark.url("vps")
        @allure.title("开仓时间查询校验")
        def test_query_openTime(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 100,
                    "flag": 1,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "platform": "",
                    "sourceUser": "",
                    "orderingSystem": "",
                    "startTime": five_time,
                    "endTime": DATETIME_NOW,
                    "closeStartTime": "",
                    "closeEndTime": "",
                    "requestOpenTimeStart": "",
                    "requestOpenTimeEnd": "",
                    "requestCloseTimeStart": "",
                    "requestCloseTimeEnd": "",
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

            with allure.step(f"3. 开仓时间查询校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 openTime）
                openTime_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].openTime",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not openTime_list:
                    attach_body = f"开仓时间查询校验，返回的openTime列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"开仓时间查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"开仓时间查询暂无数据，跳过校验")
                else:
                    attach_body = f"开仓时间查询，返回 {len(openTime_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"开仓时间查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，openTime 也是字符串）
                for idx, actual_status in enumerate(openTime_list):
                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=five_time,
                        op=CompareOp.GE,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的openTime应大于{five_time}",
                        attachment_name=f"开仓时间:{actual_status}第 {idx + 1} 条记录校验"
                    )

                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=DATETIME_NOW,
                        op=CompareOp.LE,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的openTime应小于{DATETIME_NOW}",
                        attachment_name=f"开仓时间:{actual_status}第 {idx + 1} 条记录校验"
                    )

        @pytest.mark.url("vps")
        @allure.title("开仓时间查询校验-查询结果为空")
        def test_query_openTimeNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 50,
                    "flag": 1,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "sourceUser": "",
                    "openTimes": "",
                    "closeopenTime": "",
                    "orderingSystem": "",
                    "startTime": DATETIME_NOW,
                    "endTime": DATETIME_INIT,
                    "closeStartTime": "",
                    "closeEndTime": "",
                    "requestOpenTimeStart": "",
                    "requestOpenTimeEnd": "",
                    "requestCloseTimeStart": "",
                    "requestCloseTimeEnd": "",
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

            with allure.step("3. 查询校验"):
                self.json_utils.assert_empty_list(
                    data=response.json(),
                    expression="$.data.list",
                )
                logging.info("查询结果符合预期：list为空列表")
                allure.attach("查询结果为空，符合预期", 'text/plain')

        @pytest.mark.url("vps")
        @allure.title("平仓时间查询校验")
        def test_query_closeTime(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 100,
                    "flag": 1,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "platform": "",
                    "sourceUser": "",
                    "orderingSystem": "",
                    "closeStartTime": five_time,
                    "closeEndTime": DATETIME_NOW,
                    "requestOpenTimeStart": "",
                    "requestOpenTimeEnd": "",
                    "requestCloseTimeStart": "",
                    "requestCloseTimeEnd": "",
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

            with allure.step(f"3. 平仓时间查询校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 closeTime）
                closeTime_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].closeTime",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not closeTime_list:
                    attach_body = f"平仓时间查询校验，返回的closeTime列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"平仓时间查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"平仓时间查询暂无数据，跳过校验")
                else:
                    attach_body = f"平仓时间查询，返回 {len(closeTime_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"平仓时间查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，closeTime 也是字符串）
                for idx, actual_status in enumerate(closeTime_list):
                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=five_time,
                        op=CompareOp.GE,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的closeTime应大于{five_time}",
                        attachment_name=f"平仓时间:{actual_status}第 {idx + 1} 条记录校验"
                    )

                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=DATETIME_NOW,
                        op=CompareOp.LE,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的closeTime应小于{DATETIME_NOW}",
                        attachment_name=f"平仓时间:{actual_status}第 {idx + 1} 条记录校验"
                    )

        @pytest.mark.url("vps")
        @allure.title("平仓时间查询校验-查询结果为空")
        def test_query_closeTimeNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 100,
                    "flag": 1,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "platform": "",
                    "sourceUser": "",
                    "orderingSystem": "",
                    "closeStartTime": DATETIME_INIT,
                    "closeEndTime": five_time,
                    "requestOpenTimeStart": "",
                    "requestOpenTimeEnd": "",
                    "requestCloseTimeStart": "",
                    "requestCloseTimeEnd": "",
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

            with allure.step("3. 查询校验"):
                self.json_utils.assert_empty_list(
                    data=response.json(),
                    expression="$.data.list",
                )
                logging.info("查询结果符合预期：list为空列表")
                allure.attach("查询结果为空，符合预期", 'text/plain')

        @pytest.mark.url("vps")
        @allure.title("开仓请求时间查询校验")
        def test_query_requestOpenTime(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 100,
                    "flag": 1,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "platform": "",
                    "sourceUser": "",
                    "orderingSystem": "",
                    "requestOpenTimeStart": five_time,
                    "requestOpenTimeEnd": DATETIME_NOW,
                    "requestCloseTimeStart": "",
                    "requestCloseTimeEnd": "",
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

            with allure.step(f"3. 开仓请求时间查询校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 requestOpenTime）
                requestOpenTime_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].requestOpenTime",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not requestOpenTime_list:
                    attach_body = f"开仓请求时间查询校验，返回的requestOpenTime列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"开仓请求时间查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"开仓请求时间查询暂无数据，跳过校验")
                else:
                    attach_body = f"开仓请求时间查询，返回 {len(requestOpenTime_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"开仓请求时间查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，requestOpenTime 也是字符串）
                for idx, actual_status in enumerate(requestOpenTime_list):
                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=five_time,
                        op=CompareOp.GE,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的requestOpenTime应大于{five_time}",
                        attachment_name=f"开仓请求时间:{actual_status}第 {idx + 1} 条记录校验"
                    )

                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=DATETIME_NOW,
                        op=CompareOp.LE,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的requestOpenTime应小于{DATETIME_NOW}",
                        attachment_name=f"开仓请求时间:{actual_status}第 {idx + 1} 条记录校验"
                    )

        @pytest.mark.url("vps")
        @allure.title("开仓请求时间查询校验-查询结果为空")
        def test_query_requestOpenTimeNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 100,
                    "flag": 1,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "platform": "",
                    "sourceUser": "",
                    "orderingSystem": "",
                    "requestOpenTimeStart": DATETIME_NOW,
                    "requestOpenTimeEnd": five_time,
                    "requestCloseTimeStart": "",
                    "requestCloseTimeEnd": "",
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

            with allure.step("3. 查询校验"):
                self.json_utils.assert_empty_list(
                    data=response.json(),
                    expression="$.data.list",
                )
                logging.info("查询结果符合预期：list为空列表")
                allure.attach("查询结果为空，符合预期", 'text/plain')

        @pytest.mark.url("vps")
        @allure.title("平仓请求时间查询校验")
        def test_query_requestCloseTime(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 100,
                    "flag": 1,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "platform": "",
                    "sourceUser": "",
                    "orderingSystem": "",
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

        @pytest.mark.url("vps")
        @allure.title("平仓请求时间查询校验-查询结果为空")
        def test_query_requestCloseTimeNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 100,
                    "flag": 1,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "platform": "",
                    "sourceUser": "",
                    "orderingSystem": "",
                    "requestCloseTimeStart": DATETIME_NOW,
                    "requestCloseTimeEnd": five_time,
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

            with allure.step("3. 查询校验"):
                self.json_utils.assert_empty_list(
                    data=response.json(),
                    expression="$.data.list",
                )
                logging.info("查询结果符合预期：list为空列表")
                allure.attach("查询结果为空，符合预期", 'text/plain')

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
