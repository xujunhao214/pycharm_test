import time
import allure
import logging
import pytest
from lingkuan_1116.conftest import var_manager
from lingkuan_1116.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("跟随VPS策略账号订单备注的场景校验")
class TestVPSremark:
    @allure.story("场景1：VPS看板-策略有固定注释，跟单无固定注释")
    @allure.description("""
    ### 测试说明
    - 前置条件：有VPS策略和VPS跟单
      1. 修改云策略信息-关闭跟单备注
      2. 修改跟单账号-无固定注释
      3. 云策略账号复制下单
      4. 数据库校验-策略备注生效
      5. 策略账号平仓
    - 预期结果：跟单取策略备注
    """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    class TestVPSStrategyOrderRemark1(APITestBase):
        @pytest.mark.url("vps")
        @allure.title("修改策略账号信息")
        def test_scenario1_subcontrol_trader(self, class_random_str, var_manager, logged_session, encrypted_password):
            new_user = var_manager.get_variable("new_user")
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            platformId = var_manager.get_variable("platformId")
            json_data = {
                "id": vps_trader_id,
                "type": 0,
                "account": new_user["account"],
                "password": encrypted_password,
                "platform": new_user["platform"],
                "remark": "",
                "platformId": platformId,
                "templateId": 1,
                "followStatus": 1,
                "cfd": "",
                "forex": "",
                "followOrderRemark": 0,
                "fixedComment": f"{class_random_str}ceshiceluebeizhu",
                "commentType": None,
                "digits": 0
            }
            response = self.send_put_request(
                logged_session,
                '/subcontrol/trader',
                json_data=json_data,
            )
            self.assert_response_status(response, 200, "修改vps策略信息失败")
            self.assert_json_value(response, "$.msg", "success", "响应msg应为success")

        @pytest.mark.url("vps")
        @allure.title("修改跟单账号-无固定注释")
        def test_scenario1_follow_updateSlave(self, class_random_str, var_manager, logged_session, encrypted_password):
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
                "fixedComment": "",
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
            self.assert_response_status(response, 200, "修改跟单账号失败")
            self.assert_json_value(response, "$.msg", "success", "响应msg应为success")

        @pytest.mark.url("vps")
        @allure.title("策略开仓及备注校验")
        def test_scenario1_trader_orderSend_and_verify(self, class_random_str, var_manager, logged_session,
                                                       db_transaction):
            with allure.step("1. 开仓请求"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                vps_trader_id = var_manager.get_variable("vps_trader_id")
                data = {
                    "symbol": trader_ordersend["symbol"],
                    "placedType": 0,
                    "remark": f"{class_random_str}ceshikaicangbeizhu",
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
            with allure.step("2. json校验"):
                self.assert_response_status(response, 200, "策略开仓失败")
                self.assert_json_value(response, "$.msg", "success", "响应msg应为success")

            vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
            sql = """
                SELECT fod.account, fod.comment, foi.operation_type, foi.create_time
                FROM follow_order_detail fod
                INNER JOIN follow_order_instruct foi 
                    ON foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
                WHERE foi.operation_type = %s AND fod.account = %s AND fod.comment = %s 
            """
            params = ('0', vps_user_accounts_1, f"{class_random_str}ceshiceluebeizhu")
            db_data = self.query_database_with_time(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="foi.create_time"
            )
            with allure.step("3. 数据库校验"):
                comment = db_data[0]["comment"]
                self.verify_data(
                    actual_value=comment,
                    expected_value=f"{class_random_str}ceshiceluebeizhu",
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message=f"预期：跟单取策略备注",
                    attachment_name="备注详情"
                )
                logger.info(f"备注验证通过: {comment}")

        @pytest.mark.url("vps")
        @allure.title("平仓操作")
        def test_scenario1_close_orders(self, class_random_str, var_manager, logged_session):
            # 策略平仓
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            new_user = var_manager.get_variable("new_user")
            response = self.send_post_request(
                logged_session,
                '/subcontrol/trader/orderClose',
                json_data={"isCloseAll": 1, "intervalTime": 100, "traderId": vps_trader_id,
                           "account": new_user["account"]}
            )
            self.assert_response_status(response, 200, "策略平仓失败")

            # 跟单平仓
            # vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            # vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
            # response = self.send_post_request(
            #     logged_session,
            #     '/subcontrol/trader/orderClose',
            #     json_data={"isCloseAll": 1, "intervalTime": 100, "traderId": vps_addslave_id,
            #                "account": vps_user_accounts_1}
            # )
            # self.assert_response_status(response, 200, "跟单平仓失败")

    @allure.story("场景2：VPS看板-策略有固定注释，跟单有固定注释")
    @allure.description("""
    ### 测试说明
    - 前置条件：有VPS策略和VPS跟单
      1. 修改云策略信息-关闭跟单备注
      2. 修改跟单账号-有固定注释
      3. 云策略账号复制下单
      4. 数据库校验-策略备注生效
      5. 策略账号平仓
    - 预期结果：跟单取自身备注
    """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    class TestVPSStrategyOrderRemark2(APITestBase):
        @pytest.mark.url("vps")
        @allure.title("修改策略账号信息")
        def test_scenario2_subcontrol_trader(self, class_random_str, var_manager, logged_session, encrypted_password):
            new_user = var_manager.get_variable("new_user")
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            platformId = var_manager.get_variable("platformId")
            json_data = {
                "id": vps_trader_id,
                "type": 0,
                "account": new_user["account"],
                "password": encrypted_password,
                "platform": new_user["platform"],
                "remark": "",
                "platformId": platformId,
                "templateId": 1,
                "followStatus": 1,
                "cfd": "",
                "forex": "",
                "followOrderRemark": 0,
                "fixedComment": f"{class_random_str}ceshiceluebeizhu",
                "commentType": None,
                "digits": 0
            }
            response = self.send_put_request(logged_session, '/subcontrol/trader', json_data=json_data)
            self.assert_response_status(response, 200, "修改vps策略信息失败")
            self.assert_json_value(response, "$.msg", "success", "响应msg应为success")

        @pytest.mark.url("vps")
        @allure.title("修改跟单账号-有固定注释")
        def test_scenario2_follow_updateSlave(self, class_random_str, var_manager, logged_session, encrypted_password):
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
                "fixedComment": f"{class_random_str}ceshigendanbeizhu",
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
            self.assert_response_status(response, 200, "修改跟单账号失败")
            self.assert_json_value(response, "$.msg", "success", "响应msg应为success")

        @pytest.mark.url("vps")
        @allure.title("策略开仓及备注校验")
        def test_scenario2_trader_orderSend_and_verify(self, class_random_str, var_manager, logged_session,
                                                       db_transaction):
            with allure.step("1. 开仓请求"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                vps_trader_id = var_manager.get_variable("vps_trader_id")
                data = {
                    "symbol": trader_ordersend["symbol"],
                    "placedType": 0,
                    "remark": f"{class_random_str}ceshikaicangbeizhu",
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
            with allure.step("2. 状态校验"):
                self.assert_response_status(response, 200, "策略开仓失败")

            vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
            sql = """
                SELECT fod.account, fod.comment, foi.operation_type, foi.create_time
                FROM follow_order_detail fod
                INNER JOIN follow_order_instruct foi 
                    ON foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
                WHERE foi.operation_type = %s AND fod.account = %s AND fod.comment = %s 
            """
            params = ('0', vps_user_accounts_1, f"{class_random_str}ceshigendanbeizhu")
            db_data = self.query_database_with_time(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="foi.create_time"
            )

            with allure.step("3. 数据库校验"):
                comment = db_data[0]["comment"]
                self.verify_data(
                    actual_value=comment,
                    expected_value=f"{class_random_str}ceshigendanbeizhu",
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message="预期：跟单取自身备注",
                    attachment_name="备注详情"
                )
                logger.info(f"备注验证通过: {comment}")

        @pytest.mark.url("vps")
        @allure.title("平仓操作")
        def test_scenario2_close_orders(self, class_random_str, var_manager, logged_session):
            # 策略平仓
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            new_user = var_manager.get_variable("new_user")
            response = self.send_post_request(
                logged_session,
                '/subcontrol/trader/orderClose',
                json_data={"isCloseAll": 1, "intervalTime": 100, "traderId": vps_trader_id,
                           "account": new_user["account"]}
            )
            self.assert_response_status(response, 200, "策略平仓失败")

    @allure.story("场景3：VPS看板-策略开启订单备注，跟单无固定注释")
    @allure.description("""
    ### 测试说明
    - 前置条件：有VPS策略和VPS跟单
      1. 修改云策略信息-开启跟单备注
      2. 修改跟单账号-无固定注释
      3. 云策略账号复制下单
      4. 数据库校验-策略备注生效
      5. 策略账号平仓
    - 预期结果：跟单取开仓备注
    """)
    @pytest.mark.flaky(reruns=0, reruns_delay=0)
    @pytest.mark.usefixtures("class_random_str")
    class TestVPSStrategyOrderRemark3(APITestBase):
        @pytest.mark.url("vps")
        @allure.title("修改策略账号信息-开启订单备注")
        def test_scenario3_subcontrol_trader(self, class_random_str, var_manager, logged_session, encrypted_password):
            new_user = var_manager.get_variable("new_user")
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            platformId = var_manager.get_variable("platformId")
            json_data = {
                "id": vps_trader_id,
                "type": 0,
                "account": new_user["account"],
                "password": encrypted_password,
                "platform": new_user["platform"],
                "remark": "",
                "platformId": platformId,
                "templateId": 1,
                "followStatus": 1,
                "cfd": "",
                "forex": "",
                "followOrderRemark": 1,  # 开启订单备注
                "fixedComment": f"{class_random_str}ceshiceluebeizhu",
                "commentType": None,
                "digits": 0
            }
            response = self.send_put_request(logged_session, '/subcontrol/trader', json_data=json_data)
            self.assert_response_status(response, 200, "修改vps策略信息失败")
            self.assert_json_value(response, "$.msg", "success", "响应msg应为success")

        @pytest.mark.url("vps")
        @allure.title("修改跟单账号-无固定注释")
        def test_scenario3_follow_updateSlave(self, class_random_str, var_manager, logged_session, encrypted_password):
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
                "fixedComment": "",
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
            self.assert_response_status(response, 200, "修改跟单账号失败")
            self.assert_json_value(response, "$.msg", "success", "响应msg应为success")

        @pytest.mark.url("vps")
        @allure.title("策略开仓及备注校验")
        def test_scenario3_trader_orderSend_and_verify(self, class_random_str, var_manager, logged_session,
                                                       db_transaction):
            with allure.step("1. 开仓请求"):
                trader_ordersend = var_manager.get_variable("trader_ordersend")
                vps_trader_id = var_manager.get_variable("vps_trader_id")
                data = {
                    "symbol": trader_ordersend["symbol"],
                    "placedType": 0,
                    "remark": f"{class_random_str}ceshikaicangbeizhu",
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
            with allure.step("2. json校验"):
                self.assert_response_status(response, 200, "策略开仓失败")
                self.assert_json_value(response, "$.msg", "success", "响应msg应为success")

            vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
            sql = """
                SELECT fod.account, fod.comment, foi.operation_type, foi.create_time
                FROM follow_order_detail fod
                INNER JOIN follow_order_instruct foi 
                    ON foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
                WHERE foi.operation_type = %s AND fod.account = %s AND fod.comment = %s 
            """
            params = ('0', vps_user_accounts_1, f"{class_random_str}ceshikaicangbeizhu")
            db_data = self.query_database_with_time(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="foi.create_time"
            )
            if not db_data:
                pytest.fail("数据库查询结果为空")

            with allure.step("3. 数据库校验"):
                comment = db_data[0]["comment"]
                self.verify_data(
                    actual_value=comment,
                    expected_value=f"{class_random_str}ceshikaicangbeizhu",
                    op=CompareOp.EQ,
                    use_isclose=False,
                    message="预期：跟单取开仓备注",
                    attachment_name="备注详情"
                )
                logger.info(f"备注验证通过: {comment}")

        @pytest.mark.url("vps")
        @allure.title("平仓操作")
        def test_scenario3_close_orders(self, class_random_str, var_manager, logged_session):
            # 策略平仓
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            new_user = var_manager.get_variable("new_user")
            response = self.send_post_request(
                logged_session,
                '/subcontrol/trader/orderClose',
                json_data={"isCloseAll": 1, "intervalTime": 100, "traderId": vps_trader_id,
                           "account": new_user["account"]}
            )
            self.assert_response_status(response, 200, "策略平仓失败")
