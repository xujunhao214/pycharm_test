import allure
import logging
import pytest
import time
import math
from lingkuanMT5_1107.VAR.VAR import *
from lingkuanMT5_1107.conftest import var_manager
from lingkuanMT5_1107.commons.api_base import *

logger = logging.getLogger(__name__)
SKIP_REASON = "跳过此用例"


@allure.feature("云策略复制下单-开仓的场景校验-buy")
class TestCloudStrategyOrderbuy(APITestBase):
    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("账号管理-组别列表-新增MT5云策略组别")
    def test_create_cloudgroup(self, class_random_str, logged_session, var_manager):
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
            "新增MT5云策略组别失败"
        )

        # 3. 验证JSON返回内容
        self.assert_json_value(
            response,
            "$.msg",
            "success",
            "响应msg字段应为success"
        )

    # @pytest.mark.skip(reason=SKIP_REASON)
    @allure.title("数据库校验-组别列表-新增MT5云策略组别")
    def test_dbquery_cloudgroup(self, class_random_str, var_manager, db_transaction):
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
                pytest.fail("数据库查询结果为空，无法提取数据")

            MT5cloudTrader_group_id = db_data[0]["id"]
            print(f"输出：{MT5cloudTrader_group_id}")
            logging.info(f"新增MT5云策略组别ID: {MT5cloudTrader_group_id}")
            var_manager.set_runtime_variable("MT5cloudTrader_group_id", MT5cloudTrader_group_id)
