import time

import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuan_714.VAR.VAR import *
from lingkuan_714.conftest import var_manager
from lingkuan_714.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("跟单软件看板")
class TestDeleteFollowSlave(APITestBase):
    # ---------------------------
    # 账号管理-账号列表-删除账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-账号列表-删除账号")
    def test_delete_user(self, api_session, var_manager, logged_session, db_transaction):
        """测试删除用户接口"""
        # 1. 发送删除用户请求
        trader_user_id = var_manager.get_variable("trader_user_id")
        response = self.send_delete_request(
            api_session,
            "/mascontrol/user",
            json_data=[trader_user_id]
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "删除用户失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # ---------------------------
    # 数据库校验-账号列表-删除账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-账号列表-删除账号")
    def test_dbdelete_user(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            new_user = var_manager.get_variable("new_user")
            logging.info(f"查询条件: table=FOLLOW_TRADER_USER, name={new_user['account']}")

            # 定义数据库查询
            sql = f"SELECT * FROM FOLLOW_TRADER_USER WHERE account = %s"
            params = (new_user["account"],)
            try:
                self.wait_for_database_deletion(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    timeout=DELETE_WAIT_TIMEOUT,  # 设置5秒超时时间
                    poll_interval=POLL_INTERVAL  # 每2秒查询一次
                )
                allure.attach(f"账号 {new_user['account']} 已成功从数据库删除", "验证结果")
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果")
                pytest.fail(f"删除失败: {str(e)}")