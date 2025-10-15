import time
from lingkuan_comm.commons.api_vpsbase import APIVPSBase, CompareOp, logger
import allure
import logging
import logging
import datetime
import re
import json
import pytest
import requests
from lingkuan_comm.VAR.VAR import *
from lingkuan_comm.commons.jsonpath_utils import *


@allure.title("数据校验开始前操作")
class cloud_PublicUtils(APIVPSBase):
    # 实例化JsonPath工具类（全局复用）
    json_utils = JsonPathUtils()

    @allure.title("登录MT4账号获取token")
    def test_mt4_login(self, var_manager):
        with allure.step("MT4发送登录请求"):
            global cloud_token_mt4, headers
            max_retries = 5  # 最大重试次数
            retry_interval = 5  # 重试间隔（秒）
            cloud_token_mt4 = None

            # 用于验证token格式的正则表达式（UUID格式）
            uuid_pattern = re.compile(
                r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')

            for attempt in range(max_retries):
                cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
                new_user = var_manager.get_variable("new_user")
                cloud_password = new_user["password"]
                host = var_manager.get_variable("host")
                port = var_manager.get_variable("port")
                try:
                    url = f"{MT4_URL}/Connect?user={cloudTrader_user_accounts_4}&password={cloud_password}&host={host}&port={port}&connectTimeoutSeconds=30"

                    headers = {
                        'Authorization': 'e5f9f574-fd0a-42bd-904b-3a7a088de27e',
                        'x-sign': '417B110F1E71BD2CFE96366E67849B0B',
                        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
                        'Content-Type': 'application/json',
                        'Accept': '*/*',
                        'Host': 'mt4.mtapi.io',
                        'Connection': 'keep-alive'
                    }

                    with allure.step(f"第{attempt + 1}次尝试"):
                        response = requests.request("GET", url, headers=headers, data={})
                        allure.attach(url, "请求URL", allure.attachment_type.TEXT)
                        headers_json = json.dumps(headers, ensure_ascii=False, indent=2)
                        allure.attach(headers_json, "请求头", allure.attachment_type.JSON)
                        # 去除可能的空白字符
                        response_text = response.text.strip()

                        logging.info(f"第{attempt + 1}次登录尝试 - 响应内容: {response_text}")
                        allure.attach(response_text, "响应内容", allure.attachment_type.TEXT)

                        # 验证响应是否为有效的UUID格式token
                        if uuid_pattern.match(response_text):
                            cloud_token_mt4 = response_text
                            logging.info(f"第{attempt + 1}次尝试成功 - 获取到token: {cloud_token_mt4}")
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
            if not cloud_token_mt4 or not uuid_pattern.match(cloud_token_mt4):
                logging.error(f"经过{max_retries}次尝试后，MT4登录仍失败")
                assert False, "MT4登录失败"
            else:
                print(f"登录MT4账号获取token: {cloud_token_mt4}")
                logging.info(f"登录MT4账号获取token: {cloud_token_mt4}")

    @allure.title("MT4平台开仓操作")
    def test_mt4_open(self, var_manager):
        with allure.step("MT4发送开仓请求"):
            symbol = var_manager.get_variable("symbol")
            url = f"{MT4_URL}/OrderSend?id={cloud_token_mt4}&symbol={symbol}&operation=Buy&volume=1&placedType=Client&price=0.00"

            payload = ""
            self.response = requests.request("GET", url, headers=headers, data=payload)
            allure.attach(url, "请求URL", allure.attachment_type.TEXT)
            headers_json = json.dumps(headers, ensure_ascii=False, indent=2)
            allure.attach(headers_json, "请求头", allure.attachment_type.JSON)
            self.json_utils = JsonPathUtils()
            self.response = self.response.json()
            allure.attach(json.dumps(self.response, ensure_ascii=False, indent=2), "响应内容",
                          allure.attachment_type.JSON)

            cloud_ticket_open = self.json_utils.extract(self.response, "$.ticket")
            cloud_lots_open = self.json_utils.extract(self.response, "$.lots")
            var_manager.set_runtime_variable("cloud_ticket_open", cloud_ticket_open)
            var_manager.set_runtime_variable("cloud_lots_open", cloud_lots_open)
            print(f"ticket: {cloud_ticket_open},cloud_lots_open:{cloud_lots_open}")
            logging.info(f"ticket: {cloud_ticket_open},cloud_lots_open:{cloud_lots_open}")
            if cloud_lots_open is None or cloud_ticket_open is None:
                logging.info("开仓失败")
                # 重新开仓
                self.test_mt4_open(var_manager)
            else:
                logging.info("开仓成功")

    # @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("MT4平台平仓操作")
    def test_mt4_close(self, var_manager, dbvps_transaction):
        with allure.step("MT4发送平仓请求"):
            max_attempts = 3  # 最大总尝试次数
            retry_interval = 10  # 每次尝试间隔时间(秒)
            global cloud_token_mt4, headers  # 声明使用全局变量
            ticket_close = None

            # 提取登录所需变量
            uuid_pattern = re.compile(
                r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')

            for attempt in range(max_attempts):
                try:
                    with allure.step(f"1. 第{attempt + 1}次尝试"):
                        cloud_ticket_open = var_manager.get_variable("cloud_ticket_open")
                        # 检查token是否有效，无效则重新登录
                        if not cloud_token_mt4 or not uuid_pattern.match(cloud_token_mt4):
                            with allure.step("token无效或不存在，重新登录MT4"):
                                self.test_mt4_login(var_manager)  # 调用登录方法获取新token

                        # 发送平仓请求
                        url = f"{MT4_URL}/OrderClose?id={cloud_token_mt4}&ticket={cloud_ticket_open}&price=0.00"
                        self.response = requests.request("GET", url, headers=headers)
                        self.response_json = self.response.json()
                        logging.info(f"第{attempt + 1}次平仓响应: {self.response_json}")

                        allure.attach(url, "请求URL", allure.attachment_type.TEXT)
                        headers_json = json.dumps(headers, ensure_ascii=False, indent=2)
                        allure.attach(headers_json, "请求头", allure.attachment_type.JSON)
                        allure.attach(json.dumps(self.response_json, ensure_ascii=False, indent=2), "响应内容",
                                      allure.attachment_type.JSON)

                    # 提取平仓订单号
                    ticket_close = self.json_utils.extract(self.response_json, "$.ticket")

                    # 检查平仓是否成功
                    if ticket_close is not None:
                        logger.info(f"平仓订单号：{ticket_close}")
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
                    with allure.step(f"准备第{attempt + 2}次尝试，重新登录MT4"):
                        self.test_mt4_login(var_manager)
                    # 重新开仓
                    with allure.step(f"准备第{attempt + 2}次尝试，重新开仓"):
                        self.test_mt4_open(var_manager)

            # 所有尝试结束后仍失败，标记用例失败
            if ticket_close is None:
                pytest.fail(f"经过{max_attempts}次尝试（包含重新登录）后，平仓仍失败，订单号: {cloud_ticket_open}")
