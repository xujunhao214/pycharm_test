import allure
import logging
import pytest
import time
from lingkuan_919.conftest import var_manager
from lingkuan_919.commons.api_base import *
from lingkuan_919.commons.redis_utils import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("VPS策略下单-开仓的场景校验")
class TestVPSOrdersend(APITestBase):
    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-新增策略账号")
    def test_add_trader(self, var_manager, logged_session, encrypted_password):
        # 1. 发送新增策略账号请求
        new_user = var_manager.get_variable("new_user")
        data = {
            "account": new_user["account"],
            "password": encrypted_password,
            "platform": new_user["platform"],
            "remark": new_user["remark"],
            "platformId": new_user["platformId"],
            "platformType": 0,
            "type": 0,
            "templateId": 1,
            "followStatus": 1,
            "cfd": "",
            "forex": "",
            "followOrderRemark": 1,
            "fixedComment": new_user["fixedComment"],
            "commentType": new_user["commentType"],
            "digits": new_user["digits"]
        }
        response = self.send_post_request(
            logged_session,
            '/subcontrol/trader',
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
            new_user = var_manager.get_variable("new_user")
            # 执行数据库查询
            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_trader WHERE account = %s",
                (new_user["account"],)
            )

            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            vps_trader_id = db_data[0]["id"]
            logging.info(f"新增策略账号ID: {vps_trader_id}")
            var_manager.set_runtime_variable("vps_trader_id", vps_trader_id)

        with allure.step("2. 数据校验"):
            status = db_data[0]["status"]
            assert status == 0, f"新增策略账号状态status应为0（正常），实际状态为: {status}"
            logging.info(f"新增策略账号状态status应为0（正常），实际状态为: {status}")

            euqit = db_data[0]["euqit"]
            assert euqit > 0, f"账号净值euqit有钱，实际金额为: {euqit}"
            logging.info(f"账号净值euqit有钱，实际金额为: {euqit}")

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
            "abRemark": "",
            "platformType": 0
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
