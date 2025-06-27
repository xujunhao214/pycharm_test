import allure
import logging
import time
import pytest
from lingkuan_youhua6.VAR.VAR import *
from lingkuan_youhua6.conftest import var_manager
from lingkuan_youhua6.commons.wait_utils import wait_for_condition

logger = logging.getLogger(__name__)


@allure.feature("VPS平仓")
class TestClose:
    # ---------------------------
    # 跟单软件看板-VPS数据-策略平仓
    # ---------------------------
    # @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("跟单软件看板-VPS数据-策略平仓")
    def test_trader_orderclose(self, vps_api_session, var_manager, logged_session, db_transaction):
        with allure.step("1. 发送全平订单平仓请求"):
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            vps_trader_isCloseAll = var_manager.get_variable("vps_trader_isCloseAll")
            data = {
                "isCloseAll": 1,
                "intervalTime": 100,
                "traderId": vps_trader_id,
                "account": vps_trader_isCloseAll["account"]
            }
            response = vps_api_session.post('/subcontrol/trader/orderClose', json=data)
            time.sleep(3)

        with allure.step("2. 验证响应状态码"):
            assert response.status_code == 200, f"平仓失败: {response.text}"

        with allure.step("3. 验证JSON返回内容"):
            # 使用JSONPath提取并断言
            msg = response.extract_jsonpath("$.msg")
            assert msg == "success", "响应msg字段应为success"

    # @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("数据库校验-策略平仓-策略平仓指令")
    def test_dbquery_traderclose(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否有策略平仓指令"):
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            vps_trader_isCloseAll = var_manager.get_variable("vps_trader_isCloseAll")

            # 定义数据库查询条件函数
            def check_db():
                with db_transaction.cursor() as cursor:
                    # 使用参数化查询，安全且避免语法错误
                    sql = f'''
                    SELECT * 
                    FROM {vps_trader_isCloseAll["table"]} 
                    WHERE symbol LIKE %s 
                      AND instruction_type = %s 
                      AND master_order_status = %s 
                      AND trader_id = %s 
                      AND create_time BETWEEN NOW() - INTERVAL %s MINUTE AND NOW() + INTERVAL %s MINUTE
                    '''

                    # 查询参数
                    params = (
                        f"%{vps_trader_isCloseAll['symbol']}%",  # LIKE需要使用%通配符
                        "2",
                        "1",
                        vps_trader_id,
                        MYSQL_TIME,
                        MYSQL_TIME,
                    )
                    cursor.execute(sql, params)
                    # 获取数据库查询结果
                    db_data = cursor.fetchall()
                    # 调试日志 - 查看查询结果
                    logging.info(f"数据库查询结果: {db_data}")
                    return db_data

            # 使用智能等待并记录Allure步骤
            db_data = wait_for_condition(
                condition=check_db,
                timeout=30,
                poll_interval=2,
                error_message=f"数据库查询超时: {vps_trader_id} 未找到",
                step_title=f"等待数据 {vps_trader_id} 出现在数据库中。"
            )
        with allure.step("2. 提取数据"):
            # 提取数据库中的值
            if db_data:
                master_order_status = db_data[0]["master_order_status"]
                logging.info(f"订单状态由0未平仓变为1已平仓: {master_order_status}")
                var_manager.set_runtime_variable("master_order_status", master_order_status)
            else:
                pytest.fail("数据库查询结果为空，无法提取数据")
