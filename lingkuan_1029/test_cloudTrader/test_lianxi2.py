import time
import math
import allure
import logging
import pytest
from lingkuan_1029.VAR.VAR import *
from lingkuan_1029.conftest import var_manager
from lingkuan_1029.commons.api_base import APITestBase
from lingkuan_1029.commons.redis_utils import *

logger = logging.getLogger(__name__)
SKIP_REASON = "该功能暂不需要"  # 统一跳过原因


# ---------------------------
# 修改模式、品种
# ---------------------------
@allure.feature("云策略策略下单-跟单修改模式、品种")
class TestVPSOrderSend_Scence(APITestBase):
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-组别列表-新增云策略组别")
    def test_create_cloudgroup(self, logged_session, var_manager):
        add_cloudgroup = var_manager.get_variable("add_cloudgroup")
        data = {
            "name": add_cloudgroup["name"],
            "color": add_cloudgroup["color"],
            "sort": add_cloudgroup["sort"],
            "type": add_cloudgroup["type"]
        }

        # 1. 发送新增VPS组别请求
        response = self.send_post_request(
            logged_session,
            "/mascontrol/group",
            json_data=data
        )

        # 2. 验证响应状态码
        self.assert_response_status(
            response,
            200,
            "新增云策略组别失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-组别列表-新增云策略组别")
    def test_dbquery_cloudgroup(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            add_cloudgroup = var_manager.get_variable("add_cloudgroup")

            db_data = self.query_database(
                db_transaction,
                f"SELECT * FROM follow_group WHERE name = %s",
                (add_cloudgroup["name"],),
            )

        with allure.step("2. 提取数据库中的值"):
            # 提取数据库中的值
            if not db_data:
                pytest.fail("数据库查询结果为空，订单可能没有入库")

            cloudTrader_group_id = db_data[0]["id"]
            print(f"输出：{cloudTrader_group_id}")
            logging.info(f"新增云策略组别ID: {cloudTrader_group_id}")
            var_manager.set_runtime_variable("cloudTrader_group_id", cloudTrader_group_id)
