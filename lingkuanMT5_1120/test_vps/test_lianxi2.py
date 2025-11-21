import allure
import logging
import pytest
import time
from lingkuanMT5_1120.conftest import var_manager
from lingkuanMT5_1120.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("VPS策略账号交易下单-开仓的场景校验")
class TestVPSMasOrdersend(APITestBase):
    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-新增策略账号")
    def test_add_trader(self, class_random_str, var_manager, logged_session, encrypted_password):
        # 1. 发送新增策略账号请求
        new_user = var_manager.get_variable("new_user")
        data = {
            "type": 0,
            "account": new_user["account"],
            "password": encrypted_password,
            "platform": new_user["platform"],
            "remark": "",
            "platformId": "",
            "templateId": 1,
            "followStatus": 1,
            "cfd": "",
            "forex": "",
            "followOrderRemark": 1,
            "fixedComment": "",
            "commentType": "",
            "digits": "",
            "platformType": 1,
            "followTraderSymbolEntityList": []
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
    def test_dbquery_trader(self, class_random_str, var_manager, db_transaction):
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
                pytest.fail("数据库查询结果为空")

            MT5vps_trader_id = db_data[0]["id"]
            logging.info(f"新增策略账号ID: {MT5vps_trader_id}")
            var_manager.set_runtime_variable("MT5vps_trader_id", MT5vps_trader_id)

        with allure.step("2. 数据校验"):
            status = db_data[0]["status"]
            assert status == 0, f"新增策略账号状态status应为0（正常），实际状态为: {status}"
            logging.info(f"新增策略账号状态status应为0（正常），实际状态为: {status}")

            euqit = db_data[0]["euqit"]
            assert euqit >= 0, f"账号净值euqit有钱，实际金额为: {euqit}"
            logging.info(f"账号净值euqit有钱，实际金额为: {euqit}")
