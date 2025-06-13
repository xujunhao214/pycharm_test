import json
import logging
import allure
import pytest
from lingkuan.commons.jsonpath_utils import JsonPathUtils
from lingkuan.VAR.VAR import *

JsonPathUtils = JsonPathUtils()


# @allure.title("平台列表-登录")
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


@allure.title("平台列表-获取服务器列表数据")
def test_platform_list(session, logged_session):
    global platformList
    with allure.step("1. 获取服务器列表数据"):
        session.get("/mascontrol/platform/listServer")
    with allure.step("2. 提取一个服务器数据"):
        platformList = session.extract_jsonpath("$.data[15].serverName")
        logging.info(f"提取一个服务数据platformList: {platformList}")


@allure.title("平台列表-新增列表数据")
@pytest.mark.dependency(name="create_platform")
def test_create_platform(session, logged_session):
    data = {
        "brokerName": "测试",
        "platformType": "MT4",
        "platformList": [platformList],
        "remark": "测试数据",
        "logo": "https://java-copytrade-new.oss-cn-beijing.aliyuncs.com/test/20250613/yanshi_51459.png",
        "maxLots": "1.00"
    }

    with allure.step("1. 新增列表数据"):
        session.post("/mascontrol/platform", json=data)
    with allure.step("2. 校验是否新增成功"):
        msg = session.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert msg == "success", f"是否一致：预期：success 实际：{msg} "


@allure.title("平台列表-获取列表数据")
@pytest.mark.dependency(depends=["create_platform"])
def test_platfor_list(session, logged_session):
    global list_id
    parms = {
        "page": 1,
        "limit": 50,
        "asc": "false",
        "order": "update_time",
    }
    with allure.step("1. 获取订单列表数据"):
        session.get("/mascontrol/platform/page", params=parms)
    with allure.step("2. 获取新建订单id"):
        list_id = session.extract_jsonpath("$.data.list[0].id")
        logging.info(f"新建订单id: {list_id}")


@allure.title("平台列表-编辑列表数据")
@pytest.mark.dependency(depends=["create_platform", "test_platfor_list"])
def test_update_platform(session, logged_session):
    data = {
        "id": list_id,
        "brokerName": "测试编辑",
        "platformType": "MT4",
        "server": "AdvancedMarkets-Demo",
        "serverNode": "185.97.160.58:443",
        "remark": "测试数据编辑",
        "version": 0,
        "deleted": 0,
        "creator": "10000",
        "createTime": "2025-06-13 14:18:41",
        "updater": "null",
        "updateTime": "2025-06-13 14:18:41",
        "platformList": ["AdvancedMarkets-Demo"],
        "logo": "https://java-copytrade-new.oss-cn-beijing.aliyuncs.com/test/20250613/yanshi_51459.png",
        "maxLots": "2.00"
    }

    with allure.step("1. 编辑列表数据"):
        session.put("/mascontrol/platform", json=data)
    with allure.step("2. 校验编辑是否提交成功"):
        msg = session.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert msg == "success", f"是否一致：预期：success 实际：{msg} "


@allure.title("平台列表-获取列表数据-校验编辑功能是否正确")
@pytest.mark.dependency(depends=["create_platform"])
def test_platfor_list2(session, logged_session):
    global list_id
    parms = {
        "page": 1,
        "limit": 50,
        "asc": "false",
        "order": "update_time",
    }
    with allure.step("1. 获取订单列表数据"):
        session.get("/mascontrol/platform/page", params=parms)
    with allure.step("2. 校验编辑功能是否正确"):
        brokerName = session.extract_jsonpath("$.data.list[0].brokerName")
        assert brokerName == "测试编辑"
        logging.info(f"断言：预期：测试编辑 实际：{brokerName}")

        remark = session.extract_jsonpath("$.data.list[0].remark")
        assert remark == "测试数据编辑"
        logging.info(f"断言：预期：测试数据编辑 实际：{remark}")

        maxLots = session.extract_jsonpath("$.data.list[0].maxLots")
        assert maxLots == 2.0
        logging.info(f"断言：预期：2.0 实际：{maxLots}")

# @allure.title("平台列表-删除列表数据")
# @pytest.mark.dependency(depends=["create_platform"])
# def test_delete_platform(session, logged_session):
#     data = [list_id]
#
#     with allure.step("1. 删除列表数据"):
#         session.delete("/mascontrol/platform", json=data)
#     with allure.step("2. 校验是否删除成功"):
#         msg = session.extract_jsonpath("$.msg")
#         logging.info(f"断言：预期：success 实际：{msg}")
#         assert msg == "success"
