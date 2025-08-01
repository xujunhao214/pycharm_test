# lingkuan_801/tests/test_vps_ordersend.py
import time
import math

import allure
import logging
import pytest
from lingkuan_801.VAR.VAR import *
from lingkuan_801.conftest import var_manager
from lingkuan_801.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


# ---------------------------
# 修改模式、品种
# ---------------------------
@allure.feature("云策略策略下单-跟单修改模式、品种")
class TestVPSOrderSend_Scence(APITestBase):
    # ---------------------------
    # 云策略-云策略列表-删除云策略跟单账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云策略列表-删除云策略跟单账号")
    def test_delete_cloudBatchDelete(self, api_session, var_manager, logged_session):
        # 1. 发送删除删除云策略跟单账号请求
        traderList_cloudTrader_4 = var_manager.get_variable("traderList_cloudTrader_4")
        data = {
            "traderList": [
                traderList_cloudTrader_4
            ]
        }
        response = self.send_post_request(
            api_session,
            "/mascontrol/cloudTrader/cloudBatchDelete",
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "删除云策略跟单账号失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # ---------------------------
    # 数据库校验-云策略列表-删除云策略跟单账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-云策略列表-删除云策略跟单账号")
    def test_dbdelete_cloudBatchDelete(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否删除成功"):
            traderList_cloudTrader_4 = var_manager.get_variable("traderList_cloudTrader_4")
            logging.info(f"查询条件: table=follow_cloud_trader, id={traderList_cloudTrader_4}")

            sql = f"SELECT * FROM follow_cloud_trader WHERE id = %s"
            params = (traderList_cloudTrader_4,)
            try:
                self.wait_for_database_deletion(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )
                allure.attach(f"云策略跟单账号 {traderList_cloudTrader_4} 已成功从数据库删除", "验证结果")
            except TimeoutError as e:
                allure.attach(f"删除超时: {str(e)}", "验证结果")
                pytest.fail(f"删除失败: {str(e)}")
