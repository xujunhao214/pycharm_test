import time
import math
import allure
import logging
import pytest
import re
from lingkuan_1124.VAR.VAR import *
from lingkuan_1124.conftest import var_manager
from lingkuan_1124.commons.api_base import *
from template.commons.jsonpath_utils import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"

VPS_IP_PATTERN = re.compile(r'VPS=.*?([\d.]+)')


@allure.feature("查询校验")
class TestVPSquery(APITestBase):
    @allure.story("平台管理-平台列表")
    class TestVPSqueryList(APITestBase):
        # 实例化JsonPath工具类（全局复用）
        json_utils = JsonPathUtils()

        @allure.title("券商查询校验")
        def test_query_brokeName(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                brokeName = var_manager.get_variable("broker_name")
                # 统一转为小写，用于后续不区分大小写校验（避免硬编码大小写问题）
                brokeName_lower = brokeName.lower()
                params = {
                    "page": 1,
                    "limit": 100,
                    "asc": "false",
                    "order": "update_time",
                    "loading": "false",
                    "brokerName": brokeName,
                    "server": "",
                    "platformType": ""
                }

                response = self.send_get_request(
                    logged_session,
                    '/mascontrol/platform/page',
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

        @allure.title("券商查询校验-查询结果为空")
        def test_query_brokerNameNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 50,
                    "asc": "false",
                    "order": "update_time",
                    "loading": "false",
                    "brokerName": "ceshiquanshang",
                    "server": "",
                    "platformType": "",
                }

                response = self.send_get_request(
                    logged_session,
                    '/mascontrol/platform/page',
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

        @allure.title("服务器查询校验")
        def test_query_server(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                new_user = var_manager.get_variable("new_user")
                server = new_user["platform"]
                params = {
                    "page": 1,
                    "limit": 50,
                    "asc": "false",
                    "order": "update_time",
                    "loading": "false",
                    "brokerName": "",
                    "server": server,
                    "platformType": "",
                }

                response = self.send_get_request(
                    logged_session,
                    '/mascontrol/platform/page',
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
                # 修复：正确的 JsonPath 表达式（提取所有记录的 server）
                server_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].server",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not server_list:
                    attach_body = f"服务器查询校验[{server}]，返回的server列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"服务器:{server}查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"服务器查询[{server}]暂无数据，跳过校验")
                else:
                    attach_body = f"服务器查询[{server}]，返回 {len(server_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"服务器:{server}查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，server 也是字符串）
                for idx, actual_status in enumerate(server_list):
                    self.verify_data(
                        actual_value=server,
                        expected_value=actual_status,
                        op=CompareOp.IN,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的server应为{server}，实际为{actual_status}",
                        attachment_name=f"服务器:{server}第 {idx + 1} 条记录校验"
                    )

        @allure.title("服务器查询校验-查询结果为空")
        def test_query_serverNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 50,
                    "asc": "false",
                    "order": "update_time",
                    "loading": "false",
                    "brokerName": "",
                    "server": "ceshifuwuqi",
                    "platformType": "",
                }

                response = self.send_get_request(
                    logged_session,
                    '/mascontrol/platform/page',
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

        @pytest.mark.parametrize("status, status_desc", STATUS_platformType)
        @allure.title("平台类型查询：{status_desc}（{status}）")
        def test_query_platformType(self, var_manager, logged_session, status, status_desc):
            with allure.step(f"1. 发送请求：平台类型查询-{status_desc}（{status}）"):
                params = {
                    "page": 1,
                    "limit": 50,
                    "asc": "false",
                    "order": "update_time",
                    "loading": "false",
                    "brokerName": "",
                    "server": "",
                    "platformType": status,
                }

                response = self.send_get_request(
                    logged_session,
                    '/mascontrol/platform/page',
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

    @allure.story("平台管理-服务器管理")
    class TestVPSqueryServer(APITestBase):
        # 实例化JsonPath工具类（全局复用）
        json_utils = JsonPathUtils()

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
                    "order": "",
                    "serverNode": "",
                    "brokerName": brokeName_lower,
                    "serverName": "",
                    "platformType": "",
                }

                response = self.send_get_request(
                    logged_session,
                    '/mascontrol/speed/listTestServer',
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

        @allure.title("券商查询校验-查询结果为空")
        def test_query_brokerNameNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 50,
                    "asc": "false",
                    "order": "",
                    "serverNode": "",
                    "brokerName": "ceshiquanshang",
                    "serverName": "",
                    "platformType": "",
                }

                response = self.send_get_request(
                    logged_session,
                    '/mascontrol/speed/listTestServer',
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

        @allure.title("服务器查询校验")
        def test_query_serverName(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                new_user = var_manager.get_variable("new_user")
                serverName = new_user["platform"]
                params = {
                    "page": 1,
                    "limit": 50,
                    "asc": "false",
                    "order": "",
                    "serverNode": "",
                    "brokerName": "",
                    "serverName": serverName,
                    "platformType": "",
                }

                response = self.send_get_request(
                    logged_session,
                    '/mascontrol/speed/listTestServer',
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
                # 修复：正确的 JsonPath 表达式（提取所有记录的 serverName）
                serverName_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].serverName",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not serverName_list:
                    attach_body = f"服务器查询校验[{serverName}]，返回的serverName列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"服务器:{serverName}查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"服务器查询[{serverName}]暂无数据，跳过校验")
                else:
                    attach_body = f"服务器查询[{serverName}]，返回 {len(serverName_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"服务器:{serverName}查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，serverName 也是字符串）
                for idx, actual_status in enumerate(serverName_list):
                    self.verify_data(
                        actual_value=serverName,
                        expected_value=actual_status,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的serverName应为{serverName}，实际为{actual_status}",
                        attachment_name=f"服务器:{serverName}第 {idx + 1} 条记录校验"
                    )

        @allure.title("服务器查询校验-查询结果为空")
        def test_query_serverNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 50,
                    "asc": "false",
                    "order": "",
                    "serverNode": "",
                    "brokerName": "",
                    "serverName": "ceshifuwuqi",
                    "platformType": "",
                }

                response = self.send_get_request(
                    logged_session,
                    '/mascontrol/speed/listTestServer',
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

        @pytest.mark.parametrize("status, status_desc", STATUS_platformType)
        @allure.title("平台类型查询：{status_desc}（{status}）")
        def test_query_platformType(self, var_manager, logged_session, status, status_desc):
            with allure.step(f"1. 发送请求：平台类型查询-{status_desc}（{status}）"):
                params = {
                    "page": 1,
                    "limit": 50,
                    "asc": "false",
                    "order": "",
                    "serverNode": "",
                    "brokerName": "",
                    "serverName": "",
                    "platformType": status,
                }

                response = self.send_get_request(
                    logged_session,
                    '/mascontrol/speed/listTestServer',
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

        @allure.title("节点查询校验")
        def test_query_serverNode(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                new_user = var_manager.get_variable("new_user")
                serverNode = new_user["serverNode"]
                params = {
                    "page": 1,
                    "limit": 50,
                    "asc": "false",
                    "order": "",
                    "serverNode": serverNode,
                    "brokerName": "",
                    "serverName": "",
                    "platformType": "",
                }

                response = self.send_get_request(
                    logged_session,
                    '/mascontrol/speed/listTestServer',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

            with allure.step(f"3. 节点查询校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 serverNode）
                serverNode_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].serverNode",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not serverNode_list:
                    attach_body = f"节点查询校验[{serverNode}]，返回的serverNode列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"节点:{serverNode}查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"节点查询[{serverNode}]暂无数据，跳过校验")
                else:
                    attach_body = f"节点查询[{serverNode}]，返回 {len(serverNode_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"节点:{serverNode}查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，serverNode 也是字符串）
                for idx, actual_status in enumerate(serverNode_list):
                    self.verify_data(
                        actual_value=serverNode,
                        expected_value=actual_status,
                        op=CompareOp.IN,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的serverNode应为{serverNode}，实际为{actual_status}",
                        attachment_name=f"节点:{serverNode}第 {idx + 1} 条记录校验"
                    )

        @allure.title("节点查询校验-查询结果为空")
        def test_query_serverNodeNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 50,
                    "asc": "false",
                    "order": "",
                    "serverNode": "",
                    "brokerName": "",
                    "serverName": "ceshifuwuqi",
                    "platformType": "",
                }

                response = self.send_get_request(
                    logged_session,
                    '/mascontrol/speed/listTestServer',
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

    @allure.story("日志记录-系统日志")
    class TestVPSquerylog(APITestBase):
        # 实例化JsonPath工具类（全局复用）
        json_utils = JsonPathUtils()

        realName = ["xujunhao", "zidonghua"]

        @pytest.mark.parametrize("realName", realName)
        @allure.title("用户查询校验")
        def test_query_realName(self, var_manager, logged_session, realName):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 50,
                    "realName": realName,
                    "module": "",
                    "reqUri": "",
                    "status": ""
                }

                response = self.send_get_request(
                    logged_session,
                    '/sys/log/operate/page',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

            with allure.step(f"3. 用户查询校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 realName）
                realName_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].realName",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not realName_list:
                    attach_body = f"用户查询校验[{realName}]，返回的realName列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"用户:{realName}查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"用户查询[{realName}]暂无数据，跳过校验")
                else:
                    attach_body = f"用户查询[{realName}]，返回 {len(realName_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"用户:{realName}查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，realName 也是字符串）
                for idx, actual_status in enumerate(realName_list):
                    self.verify_data(
                        actual_value=realName,
                        expected_value=actual_status,
                        op=CompareOp.IN,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的realName应为{realName}，实际为{actual_status}",
                        attachment_name=f"用户:{realName}第 {idx + 1} 条记录校验"
                    )

        @allure.title("用户查询校验-查询结果为空")
        def test_query_realNameNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 50,
                    "realName": "测试用户",
                    "module": "",
                    "reqUri": "",
                    "status": ""
                }

                response = self.send_get_request(
                    logged_session,
                    '/sys/log/operate/page',
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

        module = ["账号操作", "交易"]

        @pytest.mark.parametrize("module", module)
        @allure.title("模块名查询校验")
        def test_query_module(self, var_manager, logged_session, module):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 50,
                    "realName": "",
                    "module": module,
                    "reqUri": "",
                    "status": ""
                }

                response = self.send_get_request(
                    logged_session,
                    '/sys/log/operate/page',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

            with allure.step(f"3. 模块名查询校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 module）
                module_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].module",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not module_list:
                    attach_body = f"模块名查询校验[{module}]，返回的module列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"模块名:{module}查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"模块名查询[{module}]暂无数据，跳过校验")
                else:
                    attach_body = f"模块名查询[{module}]，返回 {len(module_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"模块名:{module}查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，module 也是字符串）
                for idx, actual_status in enumerate(module_list):
                    self.verify_data(
                        actual_value=module,
                        expected_value=actual_status,
                        op=CompareOp.IN,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的module应为{module}，实际为{actual_status}",
                        attachment_name=f"模块名:{module}第 {idx + 1} 条记录校验"
                    )

        @allure.title("模块名查询校验-查询结果为空")
        def test_query_moduleNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 50,
                    "realName": "",
                    "module": "测试模块名",
                    "reqUri": "",
                    "status": ""
                }

                response = self.send_get_request(
                    logged_session,
                    '/sys/log/operate/page',
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

        reqUri = ["/subcontrol/trader/orderSend", "/subcontrol/trader"]

        @pytest.mark.parametrize("reqUri", reqUri)
        @allure.title("请求URL查询校验")
        def test_query_reqUri(self, var_manager, logged_session, reqUri):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 50,
                    "realName": "",
                    "module": "",
                    "reqUri": reqUri,
                    "status": ""
                }

                response = self.send_get_request(
                    logged_session,
                    '/sys/log/operate/page',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

            with allure.step(f"3. 请求URL查询校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 reqUri）
                reqUri_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].reqUri",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not reqUri_list:
                    attach_body = f"请求URL查询校验[{reqUri}]，返回的reqUri列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"请求URL:{reqUri}查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"请求URL查询[{reqUri}]暂无数据，跳过校验")
                else:
                    attach_body = f"请求URL查询[{reqUri}]，返回 {len(reqUri_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"请求URL:{reqUri}查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，reqUri 也是字符串）
                for idx, actual_status in enumerate(reqUri_list):
                    self.verify_data(
                        actual_value=reqUri,
                        expected_value=actual_status,
                        op=CompareOp.IN,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的reqUri应为{reqUri}，实际为{actual_status}",
                        attachment_name=f"请求URL:{reqUri}第 {idx + 1} 条记录校验"
                    )

        @allure.title("请求URL查询校验-查询结果为空")
        def test_query_reqUriNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送查询请求"):
                params = {
                    "page": 1,
                    "limit": 50,
                    "realName": "",
                    "module": "",
                    "reqUri": "测试请求URL",
                    "status": ""
                }

                response = self.send_get_request(
                    logged_session,
                    '/sys/log/operate/page',
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

        STATUS_status = [
            (0, "失败"),
            (1, "成功")
        ]

        @pytest.mark.parametrize("status, status_desc", STATUS_status)
        @allure.title("操作状态查询：{status_desc}（{status}）")
        def test_query_status(self, var_manager, logged_session, status, status_desc):
            with allure.step(f"1. 发送请求：操作状态查询-{status_desc}（{status}）"):
                params = {
                    "page": 1,
                    "limit": 50,
                    "realName": "",
                    "module": "",
                    "reqUri": "",
                    "status": status
                }

                response = self.send_get_request(
                    logged_session,
                    '/sys/log/operate/page',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

            with allure.step(f"3. 操作状态查询结果校验：返回记录的status应为{status}"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 status）
                status_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].status",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not status_list:
                    attach_body = f"操作状态查询[{status}]，返回的status列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"操作状态:{status}查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"操作状态查询[{status}]暂无数据，跳过校验")
                else:
                    attach_body = f"操作状态查询[{status}]，返回 {len(status_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"操作状态:{status}查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，status 也是字符串）
                for idx, actual_status in enumerate(status_list):
                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=status,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的status应为{status}，实际为{actual_status}",
                        attachment_name=f"操作状态:{status}第 {idx + 1} 条记录校验"
                    )

    @allure.story("日志记录-跟单软件日志")
    class TestVPSqueryAddLog(APITestBase):
        # 实例化JsonPath工具类（全局复用）
        json_utils = JsonPathUtils()

        @allure.title("时间查询校验")
        def test_query_time(self, var_manager, logged_session):
            with allure.step(f"1. 发送时间查询请求"):
                json_data = {
                    "page": 1,
                    "limit": 200,
                    "platformType": [],
                    "startDate": DATETIME_INIT,
                    "endDate": get_current_time(),
                    "keywords": [],
                    "logInfo": [],
                    "cloudId": [],
                    "vpsId": [],
                    "source": [],
                    "logType": []
                }

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/eslog/queryLogsPage',
                    json_data=json_data
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
                    "$.data.list[*].dateTime",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not dateTime_list:
                    pytest.fail("查询结果为空，不符合预期")
                else:
                    attach_body = f"查询开始时间：[{DATETIME_INIT}]，结束时间：[{get_current_time()}]，返回 {len(dateTime_list)} 条记录"

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
                        message=f"第 {idx + 1} 条记录的dateTime应为{actual_status}",
                        attachment_name=f"时间:{actual_status}第 {idx + 1} 条记录校验"
                    )

                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=get_current_time(),
                        op=CompareOp.LE,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的dateTime应为{actual_status}",
                        attachment_name=f"时间:{actual_status}第 {idx + 1} 条记录校验"
                    )

        @allure.title("时间查询校验-查询结果为空")
        def test_query_timeNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送时间查询请求"):
                json_data = {
                    "page": 1,
                    "limit": 200,
                    "platformType": [],
                    "startDate": get_current_time(),
                    "endDate": DATETIME_INIT,
                    "keywords": [],
                    "logInfo": [],
                    "cloudId": [],
                    "vpsId": [],
                    "source": [],
                    "logType": []
                }

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/eslog/queryLogsPage',
                    json_data=json_data
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
        STATUS_logType = [
            ("连接日志", "日志类型"),
            ("交易日志", "日志类型")
        ]

        @pytest.mark.parametrize("status, status_desc", STATUS_logType)
        @allure.title("查询：{status_desc}（{status}）")
        def test_query_logType(self, var_manager, logged_session, status, status_desc):
            with allure.step(f"1. 发送请求：查询{status_desc}（{status}）"):
                json_data = {
                    "page": 1,
                    "limit": 100,
                    "platformType": [],
                    "startDate": DATETIME_INIT,
                    "endDate": get_current_time(),
                    "keywords": [],
                    "logInfo": [],
                    "cloudId": [],
                    "vpsId": [],
                    "source": [],
                    "logType": [status]
                }

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/eslog/queryLogsPage',
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

        STATUS_source = [
            ("VPS", "来源"),
            ("交易下单", "来源"),
            ("云策略", "来源"),
            ("单账号操作", "来源")
        ]

        @pytest.mark.parametrize("status, status_desc", STATUS_source)
        @allure.title("查询：{status_desc}（{status}）")
        def test_query_source(self, var_manager, logged_session, status, status_desc):
            with allure.step(f"1. 发送请求：查询{status_desc}（{status}）"):
                json_data = {
                    "page": 1,
                    "limit": 100,
                    "platformType": [],
                    "startDate": DATETIME_INIT,
                    "endDate": get_current_time(),
                    "keywords": [],
                    "logInfo": [],
                    "cloudId": [],
                    "vpsId": [],
                    "source": [
                        status
                    ],
                    "logType": []
                }

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/eslog/queryLogsPage',
                    json_data=json_data
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

            with allure.step(f"3. 查询结果校验：返回记录的source应为{status}"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 source）
                source_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].source",
                    default=[],
                    multi_match=True
                )
                # var_manager.set_runtime_variable("query_source_list", source_list)

                # 日志和 Allure 附件优化
                if not source_list:
                    attach_body = f"查询[{status}]，返回的source列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"来源:{status}查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"查询[{status}]暂无数据，跳过校验")
                else:
                    attach_body = f"查询[{status}]，返回 {len(source_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"来源:{status}查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，source 也是字符串）
                for idx, actual_status in enumerate(source_list):
                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=status,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的source应为{status}，实际为{actual_status}",
                        attachment_name=f"来源:{status}第 {idx + 1} 条记录校验"
                    )

        @allure.title("VPS查询校验")
        def test_query_vps_ip(self, var_manager, logged_session):
            # 目标VPS IP（唯一校验值）
            target_vps_ip = var_manager.get_variable("IP_ADDRESS")

            with allure.step(f"1. 发送VPS查询请求（目标IP：{target_vps_ip}）"):
                json_data = {
                    "page": 1,
                    "limit": 200,
                    "platformType": [],
                    "startDate": DATETIME_INIT,
                    "endDate": get_current_time(),
                    "keywords": [],
                    "logInfo": [],
                    "cloudId": [],
                    "vpsId": [target_vps_ip],
                    "source": [],
                    "logType": []
                }

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/eslog/queryLogsPage',
                    json_data=json_data
                )

            with allure.step("2. 返回基础校验"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )
                self.assert_json_value(
                    response,
                    "$.code",
                    0,
                    "响应code字段应为0"
                )

            with allure.step(f"3. 提取查询结果核心数据"):
                response_json = response.json()
                message_list = self.json_utils.extract(
                    response_json,
                    "$.data.list[*].message",
                    default=[],
                    multi_match=True
                )
                total = len(message_list)

                # 日志和报告展示基础信息
                base_attach = f"查询条件：VPS IP={target_vps_ip}\n"
                base_attach += f"返回总记录数：{total}\n"
                base_attach += f"前3条message预览：\n" + "\n".join([msg[:150] + "..." for msg in message_list[:3]])
                logger.info(base_attach)
                allure.attach(
                    body=base_attach,
                    name="VPS查询基础结果",
                    attachment_type="text/plain"
                )

            with allure.step(f"4. 校验：含VPS信息的记录IP必须为{target_vps_ip}"):
                invalid_records = []  # 存储IP不匹配的记录
                has_vps_count = 0  # 含VPS信息的记录数
                no_vps_count = 0  # 不含VPS信息的记录数

                for idx, message in enumerate(message_list):
                    message_str = str(message) if message else ""
                    # 提取VPS IP（兼容 "VPS=张家口（39.101.181.190）" 和 "VPS=39.101.181.190" 格式）
                    vps_match = VPS_IP_PATTERN.search(message_str)

                    if not vps_match:
                        # 不含VPS信息，仅统计
                        no_vps_count += 1
                        continue

                    # 含VPS信息，提取IP并校验
                    has_vps_count += 1
                    actual_vps_ip = vps_match.group(1).strip()  # 提取IP

                    # 核心校验：IP是否与目标一致
                    if actual_vps_ip != target_vps_ip:
                        invalid_msg = f"第{idx + 1}条记录：VPS IP不匹配\n实际IP：{actual_vps_ip}，目标IP：{target_vps_ip}\nmessage预览：{message_str[:100]}..."
                        invalid_records.append(invalid_msg)
                        logger.error(invalid_msg)

                # 统计信息展示
                stat_attach = f"VPS信息统计：\n"
                stat_attach += f"- 总记录数：{total} 条\n"
                stat_attach += f"- 含VPS信息的记录数：{has_vps_count} 条\n"
                stat_attach += f"- 不含VPS信息的记录数：{no_vps_count} 条"
                logger.info(stat_attach)
                allure.attach(
                    body=stat_attach,
                    name="VPS信息统计结果",
                    attachment_type="text/plain"
                )

                # 核心断言：含VPS信息的记录中无IP不匹配
                assert len(invalid_records) == 0, \
                    f"VPS IP校验失败！共{len(invalid_records)}条记录IP不匹配：\n" \
                    f"{chr(10).join(invalid_records)}"

                # 校验通过报告
                success_attach = f"VPS IP校验通过！\n"
                success_attach += f"- 目标IP：{target_vps_ip}\n"
                success_attach += f"- 含VPS信息的{has_vps_count}条记录IP均匹配\n"
                success_attach += f"- 不含VPS信息的{no_vps_count}条记录已忽略"
                logger.info(success_attach)
                allure.attach(
                    body=success_attach,
                    name="VPS IP校验结果",
                    attachment_type="text/plain"
                )

            # 最终总结
            allure.attach(
                body=f"VPS查询校验完成，所有含VPS信息的记录IP均为{target_vps_ip}",
                name="VPS查询校验总结",
                attachment_type="text/plain"
            )

        @allure.title("云策略查询校验")
        def test_query_cloudId(self, var_manager, logged_session, db_transaction):
            with allure.step(f"0. 提取云策略ID"):
                dbcloud_data = self.query_database(
                    db_transaction,
                    f"SELECT * FROM follow_cloud_master WHERE name = %s",
                    ("xjh测试策略",)
                )
                cloud_id = dbcloud_data[0]['id']
                # cloud_id = 106

            with allure.step(f"1. 发送查询请求"):
                json_data = {
                    "page": 1,
                    "limit": 100,
                    "platformType": [],
                    "startDate": DATETIME_INIT,
                    "endDate": get_current_time(),
                    "keywords": [],
                    "logInfo": [],
                    "cloudId": [cloud_id],
                    "vpsId": [],
                    "logType": [],
                    "source": []
                }

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/eslog/queryLogsPage',
                    json_data=json_data
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

            # 3. 提取账号（保留记录与账号的关联关系）
            with allure.step(f"3. 提取所有记录中的账号（按记录分组）"):
                response_json = response.json()
                data_list = response_json.get("data", {}).get("list", [])
                record_accounts = []  # 存储格式：[(记录索引, [账号1, 账号2, ...]), ...]

                # 正则表达式：匹配 "账号：数字" 或 "账号=数字"（冒号/等号，兼容中文冒号）
                account_pattern = re.compile(r'账号[：=](\d+)')

                for idx, item in enumerate(data_list):
                    message = item.get("message", "")
                    # 匹配当前记录的所有账号（支持一条message多个账号）
                    accounts = account_pattern.findall(message)
                    if accounts:
                        record_accounts.append((idx + 1, accounts))  # 记录“第几条记录”和“其包含的账号”
                        logger.info(f"第 {idx + 1} 条记录提取到账号：{accounts}（message：{message[:50]}...）")
                    else:
                        logger.warning(f"第 {idx + 1} 条记录未提取到账号（message：{message[:50]}...）")

                # 断言至少有一条记录提取到账号
                assert len(record_accounts) > 0, f"查询[{cloud_id}]未提取到任何账号"

                # 日志和 Allure 报告展示（按记录分组）
                attach_body = f"查询策略【xjh测试策略】cloud_id：【{cloud_id}】\n"
                attach_body += f"共提取到 {len(record_accounts)} 条含账号的记录：\n"
                for idx, accounts in record_accounts:
                    attach_body += f"- 第 {idx} 条记录：{accounts}\n"
                logger.info(attach_body)
                allure.attach(
                    body=attach_body,
                    name=f"日志:策略【xjh测试策略】cloud_id：【{cloud_id}】提取的账号列表",
                    attachment_type="text/plain"
                )

                # 提取所有去重账号（供后续用例使用，保留原有功能）
                all_accounts = []
                for _, accounts in record_accounts:
                    all_accounts.extend(accounts)
                unique_accounts = list(set(all_accounts))
                var_manager.set_runtime_variable("extracted_accounts", unique_accounts)

            with allure.step("4. 从数据库查询该策略下的所有账号（去重）"):
                db_data = self.query_database(
                    db_transaction,
                    f"SELECT * FROM follow_cloud_trader WHERE cloud_id = %s",
                    (cloud_id,)
                )
                # 1. 提取数据库账号并转字符串（统一格式）
                raw_db_accounts = [str(item["account"]) for item in db_data]
                # 2. 对数据库账号去重（避免重复对比）
                db_accounts = list(set(raw_db_accounts))  # 无序去重（效率高）
                # 若需要保持原始顺序，可替换为：db_accounts = list(dict.fromkeys(raw_db_accounts))  # Python3.7+

                # 日志和Allure展示（补充去重前后对比）
                db_attach_body = f"策略【xjh测试策略】cloud_id：【{cloud_id}】在数据库中关联的账号：\n"
                db_attach_body += f"- 去重前：共 {len(raw_db_accounts)} 个（含重复）→ {raw_db_accounts}\n"
                db_attach_body += f"- 去重后：共 {len(db_accounts)} 个 → {db_accounts}"
                logger.info(db_attach_body)
                allure.attach(
                    body=db_attach_body,
                    name=f"策略【xjh测试策略】cloud_id：【{cloud_id}】关联的数据库账号列表",
                    attachment_type="text/plain"
                )

                # 断言数据库有数据（去重后仍需有有效账号）
                assert len(
                    db_accounts) > 0, f"策略【xjh测试策略】cloud_id：【{cloud_id}】在数据库中未查询到关联账号（去重后为空）"

            with allure.step("5. 校验：每条记录至少有一个账号存在于数据库中"):
                invalid_records = []  # 存储无效记录：[(记录索引, 账号列表), ...]

                for idx, accounts in record_accounts:
                    # 核心逻辑：判断当前记录的所有账号中，是否至少有一个存在于数据库
                    has_valid_account = any(acc in db_accounts for acc in accounts)
                    if not has_valid_account:
                        # 所有账号都不在数据库中，记录为无效
                        invalid_records.append((idx, accounts))
                        logger.error(f"第 {idx} 条记录无效：所有账号{accounts}均不在数据库中")
                    else:
                        # 至少有一个有效账号，记录有效信息
                        valid_accounts = [acc for acc in accounts if acc in db_accounts]
                        logger.info(f"第 {idx} 条记录有效：有效账号{valid_accounts}（数据库中存在）")

                # 核心断言：不允许存在“所有账号都无效”的记录
                assert len(invalid_records) == 0, \
                    f"策略【xjh测试策略】cloud_id：【{cloud_id}】校验失败！以下记录的所有账号均不在数据库中：\n" \
                    + "\n".join([f"  第 {idx} 条记录：账号{accounts}" for idx, accounts in invalid_records]) \
                    + f"\n数据库关联账号：{db_accounts}"

                # 校验通过的日志和Allure报告
                success_msg = f"校验通过！\n"
                success_msg += f"- 含账号的记录总数：{len(record_accounts)} 条\n"
                success_msg += f"- 每条记录均至少有一个账号存在于数据库中\n"
                success_msg += f"- 接口提取去重后账号：{unique_accounts}\n"
                success_msg += f"- 数据库去重后账号：{db_accounts}"
                logger.info(success_msg)
                allure.attach(
                    body=success_msg,
                    name=f"账号一致性校验结果（cloud_id：{cloud_id}）",
                    attachment_type="text/plain"
                )

        # 定义参数化数据源：(查询关键词, 日志描述, 预期的typeDec)
        STATUS_loginfo = [
            # 连接日志相关（关键词对应typeDec=连接日志）
            ("账号断线", "日志标识-连接日志", "连接日志"),
            ("开始重连", "日志标识-连接日志", "连接日志"),
            ("连接成功", "日志标识-连接日志", "连接日志"),
            ("连接失败", "日志标识-连接日志", "连接日志"),
            # 交易日志相关（关键词对应typeDec=交易日志）
            ("策略账号监听", "日志标识-交易日志", "交易日志"),
            ("主指令", "日志标识-交易日志", "交易日志"),
            ("子指令", "日志标识-交易日志", "交易日志"),
            ("自动补平", "日志标识-交易日志", "交易日志"),
            ("单账户操作", "日志标识-交易日志", "交易日志"),
            ("漏单补开", "日志标识-交易日志", "交易日志"),
            ("漏单补平", "日志标识-交易日志", "交易日志"),
            ("交易执行成功", "日志标识-交易日志", "交易日志"),
            ("交易执行失败", "日志标识-交易日志", "交易日志"),
            ("交易失败", "日志标识-交易日志", "交易日志")
        ]

        # 参数化新增 expected_typeDec，对应每条关键词的预期typeDec
        @pytest.mark.parametrize("keyword, log_desc, expected_typeDec", STATUS_loginfo)
        @allure.title("查询：{log_desc}（{keyword}）")
        def test_query_loginfo(self, var_manager, logged_session, keyword, log_desc, expected_typeDec):
            with allure.step(f"1. 发送请求：查询{log_desc}（{keyword}）"):
                json_data = {
                    "page": 1,
                    "limit": 200,
                    "platformType": [],
                    "startDate": DATETIME_INIT,
                    "endDate": get_current_time(),
                    "keywords": [],
                    "logInfo": [keyword],
                    "cloudId": [],
                    "vpsId": [],
                    "source": [],
                    "logType": []
                }

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/eslog/queryLogsPage',
                    json_data=json_data
                )

            with allure.step("2. 基础返回校验"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

            with allure.step(f"3. 提取查询结果：{log_desc}"):
                response_json = response.json()
                # 提取所有记录的 typeDec 和 message（用于后续双重校验）
                typeDec_list = self.json_utils.extract(
                    response_json,
                    "$.data.list[*].typeDec",
                    default=[],
                    multi_match=True
                )
                message_list = self.json_utils.extract(
                    response_json,
                    "$.data.list[*].message",
                    default=[],
                    multi_match=True
                )

                # 日志和Allure附件展示
                total = response_json.get("data", {}).get("total", 0)
                attach_body = f"查询{keyword}\n"
                attach_body += f"预期typeDec：{expected_typeDec}\n"
                attach_body += f"总记录数：{total}\n"
                attach_body += f"typeDec列表：{typeDec_list}\n"
                attach_body += f"message列表（前3条）：{message_list[:3]}"  # 只展示前3条，避免过长

                allure.attach(
                    body=attach_body,
                    name=f"查询结果详情",
                    attachment_type="text/plain"
                )
                logger.info(f"查询关键词[{keyword}]，返回 {total} 条记录，预期typeDec：{expected_typeDec}")

                # 暂无数据时跳过后续校验
                if total == 0 or not typeDec_list or not message_list:
                    logger.warning(f"查询关键词[{keyword}]暂无数据，跳过校验")
                    pytest.skip(f"查询关键词[{keyword}]暂无数据，跳过校验")

            with allure.step(f"4. 校验1：所有记录的typeDec应为{expected_typeDec}"):
                # 遍历所有typeDec，验证是否与预期一致
                for idx, actual_type in enumerate(typeDec_list):
                    self.verify_data(
                        actual_value=actual_type,
                        expected_value=expected_typeDec,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的typeDec错误：预期{expected_typeDec}，实际{actual_type}",
                        attachment_name=f"typeDec校验-第{idx + 1}条"
                    )

            with allure.step(f"5. 校验2：所有记录的message应包含关键词[{keyword}]"):
                # 遍历所有message，验证是否包含查询关键词
                for idx, message in enumerate(message_list):
                    # 用in判断（忽略大小写可加：keyword.lower() in message.lower()）
                    assert keyword in message, \
                        f"第 {idx + 1} 条记录的message不包含关键词[{keyword}]\n" \
                        f"message内容：{message[:100]}..."  # 只展示前100字符

                logger.info(f"校验通过：所有 {len(message_list)} 条记录的message均包含关键词[{keyword}]")
                allure.attach(
                    body=f"校验通过：所有 {len(message_list)} 条记录的message均包含关键词[{keyword}]",
                    name=f"关键词包含校验结果",
                    attachment_type="text/plain"
                )

        @allure.title("多关键词-记录查询校验")
        def test_batch_query_keywords(self, var_manager, logged_session):
            # 1. 定义需要批量查询的关键词列表（动态获取账号+固定关键词）
            new_user = var_manager.get_variable("new_user")
            account = str(new_user["account"])  # 从变量管理器获取账号，转字符串
            # 关键词列表：包含账号 + 其他需要查询的关键词
            keyword_list = [
                account,
                "主动断连",
                "账号断线",
                "测试数据测试数据测试数据测试数据测试数据测试数据测试数据",
                "12345689",
                "交易失败"
            ]

            # 2. 循环遍历关键词，逐个执行查询+校验
            for keyword in keyword_list:
                # 每个关键词的独立步骤（Allure报告中会显示每个关键词的流程）
                with allure.step(f"=== 开始查询关键词：{keyword} ==="):
                    try:
                        with allure.step(f"1. 发送查询请求（关键词：{keyword}）"):
                            json_data = {
                                "page": 1,
                                "limit": 200,
                                "platformType": [],
                                "startDate": DATETIME_INIT,
                                "endDate": get_current_time(),
                                "keywords": [keyword],  # 当前循环的关键词
                                "logInfo": [],
                                "cloudId": [],
                                "vpsId": [],
                                "source": [],
                                "logType": []
                            }

                            response = self.send_post_request(
                                logged_session,
                                '/mascontrol/eslog/queryLogsPage',
                                json_data=json_data
                            )

                        with allure.step(f"2. 基础返回校验（关键词：{keyword}）"):
                            self.assert_json_value(
                                response,
                                "$.msg",
                                "success",
                                f"关键词[{keyword}]查询响应失败"
                            )

                        with allure.step(f"3. 校验关键词[{keyword}]是否存在于所有message中"):
                            response_json = response.json()
                            message_list = self.json_utils.extract(
                                response_json,
                                "$.data.list[*].message",
                                default=[],
                                multi_match=True
                            )
                            total = response_json.get("data", {}).get("total", 0)

                            # 日志和Allure附件（每个关键词独立附件）
                            attach_body = f"关键词：{keyword}\n"
                            attach_body += f"返回总记录数：{total}\n"
                            attach_body += f"message列表（前5条预览）：\n{message_list[:5]}"
                            allure.attach(
                                body=attach_body,
                                name=f"关键词[{keyword}]查询结果详情",
                                attachment_type="text/plain"
                            )
                            logger.info(f"关键词[{keyword}]查询完成，返回 {total} 条记录")

                            # 暂无数据时跳过当前关键词的后续校验，继续下一个
                            if total == 0 or not message_list:
                                logger.warning(f"关键词[{keyword}]查询暂无数据，跳过校验")
                                allure.attach(
                                    body=f"关键词[{keyword}]查询暂无数据，跳过校验",
                                    name=f"关键词[{keyword}]校验结果",
                                    attachment_type="text/plain"
                                )
                                continue  # 跳过当前关键词，执行下一个循环

                            # 核心校验：所有message必须包含当前关键词
                            invalid_messages = []
                            for idx, message in enumerate(message_list):
                                message_str = str(message) if message else ""
                                if keyword not in message_str:
                                    invalid_msg = f"第 {idx + 1} 条记录：{message_str[:200]}..."
                                    invalid_messages.append(invalid_msg)
                                    logger.error(f"关键词[{keyword}]不在第 {idx + 1} 条message中：{invalid_msg}")

                        with allure.step(f"4. 关键词[{keyword}]校验结果"):
                            assert len(invalid_messages) == 0, \
                                f"关键词[{keyword}]校验失败！共 {len(invalid_messages)} 条记录不包含该关键词\n" \
                                f"不包含关键词的记录：\n{chr(10).join(invalid_messages)}"

                            success_msg = f"关键词[{keyword}]校验通过！所有 {len(message_list)} 条记录均包含该关键词"
                            logger.info(success_msg)
                            allure.attach(
                                body=success_msg,
                                name=f"关键词[{keyword}]校验结果",
                                attachment_type="text/plain"
                            )

                    except Exception as e:
                        # 捕获当前关键词的异常，记录日志后继续下一个关键词
                        error_msg = f"关键词[{keyword}]查询失败：{str(e)}"
                        logger.error(error_msg, exc_info=True)
                        allure.attach(
                            body=error_msg,
                            name=f"关键词[{keyword}]查询异常",
                            attachment_type="text/plain"
                        )
                        # 可选：是否终止整个用例（默认继续下一个关键词）
                        # raise e  # 取消注释则当前关键词失败后终止整个用例

            # 所有关键词查询完成
            logger.info(f"所有 {len(keyword_list)} 个关键词批量查询校验完成")
            allure.attach(
                body=f"多次查询校验完成！共查询 {len(keyword_list)} 个关键词",
                name="多次查询总结",
                attachment_type="text/plain"
            )

        # 定义参数化数据源：(查询平台类型, 描述)
        STATUS_logType = [
            ("MT4", "平台类型"),
            ("MT5", "平台类型")
        ]

        # 编译正则表达式（全局复用，匹配 "平台类型=MT4" 或 "平台类型=MT5"）
        PLATFORM_PATTERN = re.compile(r'平台类型=([MT4|MT5]+)')

        @pytest.mark.parametrize("query_platform, status_desc", STATUS_logType)
        @allure.title("查询：{status_desc}（{query_platform}）")
        def test_query_platformType(self, var_manager, logged_session, query_platform, status_desc):
            with allure.step(f"1. 发送请求：查询{status_desc}（{query_platform}）"):
                json_data = {
                    "page": 1,
                    "limit": 200,
                    "platformType": [query_platform],  # 按平台类型筛选（MT4/MT5）
                    "startDate": DATETIME_INIT,
                    "endDate": get_current_time(),
                    "keywords": [],
                    "logInfo": [],
                    "cloudId": [],
                    "vpsId": [],
                    "source": [],
                    "logType": []
                }

                response = self.send_post_request(
                    logged_session,
                    '/mascontrol/eslog/queryLogsPage',
                    json_data=json_data
                )

            with allure.step("2. 基础返回校验"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

            with allure.step(f"3. 提取查询结果：{status_desc}（{query_platform}）"):
                response_json = response.json()
                # 提取所有记录的 message 字段（平台类型在message中）
                message_list = self.json_utils.extract(
                    response_json,
                    "$.data.list[*].message",
                    default=[],
                    multi_match=True
                )
                # 提取总记录数
                total = response_json.get("data", {}).get("total", 0)

                # 日志和Allure附件展示
                attach_body = f"查询平台类型：{query_platform}\n"
                attach_body += f"返回总记录数：{total}\n"
                attach_body += f"message列表（前5条预览）：{message_list[:5]}"
                allure.attach(
                    body=attach_body,
                    name=f"平台类型:{query_platform}查询结果",
                    attachment_type="text/plain"
                )
                logger.info(f"查询平台类型[{query_platform}]，返回 {total} 条记录")

                # 暂无数据时跳过校验
                if total == 0 or not message_list:
                    logger.warning(f"查询平台类型[{query_platform}]暂无数据，跳过校验")
                    pytest.skip(f"查询平台类型[{query_platform}]暂无数据，跳过校验")

            with allure.step(f"4. 校验：所有记录的平台类型应为{query_platform}"):
                invalid_records = []  # 存储平台类型不匹配的记录

                for idx, message in enumerate(message_list):
                    message_str = str(message) if message else ""
                    # 用正则提取 message 中的平台类型（匹配 "平台类型=MT4" 或 "平台类型=MT5"）
                    match = self.PLATFORM_PATTERN.search(message_str)
                    if not match:
                        # 未提取到平台类型
                        invalid_msg = f"第 {idx + 1} 条记录：未提取到平台类型（message：{message_str[:100]}...）"
                        invalid_records.append(invalid_msg)
                        logger.error(invalid_msg)
                    else:
                        actual_platform = match.group(1)  # 提取匹配到的平台类型（MT4/MT5）
                        if actual_platform != query_platform:
                            # 平台类型不匹配
                            invalid_msg = f"第 {idx + 1} 条记录：平台类型不匹配（预期{query_platform}，实际{actual_platform}）\nmessage：{message_str[:100]}..."
                            invalid_records.append(invalid_msg)
                            logger.error(invalid_msg)
                        else:
                            logger.info(f"第 {idx + 1} 条记录校验通过：平台类型={actual_platform}")

                # 核心断言：无无效记录
                assert len(invalid_records) == 0, \
                    f"平台类型[{query_platform}]校验失败！共 {len(invalid_records)} 条记录不符合要求\n" \
                    f"无效记录详情：\n{chr(10).join(invalid_records)}"

                # 校验通过的日志和Allure报告
                success_msg = f"校验通过！所有 {len(message_list)} 条记录的平台类型均为{query_platform}"
                logger.info(success_msg)
                allure.attach(
                    body=success_msg,
                    name=f"平台类型:{query_platform}校验结果",
                    attachment_type="text/plain"
                )
