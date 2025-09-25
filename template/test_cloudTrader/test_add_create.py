import time
from template.commons.api_base import APITestBase, logger
import allure
import logging
import json
import datetime
import re
import pytest
from template.VAR.VAR import *
from template.commons.jsonpath_utils import *
from template.commons.random_generator import *

# 多账号配置
FOLLOW_ACCOUNT_LIST = [
    {"account": "301392106", "password": "0sgsgtu"},
    {"account": "301392107", "password": "joj6vwd"},
    {"account": "301392108", "password": "yw5piys3"},
    {"account": "301392109", "password": "an0emxc"}
]


@allure.story("绑定跟随者账号（多账号批量版）")
class Test_follow_batch(APITestBase):
    json_utils = JsonPathUtils()

    # 全局共用用例（保持不变）
    @allure.title("【全局】数据库查询-提取BrokerID")
    def test_dbbchain_trader(self, var_manager, db_transaction):
        # 原有代码保持不变
        with allure.step("1. 执行SQL查询bchain_trader_broker表"):
            sql = "SELECT id,name FROM bchain_trader_broker WHERE name = %s"
            params = ("CPT Markets",)
            db_data = self.query_database(
                db_transaction=db_transaction,
                sql=sql,
                params=params
            )
        with allure.step("2. 提取并存储全局BrokerID"):
            brokerId = db_data[0]["id"]
            var_manager.set_runtime_variable("follow_broker_id", brokerId)
            allure.attach(str(brokerId), name="全局BrokerID", attachment_type=allure.attachment_type.TEXT)
            logging.info(f"提取全局BrokerID成功：{brokerId}")

    @allure.title("【全局】提取用户ID（xujunhao@163.com）")
    def test_user_list(self, var_manager, logged_session):
        # 原有代码保持不变
        target_email = "xujunhao@163.com"
        with allure.step("1. 发送用户列表GET请求"):
            params = {
                "_t": current_timestamp_seconds,
                "column": "createTime",
                "field": "id,,username,nickname,email,phone",
                "pageNo": "1",
                "pageSize": "20",
                "order": "desc"
            }
            response = self.send_get_request(
                logged_session,
                '/sys/user/list',
                params=params
            )

        with allure.step("2. 响应基础校验"):
            self.assert_json_value(
                response,
                "$.success",
                True,
                "用户列表接口success应为true"
            )

        with allure.step(f"3. 提取{target_email}的用户ID"):
            all_users = self.json_utils.extract(
                data=response.json(),
                expression="$.result.records[*]",
                multi_match=True,
                default=[]
            )
            assert all_users, "用户列表为空，接口返回异常"

            user_id = None
            for user in all_users:
                if user.get("email", "").lower() == target_email.lower():
                    user_id = user.get("id")
                    break

            assert user_id is not None, f"未找到email={target_email}的用户，请检查用户是否存在"
            var_manager.set_runtime_variable("follow_user_id", user_id)
            allure.attach(str(user_id), name="全局用户ID", attachment_type=allure.attachment_type.TEXT)
            logging.info(f"提取全局用户ID成功：{user_id}")

    # 省略其他全局用例（保持不变）

    # -------------------------- 修复的核心部分 --------------------------
    @allure.title("【多账号】完整流程：绑定→审核→订阅")  # 修复1：使用简单变量
    @pytest.mark.parametrize("follow_acc", FOLLOW_ACCOUNT_LIST)
    @pytest.mark.dependency(depends=[
        "test_dbbchain_trader",
        "test_user_list",
        "test_api_getData1",
        "test_api_getData7"
    ])
    def test_follow_full_flow(self, follow_acc, var_manager, logged_session):
        # 修复2：显式提取账号信息，转换为简单变量
        current_account = follow_acc.get("account")  # 使用.get()避免KeyError
        current_password = follow_acc.get("password")

        # 修复3：增加参数校验
        assert current_account, "账号信息中缺少'account'字段"
        assert current_password, "账号信息中缺少'password'字段"

        var_prefix = f"follow_{current_account}"

        try:
            # 以下流程保持不变
            with allure.step(f"1. 绑定账号：{current_account}"):
                follow_user_id = var_manager.get_variable("follow_user_id")
                follow_broker_id = var_manager.get_variable("follow_broker_id")
                follow_server_id = var_manager.get_variable("follow_server_id")

                bind_data = {
                    "userId": follow_user_id,
                    "brokerId": follow_broker_id,
                    "serverId": follow_server_id,
                    "account": current_account,
                    "password": current_password,
                    "display": "PRIVATE",
                    "passwordType": "0",
                    "subscribeFee": "0",
                    "type": "SLAVE_REAL",
                    "platform": "4"
                }

                bind_response = self.send_post_request(
                    logged_session,
                    '/blockchain/account/bind',
                    json_data=bind_data
                )
                self.assert_json_value(
                    bind_response,
                    "$.success",
                    True,
                    f"账号{current_account}绑定失败"
                )
                # 后续步骤保持不变...

        except Exception as e:
            error_msg = f"账号{current_account}执行失败：{str(e)[:200]}"
            allure.attach(error_msg, name=f"{current_account}失败详情",
                          attachment_type=allure.attachment_type.TEXT)
            logging.error(error_msg, exc_info=True)
            pytest.fail(error_msg)
