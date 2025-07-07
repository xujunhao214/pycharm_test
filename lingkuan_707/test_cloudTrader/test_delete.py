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


@allure.feature("删除基本账号-云策略账号")
class TestDelete_cloudTrader(APITestBase):
    # ---------------------------
    # 账号管理-账号列表-批量删除账号（参数化）
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-账号列表-批量删除账号")
    def test_delete_userlist(self, api_session, var_manager, logged_session, db_transaction):
        """测试批量删除用户接口"""
        # 1. 获取需要删除的账号总数（从新增阶段的变量获取，确保与新增数量一致）
        user_count_cloudTrader = var_manager.get_variable("user_count_cloudTrader", 0)
        if user_count_cloudTrader <= 0:
            pytest.fail("未找到需要删除的账号总数，请检查前置步骤")

        # 2. 循环删除每个账号
        for i in range(1, user_count_cloudTrader + 1):
            with allure.step(f"删除第{i}个账号"):
                # 获取单个账号ID
                user_id = var_manager.get_variable(f"user_ids_cloudTrader_{i}")
                if not user_id:
                    pytest.fail(f"未找到第{i}个账号的ID（变量名：user_ids_cloudTrader_{i}）")

                # 发送删除请求（接口支持传入ID列表，这里单次删除一个）
                response = self.send_delete_request(
                    api_session,
                    "/mascontrol/user",
                    json_data=[user_id]  # 保持接口要求的列表格式
                )

                # 3. 验证响应状态码
                self.assert_response_status(
                    response,
                    200,
                    f"删除第{i}个账号（ID: {user_id}）失败"
                )

                # 4. 验证响应内容
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    f"第{i}个账号删除响应msg字段应为success"
                )

                logging.info(f"第{i}个账号（ID: {user_id}）删除接口调用成功")

    # ---------------------------
    # 数据库校验-批量删除账号（参数化）
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-账号列表-批量删除账号")
    def test_dbdelete_userlist(self, var_manager, db_transaction):
        """数据库校验批量删除结果"""
        # 1. 获取账号总数和数据库查询配置
        user_count_cloudTrader = var_manager.get_variable("user_count_cloudTrader", 0)
        if user_count_cloudTrader <= 0:
            pytest.fail("未找到需要验证的账号总数，请检查前置步骤")

        db_query = var_manager.get_variable("db_query")
        if not db_query or "table" not in db_query:
            pytest.fail("数据库查询配置不完整（缺少table）")

        # 2. 循环验证每个账号的删除状态
        for i in range(1, user_count_cloudTrader + 1):
            with allure.step(f"验证第{i}个账号的删除状态"):
                # 获取当前账号的ID和账号名（用于数据库查询）
                user_id = var_manager.get_variable(f"user_ids_cloudTrader_{i}")
                account = var_manager.get_variable(f"user_accounts_cloudTrader_{i}")  # 账号名，如119999353
                if not account:
                    pytest.fail(f"未找到第{i}个账号的账号名（变量名：user_accounts_cloudTrader_{i}）")

                # 3. 执行数据库查询（按账号名查询，更直观）
                sql = f"SELECT * FROM {db_query['table']} WHERE account = %s"
                params = (account,)

                try:
                    self.wait_for_database_deletion(
                        db_transaction=db_transaction,
                        sql=sql,
                        params=params,
                        timeout=WAIT_TIMEOUT,  # 设置30秒超时时间
                        poll_interval=POLL_INTERVAL  # 每2秒查询一次
                    )
                    allure.attach(f"账号 {account} 已成功从数据库删除", "验证结果")
                except TimeoutError as e:
                    allure.attach(f"删除超时: {str(e)}", "验证结果")
                    pytest.fail(f"删除失败: {str(e)}")
