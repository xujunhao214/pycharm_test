import time
import math
import allure
import logging
import pytest
import re
from lingkuan_1126.VAR.VAR import *
from lingkuan_1126.conftest import var_manager
from lingkuan_1126.commons.api_base import *
from template.commons.jsonpath_utils import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("VPS看板-查询校验")
class TestVPSquery(APITestBase):
    @allure.story("VPS看板-日志查询")
    class TestVPSquerylog(APITestBase):
        # 实例化JsonPath工具类（全局复用）
        json_utils = JsonPathUtils()

        # 定义所有需要测试的状态（作为参数化数据源）
        STATUS_logType = [
            ("连接日志", "日志类型"),
            ("交易日志", "日志类型")
        ]

        @pytest.mark.url("vps")
        @pytest.mark.parametrize("status, status_desc", STATUS_logType)
        @allure.title("查询：{status_desc}（{status}）")
        def test_query_logType(self, var_manager, logged_session, status, status_desc):
            with allure.step(f"1. 发送请求：查询{status_desc}（{status}）"):
                json_data = {
                    "page": 1,
                    "limit": 100,
                    "platformType": [],
                    "startDate": DATETIME_INIT,
                    "endDate": get_current_time(),
                    "keywords": [],
                    "logInfo": [],
                    "cloudId": [],
                    "vpsId": [],
                    "source": [],
                    "logType": [status]
                }

                response = self.send_post_request(
                    logged_session,
                    '/subcontrol/eslog/queryLogsPage',
                    json_data=json_data
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

            with allure.step(f"3. 查询结果校验：返回记录的typeDec应为{status}"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 typeDec）
                typeDec_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].typeDec",
                    default=[],
                    multi_match=True
                )
                # var_manager.set_runtime_variable("query_typeDec_list", typeDec_list)

                # 日志和 Allure 附件优化
                if not typeDec_list:
                    attach_body = f"查询[{status}]，返回的typeDec列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"日志类型:{status}查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"查询[{status}]暂无数据，跳过校验")
                else:
                    attach_body = f"查询[{status}]，返回 {len(typeDec_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"日志类型:{status}查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，typeDec 也是字符串）
                for idx, actual_status in enumerate(typeDec_list):
                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=status,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的typeDec应为{status}，实际为{actual_status}",
                        attachment_name=f"日志类型:{status}第 {idx + 1} 条记录校验"
                    )

        STATUS_source = [
            ("VPS", "来源"),
            ("交易下单", "来源"),
            ("云策略", "来源"),
            ("单账号操作", "来源")
        ]

        @pytest.mark.url("vps")
        @pytest.mark.parametrize("status, status_desc", STATUS_source)
        @allure.title("查询：{status_desc}（{status}）")
        def test_query_source(self, var_manager, logged_session, status, status_desc):
            with allure.step(f"1. 发送请求：查询{status_desc}（{status}）"):
                json_data = {
                    "page": 1,
                    "limit": 100,
                    "platformType": [],
                    "startDate": DATETIME_INIT,
                    "endDate": get_current_time(),
                    "keywords": [],
                    "logInfo": [],
                    "cloudId": [],
                    "vpsId": [],
                    "source": [
                        status
                    ],
                    "logType": []
                }

                response = self.send_post_request(
                    logged_session,
                    '/subcontrol/eslog/queryLogsPage',
                    json_data=json_data
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

            with allure.step(f"3. 查询结果校验：返回记录的source应为{status}"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 source）
                source_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].source",
                    default=[],
                    multi_match=True
                )
                # var_manager.set_runtime_variable("query_source_list", source_list)

                # 日志和 Allure 附件优化
                if not source_list:
                    attach_body = f"查询[{status}]，返回的source列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"来源:{status}查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"查询[{status}]暂无数据，跳过校验")
                else:
                    attach_body = f"查询[{status}]，返回 {len(source_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"来源:{status}查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，source 也是字符串）
                for idx, actual_status in enumerate(source_list):
                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=status,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的source应为{status}，实际为{actual_status}",
                        attachment_name=f"来源:{status}第 {idx + 1} 条记录校验"
                    )

        @pytest.mark.url("vps")
        @allure.title("云策略查询校验")
        def test_query_cloudId(self, var_manager, logged_session, db_transaction):
            with allure.step(f"0. 提取云策略ID"):
                dbcloud_data = self.query_database(
                    db_transaction,
                    f"SELECT * FROM follow_cloud_master WHERE name = %s",
                    ("xjh测试策略",)
                )
                cloud_id = dbcloud_data[0]['id']
                # cloud_id = 106
            with allure.step(f"1. 发送查询请求"):
                json_data = {
                    "page": 1,
                    "limit": 100,
                    "platformType": [],
                    "startDate": DATETIME_INIT,
                    "endDate": get_current_time(),
                    "keywords": [],
                    "logInfo": [],
                    "cloudId": [cloud_id],
                    "vpsId": [],
                    "logType": [],
                    "source": []
                }

                response = self.send_post_request(
                    logged_session,
                    '/subcontrol/eslog/queryLogsPage',
                    json_data=json_data
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

            # 3. 提取账号（保留记录与账号的关联关系）
            with allure.step(f"3. 提取所有记录中的账号（按记录分组）"):
                response_json = response.json()
                data_list = response_json.get("data", {}).get("list", [])
                record_accounts = []  # 存储格式：[(记录索引, [账号1, 账号2, ...]), ...]

                # 正则表达式：匹配 "账号：数字" 或 "账号=数字"（冒号/等号，兼容中文冒号）
                account_pattern = re.compile(r'账号[：=](\d+)')

                for idx, item in enumerate(data_list):
                    message = item.get("message", "")
                    # 匹配当前记录的所有账号（支持一条message多个账号）
                    accounts = account_pattern.findall(message)
                    if accounts:
                        record_accounts.append((idx + 1, accounts))  # 记录“第几条记录”和“其包含的账号”
                        logger.info(f"第 {idx + 1} 条记录提取到账号：{accounts}（message：{message[:50]}...）")
                    else:
                        logger.warning(f"第 {idx + 1} 条记录未提取到账号（message：{message[:50]}...）")

                # 断言至少有一条记录提取到账号
                assert len(record_accounts) > 0, f"查询[{cloud_id}]未提取到任何账号"

                # 日志和 Allure 报告展示（按记录分组）
                attach_body = f"查询策略【xjh测试策略】cloud_id：【{cloud_id}】\n"
                attach_body += f"共提取到 {len(record_accounts)} 条含账号的记录：\n"
                for idx, accounts in record_accounts:
                    attach_body += f"- 第 {idx} 条记录：{accounts}\n"
                logger.info(attach_body)
                allure.attach(
                    body=attach_body,
                    name=f"日志:策略【xjh测试策略】cloud_id：【{cloud_id}】提取的账号列表",
                    attachment_type="text/plain"
                )

                # 提取所有去重账号（供后续用例使用，保留原有功能）
                all_accounts = []
                for _, accounts in record_accounts:
                    all_accounts.extend(accounts)
                unique_accounts = list(set(all_accounts))
                var_manager.set_runtime_variable("extracted_accounts", unique_accounts)

            with allure.step("4. 从数据库查询该策略下的所有账号（去重）"):
                db_data = self.query_database(
                    db_transaction,
                    f"SELECT * FROM follow_cloud_trader WHERE cloud_id = %s",
                    (cloud_id,)
                )
                # 1. 提取数据库账号并转字符串（统一格式）
                raw_db_accounts = [str(item["account"]) for item in db_data]
                # 2. 对数据库账号去重（避免重复对比）
                db_accounts = list(set(raw_db_accounts))  # 无序去重（效率高）
                # 若需要保持原始顺序，可替换为：db_accounts = list(dict.fromkeys(raw_db_accounts))  # Python3.7+

                # 日志和Allure展示（补充去重前后对比）
                db_attach_body = f"策略【xjh测试策略】cloud_id：【{cloud_id}】在数据库中关联的账号：\n"
                db_attach_body += f"- 去重前：共 {len(raw_db_accounts)} 个（含重复）→ {raw_db_accounts}\n"
                db_attach_body += f"- 去重后：共 {len(db_accounts)} 个 → {db_accounts}"
                logger.info(db_attach_body)
                allure.attach(
                    body=db_attach_body,
                    name=f"策略【xjh测试策略】cloud_id：【{cloud_id}】关联的数据库账号列表",
                    attachment_type="text/plain"
                )

                # 断言数据库有数据（去重后仍需有有效账号）
                assert len(
                    db_accounts) > 0, f"策略【xjh测试策略】cloud_id：【{cloud_id}】在数据库中未查询到关联账号（去重后为空）"

            with allure.step("5. 校验：每条记录至少有一个账号存在于数据库中"):
                invalid_records = []  # 存储无效记录：[(记录索引, 账号列表), ...]

                for idx, accounts in record_accounts:
                    # 核心逻辑：判断当前记录的所有账号中，是否至少有一个存在于数据库
                    has_valid_account = any(acc in db_accounts for acc in accounts)
                    if not has_valid_account:
                        # 所有账号都不在数据库中，记录为无效
                        invalid_records.append((idx, accounts))
                        logger.error(f"第 {idx} 条记录无效：所有账号{accounts}均不在数据库中")
                    else:
                        # 至少有一个有效账号，记录有效信息
                        valid_accounts = [acc for acc in accounts if acc in db_accounts]
                        logger.info(f"第 {idx} 条记录有效：有效账号{valid_accounts}（数据库中存在）")

                # 核心断言：不允许存在“所有账号都无效”的记录
                assert len(invalid_records) == 0, \
                    f"策略【xjh测试策略】cloud_id：【{cloud_id}】校验失败！以下记录的所有账号均不在数据库中：\n" \
                    + "\n".join([f"  第 {idx} 条记录：账号{accounts}" for idx, accounts in invalid_records]) \
                    + f"\n数据库关联账号：{db_accounts}"

                # 校验通过的日志和Allure报告
                success_msg = f"校验通过！\n"
                success_msg += f"- 含账号的记录总数：{len(record_accounts)} 条\n"
                success_msg += f"- 每条记录均至少有一个账号存在于数据库中\n"
                success_msg += f"- 接口提取去重后账号：{unique_accounts}\n"
                success_msg += f"- 数据库去重后账号：{db_accounts}"
                logger.info(success_msg)
                allure.attach(
                    body=success_msg,
                    name=f"账号一致性校验结果（cloud_id：{cloud_id}）",
                    attachment_type="text/plain"
                )
