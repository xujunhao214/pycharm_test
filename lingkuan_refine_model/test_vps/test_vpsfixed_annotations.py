import time
import math
import allure
import logging
import pytest
from lingkuan_819.VAR.VAR import *
from lingkuan_819.conftest import var_manager
from lingkuan_819.commons.api_base import APITestBase

logger = logging.getLogger(__name__)
SKIP_REASON = "该用例暂时跳过"


@allure.feature("VPS策略下单-跟随策略账号订单备注")
@allure.description("""
### 用例说明
- 前置条件：有vps策略和vps跟单，验证三种备注场景的跟单行为
- 三种场景：
  1. 策略有固定注释，跟单无固定注释 → 预期：跟单取策略备注
  2. 策略有固定注释，跟单有固定注释 → 预期：跟单取自身备注
  3. 策略开启订单备注，跟单无固定注释 → 预期：跟单取开仓备注
""")
class TestVPSOrderSend_AllRemarkScenarios(APITestBase):
    """合并三种备注情况的测试类，通过Story区分场景"""

    # -------------------------- 第一种情况：策略有备注，跟单无备注 --------------------------
    @allure.story("场景1：策略有固定注释，跟单无固定注释")
    @pytest.mark.url("vps")
    @allure.title("修改策略账号信息（场景1）")
    def test_scenario1_subcontrol_trader(self, var_manager, logged_session, encrypted_password):
        new_user = var_manager.get_variable("new_user")
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        platformId = var_manager.get_variable("platformId")
        json_data = {
            "id": vps_trader_id,
            "type": 0,
            "account": new_user["account"],
            "password": encrypted_password,
            "platform": new_user["platform"],
            "remark": "测试数据",
            "platformId": platformId,
            "templateId": 1,
            "followStatus": 1,
            "cfd": "",
            "forex": "",
            "followOrderRemark": 0,  # 关闭跟单备注，使用策略备注
            "fixedComment": "ceshiceluebeizhu",
            "commentType": None,
            "digits": 0
        }
        response = self.send_put_request(
            logged_session,
            '/subcontrol/trader',
            json_data=json_data,
        )
        self.assert_response_status(response, 200, "修改vps策略信息失败（场景1）")
        self.assert_json_value(response, "$.msg", "success", "响应msg应为success（场景1）")

    @allure.story("场景1：策略有固定注释，跟单无固定注释")
    @pytest.mark.url("vps")
    @allure.title("修改跟单账号（场景1：无固定注释）")
    def test_scenario1_follow_updateSlave(self, var_manager, logged_session, encrypted_password):
        new_user = var_manager.get_variable("new_user")
        vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        vps_addslave_id = var_manager.get_variable("vps_addslave_id")
        platformId = var_manager.get_variable("platformId")
        data = {
            "traderId": vps_trader_id,
            "platform": new_user["platform"],
            "account": vps_user_accounts_1,
            "password": encrypted_password,
            "remark": "",
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
            "fixedComment": "",  # 跟单无固定注释
            "commentType": "",
            "digits": 0,
            "cfd": "",
            "forex": "",
            "abRemark": "",
            "id": vps_addslave_id,
            "platformId": platformId
        }
        response = self.send_post_request(
            logged_session,
            '/subcontrol/follow/updateSlave',
            json_data=data
        )
        self.assert_response_status(response, 200, "修改跟单账号失败（场景1）")
        self.assert_json_value(response, "$.msg", "success", "响应msg应为success（场景1）")

    @allure.story("场景1：策略有固定注释，跟单无固定注释")
    @pytest.mark.url("vps")
    @allure.title("策略开仓及备注校验（场景1）")
    def test_scenario1_trader_orderSend_and_verify(self, var_manager, logged_session, db_transaction):
        # 1. 开仓请求
        trader_ordersend = var_manager.get_variable("trader_ordersend")
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        data = {
            "symbol": trader_ordersend["symbol"],
            "placedType": 0,
            "remark": "ceshikaicangbeizhu",
            "intervalTime": 100,
            "type": 0,
            "totalNum": trader_ordersend["totalNum"],
            "totalSzie": trader_ordersend["totalSzie"],
            "startSize": trader_ordersend["startSize"],
            "endSize": trader_ordersend["endSize"],
            "traderId": vps_trader_id
        }
        response = self.send_post_request(
            logged_session,
            '/subcontrol/trader/orderSend',
            json_data=data,
        )
        self.assert_response_status(response, 200, "策略开仓失败（场景1）")
        self.assert_json_value(response, "$.msg", "success", "响应msg应为success（场景1）")

        # 2. 数据库校验
        vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
        sql = """
            SELECT fod.account, fod.comment, foi.operation_type, foi.create_time
            FROM follow_order_detail fod
            INNER JOIN follow_order_instruct foi 
                ON foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
            WHERE foi.operation_type = %s AND fod.account = %s
        """
        params = ('0', vps_user_accounts_1)
        db_data = self.wait_for_database_record(
            db_transaction=db_transaction,
            sql=sql,
            params=params,
            time_field="foi.create_time"
        )
        if not db_data:
            pytest.fail("数据库查询结果为空（场景1）")
        comment = db_data[0]["comment"]
        assert comment == "ceshiceluebeizhu", f"场景1备注错误，实际：{comment}"

    @allure.story("场景1：策略有固定注释，跟单无固定注释")
    @pytest.mark.url("vps")
    @allure.title("平仓操作（场景1）")
    def test_scenario1_close_orders(self, var_manager, logged_session):
        # 策略平仓
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        new_user = var_manager.get_variable("new_user")
        response = self.send_post_request(
            logged_session,
            '/subcontrol/trader/orderClose',
            json_data={"isCloseAll": 1, "intervalTime": 100, "traderId": vps_trader_id, "account": new_user["account"]}
        )
        self.assert_response_status(response, 200, "策略平仓失败（场景1）")

        # 跟单平仓
        vps_addslave_id = var_manager.get_variable("vps_addslave_id")
        vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
        response = self.send_post_request(
            logged_session,
            '/subcontrol/trader/orderClose',
            json_data={"isCloseAll": 1, "intervalTime": 100, "traderId": vps_addslave_id,
                       "account": vps_user_accounts_1}
        )
        self.assert_response_status(response, 200, "跟单平仓失败（场景1）")

    # -------------------------- 第二种情况：策略有备注，跟单有备注 --------------------------
    @allure.story("场景2：策略有固定注释，跟单有固定注释")
    @pytest.mark.url("vps")
    @allure.title("修改策略账号信息（场景2）")
    def test_scenario2_subcontrol_trader(self, var_manager, logged_session, encrypted_password):
        new_user = var_manager.get_variable("new_user")
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        platformId = var_manager.get_variable("platformId")
        json_data = {
            "id": vps_trader_id,
            "type": 0,
            "account": new_user["account"],
            "password": encrypted_password,
            "platform": new_user["platform"],
            "remark": "测试数据",
            "platformId": platformId,
            "templateId": 1,
            "followStatus": 1,
            "cfd": "",
            "forex": "",
            "followOrderRemark": 0,
            "fixedComment": "ceshiceluebeizhu",  # 策略有固定注释
            "commentType": None,
            "digits": 0
        }
        response = self.send_put_request(logged_session, '/subcontrol/trader', json_data=json_data)
        self.assert_response_status(response, 200, "修改vps策略信息失败（场景2）")
        self.assert_json_value(response, "$.msg", "success", "响应msg应为success（场景2）")

    @allure.story("场景2：策略有固定注释，跟单有固定注释")
    @pytest.mark.url("vps")
    @allure.title("修改跟单账号（场景2：有固定注释）")
    def test_scenario2_follow_updateSlave(self, var_manager, logged_session, encrypted_password):
        new_user = var_manager.get_variable("new_user")
        vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        vps_addslave_id = var_manager.get_variable("vps_addslave_id")
        platformId = var_manager.get_variable("platformId")
        data = {
            "traderId": vps_trader_id,
            "platform": new_user["platform"],
            "account": vps_user_accounts_1,
            "password": encrypted_password,
            "remark": "",
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
            "fixedComment": "ceshigendanbeizhu",  # 跟单有固定注释
            "commentType": "",
            "digits": 0,
            "cfd": "",
            "forex": "",
            "abRemark": "",
            "id": vps_addslave_id,
            "platformId": platformId
        }
        response = self.send_post_request(
            logged_session,
            '/subcontrol/follow/updateSlave',
            json_data=data
        )
        self.assert_response_status(response, 200, "修改跟单账号失败（场景2）")
        self.assert_json_value(response, "$.msg", "success", "响应msg应为success（场景2）")

    @allure.story("场景2：策略有固定注释，跟单有固定注释")
    @pytest.mark.url("vps")
    @allure.title("策略开仓及备注校验（场景2）")
    def test_scenario2_trader_orderSend_and_verify(self, var_manager, logged_session, db_transaction):
        # 1. 开仓请求
        trader_ordersend = var_manager.get_variable("trader_ordersend")
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        data = {
            "symbol": trader_ordersend["symbol"],
            "placedType": 0,
            "remark": "ceshikaicangbeizhu",
            "intervalTime": 100,
            "type": 0,
            "totalNum": trader_ordersend["totalNum"],
            "totalSzie": trader_ordersend["totalSzie"],
            "startSize": trader_ordersend["startSize"],
            "endSize": trader_ordersend["endSize"],
            "traderId": vps_trader_id
        }
        response = self.send_post_request(
            logged_session,
            '/subcontrol/trader/orderSend',
            json_data=data,
        )
        self.assert_response_status(response, 200, "策略开仓失败（场景2）")

        # 2. 数据库校验
        vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
        sql = """
            SELECT fod.account, fod.comment, foi.operation_type, foi.create_time
            FROM follow_order_detail fod
            INNER JOIN follow_order_instruct foi 
                ON foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
            WHERE foi.operation_type = %s AND fod.account = %s
        """
        params = ('0', vps_user_accounts_1)
        db_data = self.wait_for_database_record(
            db_transaction=db_transaction,
            sql=sql,
            params=params,
            time_field="foi.create_time"
        )
        if not db_data:
            pytest.fail("数据库查询结果为空（场景2）")
        comment = db_data[0]["comment"]
        assert comment == "ceshigendanbeizhu", f"场景2备注错误，实际：{comment}"

    @allure.story("场景2：策略有固定注释，跟单有固定注释")
    @pytest.mark.url("vps")
    @allure.title("平仓操作（场景2）")
    def test_scenario2_close_orders(self, var_manager, logged_session):
        # 策略平仓
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        new_user = var_manager.get_variable("new_user")
        response = self.send_post_request(
            logged_session,
            '/subcontrol/trader/orderClose',
            json_data={"isCloseAll": 1, "intervalTime": 100, "traderId": vps_trader_id, "account": new_user["account"]}
        )
        self.assert_response_status(response, 200, "策略平仓失败（场景2）")

        # 跟单平仓
        vps_addslave_id = var_manager.get_variable("vps_addslave_id")
        vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
        response = self.send_post_request(
            logged_session,
            '/subcontrol/trader/orderClose',
            json_data={"isCloseAll": 1, "intervalTime": 100, "traderId": vps_addslave_id,
                       "account": vps_user_accounts_1}
        )
        self.assert_response_status(response, 200, "跟单平仓失败（场景2）")

    # -------------------------- 第三种情况：策略开启订单备注，跟单无备注 --------------------------
    @allure.story("场景3：策略开启订单备注，跟单无固定注释")
    @pytest.mark.url("vps")
    @allure.title("修改策略账号信息（场景3：开启订单备注）")
    def test_scenario3_subcontrol_trader(self, var_manager, logged_session, encrypted_password):
        new_user = var_manager.get_variable("new_user")
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        platformId = var_manager.get_variable("platformId")
        json_data = {
            "id": vps_trader_id,
            "type": 0,
            "account": new_user["account"],
            "password": encrypted_password,
            "platform": new_user["platform"],
            "remark": "测试数据",
            "platformId": platformId,
            "templateId": 1,
            "followStatus": 1,
            "cfd": "",
            "forex": "",
            "followOrderRemark": 1,  # 开启订单备注
            "fixedComment": "ceshiceluebeizhu",
            "commentType": None,
            "digits": 0
        }
        response = self.send_put_request(logged_session, '/subcontrol/trader', json_data=json_data)
        self.assert_response_status(response, 200, "修改vps策略信息失败（场景3）")
        self.assert_json_value(response, "$.msg", "success", "响应msg应为success（场景3）")

    @allure.story("场景3：策略开启订单备注，跟单无固定注释")
    @pytest.mark.url("vps")
    @allure.title("修改跟单账号（场景3：无固定注释）")
    def test_scenario3_follow_updateSlave(self, var_manager, logged_session, encrypted_password):
        new_user = var_manager.get_variable("new_user")
        vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        vps_addslave_id = var_manager.get_variable("vps_addslave_id")
        platformId = var_manager.get_variable("platformId")
        data = {
            "traderId": vps_trader_id,
            "platform": new_user["platform"],
            "account": vps_user_accounts_1,
            "password": encrypted_password,
            "remark": "",
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
            "fixedComment": "",  # 跟单无固定注释
            "commentType": "",
            "digits": 0,
            "cfd": "",
            "forex": "",
            "abRemark": "",
            "id": vps_addslave_id,
            "platformId": platformId
        }
        response = self.send_post_request(
            logged_session,
            '/subcontrol/follow/updateSlave',
            json_data=data
        )
        self.assert_response_status(response, 200, "修改跟单账号失败（场景3）")
        self.assert_json_value(response, "$.msg", "success", "响应msg应为success（场景3）")

    @allure.story("场景3：策略开启订单备注，跟单无固定注释")
    @pytest.mark.url("vps")
    @allure.title("策略开仓及备注校验（场景3）")
    def test_scenario3_trader_orderSend_and_verify(self, var_manager, logged_session, db_transaction):
        # 1. 开仓请求
        trader_ordersend = var_manager.get_variable("trader_ordersend")
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        data = {
            "symbol": trader_ordersend["symbol"],
            "placedType": 0,
            "remark": "ceshikaicangbeizhu",  # 开仓备注
            "intervalTime": 100,
            "type": 0,
            "totalNum": trader_ordersend["totalNum"],
            "totalSzie": trader_ordersend["totalSzie"],
            "startSize": trader_ordersend["startSize"],
            "endSize": trader_ordersend["endSize"],
            "traderId": vps_trader_id
        }
        response = self.send_post_request(
            logged_session,
            '/subcontrol/trader/orderSend',
            json_data=data,
        )
        self.assert_response_status(response, 200, "策略开仓失败（场景3）")
        self.assert_json_value(response, "$.msg", "success", "响应msg应为success（场景3）")

        # 2. 数据库校验（预期取开仓备注）
        vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
        sql = """
            SELECT fod.account, fod.comment, foi.operation_type, foi.create_time
            FROM follow_order_detail fod
            INNER JOIN follow_order_instruct foi 
                ON foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
            WHERE foi.operation_type = %s AND fod.account = %s
        """
        params = ('0', vps_user_accounts_1)
        db_data = self.wait_for_database_record(
            db_transaction=db_transaction,
            sql=sql,
            params=params,
            time_field="foi.create_time"
        )
        if not db_data:
            pytest.fail("数据库查询结果为空（场景3）")
        comment = db_data[0]["comment"]
        assert comment == "ceshikaicangbeizhu", f"场景3备注错误，实际：{comment}"

    @allure.story("场景3：策略开启订单备注，跟单无固定注释")
    @pytest.mark.url("vps")
    @allure.title("平仓操作（场景3）")
    def test_scenario3_close_orders(self, var_manager, logged_session):
        # 策略平仓
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        new_user = var_manager.get_variable("new_user")
        response = self.send_post_request(
            logged_session,
            '/subcontrol/trader/orderClose',
            json_data={"isCloseAll": 1, "intervalTime": 100, "traderId": vps_trader_id, "account": new_user["account"]}
        )
        self.assert_response_status(response, 200, "策略平仓失败（场景3）")

        # 跟单平仓
        vps_addslave_id = var_manager.get_variable("vps_addslave_id")
        vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
        response = self.send_post_request(
            logged_session,
            '/subcontrol/trader/orderClose',
            json_data={"isCloseAll": 1, "intervalTime": 100, "traderId": vps_addslave_id,
                       "account": vps_user_accounts_1}
        )
        self.assert_response_status(response, 200, "跟单平仓失败（场景3）")
