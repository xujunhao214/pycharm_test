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
    @allure.story("交易员账号")
    class Test_trader(APITestBase):
        # 实例化JsonPath工具类（全局复用）
        json_utils = JsonPathUtils()

        @pytest.mark.skipif(True, reason="该用例暂时跳过")
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

        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
        @allure.title("绑定时间查询-不存在结果")
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

        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
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

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step("3. 查询校验"):
                user_id_query = self.json_utils.extract(response.json(), "$.result.records[0].user_id")
                update_by = self.json_utils.extract(response.json(), "$.result.records[0].update_by")

                self.verify_data(
                    actual_value=user_id_query,
                    expected_value=trader_user_id,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message="查询结果符合预期",
                    attachment_name=f"查询结果,用户是：{update_by}"
                )

        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
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

        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
        @allure.title("策略名称查询-不存在结果")
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

        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
        @allure.title("状态查询")
        def test_query_status(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                params = {
                    "_t": current_timestamp_seconds,
                    "status": "PASS",
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
                status_list = self.json_utils.extract(
                    response.json(),
                    "$.result.records[*].status",
                    default=[],  # 若未找到，默认返回空列表
                    multi_match=True  # 强制返回列表（即使只有一个结果）
                )

                for idx, status in enumerate(status_list):
                    self.verify_data(
                        actual_value=status,
                        expected_value="PASS",
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的status符合预期",
                        attachment_name=f"第 {idx + 1} 条记录的status校验"
                    )

        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
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

        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
        @allure.title("MT4账号查询-不存在结果")
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

        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
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

                for idx, broker_id in enumerate(broker_id_list):
                    self.verify_data(
                        actual_value=broker_id,
                        expected_value=trader_broker_id,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的broker_id符合预期",
                        attachment_name=f"第 {idx + 1} 条记录的broker_id校验"
                    )

        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
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

                for idx, server_id in enumerate(server_id_list):
                    self.verify_data(
                        actual_value=server_id,
                        expected_value=trader_server_id,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的server_id符合预期",
                        attachment_name=f"第 {idx + 1} 条记录的server_id校验"
                    )

        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
        @allure.title("虚拟服务商查询")
        def test_query_virtual_server_name(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                params = {
                    "_t": current_timestamp_seconds,
                    "virtual_server_name": "CPT Markets",
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
                virtual_server_name = self.json_utils.extract(response.json(),
                                                              "$.result.records[0].virtual_server_name")

                self.verify_data(
                    actual_value=virtual_server_name,
                    expected_value="CPT Markets",
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message="查询结果符合预期",
                    attachment_name=f"查询结果"
                )

        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
        @allure.title("订阅类型查询-手数-不存在结果")
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

        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
        @allure.title("订阅类型查询-月-不存在结果")
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

        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
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

                for idx, subscribe_fee in enumerate(subscribe_fee_list):
                    self.verify_data(
                        actual_value=subscribe_fee,
                        expected_value=0,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的订阅费符合预期",
                        attachment_name=f"第 {idx + 1} 条记录的订阅费校验"
                    )

        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
        @allure.title("订阅费查询-不存在结果")
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

        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
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

                for idx, level_id in enumerate(level_id_list):
                    self.verify_data(
                        actual_value=float(level_id),
                        expected_value=float(3),
                        op=CompareOp.EQ,
                        message=f"第 {idx + 1} 条记录的等级符合预期",
                        attachment_name=f"第 {idx + 1} 条记录的等级校验"
                    )

        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
        @allure.title("等级查询-不存在结果")
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

                for idx, connected in enumerate(connected_list):
                    self.verify_data(
                        actual_value=float(connected),
                        expected_value=float(0),
                        op=CompareOp.EQ,
                        message=f"第 {idx + 1} 条记录的连接符合预期",
                        attachment_name=f"第 {idx + 1} 条记录的连接校验"
                    )

        @pytest.mark.skipif(True, reason="该用例暂时跳过")
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

                for idx, recommenders_user_id in enumerate(recommenders_user_id_list):
                    self.verify_data(
                        actual_value=trader_user_id,
                        expected_value=recommenders_user_id,
                        op=CompareOp.IN,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的推荐人ID符合预期",
                        attachment_name=f"第 {idx + 1} 条记录的推荐人ID校验"
                    )

        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
        @allure.title("推荐人ID查询-不存在结果")
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

        @pytest.mark.skipif(True, reason="该用例暂时跳过")
        @allure.title("推荐人名字查询")
        def test_query_recommenders_name(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                params = {
                    "_t": current_timestamp_seconds,
                    "recommenders_user_name": "xujunhao@163.com",
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
        @allure.title("推荐人名字查询-不存在结果")
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

        # @pytest.mark.skipif(True, reason="该用例暂时跳过")
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
                    "level_id": 3,
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

                for idx, recommenders_user_id in enumerate(recommenders_user_id_list):
                    self.verify_data(
                        actual_value=trader_user_id,
                        expected_value=recommenders_user_id,
                        op=CompareOp.IN,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的推荐人ID符合预期",
                        attachment_name=f"第 {idx + 1} 条记录的推荐人ID校验"
                    )
