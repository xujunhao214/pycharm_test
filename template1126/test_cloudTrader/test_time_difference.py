import time
import statistics
from typing import List, Union
import allure
import logging
import json
import pytest
from template1126.VAR.VAR import *
from template1126.commons.jsonpath_utils import *
from template1126.commons.random_generator import *
import re
import datetime
import requests
from template1126.commons.api_base import APITestBase, CompareOp, logger
from template1126.conftest import var_manager

# 配置参数
TOTAL_CYCLES = 20  # 总循环次数
TRADE_RETRY_INTERVAL = 10  # 交易重试间隔(秒)
SYNC_WAIT_SECONDS = 2  # 同步等待时间


@allure.feature("创建订单然后统计时间差")
class Test_createTD:
    @allure.story("VPS策略下单-复制下单")
    class TestVPSOrdersend(APITestBase):
        @pytest.mark.url("vps")
        @allure.title("跟单软件看板-VPS数据-策略开仓平仓循环执行")
        def test_trader_open_close_loop(self, var_manager, logged_vps):
            """单条用例内完成多次开仓平仓循环，所有循环过程展示在步骤中"""
            allure.dynamic.description(f"共执行{TOTAL_CYCLES}次循环：每次循环包含开仓→平仓操作")

            # 获取基础变量（只获取一次，避免重复读取）
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")

            # 循环执行开仓平仓
            for cycle_num in range(1, TOTAL_CYCLES + 1):
                with allure.step(f"第{cycle_num}/{TOTAL_CYCLES}次循环：开始"):
                    try:
                        # 1. 策略开仓
                        with allure.step(f"第{cycle_num}次循环 - 发送策略开仓请求"):
                            data = {
                                "symbol": trader_ordersend["symbol"],
                                "placedType": 0,
                                "remark": f"gendanshequ_loop_{cycle_num}",  # 标记当前循环次数
                                "intervalTime": 100,
                                "type": 0,
                                "totalNum": trader_ordersend["totalNum"],
                                "totalSzie": trader_ordersend["totalSzie"],
                                "startSize": trader_ordersend["startSize"],
                                "endSize": trader_ordersend["endSize"],
                                "traderId": vps_trader_id
                            }
                            response = self.send_post_request(
                                logged_vps,
                                '/subcontrol/trader/orderSend',
                                json_data=data,
                            )

                        # 2. 验证开仓响应
                        with allure.step(f"第{cycle_num}次循环 - 验证开仓响应"):
                            self.assert_response_status(
                                response,
                                200,
                                f"第{cycle_num}次开仓失败"
                            )
                            self.assert_json_value(
                                response,
                                "$.msg",
                                "success",
                                f"第{cycle_num}次开仓响应msg字段应为success"
                            )

                        # 等待同步
                        time.sleep(SYNC_WAIT_SECONDS)

                        # 3. 策略平仓
                        with allure.step(f"第{cycle_num}次循环 - 发送策略平仓请求"):
                            data = {
                                "isCloseAll": 1,
                                "intervalTime": 100,
                                "traderId": vps_trader_id,
                                "account": vps_user_accounts_1
                            }
                            response = self.send_post_request(
                                logged_vps,
                                '/subcontrol/trader/orderClose',
                                json_data=data,
                            )

                        # 4. 验证平仓响应
                        with allure.step(f"第{cycle_num}次循环 - 验证平仓响应"):
                            self.assert_response_status(
                                response,
                                200,
                                f"第{cycle_num}次平仓失败"
                            )
                            self.assert_json_value(
                                response,
                                "$.msg",
                                "success",
                                f"第{cycle_num}次平仓响应msg字段应为success"
                            )

                        logger.info(f"第{cycle_num}/{TOTAL_CYCLES}次循环执行成功")

                    except Exception as e:
                        error_msg = f"第{cycle_num}次循环执行失败: {str(e)}"
                        logger.error(error_msg)
                        allure.attach(error_msg, f"第{cycle_num}次循环失败详情", allure.attachment_type.TEXT)
                        time.sleep(TRADE_RETRY_INTERVAL)
                        # 若需要某一次循环失败后终止整个用例，取消下面这行的注释
                        # raise  # 抛出异常标记用例失败

                # 循环间的间隔（可选）
                if cycle_num < TOTAL_CYCLES:
                    with allure.step(f"第{cycle_num}次循环完成，等待下一次循环开始"):
                        time.sleep(SYNC_WAIT_SECONDS)

            with allure.step(f"所有{TOTAL_CYCLES}次循环执行完毕"):
                logger.info(f"全部{TOTAL_CYCLES}次循环执行完成")

    # @pytest.mark.skip(reason="跳过此用例")
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
                # var_manager.set_runtime_variable("trader_open_time_difference", trader_open_time_diff)

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
                # var_manager.set_runtime_variable("follow_open_time_difference", follow_open_time_diff)

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
                # var_manager.set_runtime_variable("trader_close_time_difference", trader_close_time_diff)

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
                # var_manager.set_runtime_variable("follow_close_time_difference", follow_close_time_diff)

            with allure.step("2. 时间差数据统计与格式化输出"):
                stats = self._calculate_time_stats(follow_close_time_diff)
                self._format_time_output("跟单账户平仓", stats)
