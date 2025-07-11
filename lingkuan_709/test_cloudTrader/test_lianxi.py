# lingkuan_709/tests/test_vps_ordersend.py
import time

import allure
import logging
import pytest
from lingkuan_709.VAR.VAR import *
from lingkuan_709.conftest import var_manager
from lingkuan_709.commons.api_base import APITestBase  # 导入基础类

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


# ---------------------------
# 修改模式、品种
# ---------------------------
@allure.feature("云策略策略下单-跟单修改模式、品种")
class TestVPSOrderSend_Scence(APITestBase):
    # ---------------------------
    # 账号管理-账号列表-修改用户
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-账号列表-修改用户")
    def test_update_user(self, api_session, var_manager, logged_session, db_transaction):
        # 1. 发送创建用户请求
        user_ids_cloudTrader_3 = var_manager.get_variable("user_ids_cloudTrader_3")
        user_accounts_cloudTrader_3 = var_manager.get_variable("user_accounts_cloudTrader_3")
        vps_cloudTrader_ids_2 = var_manager.get_variable("vps_cloudTrader_ids_2")
        vps_id_cloudTrader = var_manager.get_variable("vps_cloudTrader_ids_2")
        user_accounts_cloudTrader_1 = var_manager.get_variable("user_accounts_cloudTrader_1")
        vpsId = var_manager.get_variable("vpsId")
        data = {
            "id": user_ids_cloudTrader_3,
            "account": user_accounts_cloudTrader_3,
            "password": "b7e9fafa953d50f0e2278cacd85a8d15",
            "platform": "FXAdamantStone-Demo",
            "accountType": "0",
            "serverNode": "47.83.21.167:443",
            "remark": "参数化新增云策略账号",
            "sort": 100,
            "vpsDescs": [
                {
                    "desc": "39.99.136.49-主VPS-跟单账号",
                    "status": 0,
                    "statusExtra": "启动成功",
                    "forex": "",
                    "cfd": "",
                    "traderId": vps_cloudTrader_ids_2,
                    "ipAddress": "39.99.136.49",
                    "sourceId": vps_id_cloudTrader,
                    "sourceAccount": user_accounts_cloudTrader_1,
                    "sourceName": "测试数据",
                    "loginNode": "47.83.21.167:443",
                    "nodeType": 0,
                    "nodeName": "账号节点",
                    "type": None,
                    "vpsId": vpsId,
                    "traderType": None,
                    "abRemark": None
                }
            ]
        }
        response = self.send_put_request(
            api_session,
            "/mascontrol/user",
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "编辑策略信息失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # ---------------------------
    # 数据库校验-账号列表-修改用户是否成功
    # ---------------------------
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-账号列表-修改用户是否成功")
    def test_dbupdate_user(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否编辑成功"):
            user_accounts_cloudTrader_3 = var_manager.get_variable("user_accounts_cloudTrader_3")
            sql = f"SELECT * FROM follow_cloud_trader WHERE account = %s"
            params = (user_accounts_cloudTrader_3,)

            # 调用轮询等待方法（带时间范围过滤）
            db_data = self.wait_for_database_record(
                db_transaction=db_transaction,
                sql=sql,
                params=params,
                timeout=WAIT_TIMEOUT,  # 最多等30秒
                poll_interval=POLL_INTERVAL,  # 每2秒查一次
                stable_period=STBLE_PERIOD,  # 新增：数据连续5秒不变则认为加载完成
                order_by="create_time DESC"  # 按创建时间倒序
            )

            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空，无法提取数据")
            cfd_value = db_data[0]["cfd"]
            # 允许为 None 或空字符串（去除空格后）
            assert cfd_value is None or cfd_value.strip() == "", f"修改个人信息失败（cfd字段应为空，实际值：{cfd_value}）"
