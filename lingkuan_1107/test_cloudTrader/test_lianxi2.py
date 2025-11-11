import time
import math
import allure
import logging
import pytest
from lingkuan_1107.VAR.VAR import *
from lingkuan_1107.conftest import var_manager
from lingkuan_1107.commons.api_base import APITestBase
from lingkuan_1107.commons.redis_utils import *

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("云策略策略下单-跟单修改模式、品种")
class TestVPSOrderSend_Scence(APITestBase):
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云策略列表-删除MT5云跟单账号")
    def test_delete_MT5cloudBatch(self, logged_session, var_manager):
        # 发送删除请求
        cloudTrader_MT5traderID = var_manager.get_variable("cloudTrader_MT5traderID")
        data = {
            "traderList": [
                cloudTrader_MT5traderID
            ]
        }
        response = self.send_post_request(
            logged_session,
            "/mascontrol/cloudTrader/cloudBatchDelete",
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            f"删除云跟单账号失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            f"删除响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-云策略列表-批量删除云跟单账号")
    def test_dbdelete_MT5cloudBatch(self, var_manager, db_transaction):
        cloudTrader_MT5traderID = var_manager.get_variable("cloudTrader_MT5traderID")
        sql = f"SELECT * FROM follow_cloud_trader WHERE id = %s"
        params = (cloudTrader_MT5traderID,)
        try:
            self.wait_for_database_deletion(
                db_transaction=db_transaction,
                sql=sql,
                params=params
            )
            allure.attach(f"云跟单账号 {cloudTrader_MT5traderID} 已成功从数据库删除", "验证结果")
        except TimeoutError as e:
            allure.attach(f"删除超时: {str(e)}", "验证结果")
            pytest.fail(f"删除失败: {str(e)}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-删除MT5跟单账号")
    def test_delete_addMT5Slave(self, logged_session, var_manager):
        # 发送删除请求
        MT5vps_addslave_id = var_manager.get_variable("MT5vps_addslave_id")
        data = [MT5vps_addslave_id]
        response = self.send_delete_request(
            logged_session,
            "/subcontrol/trader",
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            f"删除跟单账号失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            f"删除响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-VPS数据-删除跟单账号")
    def test_dbdelete_addMT5Slave(self, var_manager, db_transaction):
        addCloud_MT5Slave = var_manager.get_variable("addCloud_MT5Slave")
        sql = f"SELECT * FROM follow_trader WHERE account = %s"
        params = (addCloud_MT5Slave["account"],)
        try:
            self.wait_for_database_deletion(
                db_transaction=db_transaction,
                sql=sql,
                params=params
            )
            allure.attach(f"云跟单账号{addCloud_MT5Slave['account']} 已成功从数据库删除", "验证结果")
        except TimeoutError as e:
            allure.attach(f"删除超时: {str(e)}", "验证结果")
            pytest.fail(f"删除失败: {str(e)}")

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-账号列表-删除MT5账号")
    def test_delete_MT5user(self, logged_session, var_manager):
        # 发送删除请求
        cloudTrader_MT5userID = var_manager.get_variable("cloudTrader_MT5userID")
        response = self.send_delete_request(
            logged_session,
            "/mascontrol/user",
            json_data=[cloudTrader_MT5userID]
        )

        # 3. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            f"账号删除失败"
        )

        # 4. 验证响应内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            f"账号删除响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-账号列表-删除MT5账号")
    def test_dbdelete_MT5user(self, var_manager, db_transaction):
        addCloud_MT5Slave = var_manager.get_variable("addCloud_MT5Slave")
        sql = f"SELECT * FROM follow_trader_user WHERE account = %s"
        params = (addCloud_MT5Slave["account"],)

        try:
            self.wait_for_database_deletion(
                db_transaction=db_transaction,
                sql=sql,
                params=params
            )
            allure.attach(f"账号 {addCloud_MT5Slave['account']} 已成功从数据库删除", "验证结果")
        except TimeoutError as e:
            allure.attach(f"删除超时: {str(e)}", "验证结果")
            pytest.fail(f"删除失败: {str(e)}")
