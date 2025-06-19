import json
import logging
import allure
import pytest
import time
from lingkuan.commons.jsonpath_utils import JsonPathUtils
from lingkuan.VAR.VAR import *

JsonPathUtils = JsonPathUtils()


# @allure.title("云策略-登录")
# def test_login(session):
#     data = {
#         "username": USERNAME,
#         "password": PASSWORD,
#     }
#     headers = {
#         "Authorization": "${token}",
#         "x-sign": "417B110F1E71BD2CFE96366E67849B0B",
#     }
#
#     with allure.step("1. 登录操作"):
#         session.post('/sys/auth/login', json=data, headers=headers)
#
#     with allure.step("2. 登录成功，提取access_token"):
#         access_token = session.extract_jsonpath("$.data.access_token")
#         print(f"access Token: {access_token}")
#         logging.info(f"access Token: {access_token}")
#         session.headers.update({
#             "Authorization": f"{access_token}",
#             "x-sign": "417B110F1E71BD2CFE96366E67849B0B",
#         })


# 获取云策略ID
@allure.title("云策略-获取云策略数据")
def test_get_cloudMasterList(session, logged_session):
    global mastervos_id, mastervos_name
    params = {
        "name": "",
        "groupId": "",
    }
    with allure.step("1. 获取云策略数据"):
        session.get('/mascontrol/cloudMaster/list', params=params)
    with allure.step("2. 提取云策略id数据"):
        mastervos_id = session.extract_jsonpath("$.data.masterVOS[0].id")
        logging.info(f"mastervos_id：{mastervos_id}")
    with allure.step("2. 提取云策略name数据"):
        mastervos_name = session.extract_jsonpath("$.data.masterVOS[0].name")
        logging.info(f"mastervos_name：{mastervos_name}")


# 获取云策略账号数据
@allure.title("云策略-获取云策略账号数据")
def test_get_traderList(session, logged_session):
    global traderList_id, traderList_platform
    with allure.step("1. 获取策略账号id"):
        session.get('/mascontrol/cloudTrader/traderList')
    with allure.step("2. 提取策略账号id数据"):
        traderList_id = session.extract_jsonpath("$.data[1].id")
        logging.info(f"traderList_id：{traderList_id}")
    with allure.step("2. 提取云策略账号平台数据"):
        traderList_platform = session.extract_jsonpath("$.data[1].platform")
        logging.info(f"traderList_platform：{traderList_platform}")


# # 修改云策略状态-关闭
# @allure.title("云策略-修改云策略状态-关闭")
# def test_update_cloudMaster(session, logged_session):
#     data = {
#         "id": mastervos_id,
#         "name": mastervos_name,
#         "type": 0,
#         "remark": "测试数据",
#         "status": 1
#     }
#     with allure.step("1. 修改云策略状态-关闭"):
#         session.put('/mascontrol/cloudMaster', json=data)
#     with allure.step("2. 判断是否修改成功"):
#         msg = session.extract_jsonpath("$.msg")
#         logging.info(f"断言：预期：success 实际：{msg}")
#         assert "success" == msg
#         time.sleep(3)
#
#     # 修改云策略状态-开启
#
#
# @allure.title("云策略-修改云策略状态-开启")
# def test_update_cloudMaster2(session, logged_session):
#     data = {
#         "id": mastervos_id,
#         "name": mastervos_name,
#         "type": 0,
#         "remark": "测试数据",
#         "status": 0
#     }
#     with allure.step("1. 修改云策略状态-开启"):
#         session.put('/mascontrol/cloudMaster', json=data)
#     with allure.step("2. 判断是否修改成功"):
#         msg = session.extract_jsonpath("$.msg")
#         logging.info(f"断言：预期：success 实际：{msg}")
#         assert "success" == msg
#
#
# # 新增云策略-已挂靠账号
# @allure.title("云策略-新增云策略-已挂靠账号")
# def test_create_cloudTrader(session, logged_session):
#     with allure.step("1. 选择一个策略账号,新增云策略"):
#         data = {
#             "cloudId": mastervos_id,
#             "sourceType": 0,
#             "remark": "ces",
#             "runningStatus": 0,
#             "traderId": traderList_id,
#             "managerIp": "",
#             "managerAccount": "",
#             "managerPassword": "",
#             "account": "",
#             "platform": "",
#             "templateId": ""
#         }
#         session.post('/mascontrol/cloudTrader', json=data)
#     with allure.step("2. 判断是否添加成功"):
#         msg = session.extract_jsonpath("$.msg")
#         logging.info(f"断言：预期：success 实际：{msg}")
#         assert "success" == msg
#         time.sleep(3)


# # 新增云策略-manager云策略
# @allure.title("云策略-新增云策略-manager云策略")
# def test_create_cloudTrader2(session, logged_session):
#     with allure.step("1. 选择一个策略账号,新增云策略"):
#         data = {
#             "cloudId": mastervos_id,
#             "sourceType": 1,
#             "remark": "ces",
#             "runningStatus": 0,
#             "traderId": "",
#             "managerIp": "demo-dc-hk-01.adamantstone.co:443",
#             "managerAccount": "66",
#             "managerPassword": "a9e12d3b6eda5cba8a2b7a30249b8797",
#             "account": "119999257",
#             "platform": traderList_platform,
#             "templateId": 1
#         }
#         session.post('/mascontrol/cloudTrader', json=data)
#     with allure.step("2. 判断是否添加成功"):
#         msg = session.extract_jsonpath("$.msg")
#         logging.info(f"断言：预期：success 实际：{msg}")
#         assert "success" == msg
#         time.sleep(3)


# 新增跟单账号
@allure.title("云策略-新增跟单账号")
def test_create_cloudBatchAdd(session, logged_session):
    with allure.step("1. 新增跟单账号"):
        data = {
            "traderList": [
                traderList_id
            ],
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
            "fixedComment": "ceshi",
            "commentType": 2,
            "digits": 0,
            "cfd": "",
            "forex": "",
            "sort": "12",
            "cloudId": mastervos_id
        }
        session.post('/mascontrol/cloudTrader/cloudBatchAdd', json=data)
    with allure.step("2. 判断新增跟单账号是否添加成功"):
        msg = session.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert "success" == msg
        time.sleep(3)
