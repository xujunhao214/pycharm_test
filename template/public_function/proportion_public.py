import time
from template.commons.api_base import APITestBase, CompareOp, logger
import allure
import logging
import logging
import datetime
import re
import json
import pytest
import requests
from template.VAR.VAR import *
from template.commons.jsonpath_utils import *
from template.commons.random_generator import *
from template.commons.session import percentage_to_decimal


@allure.title("数据校验开始前操作")
class PublicUtils(APITestBase):
    # 实例化JsonPath工具类（全局复用）
    json_utils = JsonPathUtils()

    @allure.title("跟单社区前端-登录")
    def test_login(self, var_manager):
        with allure.step("1. 跟单社区前端-发送登录请求"):
            url = f"{URL_TOP}/sys/mLogin"

            payload = json.dumps({
                "username": "xujunhao@163.com",
                "password": "123456",
                "lang": 0,
                "orgCode": "A01"
            })
            headers = {
                'priority': 'u=1, i',
                'x-access-token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3NTgyNDY3ODIsInVzZXJuYW1lIjoiYW5vbnltb3VzIn0.lvI66l-hA0VqHCsfgODrPoH4KylpOpzVuSOOycls5gE',
                'X-Access-Token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3NTc0OTMyMDMsInVzZXJuYW1lIjoiYWRtaW4ifQ.PkFLjsBa0NbCUF8ROtmIGABzYmUH2ldQfqz_ERvaKsY',
                'content-type': 'application/json',
                'Accept': '*/*',
                'Host': 'dev.lgcopytrade.top',
                'Connection': 'keep-alive'
            }

            response = requests.request("POST", url, headers=headers, data=payload)
            allure.attach(url, "请求URL", allure.attachment_type.TEXT)
            headers_json = json.dumps(headers, ensure_ascii=False, indent=2)
            allure.attach(headers_json, "请求头", allure.attachment_type.JSON)
            # print(response.text)
            logging.info(f"登录返回信息：{response.text}")
            allure.attach(response.text, "响应信息", allure.attachment_type.JSON)

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

        with allure.step("3. 提取token"):
            token_top = self.json_utils.extract(response.json(), "$.result.token")
            var_manager.set_runtime_variable("token_top", token_top)

    @allure.title("跟单社区前端-喊单账号平仓")
    def test_close_trader(self, var_manager):
        with allure.step("1. 跟单社区前端-发送喊单账号平仓请求"):
            global headers
            trader_pass_id = var_manager.get_variable("trader_pass_id")
            token_top = var_manager.get_variable("token_top")
            url = f"{URL_TOP}/blockchain/account/closeAllOrder?traderId={trader_pass_id}&including=true"

            headers = {
                'priority': 'u=1, i',
                'X-Access-Token': token_top,
                'Accept': '*/*',
                'Host': 'dev.lgcopytrade.top',
                'Connection': 'keep-alive'
            }

            response = requests.request("GET", url, headers=headers, data={})
            allure.attach(url, "请求URL", allure.attachment_type.TEXT)
            headers_json = json.dumps(headers, ensure_ascii=False, indent=2)
            allure.attach(headers_json, "请求头", allure.attachment_type.JSON)
            # print(response.text)
            logging.info(f"登录返回信息：{response.text}")
            allure.attach(response.text, "响应信息", allure.attachment_type.JSON)

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

    @allure.title("跟单社区前端-跟单账号平仓")
    def test_close_follow(self, var_manager):
        with allure.step("1. 跟单社区前端-发送跟单账号平仓请求"):
            follow_pass_id = var_manager.get_variable("follow_pass_id")
            url = f"{URL_TOP}/blockchain/account/closeAllOrder?traderId={follow_pass_id}&including=true"

            response = requests.request("GET", url, headers=headers, data={})
            allure.attach(url, "请求URL", allure.attachment_type.TEXT)
            headers_json = json.dumps(headers, ensure_ascii=False, indent=2)
            allure.attach(headers_json, "请求头", allure.attachment_type.JSON)
            # print(response.text)
            logging.info(f"登录返回信息：{response.text}")
            allure.attach(response.text, "响应信息", allure.attachment_type.JSON)

        with allure.step("2. 返回校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "响应success字段应为true"
            )

    # @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("账号管理-持仓订单-魔术号查询-开仓前")
    def test_query_magic(self, var_manager, logged_session):
        with allure.step("1. 跟单社区后台-账号管理-持仓订单-发送魔术号查询请求"):
            trader_account = var_manager.get_variable("trader_account")
            params = {
                "_t": current_timestamp_seconds,
                "magic": trader_account,
                "column": "id",
                "order": "desc",
                "pageNo": 1,
                "pageSize": 20,
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

        with allure.step("3. 查询校验"):
            jeecg_row_key_list = self.json_utils.extract(
                response.json(),
                "$.result.records[*].jeecg_row_key",
                default=[],
                multi_match=True
            )

            if jeecg_row_key_list is None:
                allure.attach("魔术号查询结果为空", "查询结果", allure.attachment_type.TEXT)
            else:
                for jeecg_row_key in jeecg_row_key_list:
                    self.send_delete_request(
                        logged_session,
                        f'/online/cgform/api/form/402883977b38c9ca017b38c9caff0000/{jeecg_row_key}'
                    )
                    allure.attach(f"删除数据成功：{jeecg_row_key}", "删除结果", allure.attachment_type.TEXT)

    # @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("账号管理-持仓订单-账号ID查询-开仓前")
    def test_query_follow_passid(self, var_manager, logged_session):
        with allure.step("1. 跟单社区后台-账号管理-持仓订单-发送账号ID查询请求"):
            trader_pass_id = var_manager.get_variable("trader_pass_id")
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
                "$.result.records[*].trader_id",
                default=[],
                multi_match=True
            )

            if trader_id_list is None:
                allure.attach("账号ID查询结果为空", "查询结果", allure.attachment_type.TEXT)
            else:
                for trader_id in trader_id_list:
                    self.send_delete_request(
                        logged_session,
                        f'/online/cgform/api/form/402883977b38c9ca017b38c9caff0000/{trader_id}'
                    )
                    allure.attach(f"删除数据成功：{trader_id}", "删除结果", allure.attachment_type.TEXT)

    @allure.title("登录MT4账号获取token")
    def test_mt4_login(self, var_manager):
        with allure.step("MT4发送登录请求"):
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

                    with allure.step(f"第{attempt + 1}/{max_retries}次尝试"):
                        response = requests.request("GET", url, headers=headers, data={})
                        allure.attach(url, "请求URL", allure.attachment_type.TEXT)
                        headers_json = json.dumps(headers, ensure_ascii=False, indent=2)
                        allure.attach(headers_json, "请求头", allure.attachment_type.JSON)
                        # 去除可能的空白字符
                        response_text = response.text.strip()

                        logging.info(f"第{attempt + 1}/{max_retries}次登录尝试 - 响应内容: {response_text}")
                        allure.attach(response_text, "响应内容", allure.attachment_type.TEXT)

                        # 验证响应是否为有效的UUID格式token
                        if uuid_pattern.match(response_text):
                            token_mt4 = response_text
                            logging.info(f"第{attempt + 1}/{max_retries}次尝试成功 - 获取到token: {token_mt4}")
                            break
                        else:
                            logging.warning(
                                f"第{attempt + 1}/{max_retries}次尝试失败 - 无效的token格式: {response_text}")

                except Exception as e:
                    logging.error(f"第{attempt + 1}/{max_retries}次尝试发生异常: {str(e)}")

                # 如果不是最后一次尝试，等待后重试
                if attempt < max_retries - 1:
                    logging.info(f"将在{retry_interval}秒后进行第{attempt + 2}/{max_retries}次重试...")
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
        with allure.step("MT4发送开仓请求"):
            symbol = var_manager.get_variable("symbol")
            url = f"{MT4_URL}/OrderSend?id={token_mt4}&symbol={symbol}&operation=Buy&volume=0.01&placedType=Client&price=0.00"

            payload = ""
            self.response = requests.request("GET", url, headers=headers, data=payload)
            allure.attach(url, "请求URL", allure.attachment_type.TEXT)
            headers_json = json.dumps(headers, ensure_ascii=False, indent=2)
            allure.attach(headers_json, "请求头", allure.attachment_type.JSON)
            self.json_utils = JsonPathUtils()
            self.response = self.response.json()
            allure.attach(json.dumps(self.response, ensure_ascii=False, indent=2), "响应内容",
                          allure.attachment_type.JSON)

            ticket_open = self.json_utils.extract(self.response, "$.ticket")
            lots_open = self.json_utils.extract(self.response, "$.lots")
            var_manager.set_runtime_variable("ticket_open", ticket_open)
            var_manager.set_runtime_variable("lots_open", lots_open)
            print(f"ticket: {ticket_open},lots_open:{lots_open}")
            logging.info(f"ticket: {ticket_open},lots_open:{lots_open}")
            if lots_open is None or ticket_open is None:
                logging.info("开仓失败")
                # 重新开仓
                self.test_mt4_open(var_manager)
            else:
                logging.info("开仓成功")

    @allure.title("MT4平台开仓操作")
    def test_mt4_open2(self, var_manager):
        with allure.step("MT4发送开仓请求"):
            symbol = var_manager.get_variable("symbol")
            url = f"{MT4_URL}/OrderSend?id={token_mt4}&symbol={symbol}&operation=Buy&volume=0.2&placedType=Client&price=0.00"

            payload = ""
            self.response = requests.request("GET", url, headers=headers, data=payload)
            allure.attach(url, "请求URL", allure.attachment_type.TEXT)
            headers_json = json.dumps(headers, ensure_ascii=False, indent=2)
            allure.attach(headers_json, "请求头", allure.attachment_type.JSON)
            self.json_utils = JsonPathUtils()
            self.response = self.response.json()
            allure.attach(json.dumps(self.response, ensure_ascii=False, indent=2), "响应内容",
                          allure.attachment_type.JSON)

            ticket_open = self.json_utils.extract(self.response, "$.ticket")
            lots_open = self.json_utils.extract(self.response, "$.lots")
            var_manager.set_runtime_variable("ticket_open", ticket_open)
            var_manager.set_runtime_variable("lots_open", lots_open)
            print(f"ticket: {ticket_open},lots_open:{lots_open}")
            logging.info(f"ticket: {ticket_open},lots_open:{lots_open}")
            if ticket_open is None:
                logging.info("开仓失败")
                # 重新开仓
                self.test_mt4_open(var_manager)
            else:
                logging.info("开仓成功")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库提取数据-提取跟单订单号")
    def test_dbquery_openorder(self, var_manager, db_transaction):
        max_attempts = 3  # 最大查询次数
        interval = 10  # 每次查询间隔（秒）
        attempt = 0  # 当前查询次数计数器

        while attempt < max_attempts:
            attempt += 1  # 次数加1
            with allure.step(f"1. 第{attempt}/{max_attempts}次查询数据库"):
                ticket_open = var_manager.get_variable("ticket_open")

                # 数据库查询
                db_data = self.query_database_with_time(
                    db_transaction,
                    "SELECT * FROM bchain_trader_subscribe_order WHERE master_ticket = %s",
                    (ticket_open,),
                )

                if db_data:  # 如果查询到数据
                    with allure.step("2. 提取数据库中的值"):
                        slave_ticket = db_data[0]["slave_ticket"]
                        print(f"跟单账号订单号：{slave_ticket}")
                        logging.info(f"跟单账号订单号: {slave_ticket}")
                        var_manager.set_runtime_variable("slave_ticket", slave_ticket)
                    return  # 成功获取后退出函数

                # 如果未查询到数据且不是最后一次尝试，则等待后重试
                if attempt < max_attempts:
                    with allure.step(f"3. 未查询到数据，{interval}秒后重试（剩余{max_attempts - attempt}次）"):
                        time.sleep(interval)

        # 如果超过最大次数仍未查询到数据，抛出异常
        pytest.fail(f"超过最大查询次数（{max_attempts}次），未找到master_ticket={ticket_open}的订单数据")

    # @pytest.mark.skipif(True, reason="跳过此用例")
    @allure.title("MT4平台平仓操作")
    def test_mt4_close(self, var_manager, db_transaction):
        with allure.step("MT4发送平仓请求"):
            max_attempts = 3  # 最大总尝试次数
            retry_interval = 10  # 每次尝试间隔时间(秒)
            global token_mt4, headers  # 声明使用全局变量
            ticket_close = None

            # 提取登录所需变量
            uuid_pattern = re.compile(
                r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')

            for attempt in range(max_attempts):
                try:
                    with allure.step(f"1. 第{attempt + 1}/{max_attempts}次尝试"):
                        ticket_open = var_manager.get_variable("ticket_open")
                        # 检查token是否有效，无效则重新登录
                        if not token_mt4 or not uuid_pattern.match(token_mt4):
                            with allure.step("token无效或不存在，重新登录MT4"):
                                self.test_mt4_login(var_manager)  # 调用登录方法获取新token

                        # 发送平仓请求
                        url = f"{MT4_URL}/OrderClose?id={token_mt4}&ticket={ticket_open}&price=0.00"
                        self.response = requests.request("GET", url, headers=headers)
                        self.response_json = self.response.json()
                        logging.info(f"第{attempt + 1}/{max_attempts}次平仓响应: {self.response_json}")

                        allure.attach(url, "请求URL", allure.attachment_type.TEXT)
                        headers_json = json.dumps(headers, ensure_ascii=False, indent=2)
                        allure.attach(headers_json, "请求头", allure.attachment_type.JSON)
                        allure.attach(json.dumps(self.response_json, ensure_ascii=False, indent=2), "响应内容",
                                      allure.attachment_type.JSON)

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
                        logging.warning(f"第{attempt + 1}/{max_attempts}次平仓失败，未获取到平仓订单号")

                except Exception as e:
                    logging.error(f"第{attempt + 1}/{max_attempts}次平仓发生异常: {str(e)}")

                # 如果不是最后一次尝试，等待后重试
                if attempt < max_attempts - 1:
                    logging.info(f"将在{retry_interval}秒后进行第{attempt + 2}/{max_attempts}次尝试...")
                    time.sleep(retry_interval)
                    # 主动重新登录获取新token
                    with allure.step(f"准备第{attempt + 2}/{max_attempts}次尝试，重新登录MT4"):
                        self.test_mt4_login(var_manager)
                    # 重新开仓
                    with allure.step(f"准备第{attempt + 2}/{max_attempts}次尝试，重新开仓"):
                        self.test_mt4_open(var_manager)
                    # 重新提取跟单订单号
                    with allure.step(f"准备第{attempt + 2}/{max_attempts}次尝试，重新提取跟单订单号"):
                        self.test_dbquery_openorder(var_manager, db_transaction)

            # 所有尝试结束后仍失败，标记用例失败
            if ticket_close is None:
                pytest.fail(f"经过{max_attempts}次尝试（包含重新登录）后，平仓仍失败，订单号: {ticket_open}")
