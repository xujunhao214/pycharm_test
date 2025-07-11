# lingkuan/tests/test_vps_ordersend.py
import time
import math

import allure
import logging
import pytest
from lingkuan.VAR.VAR import *
from lingkuan.conftest import var_manager
from lingkuan.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


# ---------------------------
# 修改模式、品种
# ---------------------------
@allure.feature("云策略策略下单-跟单修改模式、品种")
class TestVPSOrderSend_Scence(APITestBase):
    # ---------------------------
    # 账号管理-账号列表-批量挂靠VPS
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-账号列表-批量挂靠VPS（后9个账号）")
    def test_user_hangVps(self, var_manager, logged_session, db_transaction):
        # 1. 获取后9个账号的ID（使用range直接循环索引1-9，对应第2到第10个账号）
        user_count_cloudTrader = var_manager.get_variable("user_count_cloudTrader")
        user_ids_later9 = []
        for i in range(2, user_count_cloudTrader + 1):  # 循环索引1-9（共9次）
            user_id_var_name = f"user_ids_cloudTrader_{i}"
            user_id = var_manager.get_variable(user_id_var_name)
            if not user_id:
                pytest.fail(f"未找到第{i}个账号ID（变量：{user_id_var_name}）")
            user_ids_later9.append(user_id)

        var_manager.set_runtime_variable("user_ids_later9", user_ids_later9)  # 保存后9个账号ID
        print(f"将批量挂靠的后9个账号ID：{user_ids_later9}")

        # 2. 发送批量挂靠VPS请求（后续代码与之前一致）
        vps_id_cloudTrader = var_manager.get_variable("vps_id_cloudTrader")
        vpsId = var_manager.get_variable("vpsId")
        data = {
            "accountType": 1,
            "vpsId": vpsId,
            "traderId": vps_id_cloudTrader,
            "followDirection": 0,
            "followMode": 1,
            "followParam": 1,
            "remainder": 0,
            "placedType": 0,
            "templateId": 1,
            "followStatus": 1,
            "followOpen": 1,
            "followClose": 1,
            "fixedComment": "",
            "commentType": "",
            "digits": 0,
            "traderUserIds": user_ids_later9  # 传入后9个账号ID
        }
        response = self.send_post_request(
            logged_session,
            '/mascontrol/user/hangVps',
            json_data=data
        )

        # 3. 验证响应（后续代码与之前一致）
        self.assert_response_status(response, 200, "批量挂靠VPS（后9个账号）失败")
        self.assert_json_value(response, "$.msg", "success", "响应msg字段应为success")

    # ---------------------------
    # 账号管理-账号列表-数据库校验-批量挂靠VPS
    # ---------------------------
    @allure.title("数据库校验-批量挂靠VPS（后9个账号）")
    def test_dbimport_addSlave(self, var_manager, db_transaction):
        # 1. 获取后9个账号的账号名（使用range直接循环索引1-9）
        all_accounts_cloudTrader = []
        user_count_cloudTrader = var_manager.get_variable("user_count_cloudTrader")
        for i in range(2, user_count_cloudTrader + 1):  # 循环索引1-9（共9次）
            account_var_name = f"user_accounts_cloudTrader_{i}"
            account_cloudTrader = var_manager.get_variable(account_var_name)
            if not account_cloudTrader:
                pytest.fail(f"未找到第{i}个账号（变量：{account_var_name}）")
            all_accounts_cloudTrader.append(account_cloudTrader)
        print(f"将校验的后9个账号：{all_accounts_cloudTrader}")

        # 2. 逐个校验后9个账号的数据库记录（后续代码与之前一致）
        all_ids_cloudTrader = []
        for idx, account_cloudTrader in enumerate(all_accounts_cloudTrader, 1):  # idx从1到9
            with allure.step(f"验证第{idx}个账号（{account_cloudTrader}）的数据库记录"):
                # 数据库查询和校验逻辑与之前一致
                sql = f"SELECT * FROM follow_trader WHERE account = %s"
                params = (account_cloudTrader,)

                db_data = self.wait_for_database_record(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    timeout=WAIT_TIMEOUT,
                    poll_interval=POLL_INTERVAL,
                    order_by="create_time DESC"
                )

                if not db_data:
                    pytest.fail(f"账号 {account_cloudTrader} 在主表中未找到记录")

                # 保存账号ID并校验状态/净值/订阅表（代码与之前一致）
                vps_cloudTrader_id = db_data[0]["id"]
                all_ids_cloudTrader.append(vps_cloudTrader_id)
                var_manager.set_runtime_variable(f"vps_cloudTrader_ids_{idx}", vps_cloudTrader_id)
                print(
                    f"账号 {account_cloudTrader} 的ID为：{vps_cloudTrader_id}，已保存到变量 vps_cloudTrader_ids_{idx}")

                # 校验账号状态和净值
                def verify_core_fields():
                    status = db_data[0]["status"]
                    if status != 0:
                        pytest.fail(f"账号 {account_cloudTrader} 状态异常：预期status=0，实际={status}")
                    euqit = db_data[0]["euqit"]
                    if euqit == 0:
                        pytest.fail(f"账号 {account_cloudTrader} 净值异常：预期euqit≠0，实际={euqit}")

                # 执行校验（代码与之前一致）
                try:
                    verify_core_fields()
                    allure.attach(f"账号 {account_cloudTrader} 主表字段校验通过", "校验结果",
                                  allure.attachment_type.TEXT)
                except AssertionError as e:
                    allure.attach(str(e), f"账号 {account_cloudTrader} 主表字段校验失败",
                                  allure.attachment_type.TEXT)
                    raise

                # 校验订阅表记录（代码与之前一致）
                sql = f"SELECT * FROM follow_trader_subscribe WHERE slave_account = %s"
                params = (account_cloudTrader,)
                db_sub_data = self.wait_for_database_record(
                    db_transaction=db_transaction,
                    sql=sql,
                    params=params,
                    timeout=WAIT_TIMEOUT,
                    poll_interval=POLL_INTERVAL,
                    order_by="create_time DESC"
                )

                if not db_sub_data:
                    pytest.fail(f"账号 {account_cloudTrader} 在订阅表中未找到关联记录")
                slave_account_cloudTrader = db_sub_data[0]["slave_account"]
                if slave_account_cloudTrader != account_cloudTrader:
                    pytest.fail(f"订阅表账号不匹配：预期={account_cloudTrader}，实际={slave_account_cloudTrader}")
                allure.attach(f"账号 {account_cloudTrader} 订阅表关联校验通过", "校验结果",
                              allure.attachment_type.TEXT)

        # 3. 保存总数量和ID列表（代码与之前一致）
        account_count = len(all_ids_cloudTrader)
        var_manager.set_runtime_variable("account_cloudTrader", account_count)
        var_manager.set_runtime_variable("all_vps_cloudTrader_ids", all_ids_cloudTrader)
        print(f"后9个账号数据库校验完成，共提取{account_count}个ID")
