import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuan_702.VAR.VAR import *
from lingkuan_702.conftest import var_manager
from lingkuan_702.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("跟单软件看板")
class TestFollowSlave(APITestBase):
    # ---------------------------
    # 账号管理-账号列表-修改用户
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-账号列表-修改用户")
    def test_update_user(self, api_session, var_manager, logged_session, db_transaction):
        # 1. 发送创建用户请求
        new_user = var_manager.get_variable("new_user")
        trader_user_id = var_manager.get_variable("trader_user_id")
        password = var_manager.get_variable("password")
        data = {
            "id": trader_user_id,
            "account": new_user["account"],
            "password": password,
            "platform": new_user["platform"],
            "accountType": "0",
            "serverNode": new_user["serverNode"],
            "remark": "编辑个人用户",
            "sort": 12,
            "vpsDescs": [
                {
                    "desc": "39.99.136.49-主VPS-跟单策略",
                    "status": 0,
                    "statusExtra": "启动成功",
                    "forex": "",
                    "cfd": "",
                    "traderId": 5733,
                    "ipAddress": "39.99.136.49",
                    "sourceId": None,
                    "sourceAccount": None,
                    "sourceName": None,
                    "loginNode": "47.83.21.167:443",
                    "nodeType": 0,
                    "nodeName": "账号节点",
                    "type": None,
                    "vpsId": 6,
                    "traderType": None,
                    "abRemark": None
                }
            ]
        }
        response = self.send_put_request(
            api_session,
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

    # ---------------------------
    # 数据库校验-账号列表-修改用户
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-账号列表-修改用户是否成功")
    def test_dbupdate_user(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否编辑成功"):
            db_query = var_manager.get_variable("db_query")

            # 优化后的数据库查询
            db_data = self.query_database(
                db_transaction,
                f"SELECT cfd FROM {db_query['table_trader']} WHERE account = %s",
                (db_query["account"],),
            )

            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")
            cfd_value = db_data[0]["cfd"]
            # 允许为 None 或空字符串（去除空格后）
            assert cfd_value is None or cfd_value.strip() == "", f"修改个人信息失败（cfd字段应为空，实际值：{cfd_value}）"
