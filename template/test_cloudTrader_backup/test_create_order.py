import time
import re
import logging
import datetime
import pytest
import requests
import allure
from template.commons.api_base import APITestBase, CompareOp, logger
from template.VAR.VAR import *
from template.commons.jsonpath_utils import JsonPathUtils
from template.commons.random_generator import *


@allure.story("创建订单")
class Test_createOD(APITestBase):
    # 工具类实例化
    json_utils = JsonPathUtils()

    # 全局变量
    token_mt4 = None
    headers = {
        'Authorization': 'e5f9f574-fd0a-42bd-904b-3a7a088de27e',
        'x-sign': '417B110F1E71BD2CFE96366E67849B0B',
        'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
        'Content-Type': 'application/json',
        'Accept': '*/*',
        'Host': 'mt4.mtapi.io',
        'Connection': 'keep-alive'
    }

    # 配置参数
    TOTAL_CYCLES = 50  # 总循环次数
    MAX_LOGIN_RETRIES = 5  # 登录最大重试次数
    LOGIN_RETRY_INTERVAL = 5  # 登录重试间隔(秒)
    MAX_TRADE_RETRIES = 3  # 交易操作最大重试次数
    TRADE_RETRY_INTERVAL = 10  # 交易重试间隔(秒)
    SYNC_WAIT_SECONDS = 2  # 同步等待时间

    # Token格式验证正则
    uuid_pattern = re.compile(
        r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
    )

    def login_mt4(self, var_manager):
        """封装登录逻辑，供内部调用"""
        for attempt in range(self.MAX_LOGIN_RETRIES):
            try:
                # 获取登录参数
                trader_account = var_manager.get_variable("trader_account")
                trader_password = var_manager.get_variable("trader_password")
                host = var_manager.get_variable("host")
                port = var_manager.get_variable("port")

                # 构建登录URL
                url = f"{MT4_URL}/Connect?user={trader_account}&password={trader_password}&host={host}&port={port}&connectTimeoutSeconds=30"

                # 发送登录请求
                response = requests.get(url, headers=self.headers, timeout=15)
                response_text = response.text.strip()

                logging.info(f"第{attempt + 1}次登录尝试 - 响应内容: {response_text}")

                # 验证Token格式
                if self.uuid_pattern.match(response_text):
                    self.token_mt4 = response_text
                    logging.info(f"第{attempt + 1}次尝试成功 - 获取到token: {self.token_mt4}")
                    return True
                else:
                    logging.warning(f"第{attempt + 1}次尝试失败 - 无效的token格式")

            except Exception as e:
                logging.error(f"第{attempt + 1}次登录尝试异常: {str(e)}")

            # 重试等待
            if attempt < self.MAX_LOGIN_RETRIES - 1:
                time.sleep(self.LOGIN_RETRY_INTERVAL)

        # 登录失败
        logging.error(f"经过{self.MAX_LOGIN_RETRIES}次尝试，MT4登录失败")
        return False

    @allure.title("登录MT4账号获取token")
    def test_mt4_login(self, var_manager):
        """登录测试用例，确保初始Token有效"""
        login_success = self.login_mt4(var_manager)
        assert login_success, "MT4登录失败"
        print(f"登录MT4账号获取token: {self.token_mt4}")
        logging.info(f"登录MT4账号获取token: {self.token_mt4}")

    def open_position(self, var_manager, cycle):
        """执行开仓操作"""
        symbol = var_manager.get_variable("symbol")

        for attempt in range(self.MAX_TRADE_RETRIES):
            try:
                # 检查Token有效性，无效则重新登录
                if not self.token_mt4 or not self.uuid_pattern.match(self.token_mt4):
                    logging.warning("Token无效，尝试重新登录...")
                    if not self.login_mt4(var_manager):
                        continue

                # 发送开仓请求
                url = f"{MT4_URL}/OrderSend?id={self.token_mt4}&symbol={symbol}&operation=Buy&volume=0.01&placedType=Client&price=0.00"
                response = requests.get(url, headers=self.headers, timeout=15)
                response_json = response.json()
                logging.info(f"第{cycle}次循环第{attempt + 1}次开仓响应: {response_json}")

                # 提取订单号
                ticket_open = self.json_utils.extract(response_json, "$.ticket")
                lots_open = self.json_utils.extract(response_json, "$.lots")

                if ticket_open:
                    var_manager.set_runtime_variable(f"ticket_open_{cycle}", ticket_open)
                    var_manager.set_runtime_variable(f"lots_open_{cycle}", lots_open)
                    logging.info(f"第{cycle}次循环开仓成功 - ticket: {ticket_open}, lots: {lots_open}")
                    return ticket_open

                logging.warning(f"第{cycle}次循环第{attempt + 1}次开仓未获取到订单号")

            except Exception as e:
                logging.error(f"第{cycle}次循环第{attempt + 1}次开仓异常: {str(e)}")

            # 重试等待
            if attempt < self.MAX_TRADE_RETRIES - 1:
                time.sleep(self.TRADE_RETRY_INTERVAL)

        # 开仓失败
        logging.error(f"第{cycle}次循环开仓失败，已尝试{self.MAX_TRADE_RETRIES}次")

    def close_position(self, var_manager, cycle, ticket_open):
        """执行平仓操作"""
        for attempt in range(self.MAX_TRADE_RETRIES):
            try:
                # 检查Token有效性
                if not self.token_mt4 or not self.uuid_pattern.match(self.token_mt4):
                    logging.warning("Token无效，尝试重新登录...")
                    if not self.login_mt4(var_manager):
                        continue

                # 发送平仓请求
                url = f"{MT4_URL}/OrderClose?id={self.token_mt4}&ticket={ticket_open}&price=0.00"
                response = requests.get(url, headers=self.headers, timeout=15)
                response_json = response.json()
                logging.info(f"第{cycle}次循环第{attempt + 1}次平仓响应: {response_json}")

                # 提取平仓订单号
                ticket_close = self.json_utils.extract(response_json, "$.ticket")

                if ticket_close:
                    # 验证订单号一致性
                    self.verify_data(
                        actual_value=ticket_close,
                        expected_value=ticket_open,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第{cycle}次循环 - 开仓平仓订单号一致性校验",
                        attachment_name=f"第{cycle}次循环订单号详情"
                    )
                    logging.info(f"第{cycle}次循环平仓成功 - 开仓订单号: {ticket_open}, 平仓订单号: {ticket_close}")
                    return True

                logging.warning(f"第{cycle}次循环第{attempt + 1}次平仓未获取到订单号")

            except Exception as e:
                logging.error(f"第{cycle}次循环第{attempt + 1}次平仓异常: {str(e)}")

            # 重试等待
            if attempt < self.MAX_TRADE_RETRIES - 1:
                time.sleep(self.TRADE_RETRY_INTERVAL)

        # 平仓失败
        logging.error(f"第{cycle}次循环平仓失败，已尝试{self.MAX_TRADE_RETRIES}次，订单号: {ticket_open}")

    @allure.title(f"MT4平台开仓平仓循环测试（{TOTAL_CYCLES}次）")
    @pytest.mark.order(1)
    def test_open_close_cycles(self, var_manager):
        """主测试用例：执行多次开仓平仓循环"""

        # 记录成功/失败次数
        success_count = 0
        fail_count = 0
        fail_details = []

        # 循环执行开仓平仓
        for cycle in range(1, self.TOTAL_CYCLES + 1):
            allure.dynamic.description(f"第{cycle}/{self.TOTAL_CYCLES}次循环：开仓→平仓")
            logging.info(f"\n===== 开始第{cycle}/{self.TOTAL_CYCLES}次循环 =====")

            try:
                with allure.step(f"第{cycle}次：登录操作"):
                    # 先执行登录
                    self.test_mt4_login(var_manager)
                    print(f"第{cycle}次循环登录MT4成功")

                # 开仓操作
                with allure.step(f"第{cycle}次：开仓操作"):
                    ticket_open = self.open_position(var_manager, cycle)
                    print(f"第{cycle}次循环开仓成功 - 订单号: {ticket_open}")

                # 等待数据同步
                time.sleep(self.SYNC_WAIT_SECONDS)

                # 平仓操作
                with allure.step(f"第{cycle}次：平仓操作（订单号：{ticket_open}）"):
                    self.close_position(var_manager, cycle, ticket_open)
                    print(f"第{cycle}次循环平仓成功 - 订单号: {ticket_open}")

                success_count += 1
                logging.info(f"===== 第{cycle}/{self.TOTAL_CYCLES}次循环成功 =====")

            except Exception as e:
                fail_count += 1
                fail_details.append(f"第{cycle}次循环失败: {str(e)}")
                logging.error(f"===== 第{cycle}/{self.TOTAL_CYCLES}次循环失败: {str(e)} =====")
                # 记录失败信息到报告
                allure.attach(str(e), f"第{cycle}次循环失败原因", allure.attachment_type.TEXT)
                # 继续执行下一次循环，而不是终止整个测试

        # 输出测试总结
        summary = (f"测试总结：\n"
                   f"总循环次数：{self.TOTAL_CYCLES}\n"
                   f"成功次数：{success_count}\n"
                   f"失败次数：{fail_count}")

        if fail_details:
            summary += "\n失败详情：\n" + "\n".join(fail_details)

        logging.info(summary)
        allure.attach(summary, "测试结果总结", allure.attachment_type.TEXT)

        # 如果有失败，标记测试为失败
        if fail_count > 0:
            pytest.fail(f"共有{fail_count}次循环失败，请查看日志详情")
