# test_vps_loukai.py
import allure
import logging
import time
import pytest
from lingkuan_youhua11.VAR.VAR import *
from lingkuan_youhua11.conftest import var_manager
from lingkuan_youhua11.commons.wait_utils import wait_for_condition

logger = logging.getLogger(__name__)


@allure.feature("VPS策略下单-漏平")
class TestLouping:
    # ---------------------------
    # 跟单软件看板-VPS数据-修改跟单账号
    # ---------------------------
    # @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("跟单软件看板-VPS数据-修改跟单账号（漏平）")
    def test_update_slave(self, vps_api_session, var_manager, logged_session, db_transaction):
        with allure.step("1. 发送修改策略账号请求"):
            add_Slave = var_manager.get_variable("add_Slave")
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            # 平仓给关闭followClose：0
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
                "templateId": 35,
                "followStatus": 1,
                "followOpen": 1,
                "followClose": 0,
                "followRep": 0,
                "fixedComment": add_Slave["fixedComment"],
                "commentType": 2,
                "digits": 0,
                "cfd": "@",
                "forex": "",
                "abRemark": "",
                "id": 5432
            }
            response = vps_api_session.post('/subcontrol/follow/updateSlave', json=data)
            time.sleep(3)

        with allure.step("2. 验证响应状态码"):
            assert response.status_code == 200, f"创建用户失败: {response.text}"

        with allure.step("3. 验证JSON返回内容"):
            # 使用JSONPath提取并断言
            msg = response.extract_jsonpath("$.msg")
            assert msg == "success", "响应msg字段应为success"

    # @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("数据库校验-VPS数据-修改跟单账号是否成功")
    def test_dbquery_updateslave(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否修改成功"):
            follow_trader_subscribe = var_manager.get_variable("follow_trader_subscribe")
            with db_transaction.cursor() as cursor:
                sql = f'SELECT * FROM {follow_trader_subscribe["table"]} WHERE slave_account = %s ORDER BY create_time DESC'
                cursor.execute(sql, (follow_trader_subscribe["slave_account"],))
                db_data = cursor.fetchall()
                # 调试日志 - 查看查询结果
                logging.info(f"数据库查询结果: {db_data}")

                # 提取数据库中的值
                if db_data:
                    follow_close = db_data[0]["follow_close"]
                    print(f"输出：{follow_close}")
                    logging.info(f"跟单账号平仓的状态: {follow_close}")
                    var_manager.set_runtime_variable("follow_open", follow_close)
                else:
                    pytest.fail("数据库查询结果为空，无法提取数据")

                if follow_close == 0:
                    print("数据修改正确")
                    logging.info("数据修改正确")
                else:
                    print("数据没有修改成功")
                    logging.info("数据没有修改成功")

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
                order_no = db_data[0]["order_no"]
                logging.info(f"获取策略账号下单的订单号: {order_no}")
                var_manager.set_runtime_variable("order_no", order_no)
            else:
                pytest.fail("数据库查询结果为空，无法提取数据")

    # ---------------------------
    # 跟单软件看板-VPS数据-策略平仓
    # ---------------------------
    # @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("跟单软件看板-VPS数据-策略平仓-出现漏平")
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
                logging.info(f"订单状态应该是0平仓失败: {master_order_status}")
                var_manager.set_runtime_variable("master_order_status", master_order_status)
            else:
                pytest.fail("数据库查询结果为空，无法提取数据")

    # @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("数据库校验-策略平仓-订单详情数据库检查平仓成功还是失败")
    def test_dbquery_orderSend_close(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否平仓失败"):
            vps_trader_louping = var_manager.get_variable("vps_trader_louping")
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")

            # 定义数据库查询条件函数
            def check_db():
                with db_transaction.cursor() as cursor:
                    # 使用参数化查询，安全且避免语法错误
                    sql = f'''
                    SELECT * 
                    FROM {vps_trader_louping["table"]} 
                    WHERE symbol LIKE %s 
                      AND account = %s 
                      AND trader_id = %s 
                      AND type = %s 
                      AND create_time BETWEEN NOW() - INTERVAL %s MINUTE AND NOW() + INTERVAL %s MINUTE
                    '''

                    # 查询参数
                    params = (
                        f"%{vps_trader_louping['symbol']}%",  # LIKE需要使用%通配符
                        vps_trader_louping["account"],
                        vps_addslave_id,
                        vps_trader_louping["type"],
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
                error_message=f"数据库查询超时: {vps_addslave_id} 未找到",
                step_title=f"等待数据 {vps_addslave_id} 出现在数据库中。"
            )
            # 判断是否平仓失败
            if vps_trader_louping["close_status"] == db_data[0]["close_status"]:
                print("平仓失败")
                logging.info("平仓失败")
                close_remark = db_data[0]["close_remark"]
                logging.info(f"平仓失败的异常信息: {close_remark}")
            else:
                print("平仓成功")
                logging.info("平仓成功")

    # ---------------------------
    # 跟单软件看板-VPS数据-策略开仓-一键补全
    # ---------------------------
    @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("跟单软件看板-VPS数据-开仓补全")
    def test_follow_repairSend(self, vps_api_session, var_manager, logged_session):
        with allure.step("1. 发送平仓补全请求"):
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            data = {
                "type": 2,
                "masterId": vps_trader_id,
                "slaveId": vps_addslave_id
            }
            response = vps_api_session.post('/subcontrol/follow/repairSend', json=data)
        with allure.step("2. 没有开仓，需要提前开仓才可以补全"):
            msg = response.extract_jsonpath("$.msg")
            logging.info(f"断言：预期：请开启补仓开关 实际：{msg}")
            assert "请开启补仓开关" == msg

    # ---------------------------
    # 跟单软件看板-VPS数据-修改跟单账号
    # ---------------------------
    # @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("跟单软件看板-VPS数据-修改跟单账号（漏平）")
    def test_update_slave2(self, vps_api_session, var_manager, logged_session, db_transaction):
        with allure.step("1. 发送修改策略账号请求"):
            add_Slave = var_manager.get_variable("add_Slave")
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            # 平仓给开启followOpen：1
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
                "templateId": 35,
                "followStatus": 1,
                "followOpen": 1,
                "followClose": 1,
                "followRep": 0,
                "fixedComment": add_Slave["fixedComment"],
                "commentType": 2,
                "digits": 0,
                "cfd": "@",
                "forex": "",
                "abRemark": "",
                "id": 5432
            }
            response = vps_api_session.post('/subcontrol/follow/updateSlave', json=data)
            time.sleep(3)

        with allure.step("2. 验证响应状态码"):
            assert response.status_code == 200, f"创建用户失败: {response.text}"

        with allure.step("3. 验证JSON返回内容"):
            # 使用JSONPath提取并断言
            msg = response.extract_jsonpath("$.msg")
            assert msg == "success", "响应msg字段应为success"

    # @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("数据库校验-VPS数据-修改跟单账号是否成功")
    def test_dbquery_updateslave2(self, var_manager, db_transaction):
        with allure.step("1. 查询数据库验证是否修改成功"):
            follow_trader_subscribe = var_manager.get_variable("follow_trader_subscribe")
            with db_transaction.cursor() as cursor:
                sql = f'SELECT * FROM {follow_trader_subscribe["table"]} WHERE slave_account = %s ORDER BY create_time DESC'
                cursor.execute(sql, (follow_trader_subscribe["slave_account"],))
                db_data = cursor.fetchall()
                # 调试日志 - 查看查询结果
                logging.info(f"数据库查询结果: {db_data}")

                # 提取数据库中的值
                if db_data:
                    follow_open = db_data[0]["follow_open"]
                    print(f"输出：{follow_open}")
                    logging.info(f"策略账号开仓的状态: {follow_open}")
                    var_manager.set_runtime_variable("follow_open", follow_open)
                else:
                    pytest.fail("数据库查询结果为空，无法提取数据")

                if follow_open == 1:
                    print("数据修改正确")
                    logging.info("数据修改正确")
                else:
                    print("数据没有修改成功")
                    logging.info("数据没有修改成功")

    # @pytest.mark.skip(reason="该功能暂不需要")
    @allure.title("跟单软件看板-VPS数据-修改完之后进行平仓补全")
    def test_follow_repairSend2(self, vps_api_session, var_manager, logged_session):
        with allure.step("1. 发送开仓补全请求"):
            vps_addslave_id = var_manager.get_variable("vps_addslave_id")
            vps_trader_id = var_manager.get_variable("vps_trader_id")
            data = {
                "type": 2,
                "masterId": vps_trader_id,
                "slaveId": vps_addslave_id
            }
            response = vps_api_session.post('/subcontrol/follow/repairSend', json=data)
        with allure.step("2. 关仓成功"):
            msg = response.extract_jsonpath("$.msg")
            logging.info(f"断言：预期：success 实际：{msg}")
            assert "success" == msg
