# test_vps_ordersend.py
import allure
import logging
import time
import pytest
from lingkuan_youhua6.VAR.VAR import *
from lingkuan_youhua6.conftest import var_manager
from lingkuan_youhua6.commons.wait_utils import wait_for_condition

logger = logging.getLogger(__name__)


@allure.feature("VPS交易下单")
class TestMasordersend:
    # ---------------------------
    # 账号管理-交易下单-VPS分配下单
    # ---------------------------
    # @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("跟账号管理-交易下单-VPS分配下单")
    def test_bargain_masOrderSend(self, api_session, var_manager, logged_session):
        with allure.step("1. 发送VPS分配下单请求"):
            masOrderSend = var_manager.get_variable("masOrderSend")
            data = {
                "traderList": [
                    3648
                ],
                "type": 0,
                "tradeType": 0,
                "symbol": masOrderSend["symbol"],
                "startSize": "0.10",
                "endSize": "1.00",
                "totalSzie": "1.00",
                "remark": "测试数据",
                "totalNum": 0
            }
            response = api_session.post('/bargain/masOrderSend', json=data)
        with allure.step("2. 判断VPS分配下单是否成功"):
            msg = response.extract_jsonpath("$.msg")
            logging.info(f"断言：预期：success 实际：{msg}")
            assert "success" == msg

    # @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("数据库校验-VPS下单-下单指令")
    def test_dbbargain_masOrderSend(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否有下单"):
            masOrderSend = var_manager.get_variable("masOrderSend")
            vps_trader_id = var_manager.get_variable("vps_trader_id")

            # 定义数据库查询条件函数
            def check_db():
                with db_transaction.cursor() as cursor:
                    # 使用参数化查询，安全且避免语法错误
                    sql = f'''
                    SELECT * 
                    FROM {masOrderSend["table"]} 
                    WHERE symbol LIKE %s 
                      AND master_order_status = %s 
                      AND type = %s 
                      AND min_lot_size = %s 
                      AND max_lot_size = %s 
                      AND remark = %s 
                      AND total_lots = %s 
                      AND trader_id = %s 
                      AND create_time BETWEEN NOW() - INTERVAL %s MINUTE AND NOW() + INTERVAL %s MINUTE
                    '''

                    # 查询参数
                    params = (
                        f"%{masOrderSend['symbol']}%",  # LIKE需要使用%通配符
                        "0",
                        masOrderSend["type"],
                        masOrderSend["endSize"],
                        masOrderSend["startSize"],
                        masOrderSend["remark"],
                        masOrderSend["totalSzie"],
                        vps_trader_id,
                        MYSQL_TIME,
                        MYSQL_TIME
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
                error_message=f"数据库查询超时: {masOrderSend['type']} 未找到",
                step_title=f"等待数据 {masOrderSend['type']} 出现在数据库中。"
            )
        with allure.step("2. 判断是否下单成功"):
            # 提取数据库中的值
            if db_data:
                order_no = db_data[0]["order_no"]
                logging.info(f"获取策略账号下单的订单号: {order_no}")
                var_manager.set_runtime_variable("order_no", order_no)
            else:
                pytest.fail("数据库查询结果为空，无法提取数据")
            # 判断是否下单成功
            if db_data[0]["status"] == 1:
                allure.attach("下单成功", "成功详情", allure.attachment_type.TEXT)
            else:
                error_msg = "下单失败"
                allure.attach(error_msg, "下单失败", allure.attachment_type.TEXT)
                pytest.fail(error_msg)

    # @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("数据库校验-VPS分配下单-持仓检查")
    def test_dbquery_order_detail(self, var_manager, db_transaction):
        with allure.step("1. 根据下单指令仓库的order_no字段获取跟单账号订单数据"):
            order_no = var_manager.get_variable("order_no")
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            masOrderSend = var_manager.get_variable("masOrderSend")

            # 定义数据库查询条件函数
            def check_db():
                with db_transaction.cursor() as cursor:
                    # 使用参数化查询，安全且避免语法错误
                    sql = f'''
                        SELECT * 
                        FROM {masOrderSend["table_detail"]} 
                        WHERE symbol LIKE %s 
                          AND send_no = %s 
                          AND type = %s 
                          AND trader_id = %s 
                          AND create_time BETWEEN NOW() - INTERVAL %s MINUTE AND NOW() + INTERVAL %s MINUTE
                        '''

                    # 查询参数
                    params = (
                        f"%{masOrderSend['symbol']}%",  # LIKE需要使用%通配符
                        order_no,
                        masOrderSend["type"],
                        vps_trader_id,
                        MYSQL_TIME,
                        MYSQL_TIME
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
            # 提取数据库中的值
            if db_data:
                order_nos = list(map(lambda x: x["order_no"], db_data))
                logging.info(f"持仓订单的订单号: {order_nos}")
                var_manager.set_runtime_variable("order_nos", order_nos)

                addsalve_size = [record["size"] for record in db_data]
                # addsalve_size = db_data[0]["size"]
                logging.info(f"手数: {addsalve_size}")
                # var_manager.set_runtime_variable("addsalve_size", addsalve_size)
                # 计算总和（保持Decimal精度）
                total = sum(addsalve_size)
                logging.info(f"手数总和: {total}")

            else:
                pytest.fail("数据库查询结果为空，无法提取数据")
            # 判断跟单总手数是否和下单的手数相等
            if float(sum(addsalve_size)) == float(masOrderSend["totalSzie"]):
                print("跟单总手数和下单的手数相等")
                logger.info("跟单总手数和下单的手数相等")
            else:
                print("跟单总手数和下单的手数不相等")
                logger.info("跟单总手数和下单的手数不相等")

    # ---------------------------
    # 账号管理-交易下单-平仓
    # ---------------------------
    # @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("跟账号管理-交易下单-平仓")
    def test_bargain_masOrderClose(self, api_session, var_manager, logged_session):
        with allure.step("1. 发送开仓请求"):
            data = {
                "isCloseAll": 1,
                "intervalTime": 100,
                "traderList": [
                    3648
                ]
            }
            response = api_session.post('/bargain/masOrderClose', json=data)
        with allure.step("2. 判断是否平仓成功"):
            msg = response.extract_jsonpath("$.msg")
            logging.info(f"断言：预期：success 实际：{msg}")
            assert "success" == msg

    # @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("数据库校验-交易下单-平仓指令")
    def test_dbbargain_masOrderClose(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否有平仓指令"):
            masOrderSend = var_manager.get_variable("masOrderSend")
            vps_trader_id = var_manager.get_variable("vps_trader_id")

            # 定义数据库查询条件函数
            def check_db():
                with db_transaction.cursor() as cursor:
                    # 使用参数化查询，安全且避免语法错误
                    sql = f'''
                    SELECT * 
                    FROM {masOrderSend["table"]} 
                    WHERE symbol LIKE %s 
                      AND master_order_status = %s 
                      AND type = %s 
                      AND trader_id = %s 
                      AND create_time BETWEEN NOW() - INTERVAL %s MINUTE AND NOW() + INTERVAL %s MINUTE
                    '''

                    # 查询参数
                    params = (
                        f"%{masOrderSend['symbol']}%",  # LIKE需要使用%通配符
                        "1",
                        masOrderSend["type"],
                        vps_trader_id,
                        MYSQL_TIME,
                        MYSQL_TIME
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
                error_message=f"数据库查询超时: {masOrderSend['type']} 未找到",
                step_title=f"等待数据 {masOrderSend['type']} 出现在数据库中。"
            )
        with allure.step("2. 判断是否平仓成功"):
            if db_data[0]["master_order_status"] == 1:
                allure.attach("平仓成功", "成功详情", allure.attachment_type.TEXT)
                logging.info("平仓成功")
            else:
                error_msg = "平仓失败"
                allure.attach(error_msg, "平仓失败", allure.attachment_type.TEXT)
                pytest.fail(error_msg)
