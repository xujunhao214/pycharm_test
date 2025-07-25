import time

import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuan_UAT.VAR.VAR import *
from lingkuan_UAT.conftest import var_manager
from lingkuan_UAT.commons.api_base import APITestBase  # 导入基础类
from lingkuan_UAT.commons.redis_utils import *

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("跟单软件看板")
class TestDeleteFollowSlave(APITestBase):
    # ---------------------------
    # 账号管理-账号列表-批量新增用户
    # ---------------------------
    @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-账号列表-批量新增用户")
    def test_create_importuser(self, api_session, var_manager, logged_session, db_transaction):
        """验证数据库"""
        adduser = var_manager.get_variable("adduser")
        with open(adduser["csv_user_path"], 'rb') as f:
            csv_file = f.read()

        # 构造请求参数（文件上传使用files参数）
        files = {
            "file": ("账号列表数据.csv", csv_file, "text/csv")
        }

        # 1. 发送创建用户请求
        response = self.send_post_request(
            api_session,
            "/mascontrol/user/import",
            files=files
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "批量新增用户失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # ---------------------------
    # 数据库校验-账号列表-批量新增用户
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-账号列表-批量新增用户")
    def test_dbquery__importuser(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            new_user = var_manager.get_variable("new_user")

            # 执行数据库查询
            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM FOLLOW_TRADER_USER WHERE remark = %s",
                (new_user["remarkimport"],),
            )

            # 验证查询结果
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            # 提取user_ids和user_accounts（保持原有列表形式，用于后续判断）
            user_ids = [item["id"] for item in db_data]
            user_accounts = [item["account"] for item in db_data]

            print(f"提取到用户ID列表: {user_ids}")
            print(f"提取到用户账号列表: {user_accounts}")

            # 将列表拆分为单独的变量
            for i, (user_id, account) in enumerate(zip(user_ids, user_accounts), 1):
                var_manager.set_runtime_variable(f"user_ids_{i}", user_id)
                var_manager.set_runtime_variable(f"user_accounts_{i}", account)
                print(f"已设置变量: user_ids_{i}={user_id}, user_accounts_{i}={account}")

            # 保存总数，便于后续参数化使用
            var_manager.set_runtime_variable("user_count", len(user_ids))
            print(f"共提取{len(user_ids)}个用户数据")
