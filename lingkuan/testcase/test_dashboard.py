import json
import logging
import allure
import pytest
from lingkuan.commons.jsonpath_utils import JsonPathUtils

JsonPathUtils = JsonPathUtils()


# 参数化
@pytest.mark.parametrize(
    "data, res_msg",
    [
        # 正确的用户名和密码
        ({"username": "admin",
          "password": "04739db02172e04f63f5278211184deec745bad9d797882b343e7201898d8da1d9fced282f6b271d3815a5057482e62c6f6b88dacb642ba05632bd2ee348101c76cb1f86b70f91695fd1cff11fce76246f044ace477cdbfa1e3e1521b19b023b14c7165e82c5"},
         "success"),
        # 正确的用户名和错误的密码
        ({"username": "admin",
          "password": "12313213123"},
         "用户名或密码错误"),
    ]
)
@allure.title("仪表盘-登录")
@pytest.mark.dependency(name="login")
def test_login(session, data, res_msg):
    headers = {
        "Authorization": "${token}",
        "x-sign": "417B110F1E71BD2CFE96366E67849B0B",
    }

    with allure.step("1. 登录操作"):
        session.post('/sys/auth/login', json=data, headers=headers)

    with allure.step("2. 登录成功，提取access_token"):
        if res_msg == "success":
            access_token = session.extract_jsonpath("$.data.access_token")
            print(f"access Token: {access_token}")
            logging.info(f"access Token: {access_token}")
            session.headers.update({
                "Authorization": f"{access_token}",
                "x-sign": "417B110F1E71BD2CFE96366E67849B0B",
            })


@pytest.mark.dependency(depends=["login"])
@allure.title("仪表盘-获取仪表盘数据")
def test_dashboard(session):
    with allure.step("1. 获取仪表盘数据"):
        session.get("/dashboard/getStatData")
    with allure.step("2. 校验是否获取成功"):
        msg = session.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert msg == "success", f"是否一致：预期：success 实际：{msg} "

@pytest.mark.dependency(depends=["login"])
@allure.title("仪表盘-获取仪表盘数据")
def test_dashboard(session):
    with allure.step("1. 获取仪表盘数据"):
        session.get("/socket/dashboardSymbol")
    with allure.step("2. 校验是否获取成功"):
        msg = session.extract_jsonpath("$.msg")
        logging.info(f"断言：预期：success 实际：{msg}")
        assert msg == "success", f"是否一致：预期：success 实际：{msg} "
