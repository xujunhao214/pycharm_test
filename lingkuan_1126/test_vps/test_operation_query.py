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


@allure.feature("运营监控查询校验")
class TestoperationQuery:
    @allure.story("运营监控-历史指令")
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
                        actual_value=str(magical),
                        expected_value=str(actual_status),
                        op=CompareOp.IN,
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

        @pytest.mark.url("vps")
        @allure.title("券商查询校验-查询结果为空")
        def test_query_brokerNameNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 50,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "brokeName": "ceshiquanshang",
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

            with allure.step("3. 查询校验"):
                self.json_utils.assert_empty_list(
                    data=response.json(),
                    expression="$.data.list",
                )
                logging.info("查询结果符合预期：list为空列表")
                allure.attach("查询结果为空，符合预期", 'text/plain')

        STATUS_platformType = [
            (0, "MT4"),
            (1, "MT5")
        ]

        @pytest.mark.url("vps")
        @pytest.mark.parametrize("status, status_desc", STATUS_platformType)
        @allure.title("平台类型查询：{status_desc}（{status}）")
        def test_query_platformType(self, var_manager, logged_session, status, status_desc):
            with allure.step(f"1. 发送请求：平台类型查询-{status_desc}（{status}）"):
                params = {
                    "page": 1,
                    "limit": 50,
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
                    "startTime": DATETIME_INIT,
                    "endTime": DATETIME_NOW,
                    "closeStartTime": "",
                    "closeEndTime": "",
                    "requestOpenTimeStart": "",
                    "requestOpenTimeEnd": "",
                    "requestCloseTimeStart": "",
                    "requestCloseTimeEnd": "",
                    "platformType": status,
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

            with allure.step(f"3. 平台类型查询结果校验：返回记录的platformType应为{status}"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 platformType）
                platformType_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].platformType",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not platformType_list:
                    attach_body = f"平台类型查询[{status}]，返回的platformType列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"平台类型:{status}查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"平台类型查询[{status}]暂无数据，跳过校验")
                else:
                    attach_body = f"平台类型查询[{status}]，返回 {len(platformType_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"平台类型:{status}查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，platformType 也是字符串）
                for idx, actual_status in enumerate(platformType_list):
                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=status,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的platformType应为{status}，实际为{actual_status}",
                        attachment_name=f"平台类型:{status}第 {idx + 1} 条记录校验"
                    )

        STATUS_orderingSystem = [
            (0, "外部系统"),
            (1, "内部-VPS跟单"),
            (2, "内部-交易下单"),
            (3, "内部云策略-跟单"),
            (4, "内部云策略-手动")
        ]

        @pytest.mark.url("vps")
        @pytest.mark.parametrize("status, status_desc", STATUS_orderingSystem)
        @allure.title("下单系统查询：{status_desc}（{status}）")
        def test_query_orderingSystem(self, var_manager, logged_session, status, status_desc):
            with allure.step(f"1. 发送请求：下单系统查询-{status_desc}（{status}）"):
                params = {
                    "page": 1,
                    "limit": 50,
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
                    "orderingSystem": status,
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

            with allure.step(f"3. 下单系统查询结果校验：返回记录的orderingSystem应为{status}"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 orderingSystem）
                orderingSystem_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].orderingType",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not orderingSystem_list:
                    attach_body = f"下单系统查询[{status}]，返回的orderingSystem列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"下单系统:{status}查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"下单系统查询[{status}]暂无数据，跳过校验")
                else:
                    attach_body = f"下单系统查询[{status}]，返回 {len(orderingSystem_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"下单系统:{status}查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，orderingSystem 也是字符串）
                for idx, actual_status in enumerate(orderingSystem_list):
                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=status,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的orderingSystem应为{status}，实际为{actual_status}",
                        attachment_name=f"下单系统:{status}第 {idx + 1} 条记录校验"
                    )

        @pytest.mark.url("vps")
        @allure.title("服务器查询校验")
        def test_query_platform(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                new_user = var_manager.get_variable("new_user")
                platform = new_user["platform"]
                params = {
                    "page": 1,
                    "limit": 50,
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
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "brokeName": "",
                    "platform": "ceshifuwuqi",
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

            with allure.step("3. 查询校验"):
                self.json_utils.assert_empty_list(
                    data=response.json(),
                    expression="$.data.list",
                )
                logging.info("查询结果符合预期：list为空列表")
                allure.attach("查询结果为空，符合预期", 'text/plain')

        @pytest.mark.url("vps")
        @allure.title("账号查询校验")
        def test_query_account(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                new_user = var_manager.get_variable("new_user")
                account = new_user["account"]
                params = {
                    "page": 1,
                    "limit": 50,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "brokeName": "",
                    "platform": "",
                    "account": account,
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
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "brokeName": "",
                    "platform": "",
                    "account": "9999999999",
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
                    "limit": 50,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "brokeName": "",
                    "platform": "",
                    "account": "",
                    "symbol": symbol,
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
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "brokeName": "",
                    "platform": "",
                    "account": "",
                    "symbol": "9999999999",
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
                    "limit": 50,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "brokeName": "",
                    "platform": "",
                    "account": "",
                    "orderNo": orderNo,
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
                        actual_value=str(orderNo),
                        expected_value=str(actual_status),
                        op=CompareOp.EQ,
                        use_isclose=False,
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
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "brokeName": "",
                    "platform": "",
                    "account": "",
                    "orderNo": "9999999999",
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

        @pytest.mark.url("vps")
        @allure.title("魔术号查询校验")
        def test_query_magical(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                vps_redis_comparable_list_open = var_manager.get_variable("vps_redis_comparable_list_open")
                magical = vps_redis_comparable_list_open[0]["magical"]
                params = {
                    "page": 1,
                    "limit": 50,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "brokeName": "",
                    "platform": "",
                    "account": "",
                    "sourceUser": "",
                    "magicals": magical,
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
                        actual_value=str(magical),
                        expected_value=str(actual_status),
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
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "brokeName": "",
                    "platform": "",
                    "account": "",
                    "sourceUser": "",
                    "magicals": "9999999999",
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

        @pytest.mark.url("vps")
        @allure.title("开仓VPS名称查询校验")
        def test_query_openserverName(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                serverName = var_manager.get_variable("IP_ADDRESS")
                params = {
                    "page": 1,
                    "limit": 50,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "brokeName": "",
                    "platform": "",
                    "account": "",
                    "sourceUser": "",
                    "serverName": serverName,
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
                        actual_value=str(serverName),
                        expected_value=str(actual_status),
                        op=CompareOp.IN,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的serverName应为{serverName}，实际为{actual_status}",
                        attachment_name=f"开仓VPS名称:{serverName}第 {idx + 1} 条记录校验"
                    )

        @pytest.mark.url("vps")
        @allure.title("开仓VPS名称查询校验-查询结果为空")
        def test_query_openserverNameNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 50,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "brokeName": "",
                    "platform": "",
                    "account": "",
                    "sourceUser": "",
                    "serverName": "9999999999",
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

        @pytest.mark.url("vps")
        @allure.title("平仓VPS名称查询校验")
        def test_query_closecloseServerName(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                closeServerName = var_manager.get_variable("IP_ADDRESS")
                params = {
                    "page": 1,
                    "limit": 50,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "brokeName": "",
                    "platform": "",
                    "account": "",
                    "sourceUser": "",
                    "closeServerName": closeServerName,
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
                        actual_value=str(closeServerName),
                        expected_value=str(actual_status),
                        op=CompareOp.IN,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的closeServerName应为{closeServerName}，实际为{actual_status}",
                        attachment_name=f"平仓VPS名称:{closeServerName}第 {idx + 1} 条记录校验"
                    )

        @pytest.mark.url("vps")
        @allure.title("平仓VPS名称查询校验-查询结果为空")
        def test_query_closecloseServerNameNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 50,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "brokeName": "",
                    "platform": "",
                    "account": "",
                    "sourceUser": "",
                    "closeServerName": "9999999999",
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

        @pytest.mark.url("vps")
        @allure.title("开仓时间查询校验")
        def test_query_openTime(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 50,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "brokeName": "",
                    "platform": "",
                    "account": "",
                    "sourceUser": "",
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

            with allure.step(f"3. 查询结果校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 dateTime）
                dateTime_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].openTime",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not dateTime_list:
                    pytest.fail("查询结果为空，不符合预期")
                else:
                    attach_body = f"查询开始时间：[{DATETIME_INIT}]，结束时间：[{DATETIME_NOW}]，返回 {len(dateTime_list)} 条记录"

                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"时间查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，dateTime 也是字符串）
                for idx, actual_status in enumerate(dateTime_list):
                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=DATETIME_INIT,
                        op=CompareOp.GE,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的openTime应为{actual_status}",
                        attachment_name=f"时间:{actual_status}第 {idx + 1} 条记录校验"
                    )

                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=DATETIME_NOW,
                        op=CompareOp.LE,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的openTime应为{actual_status}",
                        attachment_name=f"时间:{actual_status}第 {idx + 1} 条记录校验"
                    )

        @pytest.mark.url("vps")
        @allure.title("开仓时间查询校验-查询结果为空")
        def test_query_openTimeNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 50,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "brokeName": "",
                    "platform": "",
                    "account": "",
                    "sourceUser": "",
                    "orderingSystem": "",
                    "startTime": DATETIME_NOW,
                    "endTime": DATETIME_INIT,
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

        @pytest.mark.url("vps")
        @allure.title("平仓时间查询校验")
        def test_query_closeTime(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 50,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "brokeName": "",
                    "platform": "",
                    "account": "",
                    "sourceUser": "",
                    "orderingSystem": "",
                    "closeStartTime": DATETIME_INIT,
                    "closeEndTime": DATETIME_NOW,
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

            with allure.step(f"3. 查询结果校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 closeTime）
                closeTime_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].closeTime",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not closeTime_list:
                    pytest.fail("查询结果为空，不符合预期")
                else:
                    attach_body = f"查询开始时间：[{DATETIME_INIT}]，结束时间：[{DATETIME_NOW}]，返回 {len(closeTime_list)} 条记录"

                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"时间查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，closeTime 也是字符串）
                for idx, actual_status in enumerate(closeTime_list):
                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=DATETIME_INIT,
                        op=CompareOp.GE,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的closeTime应为{actual_status}",
                        attachment_name=f"时间:{actual_status}第 {idx + 1} 条记录校验"
                    )

                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=DATETIME_NOW,
                        op=CompareOp.LE,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的closeTime应为{actual_status}",
                        attachment_name=f"时间:{actual_status}第 {idx + 1} 条记录校验"
                    )

        @pytest.mark.url("vps")
        @allure.title("平仓时间查询校验-查询结果为空")
        def test_query_closeTimeNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 50,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "brokeName": "",
                    "platform": "",
                    "account": "",
                    "sourceUser": "",
                    "orderingSystem": "",
                    "closeStartTime": DATETIME_NOW,
                    "closeEndTime": DATETIME_INIT,
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

        @pytest.mark.url("vps")
        @allure.title("开仓请求时间查询校验")
        def test_query_requestOpenTimeStart(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 50,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "brokeName": "",
                    "platform": "",
                    "account": "",
                    "sourceUser": "",
                    "orderingSystem": "",
                    "requestOpenTimeStart": DATETIME_INIT,
                    "requestOpenTimeEnd": DATETIME_NOW,
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

            with allure.step(f"3. 查询结果校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 closeTime）
                closeTime_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].requestOpenTime",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not closeTime_list:
                    pytest.fail("查询结果为空，不符合预期")
                else:
                    attach_body = f"查询开始时间：[{DATETIME_INIT}]，结束时间：[{DATETIME_NOW}]，返回 {len(closeTime_list)} 条记录"

                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"时间查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，closeTime 也是字符串）
                for idx, actual_status in enumerate(closeTime_list):
                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=DATETIME_INIT,
                        op=CompareOp.GE,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的closeTime应为{actual_status}",
                        attachment_name=f"时间:{actual_status}第 {idx + 1} 条记录校验"
                    )

                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=DATETIME_NOW,
                        op=CompareOp.LE,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的closeTime应为{actual_status}",
                        attachment_name=f"时间:{actual_status}第 {idx + 1} 条记录校验"
                    )

        @pytest.mark.url("vps")
        @allure.title("开仓请求时间查询校验-查询结果为空")
        def test_query_requestOpenTimeStartNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 50,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "brokeName": "",
                    "platform": "",
                    "account": "",
                    "sourceUser": "",
                    "orderingSystem": "",
                    "requestOpenTimeStart": DATETIME_NOW,
                    "requestOpenTimeEnd": DATETIME_INIT,
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

        @pytest.mark.url("vps")
        @allure.title("平仓请求时间查询校验")
        def test_query_requestCloseTimeStart(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 50,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "brokeName": "",
                    "platform": "",
                    "account": "",
                    "sourceUser": "",
                    "orderingSystem": "",
                    "requestCloseTimeStart": DATETIME_INIT,
                    "requestCloseTimeEnd": DATETIME_NOW,
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

            with allure.step(f"3. 查询结果校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 closeTime）
                closeTime_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].requestCloseTime",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not closeTime_list:
                    pytest.fail("查询结果为空，不符合预期")
                else:
                    attach_body = f"查询开始时间：[{DATETIME_INIT}]，结束时间：[{DATETIME_NOW}]，返回 {len(closeTime_list)} 条记录"

                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"时间查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，closeTime 也是字符串）
                for idx, actual_status in enumerate(closeTime_list):
                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=DATETIME_INIT,
                        op=CompareOp.GE,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的closeTime应为{actual_status}",
                        attachment_name=f"时间:{actual_status}第 {idx + 1} 条记录校验"
                    )

                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=DATETIME_NOW,
                        op=CompareOp.LE,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的closeTime应为{actual_status}",
                        attachment_name=f"时间:{actual_status}第 {idx + 1} 条记录校验"
                    )

        @pytest.mark.url("vps")
        @allure.title("平仓请求时间查询校验-查询结果为空")
        def test_query_requestCloseTimeStartNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 50,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "brokeName": "",
                    "platform": "",
                    "account": "",
                    "sourceUser": "",
                    "orderingSystem": "",
                    "requestCloseTimeStart": DATETIME_NOW,
                    "requestCloseTimeEnd": DATETIME_INIT,
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

        @pytest.mark.url("vps")
        @allure.title("组合查询")
        def test_query_combination(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                brokeName = var_manager.get_variable("broker_name")
                # 统一转为小写，用于后续不区分大小写校验（避免硬编码大小写问题）
                brokeName_lower = brokeName.lower()
                new_user = var_manager.get_variable("new_user")
                account = new_user["account"]
                params = {
                    "page": 1,
                    "limit": 50,
                    "asc": "false",
                    "order": "close_time",
                    "isRepeat": "false",
                    "brokeName": brokeName_lower,
                    "platform": "",
                    "account": account,
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
                    "requestCloseTimeStart": DATETIME_INIT,
                    "requestCloseTimeEnd": DATETIME_NOW,
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
                    "$.data.list[*].brokerName",
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

            with allure.step(f"5. 开仓请求时间查询结果校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 closeTime）
                closeTime_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].requestCloseTime",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not closeTime_list:
                    pytest.fail("查询结果为空，不符合预期")
                else:
                    attach_body = f"查询开始时间：[{DATETIME_INIT}]，结束时间：[{DATETIME_NOW}]，返回 {len(closeTime_list)} 条记录"

                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"时间查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，closeTime 也是字符串）
                for idx, actual_status in enumerate(closeTime_list):
                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=DATETIME_INIT,
                        op=CompareOp.GE,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的closeTime应为{actual_status}",
                        attachment_name=f"时间:{actual_status}第 {idx + 1} 条记录校验"
                    )

                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=DATETIME_NOW,
                        op=CompareOp.LE,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的closeTime应为{actual_status}",
                        attachment_name=f"时间:{actual_status}第 {idx + 1} 条记录校验"
                    )
