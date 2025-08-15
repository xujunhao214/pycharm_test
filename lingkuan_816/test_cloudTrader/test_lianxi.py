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
class TestVPSOrderSend_closeaddremark(APITestBase):
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云策略列表-新增manager策略账号")
    def test_manager_cloudTrader(self, var_manager, logged_session):
        # 1. 发送新增策略账号请求
        cloudMaster_id = var_manager.get_variable("cloudMaster_id")
        cloudTrader_user_accounts_3 = var_manager.get_variable("cloudTrader_user_accounts_3")
        new_user = var_manager.get_variable("new_user")
        manager = var_manager.get_variable("manager")
        data = {
            "cloudId": cloudMaster_id,
            "sourceType": 1,
            "remark": "新增manager账号",
            "runningStatus": 0,
            "followOrderRemark": 1,
            "traderId": "",
            "managerIp": manager["managerIp"],
            "managerAccount": manager["managerAccount"],
            "managerPassword": manager["managerPassword"],
            "account": cloudTrader_user_accounts_3,
            "platform": new_user["platform"],
            "templateId": 1,
            "fixedComment": new_user["fixedComment"],
            "commentType": "",
            "digits": ""
        }
        response = self.send_post_request(
            logged_session,
            '/mascontrol/cloudTrader',
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "新增manager策略账号失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-云策略列表-新增manager账号")
    def test_dbmanager_trader(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            cloudTrader_user_accounts_3 = var_manager.get_variable("cloudTrader_user_accounts_3")

            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_cloud_trader WHERE account = %s",
                (cloudTrader_user_accounts_3,)
            )

        with allure.step("2. 验证数据库数据"):
            manager = var_manager.get_variable("manager")
            managerdb = db_data[0]['manager_ip']
            self.assert_values_equal(
                manager['managerIp'],
                managerdb,
                f"新增manager账号服务器是：{managerdb} 应该是：{manager['managerIp']}"
            )
            logging.info(f"新增manager账号服务器是：{managerdb} 应该是：{manager['managerIp']}")

        with allure.step("3. 提取数据"):
            cloudTrader_traderList_3 = db_data[0]['id']
            var_manager.set_runtime_variable("cloudTrader_traderList_3", cloudTrader_traderList_3)
            logging.info(f"新增manager账号id是：{cloudTrader_traderList_3}")
