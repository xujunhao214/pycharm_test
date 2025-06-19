import json
import logging
import time
import allure
import pytest
from lingkuan.commons.jsonpath_utils import JsonPathUtils
from lingkuan.VAR.VAR import *

JsonPathUtils = JsonPathUtils()


# @allure.title("服务器测速-登录")
# @pytest.mark.dependency(name="login")
# def test_login(session, logged_session):
#     global access_token
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

@pytest.mark.dependency(name="get_vps")
@allure.title("服务器测速-获取vps列表数据")
def test_get_vps(session, logged_session):
    global vps_name
    with allure.step("1. 请求vps列表数据接口"):
        session.post('/mascontrol/speed/listVps')
    with allure.step("2. 提取vps列表数据"):
        vps_name = session.extract_jsonpath("$.data[-1].name")
        logging.info(f"提取的vps数据：{vps_name}")


@pytest.mark.dependency(name="get_server")
@allure.title("服务器测速-获取服务器列表数据")
def test_get_server(session, logged_session):
    global servername
    with allure.step("1. 请求服务器列表数据接口"):
        session.post('/mascontrol/speed/listServer')
    with allure.step("2. 提取服务器列表数据"):
        servername = session.extract_jsonpath("$.data[0].servername")
        logging.info(f"提取的服务器数据：{servername}")


@pytest.mark.dependency(depends=["get_vps", "get_server"])
@allure.title("服务器测速-开始进行测速")
def test_speed_measure(session, logged_session, servername=None):
    data = {
        "vps": [vps_name],
        "servers": [servername]
    }
    with allure.step("1. 请求服务器列表数据接口"):
        session.post('/mascontrol/speed/measure', json=data)
    with allure.step("2. 判断是否测速成功"):
        msg = session.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert "success" == msg
        time.sleep(2)


@allure.title("服务器测速-配置开关")
def test_speed_updateSetting(session, logged_session):
    data = {
        "id": 1,
        "defaultServerNode": 0,
        "defaultServerNodeLogin": 1
    }
    with allure.step("1. 请求服务器配置开关接口"):
        session.put('/mascontrol/speed/updateSetting', json=data)
        time.sleep(2)
    with allure.step("2. 判断是否修改状态成功"):
        msg = session.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert "success" == msg
