import time
import statistics
from typing import List, Union
import allure
import logging
import json
import pytest
from template.VAR.VAR import *
from template.commons.jsonpath_utils import *
from template.commons.random_generator import *
import re
import datetime
import requests
from template.commons.api_base import APITestBase, CompareOp, logger


@allure.feature("创建开平仓订单然后统计时间差")
class Test_createTD:
    # @pytest.mark.skip(reason="跳过此用例")
    @allure.story("创建开平仓订单")
    class Test_create_order(APITestBase):
        # 工具类实例化
        json_utils = JsonPathUtils()

        # @pytest.mark.skipif(True, reason="跳过此用例")
        @allure.title("跟单管理-实时跟单-修改订阅数据")
        def test_query_updata_editPa(self, var_manager, logged_session):
            with allure.step("1. 发送修改订阅数据请求"):
                follow_jeecg_rowkey = var_manager.get_variable("follow_jeecg_rowkey")
                data = {
                    "id": follow_jeecg_rowkey,
                    "direction": "FORWARD",
                    "followingMode": 2,
                    "fixedProportion": 100,
                    "fixedLots": None
                }
                response = self.send_put_request(
                    logged_session,
                    '/blockchain/master-slave/editPa',
                    json_data=data
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

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
        TOTAL_CYCLES = 3  # 总循环次数
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
                    allure.attach(url, "请求URL", allure.attachment_type.TEXT)
                    headers_json = json.dumps(self.headers, ensure_ascii=False, indent=2)
                    allure.attach(headers_json, "请求头", allure.attachment_type.JSON)
                    response_text = response.text.strip()

                    logging.info(f"第{attempt + 1}次登录尝试 - 响应内容: {response_text}")
                    allure.attach(response_text, "响应内容", allure.attachment_type.TEXT)

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
                    allure.attach(url, "请求URL", allure.attachment_type.TEXT)
                    headers_json = json.dumps(self.headers, ensure_ascii=False, indent=2)
                    allure.attach(headers_json, "请求头", allure.attachment_type.JSON)
                    response_json = response.json()
                    logging.info(f"第{cycle}次循环第{attempt + 1}次开仓响应: {response_json}")
                    allure.attach(json.dumps(response_json, ensure_ascii=False, indent=2), "响应内容",
                                  allure.attachment_type.JSON)

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
                    allure.attach(url, "请求URL", allure.attachment_type.TEXT)
                    headers_json = json.dumps(self.headers, ensure_ascii=False, indent=2)
                    allure.attach(headers_json, "请求头", allure.attachment_type.JSON)
                    response_json = response.json()
                    logging.info(f"第{cycle}次循环第{attempt + 1}次平仓响应: {response_json}")
                    allure.attach(json.dumps(response_json, ensure_ascii=False, indent=2), "响应内容",
                                  allure.attachment_type.JSON)

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
                        logging.info(
                            f"第{cycle}次循环平仓成功 - 开仓订单号: {ticket_open}, 平仓订单号: {ticket_close}")
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

    @allure.story("开仓/平仓时间差数据统计")
    class Test_difference(APITestBase):
        # 实例化JsonPath工具类（全局复用）
        json_utils = JsonPathUtils()

        # ------------------------------ 核心工具方法：时间差数据统计 ------------------------------
        def _calculate_time_stats(self, time_list: List[Union[int, None]]) -> dict:
            """
            计算时间差统计数据（过滤null值，支持总耗时、最值、平均值、四分位）
            :param time_list: 原始时间差列表（含null）
            :return: 统计结果字典
            """
            # 1. 过滤null值（避免统计异常）
            valid_times = [t for t in time_list if t is not None and isinstance(t, (int, float))]
            if not valid_times:
                pytest.fail("无有效时间差数据，无法进行统计")

            # 2. 基础统计：总耗时、最值、记录数
            total_time = sum(valid_times)
            min_time = min(valid_times)
            max_time = max(valid_times)
            record_count = len(valid_times)
            avg_time = int(round(statistics.mean(valid_times), 0))  # 平均值保留0位小数

            # 3. 四分位计算（Q1=25%分位数，Q2=中位数，Q3=75%分位数）
            sorted_times = sorted(valid_times)
            q1 = int(round(statistics.quantiles(sorted_times, n=4, method='inclusive')[0], 0))
            q2 = int(round(statistics.median(sorted_times), 0))
            q3 = int(round(statistics.quantiles(sorted_times, n=4, method='inclusive')[2], 0))

            # 4. 组装统计结果
            return {
                "total_time_ms": total_time,
                "min_time_ms": min_time,
                "max_time_ms": max_time,
                "avg_time_ms": avg_time,
                "quartiles_ms": f"{q1}/{q2}/{q3}",
                "valid_record_count": record_count,
                "invalid_record_count": len(time_list) - record_count  # 无效记录数（含null）
            }

        # ------------------------------ 工具方法：格式化输出统计结果 ------------------------------
        def _format_time_output(self, time_type: str, stats: dict) -> str:
            """
            格式化时间差统计结果（按目标格式输出）
            :param time_type: 时间类型（如“喊单账户开仓”“跟单账户平仓”）
            :param stats: 统计结果字典（来自_calculate_time_stats）
            :return: 格式化字符串
            """
            output = f"""
    {time_type}时间分析:
    总耗时(ms): {stats['total_time_ms']}
    最小时间差(ms): {stats['min_time_ms']}
    最大时间差(ms): {stats['max_time_ms']}
    平均时间差(ms): {stats['avg_time_ms']}
    四分位(ms): {stats['quartiles_ms']}
    有效记录数量: {stats['valid_record_count']}条
    无效记录数量: {stats['invalid_record_count']}条（含null值）
                    """
            # 日志输出（便于调试）
            logging.info(f"\n{output}")
            # Allure报告附加输出（便于查看测试结果）
            allure.attach(output, name=f"{time_type}时间统计", attachment_type=allure.attachment_type.TEXT)
            return output

        # ------------------------------ 测试用例：数据库查询+统计+格式化输出 ------------------------------
        @allure.title("数据库提取数据-喊单账户开仓时间差（含统计）")
        def test_dbquery_trader_openorder(self, var_manager, db_transaction):
            with allure.step("1. 数据库查询：喊单账户开仓时间差"):
                trader_pass_id = var_manager.get_variable("trader_pass_id")
                # 执行数据库查询（优化SQL：只查需要的字段，减少数据传输）
                db_data = self.query_database(
                    db_transaction,
                    "SELECT * FROM bchain_trader_subscribe_order WHERE master_id = %s",
                    (trader_pass_id,),
                )
                if not db_data:
                    pytest.fail(f"未查询到喊单账户[{trader_pass_id}]的开仓记录")

                # 提取原始时间差列表（保留null值，便于统计无效记录）
                trader_open_time_diff = [record["open_time_difference"] for record in db_data]
                var_manager.set_runtime_variable("trader_open_time_difference", trader_open_time_diff)

            with allure.step("2. 时间差数据统计与格式化输出"):
                # 计算统计结果
                stats = self._calculate_time_stats(trader_open_time_diff)
                # 格式化输出（日志+Allure报告）
                self._format_time_output("喊单账户开仓", stats)

        @allure.title("数据库提取数据-跟单账户开仓时间差（含统计）")
        def test_dbquery_follow_openorder(self, var_manager, db_transaction):
            with allure.step("1. 数据库查询：跟单账户开仓时间差"):
                follow_pass_id = var_manager.get_variable("follow_pass_id")
                db_data = self.query_database(
                    db_transaction,
                    "SELECT * FROM bchain_trader_subscribe_order WHERE slave_id = %s",
                    (follow_pass_id,),
                )
                if not db_data:
                    pytest.fail(f"未查询到跟单账户[{follow_pass_id}]的开仓记录")

                follow_open_time_diff = [record["open_time_difference"] for record in db_data]
                var_manager.set_runtime_variable("follow_open_time_difference", follow_open_time_diff)

            with allure.step("2. 时间差数据统计与格式化输出"):
                stats = self._calculate_time_stats(follow_open_time_diff)
                self._format_time_output("跟单账户开仓", stats)

        @allure.title("数据库提取数据-喊单账户平仓时间差（含统计）")
        def test_dbquery_trader_closeorder(self, var_manager, db_transaction):
            with allure.step("1. 数据库查询：喊单账户平仓时间差"):
                trader_pass_id = var_manager.get_variable("trader_pass_id")
                db_data = self.query_database(
                    db_transaction,
                    "SELECT * FROM bchain_trader_subscribe_order WHERE master_id = %s",
                    (trader_pass_id,),
                )
                if not db_data:
                    pytest.fail(f"未查询到喊单账户[{trader_pass_id}]的平仓记录")

                # 修复原代码bug：变量名错误（原代码将平仓时间差存入开仓变量）
                trader_close_time_diff = [record["close_time_difference"] for record in db_data]
                var_manager.set_runtime_variable("trader_close_time_difference", trader_close_time_diff)

            with allure.step("2. 时间差数据统计与格式化输出"):
                stats = self._calculate_time_stats(trader_close_time_diff)
                self._format_time_output("喊单账户平仓", stats)

        @allure.title("数据库提取数据-跟单账户平仓时间差（含统计）")
        def test_dbquery_follow_closeorder(self, var_manager, db_transaction):
            with allure.step("1. 数据库查询：跟单账户平仓时间差"):
                follow_pass_id = var_manager.get_variable("follow_pass_id")
                db_data = self.query_database(
                    db_transaction,
                    "SELECT * FROM bchain_trader_subscribe_order WHERE slave_id = %s",
                    (follow_pass_id,),
                )
                if not db_data:
                    pytest.fail(f"未查询到跟单账户[{follow_pass_id}]的平仓记录")

                follow_close_time_diff = [record["close_time_difference"] for record in db_data]
                var_manager.set_runtime_variable("follow_close_time_difference", follow_close_time_diff)

            with allure.step("2. 时间差数据统计与格式化输出"):
                stats = self._calculate_time_stats(follow_close_time_diff)
                self._format_time_output("跟单账户平仓", stats)
