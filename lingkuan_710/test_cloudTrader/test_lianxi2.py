import time

import pytest
import logging
import allure
from typing import Dict, Any, List
from lingkuan_710.VAR.VAR import *
from lingkuan_710.conftest import var_manager
from lingkuan_710.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


@allure.feature("跟单软件看板")
class TestDeleteFollowSlave(APITestBase):
    # ---------------------------
    # 账号管理-账号列表-批量下架VPS
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-账号列表-批量下架VPS（后9个账号）")
    def test_user_belowVps(self, var_manager, logged_session):
        # 1. 获取后9个账号的ID（使用range直接循环索引1-9，对应第2到第10个账号）
        user_count_cloudTrader = var_manager.get_variable("user_count_cloudTrader")
        user_ids_later9 = []
        for i in range(2, user_count_cloudTrader + 1):  # 循环索引2-10（共9次）
            user_id_var_name = f"user_ids_cloudTrader_{i}"
            user_id = var_manager.get_variable(user_id_var_name)
            if not user_id:
                pytest.fail(f"未找到第{i}个账号ID（变量：{user_id_var_name}）")
            user_ids_later9.append(user_id)

        var_manager.set_runtime_variable("user_ids_later9", user_ids_later9)  # 保存后9个账号ID
        print(f"将批量下架VPS的后9个账号ID：{user_ids_later9}")

        # 2. 发送批量下架VPS请求
        vpsId = var_manager.get_variable("vpsId")
        data = {
            "traderUserIds": user_ids_later9,  # 传入后9个账号ID
            "vpsId": [vpsId]  # VPS ID保持不变
        }
        response = self.send_post_request(
            logged_session,
            '/mascontrol/user/belowVps',
            json_data=data
        )

        # 3. 验证响应状态码和返回内容
        self.assert_response_status(response, 200, "批量下架VPS（后9个账号）失败")
        self.assert_json_value(response, "$.msg", "success", "响应msg字段应为success")

    # ---------------------------
    # 数据库校验-VPS数据-验证账号是否下架成功
    # ---------------------------
    @allure.title("数据库校验-VPS数据-验证账号是否下架成功（后9个账号）")
    def test_dbdelete_belowVps(self, var_manager, db_transaction):
        # 1. 获取账号总数和所有账号信息
        user_count_cloudTrader = var_manager.get_variable("user_count_cloudTrader", 0)
        if user_count_cloudTrader < 10:  # 修改条件为至少10个账号
            pytest.fail(f"用户总数需至少为10，当前为{user_count_cloudTrader}，无法提取后9个数据进行校验")

        # 2. 循环验证后9个账号的下架状态
        for i in range(2, user_count_cloudTrader + 1):  # 循环索引2-10（共9次）
            with allure.step(f"验证第{i}个账号是否下架成功"):
                # 获取单个账号（与下架的ID对应）
                account = var_manager.get_variable(f"user_accounts_cloudTrader_{i}")
                if not account:
                    pytest.fail(f"未找到需要验证的账号：user_accounts_cloudTrader_{i}")

                # 查询数据库（检查删除标记或记录是否存在）
                sql = f"SELECT * FROM follow_trader WHERE account = %s"

                # 调用轮询等待方法，验证记录是否被删除
                try:
                    self.wait_for_database_deletion(
                        db_transaction=db_transaction,
                        sql=sql,
                        params=(account,),
                        timeout=DELETE_WAIT_TIMEOUT,  # 设置15秒超时时间
                        poll_interval=POLL_INTERVAL,  # 每2秒查询一次
                    )
                    allure.attach(f"账号 {account} 已成功从数据库下架", "验证结果")
                    print(f"账号 {account} 已成功从数据库下架")
                except TimeoutError as e:
                    allure.attach(f"下架超时: {str(e)}", "验证结果")
                    pytest.fail(f"下架失败: {str(e)}")

                # 验证订阅表是否同步删除
                sql_sub = f"SELECT * FROM follow_trader_subscribe WHERE slave_account = %s"
                db_data_sub = self.query_database(db_transaction, sql_sub, (account,))
                assert not db_data_sub, (
                    f"第{i}个账号（{account}）的订阅表记录未删除，"
                    f"残留数据：{db_data_sub}"
                )
