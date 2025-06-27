import allure
import logging
import time
import pytest
from lingkuan_youhua5.VAR.VAR import *
from lingkuan_youhua5.conftest import var_manager
from lingkuan_youhua5.commons.wait_utils import wait_for_condition

logger = logging.getLogger(__name__)


@allure.feature("VPS跟单下单")
class TestCreate:
    # ---------------------------
    # 跟单软件看板-VPS数据
    # ---------------------------
    # @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("跟单软件看板-VPS数据-新增策略账号")
    def test_create_user(self, api_session, var_manager, logged_session, db_transaction):
        with allure.step("1. 发送新增策略账号请求"):
            vps_trader = var_manager.get_variable("vps_trader")
            response = api_session.post('/subcontrol/trader', json=vps_trader)
            time.sleep(3)

        with allure.step("2. 验证响应状态码"):
            assert response.status_code == 200, f"创建用户失败: {response.text}"

        with allure.step("3. 验证JSON返回内容"):
            # 使用JSONPath提取并断言
            msg = response.extract_jsonpath("$.msg")
            assert msg == "success", "响应msg字段应为success"

    # @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("数据库校验-VPS数据-新增策略账号")
    def test_dbquery_user(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            db_trader_query = var_manager.get_variable("db_trader_query")
            with db_transaction.cursor() as cursor:
                sql = f'SELECT * FROM {db_trader_query["table"]} WHERE account = %s ORDER BY create_time DESC'
                cursor.execute(sql, (db_trader_query["account"],))
                db_data = cursor.fetchall()
                # 调试日志 - 查看查询结果
                logging.info(f"数据库查询结果: {db_data}")

                # 提取数据库中的值
                if db_data:
                    vps_trader_id = db_data[0]["id"]
                    print(f"输出：{vps_trader_id}")
                    logging.info(f"新增策略账号ID: {vps_trader_id}")
                    var_manager.set_runtime_variable("vps_trader_id", vps_trader_id)
                else:
                    pytest.fail("数据库查询结果为空，无法提取数据")
