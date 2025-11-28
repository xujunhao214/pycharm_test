import time
import math
import allure
import logging
import pytest
from lingkuan_827.VAR.VAR import *
from lingkuan_827.conftest import var_manager
from lingkuan_827.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("云策略交易下单-跟随策略账号订单备注")
@allure.description("""
### 测试说明
包含三种云策略订单备注场景的完整测试流程：
  1. 策略有固定注释，跟单无固定注释 → 预期：跟单取策略备注
  2. 策略有固定注释，跟单有固定注释 → 预期：跟单取自身备注
  3. 策略开启订单备注，跟单无固定注释 → 预期：跟单取开仓备注
""")
class TestCloudStrategyOrderRemark(APITestBase):
    """整合云策略三种备注场景的测试类"""

    # -------------------------- 场景1：策略有备注，跟单无备注 --------------------------
    @allure.story("场景1：策略有固定注释，跟单无固定注释")
    @allure.title("修改云策略信息（关闭跟单备注）")
    def test_scenario1_update_strategy(self, var_manager, logged_session):
        with allure.step("发送修改云策略请求"):
            new_user = var_manager.get_variable("new_user")
            cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")
            cloudMaster_id = var_manager.get_variable("cloudMaster_id")
            cloudTrader_vps_ids_1 = var_manager.get_variable("cloudTrader_vps_ids_1")
            cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")

            json_data = {
                "id": cloudTrader_traderList_2,
                "cloudId": cloudMaster_id,
                "sourceType": 0,
                "remark": "",
                "runningStatus": 0,
                "followOrderRemark": 0,
                "traderId": cloudTrader_vps_ids_1,
                "managerIp": None,
                "managerAccount": None,
                "account": cloudTrader_user_accounts_2,
                "platform": new_user["platform"],
                "templateId": None,
                "fixedComment": "ceshiceluebeizhu",  # 策略固定注释
                "commentType": None,
                "digits": 0
            }

            response = self.send_put_request(
                logged_session,
                '/mascontrol/cloudTrader',
                json_data=json_data
            )

        with allure.step("验证修改结果"):
            self.assert_response_status(response, 200, "修改云策略请求失败")
            self.assert_json_value(response, "$.msg", "success", "响应msg应为success")

    @allure.story("场景1：策略有固定注释，跟单无固定注释")
    @allure.title("修改跟单账号（无固定注释）")
    def test_scenario1_update_follower(self, var_manager, logged_session):
        with allure.step("发送修改跟单账号请求"):
            cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
            cloudMaster_id = var_manager.get_variable("cloudMaster_id")
            cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")
            cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")

            data = [{
                "traderList": [cloudTrader_traderList_4],
                "cloudId": f"{cloudMaster_id}",
                "masterId": cloudTrader_traderList_2,
                "masterAccount": cloudTrader_user_accounts_2,
                "followDirection": 0,
                "followMode": 1,
                "followParam": 1,
                "remainder": 0,
                "placedType": 0,
                "templateId": 1,
                "followStatus": 1,
                "followOpen": 1,
                "followClose": 1,
                "fixedComment": "",
                "commentType": None,
                "digits": 0,
                "followTraderIds": [],
                "sort": 100,
                "remark": "",
                "cfd": None,
                "forex": None
            }]

            response = self.send_post_request(
                logged_session,
                '/mascontrol/cloudTrader/cloudBatchUpdate',
                json_data=data
            )

        with allure.step("验证修改结果"):
            self.assert_response_status(response, 200, "修改跟单账号请求失败")
            self.assert_json_value(response, "$.msg", "success", "响应msg应为success")

    @allure.story("场景1：策略有固定注释，跟单无固定注释")
    @allure.title("云策略账号复制下单")
    def test_scenario1_place_order(self, logged_session, var_manager):
        with allure.step("发送开仓请求"):
            self.cloudTrader_user_ids_2 = var_manager.get_variable("cloudTrader_user_ids_2")
            data = {
                "traderList": [self.cloudTrader_user_ids_2],
                "type": 0,
                "tradeType": 1,
                "intervalTime": 0,
                "symbol": "XAUUSD",
                "placedType": 0,
                "startSize": "0.10",
                "endSize": "1.00",
                "totalNum": "3",
                "totalSzie": "1.00",
                "remark": "ceshikaicangbeizhu"
            }

            response = self.send_post_request(
                logged_session,
                '/bargain/masOrderSend',
                json_data=data,
                sleep_seconds=0
            )

        with allure.step("验证开仓结果"):
            self.assert_json_value(response, "$.msg", "success", "响应msg应为success")

    @allure.story("场景1：策略有固定注释，跟单无固定注释")
    @allure.title("数据库校验-策略备注生效")
    def test_scenario1_verify_remark(self, var_manager, db_transaction):
        with allure.step("查询订单备注信息"):
            cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
            sql = """
                SELECT 
                fod.comment 
                FROM follow_order_detail fod
                INNER JOIN follow_order_instruct foi 
                    ON foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
                WHERE foi.operation_type = %s AND fod.account = %s
            """
            params = ('0', cloudTrader_user_accounts_4)

            db_data = self.query_database_with_time(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="foi.create_time",
                order_by="fod.comment DESC"
            )

        with allure.step("验证备注信息"):
            comment = db_data[0]["comment"]
            self.verify_data(
                actual_value=comment,
                expected_value="ceshiceluebeizhu",
                op=CompareOp.EQ,
                use_isclose=False,
                message=f"预期：跟单取策略备注",
                attachment_name="备注详情"
            )
            logger.info(f"备注验证通过: {comment}")

    @allure.story("场景1：策略有固定注释，跟单无固定注释")
    @allure.title("策略平仓操作")
    def test_scenario1_close_orders(self, logged_session, var_manager):
        with allure.step("策略账号平仓"):
            cloudTrader_user_ids_2 = var_manager.get_variable("cloudTrader_user_ids_2")
            response = self.send_post_request(
                logged_session,
                '/bargain/masOrderClose',
                json_data={
                    "isCloseAll": 1,
                    "intervalTime": 0,
                    "traderList": [cloudTrader_user_ids_2]
                }
            )
            self.assert_json_value(response, "$.msg", "success", "策略平仓失败")

        with allure.step("跟单账号平仓"):
            cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
            response = self.send_post_request(
                logged_session,
                '/mascontrol/cloudTrader/orderClose',
                json_data={
                    "traderUserId": cloudTrader_traderList_4,
                    "isCloseAll": 1
                }
            )
            self.assert_response_status(response, 200, "跟单平仓失败")
            self.assert_json_value(response, "$.msg", "success", "跟单平仓响应错误")

    # -------------------------- 场景2：策略有备注，跟单有备注 --------------------------
    @allure.story("场景2：策略有固定注释，跟单有固定注释")
    @allure.title("修改云策略信息（关闭跟单备注）")
    def test_scenario2_update_strategy(self, var_manager, logged_session):
        with allure.step("发送修改云策略请求"):
            new_user = var_manager.get_variable("new_user")
            cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")
            cloudMaster_id = var_manager.get_variable("cloudMaster_id")
            cloudTrader_vps_ids_1 = var_manager.get_variable("cloudTrader_vps_ids_1")
            cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")

            json_data = {
                "id": cloudTrader_traderList_2,
                "cloudId": cloudMaster_id,
                "sourceType": 0,
                "remark": "",
                "runningStatus": 0,
                "followOrderRemark": 0,
                "traderId": cloudTrader_vps_ids_1,
                "managerIp": None,
                "managerAccount": None,
                "account": cloudTrader_user_accounts_2,
                "platform": new_user["platform"],
                "templateId": None,
                "fixedComment": "ceshiceluebeizhu",  # 策略固定注释
                "commentType": None,
                "digits": 0
            }

            response = self.send_put_request(
                logged_session,
                '/mascontrol/cloudTrader',
                json_data=json_data
            )

        with allure.step("验证修改结果"):
            self.assert_response_status(response, 200, "修改云策略请求失败")
            self.assert_json_value(response, "$.msg", "success", "响应msg应为success")

    @allure.story("场景2：策略有固定注释，跟单有固定注释")
    @allure.title("修改跟单账号（有固定注释）")
    def test_scenario2_update_follower(self, var_manager, logged_session):
        with allure.step("发送修改跟单账号请求"):
            cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
            cloudMaster_id = var_manager.get_variable("cloudMaster_id")
            cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")
            cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")

            data = [{
                "traderList": [cloudTrader_traderList_4],
                "cloudId": f"{cloudMaster_id}",
                "masterId": cloudTrader_traderList_2,
                "masterAccount": cloudTrader_user_accounts_2,
                "followDirection": 0,
                "followMode": 1,
                "followParam": 1,
                "remainder": 0,
                "placedType": 0,
                "templateId": 1,
                "followStatus": 1,
                "followOpen": 1,
                "followClose": 1,
                "fixedComment": "ceshigendanbeizhu",  # 跟单固定注释
                "commentType": None,
                "digits": 0,
                "followTraderIds": [],
                "sort": 100,
                "remark": "",
                "cfd": None,
                "forex": None
            }]

            response = self.send_post_request(
                logged_session,
                '/mascontrol/cloudTrader/cloudBatchUpdate',
                json_data=data
            )

        with allure.step("验证修改结果"):
            self.assert_response_status(response, 200, "修改跟单账号请求失败")
            self.assert_json_value(response, "$.msg", "success", "响应msg应为success")

    @allure.story("场景2：策略有固定注释，跟单有固定注释")
    @allure.title("云策略账号复制下单")
    def test_scenario2_place_order(self, logged_session, var_manager):
        with allure.step("发送开仓请求"):
            self.cloudTrader_user_ids_2 = var_manager.get_variable("cloudTrader_user_ids_2")
            data = {
                "traderList": [self.cloudTrader_user_ids_2],
                "type": 0,
                "tradeType": 1,
                "intervalTime": 0,
                "symbol": "XAUUSD",
                "placedType": 0,
                "startSize": "0.10",
                "endSize": "1.00",
                "totalNum": "3",
                "totalSzie": "1.00",
                "remark": "ceshikaicangbeizhu"
            }

            response = self.send_post_request(
                logged_session,
                '/bargain/masOrderSend',
                json_data=data,
                sleep_seconds=0
            )

        with allure.step("验证开仓结果"):
            self.assert_json_value(response, "$.msg", "success", "响应msg应为success")

    @allure.story("场景2：策略有固定注释，跟单有固定注释")
    @allure.title("数据库校验-跟单备注生效")
    def test_scenario2_verify_remark(self, var_manager, db_transaction):
        with allure.step("查询订单备注信息"):
            cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
            sql = """
                SELECT fod.comment 
                FROM follow_order_detail fod
                INNER JOIN follow_order_instruct foi 
                    ON foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
                WHERE foi.operation_type = %s AND fod.account = %s
            """
            params = ('0', cloudTrader_user_accounts_4)

            db_data = self.query_database_with_time(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="foi.create_time",
                order_by="fod.comment DESC"
            )

        with allure.step("验证备注信息"):
            comment = db_data[0]["comment"]
            self.verify_data(
                actual_value=comment,
                expected_value="ceshigendanbeizhu",
                op=CompareOp.EQ,
                use_isclose=False,
                message="预期：跟单取自身备注",
                attachment_name="备注详情"
            )
            logger.info(f"备注验证通过: {comment}")

    @allure.story("场景2：策略有固定注释，跟单有固定注释")
    @allure.title("策略平仓操作")
    def test_scenario2_close_orders(self, logged_session, var_manager):
        with allure.step("策略账号平仓"):
            cloudTrader_user_ids_2 = var_manager.get_variable("cloudTrader_user_ids_2")
            response = self.send_post_request(
                logged_session,
                '/bargain/masOrderClose',
                json_data={
                    "isCloseAll": 1,
                    "intervalTime": 0,
                    "traderList": [cloudTrader_user_ids_2]
                }
            )
            self.assert_json_value(response, "$.msg", "success", "策略平仓失败")

        with allure.step("跟单账号平仓"):
            cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
            response = self.send_post_request(
                logged_session,
                '/mascontrol/cloudTrader/orderClose',
                json_data={
                    "traderUserId": cloudTrader_traderList_4,
                    "isCloseAll": 1
                }
            )
            self.assert_response_status(response, 200, "跟单平仓失败")
            self.assert_json_value(response, "$.msg", "success", "跟单平仓响应错误")

    # -------------------------- 场景3：策略开启订单备注，跟单无备注 --------------------------
    @allure.story("场景3：策略开启订单备注，跟单无固定注释")
    @allure.title("修改云策略信息（开启跟单备注）")
    def test_scenario3_update_strategy(self, var_manager, logged_session):
        with allure.step("发送修改云策略请求"):
            new_user = var_manager.get_variable("new_user")
            cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")
            cloudMaster_id = var_manager.get_variable("cloudMaster_id")
            cloudTrader_vps_ids_1 = var_manager.get_variable("cloudTrader_vps_ids_1")
            cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")

            json_data = {
                "id": cloudTrader_traderList_2,
                "cloudId": cloudMaster_id,
                "sourceType": 0,
                "remark": "",
                "runningStatus": 0,
                "followOrderRemark": 1,  # 开启跟单备注
                "traderId": cloudTrader_vps_ids_1,
                "managerIp": None,
                "managerAccount": None,
                "account": cloudTrader_user_accounts_2,
                "platform": new_user["platform"],
                "templateId": None,
                "fixedComment": "ceshiceluebeizhu",  # 策略固定注释
                "commentType": None,
                "digits": 0
            }

            response = self.send_put_request(
                logged_session,
                '/mascontrol/cloudTrader',
                json_data=json_data
            )

        with allure.step("验证修改结果"):
            self.assert_response_status(response, 200, "修改云策略请求失败")
            self.assert_json_value(response, "$.msg", "success", "响应msg应为success")

    @allure.story("场景3：策略开启订单备注，跟单无固定注释")
    @allure.title("修改跟单账号（无固定注释）")
    def test_scenario3_update_follower(self, var_manager, logged_session):
        with allure.step("发送修改跟单账号请求"):
            cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
            cloudMaster_id = var_manager.get_variable("cloudMaster_id")
            cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")
            cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")

            data = [{
                "traderList": [cloudTrader_traderList_4],
                "cloudId": f"{cloudMaster_id}",
                "masterId": cloudTrader_traderList_2,
                "masterAccount": cloudTrader_user_accounts_2,
                "followDirection": 0,
                "followMode": 1,
                "followParam": 1,
                "remainder": 0,
                "placedType": 0,
                "templateId": 1,
                "followStatus": 1,
                "followOpen": 1,
                "followClose": 1,
                "fixedComment": "",
                "commentType": None,
                "digits": 0,
                "followTraderIds": [],
                "sort": 100,
                "remark": "",
                "cfd": None,
                "forex": None
            }]

            response = self.send_post_request(
                logged_session,
                '/mascontrol/cloudTrader/cloudBatchUpdate',
                json_data=data
            )

        with allure.step("验证修改结果"):
            self.assert_response_status(response, 200, "修改跟单账号请求失败")
            self.assert_json_value(response, "$.msg", "success", "响应msg应为success")

    @allure.story("场景3：策略开启订单备注，跟单无固定注释")
    @allure.title("云策略账号复制下单")
    def test_scenario3_place_order(self, logged_session, var_manager):
        with allure.step("发送开仓请求"):
            self.cloudTrader_user_ids_2 = var_manager.get_variable("cloudTrader_user_ids_2")
            data = {
                "traderList": [self.cloudTrader_user_ids_2],
                "type": 0,
                "tradeType": 1,
                "intervalTime": 0,
                "symbol": "XAUUSD",
                "placedType": 0,
                "startSize": "0.10",
                "endSize": "1.00",
                "totalNum": "3",
                "totalSzie": "1.00",
                "remark": "ceshikaicangbeizhu"
            }

            response = self.send_post_request(
                logged_session,
                '/bargain/masOrderSend',
                json_data=data,
                sleep_seconds=0
            )

        with allure.step("验证开仓结果"):
            self.assert_json_value(response, "$.msg", "success", "响应msg应为success")

    @allure.story("场景3：策略开启订单备注，跟单无固定注释")
    @allure.title("数据库校验-开仓备注生效")
    def test_scenario3_verify_remark(self, var_manager, db_transaction):
        with allure.step("查询订单备注信息"):
            cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
            sql = """
                SELECT fod.comment 
                FROM follow_order_detail fod
                INNER JOIN follow_order_instruct foi 
                    ON foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
                WHERE foi.operation_type = %s AND fod.account = %s
            """
            params = ('0', cloudTrader_user_accounts_4)

            db_data = self.query_database_with_time(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="foi.create_time",
                order_by="fod.comment DESC"
            )

        with allure.step("验证备注信息"):
            comment = db_data[0]["comment"]
            self.verify_data(
                actual_value=comment,
                expected_value="ceshikaicangbeizhu",
                op=CompareOp.EQ,
                use_isclose=False,
                message="预期：跟单取开仓备注",
                attachment_name="备注详情"
            )
            logger.info(f"备注验证通过: {comment}")

    @allure.story("场景3：策略开启订单备注，跟单无固定注释")
    @allure.title("策略平仓操作")
    def test_scenario3_close_orders(self, logged_session, var_manager):
        with allure.step("策略账号平仓"):
            cloudTrader_user_ids_2 = var_manager.get_variable("cloudTrader_user_ids_2")
            response = self.send_post_request(
                logged_session,
                '/bargain/masOrderClose',
                json_data={
                    "isCloseAll": 1,
                    "intervalTime": 0,
                    "traderList": [cloudTrader_user_ids_2]
                }
            )
            self.assert_json_value(response, "$.msg", "success", "策略平仓失败")

        with allure.step("跟单账号平仓"):
            cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
            response = self.send_post_request(
                logged_session,
                '/mascontrol/cloudTrader/orderClose',
                json_data={
                    "traderUserId": cloudTrader_traderList_4,
                    "isCloseAll": 1
                }
            )
            self.assert_response_status(response, 200, "跟单平仓失败")
            self.assert_json_value(response, "$.msg", "success", "跟单平仓响应错误")
