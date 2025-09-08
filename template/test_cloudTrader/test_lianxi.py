import time
from template.commons.api_base import APITestBase
import allure
import logging
import pytest
from template.VAR.VAR import *
from template.commons.jsonpath_utils import *
from template.commons.random_generator import *


@allure.feature("账号管理")
class Test_create:
    @allure.story("创建交易员账号")
    class Test_trader(APITestBase):
        # 实例化JsonPath工具类（全局复用）
        json_utils = JsonPathUtils()

        @allure.title("数据库查询-提取数据")
        def test_dbbchain_trader2(self, var_manager, db_transaction):
            with allure.step("1. 查询数据库"):
                trader_account = var_manager.get_variable("trader_account")
                sql = f"SELECT run_ip_addr,equity,equity_init,audit_by FROM bchain_trader WHERE account = %s and status = %s"
                params = (trader_account, "PASS",)
                db_data = self.query_database(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )
            with allure.step("2. 提取数据"):
                run_ip_addr = db_data[0]["run_ip_addr"]
                equity = db_data[0]["equity"]
                equity_init = db_data[0]["equity_init"]
                audit_by = db_data[0]["audit_by"]
                var_manager.set_runtime_variable("trader_run_ip_addr", run_ip_addr)
                var_manager.set_runtime_variable("trader_equity", equity)
                var_manager.set_runtime_variable("trader_equity_init", equity_init)
                var_manager.set_runtime_variable("trader_audit_by", audit_by)

        # @pytest.mark.skip(reason="跳过此用例")
        @allure.title("账号管理-交易员账号-校验策略名是否可用")
        def test_duplicate_check(self, var_manager, logged_session):
            trader_pass_id = var_manager.get_variable("trader_pass_id")
            max_attempts = 10  # 最大尝试次数，避免无限循环
            attempt = 0
            valid_field_val = None
            response = None

            with allure.step("1. 循环生成并校验策略名，直到可用或达到最大尝试次数"):
                while attempt < max_attempts:
                    attempt += 1
                    # 生成新的策略名（前缀xjh + 随机字符串）
                    default_str = generate_random_str()
                    field_val = f"xjh{default_str}"
                    allure.attach(f"第{attempt}次尝试，生成策略名: {field_val}", "尝试信息")

                    # 发送校验请求
                    params = {
                        "_t": True,
                        "tableName": "bchain_trader",
                        "fieldName": "policy_name",
                        "fieldVal": field_val,
                        "dataId": trader_pass_id
                    }
                    response = self.send_get_request(
                        logged_session,
                        '/sys/duplicate/check',
                        params=params
                    )

                    # 提取响应消息
                    message = self.json_utils.extract(response.json(), "$.message")
                    if message == "该值可用！":
                        valid_field_val = field_val  # 记录可用的策略名
                        allure.attach(f"策略名可用: {field_val}", "校验结果")
                        break  # 找到可用值，退出循环
                    elif message == "该值不可用，系统中已存在！":
                        allure.attach(f"策略名已存在，将重新生成: {field_val}", "校验结果")
                        continue  # 继续循环生成新值
                    else:
                        # 处理未知响应消息的情况
                        allure.attach(f"收到未知响应消息: {message}，将重试", "校验结果")
                        continue

                # 循环结束后检查是否找到可用值
                assert valid_field_val is not None, \
                    f"超过最大尝试次数({max_attempts})，未找到可用的策略名"

                # 将可用的策略名存入变量管理器，供后续用例使用
                var_manager.set_runtime_variable("valid_strategy_name", valid_field_val)

            with allure.step("2. 返回结果校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

                self.assert_json_value(
                    response,
                    "$.message",
                    "该值可用！",
                    "响应message字段应为:该值可用！"
                )

        @allure.title("账号管理-交易员账号-编辑账号")
        def test_update_cgform(self, var_manager, logged_session):
            with allure.step("1. 发送请求"):
                trader_pass_id = var_manager.get_variable("trader_pass_id")
                trader_run_ip_addr = var_manager.get_variable("trader_run_ip_addr")
                trader_equity_init = var_manager.get_variable("trader_equity_init")
                trader_equity = var_manager.get_variable("trader_equity")
                trader_audit_by = var_manager.get_variable("trader_audit_by")
                valid_strategy_name = var_manager.get_variable("valid_strategy_name")
                data = {
                    "id": trader_pass_id,
                    "policy_name": valid_strategy_name,
                    "virtual_status": 0,
                    "strategy_introduce_cn": "中文",
                    "strategy_introduce_ch": "繁体",
                    "strategy_introduce_en": "English",
                    "run_ip_addr": trader_run_ip_addr,
                    "status_pass_time": DATETIME_NOW,
                    "subscribe_fee": 0,
                    "equity_init": trader_equity_init,
                    "equity": trader_equity,
                    "audit_by": trader_audit_by,
                    "dividend_ratio": 50
                }
                response = self.send_put_request(
                    logged_session,
                    f'/online/cgform/api/form/2c9a814a81d3a91b0181d3a91b250000',
                    json_data=data
                )

            with allure.step("2. 返回校验"):
                self.assert_json_value(
                    response,
                    "$.success",
                    True,
                    "响应success字段应为true"
                )

                self.assert_json_value(
                    response,
                    "$.message",
                    "修改成功！",
                    "响应message字段应为:修改成功！"
                )
