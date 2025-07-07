import time

import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuan_707.VAR.VAR import *
from lingkuan_707.conftest import var_manager
from lingkuan_707.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("跟单软件看板")
class TestDeleteFollowSlave(APITestBase):
    # ---------------------------
    # 云策略-云策略列表-新增策略账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云策略列表-新增策略账号")
    def test_mascontrol_cloudTrader(self, var_manager, logged_session, db_transaction):
        # 1. 发送新增策略账号请求
        cloudMaster_id = var_manager.get_variable("cloudMaster_id")
        user_ids_cloudTrader_2 = var_manager.get_variable("user_ids_cloudTrader_2")
        data = {
            "cloudId": cloudMaster_id,
            "sourceType": 0,
            "remark": "新增云策略账号",
            "runningStatus": 0,
            "traderId": user_ids_cloudTrader_2,
            "managerIp": "",
            "managerAccount": "",
            "managerPassword": "",
            "account": "",
            "platform": "",
            "templateId": ""
        }
        response = self.send_post_request(
            logged_session,
            '/mascontrol/cloudTrader',
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "新增策略账号失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-VPS数据-新增策略账号")
    def test_dbquery_trader(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            user_accounts_cloudTrader_2 = var_manager.get_variable("user_accounts_cloudTrader_2")
            follow_trader = var_manager.get_variable("follow_trader")

            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM {follow_trader} WHERE account = %s",
                (user_accounts_cloudTrader_2,),
            )

            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            vpsid_cloudTrader_2 = db_data[0]["id"]
            logging.info(f"新增策略账号ID: {vpsid_cloudTrader_2}")
            var_manager.set_runtime_variable("vpsid_cloudTrader_2", vpsid_cloudTrader_2)

            # 定义验证函数
            def verify_order_status():
                status = db_data[0]["status"]
                if status != 0:
                    pytest.fail(f"新增策略账号状态status应为0（正常），实际状态为: {status}")
                euqit = db_data[0]["euqit"]
                if euqit == 0:
                    pytest.fail(f"账号净值euqit有钱，实际金额为: {euqit}")

            # 执行验证
            try:
                verify_order_status()
                allure.attach("账号基础信息校验通过", "成功详情", allure.attachment_type.TEXT)
            except AssertionError as e:
                allure.attach(str(e.args[0]), "账号基础信息校验失败", allure.attachment_type.TEXT)
                raise
