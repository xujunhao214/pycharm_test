import time
import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuan_814.VAR.VAR import *
from lingkuan_814.conftest import var_manager
from lingkuan_814.commons.api_base import APITestBase

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("跟单软件看板")
class TestDeleteFollowSlave(APITestBase):
    # ---------------------------
    # 云策略-云策略列表-批量删除云策略跟单账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云策略列表-批量删除云策略跟单账号")
    def test_delete_cloudBatchDelete(self, logged_session, var_manager):
        # 1. 获取账号总数和所有ID
        cloudTrader_user_count = var_manager.get_variable("cloudTrader_user_count", 0)
        if cloudTrader_user_count < 0:
            pytest.fail("未找到需要删除的账号数量，请检查前置步骤")
        # 2. 循环获取每个账号的ID并删除
        for i in range(5, cloudTrader_user_count + 1):
            with allure.step(f"删除第{i}云策略跟单账号"):
                slave_id = var_manager.get_variable(f"cloudTrader_traderList_{i}")
                if not slave_id:
                    pytest.fail(f"未找到需要删除的账号ID：cloudTrader_traderList_{i}")
                print(f"删除第{i}云策略跟单账号：cloudTrader_traderList_{i}")

                # 发送删除请求（接口支持单个ID删除，参数为列表形式）
                data = {
                    "traderList": [
                        slave_id
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
                    f"删除第{i}云策略跟单账号（ID: {slave_id}）失败"
                )

                # 3. 验证JSON返回内容
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    f"第{i}个账号删除响应msg字段应为success"
                )
                logger.info(f"[{DATETIME_NOW}] 第{i}个跟单账号（ID: {slave_id}）删除成功")

    # ---------------------------
    # 数据库校验-云策略列表-删除云策略跟单账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-云策略列表-批量删除云策略跟单账号")
    def test_dbdelete_cloudBatchDelete(self, var_manager, db_transaction):
        # 1. 获取账号总数和所有ID
        cloudTrader_user_count = var_manager.get_variable("cloudTrader_user_count", 0)
        if cloudTrader_user_count < 0:
            pytest.fail("未找到需要校验的账号数量，请检查前置步骤")
        # 2. 循环获取每个账号的ID并校验
        for i in range(5, cloudTrader_user_count + 1):
            with allure.step(f"校验第{i}云策略跟单账号"):
                cloudTrader_traderList = var_manager.get_variable(f"cloudTrader_traderList_{i}")
                if not cloudTrader_traderList:
                    pytest.fail(f"未找到需要删除的账号ID：cloudTrader_traderList_{i}")
                print(f"校验第{i}云策略跟单账号：cloudTrader_traderList_{i}")

                sql = f"SELECT * FROM follow_cloud_trader WHERE id = %s"
                params = (cloudTrader_traderList,)
                try:
                    self.wait_for_database_deletion(
                        db_transaction=db_transaction,
                        sql=sql,
                        params=params,
                        timeout=DELETE_WAIT_TIMEOUT,  # 设置5秒超时时间
                        poll_interval=POLL_INTERVAL  # 每2秒查询一次
                    )
                    allure.attach(f"云策略跟单账号 {cloudTrader_traderList} 已成功从数据库删除", "验证结果")
                except TimeoutError as e:
                    allure.attach(f"删除超时: {str(e)}", "验证结果")
                    pytest.fail(f"删除失败: {str(e)}")