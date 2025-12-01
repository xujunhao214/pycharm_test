import time
import math
import allure
import logging
import pytest
import re
from lingkuan_1202.VAR.VAR import *
from lingkuan_1202.conftest import var_manager
from lingkuan_1202.commons.api_base import *
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

    #     @allure.title("服务器查询校验")
    #     def test_query_server(self, var_manager, logged_session):
    #         with allure.step(f"1. 发送查询请求"):
    #             new_user = var_manager.get_variable("new_user")
    #             server = new_user["platform"]
    #             params = {
    #                 "page": 1,
    #                 "limit": 50,
    #                 "asc": "false",
    #                 "order": "update_time",
    #                 "loading": "false",
    #                 "brokerName": "",
    #                 "server": server,
    #                 "platformType": "",
    #             }
    #
    #             response = self.send_get_request(
    #                 logged_session,
    #                 '/mascontrol/platform/page',
    #                 params=params
    #             )
    #
    #         with allure.step("2. 返回校验"):
    #             self.assert_json_value(
    #                 response,
    #                 "$.msg",
    #                 "success",
    #                 "响应msg字段应为success"
    #             )
    #
    #         with allure.step(f"3. 服务器查询校验"):
    #             # 修复：正确的 JsonPath 表达式（提取所有记录的 server）
    #             server_list = self.json_utils.extract(
    #                 response.json(),
    #                 "$.data.list[*].server",
    #                 default=[],
    #                 multi_match=True
    #             )
    #
    #             # 日志和 Allure 附件优化
    #             if not server_list:
    #                 attach_body = f"服务器查询校验[{server}]，返回的server列表为空（暂无数据）"
    #                 logger.info(attach_body)
    #                 allure.attach(
    #                     body=attach_body,
    #                     name=f"服务器:{server}查询结果",
    #                     attachment_type="text/plain"
    #                 )
    #                 # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
    #                 pytest.skip(f"服务器查询[{server}]暂无数据，跳过校验")
    #             else:
    #                 attach_body = f"服务器查询[{server}]，返回 {len(server_list)} 条记录"
    #                 logger.info(attach_body)
    #                 allure.attach(
    #                     body=attach_body,
    #                     name=f"服务器:{server}查询结果",
    #                     attachment_type="text/plain"
    #                 )
    #
    #             # 修复：去掉 int() 强制转换（status 是字符串，server 也是字符串）
    #             for idx, actual_status in enumerate(server_list):
    #                 self.verify_data(
    #                     actual_value=server,
    #                     expected_value=actual_status,
    #                     op=CompareOp.IN,
    #                     use_isclose=False,
    #                     message=f"第 {idx + 1} 条记录的server应为{server}，实际为{actual_status}",
    #                     attachment_name=f"服务器:{server}第 {idx + 1} 条记录校验"
    #                 )
    #
    #     @allure.title("服务器查询校验-查询结果为空")
    #     def test_query_serverNO(self, var_manager, logged_session):
    #         with allure.step(f"1. 发送查询请求"):
    #             params = {
    #                 "page": 1,
    #                 "limit": 50,
    #                 "asc": "false",
    #                 "order": "update_time",
    #                 "loading": "false",
    #                 "brokerName": "",
    #                 "server": "ceshifuwuqi",
    #                 "platformType": "",
    #             }
    #
    #             response = self.send_get_request(
    #                 logged_session,
    #                 '/mascontrol/platform/page',
    #                 params=params
    #             )
    #
    #         with allure.step("2. 返回校验"):
    #             self.assert_json_value(
    #                 response,
    #                 "$.msg",
    #                 "success",
    #                 "响应msg字段应为success"
    #             )
    #
    #         with allure.step("3. 查询校验"):
    #             self.json_utils.assert_empty_list(
    #                 data=response.json(),
    #                 expression="$.data.list",
    #             )
    #             logging.info("查询结果符合预期：list为空列表")
    #             allure.attach("查询结果为空，符合预期", 'text/plain')
    #
    #     STATUS_platformType = [
    #         (0, "MT4"),
    #         (1, "MT5")
    #     ]
    #
    #     @pytest.mark.parametrize("status, status_desc", STATUS_platformType)
    #     @allure.title("平台类型查询：{status_desc}（{status}）")
    #     def test_query_platformType(self, var_manager, logged_session, status, status_desc):
    #         with allure.step(f"1. 发送请求：平台类型查询-{status_desc}（{status}）"):
    #             params = {
    #                 "page": 1,
    #                 "limit": 50,
    #                 "asc": "false",
    #                 "order": "update_time",
    #                 "loading": "false",
    #                 "brokerName": "",
    #                 "server": "",
    #                 "platformType": status,
    #             }
    #
    #             response = self.send_get_request(
    #                 logged_session,
    #                 '/mascontrol/platform/page',
    #                 params=params
    #             )
    #
    #         with allure.step("2. 返回校验"):
    #             self.assert_json_value(
    #                 response,
    #                 "$.msg",
    #                 "success",
    #                 "响应msg字段应为success"
    #             )
    #
    #         with allure.step(f"3. 平台类型查询结果校验：返回记录的platformType应为{status}"):
    #             # 修复：正确的 JsonPath 表达式（提取所有记录的 platformType）
    #             platformType_list = self.json_utils.extract(
    #                 response.json(),
    #                 "$.data.list[*].platformType",
    #                 default=[],
    #                 multi_match=True
    #             )
    #
    #             # 日志和 Allure 附件优化
    #             if not platformType_list:
    #                 attach_body = f"平台类型查询[{status}]，返回的platformType列表为空（暂无数据）"
    #                 logger.info(attach_body)
    #                 allure.attach(
    #                     body=attach_body,
    #                     name=f"平台类型:{status}查询结果",
    #                     attachment_type="text/plain"
    #                 )
    #                 # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
    #                 pytest.skip(f"平台类型查询[{status}]暂无数据，跳过校验")
    #             else:
    #                 attach_body = f"平台类型查询[{status}]，返回 {len(platformType_list)} 条记录"
    #                 logger.info(attach_body)
    #                 allure.attach(
    #                     body=attach_body,
    #                     name=f"平台类型:{status}查询结果",
    #                     attachment_type="text/plain"
    #                 )
    #
    #             # 修复：去掉 int() 强制转换（status 是字符串，platformType 也是字符串）
    #             for idx, actual_status in enumerate(platformType_list):
    #                 self.verify_data(
    #                     actual_value=actual_status,
    #                     expected_value=status,
    #                     op=CompareOp.EQ,
    #                     use_isclose=False,
    #                     message=f"第 {idx + 1} 条记录的platformType应为{status}，实际为{actual_status}",
    #                     attachment_name=f"平台类型:{status}第 {idx + 1} 条记录校验"
    #                 )
    #
    # @allure.story("平台管理-服务器管理")
    # class TestVPSqueryServer(APITestBase):
    #     # 实例化JsonPath工具类（全局复用）
    #     json_utils = JsonPathUtils()
    #
    #     @allure.title("券商查询校验")
    #     def test_query_brokeName(self, var_manager, logged_session):
    #         with allure.step(f"1. 发送查询请求"):
    #             brokeName = var_manager.get_variable("broker_name")
    #             # 统一转为小写，用于后续不区分大小写校验（避免硬编码大小写问题）
    #             brokeName_lower = brokeName.lower()
    #             params = {
    #                 "page": 1,
    #                 "limit": 50,
    #                 "asc": "false",
    #                 "order": "",
    #                 "serverNode": "",
    #                 "brokerName": brokeName_lower,
    #                 "serverName": "",
    #                 "platformType": "",
    #             }
    #
    #             response = self.send_get_request(
    #                 logged_session,
    #                 '/mascontrol/speed/listTestServer',
    #                 params=params
    #             )
    #
    #         with allure.step("2. 返回校验"):
    #             self.assert_json_value(
    #                 response,
    #                 "$.msg",
    #                 "success",
    #                 "响应msg字段应为success"
    #             )
    #
    #         with allure.step(f"3. 券商查询校验（不区分大小写，包含{brokeName}）"):
    #             # 提取所有记录的 brokerName
    #             brokeName_list = self.json_utils.extract(
    #                 response.json(),
    #                 "$.data.list[*].brokerName",
    #                 default=[],
    #                 multi_match=True
    #             )
    #
    #             # 日志和 Allure 附件优化
    #             if not brokeName_list:
    #                 attach_body = f"券商查询校验[{brokeName}]，返回的brokerName列表为空（暂无数据）"
    #                 logger.info(attach_body)
    #                 allure.attach(
    #                     body=attach_body,
    #                     name=f"券商:{brokeName}查询结果",
    #                     attachment_type="text/plain"
    #                 )
    #                 pytest.skip(f"券商查询[{brokeName}]暂无数据，跳过校验")
    #             else:
    #                 attach_body = f"券商查询[{brokeName}]，返回 {len(brokeName_list)} 条记录：{brokeName_list}"
    #                 logger.info(attach_body)
    #                 allure.attach(
    #                     body=attach_body,
    #                     name=f"券商:{brokeName}查询结果",
    #                     attachment_type="text/plain"
    #                 )
    #
    #             # 核心修复：不区分大小写的模糊匹配校验
    #             for idx, actual_name in enumerate(brokeName_list):
    #                 # 实际值转为小写，与预期值（小写）进行包含匹配
    #                 actual_name_lower = actual_name.lower()
    #
    #                 # 思路：将「实际值包含预期值」转为「预期值 in 实际值」，并统一大小写
    #                 self.verify_data(
    #                     actual_value=brokeName_lower,
    #                     expected_value=actual_name_lower,
    #                     op=CompareOp.IN,
    #                     use_isclose=False,
    #                     message=f"第 {idx + 1} 条记录的brokerName[{actual_name}]应包含{brokeName}",
    #                     attachment_name=f"券商:{brokeName}第 {idx + 1} 条记录校验"
    #                 )
    #
    #     @allure.title("券商查询校验-查询结果为空")
    #     def test_query_brokerNameNO(self, var_manager, logged_session):
    #         with allure.step(f"1. 发送查询请求"):
    #             params = {
    #                 "page": 1,
    #                 "limit": 50,
    #                 "asc": "false",
    #                 "order": "",
    #                 "serverNode": "",
    #                 "brokerName": "ceshiquanshang",
    #                 "serverName": "",
    #                 "platformType": "",
    #             }
    #
    #             response = self.send_get_request(
    #                 logged_session,
    #                 '/mascontrol/speed/listTestServer',
    #                 params=params
    #             )
    #
    #         with allure.step("2. 返回校验"):
    #             self.assert_json_value(
    #                 response,
    #                 "$.msg",
    #                 "success",
    #                 "响应msg字段应为success"
    #             )
    #
    #         with allure.step("3. 查询校验"):
    #             self.json_utils.assert_empty_list(
    #                 data=response.json(),
    #                 expression="$.data.list",
    #             )
    #             logging.info("查询结果符合预期：list为空列表")
    #             allure.attach("查询结果为空，符合预期", 'text/plain')
