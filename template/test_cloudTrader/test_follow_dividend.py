import time
from template.commons.api_base import APITestBase, CompareOp
import allure
import logging
import pytest
from template.VAR.VAR import *
from template.commons.jsonpath_utils import *
from template.commons.random_generator import *


@allure.feature("账号管理")
class Test_create:
    @allure.story("跟随者账户查询校验")
    class Test_trader(APITestBase):
        # 实例化JsonPath工具类（全局复用）
        json_utils = JsonPathUtils()

        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
        @allure.title("分红时间查询")
        def test_query_dividendTime(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                params = {
                    "_t": current_timestamp_seconds,
                    "page": 1,
                    "limit": 20,
                    "type": "",
                    "status": "",
                    "dividendTimeBegin": dividendTime_ago,
                    "dividendTimeEnd": dividendTime_now,
                    "followerUser": "",
                    "followerTa": "",
                    "dividendUser": ""
                }
                response = self.send_get_request(
                    logged_session,
                    '/agent/agentLevelDividend/page',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step(f"3. 查询校验"):
                dividendType_list = self.json_utils.extract(
                    response.json(),
                    "$.result.list[*].slaveRecords[*].dividendTime",
                    default=[],
                    multi_match=True
                )

                if not dividendType_list:
                    attach_body = f"分红时间查询，返回的dividendTime列表为空（暂无数据）"
                else:
                    attach_body = f"分红时间查询，返回 {len(dividendType_list)} 条记录，dividendTime值如下：\n" + \
                                  "\n".join([f"第 {idx + 1} 条：{s}" for idx, s in enumerate(dividendType_list)])

                allure.attach(
                    body=attach_body,
                    name=f"分红时间查询结果",
                    attachment_type="text/plain"
                )

                for idx, dividendTime in enumerate(dividendType_list):
                    self.verify_data(
                        actual_value=dividendTime,
                        expected_value=dividendTime_ago,
                        op=CompareOp.GE,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的分红时间符合预期",
                        attachment_name=f"第 {idx + 1} 条记录的分红时间校验"
                    )

                    self.verify_data(
                        actual_value=dividendTime,
                        expected_value=dividendTime_now,
                        op=CompareOp.LE,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的分红时间符合预期",
                        attachment_name=f"第 {idx + 1} 条记录的分红时间校验"
                    )

        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
        @allure.title("分红时间查询-查询结果为空")
        def test_query_dividendTimeno(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                params = {
                    "_t": current_timestamp_seconds,
                    "page": 1,
                    "limit": 20,
                    "type": "",
                    "status": "",
                    "dividendTimeBegin": dividendTime_now,
                    "dividendTimeEnd": dividendTime_ago,
                    "followerUser": "",
                    "followerTa": "",
                    "dividendUser": ""
                }
                response = self.send_get_request(
                    logged_session,
                    '/agent/agentLevelDividend/page',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step(f"3. 查询校验"):
                self.json_utils.assert_empty_list(
                    data=response.json(),
                    expression="$.result.list"
                )
                logging.info("查询结果符合预期：records为空列表")
                allure.attach("查询结果为空，符合预期", 'text/plain')

        # 定义所有需要测试的状态（作为参数化数据源）
        STATUS_PARAMS = [
            ("0", "信号源分红"),
            ("1", "代理分红")
        ]

        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
        @pytest.mark.parametrize("status, status_desc", STATUS_PARAMS)
        @allure.title("分红类型查询：{status_desc}（{status}）")
        def test_query_create_time(self, var_manager, logged_session, status, status_desc):
            # 用例级附件：当前状态说明
            allure.attach(
                body=f"分红类型编码：{status}\n分红类型描述：{status_desc}",
                name=f"分红类型:{status_desc}说明",
                attachment_type="text/plain"
            )

            with allure.step("1. 发送请求：查询[{status_desc}]状态（{status}）"):
                params = {
                    "_t": current_timestamp_seconds,
                    "page": 1,
                    "limit": 20,
                    "type": status,
                    "status": "",
                    "dividendTimeBegin": "",
                    "dividendTimeEnd": "",
                    "followerUser": "",
                    "followerTa": "",
                    "dividendUser": ""
                }
                response = self.send_get_request(
                    logged_session,
                    '/agent/agentLevelDividend/page',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step(f"3. 业务校验：返回记录的dividendType应为{status}"):
                dividendType_list = self.json_utils.extract(
                    response.json(),
                    "$.result.list[*].slaveRecords[*].dividendType",
                    default=[],
                    multi_match=True
                )

                if not dividendType_list:
                    attach_body = f"分红类型查询[{status_desc}]，返回的dividendType列表为空（暂无数据）"
                else:
                    attach_body = f"分红类型查询[{status_desc}]，返回 {len(dividendType_list)} 条记录，dividendType值如下：\n" + \
                                  "\n".join([f"第 {idx + 1} 条：{s}" for idx, s in enumerate(dividendType_list)])

                allure.attach(
                    body=attach_body,
                    name=f"分红类型:{status_desc}查询结果",
                    attachment_type="text/plain"
                )

                # 校验每条记录的dividendType
                for idx, actual_status in enumerate(dividendType_list):
                    self.verify_data(
                        actual_value=int(actual_status),
                        expected_value=int(status),
                        op=CompareOp.EQ,
                        message=f"第 {idx + 1} 条记录的dividendType应为{status}",
                        attachment_name=f"分红类型:{status_desc}第 {idx + 1} 条记录校验"
                    )

        # 定义所有需要测试的状态（作为参数化数据源）
        STATUS_PARAMS = [
            ("0", "已结算"),
            ("1", "未结清"),
            ("2", "待结算"),
            ("3", "不分红")
        ]

        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
        @pytest.mark.parametrize("status, status_desc", STATUS_PARAMS)
        @allure.title("分红状态查询：{status_desc}（{status}）")
        def test_query_status(self, var_manager, logged_session, status, status_desc):
            # 用例级附件：当前状态说明
            allure.attach(
                body=f"分红状态编码：{status}\n分红状态描述：{status_desc}",
                name=f"分红状态:{status_desc}说明",
                attachment_type="text/plain"
            )

            with allure.step("1. 发送请求：查询[{status_desc}]状态（{status}）"):
                params = {
                    "_t": current_timestamp_seconds,
                    "page": 1,
                    "limit": 100,
                    "type": "",
                    "status": status,
                    "dividendTimeBegin": "",
                    "dividendTimeEnd": "",
                    "followerUser": "",
                    "followerTa": "",
                    "dividendUser": ""
                }
                response = self.send_get_request(
                    logged_session,
                    '/agent/agentLevelDividend/page',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step(f"3. 业务校验：返回记录的status应为{status}"):
                status_list = self.json_utils.extract(
                    response.json(),
                    "$.result.list[*].slaveRecords[*].status",
                    default=[],
                    multi_match=True
                )

                if not status_list:
                    attach_body = f"分红状态查询[{status_desc}]，返回的status列表为空（暂无数据）"
                else:
                    attach_body = f"分红状态查询[{status_desc}]，返回 {len(status_list)} 条记录，status值如下：\n" + \
                                  "\n".join([f"第 {idx + 1} 条：{s}" for idx, s in enumerate(status_list)])

                allure.attach(
                    body=attach_body,
                    name=f"分红状态:{status_desc}查询结果",
                    attachment_type="text/plain"
                )

                # 校验每条记录的status
                for idx, actual_status in enumerate(status_list):
                    self.verify_data(
                        actual_value=int(actual_status),
                        expected_value=int(status),
                        op=CompareOp.EQ,
                        message=f"第 {idx + 1} 条记录的status应为{status}",
                        attachment_name=f"分红状态:{status_desc}第 {idx + 1} 条记录校验"
                    )

        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
        @allure.title("跟单用户查询")
        def test_query_followerUser(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                login_config = var_manager.get_variable("login_config")
                followerUser = login_config["username"]
                params = {
                    "_t": current_timestamp_seconds,
                    "page": 1,
                    "limit": 100,
                    "type": "",
                    "status": "",
                    "dividendTimeBegin": "",
                    "dividendTimeEnd": "",
                    "followerUser": followerUser,
                    "followerTa": "",
                    "dividendUser": ""
                }
                response = self.send_get_request(
                    logged_session,
                    '/agent/agentLevelDividend/page',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step(f"3. 查询结果校验"):
                followerUser_list = self.json_utils.extract(
                    response.json(),
                    "$.result.list[*].slaveRecords[*].followerUser",
                    default=[],
                    multi_match=True
                )

                if not followerUser_list:
                    attach_body = f"跟单用户查询：{followerUser}，返回的followerUser列表为空（暂无数据）"
                else:
                    attach_body = f"跟单用户查询：{followerUser}，返回 {len(followerUser_list)} 条记录，followerUser值如下：\n" + \
                                  "\n".join([f"第 {idx + 1} 条：{s}" for idx, s in enumerate(followerUser_list)])

                allure.attach(
                    body=attach_body,
                    name=f"跟单用户:{followerUser}查询结果",
                    attachment_type="text/plain"
                )

                for idx, followerUserlist in enumerate(followerUser_list):
                    self.verify_data(
                        actual_value=followerUserlist,
                        expected_value=followerUser,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的followerUser应为{followerUserlist}",
                        attachment_name=f"跟单用户:{followerUser}第 {idx + 1} 条记录校验"
                    )

        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
        @allure.title("跟单用户查询-查询结果为空")
        def test_query_followerUserno(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                params = {
                    "_t": current_timestamp_seconds,
                    "page": 1,
                    "limit": 100,
                    "type": "",
                    "status": "",
                    "dividendTimeBegin": "",
                    "dividendTimeEnd": "",
                    "followerUser": "xxxxxxxxxxxxxxxxx",
                    "followerTa": "",
                    "dividendUser": ""
                }
                response = self.send_get_request(
                    logged_session,
                    '/agent/agentLevelDividend/page',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step(f"3. 查询结果校验"):
                self.json_utils.assert_empty_list(
                    data=response.json(),
                    expression="$.result.list"
                )
                logging.info("查询结果符合预期：records为空列表")
                allure.attach("查询结果为空，符合预期", 'text/plain')

        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
        @allure.title("跟单账号查询")
        def test_query_followerTa(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                followerTa = var_manager.get_variable("follow_account")
                params = {
                    "_t": current_timestamp_seconds,
                    "page": 1,
                    "limit": 100,
                    "type": "",
                    "status": "",
                    "dividendTimeBegin": "",
                    "dividendTimeEnd": "",
                    "followerUser": "",
                    "followerTa": followerTa,
                    "dividendUser": ""
                }
                response = self.send_get_request(
                    logged_session,
                    '/agent/agentLevelDividend/page',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step(f"3. 查询结果校验"):
                followerTa_list = self.json_utils.extract(
                    response.json(),
                    "$.result.list[*].slaveRecords[*].followerTa",
                    default=[],
                    multi_match=True
                )

                if not followerTa_list:
                    attach_body = f"跟单账号查询：{followerTa}，返回的followerTa列表为空（暂无数据）"
                else:
                    attach_body = f"跟单账号查询：{followerTa}，返回 {len(followerTa_list)} 条记录，followerTa值如下：\n" + \
                                  "\n".join([f"第 {idx + 1} 条：{s}" for idx, s in enumerate(followerTa_list)])

                allure.attach(
                    body=attach_body,
                    name=f"跟单账号:{followerTa}查询结果",
                    attachment_type="text/plain"
                )

                for idx, followerUserlist in enumerate(followerTa_list):
                    self.verify_data(
                        actual_value=followerUserlist,
                        expected_value=followerTa,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的followerTa应为{followerUserlist}",
                        attachment_name=f"跟单账号:{followerTa}第 {idx + 1} 条记录校验"
                    )

        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
        @allure.title("跟单账号查询-查询结果为空")
        def test_query_followerTaNO(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                params = {
                    "_t": current_timestamp_seconds,
                    "page": 1,
                    "limit": 100,
                    "type": "",
                    "status": "",
                    "dividendTimeBegin": "",
                    "dividendTimeEnd": "",
                    "followerUser": "",
                    "followerTa": "99999999999",
                    "dividendUser": ""
                }
                response = self.send_get_request(
                    logged_session,
                    '/agent/agentLevelDividend/page',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step(f"3. 查询结果校验"):
                self.json_utils.assert_empty_list(
                    data=response.json(),
                    expression="$.result.list"
                )
                logging.info("查询结果符合预期：records为空列表")
                allure.attach("查询结果为空，符合预期", 'text/plain')

        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
        @allure.title("分红用户查询")
        def test_query_dividendUser(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                login_config = var_manager.get_variable("login_config")
                dividendUser = login_config.get("username")
                params = {
                    "_t": current_timestamp_seconds,
                    "page": 1,
                    "limit": 100,
                    "type": "",
                    "status": "",
                    "dividendTimeBegin": "",
                    "dividendTimeEnd": "",
                    "followerUser": "",
                    "followerTa": "",
                    "dividendUser": dividendUser
                }
                response = self.send_get_request(
                    logged_session,
                    '/agent/agentLevelDividend/page',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step(f"3. 查询结果校验"):
                dividendUser_list = self.json_utils.extract(
                    response.json(),
                    "$.result.list[*].slaveRecords[*].dividendUser",
                    default=[],
                    multi_match=True
                )

                if not dividendUser_list:
                    attach_body = f"分红用户查询：{dividendUser}，返回的dividendUser列表为空（暂无数据）"
                else:
                    attach_body = f"分红用户查询：{dividendUser}，返回 {len(dividendUser_list)} 条记录，dividendUser值如下：\n" + \
                                  "\n".join([f"第 {idx + 1} 条：{s}" for idx, s in enumerate(dividendUser_list)])

                allure.attach(
                    body=attach_body,
                    name=f"分红用户:{dividendUser}查询结果",
                    attachment_type="text/plain"
                )

                # 关键：检查是否存在至少一条符合预期的记录
                matched_records = [
                    (idx + 1, user)  # 记录“符合预期的记录序号和值”
                    for idx, user in enumerate(dividendUser_list)
                    if user == dividendUser  # 对比：实际值 == 预期值
                ]

                # 统一断言：若没有符合预期的记录，则报错
                assert matched_records, (
                    f"分红用户查询校验失败：返回的 {len(dividendUser_list)} 条记录中，"
                    f"没有找到 dividendUser = {dividendUser} 的记录\n"
                    f"所有返回值：{dividendUser_list}"
                )

                allure.attach(
                    body=f"找到 {len(matched_records)} 条符合预期的记录：\n" + \
                         "\n".join([f"第 {idx} 条：{user}" for idx, user in matched_records]),
                    name=f"符合预期的分红用户记录",
                    attachment_type="text/plain"
                )

        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
        @allure.title("分红用户查询-查询结果为空")
        def test_query_dividendUserNO(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                params = {
                    "_t": current_timestamp_seconds,
                    "page": 1,
                    "limit": 100,
                    "type": "",
                    "status": "",
                    "dividendTimeBegin": "",
                    "dividendTimeEnd": "",
                    "followerUser": "",
                    "followerTa": "",
                    "dividendUser": "xxxxxxxx"
                }
                response = self.send_get_request(
                    logged_session,
                    '/agent/agentLevelDividend/page',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step(f"3. 查询结果校验"):
                self.json_utils.assert_empty_list(
                    data=response.json(),
                    expression="$.result.list"
                )
                logging.info("查询结果符合预期：records为空列表")
                allure.attach("查询结果为空，符合预期", 'text/plain')
