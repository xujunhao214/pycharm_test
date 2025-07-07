import time

import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuan_7061.VAR.VAR import *
from lingkuan_7061.conftest import var_manager
from lingkuan_7061.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("跟单软件看板")
class TestDeleteFollowSlave(APITestBase):
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-VPS数据-新增策略账号")
    def test_dbquery_trader(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            db_trader_query = var_manager.get_variable("db_trader_query")

            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM {db_trader_query['table']} WHERE account = %s",
                (db_trader_query["account"],),
            )

            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            vps_trader_id = db_data[0]["id"]
            logging.info(f"新增策略账号ID: {vps_trader_id}")
            var_manager.set_runtime_variable("vps_trader_id", vps_trader_id)

            # 定义验证函数
            def verify_order_status():
                status = db_data[0]["status"]
                if status != 0:
                    pytest.fail(f"新增跟单账号状态status应为0（正常），实际状态为: {status}")
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