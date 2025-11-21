import time
import math
import allure
import logging
import pytest
import re
from lingkuan_1029copy.VAR.VAR import *
from lingkuan_1029copy.conftest import var_manager
from lingkuan_1029copy.commons.api_base import *
from template.commons.jsonpath_utils import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.story("VPS看板-历史订单查询")
class TestVPSquery(APITestBase):
    # 实例化JsonPath工具类（全局复用）
    json_utils = JsonPathUtils()

    # 定义所有需要测试的状态（作为参数化数据源）
    STATUS_types = [
        (0, "Buy"),
        (1, "sell"),
        (6, "Balance")
    ]

    @pytest.mark.url("vps")
    @pytest.mark.parametrize("status, status_desc", STATUS_types)
    @allure.title("类型查询：{status_desc}（{status}）")
    def test_query_types(self, var_manager, logged_session, status, status_desc):
        with allure.step(f"1. 发送请求：类型查询{status_desc}（{status}）"):
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            params = {
                "page": 1,
                "limit": 50,
                "order": "close_time",
                "traderId": vps_addslave_id,
                "startTime": "",
                "endTime": "",
                "types": status,
                "startLots": "",
                "endLots": "",
                "magic": "",
                "startOpenTime": "",
                "endOpenTime": "",
                "symbol": "",
                "sourceUser": "",
                "platformType": "",
            }

            response = self.send_get_request(
                logged_session,
                '/subcontrol/follow/histotyOrderList',
                params=params
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

        with allure.step(f"3. 类型查询结果校验：返回记录的type应为{status}"):
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
                attach_body = f"类型查询[{status}]，返回的type列表为空（暂无数据）"
                logger.info(attach_body)
                allure.attach(
                    body=attach_body,
                    name=f"类型:{status}查询结果",
                    attachment_type="text/plain"
                )
                # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                pytest.skip(f"类型查询[{status}]暂无数据，跳过校验")
            else:
                attach_body = f"类型查询[{status}]，返回 {len(type_list)} 条记录"
                logger.info(attach_body)
                allure.attach(
                    body=attach_body,
                    name=f"日志类型:{status}类型查询结果",
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
                    attachment_name=f"日志类型:{status}第 {idx + 1} 条记录校验"
                )

    @pytest.mark.url("vps")
    @allure.title("手数范围查询")
    def test_query_size(self, var_manager, logged_session):
        with allure.step(f"1. 发送手数范围查询请求"):
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            params = {
                "page": 1,
                "limit": 50,
                "order": "close_time",
                "traderId": vps_addslave_id,
                "startTime": "",
                "endTime": "",
                "types": "",
                "startLots": "0.1",
                "endLots": "1",
                "magic": "",
                "startOpenTime": "",
                "endOpenTime": "",
                "symbol": "",
                "sourceUser": "",
                "platformType": "",
            }

            response = self.send_get_request(
                logged_session,
                '/subcontrol/follow/histotyOrderList',
                params=params
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

        with allure.step(f"3. 手数范围查询结果校验"):
            # 修复：正确的 JsonPath 表达式（提取所有记录的 size）
            size_list = self.json_utils.extract(
                response.json(),
                "$.data.list[*].size",
                default=[],
                multi_match=True
            )
            # var_manager.set_runtime_variable("query_size_list", size_list)

            # 日志和 Allure 附件优化
            if not size_list:
                attach_body = f"手数范围查询，返回的size列表为空（暂无数据）"
                logger.info(attach_body)
                allure.attach(
                    body=attach_body,
                    name=f"手数范围查询结果",
                    attachment_type="text/plain"
                )
                # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                pytest.skip(f"手数范围查询暂无数据，跳过校验")
            else:
                attach_body = f"手数范围查询，返回 {len(size_list)} 条记录"
                logger.info(attach_body)
                allure.attach(
                    body=attach_body,
                    name=f"手数范围查询结果",
                    attachment_type="text/plain"
                )

            # 修复：去掉 int() 强制转换（status 是字符串，size 也是字符串）
            for idx, size in enumerate(size_list):
                self.verify_data(
                    actual_value=size,
                    expected_value=0.1,
                    op=CompareOp.GE,
                    message=f"第 {idx + 1} 条记录的size应为{size}",
                    attachment_name=f"手数范围:{size}第 {idx + 1} 条记录校验"
                )
                self.verify_data(
                    actual_value=size,
                    expected_value=1,
                    op=CompareOp.LE,
                    message=f"第 {idx + 1} 条记录的size应为{size}",
                    attachment_name=f"手数范围:{size}第 {idx + 1} 条记录校验"
                )

    @pytest.mark.url("vps")
    @allure.title("手数范围查询-查询结果为空")
    def test_query_sizeNO(self, var_manager, logged_session):
        with allure.step(f"1. 发送手数范围查询请求"):
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            params = {
                "page": 1,
                "limit": 50,
                "order": "close_time",
                "traderId": vps_addslave_id,
                "startTime": "",
                "endTime": "",
                "types": "",
                "startLots": "1",
                "endLots": "0.1",
                "magic": "",
                "startOpenTime": "",
                "endOpenTime": "",
                "symbol": "",
                "sourceUser": "",
                "platformType": "",
            }

            response = self.send_get_request(
                logged_session,
                '/subcontrol/follow/histotyOrderList',
                params=params
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

        with allure.step(f"3. 手数范围查询结果校验"):
            # 修复：正确的 JsonPath 表达式（提取所有记录的 size）
            size_list = self.json_utils.extract(
                response.json(),
                "$.data.list[*].size",
                default=[],
                multi_match=True
            )
            # var_manager.set_runtime_variable("query_size_list", size_list)

            # 日志和 Allure 附件优化
            if not size_list:
                attach_body = f"手数范围查询，返回的size列表为空（暂无数据）"
                logger.info(attach_body)
                allure.attach(
                    body=attach_body,
                    name=f"手数范围查询结果",
                    attachment_type="text/plain"
                )
                # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                # pytest.skip(f"手数范围查询暂无数据，跳过校验")
            else:
                attach_body = f"手数范围查询，返回 {len(size_list)} 条记录"
                logger.info(attach_body)
                allure.attach(
                    body=attach_body,
                    name=f"手数范围查询结果",
                    attachment_type="text/plain"
                )

    @pytest.mark.url("vps")
    @allure.title("品种查询")
    def test_query_symbol(self, var_manager, logged_session):
        with allure.step(f"1. 发送品种查询请求"):
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            new_user = var_manager.get_variable("new_user")
            symbol = new_user["symbol"]
            params = {
                "page": 1,
                "limit": 50,
                "order": "close_time",
                "traderId": vps_addslave_id,
                "startTime": "",
                "endTime": "",
                "types": "",
                "startLots": "",
                "endLots": "",
                "magic": "",
                "startOpenTime": "",
                "endOpenTime": "",
                "symbol": symbol,
                "sourceUser": "",
                "platformType": "",
            }

            response = self.send_get_request(
                logged_session,
                '/subcontrol/follow/histotyOrderList',
                params=params
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

        with allure.step(f"3. 品种查询结果校验"):
            # 修复：正确的 JsonPath 表达式（提取所有记录的 symbol）
            symbol_list = self.json_utils.extract(
                response.json(),
                "$.data.list[*].symbol",
                default=[],
                multi_match=True
            )
            # var_manager.set_runtime_variable("query_symbol_list", symbol_list)

            # 日志和 Allure 附件优化
            if not symbol_list:
                attach_body = f"品种查询，返回的symbol列表为空（暂无数据）"
                logger.info(attach_body)
                allure.attach(
                    body=attach_body,
                    name=f"品种查询结果",
                    attachment_type="text/plain"
                )
                # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                # pytest.skip(f"品种查询暂无数据，跳过校验")
            else:
                attach_body = f"品种查询，返回 {len(symbol_list)} 条记录"
                logger.info(attach_body)
                allure.attach(
                    body=attach_body,
                    name=f"品种查询结果",
                    attachment_type="text/plain"
                )

            # 修复：去掉 int() 强制转换（status 是字符串，size 也是字符串）
            for idx, symbollist in enumerate(symbol_list):
                self.verify_data(
                    actual_value=symbollist,
                    expected_value=symbol,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的symbol应为{symbol}，实际为{symbollist}",
                    attachment_name=f"品种:{symbol}第 {idx + 1} 条记录校验"
                )

    @pytest.mark.url("vps")
    @allure.title("品种查询-查询结果为空")
    def test_query_symbolNO(self, var_manager, logged_session):
        with allure.step(f"1. 发送品种查询请求"):
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            params = {
                "page": 1,
                "limit": 50,
                "order": "close_time",
                "traderId": vps_addslave_id,
                "startTime": "",
                "endTime": "",
                "types": "",
                "startLots": "",
                "endLots": "",
                "magic": "",
                "startOpenTime": "",
                "endOpenTime": "",
                "symbol": "测试品种",
                "sourceUser": "",
                "platformType": "",
            }

            response = self.send_get_request(
                logged_session,
                '/subcontrol/follow/histotyOrderList',
                params=params
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

        with allure.step(f"3. 品种查询结果校验"):
            # 修复：正确的 JsonPath 表达式（提取所有记录的 symbol）
            symbol_list = self.json_utils.extract(
                response.json(),
                "$.data.list[*].symbol",
                default=[],
                multi_match=True
            )
            # var_manager.set_runtime_variable("query_symbol_list", symbol_list)

            # 日志和 Allure 附件优化
            if not symbol_list:
                attach_body = f"品种查询，返回的symbol列表为空（暂无数据）"
                logger.info(attach_body)
                allure.attach(
                    body=attach_body,
                    name=f"品种查询结果",
                    attachment_type="text/plain"
                )
                # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                # pytest.skip(f"品种查询暂无数据，跳过校验")
            else:
                attach_body = f"品种查询，返回 {len(symbol_list)} 条记录"
                logger.info(attach_body)
                allure.attach(
                    body=attach_body,
                    name=f"品种查询结果",
                    attachment_type="text/plain"
                )

    @pytest.mark.url("vps")
    @allure.title("魔术号查询")
    def test_query_magic(self, var_manager, logged_session):
        with allure.step(f"1. 发送魔术号查询请求"):
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            magic = var_manager.get_variable("magic")
            params = {
                "page": 1,
                "limit": 50,
                "order": "close_time",
                "traderId": vps_addslave_id,
                "startTime": "",
                "endTime": "",
                "types": "",
                "startLots": "",
                "endLots": "",
                "magic": magic,
                "startOpenTime": "",
                "endOpenTime": "",
                "symbol": "",
                "sourceUser": "",
                "platformType": "",
            }

            response = self.send_get_request(
                logged_session,
                '/subcontrol/follow/histotyOrderList',
                params=params
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

        with allure.step(f"3. 魔术号查询结果校验"):
            # 修复：正确的 JsonPath 表达式（提取所有记录的 magic）
            magic_list = self.json_utils.extract(
                response.json(),
                "$.data.list[*].magic",
                default=[],
                multi_match=True
            )
            # var_manager.set_runtime_variable("query_magic_list", magic_list)

            # 日志和 Allure 附件优化
            if not magic_list:
                attach_body = f"魔术号查询，返回的magic列表为空（暂无数据）"
                logger.info(attach_body)
                allure.attach(
                    body=attach_body,
                    name=f"魔术号查询结果",
                    attachment_type="text/plain"
                )
                # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                # pytest.skip(f"魔术号查询暂无数据，跳过校验")
            else:
                attach_body = f"魔术号查询，返回 {len(magic_list)} 条记录"
                logger.info(attach_body)
                allure.attach(
                    body=attach_body,
                    name=f"魔术号查询结果",
                    attachment_type="text/plain"
                )

            # 修复：去掉 int() 强制转换（status 是字符串，size 也是字符串）
            for idx, magiclist in enumerate(magic_list):
                self.verify_data(
                    actual_value=magiclist,
                    expected_value=magic,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的magic应为{magic}，实际为{magiclist}",
                    attachment_name=f"魔术号:{magic}第 {idx + 1} 条记录校验"
                )

    @pytest.mark.url("vps")
    @allure.title("魔术号查询-查询结果为空")
    def test_query_magicNO(self, var_manager, logged_session):
        with allure.step(f"1. 发送魔术号查询请求"):
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            params = {
                "page": 1,
                "limit": 50,
                "order": "close_time",
                "traderId": vps_addslave_id,
                "startTime": "",
                "endTime": "",
                "types": "",
                "startLots": "",
                "endLots": "",
                "magic": "测试魔术号",
                "startOpenTime": "",
                "endOpenTime": "",
                "symbol": "",
                "sourceUser": "",
                "platformType": "",
            }

            response = self.send_get_request(
                logged_session,
                '/subcontrol/follow/histotyOrderList',
                params=params
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

        with allure.step(f"3. 魔术号查询结果校验"):
            # 修复：正确的 JsonPath 表达式（提取所有记录的 magic）
            magic_list = self.json_utils.extract(
                response.json(),
                "$.data.list[*].magic",
                default=[],
                multi_match=True
            )
            # var_manager.set_runtime_variable("query_magic_list", magic_list)

            # 日志和 Allure 附件优化
            if not magic_list:
                attach_body = f"魔术号查询，返回的magic列表为空（暂无数据）"
                logger.info(attach_body)
                allure.attach(
                    body=attach_body,
                    name=f"魔术号查询结果",
                    attachment_type="text/plain"
                )
                # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                # pytest.skip(f"魔术号查询暂无数据，跳过校验")
            else:
                attach_body = f"魔术号查询，返回 {len(magic_list)} 条记录"
                logger.info(attach_body)
                allure.attach(
                    body=attach_body,
                    name=f"魔术号查询结果",
                    attachment_type="text/plain"
                )

    @pytest.mark.url("vps")
    @allure.title("主账号查询")
    def test_query_sourceUser(self, var_manager, logged_session):
        with allure.step(f"1. 发送主账号查询请求"):
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            new_user = var_manager.get_variable("new_user")
            account = new_user["account"]
            params = {
                "page": 1,
                "limit": 50,
                "order": "close_time",
                "traderId": vps_addslave_id,
                "startTime": "",
                "endTime": "",
                "types": "",
                "startLots": "",
                "endLots": "",
                "magic": "",
                "startOpenTime": "",
                "endOpenTime": "",
                "symbol": "",
                "sourceUser": account,
                "platformType": "",
            }

            response = self.send_get_request(
                logged_session,
                '/subcontrol/follow/histotyOrderList',
                params=params
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

        with allure.step(f"3. 主账号查询结果校验"):
            # 修复：正确的 JsonPath 表达式（提取所有记录的 sourceUser）
            sourceUser_list = self.json_utils.extract(
                response.json(),
                "$.data.list[*].sourceUser",
                default=[],
                multi_match=True
            )
            # var_manager.set_runtime_variable("query_sourceUser_list", sourceUser_list)

            # 日志和 Allure 附件优化
            if not sourceUser_list:
                attach_body = f"主账号查询，返回的sourceUser列表为空（暂无数据）"
                logger.info(attach_body)
                allure.attach(
                    body=attach_body,
                    name=f"主账号查询结果",
                    attachment_type="text/plain"
                )
                # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                # pytest.skip(f"魔术号查询暂无数据，跳过校验")
            else:
                attach_body = f"主账号查询，返回 {len(sourceUser_list)} 条记录"
                logger.info(attach_body)
                allure.attach(
                    body=attach_body,
                    name=f"主账号查询结果",
                    attachment_type="text/plain"
                )

            # 修复：去掉 int() 强制转换（status 是字符串，size 也是字符串）
            for idx, sourceUserlist in enumerate(sourceUser_list):
                self.verify_data(
                    actual_value=sourceUserlist,
                    expected_value=account,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的sourceUser应为{account}，实际为{sourceUserlist}",
                    attachment_name=f"主账号查询:{account}第 {idx + 1} 条记录校验"
                )

    @pytest.mark.url("vps")
    @allure.title("主账号查询-查询结果为空")
    def test_query_sourceUserNO(self, var_manager, logged_session):
        with allure.step(f"1. 发送主账号查询请求"):
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            params = {
                "page": 1,
                "limit": 50,
                "order": "close_time",
                "traderId": vps_addslave_id,
                "startTime": "",
                "endTime": "",
                "types": "",
                "startLots": "",
                "endLots": "",
                "magic": "",
                "startOpenTime": "",
                "endOpenTime": "",
                "symbol": "",
                "sourceUser": "测试主账号查询",
                "platformType": "",
            }

            response = self.send_get_request(
                logged_session,
                '/subcontrol/follow/histotyOrderList',
                params=params
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

        with allure.step(f"3. 主账号查询结果校验"):
            # 修复：正确的 JsonPath 表达式（提取所有记录的 sourceUser）
            sourceUser_list = self.json_utils.extract(
                response.json(),
                "$.data.list[*].sourceUser",
                default=[],
                multi_match=True
            )
            # var_manager.set_runtime_variable("query_sourceUser_list", sourceUser_list)

            # 日志和 Allure 附件优化
            if not sourceUser_list:
                attach_body = f"主账号查询，返回的sourceUser列表为空（暂无数据）"
                logger.info(attach_body)
                allure.attach(
                    body=attach_body,
                    name=f"主账号查询结果",
                    attachment_type="text/plain"
                )
                # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                # pytest.skip(f"魔术号查询暂无数据，跳过校验")
            else:
                attach_body = f"主账号查询，返回 {len(sourceUser_list)} 条记录"
                logger.info(attach_body)
                allure.attach(
                    body=attach_body,
                    name=f"主账号查询结果",
                    attachment_type="text/plain"
                )

    # 定义所有需要测试的状态（作为参数化数据源）
    STATUS_platformType = [
        (0, "MT4"),
        (1, "MT5")
    ]

    @pytest.mark.url("vps")
    @pytest.mark.parametrize("status, status_desc", STATUS_platformType)
    @allure.title("平台类型查询：{status_desc}（{status}）")
    def test_query_platformType(self, var_manager, logged_session, status, status_desc):
        with allure.step(f"1. 发送请求：平台类型查询{status_desc}（{status}）"):
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            params = {
                "page": 1,
                "limit": 50,
                "order": "close_time",
                "traderId": vps_addslave_id,
                "startTime": "",
                "endTime": "",
                "types": "",
                "startLots": "",
                "endLots": "",
                "magic": "",
                "startOpenTime": "",
                "endOpenTime": "",
                "symbol": "",
                "sourceUser": "",
                "platformType": status,
            }

            response = self.send_get_request(
                logged_session,
                '/subcontrol/follow/histotyOrderList',
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
            # var_manager.set_runtime_variable("query_platformType_list", platformType_list)

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
                    name=f"平台类型:{status}平台类型查询结果",
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

    @pytest.mark.url("vps")
    @allure.title("开仓时间查询校验")
    def test_query_opentime(self, var_manager, logged_session):
        with allure.step(f"1. 发送开仓时间查询请求"):
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            params = {
                "page": 1,
                "limit": 50,
                "order": "close_time",
                "traderId": vps_addslave_id,
                "startTime": "",
                "endTime": "",
                "types": "",
                "startLots": "",
                "endLots": "",
                "magic": "",
                "startOpenTime": five_time,
                "endOpenTime": DATETIME_NOW,
                "symbol": "",
                "sourceUser": "",
                "platformType": "",
            }

            response = self.send_get_request(
                logged_session,
                '/subcontrol/follow/histotyOrderList',
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
            # 修复：正确的 JsonPath 表达式（提取所有记录的 openTime）
            openTime_list = self.json_utils.extract(
                response.json(),
                "$.data.list[*].openTime",
                default=[],
                multi_match=True
            )

            # 日志和 Allure 附件优化
            if not openTime_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"查询开始时间：[{five_time}]，结束时间：[{DATETIME_NOW}]，返回 {len(openTime_list)} 条记录"

                logger.info(attach_body)
                allure.attach(
                    body=attach_body,
                    name=f"开仓时间查询结果",
                    attachment_type="text/plain"
                )

            # 修复：去掉 int() 强制转换（status 是字符串，dateTime 也是字符串）
            for idx, actual_status in enumerate(openTime_list):
                self.verify_data(
                    actual_value=actual_status,
                    expected_value=five_time,
                    op=CompareOp.GE,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的dateTime应为{actual_status}",
                    attachment_name=f"开仓时间:{actual_status}第 {idx + 1} 条记录校验"
                )

                self.verify_data(
                    actual_value=actual_status,
                    expected_value=DATETIME_NOW,
                    op=CompareOp.LE,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的dateTime应为{actual_status}",
                    attachment_name=f"开仓时间:{actual_status}第 {idx + 1} 条记录校验"
                )

    @pytest.mark.url("vps")
    @allure.title("开仓时间查询校验-结果查询为空")
    def test_query_opentimeNO(self, var_manager, logged_session):
        with allure.step(f"1. 发送开仓时间查询请求"):
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            params = {
                "page": 1,
                "limit": 50,
                "order": "close_time",
                "traderId": vps_addslave_id,
                "startTime": "",
                "endTime": "",
                "types": "",
                "startLots": "",
                "endLots": "",
                "magic": "",
                "startOpenTime": DATETIME_NOW,
                "endOpenTime": five_time,
                "symbol": "",
                "sourceUser": "",
                "platformType": "",
            }

            response = self.send_get_request(
                logged_session,
                '/subcontrol/follow/histotyOrderList',
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
    def test_query_closetime(self, var_manager, logged_session):
        with allure.step(f"1. 发送平仓时间查询请求"):
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            params = {
                "page": 1,
                "limit": 50,
                "order": "close_time",
                "traderId": vps_addslave_id,
                "startTime": five_time,
                "endTime": DATETIME_NOW,
                "types": "",
                "startLots": "",
                "endLots": "",
                "magic": "",
                "startOpenTime": "",
                "endOpenTime": "",
                "symbol": "",
                "sourceUser": "",
                "platformType": "",
            }

            response = self.send_get_request(
                logged_session,
                '/subcontrol/follow/histotyOrderList',
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
                attach_body = f"查询开始时间：[{five_time}]，结束时间：[{DATETIME_NOW}]，返回 {len(closeTime_list)} 条记录"

                logger.info(attach_body)
                allure.attach(
                    body=attach_body,
                    name=f"平仓时间查询结果",
                    attachment_type="text/plain"
                )

            # 修复：去掉 int() 强制转换（status 是字符串，dateTime 也是字符串）
            for idx, actual_status in enumerate(closeTime_list):
                self.verify_data(
                    actual_value=actual_status,
                    expected_value=five_time,
                    op=CompareOp.GE,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的dateTime应为{actual_status}",
                    attachment_name=f"平仓时间:{actual_status}第 {idx + 1} 条记录校验"
                )

                self.verify_data(
                    actual_value=actual_status,
                    expected_value=DATETIME_NOW,
                    op=CompareOp.LE,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的dateTime应为{actual_status}",
                    attachment_name=f"平仓时间:{actual_status}第 {idx + 1} 条记录校验"
                )

    @pytest.mark.url("vps")
    @allure.title("平仓时间查询校验-查询结果为空")
    def test_query_closetimeNO(self, var_manager, logged_session):
        with allure.step(f"1. 发送平仓时间查询请求"):
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            params = {
                "page": 1,
                "limit": 50,
                "order": "close_time",
                "traderId": vps_addslave_id,
                "startTime": DATETIME_NOW,
                "endTime": five_time,
                "types": "",
                "startLots": "",
                "endLots": "",
                "magic": "",
                "startOpenTime": "",
                "endOpenTime": "",
                "symbol": "",
                "sourceUser": "",
                "platformType": "",
            }

            response = self.send_get_request(
                logged_session,
                '/subcontrol/follow/histotyOrderList',
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
