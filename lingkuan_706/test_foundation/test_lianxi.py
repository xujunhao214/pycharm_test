import time

import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuan_706.VAR.VAR import *
from lingkuan_706.conftest import var_manager
from lingkuan_706.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("跟单软件看板")
class TestDeleteFollowSlave(APITestBase):
    # ---------------------------
    # 数据库校验：批量验证删除结果
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-VPS数据-批量删除跟单账号")
    def test_dbdelete_addsalvelist(self, var_manager, db_transaction):
        # 1. 获取账号总数和所有账号信息
        addslave_count = var_manager.get_variable("addslave_count", 0)
        if addslave_count <= 0:
            pytest.fail("未找到需要验证的账号数量，请检查前置步骤")

        db_addslave_query = var_manager.get_variable("db_addslave_query")
        table = db_addslave_query["table"]

        # 2. 循环验证每个账号的删除状态
        for i in range(1, addslave_count + 1):
            with allure.step(f"验证第{i}个账号是否删除成功"):
                # 获取单个账号（与删除的ID对应）
                account = var_manager.get_variable(f"user_accounts_{i}")
                if not account:
                    pytest.fail(f"未找到需要验证的账号：user_accounts_{i}")

                # 查询数据库（检查删除标记或记录是否存在）
                sql = f"SELECT * FROM {table} WHERE account = %s"
                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.query_database(db_transaction, sql, (account,))
                # 验证逻辑：根据实际业务判断（逻辑删除/物理删除）
                assert not db_data, "删除失败,还有查询结果"

                # 验证订阅表是否同步删除
                table_subscribe = db_addslave_query["table_subscribe"]
                sql_sub = f"SELECT * FROM {table_subscribe} WHERE slave_account = %s"
                db_data_sub = self.query_database(db_transaction, sql_sub, (account,))
                assert not db_data_sub, (
                    f"第{i}个账号（{account}）的订阅表记录未删除，"
                    f"残留数据：{db_data_sub}"
                )
