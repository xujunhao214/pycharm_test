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
