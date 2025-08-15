import time
import math
import allure
import logging
import pytest
from lingkuan_817.VAR.VAR import *
from lingkuan_817.conftest import var_manager
from lingkuan_817.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"


@allure.feature("VPS策略下单-跟随策略账号订单备注3种情况")
@allure.description("""
### 用例说明
- 前置条件：有vps策略和vps跟单，vps策略修改跟单备注开关
- 操作步骤：
  1. 修改vps策略备注
  2. 进行开仓
  3. 校验跟单备注信息
  4. 进行平仓
- 预期结果：跟单备注信息正确
""")
class TestVPSOrderSend_closeaddremark(APITestBase):
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-修改策略账号信息")
    def test_subcontrol_trader(self, var_manager, logged_session, encrypted_password):
        # 1. 发送修改vps策略的请求(followOrderRemark为0，关闭跟单备注，跟单才跟策略备注)
        with allure.step("发送修改vps策略的请求"):
            new_user = var_manager.get_variable("new_user")
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            json_data = {
                "id": vps_trader_id,
                "type": 0,
                "account": new_user["account"],
                "password": encrypted_password,
                "platform": new_user["platform"],
                "remark": "测试数据",
                "platformId": 346,
                "templateId": 1,
                "followStatus": 1,
                "cfd": "",
                "forex": "",
                "followOrderRemark": 1,
                "fixedComment": "ceshiceluebeizhu",
                "commentType": None,
                "digits": 0
            }
            response = self.send_put_request(
                logged_session,
                '/subcontrol/trader',
                json_data=json_data,
            )

        with allure.step("2. 验证响应状态码和内容"):
            # 2. 验证响应状态码和内容
            self.assert_response_status(
                response,
                200,
                "发送修改vps策略的请求失败"
            )
            self.assert_json_value(
                response,
                "$.msg",
                "success",
                "响应msg字段应为success"
            )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-修改跟单账号")
    def test_follow_updateSlave(self, var_manager, logged_session, encrypted_password):
        with allure.step("1. 发送修改跟单账号请求"):
            # 1. 发送修改跟单账号请求(跟单也有备注信息，走自己的备注)
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

    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-策略开仓")
    def test_trader_orderSend(self, var_manager, logged_session):
        # 1. 发送策略开仓请求
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

        # 2. 验证响应状态码和内容
        self.assert_response_status(
            response,
            200,
            "策略开仓失败"
        )
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    @allure.title("数据库校验-策略开仓-主指令及订单详情数据检查")
    def test_dbquery_orderSend(self, var_manager, db_transaction):
        with allure.step("1. 获取订单详情界面跟单账号数据"):
            vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
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
                vps_user_accounts_1,
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

    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-策略平仓")
    def test_trader_orderclose(self, var_manager, logged_session):
        # 1. 发送全平订单平仓请求
        vps_trader_id = var_manager.get_variable("vps_trader_id")
        new_user = var_manager.get_variable("new_user")
        data = {
            "isCloseAll": 1,
            "intervalTime": 100,
            "traderId": vps_trader_id,
            "account": new_user["account"]
        }
        response = self.send_post_request(
            logged_session,
            '/subcontrol/trader/orderClose',
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

    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-跟单平仓")
    def test_addtrader_orderclose(self, var_manager, logged_session):
        # 1. 发送全平订单平仓请求
        vps_addslave_id = var_manager.get_variable("vps_addslave_id")
        vps_user_accounts_1 = var_manager.get_variable("vps_user_accounts_1")
        data = {
            "isCloseAll": 1,
            "intervalTime": 100,
            "traderId": vps_addslave_id,
            "account": vps_user_accounts_1
        }
        response = self.send_post_request(
            logged_session,
            '/subcontrol/trader/orderClose',
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
