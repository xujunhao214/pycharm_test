import time
import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuan_1024.VAR.VAR import *
from lingkuan_1024.conftest import var_manager
from lingkuan_1024.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("数据管理-创建数据-为VPS测试准备")
class TestCreate(APITestBase):
    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.retry(n=3, delay=5)
    @allure.title("账号管理-账号列表-新增单个用户")
    def test_create_user(self, logged_session, var_manager, encrypted_password):
        # 1. 发送创建用户请求
        new_user = var_manager.get_variable("new_user")
        data = {
            "account": new_user["account"],
            "password": encrypted_password,
            "platform": new_user["platform"],
            "platformType": 0,
            "serverNode": new_user["serverNode"],
            "remark": new_user["remark"],
            "sort": "12",
            "vpsDescs": []
        }
        response = self.send_post_request(
            logged_session,
            "/mascontrol/user",
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "新增单个用户失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-账号列表-新增用户")
    def test_dbquery_user(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            new_user = var_manager.get_variable("new_user")

            # 优化后的数据库查询
            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM FOLLOW_TRADER_USER WHERE account = %s",
                (new_user["account"],),
            )

            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            vps_trader_user_id = db_data[0]["id"]
            print(f"输出：{vps_trader_user_id}")
            logging.info(f"新增用户ID: {vps_trader_user_id}")
            var_manager.set_runtime_variable("vps_trader_user_id", vps_trader_user_id)