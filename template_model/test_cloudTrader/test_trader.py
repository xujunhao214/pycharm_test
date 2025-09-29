import time
from template_model.commons.api_base import APITestBase, CompareOp
import allure
import logging
import json
import pytest
from template_model.VAR.VAR import *
from template_model.commons.jsonpath_utils import *
from template_model.commons.random_generator import *


@allure.feature("账号管理-交易员账户的查询校验")
class Test_trader_query(APITestBase):
    # 实例化JsonPath工具类（全局复用）
    json_utils = JsonPathUtils()

    @pytest.mark.skipif(reason="跳过此用例")
    @allure.title("绑定时间查询")
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
            create_time_list = self.json_utils.extract(
                response.json(),
                "$.result.records[*].recommenders_user_name",
                default=[],
                multi_match=True
            )

            if not create_time_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"绑定时间查询-开始时间：{ONE_HOUR_AGO}，返回 {len(create_time_list)} 条记录"

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
                    message=f"第 {idx + 1} 条记录的绑定时间符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的绑定时间校验"
                )

                self.verify_data(
                    actual_value=create_time,
                    expected_value=DATETIME_NOW,
                    op=CompareOp.LE,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的绑定时间符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的绑定时间校验"
                )

    # @pytest.mark.skipif(reason="跳过此用例")
    @allure.title("绑定时间查询-查询结果为空")
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
            self.json_utils.assert_empty_list(
                data=response.json(),
                expression="$.result.records"
            )
            logging.info("查询结果符合预期：records为空列表")
            allure.attach("查询结果为空，符合预期", 'text/plain')

    # @pytest.mark.skipif(reason="跳过此用例")
    @allure.title("用户查询")
    def test_query_usrid(self, var_manager, logged_session):
        trader_user_id = var_manager.get_variable("trader_user_id")
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "user_id": trader_user_id,
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "type": "MASTER_REAL",
                "status": "VERIFICATION,PASS,PENDING,ERROR"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/2c9a814a81d3a91b0181d3a91b250000',
                params=params
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
                attach_body = f"用户查询：{trader_user_id}，返回 {len(user_id_query_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"{trader_user_id}查询结果",
                attachment_type="text/plain"
            )
            for idx, user_id_query in enumerate(user_id_query_list):
                self.verify_data(
                    actual_value=user_id_query,
                    expected_value=trader_user_id,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message="查询结果符合预期",
                    attachment_name=f"查询结果,用户是：{update_by}"
                )

    # @pytest.mark.skipif(reason="跳过此用例")
    @allure.title("策略名称查询-存在结果")
    def test_query_policy_name(self, var_manager, logged_session):
        valid_strategy_name = var_manager.get_variable("valid_strategy_name")
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "policy_name": valid_strategy_name,
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "type": "MASTER_REAL",
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
            policy_name_query = self.json_utils.extract(response.json(), "$.result.records[0].policy_name")

            self.verify_data(
                actual_value=policy_name_query,
                expected_value=valid_strategy_name,
                op=CompareOp.EQ,
                use_isclose=False,
                message="查询结果符合预期",
                attachment_name=f"查询结果"
            )

    # @pytest.mark.skipif(reason="跳过此用例")
    @allure.title("策略名称查询-查询结果为空")
    def test_query_policy_noname(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "policy_name": "xxxxxxxxxx",
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "type": "MASTER_REAL",
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
            self.json_utils.assert_empty_list(
                data=response.json(),
                expression="$.result.records"
            )
            logging.info("查询结果符合预期：records为空列表")
            allure.attach("查询结果为空，符合预期", 'text/plain')

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
            name=f"{status_desc}状态说明",
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
                attach_body = f"状态查询[{status_desc}]：返回的records为空列表（暂无数据）"
            else:
                attach_body = f"状态查询[{status_desc}]，返回 {len(status_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"{status_desc}状态查询结果",
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
                    attachment_name=f"{status_desc}状态第 {idx + 1} 条记录校验"
                )

    # @pytest.mark.skipif(reason="跳过此用例")
    @allure.title("MT4账号查询-存在结果")
    def test_query_MT4account(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            trader_account = var_manager.get_variable("trader_account")
            params = {
                "_t": current_timestamp_seconds,
                "account": trader_account,
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
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
            account = self.json_utils.extract(response.json(), "$.result.records[0].account")

            self.verify_data(
                actual_value=account,
                expected_value=trader_account,
                op=CompareOp.EQ,
                use_isclose=False,
                message="查询结果符合预期",
                attachment_name=f"查询结果,MT4账号是：{account}"
            )

    # @pytest.mark.skipif(reason="跳过此用例")
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
            self.json_utils.assert_empty_list(
                data=response.json(),
                expression="$.result.records"
            )
            logging.info("查询结果符合预期：records为空列表")
            allure.attach("查询结果为空，符合预期", 'text/plain')

    # @pytest.mark.skipif(reason="跳过此用例")
    @allure.title("经纪商查询")
    def test_query_broker_id(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            trader_broker_id = var_manager.get_variable("trader_broker_id")
            params = {
                "_t": current_timestamp_seconds,
                "broker_id": trader_broker_id,
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
            broker_id_list = self.json_utils.extract(
                response.json(),
                "$.result.records[*].broker_id",
                default=[],
                multi_match=True
            )

            if not broker_id_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"经纪商查询：{trader_broker_id}，返回 {len(broker_id_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"{trader_broker_id}查询结果",
                attachment_type="text/plain"
            )

            for idx, broker_id in enumerate(broker_id_list):
                self.verify_data(
                    actual_value=broker_id,
                    expected_value=trader_broker_id,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的broker_id符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的broker_id校验"
                )

    # @pytest.mark.skipif(reason="跳过此用例")
    @allure.title("服务器查询")
    def test_query_server_id(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            trader_server_id = var_manager.get_variable("trader_server_id")
            params = {
                "_t": current_timestamp_seconds,
                "server_id": trader_server_id,
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
            server_id_list = self.json_utils.extract(
                response.json(),
                "$.result.records[*].server_id",
                default=[],
                multi_match=True
            )

            if not server_id_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"服务器：查询{trader_server_id}，返回 {len(server_id_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"{trader_server_id}查询结果",
                attachment_type="text/plain"
            )

            for idx, server_id in enumerate(server_id_list):
                self.verify_data(
                    actual_value=server_id,
                    expected_value=trader_server_id,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的server_id符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的server_id校验"
                )

    # @pytest.mark.skipif(reason="跳过此用例")
    @allure.title("虚拟服务商查询")
    def test_query_virtual_server_name(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            virtual_server_name = var_manager.get_variable("virtual_server_name")
            params = {
                "_t": current_timestamp_seconds,
                "virtual_server_name": virtual_server_name,
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
            virtual_server_name_list = self.json_utils.extract(
                response.json(),
                "$.result.records[*].virtual_server_name",
                default=[],
                multi_match=True
            )

            if not virtual_server_name_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"虚拟服务商查询：{virtual_server_name}，返回 {len(virtual_server_name_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"虚拟服务商查询结果",
                attachment_type="text/plain"
            )

            for idx, virtual_server_name in enumerate(virtual_server_name_list):
                self.verify_data(
                    actual_value=virtual_server_name,
                    expected_value="CPT Markets",
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message="查询结果符合预期",
                    attachment_name=f"查询结果"
                )

    # @pytest.mark.skipif(reason="跳过此用例")
    @allure.title("订阅类型查询-手数-查询结果为空")
    def test_query_subscribe_fee_idsize(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "subscribe_fee_id": "size",
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
            self.json_utils.assert_empty_list(
                data=response.json(),
                expression="$.result.records"
            )
            logging.info("查询结果符合预期：records为空列表")
            allure.attach("查询结果为空，符合预期", 'text/plain')

    # @pytest.mark.skipif(reason="跳过此用例")
    @allure.title("订阅类型查询-月-查询结果为空")
    def test_query_subscribe_fee_idmonth(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "subscribe_fee_id": "month",
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
            self.json_utils.assert_empty_list(
                data=response.json(),
                expression="$.result.records"
            )
            logging.info("查询结果符合预期：records为空列表")
            allure.attach("查询结果为空，符合预期", 'text/plain')

    # @pytest.mark.skipif(reason="跳过此用例")
    @allure.title("订阅费查询")
    def test_query_subscribe_fee(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "subscribe_fee": 0,
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
            subscribe_fee_list = self.json_utils.extract(
                response.json(),
                "$.result.records[*].subscribe_fee",
                default=[],
                multi_match=True
            )

            if not subscribe_fee_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"订阅费查询：0，返回 {len(subscribe_fee_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"订阅费查询结果",
                attachment_type="text/plain"
            )

            for idx, subscribe_fee in enumerate(subscribe_fee_list):
                self.verify_data(
                    actual_value=subscribe_fee,
                    expected_value=0,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的订阅费符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的订阅费校验"
                )

    # @pytest.mark.skipif(reason="跳过此用例")
    @allure.title("订阅费查询-查询结果为空")
    def test_query_subscribe_feeno(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "subscribe_fee": 100,
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
            self.json_utils.assert_empty_list(
                data=response.json(),
                expression="$.result.records"
            )
            logging.info("查询结果符合预期：records为空列表")
            allure.attach("查询结果为空，符合预期", 'text/plain')

    # @pytest.mark.skipif(reason="跳过此用例")
    @allure.title("等级查询")
    def test_query_level_id(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "level_id": 3,
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
            level_id_list = self.json_utils.extract(
                response.json(),
                "$.result.records[*].level_id",
                default=[],
                multi_match=True
            )

            if not level_id_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"等级查询：3，返回 {len(level_id_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"等级为3查询结果",
                attachment_type="text/plain"
            )

            for idx, level_id in enumerate(level_id_list):
                self.verify_data(
                    actual_value=float(level_id),
                    expected_value=float(3),
                    op=CompareOp.EQ,
                    message=f"第 {idx + 1} 条记录的等级符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的等级校验"
                )

    # @pytest.mark.skipif(reason="跳过此用例")
    @allure.title("等级查询-查询结果为空")
    def test_query_level_idno(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "level_id": 10,
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
            self.json_utils.assert_empty_list(
                data=response.json(),
                expression="$.result.records"
            )
            logging.info("查询结果符合预期：records为空列表")
            allure.attach("查询结果为空，符合预期", 'text/plain')

    # @pytest.mark.skipif(reason="跳过此用例")
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

    # @pytest.mark.skipif(reason="跳过此用例")
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

    @pytest.mark.skipif(reason="跳过此用例")
    @allure.title("推荐人ID查询")
    def test_query_recommenders(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            trader_user_id = var_manager.get_variable("trader_user_id")
            params = {
                "_t": current_timestamp_seconds,
                "recommenders_user_id": trader_user_id,
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
            recommenders_user_id_list = self.json_utils.extract(
                response.json(),
                "$.result.records[*].recommenders_user_id",
                default=[],
                multi_match=True
            )

            if not recommenders_user_id_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"推荐人ID查询：{trader_user_id}，返回 {len(recommenders_user_id_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"{trader_user_id}查询结果",
                attachment_type="text/plain"
            )

            for idx, recommenders_user_id in enumerate(recommenders_user_id_list):
                self.verify_data(
                    actual_value=trader_user_id,
                    expected_value=recommenders_user_id,
                    op=CompareOp.IN,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的推荐人ID符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的推荐人ID校验"
                )

    # @pytest.mark.skipif(reason="跳过此用例")
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
            self.json_utils.assert_empty_list(
                data=response.json(),
                expression="$.result.records"
            )
            logging.info("查询结果符合预期：records为空列表")
            allure.attach("查询结果为空，符合预期", 'text/plain')

    @pytest.mark.skipif(reason="跳过此用例")
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

    # @pytest.mark.skipif(reason="跳过此用例")
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
            self.json_utils.assert_empty_list(
                data=response.json(),
                expression="$.result.records"
            )
            logging.info("查询结果符合预期：records为空列表")
            allure.attach("查询结果为空，符合预期", 'text/plain')

    # @pytest.mark.skipif(reason="跳过此用例")
    @allure.title("组合查询")
    def test_query_combination(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            trader_user_id = var_manager.get_variable("trader_user_id")
            valid_strategy_name = var_manager.get_variable("valid_strategy_name")
            trader_account = var_manager.get_variable("trader_account")
            trader_broker_id = var_manager.get_variable("trader_broker_id")
            trader_server_id = var_manager.get_variable("trader_server_id")
            params = {
                "_t": current_timestamp_seconds,
                "user_id": trader_user_id,
                "policy_name": valid_strategy_name,
                "status": "PASS",
                "account": trader_account,
                "broker_id": trader_broker_id,
                "server_id": trader_server_id,
                "subscribe_fee": 0,
                # "level_id": 3,
                "connected": 1,
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
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
            recommenders_user_id_list = self.json_utils.extract(
                response.json(),
                "$.result.records[*].recommenders_user_id",
                default=[],
                multi_match=True
            )

            if not recommenders_user_id_list:
                pytest.fail("查询结果为空，不符合预期")

            for idx, recommenders_user_id in enumerate(recommenders_user_id_list):
                self.verify_data(
                    actual_value=trader_user_id,
                    expected_value=recommenders_user_id,
                    op=CompareOp.IN,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的推荐人ID符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的推荐人ID校验"
                )

    # @pytest.mark.skipif(reason="跳过此用例")
    @allure.title("高级查询-策略名称查询")
    def test_query_superQueryParams_val(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            # 1. 先构造 superQueryParams 的原始 JSON 数组（字典转 JSON 字符串）
            super_query_params = [
                {
                    "rule": "like",  # 模糊匹配（包含）
                    "type": "text",  # 字段类型为文本
                    "val": "xjh",  # 匹配值（包含“xjh”）
                    "field": "policy_name"  # 匹配的字段名（策略名称）
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
                "type": "MASTER_REAL",
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
            policy_name_list = self.json_utils.extract(
                response.json(),
                "$.result.records[*].policy_name",
                default=[],
                multi_match=True
            )

            if not policy_name_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"高级查询-策略名称查询：xjh，返回 {len(policy_name_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"{ONE_HOUR_AGO}查询结果",
                attachment_type="text/plain"
            )

            for idx, policy_name in enumerate(policy_name_list):
                # 直接判断 "xjh" 是否在 policy_name 中
                if "xjh" not in policy_name:
                    # 校验失败时手动报错
                    pytest.fail(
                        f"第 {idx + 1} 条记录的策略名称不符合预期：\n"
                        f"实际值：{policy_name}\n"
                        f"预期：包含 'xjh'"
                    )
                # 校验通过时添加附件
                allure.attach(
                    f"第 {idx + 1} 条记录的策略名称（{policy_name}）包含'xjh'",
                    name=f"第 {idx + 1} 条记录校验通过",
                    attachment_type="text/plain"
                )
