import time
from template.commons.api_base import APITestBase, CompareOp
import allure
import logging
import json
import pytest
from template.VAR.VAR import *
from template.commons.jsonpath_utils import *
from template.commons.random_generator import *


@allure.feature("账号管理-历史订单的查询校验")
class Test_historical(APITestBase):
    # 实例化JsonPath工具类（全局复用）
    json_utils = JsonPathUtils()

    # @pytest.mark.skipif(True, reason="该用例暂时跳过")
    @allure.title("订单查询")
    def test_query_order_no(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            order_no = var_manager.get_variable("order_no")
            params = {
                "_t": current_timestamp_seconds,
                "order_no": order_no,
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "superQueryMatchType": "and"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/402883977b38c9ca017b38c9d0960001',
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
            order_no_list = self.json_utils.extract(
                response.json(),
                "$.result.records[*].order_no",
                default=[],
                multi_match=True
            )

            if not order_no_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"订单查询-{order_no}：{ONE_HOUR_AGO}，返回 {len(order_no_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"{ONE_HOUR_AGO}查询结果",
                attachment_type="text/plain"
            )

            for idx, order_nol in enumerate(order_no_list):
                self.verify_data(
                    actual_value=order_nol,
                    expected_value=order_no,
                    op=CompareOp.GE,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的订单查询符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的订单校验"
                )

    # @pytest.mark.skipif(True, reason="该用例暂时跳过")
    @allure.title("订单查询-查询结果为空")
    def test_query_orderNone(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "order_no": "999999999",
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "superQueryMatchType": "and"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/402883977b38c9ca017b38c9d0960001',
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

    # 定义所有需要测试的类型（作为参数化数据源）
    TYPE_PARAMS = [
        (0, "BUY"),
        (1, "SELL"),
        (2, "BUYLIMIT"),
        (3, "SELLLIMIT"),
        (4, "BUYSTOP"),
        (5, "SELL-STOP"),
        (6, "DEPOSIT"),
        (7, "CRDIT"),
    ]

    # 使用parametrize参数化：每个类型生成一个独立用例
    @pytest.mark.parametrize("type, type_desc", TYPE_PARAMS)
    @allure.title("类型查询：{type_desc}（{type}）")  # 标题动态显示类型信息
    def test_query_type(self, var_manager, logged_session, type, type_desc):
        """按类型拆分的独立用例：查询指定类型并校验结果"""
        # 用例级附件：当前类型说明
        allure.attach(
            body=f"类型编码：{type}\n类型描述：{type_desc}",
            name=f"类型-{type_desc}：说明",
            attachment_type="text/plain"
        )

        with allure.step(f"1. 发送请求：查询[{type_desc}]类型（{type}）"):
            params = {
                "_t": current_timestamp_seconds,
                "type": type,
                "column": "open_time",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "superQueryMatchType": "and"
            }
            response = self.send_get_request(
                logged_session,
                'online/cgform/api/getData/402883977b38c9ca017b38c9d0960001',
                params=params
            )

        with allure.step("2. 基础响应校验：success = True"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

        with allure.step(f"3. 查询结果校验：返回记录的type应为{type}"):
            type_list = self.json_utils.extract(
                response.json(),
                "$.result.records[*].type",
                default=[],
                multi_match=True
            )

            # 生成查询结果附件
            if not type_list:
                attach_body = f"类型查询-{type_desc}：返回的records为空列表（暂无数据）"
            else:
                attach_body = f"类型查询-{type_desc}，返回 {len(type_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"类型-{type_desc}：查询结果",
                attachment_type="text/plain"
            )

            # 校验每条记录的type
            for idx, actual_type in enumerate(type_list):
                self.verify_data(
                    actual_value=actual_type,
                    expected_value=type,
                    op=CompareOp.EQ,
                    message=f"第 {idx + 1} 条记录的type应为{type}",
                    attachment_name=f"类型-{type_desc}：第 {idx + 1} 条记录校验"
                )

    @pytest.mark.skipif(True, reason="该用例暂时跳过")
    @allure.title("开仓时间查询")
    def test_query_open_time(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "open_time": ONE_HOUR_AGO,
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "superQueryMatchType": "and"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/402883977b38c9ca017b38c9d0960001',
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
            open_time_list = self.json_utils.extract(
                response.json(),
                "$.result.records[*].open_time",
                default=[],
                multi_match=True
            )

            if not open_time_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"开仓时间查询-{ONE_HOUR_AGO}，返回 {len(open_time_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"开仓时间-{ONE_HOUR_AGO}查询结果",
                attachment_type="text/plain"
            )

            for idx, open_timel in enumerate(open_time_list):
                self.verify_data(
                    actual_value=open_timel,
                    expected_value=ONE_HOUR_AGO,
                    op=CompareOp.GE,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的开仓时间查询符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的开仓时间校验"
                )

    # @pytest.mark.skipif(True, reason="该用例暂时跳过")
    @allure.title("开仓时间查询-查询结果为空")
    def test_query_open_timeNone(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "open_time": DATETIME_NOW,
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "superQueryMatchType": "and"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/402883977b38c9ca017b38c9d0960001',
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
    @allure.title("平仓时间查询")
    def test_query_close_time(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "close_time_begin": ONE_HOUR_AGO,
                "close_time_end": DATETIME_NOW,
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "superQueryMatchType": "and"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/402883977b38c9ca017b38c9d0960001',
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
            close_time_list = self.json_utils.extract(
                response.json(),
                "$.result.records[*].close_time",
                default=[],
                multi_match=True
            )

            if not close_time_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"平仓时间查询-{ONE_HOUR_AGO}，返回 {len(close_time_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"平仓时间-{ONE_HOUR_AGO}查询结果",
                attachment_type="text/plain"
            )

            for idx, close_timel in enumerate(close_time_list):
                self.verify_data(
                    actual_value=close_timel,
                    expected_value=ONE_HOUR_AGO,
                    op=CompareOp.GE,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的平仓时间查询符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的平仓时间校验"
                )

    # @pytest.mark.skipif(True, reason="该用例暂时跳过")
    @allure.title("平仓时间查询-查询结果为空")
    def test_query_close_timeNone(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "close_time_begin": DATETIME_NOW,
                "close_time_end": ONE_HOUR_AGO,
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "superQueryMatchType": "and"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/402883977b38c9ca017b38c9d0960001',
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
    @allure.title("交易品种查询")
    def test_query_symbol(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            symbol = var_manager.get_variable("symbol")
            params = {
                "_t": current_timestamp_seconds,
                "symbol": symbol,
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "superQueryMatchType": "and"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/402883977b38c9ca017b38c9d0960001',
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
            symbol_list = self.json_utils.extract(
                response.json(),
                "$.result.records[*].symbol",
                default=[],
                multi_match=True
            )

            if not symbol_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"交易品种查询-{symbol}，返回 {len(symbol_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"交易品种-{symbol}查询结果",
                attachment_type="text/plain"
            )

            for idx, symbollt in enumerate(symbol_list):
                self.verify_data(
                    actual_value=symbollt,
                    expected_value=symbol,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的交易品种查询符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的交易品种校验"
                )

    # @pytest.mark.skipif(True, reason="该用例暂时跳过")
    @allure.title("交易品种查询-查询结果为空")
    def test_query_symbolNone(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "symbol": "xxxxxxx",
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "superQueryMatchType": "and"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/402883977b38c9ca017b38c9d0960001',
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
    @allure.title("注释查询")
    def test_query_comment(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            comment = var_manager.get_variable("comment")
            params = {
                "_t": current_timestamp_seconds,
                "comment": comment,
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "superQueryMatchType": "and"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/402883977b38c9ca017b38c9d0960001',
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
            comment_list = self.json_utils.extract(
                response.json(),
                "$.result.records[*].comment",
                default=[],
                multi_match=True
            )

            if not comment_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"注释查询-{comment}，返回 {len(comment_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"注释-{comment}查询结果",
                attachment_type="text/plain"
            )

            for idx, commentlt in enumerate(comment_list):
                self.verify_data(
                    actual_value=commentlt,
                    expected_value=comment,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的注释查询符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的注释校验"
                )

    # @pytest.mark.skipif(True, reason="该用例暂时跳过")
    @allure.title("注释查询-查询结果为空")
    def test_query_commentNone(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "comment": "xxxxxxx",
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "superQueryMatchType": "and"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/402883977b38c9ca017b38c9d0960001',
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
    @allure.title("MT4账号查询")
    def test_query_trader_id(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            trader_pass_id = var_manager.get_variable("trader_pass_id")
            trader_account = var_manager.get_variable("trader_account")
            params = {
                "_t": current_timestamp_seconds,
                "trader_id": trader_pass_id,
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "superQueryMatchType": "and"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/402883977b38c9ca017b38c9d0960001',
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
            trader_id_list = self.json_utils.extract(
                response.json(),
                "$.result.records[*].trader_id",
                default=[],
                multi_match=True
            )

            if not trader_id_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"MT4账号查询-{trader_pass_id}，返回 {len(trader_id_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"MT4账号-{trader_pass_id}查询结果",
                attachment_type="text/plain"
            )

            for idx, trader_idlt in enumerate(trader_id_list):
                self.verify_data(
                    actual_value=trader_idlt,
                    expected_value=trader_pass_id,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的MT4账号查询符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的MT4账号校验,MT4账号是{trader_account}"
                )

    # @pytest.mark.skipif(True, reason="该用例暂时跳过")
    @allure.title("MT4账号查询-查询结果为空")
    def test_query_trader_idNone(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "trader_id": "xxxxxxx",
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "superQueryMatchType": "and"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/402883977b38c9ca017b38c9d0960001',
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
    @allure.title("所属账户查询")
    def test_query_owning_userid(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            trader_user_id = var_manager.get_variable("trader_user_id")
            trader_audit_by = var_manager.get_variable("trader_audit_by")
            params = {
                "_t": current_timestamp_seconds,
                "owning_userid": trader_user_id,
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "superQueryMatchType": "and"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/402883977b38c9ca017b38c9d0960001',
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
            owning_userid_list = self.json_utils.extract(
                response.json(),
                "$.result.records[*].owning_userid",
                default=[],
                multi_match=True
            )

            if not owning_userid_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"所属账户查询-{trader_user_id}，返回 {len(owning_userid_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"所属账户-{trader_user_id}查询结果",
                attachment_type="text/plain"
            )

            for idx, owning_useridlt in enumerate(owning_userid_list):
                self.verify_data(
                    actual_value=owning_useridlt,
                    expected_value=trader_user_id,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的所属账户查询符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的所属账户校验,所属账户是{trader_audit_by}"
                )

    # @pytest.mark.skipif(True, reason="该用例暂时跳过")
    @allure.title("所属账户查询-查询结果为空")
    def test_query_owning_useridNone(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "owning_userid": "999999999999",
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "superQueryMatchType": "and"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/402883977b38c9ca017b38c9d0960001',
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
    @allure.title("策略订单号查询")
    def test_query_master_orderno(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            master_order_no = var_manager.get_variable("master_order_no")
            params = {
                "_t": current_timestamp_seconds,
                "master_order_no": master_order_no,
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "superQueryMatchType": "and"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/402883977b38c9ca017b38c9d0960001',
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
            master_order_no_list = self.json_utils.extract(
                response.json(),
                "$.result.records[*].master_order_no",
                default=[],
                multi_match=True
            )

            if not master_order_no_list:
                pytest.fail("查询结果为空，不符合预期")
            else:
                attach_body = f"策略订单号查询-{master_order_no}，返回 {len(master_order_no_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"策略订单号-{master_order_no}查询结果",
                attachment_type="text/plain"
            )

            for idx, master_order_nolt in enumerate(master_order_no_list):
                self.verify_data(
                    actual_value=master_order_nolt,
                    expected_value=master_order_no,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录的策略订单号查询符合预期",
                    attachment_name=f"第 {idx + 1} 条记录的策略订单号校验"
                )

    # @pytest.mark.skipif(True, reason="该用例暂时跳过")
    @allure.title("策略订单号查询-查询结果为空")
    def test_query_master_ordernoNone(self, var_manager, logged_session):
        with allure.step("1. 发送请求"):
            params = {
                "_t": current_timestamp_seconds,
                "master_order_no": "999999999999",
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
                "superQueryMatchType": "and"
            }
            response = self.send_get_request(
                logged_session,
                '/online/cgform/api/getData/402883977b38c9ca017b38c9d0960001',
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
