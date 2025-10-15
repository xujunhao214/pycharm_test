import time
import pytest
import logging
import allure
import re
from typing import Dict, Any, List
from lingkuan_comm.VAR.VAR import *
from lingkuan_comm.commons.jsonpath_utils import *
from lingkuan_comm.conftest import var_manager
from lingkuan_comm.commons.api_vpsbase import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("云策略-云策略列表-日志筛选校验")
class TestCreate_cloudTrader(APIVPSBase):
    # 实例化JsonPath工具类（全局复用）
    json_utils = JsonPathUtils()

    STATUS_LOGTYPE = [
        ("连接日志", "日志类型-连接日志"),
        ("交易日志", "日志类型-交易日志")
    ]

    @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.parametrize("status, status_desc", STATUS_LOGTYPE)
    @allure.title("日志筛选：{status_desc}")
    def test_query_logtype(self, logged_vps, var_manager, status, status_desc):
        with allure.step(f"1. 发送请求：查询{status_desc}"):
            data = {
                "page": 1,
                "limit": 100,
                "platformType": [],
                "startDate": ONE_HOUR_AGO,
                "endDate": DATETIME_NOW,
                "keywords": [],
                "logInfo": [],
                "cloudId": [106],
                "vpsId": [],
                "source": [],
                "logType": [status]
            }

            # 1. 发送创建用户请求
            response = self.send_post_request(
                logged_vps,
                "/mascontrol/eslog/queryLogsPage",
                json_data=data
            )
        with allure.step(f"2. 响应校验"):
            # 2. 验证JSON返回内容
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

        with allure.step(f"3. 查询结果校验"):
            status_list = self.json_utils.extract(
                response.json(),
                "$.data.list[*].typeDec",
                default=[],
                multi_match=True
            )

            # 生成查询结果附件
            if not status_list:
                attach_body = f"日志筛选-{status_desc}：返回的为空列表（暂无数据）"
            else:
                attach_body = f"日志筛选-{status_desc}，返回 {len(status_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"日志筛选-{status_desc}：查询结果",
                attachment_type="text/plain"
            )

            # 校验每条记录的status
            for idx, actual_status in enumerate(status_list):
                self.verify_data(
                    actual_value=actual_status,
                    expected_value=status,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录应为{status}",
                    attachment_name=f"日志筛选-{status_desc}：第 {idx + 1} 条记录校验"
                )

    STATUS_SOURCE = [
        ("VPS", "来源-VPS"),
        ("交易下单", "来源-交易下单"),
        ("云策略", "来源-云策略"),
        ("单账户操作", "来源-单账户操作")
    ]

    @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.parametrize("status, status_desc", STATUS_SOURCE)
    @allure.title("日志筛选：{status_desc}")
    def test_query_source(self, logged_vps, var_manager, status, status_desc):
        with allure.step(f"1. 发送请求：查询{status_desc}"):
            data = {
                "page": 1,
                "limit": 200,
                "platformType": [],
                "startDate": ONE_HOUR_AGO,
                "endDate": DATETIME_NOW,
                "keywords": [],
                "logInfo": [],
                "cloudId": [106],
                "vpsId": [],
                "source": [status],
                "logType": []
            }

            # 1. 发送创建用户请求
            response = self.send_post_request(
                logged_vps,
                "/mascontrol/eslog/queryLogsPage",
                json_data=data
            )
        with allure.step(f"2. 响应校验"):
            # 2. 验证JSON返回内容
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

        with allure.step(f"3. 查询结果校验"):
            status_list = self.json_utils.extract(
                response.json(),
                "$.data.list[*].source",
                default=[],
                multi_match=True
            )

            # 生成查询结果附件
            if not status_list:
                attach_body = f"-{status_desc}：返回的为空列表（暂无数据）"
            else:
                attach_body = f"日志筛选-{status_desc}，返回 {len(status_list)} 条记录"

            allure.attach(
                body=attach_body,
                name=f"日志筛选-{status_desc}：查询结果",
                attachment_type="text/plain"
            )

            # 校验每条记录的status
            for idx, actual_status in enumerate(status_list):
                self.verify_data(
                    actual_value=actual_status,
                    expected_value=status,
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message=f"第 {idx + 1} 条记录应为{status}",
                    attachment_name=f"日志筛选-{status_desc}：第 {idx + 1} 条记录校验"
                )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库查询-获取VPS")
    def test_get_vpsID(self, var_manager, dbvps_transaction):
        with allure.step("1. 查询数据库数据"):
            ip_address = var_manager.get_variable("IP_ADDRESS")

            db_data = self.query_database(
                dbvps_transaction,
                f"SELECT * FROM follow_vps WHERE deleted = %s",
                (0,)
            )

        with allure.step("2. 提取数据库数据"):
            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            query_ipaddress = [record["ip_address"] for record in db_data]
            var_manager.set_runtime_variable("query_ipaddress", query_ipaddress)
            print(f"成功提取ip_address: {query_ipaddress}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("日志筛选：vps")
    def test_query_vps(self, logged_vps, var_manager):
        with allure.step(f"1. 发送请求：查询vps"):
            # 获取数据库中查询到的IP地址列表
            query_ipaddress = var_manager.get_variable("query_ipaddress")
            # 确保query_ipaddress是可迭代对象且非空
            if not query_ipaddress or not isinstance(query_ipaddress, (list, tuple)):
                pytest.fail("query_ipaddress为空或格式非法，无法进行日志筛选")

            # 存储所有VPS和代理IP的提取结果，用于后续校验
            extracted_vps = []
            extracted_proxy_ips = []
            response = None  # 初始化响应变量

            for vpsid in query_ipaddress:
                data = {
                    "page": 1,
                    "limit": 100,
                    "platformType": [],
                    "startDate": ONE_HOUR_AGO,
                    "endDate": DATETIME_NOW,
                    "keywords": [],
                    "logInfo": [],
                    "cloudId": [106],
                    "vpsId": [vpsid],
                    "logType": [],
                    "source": []
                }

                # 1. 发送请求
                response = self.send_post_request(
                    logged_vps,
                    "/mascontrol/eslog/queryLogsPage",
                    json_data=data
                )

                # 2. 提取响应中的日志列表（关键修复：处理二维列表）
                logs = self.extract_jsonpath(response, "$.data.list")
                # 修复1：展平二维列表（若logs是二维列表，取第一个元素；若为空则设为空列表）
                logs = logs[0] if (logs and isinstance(logs, list) and isinstance(logs[0], list)) else logs
                # 修复2：确保logs是一维列表（避免后续遍历报错）
                if not isinstance(logs, list):
                    logs = []

                if not logs:
                    allure.attach(f"VPSID: {vpsid} 未查询到日志数据", "查询结果", allure.attachment_type.TEXT)
                    continue

                # 3. 遍历日志提取VPS和代理IP信息（此时log已是单个字典）
                for log in logs:
                    # 额外容错：确保log是字典（避免非预期格式）
                    if not isinstance(log, dict):
                        allure.attach(f"日志格式非法（非字典）：{str(log)[:100]}", "格式错误", allure.attachment_type.TEXT)
                        continue

                    message = log.get("message", "")  # 现在log是字典，可正常调用get
                    log_time = log.get("dateTime", "未知时间")

                    # 提取VPS信息（格式：VPS=xxx-xxx）
                    if message:
                        vps_match = re.search(r"VPS=([\d.]+-[\d.]+)", message)
                        if vps_match:
                            vps_value = vps_match.group(1)
                            extracted_vps.append(f"{log_time} - {vps_value}")
                            allure.attach(f"提取到VPS: {vps_value}（时间: {log_time}）", "VPS提取结果",
                                          allure.attachment_type.TEXT)

                        # 提取代理IP信息（格式：代理ip:xxx:xxx）
                        proxy_match = re.search(r"代理ip:([\d.:]+)", message)
                        if proxy_match:
                            proxy_value = proxy_match.group(1)
                            extracted_proxy_ips.append(f"{log_time} - {proxy_value}")
                            allure.attach(f"提取到代理IP: {proxy_value}（时间: {log_time}）", "代理IP提取结果",
                                          allure.attachment_type.TEXT)

        # ---------------------- 后续校验步骤保持不变 ----------------------
        with allure.step(f"2. 响应基本校验"):
            # 确保response已初始化（避免循环未执行时response为None）
            if not response:
                pytest.fail("未发送任何请求，无法进行响应校验")

            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )
            # 校验总日志数（注意同样处理二维列表）
            total_count = self.extract_jsonpath(response, "$.data.total")
            total_count = total_count[0] if (total_count and isinstance(total_count, list)) else 0
            assert total_count > 0, f"查询结果总数为0，未找到符合条件的日志"

        with allure.step(f"3. 提取结果校验"):
            target_ip = var_manager.get_variable("IP_ADDRESS")  # 原始目标IP
            allure.attach(f"共提取到VPS记录 {len(extracted_vps)} 条", "VPS统计", allure.attachment_type.TEXT)
            allure.attach(f"共提取到代理IP记录 {len(extracted_proxy_ips)} 条", "代理IP统计",
                          allure.attachment_type.TEXT)

            # 校验是否提取到数据
            if not extracted_vps and not extracted_proxy_ips:
                pytest.fail(f"未从日志中提取到任何VPS或代理IP信息，目标IP: {target_ip}")

            # 校验VPS包含目标IP
            if extracted_vps:
                vps_has_target = any(target_ip in vps for vps in extracted_vps)
                assert vps_has_target, f"提取的VPS中无目标IP {target_ip}，提取结果：{extracted_vps[:3]}"  # 只显示前3条避免冗余

            # 校验代理IP包含目标IP
            if extracted_proxy_ips:
                proxy_has_target = any(target_ip in proxy for proxy in extracted_proxy_ips)
                assert proxy_has_target, f"提取的代理IP中无目标IP {target_ip}，提取结果：{extracted_proxy_ips[:3]}"

        with allure.step(f"4. 保存提取结果到变量"):
            var_manager.set_runtime_variable("extracted_vps", extracted_vps)
            var_manager.set_runtime_variable("extracted_proxy_ips", extracted_proxy_ips)
            print(f"VPS提取完成：{len(extracted_vps)}条；代理IP提取完成：{len(extracted_proxy_ips)}条")