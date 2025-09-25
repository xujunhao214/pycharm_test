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

        @pytest.mark.retry(n=3, delay=20)
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
            if lots_open is None:
                logging.info("开仓失败")
                # 重新开仓
                self.test_mt4_open(var_manager)
            else:
                logging.info("开仓成功")

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
