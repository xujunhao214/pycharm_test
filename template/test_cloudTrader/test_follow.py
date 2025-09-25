import time
from template.commons.api_base import APITestBase, CompareOp
import allure
import logging
import json
import pytest
from template.VAR.VAR import *
from template.commons.jsonpath_utils import *
from template.commons.random_generator import *


@allure.feature("账号管理-跟随者账户的查询校验")
class Test_follow_query(APITestBase):
    # 实例化JsonPath工具类（全局复用）
    json_utils = JsonPathUtils()

    @pytest.mark.skipif(True, reason="该用例暂时跳过")
    @allure.title("绑定日期查询")
    def test_query_create_time(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "create_time_begin": ONE_HOUR_AGO,
                "create_time_end": DATETIME_NOW,
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "status": "VERIFICATION,PASS,PENDING,ERROR",
                "type": "SLAVE_REAL"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/2c9a814a81d3a91b0181e04a36e00001',
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
                "$.result.records[*].create_time",
                default=[],
                multi_match=True
            )

            if not create_time_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"绑定日期查询-开始时间：{ONE_HOUR_AGO}，返回 {len(create_time_list)} 条记录"

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
                    message=f"第 {idx + 1} 条记录的绑定日期符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的绑定日期校验"
                )

                self.verify_data(
                    actual_value=create_time,
                    expected_value=DATETIME_NOW,
                    op=CompareOp.LE,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的绑定日期符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的绑定日期校验"
                )

    # @pytest.mark.skipif(True, reason="该用例暂时跳过")
    @allure.title("绑定日期查询-查询结果为空")
    def test_query_create_timeno(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "create_time_begin": DATETIME_NOW,
                "create_time_end": ONE_HOUR_AGO,
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "status": "VERIFICATION,PASS,PENDING,ERROR",
                "type": "SLAVE_REAL"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/2c9a814a81d3a91b0181e04a36e00001',
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
                expression="$.result.records"
            )
            logging.info("查询结果符合预期：records为空列表")
            allure.attach("查询结果为空，符合预期", 'text/plain')

    # @pytest.mark.skipif(True, reason="该用例暂时跳过")
    @allure.title("用户查询")
    def test_query_usrid(self, var_manager, logged_session):
        follow_user_id = var_manager.get_variable("follow_user_id")
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "user_id": follow_user_id,
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "type": "SLAVE_REAL",
                "status": "VERIFICATION,PASS,PENDING,ERROR"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/2c9a814a81d3a91b0181e04a36e00001',
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
            update_by = self.json_utils.extract(response.json(), "$.result.records[0].update_by")

            user_id_query_list = self.json_utils.extract(
                response.json(),
                "$.result.records[*].user_id",
                default=[],
                multi_match=True
            )

            if not user_id_query_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"用户查询：{follow_user_id}，返回 {len(user_id_query_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"{follow_user_id}查询结果",
                attachment_type="text/plain"
            )
            for idx, user_id_query in enumerate(user_id_query_list):
                self.verify_data(
                    actual_value=user_id_query,
                    expected_value=follow_user_id,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message="查询结果符合预期",
                    attachment_name=f"查询结果,用户是：{update_by}"
                )

    # 定义所有需要测试的状态（作为参数化数据源）
    STATUS_PARAMS = [
        ("VERIFICATION", "连接中"),
        ("PASS", "已连接"),
        ("ERROR", "密码错误"),
        ("PENDING", "审核中"),
        ("UNBIND", "已解绑"),
        ("REFUSE", "已拒绝")
    ]

    # 使用parametrize参数化：每个状态生成一个独立用例
    @pytest.mark.parametrize("status, status_desc", STATUS_PARAMS)
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
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "type": "SLAVE_REAL"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/2c9a814a81d3a91b0181e04a36e00001',
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
                "$.result.records[*].status",
                default=[],
                multi_match=True
            )

            # 生成查询结果附件
            if not status_list:
                attach_body = f"状态查询-{status_desc}：返回的records为空列表（暂无数据）"
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

    # @pytest.mark.skipif(True, reason="该用例暂时跳过")
    @allure.title("MT4账号查询-存在结果")
    def test_query_MT4account(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            follow_account = var_manager.get_variable("follow_account")
            params = {
                "_t": current_timestamp_seconds,
                "account": follow_account,
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "type": "SLAVE_REAL"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/2c9a814a81d3a91b0181e04a36e00001',
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
            account = self.json_utils.extract(response.json(), "$.result.records[0].account")

            self.verify_data(
                actual_value=account,
                expected_value=follow_account,
                op=CompareOp.EQ,
                use_isclose=False,
                message="查询结果符合预期",
                attachment_name=f"查询结果,MT4账号是：{account}"
            )

    # @pytest.mark.skipif(True, reason="该用例暂时跳过")
    @allure.title("MT4账号查询-查询结果为空")
    def test_query_MT4accountNO(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "account": "123456789",
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "type": "SLAVE_REAL"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/2c9a814a81d3a91b0181e04a36e00001',
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
                expression="$.result.records"
            )
            logging.info("查询结果符合预期：records为空列表")
            allure.attach("查询结果为空，符合预期", 'text/plain')

    # @pytest.mark.skipif(True, reason="该用例暂时跳过")
    @allure.title("经纪商查询")
    def test_query_broker_id(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            follow_broker_id = var_manager.get_variable("follow_broker_id")
            params = {
                "_t": current_timestamp_seconds,
                "broker_id": follow_broker_id,
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "status": "VERIFICATION,PASS,PENDING,ERROR",
                "type": "SLAVE_REAL"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/2c9a814a81d3a91b0181e04a36e00001',
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
            broker_id_list = self.json_utils.extract(
                response.json(),
                "$.result.records[*].broker_id",
                default=[],
                multi_match=True
            )

            if not broker_id_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"经纪商查询：{follow_broker_id}，返回 {len(broker_id_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"{follow_broker_id}查询结果",
                attachment_type="text/plain"
            )

            for idx, broker_id in enumerate(broker_id_list):
                self.verify_data(
                    actual_value=broker_id,
                    expected_value=follow_broker_id,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的broker_id符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的broker_id校验"
                )

    # @pytest.mark.skipif(True, reason="该用例暂时跳过")
    @allure.title("服务器查询")
    def test_query_server_id(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            follow_server_id = var_manager.get_variable("follow_server_id")
            params = {
                "_t": current_timestamp_seconds,
                "server_id": follow_server_id,
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "status": "VERIFICATION,PASS,PENDING,ERROR",
                "type": "SLAVE_REAL"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/2c9a814a81d3a91b0181e04a36e00001',
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
            server_id_list = self.json_utils.extract(
                response.json(),
                "$.result.records[*].server_id",
                default=[],
                multi_match=True
            )

            if not server_id_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"服务器：查询{follow_server_id}，返回 {len(server_id_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"{follow_server_id}查询结果",
                attachment_type="text/plain"
            )

            for idx, server_id in enumerate(server_id_list):
                self.verify_data(
                    actual_value=server_id,
                    expected_value=follow_server_id,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的server_id符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的server_id校验"
                )

    # @pytest.mark.skipif(True, reason="该用例暂时跳过")
    @allure.title("是否连接查询-是")
    def test_query_connected(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "connected": 1,
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "status": "VERIFICATION,PASS,PENDING,ERROR",
                "type": "MASTER_REAL"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/2c9a814a81d3a91b0181d3a91b250000',
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
            connected_list = self.json_utils.extract(
                response.json(),
                "$.result.records[*].connected",
                default=[],
                multi_match=True
            )

            if not connected_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"是否连接查询-是，返回 {len(connected_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"是否连接查询-是，查询结果",
                attachment_type="text/plain"
            )

            for idx, connected in enumerate(connected_list):
                self.verify_data(
                    actual_value=float(connected),
                    expected_value=float(1),
                    op=CompareOp.EQ,
                    message=f"第 {idx + 1} 条记录的连接符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的连接校验"
                )

    # @pytest.mark.skipif(True, reason="该用例暂时跳过")
    @allure.title("是否连接查询-否")
    def test_query_connectednot(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "connected": 0,
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "status": "VERIFICATION,PASS,PENDING,ERROR",
                "type": "SLAVE_REAL"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/2c9a814a81d3a91b0181e04a36e00001',
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
            connected_list = self.json_utils.extract(
                response.json(),
                "$.result.records[*].connected",
                default=[],
                multi_match=True
            )

            if not connected_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"是否连接查询-否，返回 {len(connected_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"是否连接查询-否，查询结果",
                attachment_type="text/plain"
            )

            for idx, connected in enumerate(connected_list):
                self.verify_data(
                    actual_value=float(connected),
                    expected_value=float(0),
                    op=CompareOp.EQ,
                    message=f"第 {idx + 1} 条记录的连接符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的连接校验"
                )

    # @pytest.mark.skipif(True, reason="该用例暂时跳过")
    @allure.title("封闭状态查询-是")
    def test_query_blocked_password(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "blocked_password": 1,
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "status": "VERIFICATION,PASS,PENDING,ERROR",
                "type": "SLAVE_REAL"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/2c9a814a81d3a91b0181e04a36e00001',
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
            blocked_password_list = self.json_utils.extract(
                response.json(),
                "$.result.records[*].blocked_password",
                default=[],
                multi_match=True
            )

            if not blocked_password_list:
                attach_body = f"封闭状态查询-是，返回的blocked_password列表为空（暂无数据）"
            else:
                attach_body = f"封闭状态查询-是，返回 {len(blocked_password_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"封闭状态查询-是，查询结果",
                attachment_type="text/plain"
            )

            for idx, blocked_password in enumerate(blocked_password_list):
                self.verify_data(
                    actual_value=float(blocked_password),
                    expected_value=float(0),
                    op=CompareOp.EQ,
                    message=f"第 {idx + 1} 条记录的连接符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的连接校验"
                )

    # @pytest.mark.skipif(True, reason="该用例暂时跳过")
    @allure.title("封闭状态查询-否")
    def test_query_blocked_passwordno(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "blocked_password": 0,
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "status": "VERIFICATION,PASS,PENDING,ERROR",
                "type": "SLAVE_REAL"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/2c9a814a81d3a91b0181e04a36e00001',
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
            blocked_password_list = self.json_utils.extract(
                response.json(),
                "$.result.records[*].blocked_password",
                default=[],
                multi_match=True
            )

            if not blocked_password_list:
                attach_body = f"封闭状态查询-否，返回的blocked_password列表为空（暂无数据）"
            else:
                attach_body = f"封闭状态查询-否，返回 {len(blocked_password_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"封闭状态查询-否，查询结果",
                attachment_type="text/plain"
            )

            for idx, blocked_password in enumerate(blocked_password_list):
                self.verify_data(
                    actual_value=float(blocked_password),
                    expected_value=float(0),
                    op=CompareOp.EQ,
                    message=f"第 {idx + 1} 条记录的连接符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的连接校验"
                )

    # @pytest.mark.skipif(True, reason="该用例暂时跳过")
    @allure.title("封闭状态说明查询")
    def test_query_blocked_password_extra(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "blocked_password_extra": "已解封",
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "status": "VERIFICATION,PASS,PENDING,ERROR",
                "type": "SLAVE_REAL"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/2c9a814a81d3a91b0181e04a36e00001',
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
            blocked_password_extra_list = self.json_utils.extract(
                response.json(),
                "$.result.records[*].blocked_password_extra",
                default=[],
                multi_match=True
            )

            if not blocked_password_extra_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"封闭状态说明-已解封，返回 {len(blocked_password_extra_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"封闭状态说明-已解封，查询结果",
                attachment_type="text/plain"
            )

            for idx, blocked_password_extra in enumerate(blocked_password_extra_list):
                self.verify_data(
                    actual_value=blocked_password_extra,
                    expected_value="已解封",
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的连接符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的连接校验"
                )

    # @pytest.mark.skipif(True, reason="该用例暂时跳过")
    @allure.title("封闭状态说明-查询结果为空")
    def test_query_blocked_password_extrano(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "blocked_password_extra": "账号异常",
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "status": "VERIFICATION,PASS,PENDING,ERROR",
                "type": "SLAVE_REAL"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/2c9a814a81d3a91b0181e04a36e00001',
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
                expression="$.result.records"
            )
            logging.info("查询结果符合预期：records为空列表")
            allure.attach("查询结果为空，符合预期", 'text/plain')

    @pytest.mark.skipif(True, reason="该用例暂时跳过")
    @allure.title("推荐人ID查询")
    def test_query_recommenders(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            follow_user_id = var_manager.get_variable("follow_user_id")
            params = {
                "_t": current_timestamp_seconds,
                "recommenders_user_id": follow_user_id,
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "status": "VERIFICATION,PASS,PENDING,ERROR",
                "type": "SLAVE_REAL"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/2c9a814a81d3a91b0181e04a36e00001',
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
            recommenders_user_id_list = self.json_utils.extract(
                response.json(),
                "$.result.records[*].recommenders_user_id",
                default=[],
                multi_match=True
            )

            if not recommenders_user_id_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"推荐人ID查询：{follow_user_id}，返回 {len(recommenders_user_id_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"{follow_user_id}查询结果",
                attachment_type="text/plain"
            )

            for idx, recommenders_user_id in enumerate(recommenders_user_id_list):
                self.verify_data(
                    actual_value=follow_user_id,
                    expected_value=recommenders_user_id,
                    op=CompareOp.IN,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的推荐人ID符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的推荐人ID校验"
                )

    # @pytest.mark.skipif(True, reason="该用例暂时跳过")
    @allure.title("推荐人ID查询-查询结果为空")
    def test_query_recommendersno(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "recommenders_user_id": "111111111111111",
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "status": "VERIFICATION,PASS,PENDING,ERROR",
                "type": "SLAVE_REAL"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/2c9a814a81d3a91b0181e04a36e00001',
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
                expression="$.result.records"
            )
            logging.info("查询结果符合预期：records为空列表")
            allure.attach("查询结果为空，符合预期", 'text/plain')

    @pytest.mark.skipif(True, reason="该用例暂时跳过")
    @allure.title("推荐人名字查询")
    def test_query_recommenders_name(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            login_config = var_manager.get_variable("login_config")
            recommenders_user_name = login_config.get("username")
            params = {
                "_t": current_timestamp_seconds,
                "recommenders_user_name": recommenders_user_name,
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "status": "VERIFICATION,PASS,PENDING,ERROR",
                "type": "SLAVE_REAL"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/2c9a814a81d3a91b0181e04a36e00001',
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
            recommenders_user_name_list = self.json_utils.extract(
                response.json(),
                "$.result.records[*].recommenders_user_name",
                default=[],
                multi_match=True
            )

            if not recommenders_user_name_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"推荐人名字查询：{recommenders_user_name}，返回 {len(recommenders_user_name_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"{recommenders_user_name}查询结果",
                attachment_type="text/plain"
            )

            for idx, recommenders_user_name in enumerate(recommenders_user_name_list):
                self.verify_data(
                    actual_value="xujunhao@163.com",
                    expected_value=recommenders_user_name,
                    op=CompareOp.IN,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的推荐人名字符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的推荐人名字校验"
                )

    # @pytest.mark.skipif(True, reason="该用例暂时跳过")
    @allure.title("推荐人名字查询-查询结果为空")
    def test_query_recommenders_nameno(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "recommenders_user_name": "xujunhao99999@163.com",
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "status": "VERIFICATION,PASS,PENDING,ERROR",
                "type": "SLAVE_REAL"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/2c9a814a81d3a91b0181e04a36e00001',
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
                expression="$.result.records"
            )
            logging.info("查询结果符合预期：records为空列表")
            allure.attach("查询结果为空，符合预期", 'text/plain')

    # @pytest.mark.skipif(True, reason="该用例暂时跳过")
    @allure.title("组合查询")
    def test_query_combination(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            follow_user_id = var_manager.get_variable("follow_user_id")
            follow_account = var_manager.get_variable("follow_account")
            follow_broker_id = var_manager.get_variable("follow_broker_id")
            follow_server_id = var_manager.get_variable("follow_server_id")
            params = {
                "_t": current_timestamp_seconds,
                "user_id": follow_user_id,
                "status": "PASS",
                "account": follow_account,
                "broker_id": follow_broker_id,
                "server_id": follow_server_id,
                "subscribe_fee": 0,
                # "level_id": 3,
                "connected": 1,
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "type": "SLAVE_REAL"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/2c9a814a81d3a91b0181e04a36e00001',
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
            recommenders_user_id_list = self.json_utils.extract(
                response.json(),
                "$.result.records[*].recommenders_user_id",
                default=[],
                multi_match=True
            )

            if not recommenders_user_id_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"推荐人ID查询：{follow_user_id}，返回 {len(recommenders_user_id_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"{follow_user_id}查询结果",
                attachment_type="text/plain"
            )

            for idx, recommenders_user_id in enumerate(recommenders_user_id_list):
                self.verify_data(
                    actual_value=follow_user_id,
                    expected_value=recommenders_user_id,
                    op=CompareOp.IN,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的推荐人ID符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的推荐人ID校验"
                )

    # @pytest.mark.skipif(True, reason="该用例暂时跳过")
    @allure.title("高级查询-用户查询")
    def test_query_superQueryParams_val(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            # 1. 先构造 superQueryParams 的原始 JSON 数组（字典转 JSON 字符串）
            follow_user_id = var_manager.get_variable("follow_user_id")
            super_query_params = [
                {
                    "rule": "like",
                    "type": "sel_search",
                    "dictCode": "id",
                    "dictTable": "sys_user where username != 'anonymous'",
                    "dictText": "username",
                    "val": follow_user_id,
                    "field": "user_id"
                }
            ]
            # 将 Python 列表转为 JSON 字符串（确保后端能识别为 JSON 格式）
            super_query_json = json.dumps(super_query_params)

            params = {
                "_t": current_timestamp_seconds,
                "column": "id",
                "order": "desc",
                "pageNo": "1",
                "pageSize": "50",
                "superQueryMatchType": "and",
                "superQueryParams": super_query_json,
                "type": "SLAVE_REAL",
                "status": "VERIFICATION,PASS,PENDING,ERROR"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/2c9a814a81d3a91b0181d3a91b250000',
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
            update_by = self.json_utils.extract(response.json(), "$.result.records[0].update_by")

            user_id_query_list = self.json_utils.extract(
                response.json(),
                "$.result.records[*].user_id",
                default=[],
                multi_match=True
            )

            if not user_id_query_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"用户查询：{follow_user_id}，返回 {len(user_id_query_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"{follow_user_id}查询结果",
                attachment_type="text/plain"
            )
            for idx, user_id_query in enumerate(user_id_query_list):
                self.verify_data(
                    actual_value=user_id_query,
                    expected_value=follow_user_id,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message="查询结果符合预期",
                    attachment_name=f"查询结果,用户是：{update_by}"
                )
