import time

import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuan_723.VAR.VAR import *
from lingkuan_723.conftest import var_manager
from lingkuan_723.commons.api_base import APITestBase  # 导入基础类
from lingkuan_723.commons.redis_utils import *

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("跟单软件看板")
class TestDeleteFollowSlave(APITestBase):
    # ---------------------------
    # 跟单软件看板-VPS数据-新增跟单账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-新增跟单账号")
    def test_create_addSlave(self, var_manager, logged_session, encrypted_password):
        # 1. 发送新增策略账号请求
        new_user = var_manager.get_variable("new_user")
        user_accounts_1 = var_manager.get_variable("user_accounts_1")
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        data = {
            "traderId": vps_trader_id,
            "platform": new_user["platform"],
            "account": user_accounts_1,
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
            "fixedComment": new_user["fixedComment"],
            "commentType": 2,
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
            user_accounts_1 = var_manager.get_variable("user_accounts_1")

            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_trader WHERE account = %s",
                (user_accounts_1,),
            )

            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            vps_addslave_id = db_data[0]["id"]
            logging.info(f"新增跟单账号ID: {vps_addslave_id}")
            var_manager.set_runtime_variable("vps_addslave_id", vps_addslave_id)

            # 定义验证函数
            def verify_order_status():
                status = db_data[0]["status"]
                if status != 0:
                    pytest.fail(f"新增跟单账号状态status应为0（正常），实际状态为: {status}")
                euqit = db_data[0]["euqit"]
                if euqit == 0:
                    pytest.fail(f"账号净值euqit有钱，实际金额为: {euqit}")
                logging.info(f"账号净值euqit有钱，实际金额为: {euqit}")

            # 执行验证
            try:
                verify_order_status()
                allure.attach("账号基础信息校验通过", "成功详情", allure.attachment_type.TEXT)
            except AssertionError as e:
                allure.attach(str(e.args[0]), "账号基础信息校验失败", allure.attachment_type.TEXT)
                raise

            db_data2 = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_trader_subscribe WHERE slave_account = %s",
                (user_accounts_1,),
            )

            if not db_data2:
                pytest.fail("数据库查询结果为空，无法提取数据")

            slave_account = db_data2[0]["slave_account"]
            if slave_account != user_accounts_1:
                pytest.fail(f"账号新增失败，新增账号：{user_accounts_1}  数据库账号:{slave_account}")
