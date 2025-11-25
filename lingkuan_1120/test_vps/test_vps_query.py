import time
import math
import allure
import logging
import pytest
import re
from lingkuan_1120.VAR.VAR import *
from lingkuan_1120.conftest import var_manager
from lingkuan_1120.commons.api_base import *
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
                    "endDate": DATETIME_NOW,
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
                    "endDate": DATETIME_NOW,
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
                    "endDate": DATETIME_NOW,
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

            # 3. 提取账号（核心逻辑）
            with allure.step(f"3. 提取所有记录中的账号"):
                response_json = response.json()
                data_list = response_json.get("data", {}).get("list", [])
                account_list = []  # 存储所有提取到的账号

                # 正则表达式：匹配 "账号：数字" 或 "账号=数字"（冒号/等号，兼容中文冒号）
                account_pattern = re.compile(r'账号[：=](\d+)')

                for idx, item in enumerate(data_list):
                    message = item.get("message", "")
                    # 匹配所有符合格式的账号（支持一条message多个账号）
                    accounts = account_pattern.findall(message)
                    if accounts:
                        account_list.extend(accounts)  # 批量添加到列表
                        logger.info(f"第 {idx + 1} 条记录提取到账号：{accounts}（message：{message[:50]}...）")
                    else:
                        logger.warning(f"第 {idx + 1} 条记录未提取到账号（message：{message[:50]}...）")

                # 4. 去重（可选，避免重复账号）
                unique_accounts = list(set(account_list))  # 无序去重
                # unique_accounts = list(dict.fromkeys(account_list))  # 有序去重（Python3.7+）

                # 5. 日志和 Allure 报告展示
                attach_body = f"查询[{cloud_id}]，共提取到 {len(account_list)} 个账号（去重后 {len(unique_accounts)} 个）\n"
                attach_body += f"所有账号：{account_list}\n去重后账号：{unique_accounts}"
                logger.info(attach_body)
                allure.attach(
                    body=attach_body,
                    name=f"日志:策略【xjh测试策略】cloud_id：【{cloud_id}】提取的账号列表",
                    attachment_type="text/plain"
                )

                # 6. 可选：断言（如至少提取到一个账号）
                assert len(account_list) > 0, f"查询[{cloud_id}]未提取到任何账号"

                # 存储到变量管理器（供后续用例使用）
                var_manager.set_runtime_variable("extracted_accounts", unique_accounts)

            with allure.step("4. 从数据库查询该策略下的所有账号"):
                db_data = self.query_database(
                    db_transaction,
                    f"SELECT * FROM follow_cloud_trader WHERE cloud_id = %s",
                    (cloud_id,)
                )
                # 1. 提取数据库账号并转字符串（统一格式）
                raw_db_accounts = [str(item["account"]) for item in db_data]  # 假设字段是account
                # 2. 对数据库账号去重（关键步骤）
                db_accounts = list(set(raw_db_accounts))  # 无序去重（推荐，效率高）
                # 若需要保持原始顺序，用：db_accounts = list(dict.fromkeys(raw_db_accounts))  # Python3.7+ 支持

                # 日志和Allure展示（补充去重前后的数量对比）
                db_attach_body = f"策略【xjh测试策略】cloud_id：【{cloud_id}】在数据库中关联的账号：\n"
                db_attach_body += f"去重前：共 {len(raw_db_accounts)} 个（含重复）{raw_db_accounts}\n"
                db_attach_body += f"去重后：共 {len(db_accounts)} 个{db_accounts}"
                logger.info(db_attach_body)
                allure.attach(
                    body=db_attach_body,
                    name=f"策略【xjh测试策略】cloud_id：【{cloud_id}】关联的数据库账号列表（去重后）",
                    attachment_type="text/plain"
                )

                # 断言数据库有数据（去重后仍需有数据）
                assert len(db_accounts) > 0, f"策略【xjh测试策略】cloud_id：【{cloud_id}】在数据库中未查询到关联账号（去重后为空）"

            with allure.step("5. 校验接口提取账号是否全部存在于数据库中"):
                # 找出接口提取但数据库中没有的账号（异常账号）
                invalid_accounts = [acc for acc in unique_accounts if acc not in db_accounts]

                # 核心断言：不允许存在异常账号
                assert len(invalid_accounts) == 0, \
                    f"策略【xjh测试策略】cloud_id：【{cloud_id}】校验失败！以下账号在数据库中不存在：{invalid_accounts}\n" \
                    f"接口提取账号：{unique_accounts}\n数据库关联账号：{db_accounts}"

                # 校验通过的日志和Allure报告
                success_msg = f"校验通过！接口提取的 {len(unique_accounts)} 个账号均存在于数据库中\n"
                success_msg += f"接口提取账号：{unique_accounts}\n数据库关联账号：{db_accounts}"
                logger.info(success_msg)
                allure.attach(
                    body=success_msg,
                    name=f"账号一致性校验结果",
                    attachment_type="text/plain"
                )

        # 定义参数化数据源：(查询关键词, 日志描述, 预期的typeDec)
        STATUS_loginfo = [
            # 连接日志相关（关键词对应typeDec=连接日志）
            ("账号断线", "日志标识-连接日志", "连接日志"),
            ("开始重连", "日志标识-连接日志", "连接日志"),
            ("连接成功", "日志标识-连接日志", "连接日志"),
            ("连接失败", "日志标识-连接日志", "连接日志"),
            # 交易日志相关（关键词对应typeDec=交易日志）
            ("策略账号监听", "日志标识-交易日志", "交易日志"),
            ("主指令", "日志标识-交易日志", "交易日志"),
            ("子指令", "日志标识-交易日志", "交易日志"),
            ("自动补平", "日志标识-交易日志", "交易日志"),
            ("单账户操作", "日志标识-交易日志", "交易日志"),
            ("漏单补开", "日志标识-交易日志", "交易日志"),
            ("漏单补平", "日志标识-交易日志", "交易日志"),
            ("交易执行成功", "日志标识-交易日志", "交易日志"),
            ("交易执行失败", "日志标识-交易日志", "交易日志"),
            ("交易失败", "日志标识-交易日志", "交易日志")
        ]

        @pytest.mark.url("vps")
        # 参数化新增 expected_typeDec，对应每条关键词的预期typeDec
        @pytest.mark.parametrize("keyword, log_desc, expected_typeDec", STATUS_loginfo)
        @allure.title("查询：{log_desc}（{keyword}）")
        def test_query_loginfo(self, var_manager, logged_session, keyword, log_desc, expected_typeDec):
            with allure.step(f"1. 发送请求：查询{log_desc}（{keyword}）"):
                json_data = {
                    "page": 1,
                    "limit": 200,
                    "platformType": [],
                    "startDate": DATETIME_INIT,
                    "endDate": DATETIME_NOW,
                    "keywords": [],
                    "logInfo": [keyword],
                    "cloudId": [],
                    "vpsId": [],
                    "source": [],
                    "logType": []
                }

                response = self.send_post_request(
                    logged_session,
                    '/subcontrol/eslog/queryLogsPage',
                    json_data=json_data
                )

            with allure.step("2. 基础返回校验"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

            with allure.step(f"3. 提取查询结果：{log_desc}"):
                response_json = response.json()
                # 提取所有记录的 typeDec 和 message（用于后续双重校验）
                typeDec_list = self.json_utils.extract(
                    response_json,
                    "$.data.list[*].typeDec",
                    default=[],
                    multi_match=True
                )
                message_list = self.json_utils.extract(
                    response_json,
                    "$.data.list[*].message",
                    default=[],
                    multi_match=True
                )

                # 日志和Allure附件展示
                total = response_json.get("data", {}).get("total", 0)
                attach_body = f"查询{keyword}\n"
                attach_body += f"预期typeDec：{expected_typeDec}\n"
                attach_body += f"总记录数：{total}\n"
                attach_body += f"typeDec列表：{typeDec_list}\n"
                attach_body += f"message列表（前3条）：{message_list[:3]}"  # 只展示前3条，避免过长

                allure.attach(
                    body=attach_body,
                    name=f"查询结果详情",
                    attachment_type="text/plain"
                )
                logger.info(f"查询关键词[{keyword}]，返回 {total} 条记录，预期typeDec：{expected_typeDec}")

                # 暂无数据时跳过后续校验
                if total == 0 or not typeDec_list or not message_list:
                    logger.warning(f"查询关键词[{keyword}]暂无数据，跳过校验")
                    pytest.skip(f"查询关键词[{keyword}]暂无数据，跳过校验")

            with allure.step(f"4. 校验1：所有记录的typeDec应为{expected_typeDec}"):
                # 遍历所有typeDec，验证是否与预期一致
                for idx, actual_type in enumerate(typeDec_list):
                    self.verify_data(
                        actual_value=actual_type,
                        expected_value=expected_typeDec,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的typeDec错误：预期{expected_typeDec}，实际{actual_type}",
                        attachment_name=f"typeDec校验-第{idx + 1}条"
                    )

            with allure.step(f"5. 校验2：所有记录的message应包含关键词[{keyword}]"):
                # 遍历所有message，验证是否包含查询关键词
                for idx, message in enumerate(message_list):
                    # 用in判断（忽略大小写可加：keyword.lower() in message.lower()）
                    assert keyword in message, \
                        f"第 {idx + 1} 条记录的message不包含关键词[{keyword}]\n" \
                        f"message内容：{message[:100]}..."  # 只展示前100字符

                logger.info(f"校验通过：所有 {len(message_list)} 条记录的message均包含关键词[{keyword}]")
                allure.attach(
                    body=f"校验通过：所有 {len(message_list)} 条记录的message均包含关键词[{keyword}]",
                    name=f"关键词包含校验结果",
                    attachment_type="text/plain"
                )

        @pytest.mark.url("vps")
        @allure.title("多关键词-记录查询校验")
        def test_batch_query_keywords(self, var_manager, logged_session):
            # 1. 定义需要批量查询的关键词列表（动态获取账号+固定关键词）
            new_user = var_manager.get_variable("new_user")
            account = str(new_user["account"])  # 从变量管理器获取账号，转字符串
            # 关键词列表：包含账号 + 其他需要查询的关键词
            keyword_list = [
                account,
                "主动断连",
                "账号断线",
                "测试数据测试数据测试数据测试数据测试数据测试数据测试数据",
                "12345689",
                "交易失败"
            ]

            # 2. 循环遍历关键词，逐个执行查询+校验
            for keyword in keyword_list:
                # 每个关键词的独立步骤（Allure报告中会显示每个关键词的流程）
                with allure.step(f"=== 开始查询关键词：{keyword} ==="):
                    try:
                        with allure.step(f"1. 发送查询请求（关键词：{keyword}）"):
                            json_data = {
                                "page": 1,
                                "limit": 200,
                                "platformType": [],
                                "startDate": DATETIME_INIT,
                                "endDate": DATETIME_NOW,
                                "keywords": [keyword],  # 当前循环的关键词
                                "logInfo": [],
                                "cloudId": [],
                                "vpsId": [],
                                "source": [],
                                "logType": []
                            }

                            response = self.send_post_request(
                                logged_session,
                                '/subcontrol/eslog/queryLogsPage',
                                json_data=json_data
                            )

                        with allure.step(f"2. 基础返回校验（关键词：{keyword}）"):
                            self.assert_json_value(
                                response,
                                "$.msg",
                                "success",
                                f"关键词[{keyword}]查询响应失败"
                            )

                        with allure.step(f"3. 校验关键词[{keyword}]是否存在于所有message中"):
                            response_json = response.json()
                            message_list = self.json_utils.extract(
                                response_json,
                                "$.data.list[*].message",
                                default=[],
                                multi_match=True
                            )
                            total = response_json.get("data", {}).get("total", 0)

                            # 日志和Allure附件（每个关键词独立附件）
                            attach_body = f"关键词：{keyword}\n"
                            attach_body += f"返回总记录数：{total}\n"
                            attach_body += f"message列表（前5条预览）：\n{message_list[:5]}"
                            allure.attach(
                                body=attach_body,
                                name=f"关键词[{keyword}]查询结果详情",
                                attachment_type="text/plain"
                            )
                            logger.info(f"关键词[{keyword}]查询完成，返回 {total} 条记录")

                            # 暂无数据时跳过当前关键词的后续校验，继续下一个
                            if total == 0 or not message_list:
                                logger.warning(f"关键词[{keyword}]查询暂无数据，跳过校验")
                                allure.attach(
                                    body=f"关键词[{keyword}]查询暂无数据，跳过校验",
                                    name=f"关键词[{keyword}]校验结果",
                                    attachment_type="text/plain"
                                )
                                continue  # 跳过当前关键词，执行下一个循环

                            # 核心校验：所有message必须包含当前关键词
                            invalid_messages = []
                            for idx, message in enumerate(message_list):
                                message_str = str(message) if message else ""
                                if keyword not in message_str:
                                    invalid_msg = f"第 {idx + 1} 条记录：{message_str[:200]}..."
                                    invalid_messages.append(invalid_msg)
                                    logger.error(f"关键词[{keyword}]不在第 {idx + 1} 条message中：{invalid_msg}")

                        with allure.step(f"4. 关键词[{keyword}]校验结果"):
                            assert len(invalid_messages) == 0, \
                                f"关键词[{keyword}]校验失败！共 {len(invalid_messages)} 条记录不包含该关键词\n" \
                                f"不包含关键词的记录：\n{chr(10).join(invalid_messages)}"

                            success_msg = f"关键词[{keyword}]校验通过！所有 {len(message_list)} 条记录均包含该关键词"
                            logger.info(success_msg)
                            allure.attach(
                                body=success_msg,
                                name=f"关键词[{keyword}]校验结果",
                                attachment_type="text/plain"
                            )

                    except Exception as e:
                        # 捕获当前关键词的异常，记录日志后继续下一个关键词
                        error_msg = f"关键词[{keyword}]查询失败：{str(e)}"
                        logger.error(error_msg, exc_info=True)
                        allure.attach(
                            body=error_msg,
                            name=f"关键词[{keyword}]查询异常",
                            attachment_type="text/plain"
                        )
                        # 可选：是否终止整个用例（默认继续下一个关键词）
                        # raise e  # 取消注释则当前关键词失败后终止整个用例

            # 所有关键词查询完成
            logger.info(f"所有 {len(keyword_list)} 个关键词批量查询校验完成")
            allure.attach(
                body=f"多次查询校验完成！共查询 {len(keyword_list)} 个关键词",
                name="多次查询总结",
                attachment_type="text/plain"
            )

        # 定义参数化数据源：(查询平台类型, 描述)
        STATUS_logType = [
            ("MT4", "平台类型"),
            ("MT5", "平台类型")
        ]

        # 编译正则表达式（全局复用，匹配 "平台类型=MT4" 或 "平台类型=MT5"）
        PLATFORM_PATTERN = re.compile(r'平台类型=([MT4|MT5]+)')

        @pytest.mark.url("vps")
        @pytest.mark.parametrize("query_platform, status_desc", STATUS_logType)
        @allure.title("查询：{status_desc}（{query_platform}）")
        def test_query_platformType(self, var_manager, logged_session, query_platform, status_desc):
            with allure.step(f"1. 发送请求：查询{status_desc}（{query_platform}）"):
                json_data = {
                    "page": 1,
                    "limit": 200,
                    "platformType": [query_platform],  # 按平台类型筛选（MT4/MT5）
                    "startDate": DATETIME_INIT,
                    "endDate": DATETIME_NOW,
                    "keywords": [],
                    "logInfo": [],
                    "cloudId": [],
                    "vpsId": [],
                    "source": [],
                    "logType": []
                }

                response = self.send_post_request(
                    logged_session,
                    '/subcontrol/eslog/queryLogsPage',
                    json_data=json_data
                )

            with allure.step("2. 基础返回校验"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

            with allure.step(f"3. 提取查询结果：{status_desc}（{query_platform}）"):
                response_json = response.json()
                # 提取所有记录的 message 字段（平台类型在message中）
                message_list = self.json_utils.extract(
                    response_json,
                    "$.data.list[*].message",
                    default=[],
                    multi_match=True
                )
                # 提取总记录数
                total = response_json.get("data", {}).get("total", 0)

                # 日志和Allure附件展示
                attach_body = f"查询平台类型：{query_platform}\n"
                attach_body += f"返回总记录数：{total}\n"
                attach_body += f"message列表（前5条预览）：{message_list[:5]}"
                allure.attach(
                    body=attach_body,
                    name=f"平台类型:{query_platform}查询结果",
                    attachment_type="text/plain"
                )
                logger.info(f"查询平台类型[{query_platform}]，返回 {total} 条记录")

                # 暂无数据时跳过校验
                if total == 0 or not message_list:
                    logger.warning(f"查询平台类型[{query_platform}]暂无数据，跳过校验")
                    pytest.skip(f"查询平台类型[{query_platform}]暂无数据，跳过校验")

            with allure.step(f"4. 校验：所有记录的平台类型应为{query_platform}"):
                invalid_records = []  # 存储平台类型不匹配的记录

                for idx, message in enumerate(message_list):
                    message_str = str(message) if message else ""
                    # 用正则提取 message 中的平台类型（匹配 "平台类型=MT4" 或 "平台类型=MT5"）
                    match = self.PLATFORM_PATTERN.search(message_str)
                    if not match:
                        # 未提取到平台类型
                        invalid_msg = f"第 {idx + 1} 条记录：未提取到平台类型（message：{message_str[:100]}...）"
                        invalid_records.append(invalid_msg)
                        logger.error(invalid_msg)
                    else:
                        actual_platform = match.group(1)  # 提取匹配到的平台类型（MT4/MT5）
                        if actual_platform != query_platform:
                            # 平台类型不匹配
                            invalid_msg = f"第 {idx + 1} 条记录：平台类型不匹配（预期{query_platform}，实际{actual_platform}）\nmessage：{message_str[:100]}..."
                            invalid_records.append(invalid_msg)
                            logger.error(invalid_msg)
                        else:
                            logger.info(f"第 {idx + 1} 条记录校验通过：平台类型={actual_platform}")

                # 核心断言：无无效记录
                assert len(invalid_records) == 0, \
                    f"平台类型[{query_platform}]校验失败！共 {len(invalid_records)} 条记录不符合要求\n" \
                    f"无效记录详情：\n{chr(10).join(invalid_records)}"

                # 校验通过的日志和Allure报告
                success_msg = f"校验通过！所有 {len(message_list)} 条记录的平台类型均为{query_platform}"
                logger.info(success_msg)
                allure.attach(
                    body=success_msg,
                    name=f"平台类型:{query_platform}校验结果",
                    attachment_type="text/plain"
                )

        @pytest.mark.url("vps")
        @allure.title("时间查询校验")
        def test_query_time(self, var_manager, logged_session):
            with allure.step(f"1. 发送时间查询请求"):
                json_data = {
                    "page": 1,
                    "limit": 200,
                    "platformType": [],
                    "startDate": DATETIME_INIT,
                    "endDate": DATETIME_NOW,
                    "keywords": [],
                    "logInfo": [],
                    "cloudId": [],
                    "vpsId": [],
                    "source": [],
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

            with allure.step(f"3. 查询结果校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 dateTime）
                dateTime_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].dateTime",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not dateTime_list:
                    pytest.fail("查询结果为空，不符合预期")
                else:
                    attach_body = f"查询开始时间：[{DATETIME_INIT}]，结束时间：[{DATETIME_NOW}]，返回 {len(dateTime_list)} 条记录"

                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"时间查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，dateTime 也是字符串）
                for idx, actual_status in enumerate(dateTime_list):
                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=DATETIME_INIT,
                        op=CompareOp.GE,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的dateTime应为{actual_status}",
                        attachment_name=f"时间:{actual_status}第 {idx + 1} 条记录校验"
                    )

                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=DATETIME_NOW,
                        op=CompareOp.LE,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的dateTime应为{actual_status}",
                        attachment_name=f"时间:{actual_status}第 {idx + 1} 条记录校验"
                    )

        @pytest.mark.url("vps")
        @allure.title("时间查询校验-查询结果为空")
        def test_query_timeNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送时间查询请求"):
                json_data = {
                    "page": 1,
                    "limit": 200,
                    "platformType": [],
                    "startDate": DATETIME_NOW,
                    "endDate": DATETIME_INIT,
                    "keywords": [],
                    "logInfo": [],
                    "cloudId": [],
                    "vpsId": [],
                    "source": [],
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

            with allure.step("3. 查询校验"):
                self.json_utils.assert_empty_list(
                    data=response.json(),
                    expression="$.data.list",
                )
                logging.info("查询结果符合预期：list为空列表")
                allure.attach("查询结果为空，符合预期", 'text/plain')

    @allure.story("VPS看板-历史订单查询")
    class TestVPSqueryhistoryorder(APITestBase):
        # 实例化JsonPath工具类（全局复用）
        json_utils = JsonPathUtils()

        # 定义所有需要测试的状态（作为参数化数据源）
        STATUS_types = [
            (0, "Buy"),
            (1, "sell"),
            (6, "Balance")
        ]

        @pytest.mark.url("vps")
        @pytest.mark.parametrize("status, status_desc", STATUS_types)
        @allure.title("类型查询：{status_desc}（{status}）")
        def test_query_types(self, var_manager, logged_session, status, status_desc):
            with allure.step(f"1. 发送请求：类型查询{status_desc}（{status}）"):
                vps_addslave_id = var_manager.get_variable("vps_addslave_id")
                params = {
                    "page": 1,
                    "limit": 50,
                    "order": "close_time",
                    "traderId": vps_addslave_id,
                    "startTime": "",
                    "endTime": "",
                    "types": status,
                    "startLots": "",
                    "endLots": "",
                    "magic": "",
                    "startOpenTime": "",
                    "endOpenTime": "",
                    "symbol": "",
                    "sourceUser": "",
                    "platformType": "",
                }

                response = self.send_get_request(
                    logged_session,
                    '/subcontrol/follow/histotyOrderList',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

            with allure.step(f"3. 类型查询结果校验：返回记录的type应为{status}"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 type）
                type_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].type",
                    default=[],
                    multi_match=True
                )
                # var_manager.set_runtime_variable("query_type_list", type_list)

                # 日志和 Allure 附件优化
                if not type_list:
                    attach_body = f"类型查询[{status}]，返回的type列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"类型:{status}查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"类型查询[{status}]暂无数据，跳过校验")
                else:
                    attach_body = f"类型查询[{status}]，返回 {len(type_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"日志类型:{status}类型查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，type 也是字符串）
                for idx, actual_status in enumerate(type_list):
                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=status,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的type应为{status}，实际为{actual_status}",
                        attachment_name=f"日志类型:{status}第 {idx + 1} 条记录校验"
                    )

        @pytest.mark.url("vps")
        @allure.title("手数范围查询")
        def test_query_size(self, var_manager, logged_session):
            with allure.step(f"1. 发送手数范围查询请求"):
                vps_addslave_id = var_manager.get_variable("vps_addslave_id")
                params = {
                    "page": 1,
                    "limit": 50,
                    "order": "close_time",
                    "traderId": vps_addslave_id,
                    "startTime": "",
                    "endTime": "",
                    "types": "",
                    "startLots": "0.1",
                    "endLots": "1",
                    "magic": "",
                    "startOpenTime": "",
                    "endOpenTime": "",
                    "symbol": "",
                    "sourceUser": "",
                    "platformType": "",
                }

                response = self.send_get_request(
                    logged_session,
                    '/subcontrol/follow/histotyOrderList',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

            with allure.step(f"3. 手数范围查询结果校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 size）
                size_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].size",
                    default=[],
                    multi_match=True
                )
                # var_manager.set_runtime_variable("query_size_list", size_list)

                # 日志和 Allure 附件优化
                if not size_list:
                    attach_body = f"手数范围查询，返回的size列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"手数范围查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"手数范围查询暂无数据，跳过校验")
                else:
                    attach_body = f"手数范围查询，返回 {len(size_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"手数范围查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，size 也是字符串）
                for idx, size in enumerate(size_list):
                    self.verify_data(
                        actual_value=size,
                        expected_value=0.1,
                        op=CompareOp.GE,
                        message=f"第 {idx + 1} 条记录的size应为{size}",
                        attachment_name=f"手数范围:{size}第 {idx + 1} 条记录校验"
                    )
                    self.verify_data(
                        actual_value=size,
                        expected_value=1,
                        op=CompareOp.LE,
                        message=f"第 {idx + 1} 条记录的size应为{size}",
                        attachment_name=f"手数范围:{size}第 {idx + 1} 条记录校验"
                    )

        @pytest.mark.url("vps")
        @allure.title("手数范围查询-查询结果为空")
        def test_query_sizeNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送手数范围查询请求"):
                vps_addslave_id = var_manager.get_variable("vps_addslave_id")
                params = {
                    "page": 1,
                    "limit": 50,
                    "order": "close_time",
                    "traderId": vps_addslave_id,
                    "startTime": "",
                    "endTime": "",
                    "types": "",
                    "startLots": "1",
                    "endLots": "0.1",
                    "magic": "",
                    "startOpenTime": "",
                    "endOpenTime": "",
                    "symbol": "",
                    "sourceUser": "",
                    "platformType": "",
                }

                response = self.send_get_request(
                    logged_session,
                    '/subcontrol/follow/histotyOrderList',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

            with allure.step(f"3. 手数范围查询结果校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 size）
                size_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].size",
                    default=[],
                    multi_match=True
                )
                # var_manager.set_runtime_variable("query_size_list", size_list)

                # 日志和 Allure 附件优化
                if not size_list:
                    attach_body = f"手数范围查询，返回的size列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"手数范围查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    # pytest.skip(f"手数范围查询暂无数据，跳过校验")
                else:
                    attach_body = f"手数范围查询，返回 {len(size_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"手数范围查询结果",
                        attachment_type="text/plain"
                    )

        @pytest.mark.url("vps")
        @allure.title("品种查询")
        def test_query_symbol(self, var_manager, logged_session):
            with allure.step(f"1. 发送品种查询请求"):
                vps_addslave_id = var_manager.get_variable("vps_addslave_id")
                new_user = var_manager.get_variable("new_user")
                symbol = new_user["symbol"]
                params = {
                    "page": 1,
                    "limit": 50,
                    "order": "close_time",
                    "traderId": vps_addslave_id,
                    "startTime": "",
                    "endTime": "",
                    "types": "",
                    "startLots": "",
                    "endLots": "",
                    "magic": "",
                    "startOpenTime": "",
                    "endOpenTime": "",
                    "symbol": symbol,
                    "sourceUser": "",
                    "platformType": "",
                }

                response = self.send_get_request(
                    logged_session,
                    '/subcontrol/follow/histotyOrderList',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

            with allure.step(f"3. 品种查询结果校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 symbol）
                symbol_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].symbol",
                    default=[],
                    multi_match=True
                )
                # var_manager.set_runtime_variable("query_symbol_list", symbol_list)

                # 日志和 Allure 附件优化
                if not symbol_list:
                    attach_body = f"品种查询，返回的symbol列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"品种查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    # pytest.skip(f"品种查询暂无数据，跳过校验")
                else:
                    attach_body = f"品种查询，返回 {len(symbol_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"品种查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，size 也是字符串）
                for idx, symbollist in enumerate(symbol_list):
                    self.verify_data(
                        actual_value=symbollist,
                        expected_value=symbol,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的symbol应为{symbol}，实际为{symbollist}",
                        attachment_name=f"品种:{symbol}第 {idx + 1} 条记录校验"
                    )

        @pytest.mark.url("vps")
        @allure.title("品种查询-查询结果为空")
        def test_query_symbolNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送品种查询请求"):
                vps_addslave_id = var_manager.get_variable("vps_addslave_id")
                params = {
                    "page": 1,
                    "limit": 50,
                    "order": "close_time",
                    "traderId": vps_addslave_id,
                    "startTime": "",
                    "endTime": "",
                    "types": "",
                    "startLots": "",
                    "endLots": "",
                    "magic": "",
                    "startOpenTime": "",
                    "endOpenTime": "",
                    "symbol": "测试品种",
                    "sourceUser": "",
                    "platformType": "",
                }

                response = self.send_get_request(
                    logged_session,
                    '/subcontrol/follow/histotyOrderList',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

            with allure.step(f"3. 品种查询结果校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 symbol）
                symbol_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].symbol",
                    default=[],
                    multi_match=True
                )
                # var_manager.set_runtime_variable("query_symbol_list", symbol_list)

                # 日志和 Allure 附件优化
                if not symbol_list:
                    attach_body = f"品种查询，返回的symbol列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"品种查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    # pytest.skip(f"品种查询暂无数据，跳过校验")
                else:
                    attach_body = f"品种查询，返回 {len(symbol_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"品种查询结果",
                        attachment_type="text/plain"
                    )

        @pytest.mark.url("vps")
        @allure.title("魔术号查询")
        def test_query_magic(self, var_manager, logged_session):
            with allure.step(f"1. 发送魔术号查询请求"):
                vps_addslave_id = var_manager.get_variable("vps_addslave_id")
                vps_redis_comparable_list_open = var_manager.get_variable("vps_redis_comparable_list_open")
                magic = vps_redis_comparable_list_open[0]["magical"]
                params = {
                    "page": 1,
                    "limit": 50,
                    "order": "close_time",
                    "traderId": vps_addslave_id,
                    "startTime": "",
                    "endTime": "",
                    "types": "",
                    "startLots": "",
                    "endLots": "",
                    "magic": magic,
                    "startOpenTime": "",
                    "endOpenTime": "",
                    "symbol": "",
                    "sourceUser": "",
                    "platformType": "",
                }

                response = self.send_get_request(
                    logged_session,
                    '/subcontrol/follow/histotyOrderList',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

            with allure.step(f"3. 魔术号查询结果校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 magic）
                magic_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].magic",
                    default=[],
                    multi_match=True
                )
                # var_manager.set_runtime_variable("query_magic_list", magic_list)

                # 日志和 Allure 附件优化
                if not magic_list:
                    attach_body = f"魔术号查询，返回的magic列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"魔术号查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    # pytest.skip(f"魔术号查询暂无数据，跳过校验")
                else:
                    attach_body = f"魔术号查询，返回 {len(magic_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"魔术号查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，size 也是字符串）
                for idx, magiclist in enumerate(magic_list):
                    self.verify_data(
                        actual_value=magiclist,
                        expected_value=magic,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的magic应为{magic}，实际为{magiclist}",
                        attachment_name=f"魔术号:{magic}第 {idx + 1} 条记录校验"
                    )

        @pytest.mark.url("vps")
        @allure.title("魔术号查询-查询结果为空")
        def test_query_magicNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送魔术号查询请求"):
                vps_addslave_id = var_manager.get_variable("vps_addslave_id")
                params = {
                    "page": 1,
                    "limit": 50,
                    "order": "close_time",
                    "traderId": vps_addslave_id,
                    "startTime": "",
                    "endTime": "",
                    "types": "",
                    "startLots": "",
                    "endLots": "",
                    "magic": "测试魔术号",
                    "startOpenTime": "",
                    "endOpenTime": "",
                    "symbol": "",
                    "sourceUser": "",
                    "platformType": "",
                }

                response = self.send_get_request(
                    logged_session,
                    '/subcontrol/follow/histotyOrderList',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

            with allure.step(f"3. 魔术号查询结果校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 magic）
                magic_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].magic",
                    default=[],
                    multi_match=True
                )
                # var_manager.set_runtime_variable("query_magic_list", magic_list)

                # 日志和 Allure 附件优化
                if not magic_list:
                    attach_body = f"魔术号查询，返回的magic列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"魔术号查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    # pytest.skip(f"魔术号查询暂无数据，跳过校验")
                else:
                    attach_body = f"魔术号查询，返回 {len(magic_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"魔术号查询结果",
                        attachment_type="text/plain"
                    )

        @pytest.mark.url("vps")
        @allure.title("主账号查询")
        def test_query_sourceUser(self, var_manager, logged_session):
            with allure.step(f"1. 发送主账号查询请求"):
                vps_addslave_id = var_manager.get_variable("vps_addslave_id")
                new_user = var_manager.get_variable("new_user")
                account = new_user["account"]
                params = {
                    "page": 1,
                    "limit": 50,
                    "order": "close_time",
                    "traderId": vps_addslave_id,
                    "startTime": "",
                    "endTime": "",
                    "types": "",
                    "startLots": "",
                    "endLots": "",
                    "magic": "",
                    "startOpenTime": "",
                    "endOpenTime": "",
                    "symbol": "",
                    "sourceUser": account,
                    "platformType": "",
                }

                response = self.send_get_request(
                    logged_session,
                    '/subcontrol/follow/histotyOrderList',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

            with allure.step(f"3. 主账号查询结果校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 sourceUser）
                sourceUser_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].sourceUser",
                    default=[],
                    multi_match=True
                )
                # var_manager.set_runtime_variable("query_sourceUser_list", sourceUser_list)

                # 日志和 Allure 附件优化
                if not sourceUser_list:
                    attach_body = f"主账号查询，返回的sourceUser列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"主账号查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    # pytest.skip(f"魔术号查询暂无数据，跳过校验")
                else:
                    attach_body = f"主账号查询，返回 {len(sourceUser_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"主账号查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，size 也是字符串）
                for idx, sourceUserlist in enumerate(sourceUser_list):
                    self.verify_data(
                        actual_value=sourceUserlist,
                        expected_value=account,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的sourceUser应为{account}，实际为{sourceUserlist}",
                        attachment_name=f"主账号查询:{account}第 {idx + 1} 条记录校验"
                    )

        @pytest.mark.url("vps")
        @allure.title("主账号查询-查询结果为空")
        def test_query_sourceUserNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送主账号查询请求"):
                vps_addslave_id = var_manager.get_variable("vps_addslave_id")
                params = {
                    "page": 1,
                    "limit": 50,
                    "order": "close_time",
                    "traderId": vps_addslave_id,
                    "startTime": "",
                    "endTime": "",
                    "types": "",
                    "startLots": "",
                    "endLots": "",
                    "magic": "",
                    "startOpenTime": "",
                    "endOpenTime": "",
                    "symbol": "",
                    "sourceUser": "测试主账号查询",
                    "platformType": "",
                }

                response = self.send_get_request(
                    logged_session,
                    '/subcontrol/follow/histotyOrderList',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

            with allure.step(f"3. 主账号查询结果校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 sourceUser）
                sourceUser_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].sourceUser",
                    default=[],
                    multi_match=True
                )
                # var_manager.set_runtime_variable("query_sourceUser_list", sourceUser_list)

                # 日志和 Allure 附件优化
                if not sourceUser_list:
                    attach_body = f"主账号查询，返回的sourceUser列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"主账号查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    # pytest.skip(f"魔术号查询暂无数据，跳过校验")
                else:
                    attach_body = f"主账号查询，返回 {len(sourceUser_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"主账号查询结果",
                        attachment_type="text/plain"
                    )

        # 定义所有需要测试的状态（作为参数化数据源）
        STATUS_platformType = [
            (0, "MT4"),
            (1, "MT5")
        ]

        @pytest.mark.url("vps")
        @pytest.mark.parametrize("status, status_desc", STATUS_platformType)
        @allure.title("平台类型查询：{status_desc}（{status}）")
        def test_query_platformType(self, var_manager, logged_session, status, status_desc):
            with allure.step(f"1. 发送请求：平台类型查询{status_desc}（{status}）"):
                vps_addslave_id = var_manager.get_variable("vps_addslave_id")
                params = {
                    "page": 1,
                    "limit": 50,
                    "order": "close_time",
                    "traderId": vps_addslave_id,
                    "startTime": "",
                    "endTime": "",
                    "types": "",
                    "startLots": "",
                    "endLots": "",
                    "magic": "",
                    "startOpenTime": "",
                    "endOpenTime": "",
                    "symbol": "",
                    "sourceUser": "",
                    "platformType": status,
                }

                response = self.send_get_request(
                    logged_session,
                    '/subcontrol/follow/histotyOrderList',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

            with allure.step(f"3. 平台类型查询结果校验：返回记录的platformType应为{status}"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 platformType）
                platformType_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].platformType",
                    default=[],
                    multi_match=True
                )
                # var_manager.set_runtime_variable("query_platformType_list", platformType_list)

                # 日志和 Allure 附件优化
                if not platformType_list:
                    attach_body = f"平台类型查询[{status}]，返回的platformType列表为空（暂无数据）"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"平台类型:{status}查询结果",
                        attachment_type="text/plain"
                    )
                    # 可选：暂无数据时跳过后续校验（或断言“允许为空”）
                    pytest.skip(f"平台类型查询[{status}]暂无数据，跳过校验")
                else:
                    attach_body = f"平台类型查询[{status}]，返回 {len(platformType_list)} 条记录"
                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"平台类型:{status}平台类型查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，platformType 也是字符串）
                for idx, actual_status in enumerate(platformType_list):
                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=status,
                        op=CompareOp.EQ,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的platformType应为{status}，实际为{actual_status}",
                        attachment_name=f"平台类型:{status}第 {idx + 1} 条记录校验"
                    )

        @pytest.mark.url("vps")
        @allure.title("开仓时间查询校验")
        def test_query_opentime(self, var_manager, logged_session):
            with allure.step(f"1. 发送开仓时间查询请求"):
                vps_addslave_id = var_manager.get_variable("vps_addslave_id")
                params = {
                    "page": 1,
                    "limit": 50,
                    "order": "close_time",
                    "traderId": vps_addslave_id,
                    "startTime": "",
                    "endTime": "",
                    "types": "",
                    "startLots": "",
                    "endLots": "",
                    "magic": "",
                    "startOpenTime": five_time,
                    "endOpenTime": DATETIME_NOW,
                    "symbol": "",
                    "sourceUser": "",
                    "platformType": "",
                }

                response = self.send_get_request(
                    logged_session,
                    '/subcontrol/follow/histotyOrderList',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

            with allure.step(f"3. 查询结果校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 openTime）
                openTime_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].openTime",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not openTime_list:
                    pytest.fail("查询结果为空，不符合预期")
                else:
                    attach_body = f"查询开始时间：[{five_time}]，结束时间：[{DATETIME_NOW}]，返回 {len(openTime_list)} 条记录"

                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"开仓时间查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，dateTime 也是字符串）
                for idx, actual_status in enumerate(openTime_list):
                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=five_time,
                        op=CompareOp.GE,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的dateTime应为{actual_status}",
                        attachment_name=f"开仓时间:{actual_status}第 {idx + 1} 条记录校验"
                    )

                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=DATETIME_NOW,
                        op=CompareOp.LE,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的dateTime应为{actual_status}",
                        attachment_name=f"开仓时间:{actual_status}第 {idx + 1} 条记录校验"
                    )

        @pytest.mark.url("vps")
        @allure.title("开仓时间查询校验-结果查询为空")
        def test_query_opentimeNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送开仓时间查询请求"):
                vps_addslave_id = var_manager.get_variable("vps_addslave_id")
                params = {
                    "page": 1,
                    "limit": 50,
                    "order": "close_time",
                    "traderId": vps_addslave_id,
                    "startTime": "",
                    "endTime": "",
                    "types": "",
                    "startLots": "",
                    "endLots": "",
                    "magic": "",
                    "startOpenTime": DATETIME_NOW,
                    "endOpenTime": five_time,
                    "symbol": "",
                    "sourceUser": "",
                    "platformType": "",
                }

                response = self.send_get_request(
                    logged_session,
                    '/subcontrol/follow/histotyOrderList',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

            with allure.step("3. 查询校验"):
                self.json_utils.assert_empty_list(
                    data=response.json(),
                    expression="$.data.list",
                )
                logging.info("查询结果符合预期：list为空列表")
                allure.attach("查询结果为空，符合预期", 'text/plain')

        @pytest.mark.url("vps")
        @allure.title("平仓时间查询校验")
        def test_query_closetime(self, var_manager, logged_session):
            with allure.step(f"1. 发送平仓时间查询请求"):
                vps_addslave_id = var_manager.get_variable("vps_addslave_id")
                params = {
                    "page": 1,
                    "limit": 50,
                    "order": "close_time",
                    "traderId": vps_addslave_id,
                    "startTime": five_time,
                    "endTime": DATETIME_NOW,
                    "types": "",
                    "startLots": "",
                    "endLots": "",
                    "magic": "",
                    "startOpenTime": "",
                    "endOpenTime": "",
                    "symbol": "",
                    "sourceUser": "",
                    "platformType": "",
                }

                response = self.send_get_request(
                    logged_session,
                    '/subcontrol/follow/histotyOrderList',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

            with allure.step(f"3. 查询结果校验"):
                # 修复：正确的 JsonPath 表达式（提取所有记录的 closeTime）
                closeTime_list = self.json_utils.extract(
                    response.json(),
                    "$.data.list[*].closeTime",
                    default=[],
                    multi_match=True
                )

                # 日志和 Allure 附件优化
                if not closeTime_list:
                    pytest.fail("查询结果为空，不符合预期")
                else:
                    attach_body = f"查询开始时间：[{five_time}]，结束时间：[{DATETIME_NOW}]，返回 {len(closeTime_list)} 条记录"

                    logger.info(attach_body)
                    allure.attach(
                        body=attach_body,
                        name=f"平仓时间查询结果",
                        attachment_type="text/plain"
                    )

                # 修复：去掉 int() 强制转换（status 是字符串，dateTime 也是字符串）
                for idx, actual_status in enumerate(closeTime_list):
                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=five_time,
                        op=CompareOp.GE,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的dateTime应为{actual_status}",
                        attachment_name=f"平仓时间:{actual_status}第 {idx + 1} 条记录校验"
                    )

                    self.verify_data(
                        actual_value=actual_status,
                        expected_value=DATETIME_NOW,
                        op=CompareOp.LE,
                        use_isclose=False,
                        message=f"第 {idx + 1} 条记录的dateTime应为{actual_status}",
                        attachment_name=f"平仓时间:{actual_status}第 {idx + 1} 条记录校验"
                    )

        @pytest.mark.url("vps")
        @allure.title("平仓时间查询校验-查询结果为空")
        def test_query_closetimeNO(self, var_manager, logged_session):
            with allure.step(f"1. 发送平仓时间查询请求"):
                vps_addslave_id = var_manager.get_variable("vps_addslave_id")
                params = {
                    "page": 1,
                    "limit": 50,
                    "order": "close_time",
                    "traderId": vps_addslave_id,
                    "startTime": DATETIME_NOW,
                    "endTime": five_time,
                    "types": "",
                    "startLots": "",
                    "endLots": "",
                    "magic": "",
                    "startOpenTime": "",
                    "endOpenTime": "",
                    "symbol": "",
                    "sourceUser": "",
                    "platformType": "",
                }

                response = self.send_get_request(
                    logged_session,
                    '/subcontrol/follow/histotyOrderList',
                    params=params
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    "响应msg字段应为success"
                )

            with allure.step("3. 查询校验"):
                self.json_utils.assert_empty_list(
                    data=response.json(),
                    expression="$.data.list",
                )
                logging.info("查询结果符合预期：list为空列表")
                allure.attach("查询结果为空，符合预期", 'text/plain')
