import time

import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuan_801.VAR.VAR import *
from lingkuan_801.conftest import var_manager
from lingkuan_801.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("跟单软件看板")
class TestDeleteFollowSlave(APITestBase):
    @allure.title("数据库校验-VPS数据-批量新增跟单账号")
    def test_dbimport_addSlave(self, var_manager, db_transaction):
        # 1. 校验总用户数（需至少7个，才能取后6个）
        user_count = var_manager.get_variable("user_count", 0)
        if user_count < 7:
            pytest.fail(f"用户总数需至少为7，当前为{user_count}，无法提取后6个数据进行校验")

        # 2. 提取后6个账号（对应user_accounts_2到user_accounts_7）
        all_accounts = []
        for i in range(2, 8):  # 直接指定取第2到第7个账号（共6个）
            account = var_manager.get_variable(f"user_accounts_{i}")
            if not account:
                pytest.fail(f"未找到第{i}个账号（变量：user_accounts_{i}）")
            all_accounts.append(account)
        print(f"将校验的后6个账号：{all_accounts}")

        # 3. 初始化ID列表和计数器
        all_ids = []
        addslave_count = 0

        # 4. 逐个校验后6个账号的数据库记录
        for idx, account in enumerate(all_accounts, 1):  # idx从1开始（1-6，对应6个账号）
            with allure.step(f"验证第{idx}个账号（{account}）的数据库记录"):
                sql = f"SELECT * FROM follow_trader WHERE account = %s"
                params = (account,)

                # 调用轮询等待方法（带时间范围过滤）
                db_data = self.wait_for_database_record(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )

                if not db_data:
                    pytest.fail(f"账号 {account} 在主表中未找到记录，请检查新增是否成功")

                # 提取当前账号的ID并保存到变量管理器
                vps_addslave_id = db_data[0]["id"]
                all_ids.append(vps_addslave_id)
                var_manager.set_runtime_variable(f"vps_addslave_ids_{idx}", vps_addslave_id)
                print(f"账号 {account} 的ID为：{vps_addslave_id}，已保存到变量 vps_addslave_ids_{idx}")

                # 校验账号状态和净值（核心业务规则）
                def verify_core_fields():
                    # 校验状态（0为正常）
                    status = db_data[0]["status"]
                    if status != 0:
                        pytest.fail(f"账号 {account} 状态异常：预期status=0（正常），实际={status}")
                    # 校验净值（非零）
                    euqit = db_data[0]["euqit"]
                    if euqit == 0:
                        pytest.fail(f"账号 {account} 净值异常：预期euqit≠0，实际={euqit}")

                # 执行核心校验并记录结果
                try:
                    verify_core_fields()
                    allure.attach(f"账号 {account} 主表字段校验通过", "校验结果", allure.attachment_type.TEXT)
                except AssertionError as e:
                    allure.attach(str(e), f"账号 {account} 主表字段校验失败", allure.attachment_type.TEXT)
                    raise

                # 校验订阅表记录（从表关联）
                sql = f"SELECT * FROM follow_trader_subscribe WHERE slave_account = %s"
                params = (account,)
                # 调用轮询等待方法（带时间范围过滤）
                db_sub_data = self.wait_for_database_record(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params
                )

                if not db_sub_data:
                    pytest.fail(f"账号 {account} 在订阅表中未找到关联记录")
                # 校验订阅表中的账号与当前账号一致
                slave_account = db_sub_data[0]["slave_account"]
                if slave_account != account:
                    pytest.fail(f"订阅表账号不匹配：预期={account}，实际={slave_account}")
                allure.attach(f"账号 {account} 订阅表关联校验通过", "校验结果", allure.attachment_type.TEXT)

        # 5. 保存总数量（供后续步骤使用）
        addslave_count = len(all_ids)
        var_manager.set_runtime_variable("all_ids", all_ids)
        var_manager.set_runtime_variable("addslave_count", addslave_count)
        print(f"后6个账号数据库校验完成，共提取{addslave_count}个ID，已保存到变量 addslave_count")
