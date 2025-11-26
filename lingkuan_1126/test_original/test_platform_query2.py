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
