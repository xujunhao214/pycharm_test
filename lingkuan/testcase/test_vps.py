import json
import logging
import allure
import pytest
from lingkuan.commons.jsonpath_utils import JsonPathUtils
from lingkuan.VAR.VAR import *

JsonPathUtils = JsonPathUtils()


# @allure.title("vps列表-登录")
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


# 校验服务器IP是否可用
@allure.title("vps列表-校验服务器IP是否可用")
def test_get_connect(session, logged_session):
    with allure.step("1. 校验服务器IP是否可用"):
        session.get('/mascontrol/vps/connect', params={'ipAddress': '127.0.0.1'})

    with allure.step("2. 校验接口请求是否成功"):
        msg = session.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert "success" == msg


# 获取可见用户列表
@allure.title("vps列表-获取可见用户信息")
def test_get_user(session, logged_session):
    global user_data1, user_data2
    with allure.step("1. 请求可见用户列表接口"):
        session.get('/sys/user/user')

    with allure.step("2. 获取可见用户信息"):
        user_data1 = session.extract_jsonpath("$.data[0]")
        user_data2 = session.extract_jsonpath("$.data[1]")
        logging.info(f"获取的可见用户信息：{user_data1}{user_data2}")


# 获取组别信息
@allure.title("vps列表-获取组别信息")
def test_get_group_list(session, logged_session):
    global group_data1, group_data2
    with allure.step("1. 请求组别信息接口"):
        session.get('/mascontrol/group/list', params={'type': '1'})

    with allure.step("2. 获取组别信息"):
        group_data1 = session.extract_jsonpath("$.data[0]")
        group_data2 = session.extract_jsonpath("$.data[1]")
        logging.info(f"获取的组别信息：{group_data1}{group_data2}")


# 新增vps
# 基础用例：新增vps
@pytest.mark.dependency(name="create_vps")
@allure.title("vps列表-新增vps")
def test_create_vps(session, logged_session):
    with allure.step("1. 新增vps"):
        data = {
            "ipAddress": "127.0.0.1",
            "name": "测试",
            "expiryDate": "2025-06-30 00:00:00",
            "remark": "测试",
            "isOpen": 1,
            "isActive": 1,
            "userList": ["sun", "admin"],
            "isSelectAccount": 1,
            "isMonitorRepair": 1,
            "isSpecializedRepair": 1,
            "isAutoRepair": 1,
            "groupId": "62,44",
            "sort": 150
        }
        session.post('/mascontrol/vps', json=data)
    with allure.step("2. 判断是否添加成功"):
        msg = session.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert "success" == msg


# 依赖创建vps的用例：必须创建成功才会执行
@pytest.mark.dependency(depends=["create_vps"])
@allure.title("vps列表-获取vps列表")
def test_vps_page(session, logged_session):
    global vps_list_id
    parser = {
        "page": 1,
        "limit": 50,
        "asc": "false",
        "order": "sort",
    }
    with allure.step("1. 获取vps列表"):
        session.get('/mascontrol/vps/page', params=parser)
    with allure.step("2. 获取订单id"):
        vps_list_id = session.extract_jsonpath("$.data.list[0].id")
        logging.info(f"订单id: {vps_list_id}")


# 编辑vps
@pytest.mark.dependency(depends=["create_vps", "test_vps_page"])
@allure.title("vps列表-编辑vps")
def test_update_vps(session, logged_session):
    with allure.step("1. 编辑vps"):
        data = {
            "ipAddress": "127.0.0.1",
            "name": "测试编辑name",
            "expiryDate": "2025-06-30 00:00:00",
            "remark": "测试编辑备注",
            "isOpen": 1,
            "isActive": 1,
            "userList": [user_data1, user_data2],
            "isSelectAccount": 1,
            "isMonitorRepair": 1,
            "isSpecializedRepair": 1,
            "isAutoRepair": 1,
            "groupId": "group_data1,group_data2",
            "sort": 160,
            "id": vps_list_id
        }

        session.put('/mascontrol/vps', json=data)
    with allure.step("2. 判断是否编辑成功"):
        msg = session.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert "success" == msg


# 获取vps列表
@pytest.mark.dependency(depends=["create_vps"])
@allure.title("vps列表-获取vps列表-校验编辑")
def test_vps_page2(session, logged_session):
    global vps_list_id
    parser = {
        "page": 1,
        "limit": 50,
        "asc": "false",
        "order": "sort",
    }
    with allure.step("1. 获取vps列表-校验编辑"):
        session.get('/mascontrol/vps/page', params=parser)
    with allure.step("2. 检查编辑后的信息是否正确"):
        name = session.extract_jsonpath("$.data.list[0].name")
        remark = session.extract_jsonpath("$.data.list[0].remark")
        sort = session.extract_jsonpath("$.data.list[0].sort")
        assert name == "测试编辑name"
        logging.info(f"断言:预期:'测试编辑name' 实际： {name}")
        assert remark == "测试编辑备注"
        logging.info(f"断言:预期:'测试编辑备注' 实际： {remark}")
        assert sort == 160
        logging.info(f"断言:预期:160 实际： {remark}")


# # 删除vps
# @pytest.mark.dependency(depends=["create_vps"])
# @allure.title("vps列表-删除vps")
# def test_delete_vps(session):
#     # 定义白名单（不可删除的ID列表）
#     WHITE_LIST_IDS = ["6", "91", "22", "49"]
#     if vps_list_id not in WHITE_LIST_IDS:
#         with allure.step("1. 删除vps"):
#             data = [vps_list_id]
#         session.delete('/mascontrol/vps', json=data)
#         with allure.step("2. 判断是否删除vps成功"):
#             msg = session.extract_jsonpath("$.msg")
#         logging.info(f"断言：预期：success 实际：{msg}")
#         assert "success" == msg
