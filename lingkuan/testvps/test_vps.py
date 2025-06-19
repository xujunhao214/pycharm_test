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


# 新增vps跟单账号
@allure.title("跟单软件看板-新增vps跟单账号")
def test_addSlave(api_with_db, db, logged_session):
    vps_trader_id = var_manager.get_variable("vps_trader_id")
    api = api_with_db["api"]
    db = api_with_db["db"]
    data = {
        "traderId": vps_trader_id,
        "platform": "CPTMarkets-Demo",
        "account": "301351454",
        "password": "f8337093861bede8526610afea80041d",
        "remark": "",
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
        "fixedComment": "",
        "commentType": "",
        "digits": 0,
        "cfd": "",
        "forex": ""
    }
    with allure.step("1. 新增vps跟单账号"):
        api.post("vps_api/subcontrol/follow/addSlave", json=data)
    with allure.step("2. 判断vps跟单账号是否新增成功"):
        msg = api.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert "success" == msg
        time.sleep(3)
    with allure.step("3. 从数据库判断是否新增成功"):
        # 查询数据库获取数据
        with db.cursor() as cursor:
            sql = 'SELECT * FROM follow_trader where account="%s"'
            # 执行查询
            cursor.execute(sql, (301351454))
            # 获取查询结果
            deleted = cursor.fetchall()
            if deleted:
                db_first_deleted_id = deleted[0]["account"]
            else:
                pytest.fail("数据库查询为空，无法进行对比")
            # 判断返回的是否是0
            logging.info(f"判断返回的account值是否是301351454：{db_first_deleted_id}")
            assert db_first_deleted_id == "301351454"
