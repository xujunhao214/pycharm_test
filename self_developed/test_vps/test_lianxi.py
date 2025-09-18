import time
import math
import allure
import logging
import pytest
import re
from self_developed.VAR.VAR import *
from self_developed.conftest import var_manager
from self_developed.commons.api_base import *
from self_developed.commons.jsonpath_utils import *

logger = logging.getLogger(__name__)
SKIP_REASON = "该用例暂时跳过"


# ------------------------------------
# 大模块4：VPS策略下单-平仓的订单类型功能验证
# ------------------------------------
@allure.feature("VPS策略下单-平仓的功能校验")
# @pytest.mark.skipif(True, reason=SKIP_REASON)
class TestVPSOrderType(APITestBase):
    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-新增跟单账号")
    def test_create_addSlave(self, var_manager, logged_session, encrypted_password):
        # 1. 发送新增策略账号请求
        new_user = var_manager.get_variable("new_user")
        vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        data = {
            "traderId": vps_trader_id,
            "platform": new_user["platform"],
            "account": vps_user_accounts_1,
            "password": encrypted_password,
            "remark": new_user["remark"],
            "followDirection": 0,
            "followMode": 1,
            "remainder": 0,
            "followParam": 1,
            "placedType": 0,
            "templateId": 1,
            "followStatus": 1,
            "followOpen": 1,
            "followClose": 1,
            "followRep": 0,
            "fixedComment": "",
            "commentType": "",
            "digits": 0,
            "cfd": "",
            "forex": "",
            "abRemark": ""
        }
        response = self.send_post_request(
            logged_session,
            '/subcontrol/follow/addSlave',
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "创建用户失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-VPS数据-新增跟单账号")
    def test_dbquery_addslave(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
            # 执行数据库查询
            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_trader WHERE account = %s",
                (vps_user_accounts_1,)
            )

            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            vps_addslave_id = db_data[0]["id"]
            logging.info(f"新增跟单账号ID: {vps_addslave_id}")
            var_manager.set_runtime_variable("vps_addslave_id", vps_addslave_id)

        with allure.step("2. 校验账号状态和净值"):
            status = db_data[0]["status"]
            assert status == 0, f"账号 {vps_user_accounts_1} 状态异常：预期status=0，实际={status}"
            logging.info(f"账号 {vps_user_accounts_1} 状态异常：预期status=0，实际={status}")

            euqit = db_data[0]["euqit"]
            assert euqit > 0, f"账号 {vps_user_accounts_1} 净值异常：预期euqit≠0，实际={euqit}"
            logging.info(f"账号 {vps_user_accounts_1} 净值异常：预期euqit≠0，实际={euqit}")

            db_data2 = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_trader_subscribe WHERE slave_account = %s",
                (vps_user_accounts_1,)
            )

            if not db_data2:
                pytest.fail("数据库查询结果为空，无法提取数据")

            slave_account = db_data2[0]["slave_account"]
            assert slave_account == vps_user_accounts_1, f"账号新增失败，新增账号：{vps_user_accounts_1}  数据库账号:{slave_account}"
            logging.info(f"账号新增成功，新增账号：{vps_user_accounts_1}  数据库账号:{slave_account}")
