# test_vps_ordersend.py
import allure
import logging
import time
import pytest
from lingkuan_youhua9.VAR.VAR import *
from lingkuan_youhua9.conftest import var_manager
from lingkuan_youhua9.commons.wait_utils import wait_for_condition

logger = logging.getLogger(__name__)


@allure.feature("VPS策略下单")
class TestCreate:
    # ---------------------------
    # 跟单软件看板-VPS数据-新增策略账号
    # ---------------------------
    @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("跟单软件看板-VPS数据-新增策略账号")
    def test_add_trader(self, vps_api_session, var_manager, logged_session, db_transaction):
        with allure.step("1. 发送新增策略账号请求"):
            vps_trader = var_manager.get_variable("vps_trader")
            data = {
                "account": vps_trader["account"],
                "password": vps_trader["password"],
                "remark": vps_trader["remark"],
                "followStatus": 1,
                "templateId": 1,
                "type": 0,
                "platform": vps_trader["platform"]
            }
            response = vps_api_session.post('/subcontrol/trader', json=data)
            time.sleep(3)

        with allure.step("2. 验证响应状态码"):
            assert response.status_code == 200, f"新增策略账号失败: {response.text}"

        with allure.step("3. 验证JSON返回内容"):
            # 使用JSONPath提取并断言
            msg = response.extract_jsonpath("$.msg")
            assert msg == "success", "响应msg字段应为success"

    @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("数据库校验-VPS数据-新增策略账号")
    def test_dbquery_trader(self, var_manager, db_transaction):
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

    # ---------------------------
    # 跟单软件看板-VPS数据-新增跟单账号
    # ---------------------------
    @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("跟单软件看板-VPS数据-新增跟单账号")
    def test_create_addSlave(self, vps_api_session, var_manager, logged_session, db_transaction):
        with allure.step("1. 发送新增策略账号请求"):
            add_Slave = var_manager.get_variable("add_Slave")
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            data = {
                "traderId": vps_trader_id,
                "platform": add_Slave["platform"],
                "account": add_Slave["account"],
                "password": add_Slave["password"],
                "remark": add_Slave["remark"],
                "followDirection": 0,
                "followMode": 1,
                "remainder": 0,
                "followParam": 1,
                "placedType": 0,
                "templateId": 1,
                "followStatus": 1,
                "followOpen": 1,
                "followClose": 1,
                "followRep": 0,
                "fixedComment": add_Slave["fixedComment"],
                "commentType": 2,
                "digits": 0,
                "cfd": "",
                "forex": "",
                "abRemark": ""
            }
            response = vps_api_session.post('/subcontrol/follow/addSlave', json=data)
            time.sleep(3)

        with allure.step("2. 验证响应状态码"):
            assert response.status_code == 200, f"创建用户失败: {response.text}"

        with allure.step("3. 验证JSON返回内容"):
            # 使用JSONPath提取并断言
            msg = response.extract_jsonpath("$.msg")
            assert msg == "success", "响应msg字段应为success"

    @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("数据库校验-VPS数据-新增跟单账号")
    def test_dbquery_addslave(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否新增成功"):
            db_addslave_query = var_manager.get_variable("db_addslave_query")
            with db_transaction.cursor() as cursor:
                sql = f'SELECT * FROM {db_addslave_query["table"]} WHERE account = %s ORDER BY create_time DESC'
                cursor.execute(sql, (db_addslave_query["account"],))
                db_data = cursor.fetchall()
                # 调试日志 - 查看查询结果
                logging.info(f"数据库查询结果: {db_data}")

                # 提取数据库中的值
                if db_data:
                    vps_addslave_id = db_data[0]["id"]
                    print(f"输出：{vps_addslave_id}")
                    logging.info(f"新增跟单账号ID: {vps_addslave_id}")
                    var_manager.set_runtime_variable("vps_addslave_id", vps_addslave_id)
                else:
                    pytest.fail("数据库查询结果为空，无法提取数据")

    # ---------------------------
    # 跟单软件看板-VPS数据-策略开仓
    # ---------------------------
    # @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("跟单软件看板-VPS数据-策略开仓")
    def test_trader_orderSend(self, vps_api_session, var_manager, logged_session):
        with allure.step("1. 发送策略开仓请求"):
            trader_ordersend = var_manager.get_variable("trader_ordersend")
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            data = {
                "symbol": trader_ordersend["symbol"],
                "placedType": 0,
                "remark": trader_ordersend["remark"],
                "intervalTime": 100,
                "type": 0,
                "totalNum": trader_ordersend["totalNum"],
                "totalSzie": trader_ordersend["totalSzie"],
                "startSize": trader_ordersend["startSize"],
                "endSize": trader_ordersend["endSize"],
                "traderId": vps_trader_id
            }
            response = vps_api_session.post('/subcontrol/trader/orderSend', json=data)
        with allure.step("2. 判断是否添加成功"):
            msg = response.extract_jsonpath("$.msg")
            logging.info(f"断言：预期：success 实际：{msg}")
            assert "success" == msg

    # @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("数据库校验-策略开仓-策略开仓指令")
    def test_dbquery_orderSend(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否有策略开仓指令"):
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            trader_ordersend = var_manager.get_variable("trader_ordersend")

            # 定义数据库查询条件函数
            def check_db():
                with db_transaction.cursor() as cursor:
                    # 使用参数化查询，安全且避免语法错误
                    sql = f'''
                    SELECT * 
                    FROM {trader_ordersend["table"]} 
                    WHERE symbol LIKE %s 
                      AND instruction_type = %s 
                      AND master_order_status = %s 
                      AND type = %s 
                      AND min_lot_size = %s 
                      AND max_lot_size = %s 
                      AND remark = %s 
                      AND total_lots = %s 
                      AND total_orders = %s 
                      AND trader_id = %s 
                      AND create_time BETWEEN NOW() - INTERVAL %s MINUTE AND NOW() + INTERVAL %s MINUTE
                    '''

                    # 查询参数
                    params = (
                        f"%{trader_ordersend['symbol']}%",  # LIKE需要使用%通配符
                        "1",
                        "0",
                        trader_ordersend["type"],
                        trader_ordersend["endSize"],
                        trader_ordersend["startSize"],
                        trader_ordersend["remark"],
                        trader_ordersend["totalSzie"],
                        trader_ordersend["totalNum"],
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
        with allure.step("2. 提取数据"):
            # 提取数据库中的值
            if db_data:
                order_no = db_data[0]["order_no"]
                logging.info(f"获取策略账号下单的订单号: {order_no}")
                var_manager.set_runtime_variable("order_no", order_no)
            else:
                pytest.fail("数据库查询结果为空，无法提取数据")

    # @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("数据库校验-策略开仓-跟单开仓指令")
    def test_dbquery_orderSend_addsalve(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否有跟单开仓指令"):
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            trader_ordersend = var_manager.get_variable("trader_ordersend")

            # 定义数据库查询条件函数
            def check_db():
                with db_transaction.cursor() as cursor:
                    # 使用参数化查询，安全且避免语法错误
                    sql = f'''
                    SELECT * 
                    FROM {trader_ordersend["table"]} 
                    WHERE symbol LIKE %s 
                      AND instruction_type = %s 
                      AND master_order_status = %s 
                      AND type = %s 
                      AND trader_id = %s 
                      AND create_time BETWEEN NOW() - INTERVAL %s MINUTE AND NOW() + INTERVAL %s MINUTE
                    '''

                    # 查询参数
                    params = (
                        f"%{trader_ordersend['symbol']}%",  # LIKE需要使用%通配符
                        "2",
                        "0",
                        trader_ordersend["type"],
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
                master_orders = list(map(lambda x: x["master_order"], db_data))
                logging.info(f"主账号订单: {master_orders}")
                var_manager.set_runtime_variable("master_orders", master_orders)
            else:
                pytest.fail("数据库查询结果为空，无法提取数据")

    # @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("数据库校验-策略开仓-持仓检查")
    def test_dbquery_order_detail(self, var_manager, db_transaction):
        with allure.step("1. 根据下单指令仓库的order_no字段获取跟单账号订单数据"):
            order_no = var_manager.get_variable("order_no")
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            trader_ordersend = var_manager.get_variable("trader_ordersend")

            # 定义数据库查询条件函数
            def check_db():
                with db_transaction.cursor() as cursor:
                    # 使用参数化查询，安全且避免语法错误
                    sql = f'''
                        SELECT * 
                        FROM {trader_ordersend["table_detail"]} 
                        WHERE symbol LIKE %s 
                          AND send_no = %s 
                          AND type = %s 
                          AND trader_id = %s 
                          AND create_time BETWEEN NOW() - INTERVAL %s MINUTE AND NOW() + INTERVAL %s MINUTE
                        '''

                    # 查询参数
                    params = (
                        f"%{trader_ordersend['symbol']}%",  # LIKE需要使用%通配符
                        order_no,
                        trader_ordersend["type"],
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
            if float(sum(addsalve_size)) == float(trader_ordersend["totalSzie"]):
                print("跟单总手数和下单的手数相等")
                logger.info("跟单总手数和下单的手数相等")
            else:
                print("跟单总手数和下单的手数不相等")
                logger.info("跟单总手数和下单的手数不相等")

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
