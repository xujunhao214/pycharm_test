import time
import math
import allure
import logging
import pytest
from lingkuan_1024.VAR.VAR import *
from lingkuan_1024.conftest import var_manager
from lingkuan_1024.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("VPS策略下单-开仓的场景校验")
class TestVPSOrdersend(APITestBase):
    # @pytest.mark.skip(reason=SKIP_REASON)
    @pytest.mark.url("vps")
    @allure.title("跟单软件看板-VPS数据-批量删除跟单账号")
    def test_delete_addsalvelist(self, var_manager, logged_session):
        # 1. 获取账号总数和所有ID
        vps_addslave_count = var_manager.get_variable("vps_addslave_count", 0)
        if vps_addslave_count <= 0:
            pytest.fail("未找到需要删除的账号数量，请检查前置步骤")

        # 2. 循环获取每个账号的ID并删除
        for i in range(1, vps_addslave_count + 1):
            with allure.step(f"删除第{i}个跟单账号"):
                # 获取单个账号ID（vps_addslave_ids_1, vps_addslave_ids_2, ...）
                slave_id = var_manager.get_variable(f"vps_addslave_ids_{i}")
                if not slave_id:
                    pytest.fail(f"未找到需要删除的账号ID：vps_addslave_ids_{i}")
                print(f"删除第{i}个跟单账号:vps_addslave_ids_{i}")

                # 发送删除请求
                response = self.send_delete_request(
                    logged_session,
                    '/subcontrol/trader',
                    json_data=[slave_id]  # 保持与接口要求一致的列表格式
                )

                # 验证响应
                self.assert_response_status(
                    response,
                    200,
                    f"删除第{i}个跟单账号（ID: {slave_id}）失败"
                )
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    f"第{i}个账号删除响应msg字段应为success"
                )
                logger.info(f"[{DATETIME_NOW}] 第{i}个跟单账号（ID: {slave_id}）删除成功")

    @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-VPS数据-批量删除跟单账号")
    def test_dbdelete_addsalvelist(self, var_manager, db_transaction):
        # 1. 获取账号总数和所有账号信息
        vps_addslave_count = var_manager.get_variable("vps_addslave_count", 0)
        if vps_addslave_count <= 0:
            pytest.fail("未找到需要验证的账号数量，请检查前置步骤")

        # 2. 循环验证每个账号的删除状态
        for i in range(1, vps_addslave_count + 1):
            with allure.step(f"验证第{i}个账号是否删除成功"):
                # 获取单个账号（与删除的ID对应）
                account = var_manager.get_variable(f"vps_user_accounts_{i}")
                if not account:
                    pytest.fail(f"未找到需要验证的账号：vps_user_accounts_{i}")

                # 查询数据库（检查删除标记或记录是否存在）
                sql = f"SELECT * FROM follow_trader WHERE account = %s"
                # 调用轮询等待方法（带时间范围过滤）
                try:
                    self.wait_for_database_deletion(
                        db_transaction=db_transaction,
                        sql=sql,
                        params=(account,)
                    )
                    allure.attach(f"跟单账号 {account} 已成功从数据库删除", "验证结果")
                except TimeoutError as e:
                    allure.attach(f"删除超时: {str(e)}", "验证结果")
                    pytest.fail(f"删除失败: {str(e)}")

                # 验证订阅表是否同步删除
                sql_sub = f"SELECT * FROM follow_trader_subscribe WHERE slave_account = %s"
                db_data_sub = self.query_database(db_transaction, sql_sub, (account,))
                assert not db_data_sub, (
                    f"第{i}个账号（{account}）的订阅表记录未删除，"
                    f"残留数据：{db_data_sub}"
                )
