import time
from template_back.commons.api_base import APITestBase, CompareOp
import allure
import logging
import pytest
from template_back.VAR.VAR import *
from template_back.commons.jsonpath_utils import *
from template_back.commons.random_generator import *


@allure.feature("账号管理")
class Test_create:
    @allure.story("创建交易员账号")
    class Test_trader(APITestBase):
        # 实例化JsonPath工具类（全局复用）
        json_utils = JsonPathUtils()

        @allure.title("返佣管理-跟单分红-2级分红-USD币种")
        def test_user_list(self, var_manager, logged_session):
            with allure.step("1. 发送GET请求"):
                login_config = var_manager.get_variable("login_config")
                params = {
                    "_t": current_timestamp_seconds,
                    "page": 1,
                    "limit": 50,
                    "type": "",
                    "status": "",
                    # "dividendTimeBegin": "2025-09-04",
                    # "dividendTimeEnd": "2025-09-04",
                    "followerUser": "xujunhao2@163.com",
                    # "followerUser": "1156160434@qq.com",
                    # "followerUser": "performance",
                    "followerTa": "",
                    "dividendUser": ""
                }

                response = self.send_get_request(
                    logged_session,
                    '/agent/agentLevelDividend/page',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step("3. 数据校验"):
                response = response.json()
                prePeriodEquity = self.json_utils.extract(response, "$.result.list[0].prePeriodEquity")
                endPeriodEquity = self.json_utils.extract(response, "$.result.list[0].endPeriodEquity")
                periodProfit = self.json_utils.extract(response, "$.result.list[0].periodProfit")
                periodProfitUsd = self.json_utils.extract(response, "$.result.list[0].periodProfitUsd")
                expectDividendAmount = self.json_utils.extract(response, "$.result.list[0].expectDividendAmount")
                currency = self.json_utils.extract(response, "$.result.list[0].currency")

                # 提前预定义所有分红变量，默认值0.0
                expectDividend1 = 0.0
                expectDividend2 = 0.0
                expectDividend3 = 0.0
                expectDividend4 = 0.0

                # 提前预定义所有分红变量，默认值
                default_agent_level = "分红"

                # 币种的转换其它币种转为USD
                if currency == "USD":
                    periodP = round(float(periodProfit) * 1.0, 2)
                elif currency == "JPY":
                    periodP = round(float(periodProfit) * 0.00672, 2)
                elif currency == "AUD":
                    periodP = round(float(periodProfit) * 0.6251, 2)
                elif currency == "USC":
                    periodP = round(float(periodProfit) * 0.01, 2)

                with allure.step("验证期间盈利是否正确"):
                    pre_end = round(float(endPeriodEquity) - float(prePeriodEquity), 2)
                    self.verify_data(
                        actual_value=float(pre_end),
                        expected_value=float(periodProfit),
                        op=CompareOp.EQ,
                        rel_tol=1e-2,
                        message="期间盈利应符合预期",
                        attachment_name="期间盈利详情"
                    )
                logging.info(f"期间盈利验证通过: {periodProfit}")

                with allure.step("验证币种的转换是否正确"):
                    self.verify_data(
                        actual_value=float(periodProfitUsd),
                        expected_value=float(periodP),
                        op=CompareOp.EQ,
                        message="币种的转换应符合预期",
                        attachment_name=f"币种的转换详情,当前币种{currency}"
                    )
                logging.info(f"币种的转换验证通过：{periodProfitUsd}")

                with allure.step("验证预计分红金额是否正确"):
                    if periodProfitUsd < 0:
                        logging.info("盈利金额小于0")
                        allure.attach("盈利金额小于0,没有分红", "text/plain")
                    else:
                        dividendRate0 = self.json_utils.extract(response,
                                                                "$.result.list[0].slaveRecords[0].dividendRate")
                        dividend_rate = dividendRate0 / 100
                        expectDividend = round(float(periodProfitUsd) * dividend_rate, 2)
                        self.verify_data(
                            actual_value=float(expectDividendAmount),
                            expected_value=float(expectDividend),
                            op=CompareOp.EQ,
                            message="预计分红金额应符合预期",
                            attachment_name="预计分红金额详情"
                        )
                        logging.info(f"预计分红金额验证通过：{periodProfitUsd}")

                agentLevel = self.json_utils.extract(response, "$.result.list[0].slaveRecords[1].agentLevel")
                # 若提取结果为None或空字符串，使用默认值
                agentLevel = agentLevel if agentLevel is not None and agentLevel != "" else default_agent_level
                with allure.step(f"验证{agentLevel}金额是否正确"):
                    if agentLevel == "分红":
                        logging.info(f"{agentLevel}代理不存在")
                        allure.attach(f"{agentLevel}代理不存在", "text/plain")
                    elif periodProfitUsd < 0:
                        logging.info("盈利金额小于0")
                        allure.attach("盈利金额小于0,没有分红", "text/plain")
                    else:
                        expectDividendAmount4 = self.json_utils.extract(response,
                                                                        "$.result.list[0].slaveRecords[1].expectDividendAmount")
                        dividendRate4 = self.json_utils.extract(response,
                                                                "$.result.list[0].slaveRecords[1].dividendRate")
                        dividend_rate = dividendRate4 / 100
                        expectDividend4 = round(float(expectDividendAmount) * dividend_rate, 2)
                        self.verify_data(
                            actual_value=float(expectDividendAmount4),
                            expected_value=float(expectDividend4),
                            op=CompareOp.EQ,
                            rel_tol=1e-2,
                            message=f"{agentLevel}金额应符合预期",
                            attachment_name=f"{agentLevel}金额详情"
                        )
                        logging.info(f"{agentLevel}金额验证通过：{periodProfitUsd}")

                agentLevel2 = self.json_utils.extract(response, "$.result.list[0].slaveRecords[2].agentLevel")
                agentLevel2 = agentLevel2 if agentLevel2 is not None and agentLevel2 != "" else default_agent_level
                with allure.step(f"验证{agentLevel2}金额是否正确"):
                    if agentLevel2 == "分红":
                        logging.info(f"{agentLevel2}代理不存在")
                        allure.attach(f"{agentLevel2}代理不存在", "text/plain")
                    elif periodProfitUsd < 0:
                        logging.info("盈利金额小于0")
                        allure.attach("盈利金额小于0,没有分红", "text/plain")
                    else:
                        expectDividendAmount3 = self.json_utils.extract(response,
                                                                        "$.result.list[0].slaveRecords[2].expectDividendAmount")
                        dividendRate3 = self.json_utils.extract(response,
                                                                "$.result.list[0].slaveRecords[2].dividendRate")
                        dividend_rate = (dividendRate3 - dividendRate4) / 100
                        expectDividend3 = round(float(expectDividendAmount) * dividend_rate, 2)
                        self.verify_data(
                            actual_value=float(expectDividendAmount3),
                            expected_value=float(expectDividend3),
                            op=CompareOp.EQ,
                            rel_tol=1e-2,
                            message=f"{agentLevel2}金额应符合预期",
                            attachment_name=f"{agentLevel2}金额详情"
                        )
                        logging.info(f"3级分红金额验证通过：{periodProfitUsd}")

                agentLevel3 = self.json_utils.extract(response, "$.result.list[0].slaveRecords[3].agentLevel")
                agentLevel3 = agentLevel3 if agentLevel3 is not None and agentLevel3 != "" else default_agent_level
                with allure.step(f"验证{agentLevel3}金额是否正确"):
                    if agentLevel3 == "分红":
                        logging.info(f"{agentLevel3}代理不存在")
                        allure.attach(f"{agentLevel3}代理不存在", "text/plain")
                    elif periodProfitUsd < 0:
                        logging.info("盈利金额小于0")
                        allure.attach("盈利金额小于0,没有分红", "text/plain")
                    else:
                        expectDividendAmount2 = self.json_utils.extract(response,
                                                                        "$.result.list[0].slaveRecords[3].expectDividendAmount")
                        dividendRate2 = self.json_utils.extract(response,
                                                                "$.result.list[0].slaveRecords[3].dividendRate")
                        dividend_rate = (dividendRate2 - dividendRate3) / 100
                        expectDividend2 = round(float(expectDividendAmount) * dividend_rate, 2)
                        self.verify_data(
                            actual_value=float(expectDividendAmount2),
                            expected_value=float(expectDividend2),
                            op=CompareOp.EQ,
                            rel_tol=1e-2,
                            message=f"{agentLevel3}金额应符合预期",
                            attachment_name=f"{agentLevel3}金额详情"
                        )
                        logging.info(f"{agentLevel3}金额验证通过：{periodProfitUsd}")

                agentLevel4 = self.json_utils.extract(response, "$.result.list[0].slaveRecords[4].agentLevel")
                agentLevel4 = agentLevel4 if agentLevel4 is not None and agentLevel4 != "" else default_agent_level
                with allure.step(f"验证{agentLevel4}金额是否正确"):
                    if agentLevel4 == "分红":
                        logging.info(f"{agentLevel4}代理不存在")
                        allure.attach(f"{agentLevel4}代理不存在", "text/plain")
                    elif periodProfitUsd < 0:
                        logging.info("盈利金额小于0")
                        allure.attach("盈利金额小于0,没有分红", "text/plain")
                    else:
                        expectDividendAmount1 = self.json_utils.extract(response,
                                                                        "$.result.list[0].slaveRecords[4].expectDividendAmount")
                        dividendRate1 = self.json_utils.extract(response,
                                                                "$.result.list[0].slaveRecords[4].dividendRate")
                        dividend_rate = (dividendRate1 - dividendRate2) / 100
                        expectDividend1 = round(float(expectDividendAmount) * dividend_rate, 2)
                        self.verify_data(
                            actual_value=float(expectDividendAmount1),
                            expected_value=float(expectDividend1),
                            op=CompareOp.EQ,
                            rel_tol=1e-2,
                            message=f"{agentLevel4}金额应符合预期",
                            attachment_name=f"{agentLevel4}金额详情"
                        )
                        logging.info(f"{agentLevel4}金额验证通过：{periodProfitUsd}")

                with allure.step("验证信号源分红金额是否正确"):
                    if periodProfitUsd < 0:
                        logging.info("盈利金额小于0")
                        allure.attach("盈利金额小于0,没有分红", "text/plain")
                    else:
                        expectDividendAmount0 = self.json_utils.extract(response,
                                                                        "$.result.list[0].slaveRecords[0].expectDividendAmount")
                        expectDividend0 = round(
                            float(expectDividendAmount) - float(expectDividend1) - float(expectDividend2) - float(
                                expectDividend3) - float(expectDividend4), 2)
                        self.verify_data(
                            actual_value=float(expectDividendAmount0),
                            expected_value=float(expectDividend0),
                            op=CompareOp.EQ,
                            rel_tol=1e-2,
                            message="信号源分红金额应符合预期",
                            attachment_name="信号源分红金额详情"
                        )
                        logging.info(f"信号源分红金额验证通过：{periodProfitUsd}")

        @allure.title("返佣管理-跟单分红-4级分红-USD币种")
        def test_user_list2(self, var_manager, logged_session):
            with allure.step("1. 发送GET请求"):
                login_config = var_manager.get_variable("login_config")
                params = {
                    "_t": current_timestamp_seconds,
                    "page": 1,
                    "limit": 50,
                    "type": "",
                    "status": "",
                    # "dividendTimeBegin": "2025-09-04",
                    # "dividendTimeEnd": "2025-09-04",
                    "followerUser": "xujunhao@163.com",
                    # "followerUser": "1156160434@qq.com",
                    # "followerUser": "performance",
                    "followerTa": "",
                    "dividendUser": ""
                }

                response = self.send_get_request(
                    logged_session,
                    '/agent/agentLevelDividend/page',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step("3. 数据校验"):
                response = response.json()
                prePeriodEquity = self.json_utils.extract(response, "$.result.list[0].prePeriodEquity")
                endPeriodEquity = self.json_utils.extract(response, "$.result.list[0].endPeriodEquity")
                periodProfit = self.json_utils.extract(response, "$.result.list[0].periodProfit")
                periodProfitUsd = self.json_utils.extract(response, "$.result.list[0].periodProfitUsd")
                expectDividendAmount = self.json_utils.extract(response, "$.result.list[0].expectDividendAmount")
                currency = self.json_utils.extract(response, "$.result.list[0].currency")

                # 提前预定义所有分红变量，默认值0.0
                expectDividend1 = 0.0
                expectDividend2 = 0.0
                expectDividend3 = 0.0
                expectDividend4 = 0.0

                # 提前预定义所有分红变量，默认值
                default_agent_level = "分红"

                # 币种的转换其它币种转为USD
                if currency == "USD":
                    periodP = round(float(periodProfit) * 1.0, 2)
                elif currency == "JPY":
                    periodP = round(float(periodProfit) * 0.00672, 2)
                elif currency == "AUD":
                    periodP = round(float(periodProfit) * 0.6251, 2)
                elif currency == "USC":
                    periodP = round(float(periodProfit) * 0.01, 2)

                with allure.step("验证期间盈利是否正确"):
                    pre_end = round(float(endPeriodEquity) - float(prePeriodEquity), 2)
                    self.verify_data(
                        actual_value=float(pre_end),
                        expected_value=float(periodProfit),
                        op=CompareOp.EQ,
                        rel_tol=1e-2,
                        message="期间盈利应符合预期",
                        attachment_name="期间盈利详情"
                    )
                logging.info(f"期间盈利验证通过: {periodProfit}")

                with allure.step("验证币种的转换是否正确"):
                    self.verify_data(
                        actual_value=float(periodProfitUsd),
                        expected_value=float(periodP),
                        op=CompareOp.EQ,
                        message="币种的转换应符合预期",
                        attachment_name=f"币种的转换详情,当前币种{currency}"
                    )
                logging.info(f"币种的转换验证通过：{periodProfitUsd}")

                with allure.step("验证预计分红金额是否正确"):
                    if periodProfitUsd < 0:
                        logging.info("盈利金额小于0")
                        allure.attach("盈利金额小于0,没有分红", "text/plain")
                    else:
                        dividendRate0 = self.json_utils.extract(response,
                                                                "$.result.list[0].slaveRecords[0].dividendRate")
                        dividend_rate = dividendRate0 / 100
                        expectDividend = round(float(periodProfitUsd) * dividend_rate, 2)
                        self.verify_data(
                            actual_value=float(expectDividendAmount),
                            expected_value=float(expectDividend),
                            op=CompareOp.EQ,
                            message="预计分红金额应符合预期",
                            attachment_name="预计分红金额详情"
                        )
                        logging.info(f"预计分红金额验证通过：{periodProfitUsd}")

                agentLevel = self.json_utils.extract(response, "$.result.list[0].slaveRecords[1].agentLevel")
                # 若提取结果为None或空字符串，使用默认值
                agentLevel = agentLevel if agentLevel is not None and agentLevel != "" else default_agent_level
                with allure.step(f"验证{agentLevel}金额是否正确"):
                    if agentLevel == "分红":
                        logging.info(f"{agentLevel}代理不存在")
                        allure.attach(f"{agentLevel}代理不存在", "text/plain")
                    elif periodProfitUsd < 0:
                        logging.info("盈利金额小于0")
                        allure.attach("盈利金额小于0,没有分红", "text/plain")
                    else:
                        expectDividendAmount4 = self.json_utils.extract(response,
                                                                        "$.result.list[0].slaveRecords[1].expectDividendAmount")
                        dividendRate4 = self.json_utils.extract(response,
                                                                "$.result.list[0].slaveRecords[1].dividendRate")
                        dividend_rate = dividendRate4 / 100
                        expectDividend4 = round(float(expectDividendAmount) * dividend_rate, 2)
                        self.verify_data(
                            actual_value=float(expectDividendAmount4),
                            expected_value=float(expectDividend4),
                            op=CompareOp.EQ,
                            rel_tol=1e-2,
                            message=f"{agentLevel}金额应符合预期",
                            attachment_name=f"{agentLevel}金额详情"
                        )
                        logging.info(f"{agentLevel}金额验证通过：{periodProfitUsd}")

                agentLevel2 = self.json_utils.extract(response, "$.result.list[0].slaveRecords[2].agentLevel")
                agentLevel2 = agentLevel2 if agentLevel2 is not None and agentLevel2 != "" else default_agent_level
                with allure.step(f"验证{agentLevel2}金额是否正确"):
                    if agentLevel2 == "分红":
                        logging.info(f"{agentLevel2}代理不存在")
                        allure.attach(f"{agentLevel2}代理不存在", "text/plain")
                    elif periodProfitUsd < 0:
                        logging.info("盈利金额小于0")
                        allure.attach("盈利金额小于0,没有分红", "text/plain")
                    else:
                        expectDividendAmount3 = self.json_utils.extract(response,
                                                                        "$.result.list[0].slaveRecords[2].expectDividendAmount")
                        dividendRate3 = self.json_utils.extract(response,
                                                                "$.result.list[0].slaveRecords[2].dividendRate")
                        dividend_rate = (dividendRate3 - dividendRate4) / 100
                        expectDividend3 = round(float(expectDividendAmount) * dividend_rate, 2)
                        self.verify_data(
                            actual_value=float(expectDividendAmount3),
                            expected_value=float(expectDividend3),
                            op=CompareOp.EQ,
                            rel_tol=1e-2,
                            message=f"{agentLevel2}金额应符合预期",
                            attachment_name=f"{agentLevel2}金额详情"
                        )
                        logging.info(f"3级分红金额验证通过：{periodProfitUsd}")

                agentLevel3 = self.json_utils.extract(response, "$.result.list[0].slaveRecords[3].agentLevel")
                agentLevel3 = agentLevel3 if agentLevel3 is not None and agentLevel3 != "" else default_agent_level
                with allure.step(f"验证{agentLevel3}金额是否正确"):
                    if agentLevel3 == "分红":
                        logging.info(f"{agentLevel3}代理不存在")
                        allure.attach(f"{agentLevel3}代理不存在", "text/plain")
                    elif periodProfitUsd < 0:
                        logging.info("盈利金额小于0")
                        allure.attach("盈利金额小于0,没有分红", "text/plain")
                    else:
                        expectDividendAmount2 = self.json_utils.extract(response,
                                                                        "$.result.list[0].slaveRecords[3].expectDividendAmount")
                        dividendRate2 = self.json_utils.extract(response,
                                                                "$.result.list[0].slaveRecords[3].dividendRate")
                        dividend_rate = (dividendRate2 - dividendRate3) / 100
                        expectDividend2 = round(float(expectDividendAmount) * dividend_rate, 2)
                        self.verify_data(
                            actual_value=float(expectDividendAmount2),
                            expected_value=float(expectDividend2),
                            op=CompareOp.EQ,
                            rel_tol=1e-2,
                            message=f"{agentLevel3}金额应符合预期",
                            attachment_name=f"{agentLevel3}金额详情"
                        )
                        logging.info(f"{agentLevel3}金额验证通过：{periodProfitUsd}")

                agentLevel4 = self.json_utils.extract(response, "$.result.list[0].slaveRecords[4].agentLevel")
                agentLevel4 = agentLevel4 if agentLevel4 is not None and agentLevel4 != "" else default_agent_level
                with allure.step(f"验证{agentLevel4}金额是否正确"):
                    if agentLevel4 == "分红":
                        logging.info(f"{agentLevel4}代理不存在")
                        allure.attach(f"{agentLevel4}代理不存在", "text/plain")
                    elif periodProfitUsd < 0:
                        logging.info("盈利金额小于0")
                        allure.attach("盈利金额小于0,没有分红", "text/plain")
                    else:
                        expectDividendAmount1 = self.json_utils.extract(response,
                                                                        "$.result.list[0].slaveRecords[4].expectDividendAmount")
                        dividendRate1 = self.json_utils.extract(response,
                                                                "$.result.list[0].slaveRecords[4].dividendRate")
                        dividend_rate = (dividendRate1 - dividendRate2) / 100
                        expectDividend1 = round(float(expectDividendAmount) * dividend_rate, 2)
                        self.verify_data(
                            actual_value=float(expectDividendAmount1),
                            expected_value=float(expectDividend1),
                            op=CompareOp.EQ,
                            rel_tol=1e-2,
                            message=f"{agentLevel4}金额应符合预期",
                            attachment_name=f"{agentLevel4}金额详情"
                        )
                        logging.info(f"{agentLevel4}金额验证通过：{periodProfitUsd}")

                with allure.step("验证信号源分红金额是否正确"):
                    if periodProfitUsd < 0:
                        logging.info("盈利金额小于0")
                        allure.attach("盈利金额小于0,没有分红", "text/plain")
                    else:
                        expectDividendAmount0 = self.json_utils.extract(response,
                                                                        "$.result.list[0].slaveRecords[0].expectDividendAmount")
                        expectDividend0 = round(
                            float(expectDividendAmount) - float(expectDividend1) - float(expectDividend2) - float(
                                expectDividend3) - float(expectDividend4), 2)
                        self.verify_data(
                            actual_value=float(expectDividendAmount0),
                            expected_value=float(expectDividend0),
                            op=CompareOp.EQ,
                            rel_tol=1e-2,
                            message="信号源分红金额应符合预期",
                            attachment_name="信号源分红金额详情"
                        )
                        logging.info(f"信号源分红金额验证通过：{periodProfitUsd}")

        @allure.title("返佣管理-跟单分红-4级分红-AUD币种")
        def test_user_list3(self, var_manager, logged_session):
            with allure.step("1. 发送GET请求"):
                login_config = var_manager.get_variable("login_config")
                params = {
                    "_t": current_timestamp_seconds,
                    "page": 1,
                    "limit": 50,
                    "type": "",
                    "status": "",
                    "dividendTimeBegin": "2025-09-04",
                    "dividendTimeEnd": "2025-09-04",
                    # "followerUser": "xujunhao@163.com",
                    "followerUser": "1156160434@qq.com",
                    # "followerUser": "performance",
                    "followerTa": "",
                    "dividendUser": ""
                }

                response = self.send_get_request(
                    logged_session,
                    '/agent/agentLevelDividend/page',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step("3. 数据校验"):
                response = response.json()
                prePeriodEquity = self.json_utils.extract(response, "$.result.list[0].prePeriodEquity")
                endPeriodEquity = self.json_utils.extract(response, "$.result.list[0].endPeriodEquity")
                periodProfit = self.json_utils.extract(response, "$.result.list[0].periodProfit")
                periodProfitUsd = self.json_utils.extract(response, "$.result.list[0].periodProfitUsd")
                expectDividendAmount = self.json_utils.extract(response, "$.result.list[0].expectDividendAmount")
                currency = self.json_utils.extract(response, "$.result.list[0].currency")

                # 提前预定义所有分红变量，默认值0.0
                expectDividend1 = 0.0
                expectDividend2 = 0.0
                expectDividend3 = 0.0
                expectDividend4 = 0.0

                # 提前预定义所有分红变量，默认值
                default_agent_level = "分红"

                # 币种的转换其它币种转为USD
                if currency == "USD":
                    periodP = round(float(periodProfit) * 1.0, 2)
                elif currency == "JPY":
                    periodP = round(float(periodProfit) * 0.00672, 2)
                elif currency == "AUD":
                    periodP = round(float(periodProfit) * 0.6251, 2)
                elif currency == "USC":
                    periodP = round(float(periodProfit) * 0.01, 2)

                with allure.step("验证期间盈利是否正确"):
                    pre_end = round(float(endPeriodEquity) - float(prePeriodEquity), 2)
                    self.verify_data(
                        actual_value=float(pre_end),
                        expected_value=float(periodProfit),
                        op=CompareOp.EQ,
                        rel_tol=1e-2,
                        message="期间盈利应符合预期",
                        attachment_name="期间盈利详情"
                    )
                logging.info(f"期间盈利验证通过: {periodProfit}")

                with allure.step("验证币种的转换是否正确"):
                    self.verify_data(
                        actual_value=float(periodProfitUsd),
                        expected_value=float(periodP),
                        op=CompareOp.EQ,
                        message="币种的转换应符合预期",
                        attachment_name=f"币种的转换详情,当前币种{currency}"
                    )
                logging.info(f"币种的转换验证通过：{periodProfitUsd}")

                with allure.step("验证预计分红金额是否正确"):
                    if periodProfitUsd < 0:
                        logging.info("盈利金额小于0")
                        allure.attach("盈利金额小于0,没有分红", "text/plain")
                    else:
                        dividendRate0 = self.json_utils.extract(response,
                                                                "$.result.list[0].slaveRecords[0].dividendRate")
                        dividend_rate = dividendRate0 / 100
                        expectDividend = round(float(periodProfitUsd) * dividend_rate, 2)
                        self.verify_data(
                            actual_value=float(expectDividendAmount),
                            expected_value=float(expectDividend),
                            op=CompareOp.EQ,
                            message="预计分红金额应符合预期",
                            attachment_name="预计分红金额详情"
                        )
                        logging.info(f"预计分红金额验证通过：{periodProfitUsd}")

                agentLevel = self.json_utils.extract(response, "$.result.list[0].slaveRecords[1].agentLevel")
                # 若提取结果为None或空字符串，使用默认值
                agentLevel = agentLevel if agentLevel is not None and agentLevel != "" else default_agent_level
                with allure.step(f"验证{agentLevel}金额是否正确"):
                    if agentLevel == "分红":
                        logging.info(f"{agentLevel}代理不存在")
                        allure.attach(f"{agentLevel}代理不存在", "text/plain")
                    elif periodProfitUsd < 0:
                        logging.info("盈利金额小于0")
                        allure.attach("盈利金额小于0,没有分红", "text/plain")
                    else:
                        expectDividendAmount4 = self.json_utils.extract(response,
                                                                        "$.result.list[0].slaveRecords[1].expectDividendAmount")
                        dividendRate4 = self.json_utils.extract(response,
                                                                "$.result.list[0].slaveRecords[1].dividendRate")
                        dividend_rate = dividendRate4 / 100
                        expectDividend4 = round(float(expectDividendAmount) * dividend_rate, 2)
                        self.verify_data(
                            actual_value=float(expectDividendAmount4),
                            expected_value=float(expectDividend4),
                            op=CompareOp.EQ,
                            rel_tol=1e-2,
                            message=f"{agentLevel}金额应符合预期",
                            attachment_name=f"{agentLevel}金额详情"
                        )
                        logging.info(f"{agentLevel}金额验证通过：{periodProfitUsd}")

                agentLevel2 = self.json_utils.extract(response, "$.result.list[0].slaveRecords[2].agentLevel")
                agentLevel2 = agentLevel2 if agentLevel2 is not None and agentLevel2 != "" else default_agent_level
                with allure.step(f"验证{agentLevel2}金额是否正确"):
                    if agentLevel2 == "分红":
                        logging.info(f"{agentLevel2}代理不存在")
                        allure.attach(f"{agentLevel2}代理不存在", "text/plain")
                    elif periodProfitUsd < 0:
                        logging.info("盈利金额小于0")
                        allure.attach("盈利金额小于0,没有分红", "text/plain")
                    else:
                        expectDividendAmount3 = self.json_utils.extract(response,
                                                                        "$.result.list[0].slaveRecords[2].expectDividendAmount")
                        dividendRate3 = self.json_utils.extract(response,
                                                                "$.result.list[0].slaveRecords[2].dividendRate")
                        dividend_rate = (dividendRate3 - dividendRate4) / 100
                        expectDividend3 = round(float(expectDividendAmount) * dividend_rate, 2)
                        self.verify_data(
                            actual_value=float(expectDividendAmount3),
                            expected_value=float(expectDividend3),
                            op=CompareOp.EQ,
                            rel_tol=1e-2,
                            message=f"{agentLevel2}金额应符合预期",
                            attachment_name=f"{agentLevel2}金额详情"
                        )
                        logging.info(f"3级分红金额验证通过：{periodProfitUsd}")

                agentLevel3 = self.json_utils.extract(response, "$.result.list[0].slaveRecords[3].agentLevel")
                agentLevel3 = agentLevel3 if agentLevel3 is not None and agentLevel3 != "" else default_agent_level
                with allure.step(f"验证{agentLevel3}金额是否正确"):
                    if agentLevel3 == "分红":
                        logging.info(f"{agentLevel3}代理不存在")
                        allure.attach(f"{agentLevel3}代理不存在", "text/plain")
                    elif periodProfitUsd < 0:
                        logging.info("盈利金额小于0")
                        allure.attach("盈利金额小于0,没有分红", "text/plain")
                    else:
                        expectDividendAmount2 = self.json_utils.extract(response,
                                                                        "$.result.list[0].slaveRecords[3].expectDividendAmount")
                        dividendRate2 = self.json_utils.extract(response,
                                                                "$.result.list[0].slaveRecords[3].dividendRate")
                        dividend_rate = (dividendRate2 - dividendRate3) / 100
                        expectDividend2 = round(float(expectDividendAmount) * dividend_rate, 2)
                        self.verify_data(
                            actual_value=float(expectDividendAmount2),
                            expected_value=float(expectDividend2),
                            op=CompareOp.EQ,
                            rel_tol=1e-2,
                            message=f"{agentLevel3}金额应符合预期",
                            attachment_name=f"{agentLevel3}金额详情"
                        )
                        logging.info(f"{agentLevel3}金额验证通过：{periodProfitUsd}")

                agentLevel4 = self.json_utils.extract(response, "$.result.list[0].slaveRecords[4].agentLevel")
                agentLevel4 = agentLevel4 if agentLevel4 is not None and agentLevel4 != "" else default_agent_level
                with allure.step(f"验证{agentLevel4}金额是否正确"):
                    if agentLevel4 == "分红":
                        logging.info(f"{agentLevel4}代理不存在")
                        allure.attach(f"{agentLevel4}代理不存在", "text/plain")
                    elif periodProfitUsd < 0:
                        logging.info("盈利金额小于0")
                        allure.attach("盈利金额小于0,没有分红", "text/plain")
                    else:
                        expectDividendAmount1 = self.json_utils.extract(response,
                                                                        "$.result.list[0].slaveRecords[4].expectDividendAmount")
                        dividendRate1 = self.json_utils.extract(response,
                                                                "$.result.list[0].slaveRecords[4].dividendRate")
                        dividend_rate = (dividendRate1 - dividendRate2) / 100
                        expectDividend1 = round(float(expectDividendAmount) * dividend_rate, 2)
                        self.verify_data(
                            actual_value=float(expectDividendAmount1),
                            expected_value=float(expectDividend1),
                            op=CompareOp.EQ,
                            rel_tol=1e-2,
                            message=f"{agentLevel4}金额应符合预期",
                            attachment_name=f"{agentLevel4}金额详情"
                        )
                        logging.info(f"{agentLevel4}金额验证通过：{periodProfitUsd}")

                with allure.step("验证信号源分红金额是否正确"):
                    if periodProfitUsd < 0:
                        logging.info("盈利金额小于0")
                        allure.attach("盈利金额小于0,没有分红", "text/plain")
                    else:
                        expectDividendAmount0 = self.json_utils.extract(response,
                                                                        "$.result.list[0].slaveRecords[0].expectDividendAmount")
                        expectDividend0 = round(
                            float(expectDividendAmount) - float(expectDividend1) - float(expectDividend2) - float(
                                expectDividend3) - float(expectDividend4), 2)
                        self.verify_data(
                            actual_value=float(expectDividendAmount0),
                            expected_value=float(expectDividend0),
                            op=CompareOp.EQ,
                            rel_tol=1e-2,
                            message="信号源分红金额应符合预期",
                            attachment_name="信号源分红金额详情"
                        )
                        logging.info(f"信号源分红金额验证通过：{periodProfitUsd}")

        @allure.title("返佣管理-跟单分红-没有代理-USD币种")
        def test_user_list4(self, var_manager, logged_session):
            with allure.step("1. 发送GET请求"):
                login_config = var_manager.get_variable("login_config")
                params = {
                    "_t": current_timestamp_seconds,
                    "page": 1,
                    "limit": 50,
                    "type": "",
                    "status": "",
                    "dividendTimeBegin": "2025-09-09",
                    "dividendTimeEnd": "2025-09-09",
                    "followerUser": "performance",
                    # "followerUser": "1156160434@qq.com",
                    # "followerUser": "performance",
                    "followerTa": "20893971",
                    "dividendUser": ""
                }

                response = self.send_get_request(
                    logged_session,
                    '/agent/agentLevelDividend/page',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            with allure.step("3. 数据校验"):
                response = response.json()
                prePeriodEquity = self.json_utils.extract(response, "$.result.list[0].prePeriodEquity")
                endPeriodEquity = self.json_utils.extract(response, "$.result.list[0].endPeriodEquity")
                periodProfit = self.json_utils.extract(response, "$.result.list[0].periodProfit")
                periodProfitUsd = self.json_utils.extract(response, "$.result.list[0].periodProfitUsd")
                expectDividendAmount = self.json_utils.extract(response, "$.result.list[0].expectDividendAmount")
                currency = self.json_utils.extract(response, "$.result.list[0].currency")

                # 提前预定义所有分红变量，默认值0.0
                expectDividend1 = 0.0
                expectDividend2 = 0.0
                expectDividend3 = 0.0
                expectDividend4 = 0.0

                # 提前预定义所有分红变量，默认值
                default_agent_level = "分红"

                # 币种的转换其它币种转为USD
                if currency == "USD":
                    periodP = round(float(periodProfit) * 1.0, 2)
                elif currency == "JPY":
                    periodP = round(float(periodProfit) * 0.00672, 2)
                elif currency == "AUD":
                    periodP = round(float(periodProfit) * 0.6251, 2)
                elif currency == "USC":
                    periodP = round(float(periodProfit) * 0.01, 2)

                with allure.step("验证期间盈利是否正确"):
                    pre_end = round(float(endPeriodEquity) - float(prePeriodEquity), 2)
                    self.verify_data(
                        actual_value=float(pre_end),
                        expected_value=float(periodProfit),
                        op=CompareOp.EQ,
                        rel_tol=1e-2,
                        message="期间盈利应符合预期",
                        attachment_name="期间盈利详情"
                    )
                logging.info(f"期间盈利验证通过: {periodProfit}")

                with allure.step("验证币种的转换是否正确"):
                    self.verify_data(
                        actual_value=float(periodProfitUsd),
                        expected_value=float(periodP),
                        op=CompareOp.EQ,
                        message="币种的转换应符合预期",
                        attachment_name=f"币种的转换详情,当前币种{currency}"
                    )
                logging.info(f"币种的转换验证通过：{periodProfitUsd}")

                with allure.step("验证预计分红金额是否正确"):
                    if periodProfitUsd < 0:
                        logging.info("盈利金额小于0")
                        allure.attach("盈利金额小于0,没有分红", "text/plain")
                    else:
                        dividendRate0 = self.json_utils.extract(response,
                                                                "$.result.list[0].slaveRecords[0].dividendRate")
                        dividend_rate = dividendRate0 / 100
                        expectDividend = round(float(periodProfitUsd) * dividend_rate, 2)
                        self.verify_data(
                            actual_value=float(expectDividendAmount),
                            expected_value=float(expectDividend),
                            op=CompareOp.EQ,
                            message="预计分红金额应符合预期",
                            attachment_name="预计分红金额详情"
                        )
                        logging.info(f"预计分红金额验证通过：{periodProfitUsd}")

                agentLevel = self.json_utils.extract(response, "$.result.list[0].slaveRecords[1].agentLevel")
                # 若提取结果为None或空字符串，使用默认值
                agentLevel = agentLevel if agentLevel is not None and agentLevel != "" else default_agent_level
                with allure.step(f"验证{agentLevel}金额是否正确"):
                    if agentLevel == "分红":
                        logging.info(f"{agentLevel}代理不存在")
                        allure.attach(f"{agentLevel}代理不存在", "text/plain")
                    elif periodProfitUsd < 0:
                        logging.info("盈利金额小于0")
                        allure.attach("盈利金额小于0,没有分红", "text/plain")
                    else:
                        expectDividendAmount4 = self.json_utils.extract(response,
                                                                        "$.result.list[0].slaveRecords[1].expectDividendAmount")
                        dividendRate4 = self.json_utils.extract(response,
                                                                "$.result.list[0].slaveRecords[1].dividendRate")
                        dividend_rate = dividendRate4 / 100
                        expectDividend4 = round(float(expectDividendAmount) * dividend_rate, 2)
                        self.verify_data(
                            actual_value=float(expectDividendAmount4),
                            expected_value=float(expectDividend4),
                            op=CompareOp.EQ,
                            rel_tol=1e-2,
                            message=f"{agentLevel}金额应符合预期",
                            attachment_name=f"{agentLevel}金额详情"
                        )
                        logging.info(f"{agentLevel}金额验证通过：{periodProfitUsd}")

                agentLevel2 = self.json_utils.extract(response, "$.result.list[0].slaveRecords[2].agentLevel")
                agentLevel2 = agentLevel2 if agentLevel2 is not None and agentLevel2 != "" else default_agent_level
                with allure.step(f"验证{agentLevel2}金额是否正确"):
                    if agentLevel2 == "分红":
                        logging.info(f"{agentLevel2}代理不存在")
                        allure.attach(f"{agentLevel2}代理不存在", "text/plain")
                    elif periodProfitUsd < 0:
                        logging.info("盈利金额小于0")
                        allure.attach("盈利金额小于0,没有分红", "text/plain")
                    else:
                        expectDividendAmount3 = self.json_utils.extract(response,
                                                                        "$.result.list[0].slaveRecords[2].expectDividendAmount")
                        dividendRate3 = self.json_utils.extract(response,
                                                                "$.result.list[0].slaveRecords[2].dividendRate")
                        dividend_rate = (dividendRate3 - dividendRate4) / 100
                        expectDividend3 = round(float(expectDividendAmount) * dividend_rate, 2)
                        self.verify_data(
                            actual_value=float(expectDividendAmount3),
                            expected_value=float(expectDividend3),
                            op=CompareOp.EQ,
                            rel_tol=1e-2,
                            message=f"{agentLevel2}金额应符合预期",
                            attachment_name=f"{agentLevel2}金额详情"
                        )
                        logging.info(f"3级分红金额验证通过：{periodProfitUsd}")

                agentLevel3 = self.json_utils.extract(response, "$.result.list[0].slaveRecords[3].agentLevel")
                agentLevel3 = agentLevel3 if agentLevel3 is not None and agentLevel3 != "" else default_agent_level
                with allure.step(f"验证{agentLevel3}金额是否正确"):
                    if agentLevel3 == "分红":
                        logging.info(f"{agentLevel3}代理不存在")
                        allure.attach(f"{agentLevel3}代理不存在", "text/plain")
                    elif periodProfitUsd < 0:
                        logging.info("盈利金额小于0")
                        allure.attach("盈利金额小于0,没有分红", "text/plain")
                    else:
                        expectDividendAmount2 = self.json_utils.extract(response,
                                                                        "$.result.list[0].slaveRecords[3].expectDividendAmount")
                        dividendRate2 = self.json_utils.extract(response,
                                                                "$.result.list[0].slaveRecords[3].dividendRate")
                        dividend_rate = (dividendRate2 - dividendRate3) / 100
                        expectDividend2 = round(float(expectDividendAmount) * dividend_rate, 2)
                        self.verify_data(
                            actual_value=float(expectDividendAmount2),
                            expected_value=float(expectDividend2),
                            op=CompareOp.EQ,
                            rel_tol=1e-2,
                            message=f"{agentLevel3}金额应符合预期",
                            attachment_name=f"{agentLevel3}金额详情"
                        )
                        logging.info(f"{agentLevel3}金额验证通过：{periodProfitUsd}")

                agentLevel4 = self.json_utils.extract(response, "$.result.list[0].slaveRecords[4].agentLevel")
                agentLevel4 = agentLevel4 if agentLevel4 is not None and agentLevel4 != "" else default_agent_level
                with allure.step(f"验证{agentLevel4}金额是否正确"):
                    if agentLevel4 == "分红":
                        logging.info(f"{agentLevel4}代理不存在")
                        allure.attach(f"{agentLevel4}代理不存在", "text/plain")
                    elif periodProfitUsd < 0:
                        logging.info("盈利金额小于0")
                        allure.attach("盈利金额小于0,没有分红", "text/plain")
                    else:
                        expectDividendAmount1 = self.json_utils.extract(response,
                                                                        "$.result.list[0].slaveRecords[4].expectDividendAmount")
                        dividendRate1 = self.json_utils.extract(response,
                                                                "$.result.list[0].slaveRecords[4].dividendRate")
                        dividend_rate = (dividendRate1 - dividendRate2) / 100
                        expectDividend1 = round(float(expectDividendAmount) * dividend_rate, 2)
                        self.verify_data(
                            actual_value=float(expectDividendAmount1),
                            expected_value=float(expectDividend1),
                            op=CompareOp.EQ,
                            rel_tol=1e-2,
                            message=f"{agentLevel4}金额应符合预期",
                            attachment_name=f"{agentLevel4}金额详情"
                        )
                        logging.info(f"{agentLevel4}金额验证通过：{periodProfitUsd}")

                with allure.step("验证信号源分红金额是否正确"):
                    if periodProfitUsd < 0:
                        logging.info("盈利金额小于0")
                        allure.attach("盈利金额小于0,没有分红", "text/plain")
                    else:
                        expectDividendAmount0 = self.json_utils.extract(response,
                                                                        "$.result.list[0].slaveRecords[0].expectDividendAmount")
                        expectDividend0 = round(
                            float(expectDividendAmount) - float(expectDividend1) - float(expectDividend2) - float(
                                expectDividend3) - float(expectDividend4), 2)
                        self.verify_data(
                            actual_value=float(expectDividendAmount0),
                            expected_value=float(expectDividend0),
                            op=CompareOp.EQ,
                            rel_tol=1e-2,
                            message="信号源分红金额应符合预期",
                            attachment_name="信号源分红金额详情"
                        )
                        logging.info(f"信号源分红金额验证通过：{periodProfitUsd}")
