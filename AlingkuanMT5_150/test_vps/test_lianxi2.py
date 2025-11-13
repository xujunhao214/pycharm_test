import allure
import logging
import pytest
import time
from AlingkuanMT5_150.conftest import var_manager
from AlingkuanMT5_150.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("VPS策略账号交易下单-开仓的场景校验")
class TestVPSMasOrdersend(APITestBase):
    @pytest.mark.url("vps")
    @allure.title("VPS策略账号-跟单账号平仓")
    def test_seng_close(self, class_random_str, logged_session, var_manager):
        # 1. 获取总数量（控制循环范围）
        MT5vps_user_count = var_manager.get_variable("MT5vps_user_count", 0)
        # 校验总数量合理性（确保有足够的变量可获取）
        assert MT5vps_user_count >= 2, f"MT5vps_user_count={MT5vps_user_count}，数量不足，无法执行批量下单"

        # 2. 循环获取两组变量并执行请求（按索引对应：addslave_ids_1→accounts_2、addslave_ids_2→accounts_3...）
        # 循环范围：i 对应 vps_addslave_ids 的后缀（1 到 MT5vps_user_count-1）
        # j 对应 vps_user_accounts 的后缀（2 到 MT5vps_user_count）
        for i, j in zip(range(1, MT5vps_user_count), range(2, MT5vps_user_count + 1)):
            # 动态获取两组变量
            addslave_id = var_manager.get_variable(f"MT5vps_addslave_ids_{i}")
            user_account = var_manager.get_variable(f"MT5vps_user_accounts_{j}")

            # 验证变量存在（避免空值导致接口报错）
            assert addslave_id is not None, f"变量 MT5vps_addslave_ids_{i} 未找到或值为空"
            assert user_account is not None, f"变量 MT5vps_user_accounts_{j} 未找到或值为空"

            # 3. 构造请求数据（每组变量对应一次请求）
            data = {
                "traderId": addslave_id,
                "account": user_account,
                "ifAccount": True,
                "isCloseAll": 1
            }

            with allure.step(f"1.执行下单请求（traderId={addslave_id}，account={user_account}）"):
                # 4. 发送接口请求
                response = self.send_post_request(
                    logged_session,
                    '/subcontrol/trader/orderClose',
                    json_data=data
                )
            with allure.step(f"2.验证响应结果"):
                # 5. 验证响应结果（每个请求单独校验）
                self.assert_json_value(
                    response,
                    "$.msg",
                    "success",
                    f"traderId={addslave_id}、account={user_account} 下单失败，响应msg字段应为success"
                )
                logging.info(f"traderId={addslave_id}、account={user_account} 下单成功")
