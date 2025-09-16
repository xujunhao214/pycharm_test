import time
from template.commons.api_base import APITestBase, CompareOp, logger
import allure
import logging
import logging
import datetime
import re
import pytest
import requests
from template.VAR.VAR import *
from template.commons.jsonpath_utils import *
from template.commons.random_generator import *


@allure.feature("账户管理-持仓订单")
class Test_openandclouseall:
    # @pytest.mark.skipif(True, reason="跳过此用例")
    class Test_orderseng(APITestBase):
        # 实例化JsonPath工具类（全局复用）
        json_utils = JsonPathUtils()

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("喊单者账号ID查询-开仓前")
        def test_query_trader_passid(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                trader_pass_id = var_manager.get_variable("trader_pass_id")
                params = {
                    "_t": current_timestamp_seconds,
                    "trader_id": trader_pass_id,
                    "column": "id",
                    "order": "desc",
                    "pageNo": 1,
                    "pageSize": 50,
                    "superQueryMatchType": "and"
                }
                response = self.send_get_request(
                    logged_session,
                    '/online/cgform/api/getData/402883977b38c9ca017b38c9caff0000',
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
                    expression="$.result.records"
                )
                logging.info("查询结果符合预期：records为空列表")
                allure.attach("查询结果为空，符合预期", 'text/plain')

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("跟单账号ID查询-开仓前")
        def test_query_follow_passid(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                follow_pass_id = var_manager.get_variable("follow_pass_id")
                params = {
                    "_t": current_timestamp_seconds,
                    "trader_id": follow_pass_id,
                    "column": "id",
                    "order": "desc",
                    "pageNo": 1,
                    "pageSize": 50,
                    "superQueryMatchType": "and"
                }
                response = self.send_get_request(
                    logged_session,
                    '/online/cgform/api/getData/402883977b38c9ca017b38c9caff0000',
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
                    expression="$.result.records"
                )
                logging.info("查询结果符合预期：records为空列表")
                allure.attach("查询结果为空，符合预期", 'text/plain')

        @allure.title("登录MT4账号获取token")
        def test_mt4_login(self, var_manager):
            global token_mt4, headers
            max_retries = 5  # 最大重试次数
            retry_interval = 5  # 重试间隔（秒）
            token_mt4 = None

            # 用于验证token格式的正则表达式（UUID格式）
            uuid_pattern = re.compile(
                r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')

            for attempt in range(max_retries):
                try:
                    url = "https://mt4.mtapi.io/Connect?user=2088767545&password=j7gdppb&host=acymt4demo01dns01.dnslogix.com&port=443&connectTimeoutSeconds=30"

                    headers = {
                        'Authorization': 'e5f9f574-fd0a-42bd-904b-3a7a088de27e',
                        'x-sign': '417B110F1E71BD2CFE96366E67849B0B',
                        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
                        'Content-Type': 'application/json',
                        'Accept': '*/*',
                        'Host': 'mt4.mtapi.io',
                        'Connection': 'keep-alive'
                    }

                    response = requests.request("GET", url, headers=headers, data={})
                    # 去除可能的空白字符
                    response_text = response.text.strip()

                    logging.info(f"第{attempt + 1}次登录尝试 - 响应内容: {response_text}")

                    # 验证响应是否为有效的UUID格式token
                    if uuid_pattern.match(response_text):
                        token_mt4 = response_text
                        logging.info(f"第{attempt + 1}次尝试成功 - 获取到token: {token_mt4}")
                        break
                    else:
                        logging.warning(f"第{attempt + 1}次尝试失败 - 无效的token格式: {response_text}")

                except Exception as e:
                    logging.error(f"第{attempt + 1}次尝试发生异常: {str(e)}")

                # 如果不是最后一次尝试，等待后重试
                if attempt < max_retries - 1:
                    logging.info(f"将在{retry_interval}秒后进行第{attempt + 2}次重试...")
                    time.sleep(retry_interval)

            # 最终验证结果
            if not token_mt4 or not uuid_pattern.match(token_mt4):
                logging.error(f"经过{max_retries}次尝试后，MT4登录仍失败")
                assert False, "MT4登录失败"
            else:
                print(f"登录MT4账号获取token: {token_mt4}")
                logging.info(f"登录MT4账号获取token: {token_mt4}")

        @allure.title("MT4平台开仓操作")
        def test_mt4_open(self, var_manager):
            url = f"https://mt4.mtapi.io/OrderSend?id={token_mt4}&symbol=XAUUSDzero&operation=Buy&volume=0.01&placedType=Client&price=0.00"

            payload = ""
            self.response = requests.request("GET", url, headers=headers, data=payload)
            self.json_utils = JsonPathUtils()
            self.response = self.response.json()
            ticket_open = self.json_utils.extract(self.response, "$.ticket")
            var_manager.set_runtime_variable("ticket_open", ticket_open)
            print(ticket_open)
            logging.info(f"ticket: {ticket_open}")

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("喊单者账号ID查询-开仓后")
        def test_query_opentrader_passid(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                trader_pass_id = var_manager.get_variable("trader_pass_id")
                trader_account = var_manager.get_variable("trader_account")
                params = {
                    "_t": current_timestamp_seconds,
                    "trader_id": trader_pass_id,
                    "column": "id",
                    "order": "desc",
                    "pageNo": 1,
                    "pageSize": 50,
                    "superQueryMatchType": "and"
                }
                response = self.send_get_request(
                    logged_session,
                    '/online/cgform/api/getData/402883977b38c9ca017b38c9caff0000',
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
                trader_id_list = self.json_utils.extract(
                    response.json(),
                    "$.result.records[0].trader_id",
                    default=[],
                    multi_match=True
                )

                if not trader_id_list:
                    attach_body = f"账号ID查询[{trader_account}]，返回的trader_id列表为空（暂无数据）"
                else:
                    attach_body = f"账号ID查询[{trader_account}]，返回 {len(trader_id_list)} 条记录，trader_id值如下：\n" + \
                                  "\n".join([f"第 {idx + 1} 条：{s}" for idx, s in enumerate(trader_id_list)])

                allure.attach(
                    body=attach_body,
                    name=f"账号ID:{trader_account}查询结果",
                    attachment_type="text/plain"
                )

                # 校验每条记录的dividendType
                for idx, trader_id in enumerate(trader_id_list):
                    self.verify_data(
                        actual_value=int(trader_id),
                        expected_value=int(trader_pass_id),
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的账号ID应为{trader_id}",
                        attachment_name=f"账号ID:{trader_pass_id}第 {idx + 1} 条记录校验"
                    )
                with allure.step("订单号校验"):
                    order_no = self.json_utils.extract(response.json(), "$.result.records[0].order_no")
                    ticket_open = var_manager.get_variable("ticket_open")

                    self.verify_data(
                        actual_value=order_no,
                        expected_value=ticket_open,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"订单号数据正确",
                        attachment_name="订单号详情"
                    )
                    logger.info(f"订单号数据正确,开仓订单号：{ticket_open} 喊单者订单号：{order_no}")

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("跟单账号ID查询-开仓后")
        def test_query_openfollow_passid(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                follow_pass_id = var_manager.get_variable("follow_pass_id")
                follow_account = var_manager.get_variable("follow_account")
                params = {
                    "_t": current_timestamp_seconds,
                    "trader_id": follow_pass_id,
                    "column": "id",
                    "order": "desc",
                    "pageNo": 1,
                    "pageSize": 50,
                    "superQueryMatchType": "and"
                }
                response = self.send_get_request(
                    logged_session,
                    '/online/cgform/api/getData/402883977b38c9ca017b38c9caff0000',
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
                trader_id_list = self.json_utils.extract(
                    response.json(),
                    "$.result.records[0].trader_id",
                    default=[],
                    multi_match=True
                )

                if not trader_id_list:
                    attach_body = f"账号ID查询[{follow_account}]，返回的trader_id列表为空（暂无数据）"
                else:
                    attach_body = f"账号ID查询[{follow_account}]，返回 {len(trader_id_list)} 条记录，trader_id值如下：\n" + \
                                  "\n".join([f"第 {idx + 1} 条：{s}" for idx, s in enumerate(trader_id_list)])

                allure.attach(
                    body=attach_body,
                    name=f"账号ID:{follow_account}查询结果",
                    attachment_type="text/plain"
                )

                # 校验每条记录的dividendType
                for idx, trader_id in enumerate(trader_id_list):
                    self.verify_data(
                        actual_value=int(trader_id),
                        expected_value=int(follow_pass_id),
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的账号ID应为{trader_id}",
                        attachment_name=f"账号ID:{follow_pass_id}第 {idx + 1} 条记录校验"
                    )

                with allure.step("订单号校验"):
                    master_order_no = self.json_utils.extract(response.json(), "$.result.records[0].master_order_no")
                    ticket_open = var_manager.get_variable("ticket_open")

                    self.verify_data(
                        actual_value=master_order_no,
                        expected_value=ticket_open,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"订单号数据正确",
                        attachment_name="订单号详情"
                    )
                    logger.info(f"订单号数据正确,开仓订单号：{ticket_open} 跟单者订单号：{master_order_no}")

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库校验-开仓后")
        def test_dbquery_openorder(self, var_manager, db_transaction):
            with allure.step("1. 查询数据库验证是否新增成功"):
                new_user = var_manager.get_variable("new_user")

                # 优化后的数据库查询
                db_data = self.query_database(
                    db_transaction,
                    f"SELECT * FROM FOLLOW_TRADER_USER WHERE account = %s",
                    (new_user["account"],),
                )

                # 提取数据库中的值
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

                vps_trader_user_id = db_data[0]["id"]
                print(f"输出：{vps_trader_user_id}")
                logging.info(f"新增用户ID: {vps_trader_user_id}")
                var_manager.set_runtime_variable("vps_trader_user_id", vps_trader_user_id)

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("MT4平台平仓操作")
        def test_mt4_close(self, var_manager):
            with allure.step("1. 发送平仓请求"):
                ticket_open = var_manager.get_variable("ticket_open")
                url = f"https://mt4.mtapi.io/OrderClose?id={token_mt4}&ticket={ticket_open}&price=0.00"

                self.response = requests.request("GET", url, headers=headers)
                self.json_utils = JsonPathUtils()
                self.response = self.response.json()

            with allure.step("2. 数据校验"):
                ticket_close = self.json_utils.extract(self.response, "$.ticket")

                self.verify_data(
                    actual_value=ticket_close,
                    expected_value=ticket_open,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message=f"预期：开仓订单号和平仓订单号一致",
                    attachment_name="订单号详情"
                )
                logger.info(f"开仓订单号和平仓订单号一致,开仓订单号：{ticket_open} 平仓订单号：{ticket_close}")

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("喊单者账号ID查询-平仓后")
        def test_query_closetrader_passid(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                trader_pass_id = var_manager.get_variable("trader_pass_id")
                params = {
                    "_t": current_timestamp_seconds,
                    "trader_id": trader_pass_id,
                    "column": "id",
                    "order": "desc",
                    "pageNo": 1,
                    "pageSize": 50,
                    "superQueryMatchType": "and"
                }
                response = self.send_get_request(
                    logged_session,
                    '/online/cgform/api/getData/402883977b38c9ca017b38c9caff0000',
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
                    expression="$.result.records"
                )
                logging.info("查询结果符合预期：records为空列表")
                allure.attach("查询结果为空，符合预期", 'text/plain')

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("跟单账号ID查询-平仓后")
        def test_query_closefollow_passid(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                follow_pass_id = var_manager.get_variable("follow_pass_id")
                params = {
                    "_t": current_timestamp_seconds,
                    "trader_id": follow_pass_id,
                    "column": "id",
                    "order": "desc",
                    "pageNo": 1,
                    "pageSize": 50,
                    "superQueryMatchType": "and"
                }
                response = self.send_get_request(
                    logged_session,
                    '/online/cgform/api/getData/402883977b38c9ca017b38c9caff0000',
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
                    expression="$.result.records"
                )
                logging.info("查询结果符合预期：records为空列表")
                allure.attach("查询结果为空，符合预期", 'text/plain')
