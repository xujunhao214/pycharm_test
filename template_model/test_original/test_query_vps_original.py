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

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @pytest.mark.retry(n=3, delay=10)
        @allure.title("跟单管理-VPS管理-喊单者账号-开仓后")
        def test_query_opentrader_getRecordList(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                trader_account = var_manager.get_variable("trader_account")
                vpsrunIpAddr = var_manager.get_variable("vpsrunIpAddr")
                params = {
                    "_t": current_timestamp_seconds,
                    "pageNo": "1",
                    "pageSize": "50",
                    "accountLike": trader_account,
                    "serverNameLike": "",
                    "connectTraderLike": "",
                    "connected": "",
                    "runIpAddr": vpsrunIpAddr
                }
                response = self.send_get_request(
                    logged_session,
                    '/blockchain/account/getRecordList',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.searchCount",
                    True,
                    "响应searchCount字段应为true"
                )

            with allure.step(f"3. 查询校验"):
                order_size = self.json_utils.extract(response.json(), "$.result.records[0].size")
                logging.info(f"喊单者手数是: {order_size}")
                var_manager.set_runtime_variable("order_size", order_size)

                account_list = self.json_utils.extract(
                    response.json(),
                    "$.records[0].account",
                    default=[],
                    multi_match=True
                )

                if not account_list:
                    attach_body = f"账号查询[{trader_account}]，返回的account列表为空（暂无数据）"
                else:
                    attach_body = f"账号查询[{trader_account}]，返回 {len(account_list)} 条记录，account值如下：\n" + \
                                  "\n".join([f"第 {idx + 1} 条：{s}" for idx, s in enumerate(account_list)])

                allure.attach(
                    body=attach_body,
                    name=f"账号:{trader_account}查询结果",
                    attachment_type="text/plain"
                )

                for idx, account in enumerate(account_list):
                    self.verify_data(
                        actual_value=account,
                        expected_value=trader_account,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的账号应为{account}",
                        attachment_name=f"账号:{trader_account}第 {idx + 1} 条记录校验"
                    )

                    with allure.step("手数校验-MT4开仓手数和持仓订单手数"):
                        totalLots = self.json_utils.extract(response.json(), "$.records[0].totalLots")
                        logging.info(f"手数是: {totalLots}")

                        lots_open = var_manager.get_variable("lots_open")

                        self.verify_data(
                            actual_value=float(totalLots),
                            expected_value=float(lots_open),
                            op=CompareOp.EQ,
                            message=f"手数符合预期",
                            attachment_name="手数详情"
                        )
                        logger.info(f"喊单者手数：{totalLots} MT4开仓手数：{lots_open}")

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("跟单管理-VPS管理-跟单者账号-开仓后")
        def test_query_openfollow_getRecordList(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                follow_account = var_manager.get_variable("follow_account")
                vpsrunIpAddr = var_manager.get_variable("vpsrunIpAddr")
                params = {
                    "_t": current_timestamp_seconds,
                    "pageNo": "1",
                    "pageSize": "50",
                    "accountLike": follow_account,
                    "serverNameLike": "",
                    "connectTraderLike": "",
                    "connected": "",
                    "runIpAddr": vpsrunIpAddr
                }
                response = self.send_get_request(
                    logged_session,
                    '/blockchain/account/getRecordList',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.searchCount",
                    True,
                    "响应searchCount字段应为true"
                )

            with allure.step(f"3. 查询校验"):
                order_size = self.json_utils.extract(response.json(), "$.result.records[0].size")
                logging.info(f"喊单者手数是: {order_size}")
                var_manager.set_runtime_variable("order_size", order_size)

                account_list = self.json_utils.extract(
                    response.json(),
                    "$.records[0].account",
                    default=[],
                    multi_match=True
                )

                if not account_list:
                    attach_body = f"账号查询[{follow_account}]，返回的account列表为空（暂无数据）"
                else:
                    attach_body = f"账号查询[{follow_account}]，返回 {len(account_list)} 条记录，account值如下：\n" + \
                                  "\n".join([f"第 {idx + 1} 条：{s}" for idx, s in enumerate(account_list)])

                allure.attach(
                    body=attach_body,
                    name=f"账号:{follow_account}查询结果",
                    attachment_type="text/plain"
                )

                for idx, account in enumerate(account_list):
                    self.verify_data(
                        actual_value=account,
                        expected_value=follow_account,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的账号应为{account}",
                        attachment_name=f"账号:{follow_account}第 {idx + 1} 条记录校验"
                    )

                    with allure.step("手数校验-MT4开仓手数和持仓订单手数"):
                        totalLots = self.json_utils.extract(response.json(), "$.records[0].totalLots")
                        logging.info(f"手数是: {totalLots}")

                        lots_open = var_manager.get_variable("lots_open")

                        self.verify_data(
                            actual_value=float(totalLots),
                            expected_value=float(lots_open),
                            op=CompareOp.EQ,
                            message=f"手数符合预期",
                            attachment_name="手数详情"
                        )
                        logger.info(f"跟单者手数：{totalLots} MT4开仓手数：{lots_open}")

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("MT4平台平仓操作")
        def test_mt4_close(self, var_manager):
            with allure.step("1. 发送平仓请求"):
                ticket_open = var_manager.get_variable("ticket_open")
                url = f"{MT4_URL}/OrderClose?id={token_mt4}&ticket={ticket_open}&price=0.00"

                self.response = requests.request("GET", url, headers=headers)
                self.json_utils = JsonPathUtils()
                self.response = self.response.json()

            with allure.step("2. 数据校验"):
                ticket_close = self.json_utils.extract(self.response, "$.ticket")
                logging.info(f"平仓单号：{ticket_close}")

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
        @pytest.mark.retry(n=3, delay=5)
        @allure.title("跟单管理-VPS管理-喊单者账号-平仓后")
        def test_query_closetrader_getRecordList(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                trader_account = var_manager.get_variable("trader_account")
                vpsrunIpAddr = var_manager.get_variable("vpsrunIpAddr")
                params = {
                    "_t": current_timestamp_seconds,
                    "pageNo": "1",
                    "pageSize": "50",
                    "accountLike": trader_account,
                    "serverNameLike": "",
                    "connectTraderLike": "",
                    "connected": "",
                    "runIpAddr": vpsrunIpAddr
                }
                response = self.send_get_request(
                    logged_session,
                    '/blockchain/account/getRecordList',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.searchCount",
                    True,
                    "响应searchCount字段应为true"
                )

            with allure.step(f"3. 查询校验"):
                order_size = self.json_utils.extract(response.json(), "$.result.records[0].size")
                logging.info(f"喊单者手数是: {order_size}")
                var_manager.set_runtime_variable("order_size", order_size)

                account_list = self.json_utils.extract(
                    response.json(),
                    "$.records[0].account",
                    default=[],
                    multi_match=True
                )

                if not account_list:
                    attach_body = f"账号查询[{trader_account}]，返回的account列表为空（暂无数据）"
                else:
                    attach_body = f"账号查询[{trader_account}]，返回 {len(account_list)} 条记录，account值如下：\n" + \
                                  "\n".join([f"第 {idx + 1} 条：{s}" for idx, s in enumerate(account_list)])

                allure.attach(
                    body=attach_body,
                    name=f"账号:{trader_account}查询结果",
                    attachment_type="text/plain"
                )

                for idx, account in enumerate(account_list):
                    self.verify_data(
                        actual_value=account,
                        expected_value=trader_account,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的账号应为{account}",
                        attachment_name=f"账号:{trader_account}第 {idx + 1} 条记录校验"
                    )

                    with allure.step("手数校验-MT4开仓手数和持仓订单手数"):
                        totalLots = self.json_utils.extract(response.json(), "$.records[0].totalLots")
                        logging.info(f"手数是: {totalLots}")

                        self.verify_data(
                            actual_value=float(totalLots),
                            expected_value=float(0),
                            op=CompareOp.EQ,
                            message=f"手数符合预期",
                            attachment_name="手数详情"
                        )
                        logger.info(f"平仓后手数应为：0，实际是：{totalLots}")

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("跟单管理-VPS管理-跟单者账号-平仓后")
        def test_query_closefollow_getRecordList(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                follow_account = var_manager.get_variable("follow_account")
                vpsrunIpAddr = var_manager.get_variable("vpsrunIpAddr")
                params = {
                    "_t": current_timestamp_seconds,
                    "pageNo": "1",
                    "pageSize": "50",
                    "accountLike": follow_account,
                    "serverNameLike": "",
                    "connectTraderLike": "",
                    "connected": "",
                    "runIpAddr": vpsrunIpAddr
                }
                response = self.send_get_request(
                    logged_session,
                    '/blockchain/account/getRecordList',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.searchCount",
                    True,
                    "响应searchCount字段应为true"
                )

            with allure.step(f"3. 查询校验"):
                order_size = self.json_utils.extract(response.json(), "$.result.records[0].size")
                logging.info(f"喊单者手数是: {order_size}")
                var_manager.set_runtime_variable("order_size", order_size)

                account_list = self.json_utils.extract(
                    response.json(),
                    "$.records[0].account",
                    default=[],
                    multi_match=True
                )

                if not account_list:
                    attach_body = f"账号查询[{follow_account}]，返回的account列表为空（暂无数据）"
                else:
                    attach_body = f"账号查询[{follow_account}]，返回 {len(account_list)} 条记录，account值如下：\n" + \
                                  "\n".join([f"第 {idx + 1} 条：{s}" for idx, s in enumerate(account_list)])

                allure.attach(
                    body=attach_body,
                    name=f"账号:{follow_account}查询结果",
                    attachment_type="text/plain"
                )

                for idx, account in enumerate(account_list):
                    self.verify_data(
                        actual_value=account,
                        expected_value=follow_account,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的账号应为{account}",
                        attachment_name=f"账号:{follow_account}第 {idx + 1} 条记录校验"
                    )

                    with allure.step("手数校验-MT4开仓手数和持仓订单手数"):
                        totalLots = self.json_utils.extract(response.json(), "$.records[0].totalLots")
                        logging.info(f"手数是: {totalLots}")

                        self.verify_data(
                            actual_value=float(totalLots),
                            expected_value=float(0),
                            op=CompareOp.EQ,
                            message=f"手数符合预期",
                            attachment_name="手数详情"
                        )
                        logger.info(f"平仓后手数应为：0，实际是：{totalLots}")
