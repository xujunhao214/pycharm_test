import time
from template1126.commons.api_base import APITestBase, CompareOp
import allure
import logging
import json
import pytest
from template1126.VAR.VAR import *
from template1126.commons.jsonpath_utils import *
from template1126.commons.random_generator import *


@allure.feature("跟单管理-实时跟单查询校验")
class Test_realtime_query(APITestBase):
    # 实例化JsonPath工具类（全局复用）
    json_utils = JsonPathUtils()

    # 定义所有需要测试的跟随模式（作为参数化数据源）
    following_mode = [
        (1, "智能"),
        (2, "固定比例"),
        (3, "手数"),
        (4, "净值比例")
    ]

    # @pytest.mark.skipif(True, reason="跳过测试")
    # 使用parametrize参数化：每个跟随模式生成一个独立用例
    @pytest.mark.parametrize("status, status_desc", following_mode)
    @allure.title("跟随模式查询：{status_desc}（{status}）")  # 标题动态显示跟随模式信息
    def test_query_following_mode(self, var_manager, logged_session, status, status_desc):
        """按跟随模式拆分的独立用例：查询指定跟随模式并校验结果"""
        # 用例级附件：当前跟随模式说明
        allure.attach(
            body=f"跟随模式编码：{status}\n跟随模式描述：{status_desc}",
            name=f"跟随模式-{status_desc}：说明",
            attachment_type="text/plain"
        )

        with allure.step(f"1. 发送请求：查询[{status_desc}]跟随模式（{status}）"):
            params = {
                "_t": current_timestamp_seconds,
                "following_mode": status,
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "status": "NORMAL,AUDIT"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                params=params
            )

        with allure.step("2. 基础响应校验：success = True"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

        with allure.step(f"3. 查询结果校验：返回记录的following_mode应为{status}"):
            status_list = self.json_utils.extract(
                response.json(),
                "$.result.data.records[*].following_mode",
                default=[],
                multi_match=True
            )

            # 生成查询结果附件
            if not status_list:
                attach_body = f"跟随模式查询-{status_desc}：返回的following_mode为空列表（暂无数据）"
            else:
                attach_body = f"跟随模式查询-{status_desc}，返回 {len(status_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"跟随模式-{status_desc}：查询结果",
                attachment_type="text/plain"
            )

            # 校验每条记录的following_mode
            for idx, actual_status in enumerate(status_list):
                self.verify_data(
                    actual_value=actual_status,
                    expected_value=status,
                    op=CompareOp.EQ,
                    message=f"第 {idx + 1} 条记录的following_mode应为{status}",
                    attachment_name=f"跟随模式-{status_desc}：第 {idx + 1} 条记录校验"
                )

    # 定义所有需要测试的跟随方向状态（作为参数化数据源）
    direction = [
        ("FORWARD", "正向"),
        ("REVERSE", "反向")
    ]

    # @pytest.mark.skipif(True, reason="跳过测试")
    # 使用parametrize参数化：每个跟随方向生成一个独立用例
    @pytest.mark.parametrize("status, status_desc", direction)
    @allure.title("跟随方向查询：{status_desc}（{status}）")  # 标题动态显示跟随方向信息
    def test_query_direction(self, var_manager, logged_session, status, status_desc):
        """按跟随方向拆分的独立用例：查询指定跟随方向并校验结果"""
        # 用例级附件：当前跟随方向说明
        allure.attach(
            body=f"跟随方向编码：{status}\n跟随方向描述：{status_desc}",
            name=f"跟随方向-{status_desc}：说明",
            attachment_type="text/plain"
        )

        with allure.step(f"1. 发送请求：查询[{status_desc}]跟随方向（{status}）"):
            params = {
                "_t": current_timestamp_seconds,
                "direction": status,
                "pageNo": 1,
                "pageSize": 20,
                "status": "NORMAL,AUDIT"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                params=params
            )

        with allure.step("2. 基础响应校验：success = True"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

        with allure.step(f"3. 查询结果校验：返回记录的direction应为{status}"):
            status_list = self.json_utils.extract(
                response.json(),
                "$.result.data.records[*].direction",
                default=[],
                multi_match=True
            )

            # 生成查询结果附件
            if not status_list:
                attach_body = f"跟随方向查询-{status_desc}：返回的direction为空列表（暂无数据）"
            else:
                attach_body = f"跟随方向查询-{status_desc}，返回 {len(status_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"跟随方向-{status_desc}：查询结果",
                attachment_type="text/plain"
            )

            # 校验每条记录的direction
            for idx, actual_status in enumerate(status_list):
                self.verify_data(
                    actual_value=actual_status,
                    expected_value=status,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的direction应为{status}",
                    attachment_name=f"跟随方向-{status_desc}：第 {idx + 1} 条记录校验"
                )

    # 定义所有需要测试的暂停状态（作为参数化数据源）
    pause = [
        (1, "是"),
        (0, "否")
    ]

    # @pytest.mark.skipif(True, reason="跳过测试")
    # 使用parametrize参数化：每个暂停生成一个独立用例
    @pytest.mark.parametrize("status, status_desc", pause)
    @allure.title("暂停查询：{status_desc}（{status}）")  # 标题动态显示暂停信息
    def test_query_pause(self, var_manager, logged_session, status, status_desc):
        """按暂停拆分的独立用例：查询指定暂停并校验结果"""
        # 用例级附件：当前暂停说明
        allure.attach(
            body=f"暂停编码：{status}\n暂停描述：{status_desc}",
            name=f"暂停-{status_desc}：说明",
            attachment_type="text/plain"
        )

        with allure.step(f"1. 发送请求：查询[{status_desc}]暂停（{status}）"):
            params = {
                "_t": current_timestamp_seconds,
                "pause": status,
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "status": "NORMAL,AUDIT"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                params=params
            )

        with allure.step("2. 基础响应校验：success = True"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

        with allure.step(f"3. 查询结果校验：返回记录的pause应为{status}"):
            status_list = self.json_utils.extract(
                response.json(),
                "$.result.data.records[*].pause",
                default=[],
                multi_match=True
            )

            # 生成查询结果附件
            if not status_list:
                attach_body = f"暂停查询-{status_desc}：返回的pause为空列表（暂无数据）"
            else:
                attach_body = f"暂停查询-{status_desc}，返回 {len(status_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"暂停-{status_desc}：查询结果",
                attachment_type="text/plain"
            )

            # 校验每条记录的pause
            for idx, actual_status in enumerate(status_list):
                self.verify_data(
                    actual_value=actual_status,
                    expected_value=status,
                    op=CompareOp.EQ,
                    message=f"第 {idx + 1} 条记录的pause应为{status}",
                    attachment_name=f"暂停-{status_desc}：第 {idx + 1} 条记录校验"
                )

    # 定义所有需要测试的状态（作为参数化数据源）
    status = [
        ("NORMAL", "正常"),
        ("", "历史"),
        ("AUDIT", "审核中"),
        ("", "订阅过期"),
        ("", "取消订阅"),
        ("", "信号源关闭")
    ]

    # @pytest.mark.skipif(True, reason="跳过测试")
    # 使用parametrize参数化：每个状态生成一个独立用例
    @pytest.mark.parametrize("status, status_desc", status)
    @allure.title("状态查询：{status_desc}（{status}）")  # 标题动态显示状态信息
    def test_query_status(self, var_manager, logged_session, status, status_desc):
        """按状态拆分的独立用例：查询指定状态并校验结果"""
        # 用例级附件：当前状态说明
        allure.attach(
            body=f"状态编码：{status}\n状态描述：{status_desc}",
            name=f"状态-{status_desc}：说明",
            attachment_type="text/plain"
        )

        with allure.step(f"1. 发送请求：查询[{status_desc}]状态（{status}）"):
            params = {
                "_t": current_timestamp_seconds,
                "status": status,
                "pageNo": 1,
                "pageSize": 20
                # "status": "NORMAL,AUDIT"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                params=params
            )

        with allure.step("2. 基础响应校验：success = True"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

        with allure.step(f"3. 查询结果校验：返回记录的status应为{status}"):
            status_list = self.json_utils.extract(
                response.json(),
                "$.result.data.records[*].status",
                default=[],
                multi_match=True
            )

            # 生成查询结果附件
            if not status_list:
                attach_body = f"状态查询-{status_desc}：返回的status为空列表（暂无数据）"
            else:
                attach_body = f"状态查询-{status_desc}，返回 {len(status_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"状态-{status_desc}：查询结果",
                attachment_type="text/plain"
            )

            # 校验每条记录的status
            for idx, actual_status in enumerate(status_list):
                self.verify_data(
                    actual_value=actual_status,
                    expected_value=status,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的status应为{status}",
                    attachment_name=f"状态-{status_desc}：第 {idx + 1} 条记录校验"
                )

    @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("跟随时间查询")
    def test_query_create_time(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "start_time_begin": ONE_HOUR_AGO,
                "start_time_end": DATETIME_NOW,
                "pageNo": 1,
                "pageSize": 20,
                "status": "NORMAL,AUDIT"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                params=params
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

        with allure.step("3. 查询校验"):
            create_time_list = self.json_utils.extract(
                response.json(),
                "$.result.data.records[*].create_time",
                default=[],
                multi_match=True
            )

            if not create_time_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"跟随时间查询-开始时间：{ONE_HOUR_AGO}，返回 {len(create_time_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"{ONE_HOUR_AGO}查询结果",
                attachment_type="text/plain"
            )

            for idx, create_time in enumerate(create_time_list):
                self.verify_data(
                    actual_value=create_time,
                    expected_value=ONE_HOUR_AGO,
                    op=CompareOp.GE,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的跟随时间符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的跟随时间校验"
                )

                self.verify_data(
                    actual_value=create_time,
                    expected_value=DATETIME_NOW,
                    op=CompareOp.LE,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的跟随时间符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的跟随时间校验"
                )

    # @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("跟随时间查询-查询结果为空")
    def test_query_create_timeNo(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "start_time_begin": DATETIME_NOW,
                "start_time_end": ONE_HOUR_AGO,
                "pageNo": 1,
                "pageSize": 20,
                "status": "NORMAL,AUDIT"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                params=params
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

        with allure.step("3. 查询校验"):
            self.json_utils.assert_empty_list(
                data=response.json(),
                expression="$.result.data.records"
            )
            logging.info("查询结果符合预期：records为空列表")
            allure.attach("查询结果为空，符合预期", 'text/plain')

    # @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("跟随者账户查询")
    def test_query_account(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            follow_account = var_manager.get_variable("follow_account")
            params = {
                "_t": current_timestamp_seconds,
                "account": follow_account,
                "pageNo": 1,
                "pageSize": 20,
                "status": "NORMAL,AUDIT"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                params=params
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

        with allure.step("3. 查询校验"):
            account_list = self.json_utils.extract(
                response.json(),
                "$.result.data.records[*].account",
                default=[],
                multi_match=True
            )

            if not account_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"跟随者账户查询：{follow_account}，返回 {len(account_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"{follow_account}查询结果",
                attachment_type="text/plain"
            )

            for idx, account in enumerate(account_list):
                self.verify_data(
                    actual_value=account,
                    expected_value=follow_account,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的跟随者账户符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的跟随者账户校验"
                )

    # @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("跟随者账户查询-查询结果为空")
    def test_query_accountNO(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "account": "9999999999999999",
                "pageNo": 1,
                "pageSize": 20,
                "status": "NORMAL,AUDIT"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                params=params
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

        with allure.step("3. 查询校验"):
            self.json_utils.assert_empty_list(
                data=response.json(),
                expression="$.result.data.records"
            )
            logging.info("查询结果符合预期：records为空列表")
            allure.attach("查询结果为空，符合预期", 'text/plain')

    # @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("喊单者账户查询")
    def test_query_master_account(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            trader_account = var_manager.get_variable("trader_account")
            params = {
                "_t": current_timestamp_seconds,
                "master_account": trader_account,
                "pageNo": 1,
                "pageSize": 20,
                "status": "NORMAL,AUDIT"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                params=params
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

        with allure.step("3. 查询校验"):
            master_account_list = self.json_utils.extract(
                response.json(),
                "$.result.data.records[*].master_account",
                default=[],
                multi_match=True
            )

            if not master_account_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"喊单者账户查询：{trader_account}，返回 {len(master_account_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"{trader_account}查询结果",
                attachment_type="text/plain"
            )

            for idx, master_account in enumerate(master_account_list):
                self.verify_data(
                    actual_value=master_account,
                    expected_value=trader_account,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的喊单者账户符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的喊单者账户校验"
                )

    # @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("喊单者账户查询-查询结果为空")
    def test_query_master_accountNO(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "master_account": "9999999999999999",
                "pageNo": 1,
                "pageSize": 20,
                "status": "NORMAL,AUDIT"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                params=params
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

        with allure.step("3. 查询校验"):
            self.json_utils.assert_empty_list(
                data=response.json(),
                expression="$.result.data.records"
            )
            logging.info("查询结果符合预期：records为空列表")
            allure.attach("查询结果为空，符合预期", 'text/plain')

    # @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("喊单者昵称查询")
    def test_query_master_nickname(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            trader_master_nickname = var_manager.get_variable("trader_master_nickname")
            params = {
                "_t": current_timestamp_seconds,
                "master_nickname": trader_master_nickname,
                "pageNo": 1,
                "pageSize": 20,
                "status": "NORMAL,AUDIT"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                params=params
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

        with allure.step("3. 查询校验"):
            master_nickname_list = self.json_utils.extract(
                response.json(),
                "$.result.data.records[*].master_nickname",
                default=[],
                multi_match=True
            )

            if not master_nickname_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"喊单者昵称查询：{trader_master_nickname}，返回 {len(master_nickname_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"喊单者昵称-{trader_master_nickname}:查询结果",
                attachment_type="text/plain"
            )

            for idx, master_nickname in enumerate(master_nickname_list):
                self.verify_data(
                    actual_value=master_nickname,
                    expected_value=trader_master_nickname,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的喊单者昵称符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的喊单者昵称校验"
                )

    # @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("喊单者昵称查询-查询结果为空")
    def test_query_master_nicknameNO(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "master_nickname": "XXXXXXXXX",
                "pageNo": 1,
                "pageSize": 20,
                "status": "NORMAL,AUDIT"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                params=params
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

        with allure.step("3. 查询校验"):
            self.json_utils.assert_empty_list(
                data=response.json(),
                expression="$.result.data.records"
            )
            logging.info("查询结果符合预期：records为空列表")
            allure.attach("查询结果为空，符合预期", 'text/plain')

    # @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("跟单昵称查询")
    def test_query_nickname(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            follow_nickname = var_manager.get_variable("follow_nickname")
            params = {
                "_t": current_timestamp_seconds,
                "nickname": follow_nickname,
                "pageNo": 1,
                "pageSize": 20,
                "status": "NORMAL,AUDIT"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                params=params
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

        with allure.step("3. 查询校验"):
            nickname_list = self.json_utils.extract(
                response.json(),
                "$.result.data.records[*].nickname",
                default=[],
                multi_match=True
            )

            if not nickname_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"跟单昵称查询：{follow_nickname}，返回 {len(nickname_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"跟单昵称-{follow_nickname}:查询结果",
                attachment_type="text/plain"
            )

            for idx, nickname in enumerate(nickname_list):
                self.verify_data(
                    actual_value=nickname,
                    expected_value=follow_nickname,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的跟单昵称符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的跟单昵称校验"
                )

    # @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("跟单昵称查询-查询结果为空")
    def test_query_nicknameNO(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "nickname": "XXXXXXXXX",
                "pageNo": 1,
                "pageSize": 20,
                "status": "NORMAL,AUDIT"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                params=params
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

        with allure.step("3. 查询校验"):
            self.json_utils.assert_empty_list(
                data=response.json(),
                expression="$.result.data.records"
            )
            logging.info("查询结果符合预期：records为空列表")
            allure.attach("查询结果为空，符合预期", 'text/plain')

    # @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("喊单者服务器查询")
    def test_query_master_server(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            trader_master_server = var_manager.get_variable("trader_master_server")
            params = {
                "_t": current_timestamp_seconds,
                "master_server": trader_master_server,
                "pageNo": 1,
                "pageSize": 20,
                "status": "NORMAL,AUDIT"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                params=params
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

        with allure.step("3. 查询校验"):
            master_server_list = self.json_utils.extract(
                response.json(),
                "$.result.data.records[*].master_server",
                default=[],
                multi_match=True
            )

            if not master_server_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"喊单者服务器查询：{trader_master_server}，返回 {len(master_server_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"喊单者服务器-{trader_master_server}:查询结果",
                attachment_type="text/plain"
            )

            for idx, master_server in enumerate(master_server_list):
                self.verify_data(
                    actual_value=master_server,
                    expected_value=trader_master_server,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的喊单者服务器符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的喊单者服务器校验"
                )

    # @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("喊单者服务器查询-查询结果为空")
    def test_query_master_serverNO(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "master_server": "XXXXXXXXX",
                "pageNo": 1,
                "pageSize": 20,
                "status": "NORMAL,AUDIT"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                params=params
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

        with allure.step("3. 查询校验"):
            self.json_utils.assert_empty_list(
                data=response.json(),
                expression="$.result.data.records"
            )
            logging.info("查询结果符合预期：records为空列表")
            allure.attach("查询结果为空，符合预期", 'text/plain')

    # @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("跟单者服务器查询")
    def test_query_slave_server(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            follow_slave_server = var_manager.get_variable("follow_slave_server")
            params = {
                "_t": current_timestamp_seconds,
                "slave_server": follow_slave_server,
                "pageNo": 1,
                "pageSize": 20,
                "status": "NORMAL,AUDIT"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                params=params
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

        with allure.step("3. 查询校验"):
            slave_server_list = self.json_utils.extract(
                response.json(),
                "$.result.data.records[*].slave_server",
                default=[],
                multi_match=True
            )

            if not slave_server_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"跟单者服务器查询：{follow_slave_server}，返回 {len(slave_server_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"跟单者服务器-{follow_slave_server}:查询结果",
                attachment_type="text/plain"
            )

            for idx, slave_server in enumerate(slave_server_list):
                self.verify_data(
                    actual_value=slave_server,
                    expected_value=follow_slave_server,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的跟单者服务器符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的跟单者服务器校验"
                )

    # @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("跟单者服务器查询-查询结果为空")
    def test_query_slave_serverNO(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "slave_server": "XXXXXXXXX",
                "pageNo": 1,
                "pageSize": 20,
                "status": "NORMAL,AUDIT"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                params=params
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

        with allure.step("3. 查询校验"):
            self.json_utils.assert_empty_list(
                data=response.json(),
                expression="$.result.data.records"
            )
            logging.info("查询结果符合预期：records为空列表")
            allure.attach("查询结果为空，符合预期", 'text/plain')

    # @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("喊单者ID查询")
    def test_query_master_id(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            trader_pass_id = var_manager.get_variable("trader_pass_id")
            params = {
                "_t": current_timestamp_seconds,
                "master_id": trader_pass_id,
                "pageNo": 1,
                "pageSize": 20,
                "status": "NORMAL,AUDIT"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                params=params
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

        with allure.step("3. 查询校验"):
            master_id_list = self.json_utils.extract(
                response.json(),
                "$.result.data.records[*].master_id",
                default=[],
                multi_match=True
            )

            if not master_id_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"喊单者ID查询：{trader_pass_id}，返回 {len(master_id_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"喊单者ID-{trader_pass_id}:查询结果",
                attachment_type="text/plain"
            )

            for idx, master_id in enumerate(master_id_list):
                self.verify_data(
                    actual_value=master_id,
                    expected_value=trader_pass_id,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的喊单者ID符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的喊单者ID校验"
                )

    # @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("喊单者ID查询-查询结果为空")
    def test_query_master_idNO(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "master_id": "XXXXXXXXX",
                "pageNo": 1,
                "pageSize": 20,
                "status": "NORMAL,AUDIT"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                params=params
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

        with allure.step("3. 查询校验"):
            self.json_utils.assert_empty_list(
                data=response.json(),
                expression="$.result.data.records"
            )
            logging.info("查询结果符合预期：records为空列表")
            allure.attach("查询结果为空，符合预期", 'text/plain')

    # @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("跟单ID查询")
    def test_query_slave_id(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            follow_pass_id = var_manager.get_variable("follow_pass_id")
            params = {
                "_t": current_timestamp_seconds,
                "slave_id": follow_pass_id,
                "pageNo": 1,
                "pageSize": 20,
                "status": "NORMAL,AUDIT"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                params=params
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

        with allure.step("3. 查询校验"):
            slave_id_list = self.json_utils.extract(
                response.json(),
                "$.result.data.records[*].slave_id",
                default=[],
                multi_match=True
            )

            if not slave_id_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"跟单ID查询：{follow_pass_id}，返回 {len(slave_id_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"跟单ID-{follow_pass_id}:查询结果",
                attachment_type="text/plain"
            )

            for idx, slave_id in enumerate(slave_id_list):
                self.verify_data(
                    actual_value=slave_id,
                    expected_value=follow_pass_id,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的跟单ID符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的跟单ID校验"
                )

    # @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("跟单ID查询-查询结果为空")
    def test_query_slave_idNO(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "slave_id": "XXXXXXXXX",
                "pageNo": 1,
                "pageSize": 20,
                "status": "NORMAL,AUDIT"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                params=params
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

        with allure.step("3. 查询校验"):
            self.json_utils.assert_empty_list(
                data=response.json(),
                expression="$.result.data.records"
            )
            logging.info("查询结果符合预期：records为空列表")
            allure.attach("查询结果为空，符合预期", 'text/plain')

    # @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("跟单用户查询")
    def test_query_username(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            login_config = var_manager.get_variable("login_config")
            username_log = login_config["username"]
            params = {
                "_t": current_timestamp_seconds,
                "username": username_log,
                "pageNo": 1,
                "pageSize": 20,
                "status": "NORMAL,AUDIT"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                params=params
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

        with allure.step("3. 查询校验"):
            username_list = self.json_utils.extract(
                response.json(),
                "$.result.data.records[*].username",
                default=[],
                multi_match=True
            )

            if not username_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"跟单用户查询：{username_log}，返回 {len(username_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"跟单用户-{username_log}:查询结果",
                attachment_type="text/plain"
            )

            for idx, username in enumerate(username_list):
                self.verify_data(
                    actual_value=username,
                    expected_value=username_log,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的跟单用户符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的跟单用户校验"
                )

    # @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("跟单用户查询-查询结果为空")
    def test_query_usernameNO(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "username": "XXXXXXXXX",
                "pageNo": 1,
                "pageSize": 20,
                "status": "NORMAL,AUDIT"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                params=params
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

        with allure.step("3. 查询校验"):
            self.json_utils.assert_empty_list(
                data=response.json(),
                expression="$.result.data.records"
            )
            logging.info("查询结果符合预期：records为空列表")
            allure.attach("查询结果为空，符合预期", 'text/plain')

    # @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("截止日期-查询结果为空")
    def test_query_deadlineNO(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "deadline_begin": DATETIME_OLDTIME,
                "deadline_end": DATETIME_ENDTIME,
                "pageNo": 1,
                "pageSize": 20,
                "status": "NORMAL,AUDIT"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                params=params
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

        with allure.step("3. 查询校验"):
            self.json_utils.assert_empty_list(
                data=response.json(),
                expression="$.result.data.records"
            )
            logging.info("查询结果符合预期：records为空列表")
            allure.attach("查询结果为空，符合预期", 'text/plain')

    # @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("名称查询-查询结果为空")
    def test_query_nameNO(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "name": "XXXXXXXXX",
                "pageNo": 1,
                "pageSize": 20,
                "status": "NORMAL,AUDIT"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                params=params
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

        with allure.step("3. 查询校验"):
            self.json_utils.assert_empty_list(
                data=response.json(),
                expression="$.result.data.records"
            )
            logging.info("查询结果符合预期：records为空列表")
            allure.attach("查询结果为空，符合预期", 'text/plain')

    # @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("组合查询")
    def test_query_all(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            follow_account = var_manager.get_variable("follow_account")
            trader_account = var_manager.get_variable("trader_account")
            trader_master_nickname = var_manager.get_variable("trader_master_nickname")
            follow_nickname = var_manager.get_variable("follow_nickname")
            trader_master_server = var_manager.get_variable("trader_master_server")
            follow_slave_server = var_manager.get_variable("follow_slave_server")
            trader_pass_id = var_manager.get_variable("trader_pass_id")
            follow_pass_id = var_manager.get_variable("follow_pass_id")
            login_config = var_manager.get_variable("login_config")
            username_log = login_config["username"]
            params = {
                "_t": current_timestamp_seconds,
                "account": follow_account,
                "master_account": trader_account,
                "master_nickname": trader_master_nickname,
                "nickname": follow_nickname,
                "master_server": trader_master_server,
                "slave_server": follow_slave_server,
                "master_id": trader_pass_id,
                "slave_id": follow_pass_id,
                "username": username_log,
                "pause": 0,
                "pageNo": 1,
                "pageSize": 20,
                "status": "NORMAL,AUDIT"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgreport/api/getColumnsAndData/1560189381093109761',
                params=params
            )

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

        with allure.step("3. 查询校验"):
            account_list = self.json_utils.extract(
                response.json(),
                "$.result.data.records[*].account",
                default=[],
                multi_match=True
            )

            if not account_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"跟随者账户查询：{follow_account}，返回 {len(account_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"{follow_account}查询结果",
                attachment_type="text/plain"
            )

            for idx, account in enumerate(account_list):
                self.verify_data(
                    actual_value=account,
                    expected_value=follow_account,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的跟随者账户符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的跟随者账户校验"
                )
