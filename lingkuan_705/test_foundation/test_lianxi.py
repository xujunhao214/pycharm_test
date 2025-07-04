import time

import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuan_705.VAR.VAR import *
from lingkuan_705.conftest import var_manager
from lingkuan_705.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("跟单软件看板")
class TestDeleteFollowSlave(APITestBase):
    # ---------------------------
    # 账号管理-账号列表-修改用户
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("账号管理-账号列表-修改用户")
    def test_update_user(self, api_session, var_manager, logged_session, db_transaction):
        # 1. 发送创建用户请求
        new_user = var_manager.get_variable("new_user")
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        password = var_manager.get_variable("password")
        data = {
            "id": vps_trader_id,
            "account": new_user["account"],
            "password": password,
            "remark": "测试数据",
            "followStatus": 1,
            "templateId": 1,
            "type": 0,
            "cfd": "",
            "forex": "",
            "platform": new_user["platform"]
        }
        response = self.send_put_request(
            api_session,
            "/subcontrol/trader",
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "编辑策略信息失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # ---------------------------
    # 数据库校验-账号列表-修改用户
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-账号列表-修改用户是否成功")
    def test_dbupdate_user(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否编辑成功"):
            db_query = var_manager.get_variable("db_query")
            sql = f"SELECT * FROM {db_query['table_trader']} WHERE account = %s"
            params = (db_query["account"],)

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                timeout=WAIT_TIMEOUT,  # 最多等60秒
                poll_interval=POLL_INTERVAL,  # 每2秒查一次
                order_by="create_time DESC"  # 按创建时间倒序
            )

            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")
            cfd_value = db_data[0]["cfd"]
            # 允许为 None 或空字符串（去除空格后）
            assert cfd_value is None or cfd_value.strip() == "", f"修改个人信息失败（cfd字段应为空，实际值：{cfd_value}）"
