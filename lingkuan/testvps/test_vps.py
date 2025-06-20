import json
import logging
import allure
import pytest
import time
from lingkuan.commons.jsonpath_utils import JsonPathUtils
from lingkuan.VAR.VAR import *
from lingkuan.commons.variable_manager import VariableManager

JsonPathUtils = JsonPathUtils()

# 初始化变量管理器
var_manager = VariableManager("test_vars.json")


# # 新增vps策略
# @allure.title("跟单软件看板-新增vps策略")
# def test_create_trader(api_with_db, db, logged_session):
#     api = api_with_db["api"]
#     db = api_with_db["db"]
#     data = {
#         "account": ACCOUNT,
#         "password": ACCOUNTPASS,
#         "remark": "测试vps策略",
#         "followStatus": 1,
#         "templateId": 1,
#         "type": 0,
#         "platform": USER_SERVER
#     }
#     with allure.step("1. 新增vps策略"):
#         api.post('/subcontrol/trader', json=data)
#     with allure.step("2. 判断策略是否新增成功"):
#         msg = api.extract_jsonpath("$.msg")
#         logging.info(f"断言：预期：success 实际：{msg}")
#         assert "success" == msg
#         time.sleep(3)
#     with allure.step("3. 从数据库获取新增策略id"):
#         # 查询数据库获取数据
#         with db.cursor() as cursor:
#             sql = 'SELECT * FROM follow_trader ORDER BY create_time DESC'
#             cursor.execute(sql)
#             # 获取数据库查询结果
#             db_data = cursor.fetchall()
#
#         # 提取数据库中的值
#         if db_data:
#             id = db_data[0]["id"]
#             var_manager.set_variable("vps_trader_id", id)
#             logging.info(f"新增策略id: {id}")
#             time.sleep(5)
#         else:
#             pytest.fail("数据库查询结果为空，无法进行对比")


# # 新增vps跟单账号
# @allure.title("跟单软件看板-新增vps跟单账号")
# def test_addSlave(api_with_db, db, logged_session):
#     vps_trader_id = var_manager.get_variable("vps_trader_id")
#     api = api_with_db["api"]
#     db = api_with_db["db"]
#     data = {
#         "traderId": vps_trader_id,
#         "platform": "CPTMarkets-Demo",
#         "account": "301351454",
#         "password": "f8337093861bede8526610afea80041d",
#         "remark": "",
#         "followDirection": 0,
#         "followMode": 1,
#         "remainder": 0,
#         "followParam": 1,
#         "placedType": 0,
#         "templateId": 1,
#         "followStatus": 1,
#         "followOpen": 1,
#         "followClose": 1,
#         "followRep": 0,
#         "fixedComment": "",
#         "commentType": "",
#         "digits": 0,
#         "cfd": "",
#         "forex": ""
#     }
#     with allure.step("1. 新增vps跟单账号"):
#         api.post("vps_api/subcontrol/follow/addSlave", json=data)
#     with allure.step("2. 判断vps跟单账号是否新增成功"):
#         msg = api.extract_jsonpath("$.msg")
#         logging.info(f"断言：预期：success 实际：{msg}")
#         assert "success" == msg
#         time.sleep(3)
#     with allure.step("3. 从数据库判断是否新增成功"):
#         # 查询数据库获取数据
#         with db.cursor() as cursor:
#             sql = 'SELECT * FROM follow_trader where account="%s"'
#             # 执行查询
#             cursor.execute(sql, (301351454))
#             # 获取查询结果
#             deleted = cursor.fetchall()
#             if deleted:
#                 db_first_deleted_id = deleted[0]["account"]
#             else:
#                 pytest.fail("数据库查询为空，无法进行对比")
#             # 判断返回的是否是0
#             logging.info(f"判断返回的account值是否是301351454：{db_first_deleted_id}")
#             assert db_first_deleted_id == "301351454"


# 策略开仓
@allure.title("跟单软件看板-策略开仓")
def test_orderSend(api_with_db, db, logged_session):
    # vps_trader_id = var_manager.get_variable("vps_trader_id")
    api = api_with_db['api']
    db = api_with_db['db']
    data = {
        "symbol": "XAUUSD",
        "placedType": 0,
        "remark": "ces",
        "intervalTime": 100,
        "type": 0,
        "totalNum": "3",
        "totalSzie": "1.00",
        "startSize": "0.01",
        "endSize": "0.10",
        "traderId": 5363
    }
    with allure.step("1. 策略开仓"):
        api.post("vps_api/subcontrol/trader/orderSend", json=data)
    with allure.step("2. 判断开仓是否成功"):
        msg = api.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert "success" == msg
        time.sleep(10)
    with allure.step("3. 从follow_order_instruct数据库检查是否有新的下单指令"):
        # 查询数据库获取数据
        with db.cursor() as cursor:
            sql = 'select * FROM follow_order_instruct where symbol LIKE "XAUUSD%" and min_lot_size="0.10" and max_lot_size="0.01" and remark="ces" and total_lots="1" and total_orders="3" and trader_id="5363" and create_time BETWEEN NOW() - INTERVAL 1 MINUTE AND NOW() + INTERVAL 1 MINUTE'
            time.sleep(30)
            try:
                # 执行查询
                cursor.execute(sql)
                # 获取查询结果
                result = cursor.fetchone()

                # 根据查询结果判断（添加明确的断言）
                assert result is not None, "下单失败：未找到符合条件的下单指令"
                # 如果断言通过，记录成功信息
                logging.info(f"有新的下单指令：{result}")


            except Exception as e:
                logging.error(f"查询数据库时发生错误：{str(e)}")
                # 重新抛出异常，使测试失败
                raise

@allure.title("根据数据库判断，然后提取数据")
def test_orderSenddb(db):
    with allure.step("1. 从follow_order_instruct数据库检查是否有新的下单指令"):
        # 查询数据库获取数据
        with db.cursor() as cursor:
            sql = 'select * FROM follow_order_detail where symbol LIKE "XAUUSD%" and type="0" and trader_id="5363" and create_time BETWEEN NOW() - INTERVAL 15 MINUTE AND NOW() + INTERVAL 15 MINUTE'
            time.sleep(30)
            # 执行查询
            cursor.execute(sql)
            # 获取查询结果
            result = cursor.fetchone()
            try:
                # 根据查询结果判断（添加明确的断言）
                assert result is not None, "查询失败：未找到符合条件的下单详情"
                # 如果断言通过，记录成功信息
                logging.info(f"新下单详情：{result}")


            except Exception as e:
                logging.error(f"查询数据库时发生错误：{str(e)}")
                # 重新抛出异常，使测试失败
                raise
            # 提取数据
            order_no = result[0]["order_no"]
            var_manager.set_variable("order_no", order_no)

            symbol = result[0]["symbol"]
            var_manager.set_variable("symbol", symbol)

            openPrice = result[0]["openPrice"]
            var_manager.set_variable("openPrice", openPrice)

            magic = result[0]["magic"]
            var_manager.set_variable("magic", magic)


#从MT4