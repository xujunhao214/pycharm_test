import time
from template_model.commons.api_base import APITestBase, CompareOp, logger
import allure
import logging
import logging
import datetime
import re
import pytest
import requests
from template_model.VAR.VAR import *
from template_model.commons.jsonpath_utils import *
from template_model.commons.random_generator import *
from template_model.commons.session import percentage_to_decimal


@allure.feature("账户管理-持仓订单")
class Test_openandclouseall:
    # @pytest.mark.skipif(True, reason="跳过此用例")
    class Test_orderseng(APITestBase):
        # 实例化JsonPath工具类（全局复用）
        json_utils = JsonPathUtils()

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
                trader_account = var_manager.get_variable("trader_account")
                trader_password = var_manager.get_variable("trader_password")
                host = var_manager.get_variable("host")
                port = var_manager.get_variable("port")
                try:
                    url = f"{MT4_URL}/Connect?user={trader_account}&password={trader_password}&host={host}&port={port}&connectTimeoutSeconds=30"

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
            symbol = var_manager.get_variable("symbol")
            url = f"{MT4_URL}/OrderSend?id={token_mt4}&symbol={symbol}&operation=Buy&volume=0.01&placedType=Client&price=0.00"

            payload = ""
            self.response = requests.request("GET", url, headers=headers, data=payload)
            self.json_utils = JsonPathUtils()
            self.response = self.response.json()

            ticket_open = self.json_utils.extract(self.response, "$.ticket")
            lots_open = self.json_utils.extract(self.response, "$.lots")
            var_manager.set_runtime_variable("ticket_open", ticket_open)
            var_manager.set_runtime_variable("lots_open", lots_open)
            print(ticket_open, lots_open)
            logging.info(f"ticket: {ticket_open},lots_open:{lots_open}")

        # @pytest.mark.skip(reason=SKIP_REASON)
        @allure.title("数据库提取数据-开仓时间差")
        def test_dbquery_openorder(self, var_manager, db_transaction):
            with allure.step("1. 查询数据库验证是否新增成功"):
                ticket_open = var_manager.get_variable("ticket_open")

                # 优化后的数据库查询
                db_data = self.query_database(
                    db_transaction,
                    f"SELECT * FROM bchain_trader_subscribe_order WHERE master_ticket = %s",
                    (ticket_open,),
                )

                # 提取数据库中的值
                if not db_data:
                    pytest.fail("数据库查询结果为空，无法提取数据")

            with allure.step("2. 提取数据库中的值"):
                slave_ticket = db_data[0]["slave_ticket"]
                print(f"输出：{slave_ticket}")
                logging.info(f"跟单账号订单号: {slave_ticket}")
                var_manager.set_runtime_variable("slave_ticket", slave_ticket)

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("MT4平台平仓操作")
        def test_mt4_close(self, var_manager):
            max_attempts = 3  # 最大总尝试次数
            retry_interval = 10  # 每次尝试间隔时间(秒)
            global token_mt4, headers  # 声明使用全局变量
            ticket_open = var_manager.get_variable("ticket_open")
            ticket_close = None

            # 提取登录所需变量
            uuid_pattern = re.compile(
                r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')

            for attempt in range(max_attempts):
                try:
                    with allure.step(f"1. 发送平仓请求 (第{attempt + 1}次尝试)"):
                        # 检查token是否有效，无效则重新登录
                        if not token_mt4 or not uuid_pattern.match(token_mt4):
                            with allure.step("token无效或不存在，重新登录MT4"):
                                self.test_mt4_login(var_manager)  # 调用登录方法获取新token

                        # 发送平仓请求
                        url = f"{MT4_URL}/OrderClose?id={token_mt4}&ticket={ticket_open}&price=0.00"
                        self.response = requests.request("GET", url, headers=headers)
                        self.response_json = self.response.json()
                        logging.info(f"第{attempt + 1}次平仓响应: {self.response_json}")

                    # 提取平仓订单号
                    ticket_close = self.json_utils.extract(self.response_json, "$.ticket")

                    # 检查平仓是否成功
                    if ticket_close is not None:
                        with allure.step("2. 数据校验"):
                            self.verify_data(
                                actual_value=ticket_close,
                                expected_value=ticket_open,
                                op=CompareOp.EQ,
                                use_isclose=False,
                                message="预期：开仓订单号和平仓订单号一致",
                                attachment_name="订单号详情"
                            )
                            logger.info(
                                f"开仓订单号和平仓订单号一致,开仓订单号：{ticket_open} 平仓订单号：{ticket_close}")
                        break  # 成功则跳出循环
                    else:
                        logging.warning(f"第{attempt + 1}次平仓失败，未获取到平仓订单号")

                except Exception as e:
                    logging.error(f"第{attempt + 1}次平仓发生异常: {str(e)}")

                # 如果不是最后一次尝试，等待后重试
                if attempt < max_attempts - 1:
                    logging.info(f"将在{retry_interval}秒后进行第{attempt + 2}次尝试...")
                    time.sleep(retry_interval)
                    # 主动重新登录获取新token
                    with allure.step(f"准备第{attempt + 2}次尝试，先重新登录MT4"):
                        self.test_mt4_login(var_manager)

            # 所有尝试结束后仍失败，标记用例失败
            if ticket_close is None:
                pytest.fail(f"经过{max_attempts}次尝试（包含重新登录）后，平仓仍失败，订单号: {ticket_open}")

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("账号管理-历史订单-喊单MT4账户查询-平仓后")
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

            with allure.step(f"3. 查询校验"):
                order_size = self.json_utils.extract(response.json(), "$.result.records[0].size")
                logging.info(f"喊单者手数是: {order_size}")
                var_manager.set_runtime_variable("order_size", order_size)

                trader_id_list = self.json_utils.extract(
                    response.json(),
                    "$.result.records[0].trader_id",
                    default=[],
                    multi_match=True
                )

                if not trader_id_list:
                    attach_body = f"MT4账号查询[{trader_account}]，返回的trader_id列表为空（暂无数据）"
                else:
                    attach_body = f"MT4账号查询[{trader_account}]，返回 {len(trader_id_list)} 条记录"

                allure.attach(
                    body=attach_body,
                    name=f"账号ID:{trader_account}查询结果",
                    attachment_type="text/plain"
                )

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

                    with allure.step("喊单手数校验-MT4开仓手数和持仓订单手数"):
                        order_size = self.json_utils.extract(response.json(), "$.result.records[0].size")
                        logging.info(f"喊单者手数是: {order_size}")

                        lots_open = var_manager.get_variable("lots_open")
                        self.verify_data(
                            actual_value=float(order_size),
                            expected_value=float(lots_open),
                            op=CompareOp.EQ,
                            message=f"手数符合预期",
                            attachment_name="手数详情"
                        )
                        logger.info(f"喊单者手数：{order_size} MT4开仓手数：{lots_open}")

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("账号管理-历史订单-跟单MT4账户查询-平仓后")
        def test_query_follow_id(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                follow_pass_id = var_manager.get_variable("follow_pass_id")
                follow_account = var_manager.get_variable("follow_account")
                params = {
                    "_t": current_timestamp_seconds,
                    "trader_id": follow_pass_id,
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

            with allure.step("3. 提取数据"):
                order_no = self.json_utils.extract(response.json(), "$.result.records[0].order_no")
                var_manager.set_runtime_variable("order_no", order_no)
                allure.attach(f"{order_no}", "跟单订单号", allure.attachment_type.TEXT)

            with allure.step(f"3. 查询校验"):
                trader_id_list = self.json_utils.extract(
                    response.json(),
                    "$.result.records[0].trader_id",
                    default=[],
                    multi_match=True
                )

                if not trader_id_list:
                    attach_body = f"MT4账号查询[{follow_account}]，返回的trader_id列表为空（暂无数据）"
                else:
                    attach_body = f"MT4账号查询[{follow_account}]，返回 {len(trader_id_list)} 条记录"

                allure.attach(
                    body=attach_body,
                    name=f"账号ID:{follow_account}查询结果",
                    attachment_type="text/plain"
                )

                for idx, trader_id in enumerate(trader_id_list):
                    self.verify_data(
                        actual_value=int(trader_id),
                        expected_value=int(follow_pass_id),
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的账号ID应为{trader_id}",
                        attachment_name=f"账号ID:{follow_pass_id}第 {idx + 1} 条记录校验"
                    )

                with allure.step("喊单者订单号校验"):
                    master_order_no = self.json_utils.extract(response.json(),
                                                              "$.result.records[0].master_order_no")
                    ticket_open = var_manager.get_variable("ticket_open")

                    self.verify_data(
                        actual_value=master_order_no,
                        expected_value=ticket_open,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"订单号数据正确",
                        attachment_name="订单号详情"
                    )
                    logger.info(f"订单号数据正确,开仓订单号：{ticket_open} 喊单者订单号：{master_order_no}")

                with allure.step("跟单订单号校验"):
                    slave_ticket = var_manager.get_variable("slave_ticket")
                    self.verify_data(
                        actual_value=slave_ticket,
                        expected_value=order_no,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"订单号数据正确",
                        attachment_name="订单号详情"
                    )
                    logger.info(f"订单号数据正确,跟单者订单号：{order_no} 数据库数据：{slave_ticket}")

                with allure.step("跟单手数校验"):
                    add_size = self.json_utils.extract(response.json(), "$.result.records[0].size")
                    if not add_size:
                        allure.attach("订单手数数据为空", "订单手数数据", allure.attachment_type.TEXT)
                    else:
                        lots_open = var_manager.get_variable("lots_open")
                        # 获取跟单固定比例
                        follow_fixed_proportion = var_manager.get_variable("follow_fixed_proportion")
                        # 百分比数据转换
                        follow_fixed_decimal = percentage_to_decimal(follow_fixed_proportion)
                        expected_lots_open = follow_fixed_decimal * lots_open

                        # 最小手数限制（0.01）
                        min_order_size = 0.01
                        if expected_lots_open < min_order_size:
                            allure.attach(
                                f"计算预期手数{expected_lots_open} < 最小手数{min_order_size}，强制重置为{min_order_size}",
                                "预期手数调整说明", allure.attachment_type.TEXT)
                            expected_lots_open = min_order_size

                        self.verify_data(
                            actual_value=float(add_size),
                            expected_value=float(expected_lots_open),
                            op=CompareOp.EQ,
                            message=f"手数符合预期",
                            attachment_name="手数详情"
                        )
                        logger.info(f"跟单者手数：{add_size}")
