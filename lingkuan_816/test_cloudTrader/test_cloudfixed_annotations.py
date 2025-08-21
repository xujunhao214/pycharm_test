import time
import math
import allure
import logging
import pytest
from lingkuan_816.VAR.VAR import *
from lingkuan_816.conftest import var_manager
from lingkuan_816.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"


@allure.feature("云策略交易下单-跟随策略账号订单备注-第一种情况")
@allure.description("""
### 用例说明
- 前置条件：有云策略和云跟单
- 操作步骤：
  1. 修改云策略备注，有固定注释，关闭策略跟单备注
  2. 修改跟单账号备注，没有固定注释
  3. 进行开仓，有备注
  4. 校验跟单备注信息
  5. 进行平仓
- 预期结果：跟单备注信息正确，是策略备注信息
""")
class TestVPSOrderSend_closeaddremark(APITestBase):
    @allure.title("云策略-云策略列表-修改策略账号信息")
    def test_mascontrol_cloudTrader(self, var_manager, logged_session, encrypted_password):
        # 1. 发送修改云策略的请求(followOrderRemark为0，关闭跟单备注，跟单才跟策略备注)
        with allure.step("发送修改云策略的请求"):
            new_user = var_manager.get_variable("new_user")
            cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")
            cloudMaster_id = var_manager.get_variable("cloudMaster_id")
            cloudTrader_vps_ids_1 = var_manager.get_variable("cloudTrader_vps_ids_1")
            cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
            json_data = {
                "id": cloudTrader_traderList_2,
                "cloudId": cloudMaster_id,
                "sourceType": 0,
                "remark": "测试数据",
                "runningStatus": 0,
                "followOrderRemark": 0,
                "traderId": cloudTrader_vps_ids_1,
                "managerIp": None,
                "managerAccount": None,
                "account": cloudTrader_user_accounts_2,
                "platform": new_user["platform"],
                "templateId": None,
                "fixedComment": "ceshiceluebeizhu",
                "commentType": None,
                "digits": 0
            }
            response = self.send_put_request(
                logged_session,
                '/mascontrol/cloudTrader',
                json_data=json_data,
            )

        with allure.step("2. 验证响应状态码和内容"):
            # 2. 验证响应状态码和内容
            self.assert_response_status(
                response,
                200,
                "发送修改云策略的请求失败"
            )
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云策略列表-修改跟单账号")
    def test_cloudTrader_cloudBatchUpdate(self, var_manager, logged_session, encrypted_password):
        with allure.step("1. 发送修改跟单账号请求"):
            # 1. 发送修改跟单账号请求(跟单也有备注信息，走自己的备注)
            cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
            cloudMaster_id = var_manager.get_variable("cloudMaster_id")
            cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")
            cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
            data = [
                {
                    "traderList": [
                        cloudTrader_traderList_4
                    ],
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
                }
            ]
            response = self.send_post_request(
                logged_session,
                '/mascontrol/cloudTrader/cloudBatchUpdate',
                json_data=data
            )
        with allure.step("2. 验证响应状态码和JSON返回内容"):
            # 2. 验证响应状态码
            self.assert_response_status(
                response,
                200,
                "修改vps跟单信息失败"
            )

            # 3. 验证JSON返回内容
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

    @allure.title("账号管理-交易下单-云策略账号复制下单")
    def test_bargain_masOrderSend(self, logged_session, var_manager):
        # 1. 发送云策略复制下单请求
        global cloudTrader_user_ids_2
        cloudTrader_user_ids_2 = var_manager.get_variable("cloudTrader_user_ids_2")
        data = {
            "traderList": [
                cloudTrader_user_ids_2
            ],
            "type": 0,
            "tradeType": 1,
            "intervalTime": 100,
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
            json_data=data
        )

        # 2. 判断云策略复制下单是否成功
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    @allure.title("数据库校验-交易下单-指令及订单详情数据检查")
    def test_dbquery_masOrderSend(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
            sql = f"""
                SELECT 
                    fod.account,
                    fod.comment,
                    foi.operation_type,
                    foi.create_time
                FROM 
                    follow_order_detail fod
                INNER JOIN 
                    follow_order_instruct foi 
                ON 
                    foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
                WHERE foi.operation_type = %s
                    AND fod.account = %s
                    """
            params = (
                '0',
                cloudTrader_user_accounts_4,
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="foi.create_time"
            )
        with allure.step("2. 数据校验"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            comment = db_data[0]["comment"]
            assert comment == "ceshiceluebeizhu", f"跟单账号的订单备注信息应是：ceshiceluebeizhu，实际是：{comment}"
            logging.info(f"跟单账号的订单备注信息应是：ceshiceluebeizhu，实际是：{comment}")

    @allure.title("账号管理-交易下单-平仓")
    def test_bargain_masOrderClose(self, logged_session, var_manager):
        cloudTrader_user_ids_2 = var_manager.get_variable("cloudTrader_user_ids_2")
        # 1. 发送平仓请求
        data = {
            "isCloseAll": 1,
            "intervalTime": 100,
            "traderList": [
                cloudTrader_user_ids_2
            ]
        }
        response = self.send_post_request(
            logged_session,
            '/bargain/masOrderClose',
            json_data=data
        )

        # 2. 判断是否平仓成功
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云跟单-跟单平仓")
    def test_addtrader_masOrderClose(self, var_manager, logged_session):
        # 1. 发送全平订单平仓请求
        cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
        data = {
            "traderUserId": cloudTrader_traderList_4,
            "isCloseAll": 1
        }
        response = self.send_post_request(
            logged_session,
            '/mascontrol/cloudTrader/orderClose',
            json_data=data,
        )

        # 2. 验证响应
        self.assert_response_status(
            response,
            200,
            "平仓失败"
        )
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )


@allure.feature("云策略交易下单-跟随策略账号订单备注-第二种情况")
@allure.description("""
### 用例说明
- 前置条件：有云策略和云跟单
- 操作步骤：
  1. 修改云策略备注，有固定注释，关闭策略跟单备注
  2. 修改跟单账号备注，有固定注释
  3. 进行开仓，有备注
  4. 校验跟单备注信息
  5. 进行平仓
- 预期结果：跟单备注信息正确，是跟单备注信息
""")
class TestVPSOrderSend_closeaddremark2(APITestBase):
    @allure.title("云策略-云策略列表-修改策略账号信息")
    def test_mascontrol_cloudTrader(self, var_manager, logged_session, encrypted_password):
        # 1. 发送修改云策略的请求(followOrderRemark为0，关闭跟单备注，跟单才跟策略备注)
        with allure.step("发送修改云策略的请求"):
            new_user = var_manager.get_variable("new_user")
            cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")
            cloudMaster_id = var_manager.get_variable("cloudMaster_id")
            cloudTrader_vps_ids_1 = var_manager.get_variable("cloudTrader_vps_ids_1")
            cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
            json_data = {
                "id": cloudTrader_traderList_2,
                "cloudId": cloudMaster_id,
                "sourceType": 0,
                "remark": "测试数据",
                "runningStatus": 0,
                "followOrderRemark": 0,
                "traderId": cloudTrader_vps_ids_1,
                "managerIp": None,
                "managerAccount": None,
                "account": cloudTrader_user_accounts_2,
                "platform": new_user["platform"],
                "templateId": None,
                "fixedComment": "ceshiceluebeizhu",
                "commentType": None,
                "digits": 0
            }
            response = self.send_put_request(
                logged_session,
                '/mascontrol/cloudTrader',
                json_data=json_data,
            )

        with allure.step("2. 验证响应状态码和内容"):
            # 2. 验证响应状态码和内容
            self.assert_response_status(
                response,
                200,
                "发送修改云策略的请求失败"
            )
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云策略列表-修改跟单账号")
    def test_cloudTrader_cloudBatchUpdate(self, var_manager, logged_session, encrypted_password):
        with allure.step("1. 发送修改跟单账号请求"):
            # 1. 发送修改跟单账号请求(跟单也有备注信息，走自己的备注)
            cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
            cloudMaster_id = var_manager.get_variable("cloudMaster_id")
            cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")
            cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
            data = [
                {
                    "traderList": [
                        cloudTrader_traderList_4
                    ],
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
                    "fixedComment": "ceshigendanbeizhu",
                    "commentType": None,
                    "digits": 0,
                    "followTraderIds": [],
                    "sort": 100,
                    "remark": "",
                    "cfd": None,
                    "forex": None
                }
            ]
            response = self.send_post_request(
                logged_session,
                '/mascontrol/cloudTrader/cloudBatchUpdate',
                json_data=data
            )
        with allure.step("2. 验证响应状态码和JSON返回内容"):
            # 2. 验证响应状态码
            self.assert_response_status(
                response,
                200,
                "修改vps跟单信息失败"
            )

            # 3. 验证JSON返回内容
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

    @allure.title("账号管理-交易下单-云策略账号复制下单")
    def test_bargain_masOrderSend(self, logged_session, var_manager):
        # 1. 发送云策略复制下单请求
        global cloudTrader_user_ids_2
        cloudTrader_user_ids_2 = var_manager.get_variable("cloudTrader_user_ids_2")
        data = {
            "traderList": [
                cloudTrader_user_ids_2
            ],
            "type": 0,
            "tradeType": 1,
            "intervalTime": 100,
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
            json_data=data
        )

        # 2. 判断云策略复制下单是否成功
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    @allure.title("数据库校验-交易下单-指令及订单详情数据检查")
    def test_dbquery_masOrderSend(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
            sql = f"""
                SELECT 
                    fod.account,
                    fod.comment,
                    foi.operation_type,
                    foi.create_time
                FROM 
                    follow_order_detail fod
                INNER JOIN 
                    follow_order_instruct foi 
                ON 
                    foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
                WHERE foi.operation_type = %s
                    AND fod.account = %s
                    """
            params = (
                '0',
                cloudTrader_user_accounts_4,
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="foi.create_time"
            )
        with allure.step("2. 数据校验"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            comment = db_data[0]["comment"]
            assert comment == "ceshigendanbeizhu", f"跟单账号的订单备注信息应是：ceshigendanbeizhu，实际是：{comment}"
            logging.info(f"跟单账号的订单备注信息应是：ceshigendanbeizhu，实际是：{comment}")

    @allure.title("账号管理-交易下单-平仓")
    def test_bargain_masOrderClose(self, logged_session, var_manager):
        cloudTrader_user_ids_2 = var_manager.get_variable("cloudTrader_user_ids_2")
        # 1. 发送平仓请求
        data = {
            "isCloseAll": 1,
            "intervalTime": 100,
            "traderList": [
                cloudTrader_user_ids_2
            ]
        }
        response = self.send_post_request(
            logged_session,
            '/bargain/masOrderClose',
            json_data=data
        )

        # 2. 判断是否平仓成功
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云跟单-跟单平仓")
    def test_addtrader_masOrderClose(self, var_manager, logged_session):
        # 1. 发送全平订单平仓请求
        cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
        data = {
            "traderUserId": cloudTrader_traderList_4,
            "isCloseAll": 1
        }
        response = self.send_post_request(
            logged_session,
            '/mascontrol/cloudTrader/orderClose',
            json_data=data,
        )

        # 2. 验证响应
        self.assert_response_status(
            response,
            200,
            "平仓失败"
        )
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )


@allure.feature("云策略交易下单-跟随策略账号订单备注-第三种情况")
@allure.description("""
### 用例说明
- 前置条件：有云策略和云跟单
- 操作步骤：
  1. 修改云策略备注，有固定注释，开启策略跟单备注
  2. 修改跟单账号备注，没有固定注释
  3. 进行开仓，有备注
  4. 校验跟单备注信息
  5. 进行平仓
- 预期结果：跟单备注信息正确，开仓备注信息
""")
class TestVPSOrderSend_closeaddremark3(APITestBase):
    @allure.title("云策略-云策略列表-修改策略账号信息")
    def test_mascontrol_cloudTrader(self, var_manager, logged_session, encrypted_password):
        with allure.step("发送修改云策略的请求"):
            new_user = var_manager.get_variable("new_user")
            cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")
            cloudMaster_id = var_manager.get_variable("cloudMaster_id")
            cloudTrader_vps_ids_1 = var_manager.get_variable("cloudTrader_vps_ids_1")
            cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
            json_data = {
                "id": cloudTrader_traderList_2,
                "cloudId": cloudMaster_id,
                "sourceType": 0,
                "remark": "测试数据",
                "runningStatus": 0,
                "followOrderRemark": 1,
                "traderId": cloudTrader_vps_ids_1,
                "managerIp": None,
                "managerAccount": None,
                "account": cloudTrader_user_accounts_2,
                "platform": new_user["platform"],
                "templateId": None,
                "fixedComment": "ceshiceluebeizhu",
                "commentType": None,
                "digits": 0
            }
            response = self.send_put_request(
                logged_session,
                '/mascontrol/cloudTrader',
                json_data=json_data,
            )

        with allure.step("2. 验证响应状态码和内容"):
            # 2. 验证响应状态码和内容
            self.assert_response_status(
                response,
                200,
                "发送修改云策略的请求失败"
            )
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云策略列表-修改跟单账号")
    def test_cloudTrader_cloudBatchUpdate(self, var_manager, logged_session, encrypted_password):
        with allure.step("1. 发送修改跟单账号请求"):
            # 1. 发送修改跟单账号请求(跟单也有备注信息，走自己的备注)
            cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
            cloudMaster_id = var_manager.get_variable("cloudMaster_id")
            cloudTrader_traderList_2 = var_manager.get_variable("cloudTrader_traderList_2")
            cloudTrader_user_accounts_2 = var_manager.get_variable("cloudTrader_user_accounts_2")
            data = [
                {
                    "traderList": [
                        cloudTrader_traderList_4
                    ],
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
                }
            ]
            response = self.send_post_request(
                logged_session,
                '/mascontrol/cloudTrader/cloudBatchUpdate',
                json_data=data
            )
        with allure.step("2. 验证响应状态码和JSON返回内容"):
            # 2. 验证响应状态码
            self.assert_response_status(
                response,
                200,
                "修改vps跟单信息失败"
            )

            # 3. 验证JSON返回内容
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

    @allure.title("账号管理-交易下单-云策略账号复制下单")
    def test_bargain_masOrderSend(self, logged_session, var_manager):
        # 1. 发送云策略复制下单请求
        global cloudTrader_user_ids_2
        cloudTrader_user_ids_2 = var_manager.get_variable("cloudTrader_user_ids_2")
        data = {
            "traderList": [
                cloudTrader_user_ids_2
            ],
            "type": 0,
            "tradeType": 1,
            "intervalTime": 100,
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
            json_data=data
        )

        # 2. 判断云策略复制下单是否成功
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    @allure.title("数据库校验-交易下单-指令及订单详情数据检查")
    def test_dbquery_masOrderSend(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            cloudTrader_user_accounts_4 = var_manager.get_variable("cloudTrader_user_accounts_4")
            sql = f"""
                SELECT 
                    fod.account,
                    fod.comment,
                    foi.operation_type,
                    foi.create_time
                FROM 
                    follow_order_detail fod
                INNER JOIN 
                    follow_order_instruct foi 
                ON 
                    foi.order_no = fod.send_no COLLATE utf8mb4_0900_ai_ci
                WHERE foi.operation_type = %s
                    AND fod.account = %s
                    """
            params = (
                '0',
                cloudTrader_user_accounts_4,
            )

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                time_field="foi.create_time"
            )
        with allure.step("2. 数据校验"):
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")

            comment = db_data[0]["comment"]
            assert comment == "ceshikaicangbeizhu", f"跟单账号的订单备注信息应是：ceshikaicangbeizhu，实际是：{comment}"
            logging.info(f"跟单账号的订单备注信息应是：ceshikaicangbeizhu，实际是：{comment}")

    @allure.title("账号管理-交易下单-平仓")
    def test_bargain_masOrderClose(self, logged_session, var_manager):
        cloudTrader_user_ids_2 = var_manager.get_variable("cloudTrader_user_ids_2")
        # 1. 发送平仓请求
        data = {
            "isCloseAll": 1,
            "intervalTime": 100,
            "traderList": [
                cloudTrader_user_ids_2
            ]
        }
        response = self.send_post_request(
            logged_session,
            '/bargain/masOrderClose',
            json_data=data
        )

        # 2. 判断是否平仓成功
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云跟单-跟单平仓")
    def test_addtrader_masOrderClose(self, var_manager, logged_session):
        # 1. 发送全平订单平仓请求
        cloudTrader_traderList_4 = var_manager.get_variable("cloudTrader_traderList_4")
        data = {
            "traderUserId": cloudTrader_traderList_4,
            "isCloseAll": 1
        }
        response = self.send_post_request(
            logged_session,
            '/mascontrol/cloudTrader/orderClose',
            json_data=data,
        )

        # 2. 验证响应
        self.assert_response_status(
            response,
            200,
            "平仓失败"
        )
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )
