import time
from template.commons.api_base import APITestBase, CompareOp
import allure
import logging
import pytest
from template.VAR.VAR import *
from template.commons.jsonpath_utils import *
from template.commons.random_generator import *


@allure.feature("返佣管理-跟单分红")
class Test_create:
    class Test_trader(APITestBase):
        json_utils = JsonPathUtils()

        # 定义所有用例的请求参数
        case_params_list = [
            {
                "_t": current_timestamp_seconds,
                "page": 1,
                "limit": 20,
                "type": "",
                "status": "",
                "dividendTimeBegin": dividendTime,
                "dividendTimeEnd": dividendTime,
                "followerUser": "xujunhao@163.com",
                "followerTa": "301388048",
                "dividendUser": ""
            },
            {
                "_t": current_timestamp_seconds,
                "page": 1,
                "limit": 20,
                "type": "",
                "status": "",
                "dividendTimeBegin": dividendTime,
                "dividendTimeEnd": dividendTime,
                "followerUser": "xujunhao2@163.com",
                "followerTa": "301387254",
                "dividendUser": ""
            },
            {
                "_t": current_timestamp_seconds,
                "page": 1,
                "limit": 20,
                "type": "",
                "status": "",
                "dividendTimeBegin": dividendTime,
                "dividendTimeEnd": dividendTime,
                "followerUser": "xujunhao3@163.com",
                "followerTa": "301388062",
                "dividendUser": ""
            },
            {
                "_t": current_timestamp_seconds,
                "page": 1,
                "limit": 20,
                "type": "",
                "status": "",
                "dividendTimeBegin": dividendTime,
                "dividendTimeEnd": dividendTime,
                "followerUser": "xujunhao4@163.com",
                "followerTa": "301388316",
                "dividendUser": ""
            },
            {
                "_t": current_timestamp_seconds,
                "page": 1,
                "limit": 20,
                "type": "",
                "status": "",
                "dividendTimeBegin": dividendTime,
                "dividendTimeEnd": dividendTime,
                "followerUser": "xujunhao5@163.com",
                "followerTa": "301388532",
                "dividendUser": ""
            },
            {
                "_t": current_timestamp_seconds,
                "page": 1,
                "limit": 20,
                "type": "",
                "status": "",
                "dividendTimeBegin": dividendTime,
                "dividendTimeEnd": dividendTime,
                "followerUser": "xujunhao5@163.com",
                "followerTa": "2088767546",
                "dividendUser": ""
            },
            {
                "_t": current_timestamp_seconds,
                "page": 1,
                "limit": 20,
                "type": "",
                "status": "",
                "dividendTimeBegin": dividendTime,
                "dividendTimeEnd": dividendTime,
                "followerUser": "xujunhao5@163.com",
                "followerTa": "2088767545",
                "dividendUser": ""
            }
        ]

        @allure.title("返佣管理-跟单分红-没有代理-USD币种")
        @pytest.mark.parametrize("case_params", [case_params_list[0]])
        def test_agent_dividend_no_agent(self, var_manager, logged_session, case_params):
            self._run_test(case_params, logged_session)

        @allure.title("返佣管理-跟单分红-1级代理-USD币种")
        @pytest.mark.parametrize("case_params", [case_params_list[1]])
        def test_agent_dividend_1level_usd(self, var_manager, logged_session, case_params):
            self._run_test(case_params, logged_session)

        @allure.title("返佣管理-跟单分红-2级代理-USD币种")
        @pytest.mark.parametrize("case_params", [case_params_list[2]])
        def test_agent_dividend_2level_usd(self, var_manager, logged_session, case_params):
            self._run_test(case_params, logged_session)

        @allure.title("返佣管理-跟单分红-3级代理-USD币种")
        @pytest.mark.parametrize("case_params", [case_params_list[3]])
        def test_agent_dividend_3level_usd(self, var_manager, logged_session, case_params):
            self._run_test(case_params, logged_session)

        @allure.title("返佣管理-跟单分红-4级代理-USD币种")
        @pytest.mark.parametrize("case_params", [case_params_list[4]])
        def test_agent_dividend_4level_usd(self, var_manager, logged_session, case_params):
            self._run_test(case_params, logged_session)

        @allure.title("返佣管理-跟单分红-4级代理-AUD币种")
        @pytest.mark.parametrize("case_params", [case_params_list[5]])
        def test_agent_dividend_4level_aud(self, var_manager, logged_session, case_params):
            self._run_test(case_params, logged_session)

        @allure.title("返佣管理-跟单分红-4级代理-JPY币种")
        @pytest.mark.parametrize("case_params", [case_params_list[6]])
        def test_agent_dividend_4level_jpy(self, var_manager, logged_session, case_params):
            self._run_test(case_params, logged_session)

        # 公共测试逻辑（抽取复用）
        def _run_test(self, case_params, logged_session):
            with allure.step("1. 构造参数并发送GET请求"):
                response = self.send_get_request(
                    logged_session,
                    '/agent/agentLevelDividend/page',
                    params=case_params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

            # -------------------------- 新增：slaveRecords排序逻辑 --------------------------
            # 1. 先将response转为json对象
            response = response.json()
            # 2. 提取slaveRecords列表（兼容空列表场景）
            slave_records = self.json_utils.extract(response, "$.result.list[0].slaveRecords") or []
            # 3. 按dividendType排序：0在前，1在后（核心排序逻辑）
            if slave_records:
                sorted_slave_records = sorted(
                    slave_records,
                    key=lambda x: x.get("dividendType", 0)  # 无dividendType时默认归为0（信号源）
                )
                # 4. 将排序后的列表放回response_json，覆盖原slaveRecords
                response["result"]["list"][0]["slaveRecords"] = sorted_slave_records
                # 日志打印排序结果（便于调试）
                logging.info(f"slaveRecords排序完成："
                             f"原顺序dividendType={[r.get('dividendType') for r in slave_records]}, "
                             f"排序后dividendType={[r.get('dividendType') for r in sorted_slave_records]}")
                # 附加排序对比到Allure报告（可选，便于定位问题）
                allure.attach(
                    f"排序前dividendType: {[r.get('dividendType') for r in slave_records]}\n"
                    f"排序后dividendType: {[r.get('dividendType') for r in sorted_slave_records]}",
                    "slaveRecords排序对比",
                    allure.attachment_type.TEXT
                )
            # -----------------------------------------------------------------------------

            with allure.step("3. 数据校验"):
                prePeriodEquity = self.json_utils.extract(response, "$.result.list[0].prePeriodEquity")
                endPeriodEquity = self.json_utils.extract(response, "$.result.list[0].endPeriodEquity")
                periodProfit = self.json_utils.extract(response, "$.result.list[0].periodProfit")
                periodProfitUsd = self.json_utils.extract(response, "$.result.list[0].periodProfitUsd")
                expectDividendAmount = self.json_utils.extract(response, "$.result.list[0].expectDividendAmount")
                currency = self.json_utils.extract(response, "$.result.list[0].currency")
                # 加个容错，当跟单用户为空的时候
                if currency is None or currency == "":
                    logging.info("跟单用户无返佣数据")
                    allure.attach(
                        "跟单用户无返佣数据",
                        "返佣数据",
                        allure.attachment_type.TEXT
                    )
                else:
                    expectDividend1 = 0.0
                    expectDividend2 = 0.0
                    expectDividend3 = 0.0
                    expectDividend4 = 0.0

                    default_agent_level = "分红"

                    if currency == "USD":
                        periodP = round(float(periodProfit) * 1.0, 2)
                    elif currency == "JPY":
                        periodP = round(float(periodProfit) * 0.00672, 2)
                    elif currency == "AUD":
                        periodP = round(float(periodProfit) * 0.6251, 2)
                    elif currency == "USC":
                        periodP = round(float(periodProfit) * 0.01, 2)
                    else:
                        pytest.fail(f"不支持的币种：{currency}，请补充币种转换逻辑")

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
                            attachment_name=f"币种的转换详情,当前币种{currency}，转换前：{periodProfit},转换后：{periodP}"
                        )
                    logging.info(f"币种的转换验证通过：{periodProfitUsd}")

                    with allure.step("验证预计分红金额是否正确"):
                        if periodProfitUsd < 0:
                            logging.info("盈利金额小于0")
                            allure.attach("盈利金额小于0,没有分红", "text/plain")
                        else:
                            dividendRate0 = self.json_utils.extract(response,
                                                                    "$.result.list[0].slaveRecords[0].dividendRate")
                            if not dividendRate0:
                                pytest.fail("未提取到信号源分红利率（dividendRate0），无法验证预计分红金额")
                            dividend_rate = dividendRate0 / 100
                            expectDividend = round(float(periodProfitUsd) * dividend_rate, 1)
                            self.verify_data(
                                actual_value=float(expectDividendAmount),
                                expected_value=float(expectDividend),
                                op=CompareOp.EQ,
                                rel_tol=1e-2,
                                message="预计分红金额应符合预期",
                                attachment_name="预计分红金额详情"
                            )
                            logging.info(f"预计分红金额验证通过：{periodProfitUsd}")

                    agentLevel = self.json_utils.extract(response, "$.result.list[0].slaveRecords[1].agentLevel")
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
                            if not all([expectDividendAmount4, dividendRate4]):
                                pytest.fail(f"未提取到{agentLevel}的分红数据（expectDividendAmount4/dividendRate4）")
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
                            if not all([expectDividendAmount3, dividendRate3]):
                                pytest.fail(f"未提取到{agentLevel2}的分红数据（expectDividendAmount3/dividendRate3）")
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
                            if not all([expectDividendAmount2, dividendRate2]):
                                pytest.fail(f"未提取到{agentLevel3}的分红数据（expectDividendAmount2/dividendRate2）")
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
                            if not all([expectDividendAmount1, dividendRate1]):
                                pytest.fail(f"未提取到{agentLevel4}的分红数据（expectDividendAmount1/dividendRate1）")
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
                            if not expectDividendAmount0:
                                pytest.fail("未提取到信号源分红金额（expectDividendAmount0）")
                            expectDividend0 = round(
                                float(expectDividendAmount) - float(expectDividend1) - float(expectDividend2) - float(
                                    expectDividend3) - float(expectDividend4),
                                2
                            )
                            self.verify_data(
                                actual_value=float(expectDividendAmount0),
                                expected_value=float(expectDividend0),
                                op=CompareOp.EQ,
                                rel_tol=1e-2,
                                message="信号源分红金额应符合预期",
                                attachment_name="信号源分红金额详情"
                            )
                            logging.info(f"信号源分红金额验证通过：{periodProfitUsd}")
