import time
from template_mt4.commons.api_base import APITestBase, CompareOp
import allure
import logging
import datetime
import pytest
from template_mt4.VAR.VAR import *
from template_mt4.commons.jsonpath_utils import *
from template_mt4.commons.random_generator import *


@allure.feature("返佣管理-跟单分红")
class Test_agent(APITestBase):
    json_utils = JsonPathUtils()

    # 定义所有用例的请求参数
    case_params_list = [
        {
            "_t": current_timestamp_seconds,
            "page": 1,
            "limit": 50,
            "type": "",
            "status": "",
            "dividendTimeBegin": "",
            "dividendTimeEnd": "",
            "followerUser": "xujunhao@163.com",
            "followerTa": "301390775",
            "dividendUser": ""
        },
        {
            "_t": current_timestamp_seconds,
            "page": 1,
            "limit": 50,
            "type": "",
            "status": "",
            "dividendTimeBegin": "",
            "dividendTimeEnd": "",
            "followerUser": "xujunhao2@163.com",
            "followerTa": "301390778",
            "dividendUser": ""
        },
        {
            "_t": current_timestamp_seconds,
            "page": 1,
            "limit": 50,
            "type": "",
            "status": "",
            "dividendTimeBegin": "",
            "dividendTimeEnd": "",
            "followerUser": "xujunhao3@163.com",
            "followerTa": "301390780",
            "dividendUser": ""
        },
        {
            "_t": current_timestamp_seconds,
            "page": 1,
            "limit": 50,
            "type": "",
            "status": "",
            "dividendTimeBegin": "",
            "dividendTimeEnd": "",
            "followerUser": "xujunhao4@163.com",
            "followerTa": "301390783",
            "dividendUser": ""
        },
        {
            "_t": current_timestamp_seconds,
            "page": 1,
            "limit": 50,
            "type": "",
            "status": "",
            "dividendTimeBegin": "",
            "dividendTimeEnd": "",
            "followerUser": "xujunhao5@163.com",
            "followerTa": "301390785",
            "dividendUser": ""
        },
        {
            "_t": current_timestamp_seconds,
            "page": 1,
            "limit": 50,
            "type": "",
            "status": "",
            "dividendTimeBegin": "",
            "dividendTimeEnd": "",
            "followerUser": "xujunhao6@163.com",
            "followerTa": "301394553",
            "dividendUser": ""
        },
        {
            "_t": current_timestamp_seconds,
            "page": 1,
            "limit": 50,
            "type": "",
            "status": "",
            "dividendTimeBegin": "",
            "dividendTimeEnd": "",
            "followerUser": "xujunhao5@163.com",
            "followerTa": "2088767546",
            "dividendUser": ""
        },
        {
            "_t": current_timestamp_seconds,
            "page": 1,
            "limit": 50,
            "type": "",
            "status": "",
            "dividendTimeBegin": "",
            "dividendTimeEnd": "",
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

    @allure.title("返佣管理-跟单分红-5级代理-USD币种")
    @pytest.mark.parametrize("case_params", [case_params_list[5]])
    def test_agent_dividend_5level_usd(self, var_manager, logged_session, case_params):
        self._run_test(case_params, logged_session)

    @allure.title("返佣管理-跟单分红-4级代理-AUD币种")
    @pytest.mark.parametrize("case_params", [case_params_list[6]])
    def test_agent_dividend_4level_aud(self, var_manager, logged_session, case_params):
        self._run_test(case_params, logged_session)

    @allure.title("返佣管理-跟单分红-4级代理-JPY币种")
    @pytest.mark.parametrize("case_params", [case_params_list[7]])
    def test_agent_dividend_4level_jpy(self, var_manager, logged_session, case_params):
        self._run_test(case_params, logged_session)

    # 公共测试逻辑（抽取复用）
    def _run_test(self, case_params, logged_session):
        with allure.step("1. 发送GET请求"):
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
        # 先将response转为json对象
        response = response.json()

        # -------------------------- 外层排序：result.list 按 endEquityTime 倒序 --------------------------
        # 提取外层列表 result.list（兼容空列表场景，避免后续报错）
        outer_list = response.get("result", {}).get("list", [])
        if not outer_list:
            logging.warning("响应中 result.list 为空，无需执行任何排序")
            allure.attach("响应 result.list 为空，跳过所有排序", "排序日志", allure.attachment_type.TEXT)
            return response  # 返回原响应，无排序操作

        def outer_sort_key(outer_item):
            """外层排序的key生成函数：解析endEquityTime为时间戳，用于倒序"""
            end_time_str = outer_item.get("endEquityTime", "")  # 外层list元素的endEquityTime
            if not end_time_str:
                # 无时间字段时，默认用极小时间戳（排最后）
                return datetime.datetime(1970, 1, 1).timestamp()
            try:
                # 解析时间字符串（格式："2025-09-11 16:10:00"）为datetime对象
                end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
                # 返回时间戳（正数值，倒序时用reverse=True）
                return end_time.timestamp()
            except ValueError:
                # 时间格式错误时，默认用极小时间戳（排最后）
                logging.warning(f"外层list元素时间格式错误：endEquityTime={end_time_str}，将排最后")
                return datetime.datetime(1970, 1, 1).timestamp()

        # 执行外层排序（reverse=True 表示倒序，最新时间在前）
        sorted_outer_list = sorted(outer_list, key=outer_sort_key, reverse=True)
        # 将排序后的外层列表放回响应json，覆盖原list
        response["result"]["list"] = sorted_outer_list

        # 打印外层排序日志（便于调试）
        outer_before_sort = [(item.get("id"), item.get("endEquityTime")) for item in outer_list]
        outer_after_sort = [(item.get("id"), item.get("endEquityTime")) for item in sorted_outer_list]
        logging.info(f"外层 result.list 排序完成（按endEquityTime倒序）："
                     f"原顺序(Id, endEquityTime)={outer_before_sort}, "
                     f"排序后(Id, endEquityTime)={outer_after_sort}")
        # 附加外层排序对比到Allure报告
        allure.attach(
            f"外层排序前(Id, endEquityTime)：{outer_before_sort}\n"
            f"外层排序后(Id, endEquityTime)：{outer_after_sort}",
            "外层 result.list 排序对比",
            allure.attachment_type.TEXT
        )

        # -------------------------- 新增：slaveRecords排序逻辑 --------------------------
        # 1. 先将response转为json对象
        # response = response.json()
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
                expectDividend0 = 0.0
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
                            pytest.fail("未提取到信号源分红利率，无法验证预计分红金额")
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
                            pytest.fail(f"未提取到{agentLevel}的分红数据")
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
                            pytest.fail(f"未提取到{agentLevel2}的分红数据")
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
                            pytest.fail(f"未提取到{agentLevel3}的分红数据")
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
                            pytest.fail(f"未提取到{agentLevel4}的分红数据")
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

                agentLevel5 = self.json_utils.extract(response, "$.result.list[0].slaveRecords[5].agentLevel")
                agentLevel5 = agentLevel5 if agentLevel5 is not None and agentLevel5 != "" else default_agent_level
                with allure.step(f"验证{agentLevel5}金额是否正确"):
                    if agentLevel5 == "分红":
                        logging.info(f"{agentLevel5}代理不存在")
                        allure.attach(f"{agentLevel5}代理不存在", "text/plain")
                    elif periodProfitUsd < 0:
                        logging.info("盈利金额小于0")
                        allure.attach("盈利金额小于0,没有分红", "text/plain")
                    else:
                        expectDividendAmount0 = self.json_utils.extract(response,
                                                                        "$.result.list[0].slaveRecords[5].expectDividendAmount")
                        dividendRate0 = self.json_utils.extract(response,
                                                                "$.result.list[0].slaveRecords[5].dividendRate")
                        if not all([expectDividendAmount0, dividendRate0]):
                            pytest.fail(f"未提取到{agentLevel5}的分红数据")
                        dividend_rate = (dividendRate0 - dividendRate1) / 100
                        expectDividend0 = round(float(expectDividendAmount) * dividend_rate, 2)
                        self.verify_data(
                            actual_value=float(expectDividendAmount0),
                            expected_value=float(expectDividend0),
                            op=CompareOp.EQ,
                            rel_tol=1e-2,
                            message=f"{agentLevel5}金额应符合预期",
                            attachment_name=f"{agentLevel5}金额详情"
                        )
                        logging.info(f"{agentLevel5}金额验证通过：{periodProfitUsd}")

                with allure.step("验证信号源分红金额是否正确"):
                    if periodProfitUsd < 0:
                        logging.info("盈利金额小于0")
                        allure.attach("盈利金额小于0,没有分红", "text/plain")
                    else:
                        expectDividendAmountfen = self.json_utils.extract(response,
                                                                          "$.result.list[0].slaveRecords[0].expectDividendAmount")
                        if not expectDividendAmountfen:
                            pytest.fail("未提取到信号源分红金额")
                        expectDividendfen = round(
                            float(expectDividendAmount) - float(expectDividend0) - float(expectDividend1) - float(
                                expectDividend2) - float(expectDividend3) - float(expectDividend4), 2)
                        self.verify_data(
                            actual_value=float(expectDividendAmountfen),
                            expected_value=float(expectDividendfen),
                            op=CompareOp.EQ,
                            rel_tol=1e-2,
                            message="信号源分红金额应符合预期",
                            attachment_name="信号源分红金额详情"
                        )
                        logging.info(f"信号源分红金额验证通过：{periodProfitUsd}")
