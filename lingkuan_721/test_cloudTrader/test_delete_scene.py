import time

import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuan_721.VAR.VAR import *
from lingkuan_721.conftest import var_manager
from lingkuan_721.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("删除基本账号-批量删除云策略账号")
class TestDelete_cloudTrader(APITestBase):
    # ---------------------------
    # 云策略-云策略列表-批量删除云策略跟单账号
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("云策略-云策略列表-批量删除云策略跟单账号")
    def test_delete_cloudBatchDelete(self, api_session, var_manager, logged_session):
        # 1. 获取账号总数和所有ID
        user_count_cloudTrader = var_manager.get_variable("user_count_cloudTrader", 0)
        if user_count_cloudTrader < 0:
            pytest.fail("未找到需要删除的账号数量，请检查前置步骤")
        # 2. 循环获取每个账号的ID并删除
        for i in range(5, user_count_cloudTrader + 1):
            with allure.step(f"删除第{i}云策略跟单账号"):
                slave_id = var_manager.get_variable(f"traderList_cloudTrader_{i}")
                if not slave_id:
                    pytest.fail(f"未找到需要删除的账号ID：traderList_cloudTrader_{i}")
                print(f"删除第{i}云策略跟单账号：traderList_cloudTrader_{i}")

                # 发送删除请求（接口支持单个ID删除，参数为列表形式）
                data = {
                    "traderList": [
                        slave_id
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
        user_count_cloudTrader = var_manager.get_variable("user_count_cloudTrader", 0)
        if user_count_cloudTrader < 0:
            pytest.fail("未找到需要校验的账号数量，请检查前置步骤")
        # 2. 循环获取每个账号的ID并校验
        for i in range(5, user_count_cloudTrader + 1):
            with allure.step(f"校验第{i}云策略跟单账号"):
                traderList_cloudTrader = var_manager.get_variable(f"traderList_cloudTrader_{i}")
                if not traderList_cloudTrader:
                    pytest.fail(f"未找到需要删除的账号ID：traderList_cloudTrader_{i}")
                print(f"校验第{i}云策略跟单账号：traderList_cloudTrader_{i}")

                sql = f"SELECT * FROM follow_cloud_trader WHERE id = %s"
                params = (traderList_cloudTrader,)
                try:
                    self.wait_for_database_deletion(
                        db_transaction=db_transaction,
                        sql=sql,
                        params=params,
                        timeout=DELETE_WAIT_TIMEOUT,  # 设置5秒超时时间
                        poll_interval=POLL_INTERVAL  # 每2秒查询一次
                    )
                    allure.attach(f"云策略跟单账号 {traderList_cloudTrader} 已成功从数据库删除", "验证结果")
                except TimeoutError as e:
                    allure.attach(f"删除超时: {str(e)}", "验证结果")
                    pytest.fail(f"删除失败: {str(e)}")
